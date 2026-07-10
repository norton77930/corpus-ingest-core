from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import re
from typing import Any

from . import storage
from .corpus_audio_download_runner import run_corpus_audio_download
from .corpus_episode_intake import run_corpus_episode_intake
from .corpus_local_transcription_runner import run_corpus_local_transcription
from .corpus_remediation_runner import run_corpus_remediation
from .errors import CorpusEpisodeWorkflowRunnerFailedError
from .models import (
    CorpusEpisodeWorkflowRunCounts,
    CorpusEpisodeWorkflowRunFilter,
    CorpusEpisodeWorkflowRunResult,
    CorpusEpisodeWorkflowRunRow,
    CorpusEpisodeWorkflowRunWarning,
)


RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
DEFAULT_SELECTOR = "latest"
STAGE_NEXT = "next"
STAGE_INTAKE = "intake"
STAGE_AUDIO_DOWNLOAD = "audio_download"
STAGE_LOCAL_TRANSCRIPTION = "local_transcription"
STAGE_DETERMINISTIC_REMEDIATION = "deterministic_remediation"
STAGE_COMPLETED = "completed"
STAGE_BLOCKED = "blocked"

_EXECUTABLE_STAGES = {
    STAGE_INTAKE,
    STAGE_AUDIO_DOWNLOAD,
    STAGE_LOCAL_TRANSCRIPTION,
    STAGE_DETERMINISTIC_REMEDIATION,
}
_SAFE_EPISODE_REF_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9-]{0,127}$')
_SAFE_STAGE_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
_URI_SCHEME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]*://')
_SAFE_FILENAME_PATTERN = re.compile(
    r'^[^<>:/\\|?*\x00-\x1f]+\.[A-Za-z0-9]{1,16}$'
)
_SAFE_PATH_COMPONENT_PATTERN = re.compile(r'^[A-Za-z0-9._-]+$')
_WORKFLOW_ROW_REASONS = frozenset(
    {
        'episode selector could not be resolved',
        'episode seed metadata is missing',
        'audio download is the next ready action',
        'local transcription is the next ready action',
        'deterministic remediation is the next ready action',
        'next workflow stage is blocked',
        'no executable safe workflow stage remains',
    }
)
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "http://",
    "https://",
    "?token",
    "token=",
    "api_key",
    "secret",
    "bearer ",
    "raw transcript",
    "semantic body",
    "prompt text",
    "raw llm output",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)
_QUERY_PATTERN = re.compile(r"\?[^\s|]+")


def run_corpus_episode_workflow(
    podcast_id: str,
    *,
    episode_ref: str = DEFAULT_SELECTOR,
    stage: str = STAGE_NEXT,
    confirm: bool = False,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    max_actions: int | None = None,
) -> CorpusEpisodeWorkflowRunResult:
    """Preview or run one next safe corpus workflow stage."""

    selector = _normalize_selector(episode_ref)
    normalized_stage = _normalize_stage(stage)
    if normalized_stage != STAGE_NEXT:
        raise CorpusEpisodeWorkflowRunnerFailedError("stage must be next")

    selection = _select_next_stage(
        podcast_id=podcast_id,
        selector=selector,
        max_actions=max_actions,
    )
    rows = selection["rows"]
    selected_stage = selection["selected_stage"]
    canonical_episode_ref = selection["episode_ref"]
    warnings = selection["warnings"]

    report_json_path: Path | None = None
    report_markdown_path: Path | None = None
    run_mode = RUN_MODE_CONFIRMED if confirm else RUN_MODE_DRY_RUN

    if confirm:
        if selected_stage in _EXECUTABLE_STAGES:
            rows = [
                _execute_selected_stage(
                    selected_stage=selected_stage,
                    podcast_id=podcast_id,
                    selector=selector,
                    episode_ref=canonical_episode_ref,
                    model=model,
                    device=device,
                    compute_type=compute_type,
                    vad_filter=vad_filter,
                    force=force,
                    allow_partial=allow_partial,
                    max_actions=max_actions,
                )
            ]
        elif selected_stage == STAGE_COMPLETED:
            selected_stage = STAGE_BLOCKED
            rows = _block_completed_rows(rows)
        report_paths = storage.corpus_episode_workflow_run_asset_paths(podcast_id)
        report_json_path = report_paths.json_path
        report_markdown_path = report_paths.markdown_path
        warnings = [*warnings, *_confirmed_warnings(rows)]

    result = CorpusEpisodeWorkflowRunResult(
        podcast_id=podcast_id,
        run_mode=run_mode,
        confirm=confirm,
        selector=selector,
        episode_ref=canonical_episode_ref,
        stage=normalized_stage,
        selected_stage=selected_stage,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        filters=CorpusEpisodeWorkflowRunFilter(selector, normalized_stage, max_actions),
        counts=_counts(rows, warnings),
        rows=rows,
        warnings=warnings,
        not_investment_advice=True,
    )
    if confirm:
        _write_run_report(result)
    return result


