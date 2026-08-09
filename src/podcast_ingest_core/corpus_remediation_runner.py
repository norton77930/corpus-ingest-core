from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any, Callable

from . import storage
from .corpus_remediation_plan import generate_corpus_remediation_plan
from .entity_extractor import extract_mentions
from .episode_intelligence import generate_episode_intelligence_report
from .errors import CorpusRemediationRunnerFailedError
from .run_report_io import write_part_staged_report_pair
from .external_data_boundary import generate_external_data_boundary
from .industry_mapping import generate_industry_chain_mapping
from .models import (
    CorpusRemediationRunCounts,
    CorpusRemediationRunFilter,
    CorpusRemediationRunResult,
    CorpusRemediationRunRow,
    CorpusRemediationRunWarning,
    CorpusRemediationPlanResult,
)
from .summarizer import summarize_episode


RUN_MODE_DRY_RUN = "dry_run"
RUN_MODE_CONFIRMED = "confirmed"
DETERMINISTIC_ACTION_FAMILIES = (
    "extractive_summary",
    "mentions",
    "episode_intelligence",
    "industry_mapping",
    "external_boundary",
)
EXCLUDED_ACTION_FAMILIES = {
    "audio",
    "transcript",
    "semantic_summary",
    "semantic_review",
    "stock_lens",
    "stock_lens_report",
    "stock_lens_synthesis",
    "synthesis",
}
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
_RUN_DEPENDENCIES = {
    "extractive_summary": ("transcript",),
    "mentions": ("transcript",),
    "episode_intelligence": ("transcript",),
    "industry_mapping": ("episode_intelligence",),
    "external_boundary": ("industry_mapping",),
}
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "raw transcript",
    "evidence sentinel",
    "semantic body",
    "api_key=",
    "secret-value",
    "raw llm output",
    "prompt text",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)


def run_corpus_remediation(
    podcast_id: str,
    *,
    confirm: bool = False,
    episode_ref: str | None = None,
    action_family: str | None = None,
    max_actions: int | None = None,
    force: bool = False,
    allow_partial: bool = False,
) -> CorpusRemediationRunResult:
    """Run dry-run or confirmed deterministic corpus remediation for one podcast."""

    if max_actions is not None and max_actions <= 0:
        raise CorpusRemediationRunnerFailedError("max_actions must be positive")

    source_result = generate_corpus_remediation_plan(podcast_id)
    plan_payload = _load_plan_payload(source_result.plan_json_path)
    if not confirm:
        return _preview_corpus_remediation_from_plan(
            podcast_id,
            plan_result=source_result,
            plan_payload=plan_payload,
            episode_ref=episode_ref,
            action_family=action_family,
            max_actions=max_actions,
            source_persisted=True,
        )

    filters = CorpusRemediationRunFilter(
        episode_ref=episode_ref,
        action_family=action_family,
        max_actions=max_actions,
    )
    rows, selected_action_ids = _select_rows(
        podcast_id=podcast_id,
        plan_payload=plan_payload,
        filters=filters,
        source_plan_reads=[],
    )
    if not (episode_ref or action_family):
        raise CorpusRemediationRunnerFailedError(
            "confirm requires episode or action_family"
        )

    rows = _execute_selected_rows(
        rows=rows,
        selected_action_ids=selected_action_ids,
        force=force,
        allow_partial=allow_partial,
    )
    report_paths = storage.corpus_remediation_run_asset_paths(podcast_id)
    result = CorpusRemediationRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_CONFIRMED,
        confirm=True,
        source_remediation_plan_json_path=source_result.plan_json_path,
        source_remediation_plan_markdown_path=source_result.plan_markdown_path,
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        filters=filters,
        counts=_counts(rows, selected_action_ids),
        rows=rows,
        warnings=[],
        not_investment_advice=True,
    )
    _write_run_report(result)
    return result


