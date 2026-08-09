from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, replace
import json
from pathlib import Path
import re

from . import storage
from .audit_report_pair import write_atomic_audit_report_pair
from .episode_claim import episode_writer_claimed
from .corpus_audio_download_runner import run_corpus_audio_download
from .corpus_episode_intake import run_corpus_episode_intake
from .corpus_episode_workflow_runner import (
    _preview_corpus_episode_workflow_from_snapshot,
)
from .corpus_index import _build_corpus_index_snapshot
from .corpus_local_transcription_runner import run_corpus_local_transcription
from .corpus_remediation_plan import _build_corpus_remediation_plan_snapshot
from .corpus_remediation_runner import run_corpus_remediation
from .corpus_semantic_remediation_runner import (
    SEMANTIC_API_COST_ACK,
    _preview_corpus_semantic_remediation_from_snapshot,
    run_corpus_semantic_remediation,
)
from .errors import CorpusEpisodeCompletionWorkflowRunnerFailedError
from .path_safety import is_safe_local_path_structure
from .models import (
    CorpusEpisodeCompletionWorkflowRunCounts,
    CorpusEpisodeCompletionWorkflowRunFilter,
    CorpusEpisodeCompletionWorkflowRunResult,
    CorpusEpisodeCompletionWorkflowRunRow,
    CorpusEpisodeCompletionWorkflowRunWarning,
)


DEFAULT_SELECTOR = "latest"
ACTION_NEXT = "next"
ACTION_INTAKE = "intake"
ACTION_AUDIO_DOWNLOAD = "audio_download"
ACTION_LOCAL_TRANSCRIPTION = "local_transcription"
ACTION_DETERMINISTIC_REMEDIATION = "deterministic_remediation"
ACTION_SEMANTIC_SUMMARY = "semantic_summary"
ACTION_SEMANTIC_REVIEW = "semantic_review"
ACTION_COMPLETED = "completed"
ACTION_BLOCKED = "blocked"
RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
DEFAULT_SEMANTIC_CHUNK_SECONDS = 600
DEFAULT_SEMANTIC_MAX_SEGMENTS_PER_CHUNK = 120
_SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SAFE_PROVIDER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SAFE_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SAFE_ENVIRONMENT_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
_SAFE_BASE_URL_PATTERN = re.compile(
    r"^https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?(?:/[A-Za-z0-9._~/-]*)?$"
)
_ALLOWED_PLANNED_READS = {"configured podcast RSS feed", "in-memory corpus snapshot"}
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "http://",
    "https://",
    "?token",
    "token=",
    "token",
    "api_key",
    "secret",
    "bearer",
    "raw transcript",
    "semantic body",
    "prompt text",
    "raw response",
    "raw llm output",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
    "buy-",
    "sell-",
    "target-price",
    "guaranteed-return",
    "you should buy",
    "you should sell",
)
_QUERY_PATTERN = re.compile(r"\?[^\s|]+")
_REQUESTED_ACTIONS = {
    ACTION_NEXT,
    ACTION_INTAKE,
    ACTION_AUDIO_DOWNLOAD,
    ACTION_LOCAL_TRANSCRIPTION,
    ACTION_DETERMINISTIC_REMEDIATION,
    ACTION_SEMANTIC_SUMMARY,
    ACTION_SEMANTIC_REVIEW,
}


