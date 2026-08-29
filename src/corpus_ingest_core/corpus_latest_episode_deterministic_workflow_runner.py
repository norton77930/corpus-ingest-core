"""Bounded latest-episode deterministic workflow runner."""

from __future__ import annotations

import re
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from . import storage
from .audit_report_pair import write_atomic_audit_report_pair
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    resolve_canonical_transcript_asset_paths,
)
from .corpus_audio_download_runner import run_corpus_audio_download
from .corpus_episode_intake import run_corpus_episode_intake
from .corpus_episode_workflow_runner import (
    _select_next_stage as _select_episode_workflow_stage,
)
from .corpus_local_transcription_runner import run_corpus_local_transcription
from .corpus_remediation_runner import run_corpus_remediation
from .episode_claim import episode_writer_claimed
from .errors import CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError
from .models import (
    CorpusLatestEpisodeDeterministicWorkflowRunCounts,
    CorpusLatestEpisodeDeterministicWorkflowRunFilter,
    CorpusLatestEpisodeDeterministicWorkflowRunResult,
    CorpusLatestEpisodeDeterministicWorkflowRunRow,
    CorpusLatestEpisodeDeterministicWorkflowRunWarning,
)
from .path_safety import is_safe_local_path_structure

DEFAULT_SELECTOR = "latest"
STAGE_INTAKE = "intake"
STAGE_AUDIO_DOWNLOAD = "audio_download"
STAGE_LOCAL_TRANSCRIPTION = "local_transcription"
STAGE_DETERMINISTIC_REMEDIATION = "deterministic_remediation"
STAGE_COMPLETED = "completed"
STAGE_READY = "ready_for_semantic_summary"
STAGE_BLOCKED = "blocked"
_EXECUTABLE_STAGES = {
    STAGE_INTAKE,
    STAGE_AUDIO_DOWNLOAD,
    STAGE_LOCAL_TRANSCRIPTION,
    STAGE_DETERMINISTIC_REMEDIATION,
}
_MAX_REMEDIATION_ACTIONS = 5
_SAFE_PODCAST_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_SAFE_FAILURE_CATEGORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_SAFE_ACTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,255}$")
_API_KEY_LIKE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+", re.IGNORECASE)
_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:api[_-]?key|token|password|authorization|cookie|"
    r"client[_-]?secret|private[_-]?key)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_URI_WITH_QUERY_OR_FRAGMENT_PATTERN = re.compile(
    r"\b[A-Za-z][A-Za-z0-9+.-]*:[^\s?#]*[?#]\S*"
)
_ALLOWED_PLANNED_READS = {
    "configured podcast RSS feed",
    "in-memory corpus snapshot",
}
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "http://",
    "https://",
    "?token",
    "token=",
    "api_key",
    "password=",
    "authorization",
    "cookie",
    "client_secret",
    "private_key",
    "secret",
    "bearer ",
    "raw transcript",
    "traceback",
)
_FORBIDDEN_PATH_FRAGMENTS = (
    ".env",
    "credential",
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
    "cookie",
    "authorization",
)


def run_corpus_latest_episode_deterministic_workflow(
    podcast_id: str,
    *,
    confirm: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
) -> CorpusLatestEpisodeDeterministicWorkflowRunResult:
    """Preview or process one latest episode through deterministic work only."""

    normalized_podcast_id = _normalize_podcast_id(podcast_id)
    filters = CorpusLatestEpisodeDeterministicWorkflowRunFilter(
        transcription_model=transcription_model,
        transcription_device=transcription_device,
        transcription_compute_type=transcription_compute_type,
        transcription_vad_filter=transcription_vad_filter,
    )
    canonical_episode_ref, initial_failure = _resolve_latest_episode(normalized_podcast_id)
    if initial_failure is not None:
        return _build_result(
            podcast_id=normalized_podcast_id,
            confirm=confirm,
            episode_ref=None,
            outcome=initial_failure.status,
            filters=filters,
            rows=[initial_failure],
        )
    if canonical_episode_ref is None:
        return _build_result(
            podcast_id=normalized_podcast_id,
            confirm=confirm,
            episode_ref=None,
            outcome="blocked",
            filters=filters,
            rows=[_terminal_row(None, "blocked", "latest episode could not be resolved")],
        )
    if not confirm:
        probe_row, _selected_stage = _probe_stage(
            normalized_podcast_id, canonical_episode_ref
        )
        return _build_result(
            podcast_id=normalized_podcast_id,
            confirm=False,
            episode_ref=canonical_episode_ref,
            outcome="dry_run",
            filters=filters,
            rows=[probe_row],
        )
    return _run_pinned_deterministic_workflow(
        normalized_podcast_id,
        canonical_episode_ref,
        filters=filters,
        write_report=True,
    )


