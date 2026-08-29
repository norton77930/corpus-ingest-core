"""MCP adapter for read-only verified research report source revalidation."""

from __future__ import annotations

import re
from typing import Any, Callable

from . import verified_research_report_source_revalidation as core

_ERROR_TYPE = "VerifiedResearchReportSourceRevalidationInputError"
_ERROR_MESSAGE = "verified research report source revalidation failed"
_DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def dispatch(
    *,
    success: Callable[[Any], dict[str, Any]],
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> dict[str, Any]:
    """Validate one exact locator and delegate exactly one Core operation."""

    if not _valid_locator(podcast_id, episode_ref, source_digest):
        return tool_error_payload()
    try:
        result = core.revalidate_verified_research_report_sources(
            podcast_id,
            episode_ref,
            source_digest,
        )
        return success(core.result_to_dict(result))
    except Exception:
        return tool_error_payload()


def _valid_locator(podcast_id: object, episode_ref: object, source_digest: object) -> bool:
    return (
        isinstance(podcast_id, str)
        and 1 <= len(podcast_id) <= 128
        and bool(podcast_id.strip())
        and isinstance(episode_ref, str)
        and 1 <= len(episode_ref) <= 128
        and bool(episode_ref.strip())
        and isinstance(source_digest, str)
        and _DIGEST_PATTERN.fullmatch(source_digest) is not None
    )


def tool_error_payload() -> dict[str, Any]:
    return {"ok": False, "error_type": _ERROR_TYPE, "message": _ERROR_MESSAGE}
