from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
from typing import Any

from . import storage
from .errors import EpisodeNotFoundError
from .feed_reader import get_episode
from .models import (
    Episode,
    CorpusEpisodeIntakeFilter,
    CorpusEpisodeIntakeOutcomeCounts,
    CorpusEpisodeIntakeRunResult,
    CorpusEpisodeIntakeRunRow,
    CorpusEpisodeIntakeRunWarning,
    CorpusEpisodeSeed,
)


RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
DEFAULT_SELECTOR = "latest"
PLANNED_FEED_READ = "configured podcast RSS feed"
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_QUERY_PATTERN = re.compile(r"\?[^\s|]+")
_SECRET_PATTERN = re.compile(
    r"\b(api[_-]?key|token|secret|bearer)\b[^\s|]*",
    re.IGNORECASE,
)
_FORBIDDEN_PHRASES = (
    "prompt text",
    "raw llm output",
    "traceback",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


def run_corpus_episode_intake(
    podcast_id: str,
    *,
    episode_ref: str = DEFAULT_SELECTOR,
    confirm: bool = False,
) -> CorpusEpisodeIntakeRunResult:
    """Preview or run one bounded corpus episode intake bootstrap."""

    selector = _normalize_selector(episode_ref)
    rows: list[CorpusEpisodeIntakeRunRow]
    warnings: list[CorpusEpisodeIntakeRunWarning] = []
    resolved_episode_ref: str | None = None
    try:
        episode = get_episode(podcast_id, selector)
    except EpisodeNotFoundError:
        rows = [_rejected_row(podcast_id, selector)]
    except Exception as exc:  # noqa: BLE001 - bound one feed dependency failure.
        rows = [_failed_row(podcast_id, selector, type(exc).__name__)]
    else:
        resolved_episode_ref = episode.episode_ref
        rows = [_selected_row(podcast_id, selector, episode)]
    report_json_path: Path | None = None
    report_markdown_path: Path | None = None
    if confirm:
        rows = _execute_confirmed_rows(rows)
        warnings = _confirmed_warnings(rows)
        report_paths = storage.corpus_episode_intake_run_asset_paths(podcast_id)
        report_json_path = report_paths.json_path
        report_markdown_path = report_paths.markdown_path

    result = CorpusEpisodeIntakeRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_CONFIRMED if confirm else RUN_MODE_DRY_RUN,
        confirm=confirm,
        selector=selector,
        resolved_episode_ref=resolved_episode_ref,
        report_json_path=report_json_path,
        report_markdown_path=report_markdown_path,
        filters=CorpusEpisodeIntakeFilter(episode_ref=selector),
        counts=_counts(rows, warnings),
        rows=rows,
        warnings=warnings,
        not_investment_advice=True,
    )
    if confirm:
        _write_run_report(result)
    return result


def result_to_dict(result: CorpusEpisodeIntakeRunResult) -> dict[str, Any]:
    """Serialize an episode intake result into the public JSON shape."""

    return {
        "podcast_id": result.podcast_id,
        "run_mode": result.run_mode,
        "confirm": result.confirm,
        "selector": result.selector,
        "resolved_episode_ref": result.resolved_episode_ref,
        "report_json_path": _path_or_none(result.report_json_path),
        "report_markdown_path": _path_or_none(result.report_markdown_path),
        "filters": asdict(result.filters),
        **asdict(result.counts),
        "rows": [asdict(row) for row in result.rows],
        "warnings": [asdict(warning) for warning in result.warnings],
        "not_investment_advice": result.not_investment_advice,
    }


def _normalize_selector(episode_ref: str | None) -> str:
    if episode_ref is None:
        return DEFAULT_SELECTOR
    normalized = episode_ref.strip()
    return normalized or DEFAULT_SELECTOR


