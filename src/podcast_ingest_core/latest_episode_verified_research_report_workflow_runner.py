"""Bounded SPEC 018 latest episode verified research report workflow."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, is_dataclass
from functools import wraps
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import uuid

from . import storage
from .artifact_lock import exclusive_artifact_claim
from .episode_claim import episode_writer_claim
from .generation_proof import ChildArtifactCommit, controlled_child_commit_scope
from .corpus_latest_episode_deterministic_workflow_runner import (
    DEFAULT_SELECTOR,
    _resolve_latest_episode,
    _run_pinned_deterministic_workflow,
)
from .errors import LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError
from .models import (
    CorpusLatestEpisodeDeterministicWorkflowRunFilter,
    LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    LatestEpisodeVerifiedResearchReportWorkflowRunResult,
    LatestEpisodeVerifiedResearchReportWorkflowStep,
    LatestEpisodeVerifiedResearchReportWorkflowWarning,
)
from .corpus_semantic_remediation_runner import run_corpus_semantic_remediation
from .research_workflow import run_research_workflow
from .semantic_summarizer import SEMANTIC_API_COST_ACK
from .report_safety import OMITTED_VALUE, contains_sensitive_text, is_sensitive_key, safe_text
from .semantic_review_artifact import inspect_semantic_review
from .semantic_summary_identity import canonical_semantic_summary_path
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    canonical_transcript_scope,
    resolve_canonical_transcript_asset_paths,
    resolve_canonical_transcript_identity,
)
from .verified_research_lineage import (
    lineage_path,
    record_current_verified_research_lineage,
    validate_current_verified_research_lineage,
)
from .validator import validate_transcript
from .verified_research_report import (
    REPORT_SCHEMA_VERSION,
    VerifiedResearchReportInputError,
    assemble_verified_research_report,
    publish_verified_research_report_bundle,
)


_RUN_MODE_DRY_RUN = "dry_run"
_RUN_MODE_CONFIRMED = "confirmed"
_SAFE_PODCAST_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_SAFE_EPISODE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")
_SAFE_DEPENDENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SAFE_ENVIRONMENT_NAME = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
_SAFE_STOCK_QUERY = re.compile(r"^[^\x00-\x1f?#]{1,128}$")
_SAFE_BASE_URL = re.compile(r"^https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?(?:/[A-Za-z0-9._~/-]*)?$")
_SAFE_CHECKPOINT_STAGE = re.compile(r"^[a-z_]{1,64}$")
_SAFE_CHECKPOINT_STATUS = re.compile(r"^[a-z_]{1,32}$")
_SAFE_CHECKPOINT_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|/)?[A-Za-z0-9._一-鿿\\/-]{1,1024}$")
_CHECKPOINT_TERMINAL_OUTCOMES = {
    "in_progress", "completed", "reused", "blocked", "failed", "rejected", "manual"
}
_CURRENT_INVOCATION_GENERATION: ContextVar[int | None] = ContextVar(
    "latest_episode_verified_research_invocation_generation", default=None
)
_CURRENT_WORKFLOW_CLAIM: ContextVar[Any | None] = ContextVar(
    "latest_episode_verified_research_workflow_claim", default=None
)
_CURRENT_CANONICAL_SCOPE: ContextVar[Any | None] = ContextVar(
    "latest_episode_verified_research_canonical_scope", default=None
)


def _invocation_scope(function):
    """Keep invocation generation scoped to one Core call without wall-clock ordering."""

    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any):
        reset_generation = _CURRENT_INVOCATION_GENERATION.set(None)
        try:
            return function(*args, **kwargs)
        finally:
            _release_canonical_transcript_scope()
            _release_episode_workflow_claim()
            _CURRENT_INVOCATION_GENERATION.reset(reset_generation)

    return wrapped


def _acquire_episode_workflow_claim(
    checkpoint_path: Path,
    podcast_id: str,
    episode_ref: str,
) -> None:
    """Hold the shared writer/cost boundary and legacy workflow claim to terminal."""

    shared_claim = episode_writer_claim(podcast_id, episode_ref)
    shared_claim.__enter__()
    workflow_claim = exclusive_artifact_claim(
        checkpoint_path.with_name(f".{checkpoint_path.name}.workflow.claim")
    )
    try:
        workflow_claim.__enter__()
    except BaseException:
        shared_claim.__exit__(None, None, None)
        raise
    _CURRENT_WORKFLOW_CLAIM.set((shared_claim, workflow_claim))


def _release_episode_workflow_claim() -> None:
    claims = _CURRENT_WORKFLOW_CLAIM.get()
    if claims is None:
        return
    _CURRENT_WORKFLOW_CLAIM.set(None)
    shared_claim, workflow_claim = claims
    try:
        workflow_claim.__exit__(None, None, None)
    finally:
        shared_claim.__exit__(None, None, None)


def _acquire_canonical_transcript_scope(podcast_id: str, episode_ref: str) -> None:
    """Freeze the external selector's exact path/title/SHA for all child stages."""

    identity = resolve_canonical_transcript_identity(podcast_id, episode_ref)
    if identity is None:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "canonical transcript is missing"
        )
    scope = canonical_transcript_scope(identity)
    scope.__enter__()
    _CURRENT_CANONICAL_SCOPE.set(scope)


def _release_canonical_transcript_scope() -> None:
    scope = _CURRENT_CANONICAL_SCOPE.get()
    if scope is None:
        return
    _CURRENT_CANONICAL_SCOPE.set(None)
    scope.__exit__(None, None, None)