def _preview_corpus_remediation_from_plan(
    podcast_id: str,
    *,
    plan_result: CorpusRemediationPlanResult,
    plan_payload: dict[str, Any],
    episode_ref: str | None,
    action_family: str | None,
    max_actions: int | None,
    source_persisted: bool,
) -> CorpusRemediationRunResult:
    if max_actions is not None and max_actions <= 0:
        raise CorpusRemediationRunnerFailedError("max_actions must be positive")
    filters = CorpusRemediationRunFilter(
        episode_ref=episode_ref,
        action_family=action_family,
        max_actions=max_actions,
    )
    source_plan_reads = [] if source_persisted else ["in-memory corpus snapshot"]
    rows, selected_action_ids = _select_rows(
        podcast_id=podcast_id,
        plan_payload=plan_payload,
        filters=filters,
        source_plan_reads=source_plan_reads,
    )
    return CorpusRemediationRunResult(
        podcast_id=podcast_id,
        run_mode=RUN_MODE_DRY_RUN,
        confirm=False,
        source_remediation_plan_json_path=plan_result.plan_json_path,
        source_remediation_plan_markdown_path=plan_result.plan_markdown_path,
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=_counts(rows, selected_action_ids),
        rows=rows,
        warnings=[],
        not_investment_advice=True,
    )


