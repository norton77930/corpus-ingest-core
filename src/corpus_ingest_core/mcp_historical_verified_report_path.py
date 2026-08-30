"""MCP adapter for historical verified-report next-step suggestion."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import historical_verified_report_path as core

_ERROR_TYPE = "HistoricalVerifiedReportPathInputError"
_ERROR_MESSAGE = "historical verified report path suggestion failed"


def dispatch(
    *,
    success: Callable[[Any], dict[str, Any]],
    podcast_id: str,
    episode_ref: str,
) -> dict[str, Any]:
    """Validate envelope and delegate once to Core."""

    if not isinstance(podcast_id, str) or not podcast_id.strip():
        return tool_error_payload()
    if not isinstance(episode_ref, str) or not episode_ref.strip():
        return tool_error_payload()
    try:
        return success(core.result_to_dict(core.suggest_historical_verified_report_next_step(podcast_id, episode_ref)))
    except Exception:
        return tool_error_payload()


def tool_error_payload() -> dict[str, Any]:
    return {"ok": False, "error_type": _ERROR_TYPE, "message": _ERROR_MESSAGE}
