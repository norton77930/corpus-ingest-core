"""MCP adapter for verified report gap backlog."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import verified_report_gap_backlog as core

_ERROR_TYPE = "VerifiedReportGapBacklogInputError"
_ERROR_MESSAGE = "verified report gap backlog query failed"
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100


def dispatch(
    *,
    success: Callable[[Any], dict[str, Any]],
    podcast_id: str,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Validate envelope and delegate once to Core."""

    if not isinstance(podcast_id, str) or not podcast_id.strip():
        return tool_error_payload()
    if type(limit) is not int or not (1 <= limit <= _MAX_LIMIT):
        return tool_error_payload()
    try:
        return success(core.result_to_dict(core.list_verified_report_gap_backlog(podcast_id, limit=limit)))
    except Exception:
        return tool_error_payload()


def tool_error_payload() -> dict[str, Any]:
    return {"ok": False, "error_type": _ERROR_TYPE, "message": _ERROR_MESSAGE}
