"""Append-only read-query Tool30 for learning-bundle recovery."""
from __future__ import annotations
from typing import Any
from . import learning_bundle_recovery
from .mcp_runtime import mcp, tool_error, tool_success

@mcp.tool()
def inspect_learning_bundle_recovery(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Read-only offline inspection of five fixed bundle locations; no cleanup, repair or publication proof."""
    try:
        return tool_success(learning_bundle_recovery.inspect_learning_bundle_recovery(podcast_id, episode_ref))
    except ValueError:
        return tool_error(learning_bundle_recovery.INVALID_IDENTITY_MESSAGE, "ValueError")
    except Exception:
        return tool_error(learning_bundle_recovery.QUERY_ERROR_MESSAGE, "InternalError")
