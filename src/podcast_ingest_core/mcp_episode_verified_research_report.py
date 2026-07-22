"""MCP adapter surface for SPEC 019 (kept out of mcp_server.py bulk)."""

from __future__ import annotations

import re
from typing import Any, Callable

from . import episode_verified_research_report_workflow_runner as core
from .serialization import to_jsonable

_TOOL_ERROR_TYPE = "EpisodeVerifiedResearchReportWorkflowRunnerFailedError"
_TOOL_ERROR_MESSAGE = "episode verified research report workflow command failed"
_SAFE_EPISODE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")


def dispatch(
    *,
    podcast_id: str,
    episode_ref: str,
    confirm: bool = False,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
) -> dict[str, Any]:
    """Early-reject reserved selectors, then map Core results to MCP envelopes."""

    if request_rejected_early(confirm=confirm, episode_ref=episode_ref):
        return tool_error_payload()
    return tool_call(
        operation=lambda: core.run_episode_verified_research_report_workflow(
            podcast_id,
            episode_ref,
            confirm=confirm,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
        ),
        confirm=confirm,
    )


def request_rejected_early(*, confirm: bool, episode_ref: str) -> bool:
    """Reject blank and reserved selectors before Core."""

    if not isinstance(episode_ref, str) or not episode_ref.strip():
        return True
    if episode_ref.strip().casefold() in {"latest", "next"}:
        return True
    if confirm and not _SAFE_EPISODE_REF_PATTERN.fullmatch(episode_ref.strip()):
        return True
    return False


def tool_call(*, operation: Callable[[], Any], confirm: bool) -> dict[str, Any]:
    try:
        result = operation()
        payload = core.result_to_dict(result)
    except Exception:
        return tool_error_payload()
    if confirm:
        return {"ok": True, "data": to_jsonable(payload)}
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": to_jsonable(payload),
    }


def tool_error_payload() -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": _TOOL_ERROR_TYPE,
        "message": _TOOL_ERROR_MESSAGE,
    }