def run_corpus_episode_completion_workflow(
    podcast_id: str,
    *,
    episode_ref: str = DEFAULT_SELECTOR,
    action: str = ACTION_NEXT,
    confirm: bool = False,
    api_cost_ack: str = "",
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
    progress_callback: Callable[..., None] | None = None,
) -> CorpusEpisodeCompletionWorkflowRunResult:
    """Preview or execute one human-approved completion workflow action."""

    normalized_podcast_id = _normalize_podcast_id(podcast_id)
    selector = _normalize_selector(episode_ref)
    requested_action = _normalize_action(action)
    if requested_action == ACTION_SEMANTIC_SUMMARY:
        _validate_semantic_summary_settings(
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
        )
    if confirm:
        _require_confirmed_request(
            selector=selector,
            action=requested_action,
            api_cost_ack=api_cost_ack,
        )

    row, selected_action, canonical_episode_ref, warnings = _preview_selection(
        normalized_podcast_id,
        selector,
    )
    if selected_action == ACTION_SEMANTIC_SUMMARY and requested_action == ACTION_NEXT:
        _validate_semantic_summary_settings(
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
        )
    if confirm:
        if selected_action in {ACTION_BLOCKED, ACTION_COMPLETED}:
            return _build_result(
                podcast_id=normalized_podcast_id,
                selector=selector,
                episode_ref=canonical_episode_ref,
                requested_action=requested_action,
                selected_action=selected_action,
                confirm=True,
                row=row,
                warnings=warnings,
                transcription_model=transcription_model,
                transcription_device=transcription_device,
                transcription_compute_type=transcription_compute_type,
                transcription_vad_filter=transcription_vad_filter,
                semantic_provider=semantic_provider,
                semantic_model=semantic_model,
                semantic_chunk_seconds=semantic_chunk_seconds,
                semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            )
        if requested_action != selected_action:
            row = replace(
                row,
                status="rejected",
                reason="requested action does not match fresh selection",
                requires_confirmation=False,
            )
            return _build_result(
                podcast_id=normalized_podcast_id,
                selector=selector,
                episode_ref=canonical_episode_ref,
                requested_action=requested_action,
                selected_action=selected_action,
                confirm=True,
                row=row,
                warnings=warnings,
                transcription_model=transcription_model,
                transcription_device=transcription_device,
                transcription_compute_type=transcription_compute_type,
                transcription_vad_filter=transcription_vad_filter,
                semantic_provider=semantic_provider,
                semantic_model=semantic_model,
                semantic_chunk_seconds=semantic_chunk_seconds,
                semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            )
        if canonical_episode_ref is None:
            row = replace(
                row,
                action=ACTION_BLOCKED,
                status="rejected",
                reason="confirmed episode is unavailable",
                requires_confirmation=False,
                manual_only=True,
            )
            return _build_result(
                podcast_id=normalized_podcast_id,
                selector=selector,
                episode_ref=None,
                requested_action=requested_action,
                selected_action=selected_action,
                confirm=True,
                row=row,
                warnings=warnings,
                transcription_model=transcription_model,
                transcription_device=transcription_device,
                transcription_compute_type=transcription_compute_type,
                transcription_vad_filter=transcription_vad_filter,
                semantic_provider=semantic_provider,
                semantic_model=semantic_model,
                semantic_chunk_seconds=semantic_chunk_seconds,
                semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            )
        executed_row = _execute_confirmed_action(
            selected_row=row,
            selected_action=selected_action,
            podcast_id=normalized_podcast_id,
            episode_ref=canonical_episode_ref,
            api_cost_ack=api_cost_ack,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            progress_callback=progress_callback,
        )
        confirmed_warnings = [
            *warnings,
            *_confirmed_warnings(canonical_episode_ref),
        ]
        report_paths = storage.corpus_episode_completion_workflow_run_asset_paths(
            normalized_podcast_id
        )
        result = _build_result(
            podcast_id=normalized_podcast_id,
            selector=selector,
            episode_ref=canonical_episode_ref,
            requested_action=requested_action,
            selected_action=selected_action,
            confirm=True,
            row=executed_row,
            warnings=confirmed_warnings,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            executed_action=selected_action,
            report_json_path=report_paths.json_path,
            report_markdown_path=report_paths.markdown_path,
        )
        _write_run_report(result)
        return result
    return _build_result(
        podcast_id=normalized_podcast_id,
        selector=selector,
        episode_ref=canonical_episode_ref,
        requested_action=requested_action,
        selected_action=selected_action,
        confirm=False,
        row=row,
        warnings=warnings,
        transcription_model=transcription_model,
        transcription_device=transcription_device,
        transcription_compute_type=transcription_compute_type,
        transcription_vad_filter=transcription_vad_filter,
        semantic_provider=semantic_provider,
        semantic_model=semantic_model,
        semantic_chunk_seconds=semantic_chunk_seconds,
        semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
    )


def result_to_dict(result: CorpusEpisodeCompletionWorkflowRunResult) -> dict[str, object]:
    """Serialize a completion workflow result into bounded JSON metadata."""

    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    counts = payload.pop("counts")
    if isinstance(counts, dict):
        payload.update(counts)
    return _sanitize_payload(payload)


def _write_run_report(result: CorpusEpisodeCompletionWorkflowRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    try:
        write_atomic_audit_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            payload,
            _render_markdown(payload),
        )
    except OSError as exc:
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError(
            "failed to write completion workflow report: "
            f"{type(exc).__name__}"
        ) from exc