def _selected_row(
    podcast_id: str,
    selector: str,
    episode: Episode,
) -> CorpusEpisodeIntakeRunRow:
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode.episode_ref)
    return CorpusEpisodeIntakeRunRow(
        podcast_id=podcast_id,
        selector=selector,
        episode_ref=episode.episode_ref,
        title=_safe_optional_text(episode.title) or episode.episode_ref,
        published_at=_safe_optional_text(episode.published_at),
        duration=_safe_optional_text(episode.duration),
        guid_status="present" if episode.guid else "missing",
        has_audio_url=bool(episode.audio_url),
        outcome_status="selected",
        reason="episode resolved from configured feed",
        planned_reads=[PLANNED_FEED_READ],
        planned_writes=[str(seed_path)],
        seed_json_path=str(seed_path),
        warnings=[],
    )


def _rejected_row(podcast_id: str, selector: str) -> CorpusEpisodeIntakeRunRow:
    return CorpusEpisodeIntakeRunRow(
        podcast_id=podcast_id,
        selector=selector,
        episode_ref=None,
        title=None,
        published_at=None,
        duration=None,
        guid_status="missing",
        has_audio_url=False,
        outcome_status="rejected",
        reason="episode selector was not found in configured feed",
        planned_reads=[PLANNED_FEED_READ],
        planned_writes=[],
        seed_json_path=None,
        warnings=[],
    )


def _failed_row(
    podcast_id: str,
    selector: str,
    error_category: str,
) -> CorpusEpisodeIntakeRunRow:
    return CorpusEpisodeIntakeRunRow(
        podcast_id=podcast_id,
        selector=selector,
        episode_ref=None,
        title=None,
        published_at=None,
        duration=None,
        guid_status="missing",
        has_audio_url=False,
        outcome_status="failed",
        reason=f"feed resolution failed: {_safe_optional_text(error_category) or 'Error'}",
        planned_reads=[PLANNED_FEED_READ],
        planned_writes=[],
        seed_json_path=None,
        warnings=[],
    )


def _counts(
    rows: list[CorpusEpisodeIntakeRunRow],
    warnings: list[CorpusEpisodeIntakeRunWarning],
) -> CorpusEpisodeIntakeOutcomeCounts:
    warning_count = len(warnings) + sum(len(row.warnings) for row in rows)
    return CorpusEpisodeIntakeOutcomeCounts(
        row_count=len(rows),
        selected_count=sum(
            row.outcome_status in {"selected", "seeded", "reused", "failed"}
            for row in rows
        ),
        seeded_count=sum(row.outcome_status == "seeded" for row in rows),
        reused_count=sum(row.outcome_status == "reused" for row in rows),
        failed_count=sum(row.outcome_status == "failed" for row in rows),
        skipped_count=sum(row.outcome_status == "skipped" for row in rows),
        rejected_count=sum(row.outcome_status == "rejected" for row in rows),
        warning_count=warning_count,
    )


def _execute_confirmed_rows(
    rows: list[CorpusEpisodeIntakeRunRow],
) -> list[CorpusEpisodeIntakeRunRow]:
    executed_rows: list[CorpusEpisodeIntakeRunRow] = []
    for row in rows:
        if row.outcome_status != "selected" or row.episode_ref is None:
            executed_rows.append(row)
            continue
        seed_path = storage.corpus_episode_seed_asset_path(row.podcast_id, row.episode_ref)
        seed_payload = _seed_payload(row)
        existing_payload = _read_existing_json(seed_path)
        outcome = "reused" if existing_payload == seed_payload else "seeded"
        if outcome == "seeded":
            _write_json(seed_path, seed_payload)
        executed_rows.append(
            CorpusEpisodeIntakeRunRow(
                podcast_id=row.podcast_id,
                selector=row.selector,
                episode_ref=row.episode_ref,
                title=row.title,
                published_at=row.published_at,
                duration=row.duration,
                guid_status=row.guid_status,
                has_audio_url=row.has_audio_url,
                outcome_status=outcome,
                reason=f"episode seed metadata {outcome}",
                planned_reads=row.planned_reads,
                planned_writes=row.planned_writes,
                seed_json_path=row.seed_json_path,
                warnings=row.warnings,
            )
        )
    return executed_rows


