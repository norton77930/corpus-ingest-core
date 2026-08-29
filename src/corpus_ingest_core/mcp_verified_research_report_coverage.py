"""MCP adapter for the read-only verified research report coverage index."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import verified_research_report_coverage as core

_ERROR_TYPE = "VerifiedResearchReportCoverageInputError"
_ERROR_MESSAGE = "verified research report coverage query failed"
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100


def dispatch(
    *,
    success: Callable[[Any], dict[str, Any]],
    podcast_id: str,
    has_bundle: bool | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Validate the bounded MCP envelope and delegate once to Core."""

    if not _valid_limit(limit):
        return tool_error_payload()
    if has_bundle is not None and type(has_bundle) is not bool:
        return tool_error_payload()
    if not isinstance(podcast_id, str) or not podcast_id.strip():
        return tool_error_payload()
    try:
        return success(
            core.result_to_dict(
                core.list_verified_research_report_coverage(
                    podcast_id,
                    has_bundle=has_bundle,
                    limit=limit,
                )
            )
        )
    except Exception:
        return tool_error_payload()


def _valid_limit(limit: int) -> bool:
    return type(limit) is int and 1 <= limit <= _MAX_LIMIT


def tool_error_payload() -> dict[str, Any]:
    return {"ok": False, "error_type": _ERROR_TYPE, "message": _ERROR_MESSAGE}
