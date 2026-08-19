from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

from . import storage
from .corpus_remediation_plan import generate_corpus_remediation_plan
from .downloader import download_audio
from .errors import CorpusAudioDownloadRunnerFailedError
from .run_report_io import write_part_staged_report_pair
from .models import (
    VIDEO_SEED_SOURCES,
    CorpusAudioDownloadOutcomeCounts,
    CorpusAudioDownloadRunFilter,
    CorpusAudioDownloadRunResult,
    CorpusAudioDownloadRunRow,
    CorpusAudioDownloadRunWarning,
    CorpusRemediationPlanResult,
)


RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
AUDIO_ACTION_FAMILY = "audio"
AUDIO_STATUS_MISSING = "missing"
_FAMILY_ORDER = {
    "audio": 1,
    "transcript": 2,
    "extractive_summary": 3,
    "mentions": 4,
    "semantic_summary": 5,
    "semantic_review": 6,
    "episode_intelligence": 7,
    "industry_mapping": 8,
    "external_boundary": 9,
}
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "http://",
    "https://",
    "?token",
    "api_key",
    "token=",
    "bearer ",
    "secret",
    "prompt text",
    "raw llm output",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


def run_corpus_audio_download(
    podcast_id: str,
    *,
    episode_ref: str | None = None,
    confirm: bool = False,
) -> CorpusAudioDownloadRunResult:
    """Preview or run one bounded corpus audio download."""

    source_result = generate_corpus_remediation_plan(podcast_id)
    plan_payload = _load_plan_payload(source_result.plan_json_path)
    normalized_episode_ref = _normalize_episode_ref(episode_ref)
    if confirm and normalized_episode_ref is None:
        raise CorpusAudioDownloadRunnerFailedError("confirm requires episode")
    if not confirm:
        return _preview_corpus_audio_download_from_plan(
            podcast_id,
            plan_result=source_result,
            plan_payload=plan_payload,
            episode_ref=normalized_episode_ref,
            source_persisted=True,
        )

    filters = CorpusAudioDownloadRunFilter(episode_ref=normalized_episode_ref)
    source_plan_paths = [
        str(source_result.plan_json_path),
        str(source_result.plan_markdown_path),
    ]
    rows = _select_rows(
        podcast_id=podcast_id,
        plan_payload=plan_payload,
        filters=filters,
        confirmed=True,
        source_plan_paths=source_plan_paths,
    )
    rows = _with_missing_requested_episode_row(
        rows=rows,
        podcast_id=podcast_id,
        filters=filters,
        source_plan_paths=source_plan_paths,
    )
    rows = _execute_confirmed_rows(rows)
    warnings = _confirmed_warnings(rows)
    report_paths = storage.corpus_audio_download_run_asset_paths(podcast_id)
    result = CorpusAudioDownloadRunResult(
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


def _preview_corpus_audio_download_from_plan(
    podcast_id: str,
    *,
    plan_result: CorpusRemediationPlanResult,
    plan_payload: dict[str, Any],
    episode_ref: str | None,
    source_persisted: bool,
) -> CorpusAudioDownloadRunResult:
    filters = CorpusAudioDownloadRunFilter(
        episode_ref=_normalize_episode_ref(episode_ref)
    )
    source_plan_reads = (
        [
            str(plan_result.plan_json_path),
            str(plan_result.plan_markdown_path),
        ]
        if source_persisted
        else ["in-memory corpus snapshot"]
    )
    rows = _select_rows(
        podcast_id=podcast_id,
        plan_payload=plan_payload,
        filters=filters,
        confirmed=False,
        source_plan_paths=source_plan_reads,
    )
    return CorpusAudioDownloadRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_DRY_RUN,
        confirm=False,
        source_remediation_plan_json_path=plan_result.plan_json_path,
        source_remediation_plan_markdown_path=plan_result.plan_markdown_path,
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=_counts(rows, []),
        rows=rows,
        warnings=[],
        not_investment_advice=True,
    )


def result_to_dict(result: CorpusAudioDownloadRunResult) -> dict[str, Any]:
    """Serialize an audio download runner result into public JSON shape."""

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
        raise CorpusAudioDownloadRunnerFailedError(
            f"failed to read corpus remediation plan: {type(exc).__name__}"
        ) from exc
    if not isinstance(payload, dict):
        raise CorpusAudioDownloadRunnerFailedError(
            "corpus remediation plan root must be an object"
        )
    return payload


