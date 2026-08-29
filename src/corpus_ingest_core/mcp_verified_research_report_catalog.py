"""MCP adapter for the read-only verified research report catalog."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from . import verified_research_report_catalog as core

_ERROR_TYPE = "VerifiedResearchReportCatalogInputError"
_ERROR_MESSAGE = "verified research report catalog query failed"
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100


def dispatch(
    *,
    success: Callable[[Any], dict[str, Any]],
    action: str = "list",
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    source_digest: str | None = None,
    query: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Validate the bounded MCP envelope and delegate one operation to Core."""

    if not _valid_limit(limit) or not isinstance(action, str):
        return tool_error_payload()
    if action == "list":
        if query is not None or source_digest is not None:
            return tool_error_payload()
        operation = partial(
            core.list_verified_research_reports,
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            limit=limit,
        )
    elif action == "search":
        if source_digest is not None or not isinstance(query, str) or not query.strip():
            return tool_error_payload()
        operation = partial(
            core.search_verified_research_reports,
            query,
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            limit=limit,
        )
    elif action == "inspect":
        if (
            query is not None
            or limit != _DEFAULT_LIMIT
            or not all(isinstance(value, str) and value.strip() for value in (podcast_id, episode_ref, source_digest))
        ):
            return tool_error_payload()
        operation = partial(
            core.inspect_verified_research_report,
            podcast_id,
            episode_ref,
            source_digest,
        )
    else:
        return tool_error_payload()

    try:
        return success(core.result_to_dict(operation()))
    except Exception:
        return tool_error_payload()


def _valid_limit(limit: int) -> bool:
    return isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= _MAX_LIMIT


def tool_error_payload() -> dict[str, Any]:
    return {"ok": False, "error_type": _ERROR_TYPE, "message": _ERROR_MESSAGE}