@_invocation_scope
def run_latest_episode_verified_research_report_workflow(
    podcast_id: str,
    *,
    confirm: bool = False,
    expected_episode_ref: str | None = None,
    api_cost_ack: str = "",
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> LatestEpisodeVerifiedResearchReportWorkflowRunResult:
    """Preview or complete exactly one approved latest episode report workflow.

    Confirmed execution validates the episode-scoped acknowledgement before RSS,
    provider, writer, or child-stage interaction.  The latest selector is then
    resolved exactly once and all later work receives the pinned reference.
    """

    if not isinstance(confirm, bool):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("confirm is invalid")
    normalized_podcast_id = _normalize_podcast_id(podcast_id)
    normalized_expected_episode_ref = _normalize_expected_episode_ref(expected_episode_ref)
    normalized_stock_query = _normalize_stock_query(stock_query)
    normalized_semantic_base_url = _normalize_semantic_base_url(semantic_base_url)
    normalized_semantic_api_key_env = _normalize_semantic_api_key_env(semantic_api_key_env)
    _normalize_api_cost_ack(api_cost_ack)
    filters = _filters(
        expected_episode_ref=normalized_expected_episode_ref,
        stock_query=normalized_stock_query,
        include_fixture_verification=include_fixture_verification,
        transcription_model=transcription_model,
        transcription_device=transcription_device,
        transcription_compute_type=transcription_compute_type,
        transcription_vad_filter=transcription_vad_filter,
        semantic_provider=semantic_provider,
        semantic_model=semantic_model,
        semantic_base_url_identity_sha256=_semantic_base_url_identity_sha256(
            normalized_semantic_base_url
        ),
        semantic_chunk_seconds=semantic_chunk_seconds,
        semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
    )
    if confirm:
        _require_confirmed_approval(normalized_expected_episode_ref, api_cost_ack)

    canonical_episode_ref, initial_failure = _resolve_latest_episode(normalized_podcast_id)
    if initial_failure is not None:
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=confirm,
            episode_ref=None,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome=initial_failure.status,
            filters=filters,
            stage_plan=[_step("deterministic_processing", initial_failure.status, "latest episode resolution failed")],
        )
    if canonical_episode_ref is None:
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=confirm,
            episode_ref=None,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome="blocked",
            filters=filters,
            stage_plan=[_step("deterministic_processing", "blocked", "latest episode could not be resolved")],
        )

    if not confirm:
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=False,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=None,
            outcome="dry_run",
            filters=filters,
            stage_plan=_preview_plan(normalized_podcast_id, canonical_episode_ref),
        )

    if canonical_episode_ref != normalized_expected_episode_ref:
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=True,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome="rejected",
            filters=filters,
            stage_plan=[
                _step(
                    "approval_boundary",
                    "rejected",
                    "latest episode does not match expected_episode_ref",
                )
            ],
            approval_boundary_rejected=True,
        )

    checkpoint_path = storage.latest_episode_verified_research_report_paths(
        normalized_podcast_id, canonical_episode_ref, "0" * 64
    ).checkpoint_path
    try:
        _acquire_episode_workflow_claim(
            checkpoint_path, normalized_podcast_id, canonical_episode_ref
        )
    except Exception as exc:  # noqa: BLE001 - claim acquisition is a bounded boundary.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="workflow_claim",
            exception=exc,
            finalize_checkpoint=False,
        )
    # Artifact truth is inspected inside the episode claim before a corrupt or
    # identity-bad checkpoint is read.  A complete independently validated bundle
    # therefore remains adoptable and checkpoint persistence is only a warning.
    try:
        adopted_bundle = _adopt_complete_bundle(
            normalized_podcast_id,
            canonical_episode_ref,
            normalized_stock_query,
            include_fixture_verification,
            filters,
        )
    except Exception as exc:  # noqa: BLE001 - artifact inspection is a bounded stage.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="inspection",
            exception=exc,
        )
    if adopted_bundle is not None:
        warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning] = []
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=True,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome="reused" if adopted_bundle.reused else "completed",
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage_plan=[
                _step(
                    "publish",
                    "reused" if adopted_bundle.reused else "completed",
                    "complete verified report bundle reused"
                    if adopted_bundle.reused
                    else "complete verified report artifacts published",
                )
            ],
            report_version=adopted_bundle.report_version,
            source_digest=adopted_bundle.source_digest,
            bundle_dir=adopted_bundle.bundle_dir,
            report_json_path=adopted_bundle.report_json_path,
            report_markdown_path=adopted_bundle.report_markdown_path,
            manifest_path=adopted_bundle.manifest_path,
            warnings=warnings,
        )
    try:
        invocation_generation = _reserve_invocation_generation(
            checkpoint_path, normalized_podcast_id, canonical_episode_ref
        )
    except Exception as exc:  # noqa: BLE001 - recovery reservation is terminal.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="checkpoint_reservation",
            exception=exc,
            finalize_checkpoint=False,
        )
    _CURRENT_INVOCATION_GENERATION.set(invocation_generation)
    stages: list[LatestEpisodeVerifiedResearchReportWorkflowStep] = []
    checkpoint_history: list[dict[str, str]] = []
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning] = []
    try:
        deterministic = _run_pinned_deterministic_workflow(
            normalized_podcast_id,
            canonical_episode_ref,
            filters=CorpusLatestEpisodeDeterministicWorkflowRunFilter(
                transcription_model=filters.transcription_model,
                transcription_device=filters.transcription_device,
                transcription_compute_type=filters.transcription_compute_type,
                transcription_vad_filter=filters.transcription_vad_filter,
            ),
            write_report=False,
        )
    except Exception as exc:  # noqa: BLE001 - deterministic child is bounded here.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="deterministic_processing",
            exception=exc,
            warnings=warnings,
        )
    if deterministic.episode_ref != canonical_episode_ref:
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=True,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome="blocked",
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage_plan=[_step("deterministic_processing", "blocked", "deterministic child identity mismatch")],
        )
    deterministic_status = "completed" if deterministic.outcome == "ready_for_semantic_summary" else deterministic.outcome
    stages.append(_step("deterministic_processing", deterministic_status, "pinned deterministic workflow completed" if deterministic_status == "completed" else "pinned deterministic workflow stopped"))
    checkpoint_history.append({"stage": "deterministic_processing", "status": deterministic_status})
    _record_checkpoint_warning(
        warnings, checkpoint_path, normalized_podcast_id, canonical_episode_ref, checkpoint_history
    )
    if deterministic.outcome != "ready_for_semantic_summary":
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=True,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome=deterministic.outcome,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage_plan=stages,
        )
    try:
        _acquire_canonical_transcript_scope(
            normalized_podcast_id, canonical_episode_ref
        )
    except Exception as exc:  # noqa: BLE001 - selector failure is a bounded gate.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="canonical_transcript",
            exception=exc,
            stages=stages,
            warnings=warnings,
        )

    lineage_current = _lineage_is_current(
        normalized_podcast_id, canonical_episode_ref, filters
    )
    summary_lineage_current = _lineage_roles_are_current(
        normalized_podcast_id,
        canonical_episode_ref,
        filters,
        roles=("semantic_summary",),
    )
    review_lineage_current = _lineage_roles_are_current(
        normalized_podcast_id,
        canonical_episode_ref,
        filters,
        roles=("semantic_review",),
    )
    fresh_summary = False
    fresh_review = False
    try:
        title = _transcript_title(normalized_podcast_id, canonical_episode_ref)
        semantic_state = _semantic_state(normalized_podcast_id, canonical_episode_ref, title)
        if not summary_lineage_current and semantic_state["summary"] in {"available", "missing"}:
            # Existing readable summaries without a direct canonical-transcript
            # binding must be regenerated, not adopted just because the path
            # exists.  A malformed summary remains blocked rather than being
            # relabelled as a safe regeneration candidate.
            semantic_state = {"summary": "missing", "review": "missing"}
        elif not review_lineage_current and semantic_state["review"] == "passed":
            # A summary can remain trusted while an apparently passed review is
            # forged or stale; re-review it without re-sending transcript bytes.
            semantic_state["review"] = "needs_review"
    except Exception as exc:  # noqa: BLE001 - inspection never escapes the workflow.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="inspection",
            exception=exc,
            stages=stages,
            warnings=warnings,
        )

    if semantic_state["summary"] not in {"available", "missing"}:
        stages.append(_step("semantic_summary", "blocked", "semantic summary is unavailable"))
        return _result(
            podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
            checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
        )

    if semantic_state["summary"] == "missing":
        summary_commits: set[str] = set()
        try:
            with _progressive_lineage_scope(
                normalized_podcast_id,
                canonical_episode_ref,
                filters,
                {"semantic_summary": storage.semantic_summary_asset_path(
                    normalized_podcast_id, canonical_episode_ref, title
                )},
                summary_commits,
            ) as record_summary_commit:
                summary_result = run_corpus_semantic_remediation(
                    normalized_podcast_id,
                    episode_ref=canonical_episode_ref,
                    action="semantic_summary",
                    confirm=True,
                    api_cost_ack=api_cost_ack,
                    provider=filters.semantic_provider or "openai-compatible",
                    model=filters.semantic_model,
                    base_url=normalized_semantic_base_url,
                    api_key_env=normalized_semantic_api_key_env,
                    chunk_seconds=filters.semantic_chunk_seconds,
                    max_segments_per_chunk=filters.semantic_max_segments_per_chunk,
                )
        except Exception as exc:  # noqa: BLE001 - child may have written an artifact; resume inspects it.
            return _stage_failure_result(
                podcast_id=normalized_podcast_id,
                episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref,
                filters=filters,
                checkpoint_path=checkpoint_path,
                stage="semantic_summary",
                exception=exc,
                stages=stages,
                warnings=warnings,
            )
        if not _child_identity_matches(summary_result, canonical_episode_ref) or not _child_succeeded(summary_result):
            stages.append(_step("semantic_summary", "failed", "semantic summary child did not complete"))
            return _result(
                podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref, outcome="failed", filters=filters,
                checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
            )
        fresh_summary = _child_generated(summary_result)
        if fresh_summary and "semantic_summary" not in summary_commits:
            # Compatibility for a controlled child implementation that predates
            # the notifier: it may only prove the pre-registered missing path.
            record_summary_commit(
                ChildArtifactCommit(
                    "semantic_summary",
                    storage.semantic_summary_asset_path(
                        normalized_podcast_id, canonical_episode_ref, title
                    ),
                    True,
                    {},
                )
            )
        summary_lineage_current = _lineage_roles_are_current(
            normalized_podcast_id, canonical_episode_ref, filters, roles=("semantic_summary",)
        )
        if not summary_lineage_current or "semantic_summary" not in summary_commits:
            stages.append(_step("semantic_summary", "blocked", "semantic summary lacks controlled generation proof"))
            return _result(
                podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
                checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
            )
        stages.append(_step("semantic_summary", "completed", "semantic summary completed"))
        checkpoint_history.append({"stage": "semantic_summary", "status": "completed"})
        _record_checkpoint_warning(
            warnings, checkpoint_path, normalized_podcast_id, canonical_episode_ref, checkpoint_history
        )
        try:
            semantic_state = _semantic_state(normalized_podcast_id, canonical_episode_ref, title)
        except Exception as exc:  # noqa: BLE001 - post-child inspection is bounded.
            return _stage_failure_result(
                podcast_id=normalized_podcast_id,
                episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref,
                filters=filters,
                checkpoint_path=checkpoint_path,
                stage="inspection",
                exception=exc,
                stages=stages,
                warnings=warnings,
            )
    else:
        stages.append(_step("semantic_summary", "reused", "semantic summary already exists"))

    if semantic_state["summary"] != "available":
        stages[-1] = _step("semantic_summary", "blocked", "semantic summary is unavailable")
        return _result(
            podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
            checkpoint_path=checkpoint_path, stage_plan=stages,
        )

    if semantic_state["review"] in {"missing", "needs_review"}:
        is_authenticity_rereview = semantic_state["review"] == "needs_review"
        review_commits: set[str] = set()
        try:
            with _progressive_lineage_scope(
                normalized_podcast_id,
                canonical_episode_ref,
                filters,
                {"semantic_review": None},
                review_commits,
            ) as record_review_commit:
                if is_authenticity_rereview:
                    review_result = _run_018_authenticity_rereview(
                        normalized_podcast_id, canonical_episode_ref
                    )
                else:
                    review_result = run_corpus_semantic_remediation(
                        normalized_podcast_id,
                        episode_ref=canonical_episode_ref,
                        action="semantic_review",
                        confirm=True,
                    )
        except Exception as exc:  # noqa: BLE001 - safe review child is bounded.
            return _stage_failure_result(
                podcast_id=normalized_podcast_id,
                episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref,
                filters=filters,
                checkpoint_path=checkpoint_path,
                stage="semantic_review",
                exception=exc,
                stages=stages,
                warnings=warnings,
            )
        if not _child_identity_matches(review_result, canonical_episode_ref):
            stages.append(_step("semantic_review", "failed", "semantic review child identity mismatch"))
            return _result(
                podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref, outcome="failed", filters=filters,
                checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
            )
        if is_authenticity_rereview:
            if getattr(review_result, "review_status", None) != "passed":
                stages.append(_step("semantic_review", "blocked", "semantic review did not pass"))
                return _result(
                    podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                    expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
                    checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
                )
        elif not _child_succeeded(review_result):
            child_rows = getattr(review_result, "rows", None)
            child_status = (
                getattr(child_rows[0], "status", None)
                if isinstance(child_rows, list) and child_rows
                else None
            )
            if child_status == "blocked":
                stages.append(_step("semantic_review", "blocked", "semantic review did not pass"))
                return _result(
                    podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                    expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
                    checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
                )
            stages.append(_step("semantic_review", "failed", "semantic review child did not complete"))
            return _result(
                podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref, outcome="failed", filters=filters,
                checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
            )
        if "semantic_review" not in review_commits:
            review_path = getattr(review_result, "review_json_path", None)
            if isinstance(review_path, Path):
                record_review_commit(
                    ChildArtifactCommit("semantic_review", review_path, True, {})
                )
        try:
            semantic_state = _semantic_state(normalized_podcast_id, canonical_episode_ref, title)
        except Exception as exc:  # noqa: BLE001 - post-review inspection is bounded.
            return _stage_failure_result(
                podcast_id=normalized_podcast_id,
                episode_ref=canonical_episode_ref,
                expected_episode_ref=normalized_expected_episode_ref,
                filters=filters,
                checkpoint_path=checkpoint_path,
                stage="inspection",
                exception=exc,
                stages=stages,
                warnings=warnings,
            )
        if semantic_state["review"] == "passed":
            review_lineage_current = _lineage_roles_are_current(
                normalized_podcast_id, canonical_episode_ref, filters, roles=("semantic_review",)
            )
            if not review_lineage_current or "semantic_review" not in review_commits:
                stages.append(_step("semantic_review", "blocked", "semantic review lacks controlled generation proof"))
                return _result(
                    podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
                    expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
                    checkpoint_path=checkpoint_path, stage_plan=stages, warnings=warnings,
                )
            fresh_review = True
            stages.append(_step("semantic_review", "completed", "semantic review passed"))
            checkpoint_history.append({"stage": "semantic_review", "status": "passed"})
            _record_checkpoint_warning(
                warnings, checkpoint_path, normalized_podcast_id, canonical_episode_ref, checkpoint_history
            )
        else:
            stages.append(_step("semantic_review", "blocked", "semantic review did not pass"))
    elif semantic_state["review"] == "passed":
        stages.append(_step("semantic_review", "reused", "semantic review already passed"))
    else:
        stages.append(_step("semantic_review", "blocked", "semantic review did not pass"))

    if semantic_state["review"] != "passed":
        return _result(
            podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
            checkpoint_path=checkpoint_path, stage_plan=stages,
        )

    # A fresh semantic/review record can make an otherwise valid deterministic
    # research chain complete without re-adopting any stale downstream bytes.
    lineage_current = _lineage_is_current(
        normalized_podcast_id, canonical_episode_ref, filters
    )
    research_commits: set[str] = set()
    research_expected_paths = {
        "mentions": storage.mention_asset_paths(
            normalized_podcast_id, canonical_episode_ref, title
        ).json_path,
        "intelligence": storage.episode_intelligence_report_asset_paths(
            normalized_podcast_id, canonical_episode_ref, title
        ).json_path,
        "industry_mapping": storage.industry_chain_mapping_asset_paths(
            normalized_podcast_id, canonical_episode_ref, title
        ).json_path,
        "external_boundary": storage.external_data_boundary_asset_paths(
            normalized_podcast_id, canonical_episode_ref, title
        ).json_path,
    }
    if include_fixture_verification:
        research_expected_paths["fixture"] = research_expected_paths["external_boundary"]
    if normalized_stock_query is not None:
        research_expected_paths["stock_lens"] = storage.stock_lens_report_asset_paths(
            normalized_podcast_id, normalized_stock_query
        ).json_path
    try:
        with _progressive_lineage_scope(
            normalized_podcast_id,
            canonical_episode_ref,
            filters,
            research_expected_paths,
            research_commits,
        ):
            research_result = run_research_workflow(
                normalized_podcast_id,
                canonical_episode_ref,
                stock_query=normalized_stock_query,
                confirm=True,
                force=False,
                allow_partial=False,
                include_semantic_summary=False,
                include_stock_lens_synthesis=False,
                include_external_data_verification=include_fixture_verification,
            )
        research_status = getattr(research_result, "workflow_status", None)
    except Exception as exc:  # noqa: BLE001 - bounded workflow outcome only.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="research",
            exception=exc,
            stages=stages,
            warnings=warnings,
        )
    if research_status != "completed":
        stages.append(_step("research", "blocked", "research workflow did not complete"))
        return _result(
            podcast_id=normalized_podcast_id, confirm=True, episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref, outcome="blocked", filters=filters,
            checkpoint_path=checkpoint_path, stage_plan=stages,
        )
    stages.append(_step("research", "completed", "deterministic research completed"))
    checkpoint_history.append({"stage": "research", "status": "completed"})
    _record_checkpoint_warning(
        warnings, checkpoint_path, normalized_podcast_id, canonical_episode_ref, checkpoint_history
    )
    lineage_current = _lineage_is_current(
        normalized_podcast_id, canonical_episode_ref, filters
    )
    if not lineage_current and not set(research_expected_paths) <= research_commits:
        stages[-1] = _step(
            "research", "blocked", "research artifacts lack controlled current lineage"
        )
        return _result(
            podcast_id=normalized_podcast_id,
            confirm=True,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            outcome="blocked",
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage_plan=stages,
            warnings=warnings,
        )

    try:
        assembly = assemble_verified_research_report(
            normalized_podcast_id,
            canonical_episode_ref,
            stock_query=normalized_stock_query,
            include_fixture_verification=include_fixture_verification,
            summary_options=_summary_lineage_options(filters),
        )
        bundle = publish_verified_research_report_bundle(assembly)
    except Exception as exc:  # noqa: BLE001 - assembly and publication are one terminal boundary.
        return _stage_failure_result(
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            expected_episode_ref=normalized_expected_episode_ref,
            filters=filters,
            checkpoint_path=checkpoint_path,
            stage="publish",
            exception=exc,
            stages=stages,
            warnings=warnings,
        )
    stages.append(_step("publish", "reused" if bundle.reused else "completed", "verified report bundle reused" if bundle.reused else "verified report bundle published"))
    checkpoint_history.append({"stage": "publish", "status": "reused" if bundle.reused else "completed"})
    return _result(
        podcast_id=normalized_podcast_id,
        confirm=True,
        episode_ref=canonical_episode_ref,
        expected_episode_ref=normalized_expected_episode_ref,
        outcome="reused" if bundle.reused else "completed",
        filters=filters,
        checkpoint_path=checkpoint_path,
        stage_plan=stages,
        report_version=bundle.report_version,
        source_digest=bundle.source_digest,
        bundle_dir=bundle.bundle_dir,
        report_json_path=bundle.report_json_path,
        report_markdown_path=bundle.report_markdown_path,
        manifest_path=bundle.manifest_path,
        warnings=warnings,
    )