def result_to_dict(result: CorpusEpisodeWorkflowRunResult) -> dict[str, Any]:
    """Serialize a workflow result into the public JSON-compatible shape."""

    payload = {
        "podcast_id": result.podcast_id,
        "run_mode": result.run_mode,
        "confirm": result.confirm,
        "selector": result.selector,
        "episode_ref": result.episode_ref,
        "stage": result.stage,
        "selected_stage": result.selected_stage,
        "report_json_path": _path_or_none(result.report_json_path),
        "report_markdown_path": _path_or_none(result.report_markdown_path),
        "filters": asdict(result.filters),
        **asdict(result.counts),
        "rows": [asdict(row) for row in result.rows],
        "warnings": [asdict(warning) for warning in result.warnings],
        "not_investment_advice": result.not_investment_advice,
    }
    return _sanitize_payload(payload)


def _select_next_stage(
    *,
    podcast_id: str,
    selector: str,
    max_actions: int | None,
) -> dict[str, Any]:
    try:
        intake_result = run_corpus_episode_intake(
            podcast_id,
            episode_ref=selector,
            confirm=False,
        )
    except Exception as exc:  # noqa: BLE001 - keep probe failures bounded.
        return _probe_failure(STAGE_INTAKE, None, exc)
    episode_ref = getattr(intake_result, "resolved_episode_ref", None)
    episode_ref = _safe_episode_ref(episode_ref)
    terminal_selection = _returned_terminal_selection(
        STAGE_INTAKE,
        episode_ref,
        intake_result,
    )
    if terminal_selection is not None:
        return terminal_selection

    if episode_ref is None:
        row = _stage_row(
            stage=STAGE_BLOCKED,
            status="blocked",
            reason="episode selector could not be resolved",
            source_result=intake_result,
        )
        return {
            "selected_stage": STAGE_BLOCKED,
            "episode_ref": None,
            "rows": [row],
            "warnings": [],
        }

    if not _episode_seed_exists(podcast_id, episode_ref):
        row = _stage_row(
            stage=STAGE_INTAKE,
            status="selected",
            reason="episode seed metadata is missing",
            source_result=intake_result,
            source_row=_first_row(intake_result),
        )
        return {
            "selected_stage": STAGE_INTAKE,
            "episode_ref": episode_ref,
            "rows": [row],
            "warnings": [],
        }

    try:
        audio_result = run_corpus_audio_download(
            podcast_id,
            episode_ref=episode_ref,
            confirm=False,
        )
    except Exception as exc:  # noqa: BLE001 - keep probe failures bounded.
        return _probe_failure(STAGE_AUDIO_DOWNLOAD, episode_ref, exc)
    terminal_selection = _returned_terminal_selection(
        STAGE_AUDIO_DOWNLOAD,
        episode_ref,
        audio_result,
    )
    if terminal_selection is not None:
        return terminal_selection
    audio_selected = _first_status_row(audio_result, "selected")
    if audio_selected is not None:
        return {
            "selected_stage": STAGE_AUDIO_DOWNLOAD,
            "episode_ref": episode_ref,
            "rows": [
                _stage_row(
                    stage=STAGE_AUDIO_DOWNLOAD,
                    status="selected",
                    reason="audio download is the next ready action",
                    source_result=audio_result,
                    source_row=audio_selected,
                )
            ],
            "warnings": [],
        }

    try:
        transcription_result = run_corpus_local_transcription(
            podcast_id,
            episode_ref=episode_ref,
            confirm=False,
        )
    except Exception as exc:  # noqa: BLE001 - keep probe failures bounded.
        return _probe_failure(STAGE_LOCAL_TRANSCRIPTION, episode_ref, exc)
    terminal_selection = _returned_terminal_selection(
        STAGE_LOCAL_TRANSCRIPTION,
        episode_ref,
        transcription_result,
    )
    if terminal_selection is not None:
        return terminal_selection
    transcription_selected = _first_status_row(transcription_result, "selected")
    if transcription_selected is not None:
        return {
            "selected_stage": STAGE_LOCAL_TRANSCRIPTION,
            "episode_ref": episode_ref,
            "rows": [
                _stage_row(
                    stage=STAGE_LOCAL_TRANSCRIPTION,
                    status="selected",
                    reason="local transcription is the next ready action",
                    source_result=transcription_result,
                    source_row=transcription_selected,
                )
            ],
            "warnings": [],
        }

    try:
        remediation_result = run_corpus_remediation(
            podcast_id,
            confirm=False,
            episode_ref=episode_ref,
            max_actions=max_actions,
        )
    except Exception as exc:  # noqa: BLE001 - keep probe failures bounded.
        return _probe_failure(STAGE_DETERMINISTIC_REMEDIATION, episode_ref, exc)
    terminal_selection = _returned_terminal_selection(
        STAGE_DETERMINISTIC_REMEDIATION,
        episode_ref,
        remediation_result,
    )
    if terminal_selection is not None:
        return terminal_selection
    remediation_selected = _first_status_row(remediation_result, "selected")
    if remediation_selected is not None:
        return {
            "selected_stage": STAGE_DETERMINISTIC_REMEDIATION,
            "episode_ref": episode_ref,
            "rows": [
                _stage_row(
                    stage=STAGE_DETERMINISTIC_REMEDIATION,
                    status="selected",
                    reason="deterministic remediation is the next ready action",
                    source_result=remediation_result,
                    source_row=remediation_selected,
                )
            ],
            "warnings": [],
        }

    blocked_row = _first_status_row(remediation_result, "blocked")
    if blocked_row is not None:
        return {
            "selected_stage": STAGE_BLOCKED,
            "episode_ref": episode_ref,
            "rows": [
                _stage_row(
                    stage=STAGE_BLOCKED,
                    status="blocked",
                    reason="next workflow stage is blocked",
                    source_result=remediation_result,
                    source_row=blocked_row,
                )
            ],
            "warnings": [],
        }

    manual_rows = [
        _stage_row(
            stage=_safe_stage_name(getattr(row, "artifact_family", "manual")),
            status="manual_only",
            reason=getattr(row, "reason", "manual follow-up is required"),
            source_result=remediation_result,
            source_row=row,
        )
        for row in getattr(remediation_result, "rows", [])
        if getattr(row, "outcome_status", None) == "excluded"
    ]
    warnings = _manual_follow_up_warnings(episode_ref) if manual_rows else []
    completed_row = CorpusEpisodeWorkflowRunRow(
        stage=STAGE_COMPLETED,
        status="completed",
        reason="no executable safe workflow stage remains",
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=_source_report_paths(remediation_result),
        stage_counts=_stage_counts(remediation_result),
        warnings=[],
    )
    return {
        "selected_stage": STAGE_COMPLETED,
        "episode_ref": episode_ref,
        "rows": [*manual_rows, completed_row],
        "warnings": warnings,
    }


