from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from . import storage
from .audit_report_pair import write_atomic_audit_report_pair
from .corpus_index import _build_corpus_index_snapshot
from .corpus_remediation_plan import _build_corpus_remediation_plan_snapshot
from .episode_claim import (
    _consume_controlled_regeneration_capability,
    _ControlledRegenerationCapability,
    episode_writer_claimed,
)
from .errors import CorpusSemanticRemediationRunnerFailedError
from .generation_proof import notify_child_artifact_committed
from .models import (
    CorpusSemanticRemediationRunCounts,
    CorpusSemanticRemediationRunFilter,
    CorpusSemanticRemediationRunResult,
    CorpusSemanticRemediationRunRow,
    CorpusSemanticRemediationRunWarning,
)
from .path_safety import is_safe_local_path_structure
from .semantic_summarizer import (
    SEMANTIC_API_COST_ACK,
    semantic_summarize_episode,
)
from .semantic_summary_smoke_review import review_semantic_summary_smoke

RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
ACTION_NEXT = "next"
ACTION_SEMANTIC_SUMMARY = "semantic_summary"
ACTION_SEMANTIC_REVIEW = "semantic_review"
ACTION_COMPLETED = "completed"
ACTION_BLOCKED = "blocked"

_IN_MEMORY_SNAPSHOT_LABEL = "in-memory corpus snapshot"
_TIMESTAMPED_REVIEW_REPORT_LABEL = "timestamped semantic review JSON/Markdown reports"
_ALLOWED_ACTIONS = {
    ACTION_NEXT,
    ACTION_SEMANTIC_SUMMARY,
    ACTION_SEMANTIC_REVIEW,
}
_EXECUTABLE_ACTIONS = {
    ACTION_SEMANTIC_SUMMARY,
    ACTION_SEMANTIC_REVIEW,
}

_SAFE_PROVIDER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SAFE_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SAFE_API_KEY_ENV_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
_SAFE_EXCEPTION_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
_QUERY_PATTERN = re.compile(r"\?[^\s|]+")


@dataclass(frozen=True)
class _ControlledSemanticSummaryRegenerationResult:
    """Parent-only child result for a single verified overwrite."""

    podcast_id: str
    episode_ref: str
    summary_path: Path
    generated: bool
    already_exists: bool
    provider: str | None
    model: str | None


_FORBIDDEN_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "token=",
    "api_key",
    "bearer ",
    "raw transcript",
    "semantic body",
    "prompt text",
    "raw response",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