@episode_writer_claimed
def _run_pinned_deterministic_workflow(
    podcast_id: str,
    canonical_episode_ref: str,
    *,
    filters: CorpusLatestEpisodeDeterministicWorkflowRunFilter,
    write_report: bool,
) -> CorpusLatestEpisodeDeterministicWorkflowRunResult:
    """Run the 017 deterministic ladder for an already pinned canonical episode.

    This package-private seam deliberately performs no latest resolution.  It lets
    SPEC 018 reuse the exact 017 stage loop without adding another RSS lookup.
    """

    probe_row, selected_stage = _probe_stage(podcast_id, canonical_episode_ref)
    rows: list[CorpusLatestEpisodeDeterministicWorkflowRunRow] = []
    remediation_actions = 0
    completed_remediation_action_ids: set[str] = set()
    while True:
        if selected_stage == STAGE_COMPLETED:
            try:
                canonical_transcript = resolve_canonical_transcript_asset_paths(
                    podcast_id, canonical_episode_ref
                )
            except CanonicalTranscriptResolutionError:
                rows.append(
                    _terminal_row(
                        canonical_episode_ref,
                        "blocked",
                        "canonical transcript title variants are ambiguous",
                    )
                )
                return _confirmed_result(
                    podcast_id,
                    canonical_episode_ref,
                    "blocked",
                    filters,
                    rows,
                    write_report=write_report,
                )
            if canonical_transcript is None:
                rows.append(
                    _terminal_row(
                        canonical_episode_ref,
                        "blocked",
                        "canonical transcript is unavailable",
                    )
                )
                return _confirmed_result(
                    podcast_id,
                    canonical_episode_ref,
                    "blocked",
                    filters,
                    rows,
                    write_report=write_report,
                )
            rows.append(_ready_row(canonical_episode_ref))
            return _confirmed_result(
                podcast_id,
                canonical_episode_ref,
                STAGE_READY,
                filters,
                rows,
                write_report=write_report,
            )
        if selected_stage not in _EXECUTABLE_STAGES:
            rows.append(
                replace(
                    probe_row,
                    stage=STAGE_BLOCKED,
                    status="blocked",
                    reason="next deterministic workflow stage is blocked",
                    requires_confirmation=False,
                )
            )
            return _confirmed_result(
                podcast_id,
                canonical_episode_ref,
                "blocked",
                filters,
                rows,
                write_report=write_report,
            )
        if selected_stage == STAGE_DETERMINISTIC_REMEDIATION and (
            remediation_actions >= _MAX_REMEDIATION_ACTIONS
            or probe_row.action_id in completed_remediation_action_ids
        ):
            rows.append(
                _terminal_row(
                    canonical_episode_ref,
                    "blocked",
                    "deterministic remediation made no bounded progress",
                )
            )
            return _confirmed_result(
                podcast_id,
                canonical_episode_ref,
                "blocked",
                filters,
                rows,
                write_report=write_report,
            )

        attempted = _execute_stage(
            selected_stage=selected_stage,
            podcast_id=podcast_id,
            episode_ref=canonical_episode_ref,
            transcription_model=filters.transcription_model,
            transcription_device=filters.transcription_device,
            transcription_compute_type=filters.transcription_compute_type,
            transcription_vad_filter=filters.transcription_vad_filter,
            selected_row=probe_row,
        )
        rows.append(attempted)
        if attempted.status not in {"executed", "reused"}:
            return _confirmed_result(
                podcast_id,
                canonical_episode_ref,
                attempted.status,
                filters,
                rows,
                write_report=write_report,
            )
        if selected_stage == STAGE_DETERMINISTIC_REMEDIATION:
            if attempted.action_id is not None:
                completed_remediation_action_ids.add(attempted.action_id)
            remediation_actions += 1
        probe_row, selected_stage = _probe_stage(podcast_id, canonical_episode_ref)


def result_to_dict(
    result: CorpusLatestEpisodeDeterministicWorkflowRunResult,
) -> dict[str, object]:
    """Serialize a latest deterministic workflow result safely."""

    return _sanitize_payload(
        {
            "podcast_id": result.podcast_id,
            "run_mode": result.run_mode,
            "confirm": result.confirm,
            "selector": result.selector,
            "episode_ref": result.episode_ref,
            "outcome": result.outcome,
            "report_json_path": _path_or_none(result.report_json_path),
            "report_markdown_path": _path_or_none(result.report_markdown_path),
            "filters": asdict(result.filters),
            **asdict(result.counts),
            "rows": [asdict(row) for row in result.rows],
            "warnings": [asdict(warning) for warning in result.warnings],
            "not_investment_advice": result.not_investment_advice,
        }
    )