def _adopt_complete_bundle(
    podcast_id: str,
    episode_ref: str,
    stock_query: str | None,
    include_fixture_verification: bool = False,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter | None = None,
) -> Any | None:
    """Reuse only a full current artifact contract; checkpoint claims never suffice."""

    validation = validate_transcript(podcast_id, episode_ref)
    if validation.status != "valid" or not validation.valid:
        return None
    try:
        transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
        if transcript_paths is None or not all(
            path.is_file()
            for path in (
                transcript_paths.json_path,
                transcript_paths.text_path,
                transcript_paths.srt_path,
            )
        ):
            return None
        # Validate identity before a completed/reused outcome can bypass the 017 ladder.
        _transcript_title(podcast_id, episode_ref)
        if filters is None:
            return None
        assembly = assemble_verified_research_report(
            podcast_id,
            episode_ref,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
            summary_options=_summary_lineage_options(filters),
        )
        return publish_verified_research_report_bundle(assembly)
    except VerifiedResearchReportInputError:
        return None


def result_to_dict(
    result: LatestEpisodeVerifiedResearchReportWorkflowRunResult,
) -> dict[str, Any]:
    """Recursively serialize only JSON-safe, credential-free workflow metadata."""

    return _sanitize_result_value(asdict(result))


def _preview_plan(podcast_id: str, episode_ref: str) -> list[LatestEpisodeVerifiedResearchReportWorkflowStep]:
    report_root = f"data/research-reports/{podcast_id}/{episode_ref}/v1-{{source_digest}}"
    return [
        _step("deterministic_processing", "planned", "reuse pinned deterministic intake, download, transcription, and remediation", planned_reads=["configured podcast RSS feed", "in-memory corpus snapshot"], planned_writes=[f"data/corpus/{podcast_id}/...", f"data/transcripts/{podcast_id}/..."]),
        _step("semantic_summary", "planned", "generate at most one missing semantic summary", requires_ack=True, transfer_risk=True, api_cost_risk=True, planned_reads=[f"data/transcripts/{podcast_id}/{episode_ref}__*.json"], planned_writes=[f"data/summaries/{podcast_id}/{episode_ref}__*.semantic.md"]),
        _step("semantic_review", "planned", "run deterministic semantic review only when missing", planned_writes=["evals/research-llm-smoke/reports/*.semantic-review.json"]),
        _step("research", "planned", "generate deterministic research artifacts with fixed safe options", planned_writes=[f"data/mentions/{podcast_id}/...", f"data/reports/{podcast_id}/...", f"data/mappings/{podcast_id}/...", f"data/external/{podcast_id}/..."]),
        _step("publish", "planned", "atomically publish JSON, Markdown, and manifest bundle", planned_writes=[f"{report_root}/report.json", f"{report_root}/report.md", f"{report_root}/manifest.json", f"data/corpus/{podcast_id}/verified-research/{episode_ref}.checkpoint.json"]),
    ]