def run_corpus_semantic_remediation(
    podcast_id: str,
    *,
    episode_ref: str,
    action: str = "next",
    confirm: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
    chunk_seconds: int = 600,
    max_segments_per_chunk: int = 120,
    progress_callback: Callable[..., None] | None = None,
) -> CorpusSemanticRemediationRunResult:
    """Preview or execute one semantic remediation action for one episode."""

    normalized_podcast_id = _normalize_podcast_id(podcast_id)
    normalized_episode_ref = _normalize_episode_ref(episode_ref)
    requested_action = _normalize_action(action)
    _require_positive_int(read_timeout_seconds, "read_timeout_seconds", maximum=3_600)
    _require_positive_int(chunk_seconds, "chunk_seconds")
    _require_positive_int(max_segments_per_chunk, "max_segments_per_chunk")
    if confirm and requested_action == ACTION_NEXT:
        raise CorpusSemanticRemediationRunnerFailedError("confirmed action must be semantic_summary or semantic_review")
    if confirm and requested_action == ACTION_SEMANTIC_SUMMARY and api_cost_ack != SEMANTIC_API_COST_ACK:
        raise CorpusSemanticRemediationRunnerFailedError(
            f"semantic_summary requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}"
        )

    requested_provider: str | None = None
    requested_model: str | None = None
    requested_reasoning_effort: str | None = None
    if confirm and requested_action == ACTION_SEMANTIC_SUMMARY:
        requested_provider = _normalize_provider(provider)
        requested_model = _normalize_model(model)
        requested_reasoning_effort = _normalize_model(reasoning_effort)
        _normalize_api_key_env(api_key_env)

    row, selected_action, warnings = _preview_selection(
        normalized_podcast_id,
        normalized_episode_ref,
    )

    if not confirm:
        if (
            requested_action != ACTION_NEXT
            and selected_action in _EXECUTABLE_ACTIONS
            and requested_action != selected_action
        ):
            row = replace(
                row,
                status="rejected",
                reason="requested action does not match fresh selection",
            )
        if selected_action == ACTION_SEMANTIC_SUMMARY:
            requested_provider = _normalize_provider(provider)
            requested_model = _normalize_model(model)
            requested_reasoning_effort = _normalize_model(reasoning_effort)
            row = replace(
                row,
                provider=requested_provider,
                model=requested_model,
            )
        return _build_result(
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
            requested_action=requested_action,
            selected_action=selected_action,
            executed_action=None,
            confirm=False,
            row=row,
            warnings=warnings,
            provider=requested_provider,
            model=requested_model,
            reasoning_effort=requested_reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            chunk_seconds=chunk_seconds,
            max_segments_per_chunk=max_segments_per_chunk,
        )

    executed_action: str | None = None
    if row.status == "failed" or selected_action == ACTION_BLOCKED:
        pass
    elif selected_action == ACTION_COMPLETED:
        row = replace(
            row,
            status="rejected",
            reason="semantic remediation is already completed",
        )
    elif requested_action != selected_action:
        row = replace(
            row,
            status="rejected",
            reason="requested action does not match fresh selection",
        )
    elif selected_action == ACTION_SEMANTIC_SUMMARY:
        executed_action = ACTION_SEMANTIC_SUMMARY
        row = _execute_semantic_summary(
            row=row,
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
            api_cost_ack=api_cost_ack,
            provider=requested_provider or "openai-compatible",
            model=requested_model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=requested_reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            chunk_seconds=chunk_seconds,
            max_segments_per_chunk=max_segments_per_chunk,
            progress_callback=progress_callback,
        )
    elif selected_action == ACTION_SEMANTIC_REVIEW:
        executed_action = ACTION_SEMANTIC_REVIEW
        row = _execute_semantic_review(
            row=row,
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
        )

    warnings = [*warnings, *_confirmed_warnings(executed_action)]
    report_paths = storage.corpus_semantic_remediation_run_asset_paths(normalized_podcast_id)
    result = _build_result(
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
        requested_action=requested_action,
        selected_action=selected_action,
        executed_action=executed_action,
        confirm=True,
        row=row,
        warnings=warnings,
        provider=requested_provider,
        model=requested_model,
        reasoning_effort=requested_reasoning_effort,
        read_timeout_seconds=read_timeout_seconds,
        chunk_seconds=chunk_seconds,
        max_segments_per_chunk=max_segments_per_chunk,
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
    )
    _write_run_report(result)
    return result


def result_to_dict(result: CorpusSemanticRemediationRunResult) -> dict[str, Any]:
    """Serialize a semantic remediation result into bounded JSON metadata."""

    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    counts = payload.pop("counts")
    payload.update(counts)
    return _sanitize_payload(payload)


