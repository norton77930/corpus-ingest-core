"""Read-query Tool 27: one local learning next-step decision, never execution."""
from __future__ import annotations

from typing import Any

from . import learning_workflow_next_step
from .mcp_runtime import mcp, tool_error, tool_success


@mcp.tool()
def suggest_learning_workflow_next_step(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Read-only local query for one explicit episode; no network, writes or LLM. Suggestions are previews, not execution authorization. Completion means reuse, not source freshness or quality."""
    try:
        result = learning_workflow_next_step.suggest_learning_workflow_next_step(podcast_id, episode_ref)
        return tool_success(result)
    except ValueError:
        return tool_error(learning_workflow_next_step.INVALID_IDENTITY_MESSAGE, "ValueError")
    except learning_workflow_next_step.LearningWorkflowQueryError:
        return tool_error(learning_workflow_next_step.QUERY_ERROR_MESSAGE, "LearningWorkflowQueryError")
    except Exception:
        return tool_error(learning_workflow_next_step.QUERY_ERROR_MESSAGE, "InternalError")