def _step(
    stage: str,
    status: str,
    reason: str,
    failure_category: str | None = None,
    *,
    requires_ack: bool = False,
    transfer_risk: bool = False,
    api_cost_risk: bool = False,
    planned_reads: list[str] | None = None,
    planned_writes: list[str] | None = None,
) -> LatestEpisodeVerifiedResearchReportWorkflowStep:
    return LatestEpisodeVerifiedResearchReportWorkflowStep(
        stage=stage, status=status, reason=reason, requires_confirmation=status == "planned",
        requires_api_cost_ack=requires_ack, network_risk=stage == "deterministic_processing",
        local_compute_risk=stage == "deterministic_processing", transcript_transfer_risk=transfer_risk,
        may_incur_api_cost=api_cost_risk, planned_reads=planned_reads or [], planned_writes=planned_writes or [],
        output_paths=[], failure_category=failure_category,
    )


def _result(
    *, podcast_id: str, confirm: bool, episode_ref: str | None, expected_episode_ref: str | None,
    outcome: str, filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    stage_plan: list[LatestEpisodeVerifiedResearchReportWorkflowStep], checkpoint_path: Path | None = None,
    report_version: str | None = None, source_digest: str | None = None, bundle_dir: Path | None = None,
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning] | None = None,
    report_json_path: Path | None = None, report_markdown_path: Path | None = None, manifest_path: Path | None = None,
    approval_boundary_rejected: bool = False,
    finalize_checkpoint: bool = True,
) -> LatestEpisodeVerifiedResearchReportWorkflowRunResult:
    workflow_warnings = warnings if warnings is not None else []
    result = LatestEpisodeVerifiedResearchReportWorkflowRunResult(
        podcast_id=podcast_id, run_mode=_RUN_MODE_CONFIRMED if confirm else _RUN_MODE_DRY_RUN,
        confirm=confirm, selector=DEFAULT_SELECTOR, episode_ref=episode_ref,
        expected_episode_ref=expected_episode_ref, outcome=outcome,
        required_api_cost_ack=SEMANTIC_API_COST_ACK, report_version=report_version,
        source_digest=source_digest, bundle_dir=bundle_dir, report_json_path=report_json_path,
        report_markdown_path=report_markdown_path, manifest_path=manifest_path,
        checkpoint_path=checkpoint_path, filters=filters, stage_plan=stage_plan,
        warnings=workflow_warnings, not_investment_advice=True,
    )
    if finalize_checkpoint:
        _finalize_confirmed_checkpoint(
            result,
            workflow_warnings,
            approval_boundary_rejected=approval_boundary_rejected,
        )
    return result