def _build_result(
    *,
    podcast_id: str,
    episode_ref: str,
    requested_action: str,
    selected_action: str,
    executed_action: str | None,
    confirm: bool,
    row: CorpusSemanticRemediationRunRow,
    warnings: list[CorpusSemanticRemediationRunWarning],
    provider: str | None,
    model: str | None,
    reasoning_effort: str | None,
    read_timeout_seconds: int,
    chunk_seconds: int,
    max_segments_per_chunk: int,
    report_json_path: Path | None = None,
    report_markdown_path: Path | None = None,
) -> CorpusSemanticRemediationRunResult:
    rows = [row]
    return CorpusSemanticRemediationRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_CONFIRMED if confirm else RUN_MODE_DRY_RUN,
        confirm=confirm,
        episode_ref=episode_ref,
        requested_action=requested_action,
        selected_action=selected_action,
        executed_action=executed_action,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        filters=CorpusSemanticRemediationRunFilter(
            episode_ref=episode_ref,
            action=requested_action,
            provider=provider,
            model=model,
            reasoning_effort=reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            chunk_seconds=chunk_seconds,
            max_segments_per_chunk=max_segments_per_chunk,
        ),
        counts=_counts(rows, warnings),
        rows=rows,
        warnings=warnings,
        not_investment_advice=True,
    )


@episode_writer_claimed
def _execute_semantic_summary(
    *,
    row: CorpusSemanticRemediationRunRow,
    podcast_id: str,
    episode_ref: str,
    api_cost_ack: str,
    provider: str,
    model: str | None,
    base_url: str | None,
    api_key_env: str,
    reasoning_effort: str | None,
    read_timeout_seconds: int,
    chunk_seconds: int,
    max_segments_per_chunk: int,
    progress_callback: Callable[..., None] | None,
) -> CorpusSemanticRemediationRunRow:
    try:
        summary = semantic_summarize_episode(
            podcast_id,
            episode_ref,
            api_cost_ack=api_cost_ack,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            chunk_seconds=chunk_seconds,
            max_segments_per_chunk=max_segments_per_chunk,
            progress_callback=progress_callback,
        )
    except Exception as exc:  # noqa: BLE001 - executor failures are bounded.
        category = _safe_exception_category(exc)
        return replace(
            row,
            status="failed",
            reason="semantic summary execution failed",
            manual_only=True,
            output_paths=[],
            failure_category=category,
            warnings=["semantic summary execution failed"],
        )
    status = "reused" if getattr(summary, "already_exists", False) else "executed"
    summary_path = Path(str(getattr(summary, "summary_path", "")))
    notify_child_artifact_committed(
        "semantic_summary",
        summary_path,
        generated=status == "executed",
        metadata={
            "provider": getattr(summary, "provider", None),
            "model": getattr(summary, "model", None),
            "summary_mode": getattr(summary, "summary_mode", None),
        },
    )
    reason = "semantic summary already exists" if status == "reused" else "semantic summary generated"
    output_paths = _safe_list([str(getattr(summary, "summary_path", ""))])
    return replace(
        row,
        status=status,
        reason=reason,
        manual_only=False,
        output_paths=output_paths,
        provider=_safe_dependency_identifier(getattr(summary, "provider", None), provider),
        model=_safe_dependency_identifier(getattr(summary, "model", None), model),
        failure_category=None,
        warnings=[],
    )


def _run_controlled_semantic_summary_regeneration(
    podcast_id: str,
    episode_ref: str,
    *,
    authorization: _ControlledRegenerationCapability,
    expected_summary_path: Path,
    api_cost_ack: str,
    provider: str,
    model: str | None,
    base_url: str | None,
    api_key_env: str,
    reasoning_effort: str | None,
    read_timeout_seconds: int,
    chunk_seconds: int,
    max_segments_per_chunk: int,
) -> _ControlledSemanticSummaryRegenerationResult:
    """Overwrite one summary only for the claimed latest-workflow transaction.

    This is deliberately not a public remediation action: its only production
    caller owns the confirmed episode claim and captures the commit notification.
    """

    try:
        _consume_controlled_regeneration_capability(authorization, podcast_id, episode_ref)
    except ValueError as exc:
        raise CorpusSemanticRemediationRunnerFailedError(
            "controlled semantic regeneration authorization is invalid"
        ) from exc

    summary = semantic_summarize_episode(
        podcast_id,
        episode_ref,
        api_cost_ack=api_cost_ack,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        reasoning_effort=reasoning_effort,
        read_timeout_seconds=read_timeout_seconds,
        force=True,
        chunk_seconds=chunk_seconds,
        max_segments_per_chunk=max_segments_per_chunk,
    )
    actual_path = Path(str(getattr(summary, "summary_path", "")))
    if (
        getattr(summary, "podcast_id", None) != podcast_id
        or getattr(summary, "episode_ref", None) != episode_ref
        or actual_path.resolve(strict=False) != expected_summary_path.resolve(strict=False)
        or getattr(summary, "generated", None) is not True
        or getattr(summary, "already_exists", None) is not False
    ):
        raise CorpusSemanticRemediationRunnerFailedError("controlled semantic regeneration child result is invalid")
    notify_child_artifact_committed(
        "semantic_summary",
        expected_summary_path,
        generated=True,
        metadata={
            "provider": getattr(summary, "provider", None),
            "model": getattr(summary, "model", None),
            "summary_mode": getattr(summary, "summary_mode", None),
        },
    )
    return _ControlledSemanticSummaryRegenerationResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        summary_path=expected_summary_path,
        generated=True,
        already_exists=False,
        provider=getattr(summary, "provider", None),
        model=getattr(summary, "model", None),
    )