def _resolve_latest_episode(
    podcast_id: str,
) -> tuple[str | None, CorpusLatestEpisodeDeterministicWorkflowRunRow | None]:
    try:
        result = run_corpus_episode_intake(
            podcast_id,
            episode_ref=DEFAULT_SELECTOR,
            confirm=False,
        )
    except Exception as exc:  # noqa: BLE001 - fail closed at external selection.
        return None, _terminal_row(
            None,
            "failed",
            "latest episode selector inspection failed",
            type(exc).__name__,
        )
    value = getattr(result, "resolved_episode_ref", None)
    if not isinstance(value, str) or not storage.is_safe_episode_ref(value, max_length=128):
        return None, None
    return value, None


def _probe_stage(
    podcast_id: str,
    episode_ref: str,
) -> tuple[CorpusLatestEpisodeDeterministicWorkflowRunRow, str]:
    try:
        selection = _select_episode_workflow_stage(
            podcast_id=podcast_id,
            selector=episode_ref,
            max_actions=1,
            allow_semantic_handoff=True,
        )
    except Exception as exc:  # noqa: BLE001 - probes must remain bounded.
        row = _terminal_row(
            episode_ref,
            "failed",
            "deterministic stage inspection failed",
            type(exc).__name__,
        )
        return row, STAGE_BLOCKED
    if not isinstance(selection, dict) or selection.get("episode_ref") != episode_ref:
        return (
            _terminal_row(
                episode_ref,
                "blocked",
                "deterministic stage inspection episode mismatch",
            ),
            STAGE_BLOCKED,
        )
    stage = selection.get("selected_stage", STAGE_BLOCKED)
    if not isinstance(stage, str):
        stage = STAGE_BLOCKED
    raw_action_id = selection.get("action_id")
    action_id = _safe_action_id(raw_action_id)
    if raw_action_id is not None and action_id is None:
        return (
            _terminal_row(
                episode_ref,
                "blocked",
                "deterministic stage inspection action identity invalid",
            ),
            STAGE_BLOCKED,
        )
    source_rows = selection.get("rows", [])
    source_row = (
        source_rows[0] if isinstance(source_rows, list) and source_rows else None
    )
    return (
        _row_from_source(
            episode_ref,
            stage,
            source_row,
            action_id=action_id,
        ),
        stage,
    )


def _execute_stage(
    *,
    selected_stage: str,
    podcast_id: str,
    episode_ref: str,
    transcription_model: str | None,
    transcription_device: str,
    transcription_compute_type: str,
    transcription_vad_filter: bool,
    selected_row: CorpusLatestEpisodeDeterministicWorkflowRunRow,
) -> CorpusLatestEpisodeDeterministicWorkflowRunRow:
    try:
        if selected_stage == STAGE_INTAKE:
            source_result = run_corpus_episode_intake(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
            )
        elif selected_stage == STAGE_AUDIO_DOWNLOAD:
            source_result = run_corpus_audio_download(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
            )
        elif selected_stage == STAGE_LOCAL_TRANSCRIPTION:
            source_result = run_corpus_local_transcription(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
                model=transcription_model,
                device=transcription_device,
                compute_type=transcription_compute_type,
                vad_filter=transcription_vad_filter,
            )
        else:
            source_result = run_corpus_remediation(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
                max_actions=1,
            )
    except Exception as exc:  # noqa: BLE001 - one action attempt is contained.
        return replace(
            selected_row,
            status="failed",
            reason="deterministic stage execution failed",
            requires_confirmation=False,
            failure_category=type(exc).__name__,
            planned_writes=[],
            output_paths=[],
            warnings=["deterministic stage execution failed"],
        )
    return _row_from_execution(selected_row, source_result)