def _render_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# Corpus Episode Completion Workflow - {_markdown_cell(payload.get('podcast_id'))}",
        "",
        "## Summary",
        "",
        f"- Run mode: {_markdown_cell(payload.get('run_mode'))}",
        f"- Episode: {_markdown_cell(payload.get('episode_ref'))}",
        f"- Requested action: {_markdown_cell(payload.get('requested_action'))}",
        f"- Selected action: {_markdown_cell(payload.get('selected_action'))}",
        f"- Executed action: {_markdown_cell(payload.get('executed_action'))}",
        "",
        "## Outcome",
        "",
        "| Action | Status | Reason |",
        "| --- | --- | --- |",
    ]
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    (
                        _markdown_cell(row.get("action")),
                        _markdown_cell(row.get("status")),
                        _markdown_cell(row.get("reason")),
                    )
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Boundary Notice",
            "",
            "This report contains bounded local workflow metadata only. It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_cell(value: object) -> str:
    if not isinstance(value, str):
        return "none" if value is None else _safe_output_text(str(value))
    return _safe_output_text(value).replace("|", "\\|").replace("\n", " ")


def _preview_selection(
    podcast_id: str,
    selector: str,
) -> tuple[
    CorpusEpisodeCompletionWorkflowRunRow,
    str,
    str | None,
    list[CorpusEpisodeCompletionWorkflowRunWarning],
]:
    try:
        intake_result = run_corpus_episode_intake(
            podcast_id,
            episode_ref=selector,
            confirm=False,
        )
    except Exception as exc:  # noqa: BLE001 - retain a bounded dry-run result.
        return _blocked_row(
            episode_ref=None,
            status="failed",
            reason="episode selector inspection failed",
            failure_category=_safe_exception_category(type(exc).__name__),
        ), ACTION_BLOCKED, None, []

    canonical_episode_ref = _safe_episode_ref(
        getattr(intake_result, "resolved_episode_ref", None)
    )
    if canonical_episode_ref is None:
        return _blocked_row(
            episode_ref=None,
            status="blocked",
            reason="episode selector could not be resolved",
        ), ACTION_BLOCKED, None, []

    if not storage.corpus_episode_seed_asset_path(
        podcast_id,
        canonical_episode_ref,
    ).exists():
        intake_row = _first_row(intake_result)
        return (
        CorpusEpisodeCompletionWorkflowRunRow(
            episode_ref=canonical_episode_ref,
            action=ACTION_INTAKE,
            status="selected",
            reason="episode seed metadata is missing",
            requires_confirmation=True,
            requires_api_cost_ack=False,
            network_risk=True,
            local_compute_risk=False,
            transcript_transfer_risk=False,
            may_incur_api_cost=False,
            manual_only=False,
            planned_reads=_safe_planned_reads(
                getattr(intake_row, "planned_reads", [])
            ),
            planned_writes=_safe_string_list(
                getattr(intake_row, "planned_writes", [])
            ),
            output_paths=[],
            source_report_paths=[],
            stage_counts={},
            provider=None,
            model=None,
            failure_category=None,
            warnings=[],
        ),
            ACTION_INTAKE,
            canonical_episode_ref,
            [],
        )

    try:
        index_snapshot = _build_corpus_index_snapshot(podcast_id)
        plan_snapshot = _build_corpus_remediation_plan_snapshot(
            podcast_id,
            index_result=index_snapshot.result,
            index_payload=index_snapshot.payload,
        )
    except Exception as exc:  # noqa: BLE001 - fresh snapshot failures are bounded.
        return _blocked_row(
            episode_ref=canonical_episode_ref,
            status="failed",
            reason="corpus snapshot evaluation failed",
            failure_category=_safe_exception_category(type(exc).__name__),
        ), ACTION_BLOCKED, canonical_episode_ref, []

    try:
        deterministic = _preview_corpus_episode_workflow_from_snapshot(
            podcast_id,
            episode_ref=canonical_episode_ref,
            plan_result=plan_snapshot.result,
            plan_payload=plan_snapshot.payload,
            max_actions=1,
            allow_semantic_handoff=True,
        )
    except Exception as exc:  # noqa: BLE001 - private preview remains fail-closed.
        return _blocked_row(
            episode_ref=canonical_episode_ref,
            status="failed",
            reason="workflow stage inspection failed",
            failure_category=_safe_exception_category(type(exc).__name__),
        ), ACTION_BLOCKED, canonical_episode_ref, []

    selected_stage = deterministic.get("selected_stage")
    source_row = _first_row_from_mapping(deterministic)
    if selected_stage in {
        ACTION_AUDIO_DOWNLOAD,
        ACTION_LOCAL_TRANSCRIPTION,
        ACTION_DETERMINISTIC_REMEDIATION,
    }:
        return (
            _row_from_stage(
                episode_ref=canonical_episode_ref,
                action=selected_stage,
                source_row=source_row,
            ),
            selected_stage,
            canonical_episode_ref,
            [],
        )
    if selected_stage != ACTION_COMPLETED:
        return (
            _blocked_row_from_source(
                episode_ref=canonical_episode_ref,
                source_row=source_row,
            ),
            ACTION_BLOCKED,
            canonical_episode_ref,
            [],
        )

    try:
        semantic_row, semantic_action, _semantic_warnings = (
            _preview_corpus_semantic_remediation_from_snapshot(
                podcast_id,
                canonical_episode_ref,
                plan_payload=plan_snapshot.payload,
            )
        )
    except Exception as exc:  # noqa: BLE001 - semantic inspection is bounded.
        return _blocked_row(
            episode_ref=canonical_episode_ref,
            status="failed",
            reason="semantic stage inspection failed",
            failure_category=_safe_exception_category(type(exc).__name__),
        ), ACTION_BLOCKED, canonical_episode_ref, []

    if semantic_action in {ACTION_SEMANTIC_SUMMARY, ACTION_SEMANTIC_REVIEW}:
        return (
            _row_from_semantic(
                episode_ref=canonical_episode_ref,
                action=semantic_action,
                source_row=semantic_row,
            ),
            semantic_action,
            canonical_episode_ref,
            [],
        )
    if semantic_action == ACTION_COMPLETED:
        return (
            _completed_row(canonical_episode_ref, semantic_row),
            ACTION_COMPLETED,
            canonical_episode_ref,
            [],
        )
    return (
        _blocked_row_from_source(
            episode_ref=canonical_episode_ref,
            source_row=semantic_row,
        ),
        ACTION_BLOCKED,
        canonical_episode_ref,
        [],
    )