def _select_rows(
    *,
    podcast_id: str,
    plan_payload: dict[str, Any],
    filters: CorpusAudioDownloadRunFilter,
    confirmed: bool,
    source_plan_paths: list[str],
) -> list[CorpusAudioDownloadRunRow]:
    rows: list[CorpusAudioDownloadRunRow] = []
    for episode_payload in _episode_payloads(plan_payload):
        rows.append(
            _row_for_episode_audio(
                podcast_id=podcast_id,
                episode_payload=episode_payload,
                filters=filters,
                confirmed=confirmed,
                source_plan_paths=source_plan_paths,
            )
        )
        for action_payload in _action_payloads(episode_payload):
            family = _safe_text(action_payload.get("artifact_family"), "unknown")
            if family == AUDIO_ACTION_FAMILY:
                continue
            rows.append(
                _row_for_non_audio_action(
                    podcast_id=podcast_id,
                    episode_payload=episode_payload,
                    action_payload=action_payload,
                    confirmed=confirmed,
                    source_plan_paths=source_plan_paths,
                )
            )
    return sorted(rows, key=_row_sort_key)


def _with_missing_requested_episode_row(
    *,
    rows: list[CorpusAudioDownloadRunRow],
    podcast_id: str,
    filters: CorpusAudioDownloadRunFilter,
    source_plan_paths: list[str],
) -> list[CorpusAudioDownloadRunRow]:
    if filters.episode_ref is None:
        return rows
    if any(row.episode_ref == filters.episode_ref for row in rows):
        return rows
    requested_row = CorpusAudioDownloadRunRow(
        action_id=f"{filters.episode_ref}:audio",
        podcast_id=podcast_id,
        episode_ref=filters.episode_ref,
        audio_status="unknown",
        outcome_status="rejected",
        reason="requested episode is not present in refreshed remediation plan",
        planned_reads=source_plan_paths,
        planned_writes=[],
        local_audio_path=None,
        content_type=None,
        size_bytes=None,
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


def _row_for_episode_audio(
    *,
    podcast_id: str,
    episode_payload: dict[str, Any],
    filters: CorpusAudioDownloadRunFilter,
    confirmed: bool,
    source_plan_paths: list[str],
) -> CorpusAudioDownloadRunRow:
    episode_ref = _safe_text(episode_payload.get("episode_ref"), "unknown")
    artifact_status = _artifact_status(episode_payload)
    audio_payload = _status_payload(artifact_status, AUDIO_ACTION_FAMILY)
    action_payload = _audio_action(episode_payload)
    action_id = _safe_text(
        action_payload.get("action_id") if action_payload else None,
        f"{episode_ref}:audio",
    )
    audio_status = _status_text(audio_payload)
    outcome_status, reason = _audio_outcome(
        action_payload=action_payload,
        filters=filters,
        confirmed=confirmed,
        episode_ref=episode_ref,
        audio_status=audio_status,
        episode_payload=episode_payload,
    )
    return CorpusAudioDownloadRunRow(
        action_id=action_id,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        audio_status=audio_status,
        outcome_status=outcome_status,
        reason=reason,
        planned_reads=source_plan_paths,
        planned_writes=_planned_audio_writes(podcast_id, episode_ref),
        local_audio_path=_local_audio_path(audio_payload),
        content_type=None,
        size_bytes=None,
        warnings=_source_warnings(episode_payload, AUDIO_ACTION_FAMILY),
    )


def _row_for_non_audio_action(
    *,
    podcast_id: str,
    episode_payload: dict[str, Any],
    action_payload: dict[str, Any],
    confirmed: bool,
    source_plan_paths: list[str],
) -> CorpusAudioDownloadRunRow:
    episode_ref = _safe_text(episode_payload.get("episode_ref"), "unknown")
    artifact_status = _artifact_status(episode_payload)
    audio_status = _status_text(_status_payload(artifact_status, AUDIO_ACTION_FAMILY))
    family = _safe_text(action_payload.get("artifact_family"), "unknown")
    action_id = _safe_text(action_payload.get("action_id"), f"{episode_ref}:{family}")
    return CorpusAudioDownloadRunRow(
        action_id=action_id,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        audio_status=audio_status,
        outcome_status="skipped",
        reason=f"{family} is outside audio download runner v1",
        planned_reads=source_plan_paths,
        planned_writes=[],
        local_audio_path=None,
        content_type=None,
        size_bytes=None,
        warnings=_source_warnings(episode_payload, family),
    )


def _video_seed_source(episode_payload: dict[str, Any]) -> str | None:
    source_metadata = episode_payload.get("source_metadata")
    if not isinstance(source_metadata, dict):
        return None
    episode_seed = source_metadata.get("episode_seed")
    if not isinstance(episode_seed, dict):
        return None
    seed_source = episode_seed.get("seed_source")
    if seed_source in VIDEO_SEED_SOURCES:
        return str(seed_source)
    return None


def _audio_outcome(
    *,
    action_payload: dict[str, Any] | None,
    filters: CorpusAudioDownloadRunFilter,
    confirmed: bool,
    episode_ref: str,
    audio_status: str,
    episode_payload: dict[str, Any] | None = None,
) -> tuple[str, str]:
    if filters.episode_ref is not None and filters.episode_ref != episode_ref:
        return "skipped", "episode filter does not match"
    unsafe_status = "rejected" if confirmed else "skipped"
    video_source = (
        _video_seed_source(episode_payload) if episode_payload is not None else None
    )
    if video_source == "x-video":
        return unsafe_status, "audio is recovered through scripts/run_x_video_ingest.py"
    if video_source == "yt-video":
        return (
            unsafe_status,
            "audio is recovered through scripts/run_youtube_video_ingest.py",
        )
    if audio_status != AUDIO_STATUS_MISSING:
        return unsafe_status, f"audio status is {audio_status}"
    if action_payload is None:
        return unsafe_status, "audio remediation action is missing"
    source_status = _safe_text(action_payload.get("status"), "unknown")
    if source_status != "ready":
        return unsafe_status, f"source action status is {source_status}"
    if any(
        bool(action_payload.get(field))
        for field in ("optional", "gated", "requires_api_cost_ack")
    ):
        return unsafe_status, "source action requires optional or gated workflow"
    return "selected", _safe_message(
        _safe_text(action_payload.get("reason"), "audio missing and download action ready"),
        "reason omitted by safety boundary",
    )


def _execute_confirmed_rows(
    rows: list[CorpusAudioDownloadRunRow],
) -> list[CorpusAudioDownloadRunRow]:
    updated_rows: list[CorpusAudioDownloadRunRow] = []
    for row in rows:
        if row.outcome_status != "selected":
            updated_rows.append(row)
            continue
        try:
            asset = download_audio(row.podcast_id, row.episode_ref)
        except Exception as exc:  # noqa: BLE001 - contain one requested download.
            category = _safe_exception_category(exc)
            updated_rows.append(
                replace(
                    row,
                    outcome_status="failed",
                    reason=f"download failed: {category}",
                    warnings=[*row.warnings, f"download failed: {category}"],
                )
            )
            continue
        outcome = "reused" if getattr(asset, "already_exists", False) else "downloaded"
        local_path = getattr(asset, "local_path", None)
        local_audio_path = (
            _safe_path_text(str(local_path)) if isinstance(local_path, Path) else None
        )
        updated_rows.append(
            replace(
                row,
                outcome_status=outcome,
                reason=f"audio {outcome}",
                planned_writes=[local_audio_path] if local_audio_path else row.planned_writes,
                local_audio_path=local_audio_path,
                content_type=_safe_optional_text(getattr(asset, "content_type", None)),
                size_bytes=_safe_optional_int(getattr(asset, "size_bytes", None)),
            )
        )
    return updated_rows


def _confirmed_warnings(
    rows: list[CorpusAudioDownloadRunRow],
) -> list[CorpusAudioDownloadRunWarning]:
    if any(row.outcome_status in {"downloaded", "reused"} for row in rows):
        return [
            CorpusAudioDownloadRunWarning(
                scope="run",
                episode_ref=None,
                message=(
                    "Manual follow-up is required after audio availability changes; "
                    "transcription, downstream remediation, and SQLite cache rebuild "
                    "remain manual."
                ),
            )
        ]
    return []


def _counts(
    rows: list[CorpusAudioDownloadRunRow],
    warnings: list[CorpusAudioDownloadRunWarning],
) -> CorpusAudioDownloadOutcomeCounts:
    warning_count = len(warnings) + sum(len(row.warnings) for row in rows)
    return CorpusAudioDownloadOutcomeCounts(
        row_count=len(rows),
        selected_count=sum(
            row.outcome_status in {"selected", "downloaded", "reused", "failed"}
            for row in rows
        ),
        downloaded_count=sum(row.outcome_status == "downloaded" for row in rows),
        reused_count=sum(row.outcome_status == "reused" for row in rows),
        failed_count=sum(row.outcome_status == "failed" for row in rows),
        skipped_count=sum(row.outcome_status == "skipped" for row in rows),
        rejected_count=sum(row.outcome_status == "rejected" for row in rows),
        warning_count=warning_count,
    )


def _write_run_report(result: CorpusAudioDownloadRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    markdown = _render_markdown(payload)
    try:
        write_part_staged_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            payload,
            markdown,
        )
    except OSError as exc:
        raise CorpusAudioDownloadRunnerFailedError(
            f"failed to write corpus audio download run report: {type(exc).__name__}"
        ) from exc


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Audio Download Run - {payload['podcast_id']}",
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
        "downloaded_count",
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
            "## Audio Download Outcomes",
            "",
            "| Episode | Audio | Outcome | Reason | Local path | Content type | Size bytes | Warnings |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["episode_ref"]),
                    _markdown_cell(row["audio_status"]),
                    _markdown_cell(row["outcome_status"]),
                    _markdown_cell(row["reason"]),
                    _markdown_cell(row["local_audio_path"] or "none"),
                    _markdown_cell(row["content_type"] or "none"),
                    _markdown_cell(row["size_bytes"] if row["size_bytes"] is not None else "none"),
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
            "This corpus-audio-download-run artifact contains metadata, paths, counts, warnings, and outcomes only.",
            "Dry-run does not read RSS, call network providers, call the downloader, or write run report artifacts.",
            "Confirmed execution is bounded to one requested episode and uses the existing audio downloader only.",
            "It does not transcribe audio, run downstream remediation, call LLM providers, invoke MCP tools, generate stock-lens artifacts, or update SQLite cache automatically.",
            "It omits full source URLs, query strings, transcript bodies, prompt bodies, LLM response bodies, secret values, traceback bodies, market claims, and investment recommendations.",
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


def _audio_action(episode_payload: dict[str, Any]) -> dict[str, Any] | None:
    for action_payload in _action_payloads(episode_payload):
        if _safe_text(action_payload.get("artifact_family"), "") == AUDIO_ACTION_FAMILY:
            return action_payload
    return None


def _status_text(status_payload: dict[str, Any]) -> str:
    status = status_payload.get("status")
    return status if isinstance(status, str) and status.strip() else "missing"


def _local_audio_path(audio_payload: dict[str, Any]) -> str | None:
    path = audio_payload.get("path")
    if isinstance(path, str) and path.strip():
        return _safe_path_text(path)
    paths = audio_payload.get("paths")
    if isinstance(paths, dict):
        for value in paths.values():
            if isinstance(value, str) and value.strip():
                return _safe_path_text(value)
    return None


def _planned_audio_writes(podcast_id: str, episode_ref: str) -> list[str]:
    return [str(storage.audio_asset_path(podcast_id, episode_ref, episode_ref, ".mp3"))]


def _source_warnings(episode_payload: dict[str, Any], family: str) -> list[str]:
    warnings: list[str] = []
    for warning in episode_payload.get("warnings", []):
        if isinstance(warning, dict):
            warning_family = warning.get("artifact_family")
            message = warning.get("message")
            if warning_family in {family, None} and isinstance(message, str):
                warnings.append(
                    _safe_message(message, f"source {family} warning omitted by safety boundary")
                )
        elif isinstance(warning, str):
            warnings.append(
                _safe_message(warning, "source warning omitted by safety boundary")
            )
    return warnings


def _row_sort_key(row: CorpusAudioDownloadRunRow) -> tuple[int, str, str]:
    family = row.action_id.split(":", 1)[1] if ":" in row.action_id else "unknown"
    return (_FAMILY_ORDER.get(family, 99), row.episode_ref, row.action_id)


def _safe_text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _safe_optional_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return _safe_message(value, "metadata omitted by safety boundary")


def _safe_optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _normalize_episode_ref(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _safe_exception_category(exc: Exception) -> str:
    category = type(exc).__name__
    return _safe_message(category, "download_dependency_error")


def _safe_path_text(value: str) -> str:
    return _safe_message(value, "path omitted by safety boundary")


def _safe_message(value: str, replacement: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS):
        return replacement
    return value


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")