def _finalize_confirmed_checkpoint(
    result: LatestEpisodeVerifiedResearchReportWorkflowRunResult,
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning],
    *,
    approval_boundary_rejected: bool = False,
) -> None:
    """Persist canonical terminal outcomes, except a pre-write approval rejection."""

    # A latest-reference drift rejects the human approval before an episode is
    # authorized.  It must not create even metadata for either episode.
    if approval_boundary_rejected:
        return
    if (
        not result.confirm
        or result.checkpoint_path is None
        or result.episode_ref is None
        or result.outcome not in _CHECKPOINT_TERMINAL_OUTCOMES - {"in_progress"}
    ):
        return
    history = [
        {"stage": step.stage, "status": step.status}
        for step in result.stage_plan
        if _SAFE_CHECKPOINT_STAGE.fullmatch(step.stage)
        and _SAFE_CHECKPOINT_STATUS.fullmatch(step.status)
    ]
    references = {
        key: str(path)
        for key, path in (
            ("bundle_dir", result.bundle_dir),
            ("report_json_path", result.report_json_path),
            ("report_markdown_path", result.report_markdown_path),
            ("manifest_path", result.manifest_path),
        )
        if path is not None and _safe_checkpoint_reference(str(path))
    }
    _record_checkpoint_warning(
        warnings,
        result.checkpoint_path,
        result.podcast_id,
        result.episode_ref,
        history,
        source_digest=result.source_digest,
        report_version=result.report_version,
        terminal_outcome=result.outcome,
        bundle_references=references or None,
        invocation_generation=_CURRENT_INVOCATION_GENERATION.get(),
    )


def _filters(**values: Any) -> LatestEpisodeVerifiedResearchReportWorkflowRunFilter:
    _require_positive(values["semantic_chunk_seconds"], "semantic_chunk_seconds", maximum=86_400)
    _require_positive(values["semantic_max_segments_per_chunk"], "semantic_max_segments_per_chunk", maximum=10_000)
    provider = _safe_dependency(values["semantic_provider"], "semantic_provider")
    model = _optional_safe_dependency(values["semantic_model"], "semantic_model")
    transcription_model = _optional_safe_dependency(values["transcription_model"], "transcription_model")
    transcription_device = _safe_dependency(values["transcription_device"], "transcription_device")
    transcription_compute_type = _safe_dependency(
        values["transcription_compute_type"], "transcription_compute_type"
    )
    if not isinstance(values["transcription_vad_filter"], bool):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("transcription_vad_filter is invalid")
    if not isinstance(values["include_fixture_verification"], bool):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("include_fixture_verification is invalid")
    return LatestEpisodeVerifiedResearchReportWorkflowRunFilter(
        expected_episode_ref=values["expected_episode_ref"], stock_query=values["stock_query"],
        include_fixture_verification=values["include_fixture_verification"],
        transcription_model=transcription_model, transcription_device=transcription_device,
        transcription_compute_type=transcription_compute_type, transcription_vad_filter=values["transcription_vad_filter"],
        semantic_provider=provider, semantic_model=model,
        semantic_base_url_identity_sha256=_optional_sha256(
            values.get("semantic_base_url_identity_sha256")
        ),
        semantic_chunk_seconds=values["semantic_chunk_seconds"], semantic_max_segments_per_chunk=values["semantic_max_segments_per_chunk"],
    )


def _require_confirmed_approval(expected_episode_ref: str | None, api_cost_ack: str) -> None:
    if expected_episode_ref is None:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("confirmed expected_episode_ref is invalid")
    if api_cost_ack != SEMANTIC_API_COST_ACK:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("confirmed workflow requires exact api_cost_ack")


