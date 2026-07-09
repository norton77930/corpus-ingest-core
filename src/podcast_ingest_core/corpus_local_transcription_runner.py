from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

from . import storage
from .corpus_remediation_plan import generate_corpus_remediation_plan
from .errors import CorpusLocalTranscriptionRunnerFailedError
from .models import (
    CorpusLocalTranscriptionOutcomeCounts,
    CorpusLocalTranscriptionRunFilter,
    CorpusLocalTranscriptionRunResult,
    CorpusLocalTranscriptionRunRow,
    CorpusLocalTranscriptionRunWarning,
)
from .transcriber import transcribe_episode


RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
TRANSCRIPT_ACTION_FAMILY = "transcript"
TRANSCRIPT_STATUS_MISSING = "missing"
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "raw transcript",
    "prompt text",
    "raw llm output",
    "api_key=",
    "secret-value",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


def run_corpus_local_transcription(
    podcast_id: str,
    *,
    episode_ref: str | None = None,
    confirm: bool = False,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
) -> CorpusLocalTranscriptionRunResult:
    """Run dry-run or confirmed local transcription for one podcast corpus."""

    source_result = generate_corpus_remediation_plan(podcast_id)
    plan_payload = _load_plan_payload(source_result.plan_json_path)
    normalized_episode_ref = _normalize_episode_ref(episode_ref)
    if confirm and normalized_episode_ref is None:
        raise CorpusLocalTranscriptionRunnerFailedError(
            "confirm requires episode"
        )
    filters = CorpusLocalTranscriptionRunFilter(episode_ref=normalized_episode_ref)
    rows = _select_rows(
        podcast_id=podcast_id,
        plan_payload=plan_payload,
        filters=filters,
        confirmed=confirm,
    )
    if confirm:
        rows = _with_missing_requested_episode_row(
            rows=rows,
            podcast_id=podcast_id,
            filters=filters,
        )
        report_paths = storage.corpus_local_transcription_run_asset_paths(podcast_id)
        rows = _execute_confirmed_rows(
            rows=rows,
            model=model,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
        )
        warnings = _confirmed_warnings(rows)
        result = CorpusLocalTranscriptionRunResult(
            podcast_id=podcast_id,
            run_mode=RUN_MODE_CONFIRMED,
            confirm=True,
            source_remediation_plan_json_path=source_result.plan_json_path,
            source_remediation_plan_markdown_path=source_result.plan_markdown_path,
            report_json_path=report_paths.json_path,
            report_markdown_path=report_paths.markdown_path,
            filters=filters,
            counts=_counts(rows, warnings),
            rows=rows,
            warnings=warnings,
            not_investment_advice=True,
        )
        _write_run_report(result)
        return result
    return CorpusLocalTranscriptionRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_DRY_RUN,
        confirm=False,
        source_remediation_plan_json_path=source_result.plan_json_path,
        source_remediation_plan_markdown_path=source_result.plan_markdown_path,
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=_counts(rows, []),
        rows=rows,
        warnings=[],
        not_investment_advice=True,
    )


def result_to_dict(result: CorpusLocalTranscriptionRunResult) -> dict[str, Any]:
    """Serialize a local transcription runner result into public JSON shape."""

    return {
        "podcast_id": result.podcast_id,
        "run_mode": result.run_mode,
        "confirm": result.confirm,
        "source_remediation_plan_json_path": str(result.source_remediation_plan_json_path),
        "source_remediation_plan_markdown_path": str(
            result.source_remediation_plan_markdown_path
        ),
        "report_json_path": str(result.report_json_path) if result.report_json_path else None,
        "report_markdown_path": (
            str(result.report_markdown_path) if result.report_markdown_path else None
        ),
        "filters": asdict(result.filters),
        **asdict(result.counts),
        "rows": [asdict(row) for row in result.rows],
        "warnings": [asdict(warning) for warning in result.warnings],
        "not_investment_advice": result.not_investment_advice,
    }