def result_to_dict(result: CorpusRemediationRunResult) -> dict[str, Any]:
    """Serialize a runner result into the public JSON-compatible shape."""

    payload = {
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
    return payload


def _load_plan_payload(plan_json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(plan_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusRemediationRunnerFailedError(
            f"failed to read corpus remediation plan: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CorpusRemediationRunnerFailedError("corpus remediation plan root must be an object")
    return payload


def _select_rows(
    *,
    podcast_id: str,
    plan_payload: dict[str, Any],
    filters: CorpusRemediationRunFilter,
    source_plan_reads: list[str],
) -> tuple[list[CorpusRemediationRunRow], set[str]]:
    rows: list[CorpusRemediationRunRow] = []
    selected_action_ids: set[str] = set()
    selected_count = 0
    for episode_payload in _episode_payloads(plan_payload):
        episode_ref = _safe_text(episode_payload.get("episode_ref"), "unknown")
        title = _safe_text(episode_payload.get("title"), episode_ref)
        artifact_status = episode_payload.get("artifact_status")
        if not isinstance(artifact_status, dict):
            artifact_status = {}
        for action_payload in _action_payloads(episode_payload):
            family = _safe_text(action_payload.get("artifact_family"), "unknown")
            source_status = _safe_text(action_payload.get("status"), "unknown")
            action_id = _safe_text(action_payload.get("action_id"), f"{episode_ref}:{family}")
            planned_reads = _planned_reads(
                family,
                artifact_status,
                source_plan_reads=source_plan_reads,
            )
            planned_writes = _planned_writes(podcast_id, episode_ref, title, family)
            outcome_status, reason = _initial_outcome(
                action_payload=action_payload,
                filters=filters,
                selected_count=selected_count,
            )
            if outcome_status == "selected":
                selected_count += 1
                selected_action_ids.add(action_id)
            rows.append(
                CorpusRemediationRunRow(
                    action_id=action_id,
                    podcast_id=podcast_id,
                    episode_ref=episode_ref,
                    title=_safe_message(title, "title omitted by safety boundary"),
                    artifact_family=family,
                    source_status=source_status,
                    outcome_status=outcome_status,
                    reason=reason,
                    planned_reads=planned_reads,
                    planned_writes=planned_writes,
                    output_paths=[],
                    warnings=_source_warnings(episode_payload, family),
                )
            )
    return sorted(rows, key=_row_sort_key), selected_action_ids


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


def _initial_outcome(
    *,
    action_payload: dict[str, Any],
    filters: CorpusRemediationRunFilter,
    selected_count: int,
) -> tuple[str, str]:
    family = _safe_text(action_payload.get("artifact_family"), "unknown")
    source_status = _safe_text(action_payload.get("status"), "unknown")
    if filters.episode_ref is not None and filters.episode_ref != _safe_text(
        action_payload.get("action_id"), ""
    ).split(":", 1)[0]:
        return "skipped", "episode filter does not match"
    if source_status == "blocked":
        blockers = ", ".join(
            item
            for item in action_payload.get("blocking_artifacts", [])
            if isinstance(item, str)
        )
        return "blocked", f"blocked by {blockers or 'upstream artifact'}"
    if family not in DETERMINISTIC_ACTION_FAMILIES:
        return "excluded", _excluded_reason(family)
    if source_status != "ready":
        return "skipped", f"source action status is {source_status}"
    if filters.action_family is not None and filters.action_family != family:
        return "skipped", "action_family filter does not match"
    if filters.max_actions is not None and selected_count >= filters.max_actions:
        return "skipped", "max_actions limit reached"
    return "selected", _safe_message(
        _safe_text(action_payload.get("reason"), "ready deterministic action"),
        "reason omitted by safety boundary",
    )


def _excluded_reason(family: str) -> str:
    if family in {"audio", "transcript"}:
        return f"{family} actions are manual-only in runner v1"
    if family in {"semantic_summary", "semantic_review"}:
        return f"{family} actions require semantic or LLM workflow outside runner v1"
    if family.startswith("stock_lens") or family in EXCLUDED_ACTION_FAMILIES:
        return f"{family} actions are outside runner v1 scope"
    return f"{family} is not in deterministic runner allowlist"


def _execute_selected_rows(
    *,
    rows: list[CorpusRemediationRunRow],
    selected_action_ids: set[str],
    force: bool,
    allow_partial: bool,
) -> list[CorpusRemediationRunRow]:
    updated_rows: list[CorpusRemediationRunRow] = []
    unavailable_by_episode: dict[str, set[str]] = {}
    for row in rows:
        if row.action_id not in selected_action_ids:
            updated_rows.append(row)
            continue
        failed_dependency = _failed_dependency(row, unavailable_by_episode)
        if failed_dependency is not None:
            skipped = replace(
                row,
                outcome_status="skipped",
                reason=f"failed dependency: {failed_dependency}",
            )
            unavailable_by_episode.setdefault(row.episode_ref, set()).add(
                row.artifact_family
            )
            updated_rows.append(skipped)
            continue
        try:
            asset = _dispatch(row.artifact_family)(
                row.podcast_id,
                row.episode_ref,
                force=force,
                allow_partial=allow_partial,
            )
        except Exception as exc:  # noqa: BLE001 - record per-action failure.
            failed = replace(
                row,
                outcome_status="failed",
                reason=f"action failed: {type(exc).__name__}",
                warnings=[*row.warnings, f"action failed: {type(exc).__name__}"],
            )
            unavailable_by_episode.setdefault(row.episode_ref, set()).add(
                row.artifact_family
            )
            updated_rows.append(failed)
            continue
        outcome = "reused" if getattr(asset, "already_exists", False) else "executed"
        updated_rows.append(
            replace(
                row,
                outcome_status=outcome,
                reason=f"{row.artifact_family} {outcome}",
                output_paths=_asset_output_paths(asset),
            )
        )
    return updated_rows


def _dispatch(family: str) -> Callable[..., Any]:
    dispatchers: dict[str, Callable[..., Any]] = {
        "extractive_summary": summarize_episode,
        "mentions": extract_mentions,
        "episode_intelligence": generate_episode_intelligence_report,
        "industry_mapping": generate_industry_chain_mapping,
        "external_boundary": generate_external_data_boundary,
    }
    try:
        return dispatchers[family]
    except KeyError as exc:
        raise CorpusRemediationRunnerFailedError(
            f"no deterministic dispatcher for {family}"
        ) from exc


def _failed_dependency(
    row: CorpusRemediationRunRow,
    unavailable_by_episode: dict[str, set[str]],
) -> str | None:
    unavailable = unavailable_by_episode.get(row.episode_ref, set())
    for dependency in _RUN_DEPENDENCIES.get(row.artifact_family, ()):
        if dependency in unavailable:
            return dependency
    return None


def _asset_output_paths(asset: Any) -> list[str]:
    paths: list[str] = []
    for attribute in (
        "summary_path",
        "mentions_json_path",
        "mentions_markdown_path",
        "report_json_path",
        "report_markdown_path",
        "mapping_json_path",
        "mapping_markdown_path",
        "boundary_json_path",
        "boundary_markdown_path",
        "json_path",
        "markdown_path",
    ):
        value = getattr(asset, attribute, None)
        if isinstance(value, Path):
            text = str(value)
            if text not in paths:
                paths.append(text)
    return paths


def _counts(
    rows: list[CorpusRemediationRunRow],
    selected_action_ids: set[str],
) -> CorpusRemediationRunCounts:
    warning_count = sum(len(row.warnings) for row in rows)
    return CorpusRemediationRunCounts(
        row_count=len(rows),
        selected_count=len(selected_action_ids),
        executed_count=sum(row.outcome_status == "executed" for row in rows),
        reused_count=sum(row.outcome_status == "reused" for row in rows),
        failed_count=sum(row.outcome_status == "failed" for row in rows),
        skipped_count=sum(row.outcome_status == "skipped" for row in rows),
        blocked_count=sum(row.outcome_status == "blocked" for row in rows),
        excluded_count=sum(row.outcome_status == "excluded" for row in rows),
        warning_count=warning_count,
    )


def _planned_reads(
    family: str,
    artifact_status: dict[str, Any],
    *,
    source_plan_reads: list[str],
) -> list[str]:
    dependency_paths: dict[str, tuple[str, ...]] = {
        "extractive_summary": ("transcript",),
        "mentions": ("transcript",),
        "episode_intelligence": ("transcript", "mentions"),
        "industry_mapping": ("episode_intelligence",),
        "external_boundary": ("industry_mapping",),
    }
    reads: list[str] = []
    for dependency in dependency_paths.get(family, ()):
        status_payload = artifact_status.get(dependency)
        if not isinstance(status_payload, dict):
            continue
        paths = status_payload.get("paths")
        if isinstance(paths, dict):
            reads.extend(str(value) for value in paths.values() if isinstance(value, str))
        path = status_payload.get("path")
        if isinstance(path, str):
            reads.append(path)
    return [*source_plan_reads, *sorted(dict.fromkeys(reads))]


def _planned_writes(
    podcast_id: str,
    episode_ref: str,
    title: str,
    family: str,
) -> list[str]:
    if family == "extractive_summary":
        return [str(storage.summary_asset_path(podcast_id, episode_ref, title))]
    if family == "mentions":
        paths = storage.mention_asset_paths(podcast_id, episode_ref, title)
        return [str(paths.json_path), str(paths.markdown_path)]
    if family == "episode_intelligence":
        paths = storage.episode_intelligence_report_asset_paths(
            podcast_id, episode_ref, title
        )
        return [str(paths.json_path), str(paths.markdown_path)]
    if family == "industry_mapping":
        paths = storage.industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
        return [str(paths.json_path), str(paths.markdown_path)]
    if family == "external_boundary":
        paths = storage.external_data_boundary_asset_paths(podcast_id, episode_ref, title)
        return [str(paths.json_path), str(paths.markdown_path)]
    return []


def _source_warnings(episode_payload: dict[str, Any], family: str) -> list[str]:
    warnings: list[str] = []
    for warning in episode_payload.get("warnings", []):
        if isinstance(warning, dict):
            warning_family = warning.get("artifact_family")
            message = warning.get("message")
            if warning_family in {family, None} and isinstance(message, str):
                warnings.append(_safe_message(message, "warning omitted by safety boundary"))
        elif isinstance(warning, str):
            warnings.append(_safe_message(warning, "warning omitted by safety boundary"))
    return warnings


def _write_run_report(result: CorpusRemediationRunResult) -> None:
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
        raise CorpusRemediationRunnerFailedError(
            f"failed to write corpus remediation run report: {exc}"
        ) from exc


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Remediation Run - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Run mode: {payload['run_mode']}",
        f"- Confirm: {payload['confirm']}",
        f"- Source remediation plan: {payload['source_remediation_plan_json_path']}",
        f"- Source remediation plan Markdown: {payload['source_remediation_plan_markdown_path']}",
        "",
        "## Filters",
        "",
        f"- Episode: {payload['filters']['episode_ref'] or 'none'}",
        f"- Action family: {payload['filters']['action_family'] or 'none'}",
        f"- Max actions: {payload['filters']['max_actions'] or 'none'}",
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
        "excluded_count",
        "warning_count",
    ):
        lines.append(f"| {key} | {payload[key]} |")
    lines.extend(
        [
            "",
            "## Action Outcomes",
            "",
            "| Episode | Family | Source | Outcome | Reason | Outputs | Warnings |",
            "| --- | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["episode_ref"]),
                    _markdown_cell(row["artifact_family"]),
                    _markdown_cell(row["source_status"]),
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
            "This corpus-remediation-run artifact contains deterministic action outcomes only.",
            "It does not execute downloads, transcriptions, semantic workflows, LLM calls, RSS reads, network reads, SQLite cache operations, MCP tools, or cache rebuilds.",
            "It does not include raw transcript text, evidence snippets, semantic bodies, prompts, raw LLM output, secrets, or market claims.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _row_sort_key(row: CorpusRemediationRunRow) -> tuple[int, str, str, str]:
    return (
        _FAMILY_ORDER.get(row.artifact_family, 99),
        row.episode_ref,
        row.artifact_family,
        row.action_id,
    )


def _safe_text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _safe_message(value: str, replacement: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_OUTPUT_FRAGMENTS):
        return replacement
    return value


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")