def _normalize_podcast_id(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_PODCAST_ID.fullmatch(value):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("podcast_id is invalid")
    return value


def _normalize_expected_episode_ref(value: str | None) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not _SAFE_EPISODE_REF.fullmatch(value)
        or value.casefold() == DEFAULT_SELECTOR
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("expected_episode_ref is invalid")
    return value


def _normalize_api_cost_ack(value: object) -> str:
    if not isinstance(value, str) or len(value) > 256 or contains_sensitive_text(value):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("api_cost_ack is invalid")
    return value


def _normalize_stock_query(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SAFE_STOCK_QUERY.fullmatch(value.strip()):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("stock_query is invalid")
    normalized = value.strip()
    if contains_sensitive_text(normalized, reject_any_uri=True):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("stock_query is invalid")
    return normalized


def _normalize_semantic_base_url(value: str | None) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) > 512
        or not _SAFE_BASE_URL.fullmatch(value)
        or contains_sensitive_text(value)
        or "@" in value
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("semantic_base_url is invalid")
    return value


def _semantic_base_url_identity_sha256(value: str | None) -> str | None:
    """Return a non-reversible lineage identity for the selected endpoint."""

    return None if value is None else hashlib.sha256(value.encode("utf-8")).hexdigest()


def _optional_sha256(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "semantic base URL identity is invalid"
        )
    return value


def _normalize_semantic_api_key_env(value: object) -> str:
    if not isinstance(value, str) or not _SAFE_ENVIRONMENT_NAME.fullmatch(value):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("semantic_api_key_env is invalid")
    return value


def _safe_dependency(value: object, name: str) -> str:
    if not isinstance(value, str) or not _SAFE_DEPENDENCY.fullmatch(value):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(f"{name} is invalid")
    lowered = value.lower()
    if contains_sensitive_text(value, reject_any_uri=True) or any(
        fragment in lowered
        for fragment in ("secret", "token", "credential", "password", "private", "authorization", "cookie", "api_key")
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(f"{name} is invalid")
    return value


def _optional_safe_dependency(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _safe_dependency(value, name)


def _require_positive(value: object, name: str, *, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(f"{name} is invalid")


def _transcript_title(podcast_id: str, episode_ref: str) -> str:
    try:
        paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    except CanonicalTranscriptResolutionError as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "canonical transcript is ambiguous"
        ) from exc
    if paths is None:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("transcript is missing")
    try:
        payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("transcript is unreadable") from exc
    if not isinstance(payload, dict) or payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != episode_ref:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("transcript identity mismatch")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError("transcript title is invalid")
    return title


def _semantic_state(podcast_id: str, episode_ref: str, title: str) -> dict[str, str]:
    from .semantic_summary_smoke_review import REPORTS_DIR

    canonical_path = canonical_semantic_summary_path(podcast_id, episode_ref)
    expected_path = storage.semantic_summary_asset_path(podcast_id, episode_ref, title)
    # The title is read and identity-checked by _transcript_title immediately
    # before this call.  Refuse a glob-derived or mismatched summary path.
    if canonical_path is None or canonical_path != expected_path:
        return {"summary": "missing", "review": "missing"}
    inspection = inspect_semantic_review(
        podcast_id,
        episode_ref,
        semantic_summary_path=canonical_path,
        review_reports_dir=REPORTS_DIR,
    )
    return {"summary": inspection.summary_status, "review": inspection.review_status}


def _summary_lineage_options(
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
) -> dict[str, Any]:
    return {
        "summary_mode": "semantic-llm",
        "requested_provider": filters.semantic_provider or "openai-compatible",
        "requested_model": filters.semantic_model,
        "requested_base_url_identity_sha256": filters.semantic_base_url_identity_sha256,
        "requested_chunk_seconds": filters.semantic_chunk_seconds,
        "requested_max_segments_per_chunk": filters.semantic_max_segments_per_chunk,
    }


def _lineage_is_current(
    podcast_id: str,
    episode_ref: str,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
) -> bool:
    return _lineage_roles_are_current(podcast_id, episode_ref, filters, roles=None)


def _lineage_roles_are_current(
    podcast_id: str,
    episode_ref: str,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    *,
    roles: tuple[str, ...] | None,
) -> bool:
    try:
        validate_current_verified_research_lineage(
            podcast_id,
            episode_ref,
            stock_query=filters.stock_query,
            include_fixture_verification=filters.include_fixture_verification,
            summary_options=_summary_lineage_options(filters),
            roles=roles,
            require_generation_proofs=True,
        )
    except VerifiedResearchReportInputError:
        return False
    return True


def _record_lineage_roles(
    podcast_id: str,
    episode_ref: str,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    *,
    roles: tuple[str, ...],
) -> None:
    record_current_verified_research_lineage(
        podcast_id,
        episode_ref,
        stock_query=filters.stock_query,
        include_fixture_verification=filters.include_fixture_verification,
        summary_options=_summary_lineage_options(filters),
        roles=roles,
    )


def _record_full_lineage(
    podcast_id: str,
    episode_ref: str,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
) -> None:
    record_current_verified_research_lineage(
        podcast_id,
        episode_ref,
        stock_query=filters.stock_query,
        include_fixture_verification=filters.include_fixture_verification,
        summary_options=_summary_lineage_options(filters),
    )


@contextmanager
def _progressive_lineage_scope(
    podcast_id: str,
    episode_ref: str,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    expected_paths: dict[str, Path | None],
    committed_roles: set[str],
):
    """Persist each post-commit child proof before later child/report failures."""

    expected = {
        role: (
            _canonical_local_path(path) if path is not None else None,
            _sha256_if_file(path) if path is not None else None,
        )
        for role, path in expected_paths.items()
    }

    def record(commit: ChildArtifactCommit) -> None:
        expectation = expected.get(commit.role)
        if expectation is None:
            raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                "child committed an unexpected verified-report role"
            )
        expected_path, pre_sha256 = expectation
        actual_path = _canonical_local_path(commit.path)
        post_sha256 = _sha256_if_file(commit.path)
        if (expected_path is not None and actual_path != expected_path) or post_sha256 is None:
            raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                "child committed an unexpected verified-report output"
            )
        expected_path = expected_path or actual_path
        if not commit.generated:
            # Reuse is safe only when an earlier controlled generation already
            # validates this exact role.  A child result alone never blesses it.
            if not _lineage_roles_are_current(
                podcast_id, episode_ref, filters, roles=(commit.role,)
            ):
                raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                    "child reused an artifact without current verified lineage"
                )
            committed_roles.add(commit.role)
            return
        in_place_fixture_commit = False
        if pre_sha256 is not None:
            boundary_expectation = expected.get("external_boundary")
            if (
                commit.role != "fixture"
                or boundary_expectation is None
                or boundary_expectation[0] != expected_path
                or boundary_expectation[1] != pre_sha256
            ):
                raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                    "child attempted to bless a preexisting verified-report artifact"
                )
            # Fixture verification is the sole legal in-place writer.  Its marker
            # and immutable snapshot are validated by record_current... before the
            # pair is persisted; no general preexisting generated path is allowed.
            in_place_fixture_commit = True
            roles = ("external_boundary", "fixture")
            proofs = {
                role: {
                    "expected_path": expected_path,
                    "pre_sha256": pre_sha256,
                    "post_sha256": post_sha256,
                    "execution": "generated",
                }
                for role in roles
            }
        else:
            proofs = {
                commit.role: {
                    "expected_path": expected_path,
                    "pre_sha256": None,
                    "post_sha256": post_sha256,
                    "execution": "generated",
                }
            }
            roles = (commit.role,)
            if commit.role == "fixture":
                boundary_expectation = expected.get("external_boundary")
                if boundary_expectation is None or boundary_expectation[0] != expected_path:
                    raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                        "fixture committed without its paired external boundary output"
                    )
                # A fresh boundary is also overwritten by the fixture verifier;
                # persist both post-commit entries even though neither path existed
                # when this scope began.
                in_place_fixture_commit = True
                roles = ("external_boundary", "fixture")
                proofs = {
                    role: {
                        "expected_path": expected_path,
                        "pre_sha256": None,
                        "post_sha256": post_sha256,
                        "execution": "generated",
                    }
                    for role in roles
                }
        if commit.role == "semantic_summary":
            # The transcript root is selected independently by the corpus seed,
            # not by the sidecar being written.
            transcript_paths = resolve_canonical_transcript_asset_paths(
                podcast_id, episode_ref
            )
            if transcript_paths is None:
                raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                    "canonical transcript is missing"
                )
            transcript_sha256 = _sha256_if_file(transcript_paths.json_path)
            if transcript_sha256 is None:
                raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                    "canonical transcript is unreadable"
                )
            proofs["transcript"] = {
                "expected_path": _canonical_local_path(transcript_paths.json_path),
                "pre_sha256": None,
                "post_sha256": transcript_sha256,
                "execution": "external_selector",
            }
            roles = ("transcript", "semantic_summary")
        record_current_verified_research_lineage(
            podcast_id,
            episode_ref,
            stock_query=filters.stock_query,
            include_fixture_verification=filters.include_fixture_verification,
            summary_options=_summary_lineage_options_from_commit(filters, commit),
            roles=roles,
            generation_proofs=proofs,
        )
        if in_place_fixture_commit:
            committed_roles.update(roles)
        else:
            committed_roles.add(commit.role)

    with controlled_child_commit_scope(record):
        yield record


def _summary_lineage_options_from_commit(
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    commit: ChildArtifactCommit,
) -> dict[str, Any]:
    """Keep caller-selected request identity immutable across child metadata."""

    del commit
    return _summary_lineage_options(filters)


def _canonical_local_path(path: Path) -> str:
    return path.resolve(strict=False).as_posix()


