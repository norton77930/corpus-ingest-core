"""Append-only read-query Tool31 for the learning workflow overview."""
from __future__ import annotations
from typing import Any
from . import learning_workflow_status
from .mcp_runtime import mcp, tool_error, tool_success

@mcp.tool()
def inspect_learning_workflow_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Offline overview of scoped progress, lineage and recovery observations; no execution authorization."""
    try:
        return tool_success(learning_workflow_status.inspect_learning_workflow_status(podcast_id, episode_ref))
    except ValueError:
        return tool_error(learning_workflow_status.INVALID_IDENTITY_MESSAGE, "ValueError")
    except Exception:
        return tool_error(learning_workflow_status.QUERY_ERROR_MESSAGE, "InternalError")