def _row_from_execution(
    selected_row: CorpusLatestEpisodeDeterministicWorkflowRunRow,
    source_result: object,
) -> CorpusLatestEpisodeDeterministicWorkflowRunRow:
    source_rows = [
        row
        for row in list(getattr(source_result, "rows", []) or [])
        if getattr(row, "episode_ref", None) == selected_row.episode_ref
    ]
    status = _source_status(source_rows)
    source_row = next(
        (row for row in source_rows if _source_status([row]) == status),
        None,
    )
    selected_action_id_value = getattr(selected_row, "action_id", None)
    source_action_id_value = getattr(source_row, "action_id", None)
    selected_action_id = _safe_action_id(selected_action_id_value)
    source_action_id = _safe_action_id(source_action_id_value)
    action_identity_is_invalid = (
        selected_action_id_value is not None and selected_action_id is None
    ) or (source_action_id_value is not None and source_action_id is None)
    action_identity_mismatches = (
        selected_action_id is not None
        and source_action_id is not None
        and selected_action_id != source_action_id
    )
    if action_identity_is_invalid or action_identity_mismatches:
        return replace(
            selected_row,
            action_id=selected_action_id,
            status="blocked",
            reason="deterministic stage execution action mismatch",
            requires_confirmation=False,
            planned_reads=[],
            planned_writes=[],
            output_paths=[],
            source_report_paths=[],
            failure_category=None,
            warnings=[],
        )
    return replace(
        selected_row,
        action_id=selected_action_id or source_action_id,
        status=status,
        reason=_safe_text(getattr(source_row, "reason", f"{selected_row.stage} {status}")),
        requires_confirmation=False,
        planned_reads=_safe_paths_or_labels(getattr(source_row, "planned_reads", [])),
        planned_writes=_safe_local_paths(getattr(source_row, "planned_writes", [])),
        output_paths=_safe_local_paths(getattr(source_row, "output_paths", [])),
        source_report_paths=_safe_local_paths(
            getattr(source_row, "source_report_paths", [])
        ),
        failure_category=_safe_identifier(getattr(source_row, "failure_category", None)),
        warnings=_safe_text_list(getattr(source_row, "warnings", [])),
    )