def _execute_semantic_review(
    *,
    row: CorpusSemanticRemediationRunRow,
    podcast_id: str,
    episode_ref: str,
) -> CorpusSemanticRemediationRunRow:
    try:
        review = review_semantic_summary_smoke(podcast_id, episode_ref)
    except Exception as exc:  # noqa: BLE001 - executor failures are bounded.
        category = _safe_exception_category(exc)
        return replace(
            row,
            status="failed",
            reason="semantic review execution failed",
            manual_only=True,
            output_paths=[],
            failure_category=category,
            warnings=["semantic review execution failed"],
        )

    review_status = getattr(review, "review_status", None)
    passed = review_status == "passed"
    review_path = getattr(review, "review_json_path", None)
    if passed and isinstance(review_path, Path):
        notify_child_artifact_committed(
            "semantic_review",
            review_path,
            generated=True,
            metadata={"review_status": review_status},
        )
    output_paths = _safe_list(
        [
            str(getattr(review, "review_json_path", "")),
            str(getattr(review, "review_markdown_path", "")),
        ]
    )
    return replace(
        row,
        status="executed" if passed else "blocked",
        reason=("semantic review passed" if passed else "semantic review did not pass"),
        manual_only=not passed,
        output_paths=output_paths,
        provider=None,
        model=None,
        failure_category=None,
        warnings=[],
    )


def _confirmed_warnings(
    executed_action: str | None,
) -> list[CorpusSemanticRemediationRunWarning]:
    if executed_action is None:
        return []
    return [
        CorpusSemanticRemediationRunWarning(
            scope="corpus",
            episode_ref=None,
            message=("Persisted corpus index and remediation plan may be stale; refresh them manually."),
        ),
        CorpusSemanticRemediationRunWarning(
            scope="cache",
            episode_ref=None,
            message="SQLite cache may be stale; rebuild cache manually.",
        ),
    ]


def _write_run_report(result: CorpusSemanticRemediationRunResult) -> None:
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
        raise CorpusSemanticRemediationRunnerFailedError(
            f"failed to write corpus semantic remediation run report: {_safe_exception_category(exc)}"
        ) from exc