def _execute_selected_stage(
    *,
    selected_stage: str,
    podcast_id: str,
    selector: str,
    episode_ref: str | None,
    model: str | None,
    device: str,
    compute_type: str,
    vad_filter: bool,
    force: bool,
    allow_partial: bool,
    max_actions: int | None,
) -> CorpusEpisodeWorkflowRunRow:
    try:
        if selected_stage == STAGE_INTAKE:
            result = run_corpus_episode_intake(
                podcast_id,
                episode_ref=selector,
                confirm=True,
            )
        elif selected_stage == STAGE_AUDIO_DOWNLOAD:
            result = run_corpus_audio_download(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
            )
        elif selected_stage == STAGE_LOCAL_TRANSCRIPTION:
            result = run_corpus_local_transcription(
                podcast_id,
                episode_ref=episode_ref,
                confirm=True,
                model=model,
                device=device,
                compute_type=compute_type,
                vad_filter=vad_filter,
            )
        elif selected_stage == STAGE_DETERMINISTIC_REMEDIATION:
            result = run_corpus_remediation(
                podcast_id,
                confirm=True,
                episode_ref=episode_ref,
                force=force,
                allow_partial=allow_partial,
                max_actions=max_actions,
            )
        else:
            return CorpusEpisodeWorkflowRunRow(
                stage=selected_stage,
                status="blocked",
                reason="selected workflow stage is not executable",
                planned_reads=[],
                planned_writes=[],
                output_paths=[],
                source_report_paths=[],
                stage_counts={},
                warnings=[],
            )
    except Exception as exc:  # noqa: BLE001 - contain one selected stage attempt.
        return CorpusEpisodeWorkflowRunRow(
            stage=selected_stage,
            status="failed",
            reason=f"stage failed: {_safe_exception_category(exc)}",
            planned_reads=[],
            planned_writes=[],
            output_paths=[],
            source_report_paths=[],
            stage_counts={},
            warnings=[f"stage failed: {_safe_exception_category(exc)}"],
        )

    return _stage_row(
        stage=selected_stage,
        status=_confirmed_status(result),
        reason=f"{selected_stage} {_confirmed_status(result)}",
        source_result=result,
        source_row=_first_row(result),
    )