def _source_status(rows: list[object]) -> str:
    statuses = {
        status
        if status
        in {"failed", "executed", "downloaded", "seeded", "reused", "blocked", "rejected"}
        else "blocked"
        for row in rows
        for status in [
            getattr(row, "outcome_status", getattr(row, "status", None))
        ]
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
    return "blocked"


def _row_from_source(
    episode_ref: str,
    stage: str,
    source_row: object | None,
    *,
    action_id: str | None = None,
) -> CorpusLatestEpisodeDeterministicWorkflowRunRow:
    return CorpusLatestEpisodeDeterministicWorkflowRunRow(
        episode_ref=episode_ref,
        stage=stage,
        action_id=action_id or _safe_action_id(getattr(source_row, "action_id", None)),
        status=_safe_status(getattr(source_row, "status", "selected")),
        reason=_safe_text(getattr(source_row, "reason", f"{stage} selected")),
        requires_confirmation=True,
        network_risk=stage in {STAGE_INTAKE, STAGE_AUDIO_DOWNLOAD},
        local_compute_risk=stage == STAGE_LOCAL_TRANSCRIPTION,
        planned_reads=_safe_paths_or_labels(getattr(source_row, "planned_reads", [])),
        planned_writes=_safe_local_paths(getattr(source_row, "planned_writes", [])),
        output_paths=[],
        source_report_paths=[],
        failure_category=None,
        warnings=_safe_text_list(getattr(source_row, "warnings", [])),
    )


def _ready_row(episode_ref: str) -> CorpusLatestEpisodeDeterministicWorkflowRunRow:
    return CorpusLatestEpisodeDeterministicWorkflowRunRow(
        episode_ref=episode_ref,
        stage=STAGE_READY,
        action_id=None,
        status="ready",
        reason="deterministic processing is ready for semantic summary",
        requires_confirmation=False,
        network_risk=False,
        local_compute_risk=False,
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        failure_category=None,
        warnings=[],
    )


def _terminal_row(
    episode_ref: str | None,
    status: str,
    reason: str,
    failure_category: str | None = None,
) -> CorpusLatestEpisodeDeterministicWorkflowRunRow:
    return CorpusLatestEpisodeDeterministicWorkflowRunRow(
        episode_ref=episode_ref,
        stage=STAGE_BLOCKED,
        action_id=None,
        status=status,
        reason=_safe_text(reason),
        requires_confirmation=False,
        network_risk=False,
        local_compute_risk=False,
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        failure_category=_safe_identifier(failure_category),
        warnings=[],
    )


def _build_result(
    *,
    podcast_id: str,
    confirm: bool,
    episode_ref: str | None,
    outcome: str,
    filters: CorpusLatestEpisodeDeterministicWorkflowRunFilter,
    rows: list[CorpusLatestEpisodeDeterministicWorkflowRunRow],
    report_json_path: Path | None = None,
    report_markdown_path: Path | None = None,
    warnings: list[CorpusLatestEpisodeDeterministicWorkflowRunWarning] | None = None,
) -> CorpusLatestEpisodeDeterministicWorkflowRunResult:
    warnings = warnings or []
    return CorpusLatestEpisodeDeterministicWorkflowRunResult(
        podcast_id=podcast_id,
        run_mode="confirmed" if confirm else "dry_run",
        confirm=confirm,
        selector=DEFAULT_SELECTOR,
        episode_ref=episode_ref,
        outcome=outcome,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        filters=filters,
        counts=CorpusLatestEpisodeDeterministicWorkflowRunCounts(
            row_count=len(rows),
            selected_count=sum(row.status == "selected" for row in rows),
            executed_count=sum(row.status == "executed" for row in rows),
            reused_count=sum(row.status == "reused" for row in rows),
            ready_count=sum(row.status == "ready" for row in rows),
            failed_count=sum(row.status == "failed" for row in rows),
            blocked_count=sum(row.status == "blocked" for row in rows),
            rejected_count=sum(row.status == "rejected" for row in rows),
            warning_count=len(warnings) + sum(len(row.warnings) for row in rows),
        ),
        rows=rows,
        warnings=warnings,
        not_investment_advice=True,
    )


def _confirmed_result(
    podcast_id: str,
    episode_ref: str,
    outcome: str,
    filters: CorpusLatestEpisodeDeterministicWorkflowRunFilter,
    rows: list[CorpusLatestEpisodeDeterministicWorkflowRunRow],
    *,
    write_report: bool = True,
) -> CorpusLatestEpisodeDeterministicWorkflowRunResult:
    report_paths = storage.corpus_latest_episode_deterministic_workflow_run_asset_paths(
        podcast_id
    )
    warnings = [
        CorpusLatestEpisodeDeterministicWorkflowRunWarning(
            scope="cache",
            episode_ref=episode_ref,
            message="SQLite cache may be stale; rebuild cache manually.",
        )
    ]
    result = _build_result(
        podcast_id=podcast_id,
        confirm=True,
        episode_ref=episode_ref,
        outcome=outcome,
        filters=filters,
        rows=rows,
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        warnings=warnings,
    )
    if write_report:
        _write_run_report(result)
    return result


def _write_run_report(result: CorpusLatestEpisodeDeterministicWorkflowRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    try:
        write_atomic_audit_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            payload,
            "# Latest Episode Deterministic Workflow\n\n"
            f"- Outcome: {payload['outcome']}\n"
            f"- Episode: {payload['episode_ref'] or 'none'}\n"
            "- SQLite cache may be stale; rebuild cache manually.\n"
            "- This report is not investment advice.\n",
        )
    except OSError as exc:
        raise CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError(
            f"failed to write latest deterministic workflow report: {type(exc).__name__}"
        ) from exc


def _normalize_podcast_id(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_PODCAST_ID.fullmatch(value):
        raise CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError(
            "podcast_id is invalid"
        )
    return value


def _safe_status(value: object) -> str:
    return value if value in {"selected", "blocked", "failed", "rejected"} else "selected"


def _safe_identifier(value: object) -> str | None:
    if isinstance(value, str) and _SAFE_FAILURE_CATEGORY.fullmatch(value):
        return value
    return None


def _safe_action_id(value: object) -> str | None:
    if isinstance(value, str) and _SAFE_ACTION_ID.fullmatch(value):
        return value
    return None


def _safe_paths_or_labels(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if item in _ALLOWED_PLANNED_READS or _is_safe_local_path(item)
    ]


def _safe_local_paths(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if _is_safe_local_path(item)]


def _safe_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_safe_text(item) for item in value if isinstance(item, str)]


def _is_safe_local_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if not is_safe_local_path_structure(
        value, allow_absolute=False, require_separator=False
    ):
        return False
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_PATH_FRAGMENTS):
        return False
    return _safe_text(value) == value


def _safe_text(value: object) -> str:
    text = str(value).replace("\n", " ")[:1024]
    lowered = text.lower()
    if (
        any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS)
        or _API_KEY_LIKE_PATTERN.search(text)
        or _SENSITIVE_ASSIGNMENT_PATTERN.search(text)
        or _URI_WITH_QUERY_OR_FRAGMENT_PATTERN.search(text)
        or any(ord(character) < 32 or ord(character) == 127 for character in text)
    ):
        return "value omitted by safety boundary"
    return text


def _path_or_none(path: Path | None) -> str | None:
    if path is None:
        return None
    value = str(path)
    return value if _is_safe_local_path(value) else None


def _sanitize_payload(value: object) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value