def _write_atomic_text(path: Path, text: str) -> None:
    part_path = path.with_name(f"{path.name}.part")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        part_path.unlink(missing_ok=True)
        part_path.write_text(text, encoding="utf-8")
        part_path.replace(path)
    except OSError:
        try:
            part_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _render_markdown(payload: dict[str, Any]) -> str:
    filters = payload["filters"]
    lines = [
        f"# Corpus Semantic Remediation Run - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Run mode: {payload['run_mode']}",
        f"- Confirm: {payload['confirm']}",
        f"- Episode: {payload['episode_ref']}",
        f"- Requested action: {payload['requested_action']}",
        f"- Selected action: {payload['selected_action']}",
        f"- Executed action: {payload['executed_action'] or 'none'}",
        f"- Report JSON path: {payload['report_json_path'] or 'none'}",
        f"- Report Markdown path: {payload['report_markdown_path'] or 'none'}",
        f"- Not investment advice: {payload['not_investment_advice']}",
        "",
        "## Filters",
        "",
        f"- Filter episode: {filters['episode_ref']}",
        f"- Filter action: {filters['action']}",
        f"- Provider: {filters['provider'] or 'none'}",
        f"- Model: {filters['model'] or 'none'}",
        f"- Reasoning effort: {filters['reasoning_effort'] or 'none'}",
        f"- Read timeout seconds: {filters['read_timeout_seconds']}",
        f"- Chunk seconds: {filters['chunk_seconds']}",
        f"- Max segments per chunk: {filters['max_segments_per_chunk']}",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "row_count",
        "selected_count",
        "executed_count",
        "reused_count",
        "completed_count",
        "failed_count",
        "blocked_count",
        "rejected_count",
        "manual_only_count",
        "warning_count",
    ):
        lines.append(f"| {key} | {payload[key]} |")
    lines.extend(
        [
            "",
            "## Outcome",
        ]
    )
    for row in payload["rows"]:
        lines.extend(
            [
                "",
                f"### {_markdown_cell(row['episode_ref'])}",
                "",
                f"- Action: {_markdown_cell(row['action'])}",
                f"- Status: {_markdown_cell(row['status'])}",
                f"- Reason: {_markdown_cell(row['reason'])}",
                f"- Requires API cost acknowledgement: {row['requires_api_cost_ack']}",
                f"- Transcript transfer risk: {row['transcript_transfer_risk']}",
                f"- May incur API cost: {row['may_incur_api_cost']}",
                f"- Manual only: {row['manual_only']}",
                f"- Planned reads: {_markdown_values(row['planned_reads'])}",
                f"- Planned writes: {_markdown_values(row['planned_writes'])}",
                f"- Output paths: {_markdown_values(row['output_paths'])}",
                f"- Source report paths: {_markdown_values(row['source_report_paths'])}",
                f"- Provider: {_markdown_cell(row['provider'] or 'none')}",
                f"- Model: {_markdown_cell(row['model'] or 'none')}",
                f"- Failure category: {_markdown_cell(row['failure_category'] or 'none')}",
                f"- Row warnings: {_markdown_values(row['warnings'])}",
            ]
        )
    lines.extend(
        [
            "",
            "## Warnings",
            "",
            "| Warning scope | Warning episode | Message |",
            "| --- | --- | --- |",
        ]
    )
    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_cell(warning["scope"]),
                        _markdown_cell(warning["episode_ref"] or "none"),
                        _markdown_cell(warning["message"]),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none | none | none |")
    lines.extend(
        [
            "",
            "## Boundary Notice",
            "",
            "This report contains metadata, safe paths, counts, and bounded outcomes only.",
            "It omits transcript, semantic, prompt, provider, endpoint, credential, and traceback bodies.",
            "Persisted corpus metadata and SQLite cache refresh remain manual.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _safe_dependency_identifier(value: Any, fallback: str | None) -> str | None:
    if value is None:
        return fallback
    if not isinstance(value, str):
        return fallback
    if _SAFE_MODEL_PATTERN.fullmatch(value) and _safe_identifier_text(value):
        return value
    return fallback


def _markdown_cell(value: Any) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def _markdown_values(values: list[Any]) -> str:
    return _markdown_cell(", ".join(str(value) for value in values) or "none")


def _preview_selection(
    podcast_id: str,
    episode_ref: str,
) -> tuple[
    CorpusSemanticRemediationRunRow,
    str,
    list[CorpusSemanticRemediationRunWarning],
]:
    try:
        index_snapshot = _build_corpus_index_snapshot(podcast_id)
        plan_snapshot = _build_corpus_remediation_plan_snapshot(
            podcast_id,
            index_result=index_snapshot.result,
            index_payload=index_snapshot.payload,
        )
    except Exception as exc:  # noqa: BLE001 - snapshot failures are fail-closed.
        category = _safe_exception_category(exc)
        row = _row(
            episode_ref=episode_ref,
            action=ACTION_BLOCKED,
            status="failed",
            reason="corpus snapshot evaluation failed",
            manual_only=True,
            failure_category=category,
        )
        warnings = [
            CorpusSemanticRemediationRunWarning(
                scope="semantic_remediation",
                episode_ref=episode_ref,
                message="corpus snapshot evaluation failed",
            )
        ]
        return row, ACTION_BLOCKED, warnings

    return _preview_corpus_semantic_remediation_from_snapshot(
        podcast_id,
        episode_ref,
        plan_payload=plan_snapshot.payload,
    )


def _preview_corpus_semantic_remediation_from_snapshot(
    podcast_id: str,
    episode_ref: str,
    *,
    plan_payload: dict[str, Any],
) -> tuple[
    CorpusSemanticRemediationRunRow,
    str,
    list[CorpusSemanticRemediationRunWarning],
]:
    """Preview one semantic action from a caller-owned in-memory snapshot."""

    episode = _episode_payload(plan_payload, episode_ref)
    if episode is None:
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_BLOCKED,
                status="blocked",
                reason="episode is absent from fresh corpus snapshot",
                manual_only=True,
            ),
            ACTION_BLOCKED,
            [],
        )
    row, selected_action = _reduce_episode_state(episode_ref, episode)
    return row, selected_action, []


