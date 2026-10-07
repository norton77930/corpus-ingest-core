"""Append-only read-query Tool28 for derivation lineage."""
from __future__ import annotations

from typing import Any

from . import workflow_derivation
from .mcp_runtime import mcp, tool_error, tool_success


@mcp.tool()
def inspect_workflow_derivation_lineage(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Read-only offline comparison of recorded derivation inputs/outputs for one explicit episode. No generation, repair, network or LLM. Custom-context and legacy outputs cannot establish currentness."""
    try:
        return tool_success(workflow_derivation.inspect_workflow_derivation_lineage(podcast_id, episode_ref))
    except ValueError:
        return tool_error(workflow_derivation.LINEAGE_INVALID_IDENTITY_MESSAGE, "ValueError")
    except Exception:
        return tool_error(workflow_derivation.LINEAGE_QUERY_ERROR_MESSAGE, "InternalError")
