from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from . import storage
from .corpus_index import generate_corpus_index
from .errors import CorpusRemediationPlanFailedError
from .models import (
    CorpusIndexResult,
    CorpusRemediationAction,
    CorpusRemediationActionCounts,
    CorpusRemediationBlocker,
    CorpusRemediationEpisodeRow,
    CorpusRemediationPlanResult,
    CorpusRemediationWarning,
)


PLAN_MODE = "deterministic-corpus-remediation-plan-v1"
SOURCE_SCOPE = "refreshed-local-corpus-index-only"
ARTIFACT_LADDER = (
    "audio",
    "transcript",
    "extractive_summary",
    "mentions",
    "semantic_summary",
    "semantic_review",
    "episode_intelligence",
    "industry_mapping",
    "external_boundary",
)
_OPTIONAL_FAMILIES = {"semantic_summary", "semantic_review"}
_GATED_FAMILIES = {"semantic_summary"}
_ACTION_TYPES = {
    "audio": "download",
    "transcript": "transcribe",
    "extractive_summary": "generate",
    "mentions": "generate",
    "semantic_summary": "generate",
    "semantic_review": "review",
    "episode_intelligence": "generate",
    "industry_mapping": "generate",
    "external_boundary": "generate",
}
_DEPENDENCIES = {
    "audio": (),
    "transcript": ("audio",),
    "extractive_summary": ("transcript",),
    "mentions": ("transcript",),
    "semantic_summary": ("transcript",),
    "semantic_review": ("transcript", "semantic_summary"),
    "episode_intelligence": ("transcript",),
    "industry_mapping": ("transcript", "episode_intelligence"),
    "external_boundary": ("transcript", "industry_mapping"),
}


@dataclass(frozen=True)
class _CorpusRemediationPlanSnapshot:
    result: CorpusRemediationPlanResult
    payload: dict[str, Any]
    markdown: str


def generate_corpus_remediation_plan(podcast_id: str) -> CorpusRemediationPlanResult:
    """Generate a deterministic local remediation plan for one podcast corpus."""

    index_result = generate_corpus_index(podcast_id)
    snapshot = _build_corpus_remediation_plan_snapshot(
        podcast_id,
        index_result=index_result,
        index_payload=_load_index_payload(index_result.index_json_path),
    )
    return _persist_corpus_remediation_plan_snapshot(snapshot)


def _build_corpus_remediation_plan_snapshot(
    podcast_id: str,
    *,
    index_result: CorpusIndexResult,
    index_payload: dict[str, Any],
) -> _CorpusRemediationPlanSnapshot:
    rows = [
        _build_remediation_row(podcast_id, row_payload)
        for row_payload in index_payload.get("episodes", [])
        if isinstance(row_payload, dict)
    ]
    action_counts = _action_counts(rows)
    warning_count = sum(len(row.warnings) for row in rows)
    paths = storage.corpus_remediation_plan_asset_paths(podcast_id)
    payload = {
        "podcast_id": podcast_id,
        "plan_mode": PLAN_MODE,
        "source_scope": SOURCE_SCOPE,
        "source_corpus_index_json_path": str(index_result.index_json_path),
        "source_corpus_index_markdown_path": str(index_result.index_markdown_path),
        "episode_count": len(rows),
        "action_count": action_counts.action_count,
        "blocked_action_count": action_counts.blocked_action_count,
        "optional_action_count": action_counts.optional_action_count,
        "gated_action_count": action_counts.gated_action_count,
        "warning_count": warning_count,
        "episodes": [asdict(row) for row in rows],
        "not_investment_advice": True,
    }
    result = CorpusRemediationPlanResult(
        podcast_id=podcast_id,
        plan_json_path=paths.json_path,
        plan_markdown_path=paths.markdown_path,
        source_corpus_index_json_path=index_result.index_json_path,
        source_corpus_index_markdown_path=index_result.index_markdown_path,
        episode_count=len(rows),
        warning_count=warning_count,
        action_counts=action_counts,
    )
    return _CorpusRemediationPlanSnapshot(
        result=result,
        payload=payload,
        markdown=_render_markdown(payload),
    )