def _sha256_if_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _research_generated_current_lineage(
    result: object,
    *,
    include_fixture_verification: bool,
    stock_query: str | None,
) -> bool:
    """Only a fresh all-stage research result may bootstrap missing lineage."""

    expected = {
        "extract_mentions",
        "generate_episode_intelligence_report",
        "generate_industry_chain_mapping",
        "generate_external_data_boundary",
    }
    if include_fixture_verification:
        expected.add("verify_external_data_boundary")
    if stock_query is not None:
        expected.add("generate_stock_lens_report")
    steps = getattr(result, "steps", None)
    if not isinstance(steps, list):
        return False
    statuses = {getattr(step, "name", None): getattr(step, "status", None) for step in steps}
    return all(statuses.get(name) == "completed" for name in expected)


def _run_018_authenticity_rereview(podcast_id: str, episode_ref: str) -> Any:
    """Repair stale or forged review provenance without widening 015/016 selection."""

    from .semantic_summary_smoke_review import review_semantic_summary_smoke

    return review_semantic_summary_smoke(podcast_id, episode_ref)


def _child_identity_matches(result: object, episode_ref: str) -> bool:
    return getattr(result, "episode_ref", None) == episode_ref


def _child_succeeded(result: object) -> bool:
    rows = getattr(result, "rows", None)
    if not isinstance(rows, list) or not rows:
        return False
    return getattr(rows[0], "status", None) in {"executed", "reused"}


def _child_generated(result: object) -> bool:
    rows = getattr(result, "rows", None)
    return isinstance(rows, list) and bool(rows) and getattr(rows[0], "status", None) == "executed"


def _stage_failure_result(
    *,
    podcast_id: str,
    episode_ref: str,
    expected_episode_ref: str | None,
    filters: LatestEpisodeVerifiedResearchReportWorkflowRunFilter,
    checkpoint_path: Path,
    stage: str,
    exception: Exception,
    stages: list[LatestEpisodeVerifiedResearchReportWorkflowStep] | None = None,
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning] | None = None,
    finalize_checkpoint: bool = True,
) -> LatestEpisodeVerifiedResearchReportWorkflowRunResult:
    stage_plan = list(stages or [])
    stage_plan.append(
        _step(stage, "failed", f"{stage.replace('_', ' ')} stage failed", _safe_failure_category(exception))
    )
    workflow_warnings = warnings if warnings is not None else []
    return _result(
        podcast_id=podcast_id,
        confirm=True,
        episode_ref=episode_ref,
        expected_episode_ref=expected_episode_ref,
        outcome="failed",
        filters=filters,
        checkpoint_path=checkpoint_path,
        stage_plan=stage_plan,
        warnings=workflow_warnings,
        finalize_checkpoint=finalize_checkpoint,
    )


def _safe_failure_category(exception: Exception) -> str:
    category = type(exception).__name__
    return category if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", category) else "workflow_dependency_error"


def _record_checkpoint_warning(
    warnings: list[LatestEpisodeVerifiedResearchReportWorkflowWarning],
    path: Path,
    podcast_id: str,
    episode_ref: str,
    history: list[dict[str, str]],
    *,
    source_digest: str | None = None,
    report_version: str | None = None,
    terminal_outcome: str = "in_progress",
    bundle_references: dict[str, str] | None = None,
    invocation_generation: int | None = None,
) -> None:
    try:
        _write_checkpoint(
            path,
            podcast_id,
            episode_ref,
            history,
            source_digest=source_digest,
            report_version=report_version,
            terminal_outcome=terminal_outcome,
            bundle_references=bundle_references,
            invocation_generation=(
                invocation_generation
                if invocation_generation is not None
                else _CURRENT_INVOCATION_GENERATION.get()
            ),
        )
    except Exception:  # noqa: BLE001 - checkpoint persistence is always non-fatal metadata.
        warnings.append(
            LatestEpisodeVerifiedResearchReportWorkflowWarning(
                scope="checkpoint",
                episode_ref=episode_ref,
                message=(
                    "verified report bundle published but checkpoint update failed"
                    if bundle_references is not None
                    else "verified research checkpoint update failed"
                ),
            )
        )


def _bundle_references(bundle: Any) -> dict[str, str]:
    references = {
        "bundle_dir": str(bundle.bundle_dir),
        "report_json_path": str(bundle.report_json_path),
        "report_markdown_path": str(bundle.report_markdown_path),
        "manifest_path": str(bundle.manifest_path),
    }
    return {
        key: value
        for key, value in references.items()
        if _safe_checkpoint_reference(value)
    }


def _read_checkpoint(path: Path, podcast_id: str, episode_ref: str) -> dict[str, Any]:
    if not path.exists():
        return _empty_checkpoint()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint is unreadable"
        ) from exc
    if not isinstance(payload, dict):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint is invalid"
        )
    if (
        payload.get("schema_version") != REPORT_SCHEMA_VERSION
        or payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or payload.get("not_investment_advice") is not True
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint identity is invalid"
        )
    history = _validated_checkpoint_history(payload.get("stage_history"))
    terminal_outcome = payload.get("terminal_outcome", "in_progress")
    if terminal_outcome not in _CHECKPOINT_TERMINAL_OUTCOMES:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint outcome is invalid"
        )
    source_digest = payload.get("source_digest")
    if source_digest is not None and (
        not isinstance(source_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", source_digest)
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint source digest is invalid"
        )
    report_version = payload.get("report_version")
    if report_version is not None and (
        not isinstance(report_version, str)
        or not re.fullmatch(r"v1-[a-f0-9]{64}", report_version)
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint report version is invalid"
        )
    # Generation fields are additive.  Checkpoints written before generation
    # reservation are accepted as generation zero and retain their bundle truth.
    invocation_generation = payload.get("invocation_generation", 0)
    if (
        not isinstance(invocation_generation, int)
        or isinstance(invocation_generation, bool)
        or invocation_generation < 0
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint invocation generation is invalid"
        )
    successful_invocation_generation = payload.get("successful_invocation_generation")
    if successful_invocation_generation is not None and (
        not isinstance(successful_invocation_generation, int)
        or isinstance(successful_invocation_generation, bool)
        or not 1 <= successful_invocation_generation <= invocation_generation
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint successful generation is invalid"
        )
    references = payload.get("bundle_references", {})
    if not isinstance(references, dict) or len(references) > 4 or any(
        key not in {"bundle_dir", "report_json_path", "report_markdown_path", "manifest_path"}
        or not _safe_checkpoint_reference(value)
        for key, value in references.items()
    ):
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint bundle references are invalid"
        )
    return {
        "stage_history": history,
        "source_digest": source_digest,
        "report_version": report_version,
        "terminal_outcome": terminal_outcome,
        "bundle_references": dict(references),
        "invocation_generation": invocation_generation,
        "successful_invocation_generation": successful_invocation_generation,
    }


def _empty_checkpoint() -> dict[str, Any]:
    """Return a source-free checkpoint state after absence or safe recovery."""

    return {
        "stage_history": [],
        "source_digest": None,
        "report_version": None,
        "terminal_outcome": "in_progress",
        "bundle_references": {},
        "invocation_generation": 0,
        "successful_invocation_generation": None,
    }


def _validated_checkpoint_history(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > 32:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint history is invalid"
        )
    history: list[dict[str, str]] = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {"stage", "status"}
            or not isinstance(item.get("stage"), str)
            or not isinstance(item.get("status"), str)
            or not _SAFE_CHECKPOINT_STAGE.fullmatch(item["stage"])
            or not _SAFE_CHECKPOINT_STATUS.fullmatch(item["status"])
        ):
            raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
                "verified research checkpoint history is invalid"
            )
        normalized = {"stage": item["stage"], "status": item["status"]}
        if normalized not in history:
            history.append(normalized)
    return history