def _load_plan_payload(plan_json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(plan_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusLocalTranscriptionRunnerFailedError(
            f"failed to read corpus remediation plan: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CorpusLocalTranscriptionRunnerFailedError(
            "corpus remediation plan root must be an object"
        )
    return payload


def _select_rows(
    *,
    podcast_id: str,
    plan_payload: dict[str, Any],
    filters: CorpusLocalTranscriptionRunFilter,
    confirmed: bool,
) -> list[CorpusLocalTranscriptionRunRow]:
    rows: list[CorpusLocalTranscriptionRunRow] = []
    for episode_payload in _episode_payloads(plan_payload):
        rows.append(
            _row_for_episode_transcript(
                podcast_id=podcast_id,
                episode_payload=episode_payload,
                filters=filters,
                confirmed=confirmed,
            )
        )
        for action_payload in _action_payloads(episode_payload):
            family = _safe_text(action_payload.get("artifact_family"), "unknown")
            if family == TRANSCRIPT_ACTION_FAMILY:
                continue
            rows.append(
                _row_for_non_transcript_action(
                    podcast_id=podcast_id,
                    episode_payload=episode_payload,
                    action_payload=action_payload,
                    confirmed=confirmed,
                )
            )
    return sorted(rows, key=_row_sort_key)


def _with_missing_requested_episode_row(
    *,
    rows: list[CorpusLocalTranscriptionRunRow],
    podcast_id: str,
    filters: CorpusLocalTranscriptionRunFilter,
) -> list[CorpusLocalTranscriptionRunRow]:
    if filters.episode_ref is None:
        return rows
    if any(row.episode_ref == filters.episode_ref for row in rows):
        return rows
    requested_row = CorpusLocalTranscriptionRunRow(
        action_id=f"{filters.episode_ref}:transcript",
        podcast_id=podcast_id,
        episode_ref=filters.episode_ref,
        title=filters.episode_ref,
        transcript_status="unknown",
        audio_status="unknown",
        audio_path=None,
        outcome_status="rejected",
        reason="requested episode is not present in refreshed remediation plan",
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        warnings=[],
    )
    return sorted([*rows, requested_row], key=_row_sort_key)


def _episode_payloads(plan_payload: dict[str, Any]) -> list[dict[str, Any]]:
    episodes = plan_payload.get("episodes")
    if not isinstance(episodes, list):
        return []
    return [episode for episode in episodes if isinstance(episode, dict)]


def _action_payloads(episode_payload: dict[str, Any]) -> list[dict[str, Any]]:
    actions = episode_payload.get("actions")
    if not isinstance(actions, list):
        return []
    return [action for action in actions if isinstance(action, dict)]


def _row_for_episode_transcript(
    *,
    podcast_id: str,
    episode_payload: dict[str, Any],
    filters: CorpusLocalTranscriptionRunFilter,
    confirmed: bool,
) -> CorpusLocalTranscriptionRunRow:
    episode_ref = _safe_text(episode_payload.get("episode_ref"), "unknown")
    artifact_status = _artifact_status(episode_payload)
    transcript_payload = _status_payload(artifact_status, "transcript")
    audio_payload = _status_payload(artifact_status, "audio")
    action_payload = _transcript_action(episode_payload)
    action_id = _safe_text(
        action_payload.get("action_id") if action_payload else None,
        f"{episode_ref}:transcript",
    )
    transcript_status = _status_text(transcript_payload)
    audio_status = _status_text(audio_payload)
    audio_path = _local_audio_path(audio_payload)
    outcome_status, reason = _transcript_outcome(
        action_payload=action_payload,
        filters=filters,
        confirmed=confirmed,
        episode_ref=episode_ref,
        transcript_status=transcript_status,
        audio_status=audio_status,
        audio_path=audio_path,
    )
    planned_writes = _planned_transcript_writes(podcast_id, episode_ref)
    return CorpusLocalTranscriptionRunRow(
        action_id=action_id,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=episode_ref,
        transcript_status=transcript_status,
        audio_status=audio_status,
        audio_path=str(audio_path) if audio_path else None,
        outcome_status=outcome_status,
        reason=reason,
        planned_reads=[str(audio_path)] if audio_path else [],
        planned_writes=planned_writes,
        output_paths=[],
        warnings=_source_warnings(episode_payload, TRANSCRIPT_ACTION_FAMILY),
    )


def _row_for_non_transcript_action(
    *,
    podcast_id: str,
    episode_payload: dict[str, Any],
    action_payload: dict[str, Any],
    confirmed: bool,
) -> CorpusLocalTranscriptionRunRow:
    episode_ref = _safe_text(episode_payload.get("episode_ref"), "unknown")
    artifact_status = _artifact_status(episode_payload)
    transcript_status = _status_text(_status_payload(artifact_status, "transcript"))
    audio_status = _status_text(_status_payload(artifact_status, "audio"))
    family = _safe_text(action_payload.get("artifact_family"), "unknown")
    action_id = _safe_text(action_payload.get("action_id"), f"{episode_ref}:{family}")
    outcome_status = "rejected" if confirmed else "skipped"
    return CorpusLocalTranscriptionRunRow(
        action_id=action_id,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=episode_ref,
        transcript_status=transcript_status,
        audio_status=audio_status,
        audio_path=None,
        outcome_status=outcome_status,
        reason=f"{family} is outside local transcription runner v1",
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        warnings=_source_warnings(episode_payload, family),
    )


def _transcript_outcome(
    *,
    action_payload: dict[str, Any] | None,
    filters: CorpusLocalTranscriptionRunFilter,
    confirmed: bool,
    episode_ref: str,
    transcript_status: str,
    audio_status: str,
    audio_path: Path | None,
) -> tuple[str, str]:
    skipped_status = "rejected" if confirmed else "skipped"
    if filters.episode_ref is not None and filters.episode_ref != episode_ref:
        return "skipped", "episode filter does not match"
    if transcript_status != TRANSCRIPT_STATUS_MISSING:
        return skipped_status, f"transcript status is {transcript_status}"
    if action_payload is None:
        return skipped_status, "transcript remediation action is missing"
    source_status = _safe_text(action_payload.get("status"), "unknown")
    if source_status != "ready":
        return skipped_status, f"source action status is {source_status}"
    if audio_status != "available":
        return skipped_status, f"audio status is {audio_status}"
    if audio_path is None:
        return skipped_status, "local audio path is missing"
    if not audio_path.exists():
        return skipped_status, "local audio path does not exist"
    return "selected", "local audio available and transcript missing"


def _counts(
    rows: list[CorpusLocalTranscriptionRunRow],
    warnings: list[CorpusLocalTranscriptionRunWarning],
) -> CorpusLocalTranscriptionOutcomeCounts:
    warning_count = len(warnings) + sum(len(row.warnings) for row in rows)
    return CorpusLocalTranscriptionOutcomeCounts(
        row_count=len(rows),
        selected_count=sum(row.outcome_status == "selected" for row in rows),
        executed_count=sum(row.outcome_status == "executed" for row in rows),
        reused_count=sum(row.outcome_status == "reused" for row in rows),
        failed_count=sum(row.outcome_status == "failed" for row in rows),
        skipped_count=sum(row.outcome_status == "skipped" for row in rows),
        rejected_count=sum(row.outcome_status == "rejected" for row in rows),
        warning_count=warning_count,
    )


def _execute_confirmed_rows(
    *,
    rows: list[CorpusLocalTranscriptionRunRow],
    model: str | None,
    device: str,
    compute_type: str,
    vad_filter: bool,
) -> list[CorpusLocalTranscriptionRunRow]:
    updated_rows: list[CorpusLocalTranscriptionRunRow] = []
    for row in rows:
        if row.outcome_status != "selected":
            updated_rows.append(row)
            continue
        if row.audio_path is None:
            updated_rows.append(
                replace(
                    row,
                    outcome_status="rejected",
                    reason="local audio path is missing",
                )
            )
            continue
        try:
            asset = transcribe_episode(
                row.podcast_id,
                row.episode_ref,
                model=model,
                device=device,
                compute_type=compute_type,
                vad_filter=vad_filter,
                force=False,
                audio_path=Path(row.audio_path),
            )
        except Exception as exc:  # noqa: BLE001 - record per-episode failure safely.
            updated_rows.append(
                replace(
                    row,
                    outcome_status="failed",
                    reason=f"transcription failed: {type(exc).__name__}",
                    warnings=[
                        *row.warnings,
                        f"transcription failed: {type(exc).__name__}",
                    ],
                )
            )
            continue
        outcome = "reused" if getattr(asset, "already_exists", False) else "executed"
        updated_rows.append(
            replace(
                row,
                outcome_status=outcome,
                reason=f"transcript {outcome}",
                output_paths=_transcript_output_paths(asset),
            )
        )
    return updated_rows


def _confirmed_warnings(
    rows: list[CorpusLocalTranscriptionRunRow],
) -> list[CorpusLocalTranscriptionRunWarning]:
    if any(row.outcome_status in {"executed", "reused"} for row in rows):
        return [
            CorpusLocalTranscriptionRunWarning(
                scope="run",
                episode_ref=None,
                message=(
                    "SQLite cache metadata may be stale after transcript writes; "
                    "update cache manually if search metadata must include this run."
                ),
            )
        ]
    return []


def _transcript_output_paths(asset: Any) -> list[str]:
    paths: list[str] = []
    for attribute in ("json_path", "text_path", "srt_path"):
        value = getattr(asset, attribute, None)
        if isinstance(value, Path):
            paths.append(str(value))
    return paths


def _write_run_report(result: CorpusLocalTranscriptionRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    markdown = _render_markdown(payload)
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
        markdown_part_path.write_text(markdown, encoding="utf-8")
        json_part_path.replace(result.report_json_path)
        markdown_part_path.replace(result.report_markdown_path)
    except OSError as exc:
        for part_path in (json_part_path, markdown_part_path):
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise CorpusLocalTranscriptionRunnerFailedError(
            f"failed to write corpus local transcription run report: {exc}"
        ) from exc


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Local Transcription Run - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Run mode: {payload['run_mode']}",
        f"- Confirm: {payload['confirm']}",
        f"- Episode: {payload['filters']['episode_ref'] or 'none'}",
        f"- Source remediation plan: {payload['source_remediation_plan_json_path']}",
        f"- Source remediation plan Markdown: {payload['source_remediation_plan_markdown_path']}",
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
        "rejected_count",
        "warning_count",
    ):
        lines.append(f"| {key} | {payload[key]} |")
    lines.extend(
        [
            "",
            "## Local Transcription Outcomes",
            "",
            "| Episode | Transcript | Audio | Outcome | Reason | Outputs | Warnings |",
            "| --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["episode_ref"]),
                    _markdown_cell(row["transcript_status"]),
                    _markdown_cell(row["audio_status"]),
                    _markdown_cell(row["outcome_status"]),
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
            "This corpus-local-transcription-run artifact contains metadata, paths, counts, warnings, and outcomes only.",
            "It does not download audio, call RSS or network providers, call LLM providers, invoke MCP tools, run semantic workflows, execute downstream remediation, generate stock-lens artifacts, or update SQLite cache automatically.",
            "It does not include raw transcript text, prompt text, raw LLM output, secret values, traceback bodies, market claims, or investment recommendations.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _artifact_status(episode_payload: dict[str, Any]) -> dict[str, Any]:
    artifact_status = episode_payload.get("artifact_status")
    return artifact_status if isinstance(artifact_status, dict) else {}


def _status_payload(artifact_status: dict[str, Any], family: str) -> dict[str, Any]:
    payload = artifact_status.get(family)
    return payload if isinstance(payload, dict) else {}


def _transcript_action(episode_payload: dict[str, Any]) -> dict[str, Any] | None:
    for action_payload in _action_payloads(episode_payload):
        if _safe_text(action_payload.get("artifact_family"), "") == TRANSCRIPT_ACTION_FAMILY:
            return action_payload
    return None


def _status_text(status_payload: dict[str, Any]) -> str:
    status = status_payload.get("status")
    return status if isinstance(status, str) and status.strip() else "missing"


def _local_audio_path(audio_payload: dict[str, Any]) -> Path | None:
    path = audio_payload.get("path")
    if isinstance(path, str) and path.strip():
        return Path(path)
    paths = audio_payload.get("paths")
    if isinstance(paths, dict):
        for value in paths.values():
            if isinstance(value, str) and value.strip():
                return Path(value)
    return None


def _planned_transcript_writes(
    podcast_id: str,
    episode_ref: str,
) -> list[str]:
    paths = storage.transcript_asset_paths(podcast_id, episode_ref, episode_ref)
    return [str(paths.json_path), str(paths.text_path), str(paths.srt_path)]


def _source_warnings(episode_payload: dict[str, Any], family: str) -> list[str]:
    warnings: list[str] = []
    for warning in episode_payload.get("warnings", []):
        if isinstance(warning, dict):
            warning_family = warning.get("artifact_family")
            message = warning.get("message")
            if warning_family in {family, None} and isinstance(message, str):
                warnings.append(f"source {family} warning omitted by safety boundary")
        elif isinstance(warning, str):
            warnings.append("source warning omitted by safety boundary")
    return warnings


def _row_sort_key(row: CorpusLocalTranscriptionRunRow) -> tuple[str, str]:
    return (row.episode_ref, row.action_id)


def _safe_text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _normalize_episode_ref(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _safe_message(value: str, replacement: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS):
        return replacement
    return value


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")