def _persist_corpus_remediation_plan_snapshot(
    snapshot: _CorpusRemediationPlanSnapshot,
) -> CorpusRemediationPlanResult:
    _write_plan(
        snapshot.result.plan_json_path,
        snapshot.result.plan_markdown_path,
        snapshot.payload,
        snapshot.markdown,
    )
    return snapshot.result


def _load_index_payload(index_json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(index_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusRemediationPlanFailedError(
            f"讀取 corpus artifact index 失敗：{exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CorpusRemediationPlanFailedError("corpus artifact index root 必須是 object。")
    return payload


def _build_remediation_row(
    podcast_id: str,
    row_payload: dict[str, Any],
) -> CorpusRemediationEpisodeRow:
    episode_ref = _safe_text(row_payload.get("episode_ref"), "unknown")
    title = _safe_text(row_payload.get("title"), episode_ref)
    artifact_status = row_payload.get("artifact_status")
    if not isinstance(artifact_status, dict):
        artifact_status = {}
    source_metadata = row_payload.get("source_metadata")
    if not isinstance(source_metadata, dict):
        source_metadata = {}
    warnings = [
        _warning_from_index_text(episode_ref, warning)
        for warning in row_payload.get("warnings", [])
        if isinstance(warning, str)
    ]
    actions = [
        action
        for family in ARTIFACT_LADDER
        if _needs_action(artifact_status.get(family, {}))
        for action in [
            _build_action(
                podcast_id,
                episode_ref,
                family,
                artifact_status,
                source_metadata,
            )
        ]
    ]
    blockers = [
        blocker
        for action in actions
        for blocker in _blockers_for_action(action, artifact_status)
    ]
    missing_artifacts = [
        family
        for family in row_payload.get("missing_artifacts", [])
        if isinstance(family, str)
    ]
    return CorpusRemediationEpisodeRow(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        artifact_status=artifact_status,
        missing_artifacts=missing_artifacts,
        blockers=blockers,
        warnings=warnings,
        actions=actions,
    )


def _needs_action(status_payload: Any) -> bool:
    if not isinstance(status_payload, dict):
        return True
    return _status_text(status_payload) in {"missing", "unreadable"}


def _build_action(
    podcast_id: str,
    episode_ref: str,
    family: str,
    artifact_status: dict[str, Any],
    source_metadata: dict[str, Any],
) -> CorpusRemediationAction:
    blockers = _blocking_dependencies(family, artifact_status)
    status_payload = artifact_status.get(family, {})
    source_status = _status_text(status_payload)
    if family == "audio" and _seed_audio_unavailable(source_metadata):
        blockers = ["feed_audio_url"]
    if blockers:
        status = "blocked"
    elif family in _GATED_FAMILIES:
        status = "gated"
    elif family == "semantic_review":
        status = "optional"
    else:
        status = "ready"
    return CorpusRemediationAction(
        action_id=f"{episode_ref}:{family}",
        artifact_family=family,
        action_type=_ACTION_TYPES[family],
        status=status,
        order=ARTIFACT_LADDER.index(family) + 1,
        reason=_action_reason(family, source_status, source_metadata),
        blocking_artifacts=blockers,
        suggested_command=_suggested_command(podcast_id, episode_ref, family),
        manual_only=True,
        optional=family in _OPTIONAL_FAMILIES,
        gated=family in _GATED_FAMILIES,
        requires_api_cost_ack=family in _GATED_FAMILIES,
    )


def _blocking_dependencies(
    family: str,
    artifact_status: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    for dependency in _DEPENDENCIES[family]:
        dependency_status = artifact_status.get(dependency, {})
        if not _is_available(dependency_status):
            blockers.append(dependency)
    return blockers


def _is_available(status_payload: Any) -> bool:
    if not isinstance(status_payload, dict):
        return False
    return _status_text(status_payload) not in {"missing", "unreadable"}


def _status_text(status_payload: Any) -> str:
    if not isinstance(status_payload, dict):
        return "missing"
    status = status_payload.get("status")
    return status if isinstance(status, str) and status else "missing"


def _seed_audio_unavailable(source_metadata: dict[str, Any]) -> bool:
    episode_seed = source_metadata.get("episode_seed")
    if not isinstance(episode_seed, dict):
        return False
    if episode_seed.get("status") != "available":
        return False
    return episode_seed.get("has_audio_url") is False


def _action_reason(
    family: str,
    source_status: str,
    source_metadata: dict[str, Any],
) -> str:
    if family == "audio" and _seed_audio_unavailable(source_metadata):
        return "audio artifact is missing but feed audio is unavailable"
    if source_status == "unreadable":
        return f"{family} artifact is unreadable"
    return f"{family} artifact is missing"


def _suggested_command(podcast_id: str, episode_ref: str, family: str) -> str:
    base = f"--podcast {podcast_id} --episode {episode_ref}"
    commands = {
        "audio": f"python scripts/download_episode.py {base}",
        "transcript": f"python scripts/transcribe_episode.py {base}",
        "extractive_summary": (
            f"python scripts/summarize_episode.py {base} --mode extractive"
        ),
        "mentions": f"python scripts/extract_mentions.py {base}",
        "semantic_summary": (
            f"python scripts/summarize_episode.py {base} "
            "--mode semantic --api-cost-ack REQUIRED"
        ),
        "semantic_review": (
            f"python scripts/review_semantic_summary_smoke.py {base}"
        ),
        "episode_intelligence": (
            f"python scripts/generate_episode_intelligence_report.py {base}"
        ),
        "industry_mapping": (
            f"python scripts/generate_industry_chain_mapping.py {base}"
        ),
        "external_boundary": (
            f"python scripts/generate_external_data_boundary.py {base}"
        ),
    }
    return commands[family]


def _blockers_for_action(
    action: CorpusRemediationAction,
    artifact_status: dict[str, Any],
) -> list[CorpusRemediationBlocker]:
    return [
        CorpusRemediationBlocker(
            blocked_artifact=action.artifact_family,
            blocking_artifact=blocking_artifact,
            blocking_status=_status_text(artifact_status.get(blocking_artifact, {})),
            message=(
                f"{blocking_artifact} is "
                f"{_status_text(artifact_status.get(blocking_artifact, {}))}"
            ),
        )
        for blocking_artifact in action.blocking_artifacts
    ]


def _warning_from_index_text(
    episode_ref: str,
    warning: str,
) -> CorpusRemediationWarning:
    artifact_family = None
    message = warning
    if ": " in warning:
        candidate_family, candidate_message = warning.split(": ", 1)
        if candidate_family in ARTIFACT_LADDER:
            artifact_family = candidate_family
            message = candidate_message
    return CorpusRemediationWarning(
        scope="episode",
        episode_ref=episode_ref,
        artifact_family=artifact_family,
        message=message,
    )


def _action_counts(
    rows: list[CorpusRemediationEpisodeRow],
) -> CorpusRemediationActionCounts:
    actions = [action for row in rows for action in row.actions]
    return CorpusRemediationActionCounts(
        action_count=len(actions),
        blocked_action_count=sum(action.status == "blocked" for action in actions),
        optional_action_count=sum(action.optional for action in actions),
        gated_action_count=sum(action.gated for action in actions),
    )


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Corpus Remediation Plan - {payload['podcast_id']}",
        "",
        "## Summary",
        "",
        f"- Plan mode: {payload['plan_mode']}",
        f"- Source scope: {payload['source_scope']}",
        f"- Source index: {payload['source_corpus_index_json_path']}",
        f"- Source index Markdown: {payload['source_corpus_index_markdown_path']}",
        f"- Episode count: {payload['episode_count']}",
        f"- Action count: {payload['action_count']}",
        f"- Blocked action count: {payload['blocked_action_count']}",
        f"- Optional action count: {payload['optional_action_count']}",
        f"- Gated action count: {payload['gated_action_count']}",
        f"- Warning count: {payload['warning_count']}",
        "",
        "### Summary Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| episode_count | {payload['episode_count']} |",
        f"| action_count | {payload['action_count']} |",
        f"| blocked_action_count | {payload['blocked_action_count']} |",
        f"| optional_action_count | {payload['optional_action_count']} |",
        f"| gated_action_count | {payload['gated_action_count']} |",
        f"| warning_count | {payload['warning_count']} |",
        "",
        "## Episode Actions",
        "",
        "| Episode | Title | Actions | Blocked | Optional | Gated | Warnings | Next Actions |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["episodes"]:
        actions = row["actions"]
        next_actions = "; ".join(
            f"{action['artifact_family']}:{action['status']}"
            for action in actions
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["episode_ref"]),
                    _markdown_cell(row["title"]),
                    _markdown_cell(len(actions)),
                    _markdown_cell(
                        sum(action["status"] == "blocked" for action in actions)
                    ),
                    _markdown_cell(sum(action["optional"] for action in actions)),
                    _markdown_cell(sum(action["gated"] for action in actions)),
                    _markdown_cell(len(row["warnings"])),
                    _markdown_cell(next_actions or "none"),
                ]
            )
            + " |"
        )

    if payload["episodes"]:
        lines.extend(["", "## Action Details", ""])
        for row in payload["episodes"]:
            if not row["actions"]:
                continue
            lines.append(f"### {row['episode_ref']} - {row['title']}")
            lines.append("")
            for action in row["actions"]:
                blockers = ", ".join(action["blocking_artifacts"]) or "none"
                lines.append(
                    "- "
                    f"{action['artifact_family']} [{action['status']}]: "
                    f"{action['reason']}; blockers={blockers}; "
                    f"command={action['suggested_command']}"
                )
            lines.append("")

    if payload["warning_count"]:
        lines.extend(["## Warnings", ""])
        for row in payload["episodes"]:
            for warning in row["warnings"]:
                family = warning["artifact_family"] or "episode"
                lines.append(
                    f"- {row['episode_ref']} {family}: {warning['message']}"
                )
        lines.append("")

    lines.extend(
        [
            "## Boundary Notice",
            "",
            "This corpus-remediation-plan artifact contains missing artifacts and next actions only.",
            "It does not execute downloads, transcriptions, LLM calls, RSS reads, network reads, SQLite cache operations, MCP tools, or cache rebuilds.",
            "It does not include raw transcript text, evidence snippets, semantic bodies, prompts, raw LLM output, secrets, or market claims.",
            "It is not investment advice.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_plan(
    json_path: Path,
    markdown_path: Path,
    payload: dict[str, Any],
    markdown: str,
) -> None:
    json_part_path = json_path.with_name(f"{json_path.name}.part")
    markdown_part_path = markdown_path.with_name(f"{markdown_path.name}.part")
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_part_path.unlink(missing_ok=True)
        markdown_part_path.unlink(missing_ok=True)
        json_part_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_part_path.write_text(markdown, encoding="utf-8")
        json_part_path.replace(json_path)
        markdown_part_path.replace(markdown_path)
    except OSError as exc:
        for part_path in (json_part_path, markdown_part_path):
            try:
                part_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise CorpusRemediationPlanFailedError(
            f"寫入 corpus remediation plan 失敗：{exc}"
        ) from exc


def _safe_text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value.strip() else default


def _markdown_cell(value: Any) -> str:
    text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")