@episode_writer_claimed
def _execute_confirmed_action(
    *,
    selected_row: CorpusEpisodeCompletionWorkflowRunRow,
    selected_action: str,
    podcast_id: str,
    episode_ref: str,
    api_cost_ack: str,
    transcription_model: str | None,
    transcription_device: str,
    transcription_compute_type: str,
    transcription_vad_filter: bool,
    semantic_provider: str,
    semantic_model: str | None,
    semantic_base_url: str | None,
    semantic_api_key_env: str,
    semantic_chunk_seconds: int,
    semantic_max_segments_per_chunk: int,
    progress_callback: Callable[..., None] | None,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    try:
        if selected_action == ACTION_INTAKE:
            source_result = run_corpus_episode_intake(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
            )
        elif selected_action == ACTION_AUDIO_DOWNLOAD:
            source_result = run_corpus_audio_download(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
            )
        elif selected_action == ACTION_LOCAL_TRANSCRIPTION:
            source_result = run_corpus_local_transcription(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
                model=transcription_model,
                device=transcription_device,
                compute_type=transcription_compute_type,
                vad_filter=transcription_vad_filter,
            )
        elif selected_action == ACTION_DETERMINISTIC_REMEDIATION:
            source_result = run_corpus_remediation(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
                max_actions=1,
            )
        elif selected_action == ACTION_SEMANTIC_SUMMARY:
            source_result = run_corpus_semantic_remediation(
                podcast_id,
                episode_ref=episode_ref,
                action=ACTION_SEMANTIC_SUMMARY,
                confirm=True,
                api_cost_ack=api_cost_ack,
                provider=semantic_provider,
                model=semantic_model,
                base_url=semantic_base_url,
                api_key_env=semantic_api_key_env,
                chunk_seconds=semantic_chunk_seconds,
                max_segments_per_chunk=semantic_max_segments_per_chunk,
                progress_callback=progress_callback,
            )
        elif selected_action == ACTION_SEMANTIC_REVIEW:
            source_result = run_corpus_semantic_remediation(
                podcast_id,
                episode_ref=episode_ref,
                action=ACTION_SEMANTIC_REVIEW,
                confirm=True,
            )
        else:
            return replace(
                selected_row,
                action=ACTION_BLOCKED,
                status="blocked",
                reason="selected action is not executable",
                requires_confirmation=False,
                manual_only=True,
            )
    except Exception as exc:  # noqa: BLE001 - one stage attempt is contained.
        return replace(
            selected_row,
            status="failed",
            reason="selected action execution failed",
            requires_confirmation=False,
            manual_only=True,
            planned_writes=[],
            output_paths=[],
            failure_category=_safe_exception_category(type(exc).__name__),
            warnings=["selected action execution failed"],
        )
    return _confirmed_row_from_stage_result(
        selected_row=selected_row,
        selected_action=selected_action,
        episode_ref=episode_ref,
        source_result=source_result,
    )


def _confirmed_row_from_stage_result(
    *,
    selected_row: CorpusEpisodeCompletionWorkflowRunRow,
    selected_action: str,
    episode_ref: str,
    source_result: object,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    source_rows = [
        row
        for row in getattr(source_result, "rows", [])
        if getattr(row, "episode_ref", None) == episode_ref
    ]
    status = _confirmed_status(source_rows)
    child_report_paths = [
        *_collect_row_values(source_rows, "source_report_paths"),
        getattr(source_result, "report_json_path", None),
        getattr(source_result, "report_markdown_path", None),
    ]
    failure_category = next(
        (
            _safe_exception_category(getattr(row, "failure_category", None))
            for row in source_rows
            if _safe_exception_category(getattr(row, "failure_category", None)) is not None
        ),
        None,
    )
    child_warnings = [
        *_collect_row_values(source_rows, "warnings"),
        *[
            getattr(warning, "message", warning)
            for warning in (getattr(source_result, "warnings", []) or [])
        ],
    ]
    return replace(
        selected_row,
        status=status,
        reason=f"{selected_action} {status}",
        requires_confirmation=False,
        manual_only=status in {"blocked", "failed"},
        planned_reads=_safe_paths_or_labels(
            _collect_row_values(source_rows, "planned_reads")
        ),
        planned_writes=_safe_string_list(
            _collect_row_values(source_rows, "planned_writes")
        ),
        output_paths=_safe_string_list(
            _collect_row_values(source_rows, "output_paths")
        ),
        source_report_paths=_safe_string_list(child_report_paths),
        stage_counts=_safe_stage_counts(
            getattr(source_result, "stage_counts", {})
        ),
        failure_category=failure_category,
        warnings=_safe_warning_list(child_warnings),
    )


def _confirmed_status(rows: list[object]) -> str:
    statuses = {
        getattr(row, "outcome_status", getattr(row, "status", None))
        for row in rows
    }
    if "failed" in statuses:
        return "failed"
    if statuses & {"executed", "downloaded", "seeded"}:
        return "executed"
    if "reused" in statuses:
        return "reused"
    if "blocked" in statuses:
        return "blocked"
    if "rejected" in statuses:
        return "rejected"
    if "completed" in statuses:
        return "completed"
    return "rejected"


def _collect_row_values(rows: list[object], field: str) -> list[object]:
    values: list[object] = []
    for row in rows:
        for value in getattr(row, field, []) or []:
            if value not in values:
                values.append(value)
    return values


def _build_result(
    *,
    podcast_id: str,
    selector: str,
    episode_ref: str | None,
    requested_action: str,
    selected_action: str,
    confirm: bool,
    row: CorpusEpisodeCompletionWorkflowRunRow,
    warnings: list[CorpusEpisodeCompletionWorkflowRunWarning],
    transcription_model: str | None,
    transcription_device: str,
    transcription_compute_type: str,
    transcription_vad_filter: bool,
    semantic_provider: str,
    semantic_model: str | None,
    semantic_chunk_seconds: int,
    semantic_max_segments_per_chunk: int,
    executed_action: str | None = None,
    report_json_path: Path | None = None,
    report_markdown_path: Path | None = None,
) -> CorpusEpisodeCompletionWorkflowRunResult:
    rows = [row]
    filter_provider = _safe_identifier_or_none(semantic_provider)
    filter_model = _safe_identifier_or_none(semantic_model)
    filter_chunk_seconds = semantic_chunk_seconds
    filter_max_segments_per_chunk = semantic_max_segments_per_chunk
    if selected_action == ACTION_SEMANTIC_REVIEW:
        filter_provider = None
        filter_model = None
        filter_chunk_seconds = DEFAULT_SEMANTIC_CHUNK_SECONDS
        filter_max_segments_per_chunk = DEFAULT_SEMANTIC_MAX_SEGMENTS_PER_CHUNK
    return CorpusEpisodeCompletionWorkflowRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_CONFIRMED if confirm else RUN_MODE_DRY_RUN,
        confirm=confirm,
        selector=selector,
        episode_ref=episode_ref,
        requested_action=requested_action,
        selected_action=selected_action,
        executed_action=executed_action,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        filters=CorpusEpisodeCompletionWorkflowRunFilter(
            episode_ref=selector,
            action=requested_action,
            transcription_model=_safe_identifier_or_none(transcription_model),
            transcription_device=_safe_identifier_or_omitted(transcription_device),
            transcription_compute_type=_safe_identifier_or_omitted(
                transcription_compute_type
            ),
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=filter_provider,
            semantic_model=filter_model,
            semantic_chunk_seconds=filter_chunk_seconds,
            semantic_max_segments_per_chunk=filter_max_segments_per_chunk,
        ),
        counts=_counts(rows, warnings),
        rows=rows,
        warnings=warnings,
        not_investment_advice=True,
    )


def _blocked_row(
    *,
    episode_ref: str | None,
    status: str,
    reason: str,
    failure_category: str | None = None,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref=episode_ref,
        action=ACTION_BLOCKED,
        status=status,
        reason=reason,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        network_risk=False,
        local_compute_risk=False,
        transcript_transfer_risk=False,
        may_incur_api_cost=False,
        manual_only=True,
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
        provider=None,
        model=None,
        failure_category=failure_category,
        warnings=[],
    )


def _first_row_from_mapping(selection: object) -> object | None:
    if not isinstance(selection, dict):
        return None
    rows = selection.get("rows")
    if not isinstance(rows, list) or not rows:
        return None
    return rows[0]


def _row_from_stage(
    *,
    episode_ref: str,
    action: str,
    source_row: object | None,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    risk = {
        ACTION_AUDIO_DOWNLOAD: (True, False),
        ACTION_LOCAL_TRANSCRIPTION: (False, True),
        ACTION_DETERMINISTIC_REMEDIATION: (False, False),
    }[action]
    reason = {
        ACTION_AUDIO_DOWNLOAD: "audio download is the next ready action",
        ACTION_LOCAL_TRANSCRIPTION: "local transcription is the next ready action",
        ACTION_DETERMINISTIC_REMEDIATION: "deterministic remediation is the next ready action",
    }[action]
    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref=episode_ref,
        action=action,
        status="selected",
        reason=reason,
        requires_confirmation=True,
        requires_api_cost_ack=False,
        network_risk=risk[0],
        local_compute_risk=risk[1],
        transcript_transfer_risk=False,
        may_incur_api_cost=False,
        manual_only=False,
        planned_reads=_safe_paths_or_labels(
            getattr(source_row, "planned_reads", [])
        ),
        planned_writes=_safe_string_list(
            getattr(source_row, "planned_writes", [])
        ),
        output_paths=_safe_string_list(getattr(source_row, "output_paths", [])),
        source_report_paths=_safe_string_list(
            getattr(source_row, "source_report_paths", [])
        ),
        stage_counts=_safe_stage_counts(getattr(source_row, "stage_counts", {})),
        provider=None,
        model=None,
        failure_category=None,
        warnings=[],
    )


def _row_from_semantic(
    *,
    episode_ref: str,
    action: str,
    source_row: object,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    is_summary = action == ACTION_SEMANTIC_SUMMARY
    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref=episode_ref,
        action=action,
        status="selected",
        reason=(
            "semantic summary is missing"
            if is_summary
            else "semantic review is missing"
        ),
        requires_confirmation=True,
        requires_api_cost_ack=is_summary,
        network_risk=is_summary,
        local_compute_risk=False,
        transcript_transfer_risk=is_summary,
        may_incur_api_cost=is_summary,
        manual_only=False,
        planned_reads=_safe_paths_or_labels(
            getattr(source_row, "planned_reads", [])
        ),
        planned_writes=_safe_string_list(
            getattr(source_row, "planned_writes", [])
        ),
        output_paths=_safe_string_list(getattr(source_row, "output_paths", [])),
        source_report_paths=_safe_string_list(
            getattr(source_row, "source_report_paths", [])
        ),
        stage_counts=_safe_stage_counts(getattr(source_row, "stage_counts", {})),
        provider=None,
        model=None,
        failure_category=None,
        warnings=[],
    )


def _completed_row(
    episode_ref: str,
    source_row: object,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref=episode_ref,
        action=ACTION_COMPLETED,
        status="completed",
        reason="no executable safe workflow action remains",
        requires_confirmation=False,
        requires_api_cost_ack=False,
        network_risk=False,
        local_compute_risk=False,
        transcript_transfer_risk=False,
        may_incur_api_cost=False,
        manual_only=False,
        planned_reads=_safe_paths_or_labels(
            getattr(source_row, "planned_reads", [])
        ),
        planned_writes=[],
        output_paths=[],
        source_report_paths=_safe_string_list(
            getattr(source_row, "source_report_paths", [])
        ),
        stage_counts=_safe_stage_counts(getattr(source_row, "stage_counts", {})),
        provider=None,
        model=None,
        failure_category=None,
        warnings=[],
    )


def _blocked_row_from_source(
    *,
    episode_ref: str,
    source_row: object | None,
) -> CorpusEpisodeCompletionWorkflowRunRow:
    source_status = getattr(source_row, "status", None)
    if source_status is None:
        source_status = getattr(source_row, "outcome_status", None)
    status = "failed" if source_status == "failed" else "blocked"
    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref=episode_ref,
        action=ACTION_BLOCKED,
        status=status,
        reason=(
            "workflow stage inspection failed"
            if status == "failed"
            else "next workflow stage is blocked"
        ),
        requires_confirmation=False,
        requires_api_cost_ack=False,
        network_risk=False,
        local_compute_risk=False,
        transcript_transfer_risk=False,
        may_incur_api_cost=False,
        manual_only=True,
        planned_reads=_safe_paths_or_labels(
            getattr(source_row, "planned_reads", [])
        ),
        planned_writes=[],
        output_paths=[],
        source_report_paths=_safe_string_list(
            getattr(source_row, "source_report_paths", [])
        ),
        stage_counts=_safe_stage_counts(getattr(source_row, "stage_counts", {})),
        provider=None,
        model=None,
        failure_category=_safe_exception_category(
            getattr(source_row, "failure_category", None)
        ),
        warnings=[],
    )