def _returned_terminal_selection(
    stage: str,
    episode_ref: str | None,
    result: Any,
) -> dict[str, Any] | None:
    for row in getattr(result, 'rows', []):
        status = getattr(row, 'outcome_status', None)
        if status not in {'failed', 'rejected', 'blocked'}:
            continue
        return {
            'selected_stage': STAGE_BLOCKED,
            'episode_ref': episode_ref,
            'rows': [
                _stage_row(
                    stage=stage,
                    status=status,
                    reason=getattr(row, 'reason', 'stage probe returned terminal outcome'),
                    source_result=result,
                    source_row=row,
                )
            ],
            'warnings': [],
        }
    return None


def _probe_failure(
    stage: str,
    episode_ref: str | None,
    exc: Exception,
) -> dict[str, Any]:
    failed_stage = stage
    stage = STAGE_BLOCKED
    return {
        "selected_stage": stage,
        "episode_ref": episode_ref,
        "rows": [
            CorpusEpisodeWorkflowRunRow(
                stage=failed_stage,
                status="failed",
                reason=f"stage probe failed: {_safe_exception_category(exc)}",
                planned_reads=[],
                planned_writes=[],
                output_paths=[],
                source_report_paths=[],
                stage_counts={},
                warnings=[f"stage probe failed: {_safe_exception_category(exc)}"],
            )
        ],
        "warnings": [],
    }


def _confirmed_status(result: Any) -> str:
    counts = getattr(result, "counts", None)
    if counts is None:
        return "completed"
    if getattr(counts, "failed_count", 0):
        return "failed"
    if getattr(counts, "rejected_count", 0):
        return "rejected"
    if getattr(counts, "blocked_count", 0):
        return "blocked"
    if getattr(counts, "executed_count", 0) or getattr(counts, "downloaded_count", 0):
        return "executed"
    if getattr(counts, "seeded_count", 0):
        return "executed"
    if getattr(counts, "reused_count", 0):
        return "reused"
    if getattr(counts, "skipped_count", 0):
        return "skipped"
    return "completed"


def _stage_row(
    *,
    stage: str,
    status: str,
    reason: str,
    source_result: Any,
    source_row: Any | None = None,
) -> CorpusEpisodeWorkflowRunRow:
    reason = _workflow_owned_reason(stage, status, reason)
    try:
        source_row = replace(source_row, warnings=[])
    except (TypeError, ValueError):
        source_row = None
    return CorpusEpisodeWorkflowRunRow(
        stage=stage,
        status=status,
        reason=_safe_message(reason, "reason omitted by safety boundary"),
        planned_reads=_safe_list(getattr(source_row, "planned_reads", [])),
        planned_writes=_safe_list(getattr(source_row, "planned_writes", [])),
        output_paths=_safe_list(getattr(source_row, "output_paths", [])),
        source_report_paths=_source_report_paths(source_result),
        stage_counts=_stage_counts(source_result),
        warnings=_safe_list(getattr(source_row, "warnings", [])),
    )


def _workflow_owned_reason(stage: str, status: str, reason: Any) -> str:
    if status == 'manual_only':
        return 'manual follow-up is required'
    if isinstance(reason, str) and reason in _WORKFLOW_ROW_REASONS:
        return reason
    expected_stage_reason = f'{stage} {status}'
    if stage in _EXECUTABLE_STAGES and reason == expected_stage_reason:
        return expected_stage_reason
    if stage in _EXECUTABLE_STAGES and status in {'failed', 'rejected', 'blocked'}:
        return f'{stage} probe returned {status}'
    return 'dependency metadata omitted by safety boundary'