def _episode_payload(payload: dict[str, Any], episode_ref: str) -> dict[str, Any] | None:
    episodes = payload.get("episodes")
    if not isinstance(episodes, list):
        return None
    for episode in episodes:
        if not isinstance(episode, dict):
            continue
        if episode.get("episode_ref") == episode_ref:
            return episode
    return None


def _reduce_episode_state(
    episode_ref: str,
    episode: dict[str, Any],
) -> tuple[CorpusSemanticRemediationRunRow, str]:
    artifact_status = episode.get("artifact_status")
    if not isinstance(artifact_status, dict):
        artifact_status = {}
    transcript = _status_payload(artifact_status, "transcript")
    summary = _status_payload(artifact_status, "semantic_summary")
    review = _status_payload(artifact_status, "semantic_review")
    transcript_paths = _status_paths(transcript)
    summary_paths = _status_paths(summary)
    review_paths = _status_paths(review)
    common_reads = _safe_list(
        [_IN_MEMORY_SNAPSHOT_LABEL, *transcript_paths],
        allowed_labels={_IN_MEMORY_SNAPSHOT_LABEL},
    )

    if _status_text(transcript) != "valid":
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_BLOCKED,
                status="blocked",
                reason="transcript is not valid",
                manual_only=True,
                planned_reads=common_reads,
            ),
            ACTION_BLOCKED,
        )

    if _status_text(summary) == "missing":
        title = episode.get("title")
        if not isinstance(title, str) or not title.strip():
            title = episode_ref
        try:
            planned_summary_path = storage.semantic_summary_asset_path(
                episode.get("podcast_id", ""),
                episode_ref,
                title,
            )
        except (TypeError, ValueError):
            planned_writes: list[str] = []
        else:
            planned_writes = _safe_list([str(planned_summary_path)])
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_SEMANTIC_SUMMARY,
                status="selected",
                reason="semantic summary is missing",
                planned_reads=common_reads,
                planned_writes=planned_writes,
                requires_api_cost_ack=True,
                transcript_transfer_risk=True,
                may_incur_api_cost=True,
            ),
            ACTION_SEMANTIC_SUMMARY,
        )

    if not (summary.get("readable") is True and summary.get("readability_status") == "readable"):
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_BLOCKED,
                status="blocked",
                reason="semantic summary is unreadable",
                manual_only=True,
                planned_reads=_safe_list(
                    [_IN_MEMORY_SNAPSHOT_LABEL, *summary_paths],
                    allowed_labels={_IN_MEMORY_SNAPSHOT_LABEL},
                ),
            ),
            ACTION_BLOCKED,
        )

    review_status = review.get("review_status")
    if _status_text(review) == "missing" and review_status == "missing":
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_SEMANTIC_REVIEW,
                status="selected",
                reason=(
                    "semantic review is missing" if review_status == "missing" else "semantic review is not current"
                ),
                planned_reads=_safe_list(
                    [_IN_MEMORY_SNAPSHOT_LABEL, *summary_paths],
                    allowed_labels={_IN_MEMORY_SNAPSHOT_LABEL},
                ),
                planned_writes=[_TIMESTAMPED_REVIEW_REPORT_LABEL],
            ),
            ACTION_SEMANTIC_REVIEW,
        )

    if _status_text(review) == "passed" and review_status == "passed":
        return (
            _row(
                episode_ref=episode_ref,
                action=ACTION_COMPLETED,
                status="completed",
                reason="semantic review passed",
                planned_reads=_safe_list(
                    [_IN_MEMORY_SNAPSHOT_LABEL, *summary_paths, *review_paths],
                    allowed_labels={_IN_MEMORY_SNAPSHOT_LABEL},
                ),
                source_report_paths=_safe_list(review_paths),
            ),
            ACTION_COMPLETED,
        )

    return (
        _row(
            episode_ref=episode_ref,
            action=ACTION_BLOCKED,
            status="blocked",
            reason="semantic review requires manual intervention",
            manual_only=True,
            planned_reads=_safe_list(
                [_IN_MEMORY_SNAPSHOT_LABEL, *summary_paths, *review_paths],
                allowed_labels={_IN_MEMORY_SNAPSHOT_LABEL},
            ),
            source_report_paths=_safe_list(review_paths),
        ),
        ACTION_BLOCKED,
    )