def _merge_checkpoint_history(
    persisted: list[dict[str, str]], current: list[dict[str, str]]
) -> list[dict[str, str]]:
    merged = list(persisted)
    for item in _validated_checkpoint_history(current):
        if item not in merged:
            merged.append(item)
    return merged[-32:]


def _checkpoint_has_successful_bundle(checkpoint: dict[str, Any]) -> bool:
    return (
        checkpoint["terminal_outcome"] in {"completed", "reused"}
        and checkpoint["source_digest"] is not None
        and checkpoint["report_version"] is not None
        and bool(checkpoint["bundle_references"])
    )


def _safe_checkpoint_reference(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(_SAFE_CHECKPOINT_PATH.fullmatch(value))
        and "?" not in value
        and "#" not in value
        and not contains_sensitive_text(value)
        and not any(fragment in value.lower() for fragment in ("credential", "secret", "token", "password", ".env"))
    )


def _reserve_invocation_generation(path: Path, podcast_id: str, episode_ref: str) -> int:
    """Atomically reserve the next episode-local generation after approval drift passes."""

    claim_path = path.with_name(f".{path.name}.checkpoint.claim")
    try:
        with exclusive_artifact_claim(claim_path):
            try:
                persisted = _read_checkpoint(path, podcast_id, episode_ref)
            except LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError:
                # Checkpoints are untrusted metadata.  A claimed invocation may
                # safely replace corrupt/identity-bad bytes with source-free
                # generation-zero state; no old references or history survive.
                persisted = _empty_checkpoint()
            generation = persisted["invocation_generation"] + 1
            _write_checkpoint_locked(
                path,
                podcast_id,
                episode_ref,
                [],
                invocation_generation=generation,
                reserve_generation=True,
                persisted_override=persisted,
            )
            return generation
    except TimeoutError as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint generation reservation failed: TimeoutError"
        ) from exc


def _write_checkpoint(
    path: Path,
    podcast_id: str,
    episode_ref: str,
    history: list[dict[str, str]],
    *,
    source_digest: str | None = None,
    report_version: str | None = None,
    terminal_outcome: str = "in_progress",
    bundle_references: dict[str, str] | None = None,
    invocation_generation: int | None = None,
) -> None:
    """Serialize read/validate/merge/replace under an episode-scoped file claim."""

    claim_path = path.with_name(f".{path.name}.checkpoint.claim")
    try:
        with exclusive_artifact_claim(claim_path):
            _write_checkpoint_locked(
                path,
                podcast_id,
                episode_ref,
                history,
                source_digest=source_digest,
                report_version=report_version,
                terminal_outcome=terminal_outcome,
                bundle_references=bundle_references,
                invocation_generation=invocation_generation,
            )
    except TimeoutError as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            "verified research checkpoint write failed: TimeoutError"
        ) from exc


def _write_checkpoint_locked(
    path: Path,
    podcast_id: str,
    episode_ref: str,
    history: list[dict[str, str]],
    *,
    source_digest: str | None = None,
    report_version: str | None = None,
    terminal_outcome: str = "in_progress",
    bundle_references: dict[str, str] | None = None,
    invocation_generation: int | None = None,
    reserve_generation: bool = False,
    persisted_override: dict[str, Any] | None = None,
) -> None:
    try:
        persisted = (
            dict(persisted_override)
            if persisted_override is not None
            else _read_checkpoint(path, podcast_id, episode_ref)
        )
        if terminal_outcome not in _CHECKPOINT_TERMINAL_OUTCOMES:
            raise ValueError("terminal outcome")
        if invocation_generation is not None and (
            not isinstance(invocation_generation, int)
            or isinstance(invocation_generation, bool)
            or invocation_generation < 1
        ):
            raise ValueError("invocation generation")
        persisted_generation = persisted["invocation_generation"]
        if reserve_generation:
            if invocation_generation != persisted_generation + 1:
                raise ValueError("generation reservation")
            effective_invocation_generation = invocation_generation
        else:
            if invocation_generation is not None and invocation_generation > persisted_generation:
                raise ValueError("unreserved invocation generation")
            effective_invocation_generation = persisted_generation
        persisted_success = _checkpoint_has_successful_bundle(persisted)
        incoming_success = (
            terminal_outcome in {"completed", "reused"}
            and source_digest is not None
            and report_version is not None
            and bool(bundle_references)
        )
        persisted_success_generation = persisted["successful_invocation_generation"]
        preserve_persisted_success = persisted_success and (
            not incoming_success
            # Legacy writers lack a reserved generation and cannot supersede a
            # generation-aware successful bundle.  A smaller generation is stale.
            or invocation_generation is None
            or (
                persisted_success_generation is not None
                and persisted_success_generation >= invocation_generation
            )
        )
        # This read/compare/write executes beneath the per-episode OS claim.
        # A late invocation can merge stage history, but a completed newer
        # invocation remains the authoritative bundle checkpoint.
        if preserve_persisted_success:
            effective_terminal_outcome = persisted["terminal_outcome"]
            effective_source_digest = persisted["source_digest"]
            effective_report_version = persisted["report_version"]
            references = dict(persisted["bundle_references"])
            effective_successful_generation = persisted_success_generation
        else:
            effective_terminal_outcome = terminal_outcome
            effective_source_digest = (
                source_digest if source_digest is not None else persisted["source_digest"]
            )
            effective_report_version = (
                report_version if report_version is not None else persisted["report_version"]
            )
            references = (
                dict(bundle_references)
                if isinstance(bundle_references, dict) and bundle_references
                else dict(persisted["bundle_references"])
            )
            effective_successful_generation = (
                invocation_generation if incoming_success else persisted_success_generation
            )
        if effective_source_digest is not None and not re.fullmatch(r"[a-f0-9]{64}", effective_source_digest):
            raise ValueError("source digest")
        if effective_report_version is not None and not re.fullmatch(r"v1-[a-f0-9]{64}", effective_report_version):
            raise ValueError("report version")
        if not isinstance(references, dict) or len(references) > 4 or any(
            key not in {"bundle_dir", "report_json_path", "report_markdown_path", "manifest_path"}
            or not _safe_checkpoint_reference(value)
            for key, value in references.items()
        ):
            raise ValueError("bundle references")
        payload = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "stage_history": _merge_checkpoint_history(persisted["stage_history"], history),
            "source_digest": effective_source_digest,
            "report_version": effective_report_version,
            "terminal_outcome": effective_terminal_outcome,
            "bundle_references": dict(references),
            "invocation_generation": effective_invocation_generation,
            "successful_invocation_generation": effective_successful_generation,
            "not_investment_advice": True,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        part_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
        try:
            part_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            part_path.replace(path)
        finally:
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
    except LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError(
            f"verified research checkpoint write failed: {_safe_failure_category(exc)}"
        ) from exc


def _sanitize_result_value(value: Any) -> Any:
    if isinstance(value, Path):
        return _safe_result_path(value)
    if is_dataclass(value):
        return _sanitize_result_value(asdict(value))
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if value == value and value not in {float("inf"), float("-inf")} else None
    if isinstance(value, str):
        return safe_text(value, maximum_length=1024)
    if isinstance(value, list) or isinstance(value, tuple):
        return [_sanitize_result_value(item) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or is_sensitive_key(key):
                continue
            safe_key = safe_text(key, maximum_length=128)
            if safe_key != OMITTED_VALUE:
                sanitized[safe_key] = _sanitize_result_value(item)
        return sanitized
    return None


def _safe_result_path(path: Path) -> str | None:
    value = str(path)
    return value if _safe_checkpoint_reference(value) else None