def _counts(
    rows: list[CorpusEpisodeCompletionWorkflowRunRow],
    warnings: list[CorpusEpisodeCompletionWorkflowRunWarning],
) -> CorpusEpisodeCompletionWorkflowRunCounts:
    return CorpusEpisodeCompletionWorkflowRunCounts(
        row_count=len(rows),
        selected_count=sum(row.status == "selected" for row in rows),
        executed_count=sum(row.status == "executed" for row in rows),
        reused_count=sum(row.status == "reused" for row in rows),
        completed_count=sum(row.status == "completed" for row in rows),
        failed_count=sum(row.status == "failed" for row in rows),
        blocked_count=sum(row.status == "blocked" for row in rows),
        rejected_count=sum(row.status == "rejected" for row in rows),
        manual_only_count=sum(row.manual_only for row in rows),
        warning_count=len(warnings) + sum(len(row.warnings) for row in rows),
    )


def _confirmed_warnings(
    episode_ref: str,
) -> list[CorpusEpisodeCompletionWorkflowRunWarning]:
    return [
        CorpusEpisodeCompletionWorkflowRunWarning(
            scope="corpus",
            episode_ref=episode_ref,
            message=(
                "Persisted corpus index and remediation plan may be stale; "
                "refresh them manually."
            ),
        ),
        CorpusEpisodeCompletionWorkflowRunWarning(
            scope="cache",
            episode_ref=episode_ref,
            message="SQLite cache may be stale; rebuild cache manually.",
        ),
    ]


