"""Read-only next-step suggestion for historical verified-report operator path."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .corpus_episode_completion_workflow_runner import (
    run_corpus_episode_completion_workflow,
)
from .episode_verified_research_report_workflow_runner import (
    run_episode_verified_research_report_workflow,
)
from .errors import (
    HistoricalVerifiedReportPathInputError,
    VerifiedResearchReportCatalogInputError,
)
from .models import HistoricalVerifiedReportNextStep
from . import storage
from .verified_research_report_catalog import (
    discover_eligible_report_summaries,
    require_safe_podcast_id,
)

_RESERVED = frozenset({"latest", "next"})
_MAX_DIGESTS = 10
_TOOL_PUBLISH = "run_episode_verified_research_report_workflow"
_TOOL_COMPLETION = "run_corpus_episode_completion_workflow"
_ACTION_SEMANTIC_SUMMARY = "semantic_summary"
_ACTION_BLOCKED = "blocked"
_ACTION_COMPLETED = "completed"


def suggest_historical_verified_report_next_step(
    podcast_id: str,
    episode_ref: str,
) -> HistoricalVerifiedReportNextStep:
    """Suggest one next human-gated step without writes or confirmed side effects."""

    normalized_podcast_id = _validate_podcast_id(podcast_id)
    normalized_episode_ref = _validate_episode_ref(episode_ref)

    summaries, _root_status, _traversal_status = discover_eligible_report_summaries(
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
    )
    digests = sorted({item.source_digest for item in summaries})[:_MAX_DIGESTS]
    # Incomplete discovery returns no summaries; non-empty digests already imply presence.
    has_bundle = bool(digests)

    if has_bundle:
        return HistoricalVerifiedReportNextStep(
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
            suggestion="report_present",
            has_bundle=True,
            source_digests=digests,
            publish_ready=False,
            missing_roles=[],
            stale_roles=[],
            completion_action=None,
            recommended_mcp_tool=None,
            requires_api_cost_ack=False,
        )

    publish_preview = run_episode_verified_research_report_workflow(
        normalized_podcast_id,
        normalized_episode_ref,
        confirm=False,
    )
    if publish_preview.ready:
        return HistoricalVerifiedReportNextStep(
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
            suggestion="publish_verified_report",
            has_bundle=False,
            source_digests=[],
            publish_ready=True,
            missing_roles=[],
            stale_roles=[],
            completion_action=None,
            recommended_mcp_tool=_TOOL_PUBLISH,
            requires_api_cost_ack=False,
        )

    completion_preview = run_corpus_episode_completion_workflow(
        normalized_podcast_id,
        episode_ref=normalized_episode_ref,
        action="next",
        confirm=False,
    )
    selected = completion_preview.selected_action
    if selected in {_ACTION_BLOCKED, _ACTION_COMPLETED}:
        return HistoricalVerifiedReportNextStep(
            podcast_id=normalized_podcast_id,
            episode_ref=normalized_episode_ref,
            suggestion="blocked",
            has_bundle=False,
            source_digests=[],
            publish_ready=False,
            missing_roles=list(publish_preview.missing_roles),
            stale_roles=list(publish_preview.stale_roles),
            completion_action=selected,
            recommended_mcp_tool=None,
            requires_api_cost_ack=False,
        )

    return HistoricalVerifiedReportNextStep(
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
        suggestion="completion_action",
        has_bundle=False,
        source_digests=[],
        publish_ready=False,
        missing_roles=list(publish_preview.missing_roles),
        stale_roles=list(publish_preview.stale_roles),
        completion_action=selected,
        recommended_mcp_tool=_TOOL_COMPLETION,
        requires_api_cost_ack=selected == _ACTION_SEMANTIC_SUMMARY,
    )


def result_to_dict(result: HistoricalVerifiedReportNextStep) -> dict[str, Any]:
    """Serialize suggestion to JSON-safe scalars and lists only."""

    return asdict(result)


def _validate_podcast_id(value: str) -> str:
    try:
        return require_safe_podcast_id(value)
    except VerifiedResearchReportCatalogInputError as exc:
        raise HistoricalVerifiedReportPathInputError("podcast_id is invalid") from exc


def _validate_episode_ref(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HistoricalVerifiedReportPathInputError("episode_ref is required")
    normalized = value.strip()
    if normalized.casefold() in _RESERVED:
        raise HistoricalVerifiedReportPathInputError(
            "episode_ref rejects reserved selectors"
        )
    # Same episode_ref character class as catalog safe episode refs (no latest/next).
    if not storage.is_safe_episode_ref(normalized):
        raise HistoricalVerifiedReportPathInputError("episode_ref is invalid")
    return normalized