def _first_status_row(result: Any, status: str) -> Any | None:
    for row in getattr(result, "rows", []):
        if getattr(row, "outcome_status", None) == status:
            return row
    return None


def _first_row(result: Any) -> Any | None:
    rows = getattr(result, "rows", [])
    return rows[0] if rows else None


def _episode_seed_exists(podcast_id: str, episode_ref: str) -> bool:
    return storage.corpus_episode_seed_asset_path(podcast_id, episode_ref).exists()


def _counts(
    rows: list[CorpusEpisodeWorkflowRunRow],
    warnings: list[CorpusEpisodeWorkflowRunWarning],
) -> CorpusEpisodeWorkflowRunCounts:
    warning_count = len(warnings) + sum(len(row.warnings) for row in rows)
    return CorpusEpisodeWorkflowRunCounts(
        row_count=len(rows),
        selected_count=sum(row.status == "selected" for row in rows),
        executed_count=sum(row.status == "executed" for row in rows),
        reused_count=sum(row.status == "reused" for row in rows),
        failed_count=sum(row.status == "failed" for row in rows),
        skipped_count=sum(row.status == "skipped" for row in rows),
        blocked_count=sum(row.status == "blocked" for row in rows),
        rejected_count=sum(row.status == "rejected" for row in rows),
        manual_only_count=sum(row.status == "manual_only" for row in rows),
        warning_count=warning_count,
    )


def _confirmed_warnings(
    rows: list[CorpusEpisodeWorkflowRunRow],
) -> list[CorpusEpisodeWorkflowRunWarning]:
    if not rows:
        return []
    if any(row.status in {"executed", "reused"} for row in rows):
        return [
            CorpusEpisodeWorkflowRunWarning(
                scope="run",
                episode_ref=None,
                message=(
                    "Manual follow-up remains required after one workflow stage; "
                    "rerun dry-run to inspect the next stage and rebuild cache manually "
                    "if needed."
                ),
            )
        ]
    return []


def _block_completed_rows(
    rows: list[CorpusEpisodeWorkflowRunRow],
) -> list[CorpusEpisodeWorkflowRunRow]:
    blocked_rows: list[CorpusEpisodeWorkflowRunRow] = []
    converted = False
    for row in rows:
        if row.status == "completed":
            blocked_rows.append(
                replace(
                    row,
                    stage=STAGE_BLOCKED,
                    status="blocked",
                    reason="confirmed workflow has no executable safe next stage",
                )
            )
            converted = True
        else:
            blocked_rows.append(row)
    if converted:
        return blocked_rows
    return [
        CorpusEpisodeWorkflowRunRow(
            stage=STAGE_BLOCKED,
            status="blocked",
            reason="confirmed workflow has no executable safe next stage",
            planned_reads=[],
            planned_writes=[],
            output_paths=[],
            source_report_paths=[],
            stage_counts={},
            warnings=[],
        )
    ]


def _manual_follow_up_warnings(
    episode_ref: str | None,
) -> list[CorpusEpisodeWorkflowRunWarning]:
    return [
        CorpusEpisodeWorkflowRunWarning(
            scope="run",
            episode_ref=episode_ref,
            message=(
                "Manual follow-up remains required for excluded semantic, LLM, "
                "stock-lens, tool registry, cache rebuild, or batch work."
            ),
        )
    ]