def _normalize_podcast_id(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("podcast_id is invalid")
    return value


def _normalize_selector(value: str | None) -> str:
    if value is None:
        return DEFAULT_SELECTOR
    if not isinstance(value, str):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("episode_ref is invalid")
    normalized = value.strip()
    if not normalized:
        return DEFAULT_SELECTOR
    if normalized.casefold() == DEFAULT_SELECTOR:
        if normalized != DEFAULT_SELECTOR:
            raise CorpusEpisodeCompletionWorkflowRunnerFailedError("episode_ref is invalid")
        return DEFAULT_SELECTOR
    if _SAFE_IDENTIFIER_PATTERN.fullmatch(normalized):
        if normalized.casefold().startswith(f"{DEFAULT_SELECTOR}-"):
            raise CorpusEpisodeCompletionWorkflowRunnerFailedError(
                "episode_ref is invalid"
            )
        return normalized
    raise CorpusEpisodeCompletionWorkflowRunnerFailedError("episode_ref is invalid")


def _normalize_action(value: str) -> str:
    if not isinstance(value, str):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("action is invalid")
    normalized = value.strip()
    if normalized not in _REQUESTED_ACTIONS:
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("action is invalid")
    return normalized


def _require_positive_int(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError(f"{name} is invalid")


def _validate_semantic_summary_settings(
    *,
    semantic_provider: object,
    semantic_model: object,
    semantic_base_url: object,
    semantic_api_key_env: object,
    semantic_chunk_seconds: object,
    semantic_max_segments_per_chunk: object,
) -> None:
    """Validate settings only when fresh selection can execute semantic summary."""

    _require_positive_int(semantic_chunk_seconds, "semantic_chunk_seconds")
    _require_positive_int(
        semantic_max_segments_per_chunk, "semantic_max_segments_per_chunk"
    )
    if (
        not isinstance(semantic_provider, str)
        or not _SAFE_PROVIDER_PATTERN.fullmatch(semantic_provider)
        or _safe_output_text(semantic_provider) != semantic_provider
    ):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("semantic_provider is invalid")
    if semantic_model is not None and (
        not isinstance(semantic_model, str)
        or not _SAFE_MODEL_PATTERN.fullmatch(semantic_model)
        or _safe_output_text(semantic_model) != semantic_model
    ):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("semantic_model is invalid")
    if semantic_base_url is not None and (
        not isinstance(semantic_base_url, str)
        or not _SAFE_BASE_URL_PATTERN.fullmatch(semantic_base_url)
        or "@" in semantic_base_url
        or _safe_output_text(semantic_base_url) != semantic_base_url
    ):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("semantic_base_url is invalid")
    if not isinstance(semantic_api_key_env, str) or not _SAFE_ENVIRONMENT_PATTERN.fullmatch(
        semantic_api_key_env
    ):
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError("semantic_api_key_env is invalid")


CONFIRMED_ACTION_MUST_BE_EXPLICIT_MESSAGE = "confirmed action must be explicit"
CONFIRMED_EPISODE_REF_MUST_BE_CANONICAL_MESSAGE = (
    "confirmed episode_ref must be canonical"
)
SEMANTIC_SUMMARY_REQUIRES_EXACT_ACK_MESSAGE = (
    "semantic_summary requires exact api_cost_ack"
)


def confirmed_request_rejection_reason(
    *,
    selector: str,
    action: str,
    api_cost_ack: str,
) -> str | None:
    """Single source of the confirmed-request rejection rules and messages.

    specs/025-core-consolidation FR-006: the MCP early gate and the CLI reuse
    this instead of re-implementing the predicate or re-typing the strings.
    """

    if action == ACTION_NEXT:
        return CONFIRMED_ACTION_MUST_BE_EXPLICIT_MESSAGE
    if selector.casefold() == DEFAULT_SELECTOR:
        return CONFIRMED_EPISODE_REF_MUST_BE_CANONICAL_MESSAGE
    if action == ACTION_SEMANTIC_SUMMARY and api_cost_ack != SEMANTIC_API_COST_ACK:
        return SEMANTIC_SUMMARY_REQUIRES_EXACT_ACK_MESSAGE
    return None


def _require_confirmed_request(
    *,
    selector: str,
    action: str,
    api_cost_ack: str,
) -> None:
    reason = confirmed_request_rejection_reason(
        selector=selector, action=action, api_cost_ack=api_cost_ack
    )
    if reason is not None:
        raise CorpusEpisodeCompletionWorkflowRunnerFailedError(reason)


def _safe_episode_ref(value: object) -> str | None:
    if isinstance(value, str) and _SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        return value
    return None


def _first_row(result: object) -> object | None:
    rows = getattr(result, "rows", [])
    return rows[0] if rows else None


def _safe_planned_reads(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if value in _ALLOWED_PLANNED_READS]


def _safe_paths_or_labels(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [
        value
        for value in values
        if value in _ALLOWED_PLANNED_READS or _is_safe_local_path(value)
    ]


def _safe_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    safe_values: list[str] = []
    for value in values:
        if _is_safe_local_path(value) and value not in safe_values:
            safe_values.append(value)
    return safe_values


def _safe_warning_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    warnings: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or _safe_output_text(value) != value:
            continue
        if value not in warnings:
            warnings.append(value)
    return warnings


def _safe_stage_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        key: count
        for key, count in value.items()
        if isinstance(key, str)
        and _SAFE_IDENTIFIER_PATTERN.fullmatch(key)
        and isinstance(count, int)
        and count >= 0
    }


def _safe_exception_category(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", value):
        return value
    return None


def _is_safe_local_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if not is_safe_local_path_structure(value, allow_absolute=True):
        return False
    return _safe_output_text(value) == value


def _path_or_none(path: Path | None) -> str | None:
    if path is None:
        return None
    value = str(path)
    return value if _is_safe_local_path(value) else None


def _sanitize_payload(value: object) -> object:
    if isinstance(value, Path):
        return _path_or_none(value)
    if isinstance(value, dict):
        return {
            key: _sanitize_payload(item)
            for key, item in value.items()
            if isinstance(key, str) and _safe_output_key(key)
        }
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _safe_output_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return None


def _safe_output_key(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value))


def _safe_output_text(value: str) -> str:
    text = _QUERY_PATTERN.sub("[redacted-query]", value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS):
        return "value omitted by safety boundary"
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        return "value omitted by safety boundary"
    return text


def _safe_identifier_or_none(value: object) -> str | None:
    if not isinstance(value, str) or not _SAFE_IDENTIFIER_PATTERN.fullmatch(value):
        return None
    return value if _safe_output_text(value) == value else None


def _safe_identifier_or_omitted(value: object) -> str:
    safe_value = _safe_identifier_or_none(value)
    return safe_value if safe_value is not None else "value omitted by safety boundary"