def _seed_payload(row: CorpusEpisodeIntakeRunRow) -> dict[str, Any]:
    seed = CorpusEpisodeSeed(
        podcast_id=row.podcast_id,
        episode_ref=row.episode_ref or "unknown",
        title=row.title or row.episode_ref or "unknown",
        published_at=row.published_at,
        duration=row.duration,
        guid_status=row.guid_status,
        has_audio_url=row.has_audio_url,
        seed_source="rss",
        selector=row.selector,
        warning_count=len(row.warnings),
        warnings=row.warnings,
        not_investment_advice=True,
    )
    return asdict(seed)


def _read_existing_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    part_path = path.with_name(f"{path.name}.part")
    path.parent.mkdir(parents=True, exist_ok=True)
    part_path.unlink(missing_ok=True)
    try:
        part_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        part_path.replace(path)
    finally:
        part_path.unlink(missing_ok=True)


def _write_run_report(result: CorpusEpisodeIntakeRunResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    _write_json(result.report_json_path, payload)
    markdown_part = result.report_markdown_path.with_name(
        f"{result.report_markdown_path.name}.part"
    )
    result.report_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_part.unlink(missing_ok=True)
    try:
        markdown_part.write_text(_render_markdown(payload), encoding="utf-8")
        markdown_part.replace(result.report_markdown_path)
    finally:
        markdown_part.unlink(missing_ok=True)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Episode Intake Run - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Run mode: {payload['run_mode']}",
        f"- Confirm: {payload['confirm']}",
        f"- Selector: {payload['selector']}",
        f"- Resolved episode: {payload['resolved_episode_ref'] or 'none'}",
        "",
        "## Summary Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "row_count",
        "selected_count",
        "seeded_count",
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
            "## Intake Outcomes",
            "",
            "| Selector | Episode | Title | Published | Has audio | Outcome | Reason | Seed path | Warnings |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["selector"]),
                    _markdown_cell(row["episode_ref"] or "none"),
                    _markdown_cell(row["title"] or "none"),
                    _markdown_cell(row["published_at"] or "none"),
                    _markdown_cell(row["has_audio_url"]),
                    _markdown_cell(row["outcome_status"]),
                    _markdown_cell(row["reason"]),
                    _markdown_cell(row["seed_json_path"] or "none"),
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
            "This corpus-episode-intake-run artifact contains metadata, paths, counts, warnings, and outcomes only.",
            "Dry-run may resolve the configured feed selector but writes no seed metadata or run report artifacts.",
            "Confirmed execution writes seed metadata and this latest run report only.",
            "It does not download audio, transcribe audio, run downstream remediation, call LLM providers, invoke MCP tools, generate stock-lens artifacts, or update SQLite cache automatically.",
            "It omits unsafe feed details, provider bodies, credentials, diagnostic bodies, market claims, and investment recommendations.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _confirmed_warnings(
    rows: list[CorpusEpisodeIntakeRunRow],
) -> list[CorpusEpisodeIntakeRunWarning]:
    if not any(row.outcome_status in {"seeded", "reused"} for row in rows):
        return []
    return [
        CorpusEpisodeIntakeRunWarning(
            scope="run",
            episode_ref=None,
            message=(
                "Manual follow-up is required after episode seed changes; "
                "index refresh, remediation planning, audio download, transcription, "
                "downstream remediation, and SQLite cache rebuild remain manual."
            ),
        )
    ]


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _safe_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = _URL_PATTERN.sub("[redacted-url]", text)
    text = _QUERY_PATTERN.sub("[redacted-query]", text)
    text = _SECRET_PATTERN.sub("[redacted]", text)
    for phrase in _FORBIDDEN_PHRASES:
        text = re.sub(re.escape(phrase), "[redacted]", text, flags=re.IGNORECASE)
    return text.strip() or None


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None