def _write_run_report(result: CorpusEpisodeWorkflowRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    json_part_path = result.report_json_path.with_name(
        f"{result.report_json_path.name}.part"
    )
    markdown_part_path = result.report_markdown_path.with_name(
        f"{result.report_markdown_path.name}.part"
    )
    try:
        result.report_json_path.parent.mkdir(parents=True, exist_ok=True)
        json_part_path.unlink(missing_ok=True)
        markdown_part_path.unlink(missing_ok=True)
        json_part_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_part_path.write_text(_render_markdown(payload), encoding="utf-8")
        json_part_path.replace(result.report_json_path)
        markdown_part_path.replace(result.report_markdown_path)
    except OSError as exc:
        for part_path in (json_part_path, markdown_part_path):
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise CorpusEpisodeWorkflowRunnerFailedError(
            f"failed to write corpus episode workflow run report: {type(exc).__name__}"
        ) from exc


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Episode Workflow Run - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Run mode: {payload['run_mode']}",
        f"- Confirm: {payload['confirm']}",
        f"- Selector: {payload['selector']}",
        f"- Episode: {payload['episode_ref'] or 'none'}",
        f"- Stage: {payload['selected_stage']}",
        "",
        "## Summary Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "row_count",
        "selected_count",
        "executed_count",
        "reused_count",
        "failed_count",
        "skipped_count",
        "blocked_count",
        "rejected_count",
        "manual_only_count",
        "warning_count",
    ):
        lines.append(f"| {key} | {payload[key]} |")
    lines.extend(
        [
            "",
            "## Stage Outcomes",
            "",
            "| Stage | Status | Reason | Outputs | Warnings |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["stage"]),
                    _markdown_cell(row["status"]),
                    _markdown_cell(row["reason"]),
                    _markdown_cell(", ".join(row["output_paths"]) or "none"),
                    _markdown_cell(len(row["warnings"])),
                ]
            )
            + " |"
        )
    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in payload["warnings"]:
            lines.append(f"- {_markdown_cell(warning['message'])}")
    lines.extend(
        [
            "",
            "## Boundary Notice",
            "",
            "This corpus-episode-workflow-run artifact contains metadata, paths, counts, warnings, and outcomes only.",
            "Dry-run writes no workflow report and confirmed execution stops after one selected stage attempt.",
            "Semantic, LLM, stock-lens, tool registry, cache rebuild, and batch workflows remain manual.",
            "It omits unsafe source bodies, provider bodies, credentials, and diagnostic bodies.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _source_report_paths(result: Any) -> list[str]:
    paths: list[str] = []
    for attribute in ("report_json_path", "report_markdown_path"):
        value = getattr(result, attribute, None)
        if isinstance(value, Path):
            paths.append(str(value))
    return _safe_list(paths)


def _stage_counts(result: Any) -> dict[str, int]:
    counts = getattr(result, "counts", None)
    if counts is None:
        return {}
    return {
        key: value
        for key, value in asdict(counts).items()
        if isinstance(value, int)
    }


def _normalize_selector(value: str | None) -> str:
    if value is None:
        return DEFAULT_SELECTOR
    normalized = value.strip()
    return normalized or DEFAULT_SELECTOR


def _normalize_stage(value: str | None) -> str:
    if value is None:
        return STAGE_NEXT
    normalized = value.strip()
    return normalized or STAGE_NEXT


def _safe_stage_name(value: Any) -> str:
    if not isinstance(value, str) or not _SAFE_STAGE_NAME_PATTERN.fullmatch(value):
        return 'manual'
    text = str(value).strip() if value is not None else "manual"
    return text or "manual"


def _safe_episode_ref(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if not _SAFE_EPISODE_REF_PATTERN.fullmatch(value):
        return None
    return value


def _safe_exception_category(exc: Exception) -> str:
    return _safe_message(type(exc).__name__, "stage_dependency_error")


def _safe_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    values = [value for value in values if _is_safe_local_path(value)]
    return [
        _safe_message(str(value), "metadata omitted by safety boundary")
        for value in values
    ]


def _is_safe_local_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if not value or value != value.strip() or len(value) > 1024:
        return False
    if _URI_SCHEME_PATTERN.match(value) or value.startswith(('\\\\', '//')):
        return False
    if '?' in value or '#' in value or '|' in value:
        return False
    if '/' not in value and '\\' not in value:
        return False
    if any(character.isspace() for character in value):
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    path_without_drive = (
        value[2:] if re.match(r'^[A-Za-z]:[\\/]', value) else value
    )
    if ':' in path_without_drive:
        return False
    parts = re.split(r'[\\/]', value)
    if re.match(r'^[A-Za-z]:[\\/]', value):
        path_parts = parts[1:]
    elif value.startswith('/'):
        path_parts = parts[1:]
    else:
        path_parts = parts
    if not path_parts or any(
        not part
        or part in {'.', '..'}
        or not _SAFE_PATH_COMPONENT_PATTERN.fullmatch(part)
        for part in path_parts
    ):
        return False
    if not _SAFE_FILENAME_PATTERN.fullmatch(path_parts[-1]):
        return False
    return _safe_message(value, '') == value


def _safe_message(value: str, replacement: str) -> str:
    text = _QUERY_PATTERN.sub("[redacted-query]", str(value))
    lowered = text.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS):
        return replacement
    return text


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _safe_message(value, "metadata omitted by safety boundary")
    return value


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")