def _row(
    *,
    episode_ref: str,
    action: str,
    status: str,
    reason: str,
    requires_api_cost_ack: bool = False,
    transcript_transfer_risk: bool = False,
    may_incur_api_cost: bool = False,
    manual_only: bool = False,
    planned_reads: list[str] | None = None,
    planned_writes: list[str] | None = None,
    output_paths: list[str] | None = None,
    source_report_paths: list[str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    failure_category: str | None = None,
    warnings: list[str] | None = None,
) -> CorpusSemanticRemediationRunRow:
    return CorpusSemanticRemediationRunRow(
        episode_ref=episode_ref,
        action=action,
        status=status,
        reason=reason,
        requires_api_cost_ack=requires_api_cost_ack,
        transcript_transfer_risk=transcript_transfer_risk,
        may_incur_api_cost=may_incur_api_cost,
        manual_only=manual_only,
        planned_reads=planned_reads or [],
        planned_writes=planned_writes or [],
        output_paths=output_paths or [],
        source_report_paths=source_report_paths or [],
        provider=provider,
        model=model,
        failure_category=failure_category,
        warnings=warnings or [],
    )


def _counts(
    rows: list[CorpusSemanticRemediationRunRow],
    warnings: list[CorpusSemanticRemediationRunWarning],
) -> CorpusSemanticRemediationRunCounts:
    warning_count = len(warnings) + sum(len(row.warnings) for row in rows)
    return CorpusSemanticRemediationRunCounts(
        row_count=len(rows),
        selected_count=sum(row.status == "selected" for row in rows),
        executed_count=sum(row.status == "executed" for row in rows),
        reused_count=sum(row.status == "reused" for row in rows),
        completed_count=sum(row.status == "completed" for row in rows),
        failed_count=sum(row.status == "failed" for row in rows),
        blocked_count=sum(row.status == "blocked" for row in rows),
        rejected_count=sum(row.status == "rejected" for row in rows),
        manual_only_count=sum(row.manual_only for row in rows),
        warning_count=warning_count,
    )


def _normalize_podcast_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CorpusSemanticRemediationRunnerFailedError("invalid podcast_id")
    try:
        storage.corpus_semantic_remediation_run_asset_paths(value)
    except (TypeError, ValueError) as exc:
        raise CorpusSemanticRemediationRunnerFailedError("invalid podcast_id") from exc
    return value


def _normalize_episode_ref(value: str) -> str:
    if not isinstance(value, str) or not storage.is_safe_episode_ref(value, max_length=128):
        raise CorpusSemanticRemediationRunnerFailedError("invalid episode_ref")
    if value.lower() == "latest":
        raise CorpusSemanticRemediationRunnerFailedError("invalid episode_ref")
    return value


def _normalize_action(value: str) -> str:
    if not isinstance(value, str):
        raise CorpusSemanticRemediationRunnerFailedError("invalid action")
    normalized = value.strip()
    if normalized not in _ALLOWED_ACTIONS:
        raise CorpusSemanticRemediationRunnerFailedError("invalid action")
    return normalized


def _require_positive_int(value: int, field_name: str, *, maximum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or (maximum is not None and value > maximum):
        raise CorpusSemanticRemediationRunnerFailedError(f"invalid {field_name}")


def _normalize_provider(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_PROVIDER_PATTERN.fullmatch(value):
        raise CorpusSemanticRemediationRunnerFailedError("invalid provider")
    if not _safe_identifier_text(value):
        raise CorpusSemanticRemediationRunnerFailedError("invalid provider")
    return value


def _normalize_model(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SAFE_MODEL_PATTERN.fullmatch(value):
        raise CorpusSemanticRemediationRunnerFailedError("invalid model")
    if not _safe_identifier_text(value):
        raise CorpusSemanticRemediationRunnerFailedError("invalid model")
    return value


def _normalize_api_key_env(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_API_KEY_ENV_PATTERN.fullmatch(value):
        raise CorpusSemanticRemediationRunnerFailedError("invalid api_key_env")
    return value


def _safe_identifier_text(value: str) -> bool:
    lowered = value.lower()
    if "://" in value or "?" in value or "#" in value:
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    return not any(
        fragment in lowered
        for fragment in (
            "token",
            "secret",
            "api_key",
            "bearer",
            "buy",
            "sell",
            "target-price",
            "guaranteed-return",
        )
    )


def _status_payload(artifact_status: dict[str, Any], family: str) -> dict[str, Any]:
    payload = artifact_status.get(family)
    return payload if isinstance(payload, dict) else {}


def _status_text(payload: dict[str, Any]) -> str:
    value = payload.get("status")
    return value if isinstance(value, str) and value else "missing"


def _status_paths(payload: dict[str, Any]) -> list[str]:
    paths = payload.get("paths")
    if not isinstance(paths, dict):
        return []
    return [value for value in paths.values() if isinstance(value, str)]


def _safe_exception_category(exc: Exception) -> str:
    category = type(exc).__name__
    if not _SAFE_EXCEPTION_PATTERN.fullmatch(category):
        return "semantic_dependency_error"
    return category


def _safe_list(
    values: list[Any],
    *,
    allowed_labels: set[str] | None = None,
) -> list[str]:
    labels = allowed_labels or set()
    collected: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        if value not in labels and not _is_safe_local_path(value):
            continue
        if value not in collected:
            collected.append(value)
    return collected


def _is_safe_local_path(value: str) -> bool:
    return is_safe_local_path_structure(value, allow_absolute=True)


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _safe_message(value, "metadata omitted by safety boundary")
    return value


def _safe_message(value: str, replacement: str) -> str:
    text = _QUERY_PATTERN.sub("[redacted-query]", value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_TEXT_FRAGMENTS):
        return replacement
    return text


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None
