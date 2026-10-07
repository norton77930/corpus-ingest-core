"""Thin MCP Tool32 for one approved learning step."""
from __future__ import annotations
from typing import Any
from . import learning_workflow_advance
from .errors import (
    LLMProviderConfigError, PodcastIngestCoreError, StudyGuideBundleStateError,
    WorkflowDerivationStateError, _STUDY_GUIDE_STATE_MESSAGES, _STUDY_GUIDE_STATE_GENERIC,
    _WORKFLOW_DERIVATION_STATE_MESSAGES, _WORKFLOW_DERIVATION_STATE_GENERIC,
)
from .mcp_runtime import mcp, tool_error, tool_success


@mcp.tool()
def advance_learning_workflow(podcast_id: str, episode_ref: str, confirm: bool = False,
                              expected_action: str = "", expected_plan_id: str = "", api_cost_ack: str = "") -> dict[str, Any]:
    """Preview one learning action; confirm needs returned action/plan_id and exact cost acknowledgement for generation. Execute once then stop."""
    try:
        result = learning_workflow_advance.advance_learning_workflow(
            podcast_id, episode_ref, confirm=confirm, expected_action=expected_action,
            expected_plan_id=expected_plan_id, api_cost_ack=api_cost_ack)
    except Exception as exc:
        return _safe_error(exc)
    response = tool_success(result)
    if not confirm:
        response["dry_run"] = True
    return response


def _safe_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, learning_workflow_advance.LearningWorkflowPlanChangedError):
        return tool_error(learning_workflow_advance.PLAN_CHANGED_MESSAGE, "LearningWorkflowPlanChangedError")
    if isinstance(exc, learning_workflow_advance.LearningWorkflowAdvanceError):
        return tool_error(learning_workflow_advance.UNCERTAIN_MESSAGE, "LearningWorkflowAdvanceError")
    if isinstance(exc, LLMProviderConfigError):
        return tool_error("Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration.", "LLMProviderConfigError")
    for cls, messages, fallback in (
        (StudyGuideBundleStateError, _STUDY_GUIDE_STATE_MESSAGES, _STUDY_GUIDE_STATE_GENERIC),
        (WorkflowDerivationStateError, _WORKFLOW_DERIVATION_STATE_MESSAGES, _WORKFLOW_DERIVATION_STATE_GENERIC),
    ):
        if isinstance(exc, cls):
            message = messages.get(exc.reason_code, fallback) if type(exc.reason_code) is str else fallback
            return tool_error(message, cls.__name__)
    if isinstance(exc, ValueError):
        return tool_error(learning_workflow_advance.INVALID_REQUEST_MESSAGE, "ValueError")
    return tool_error(learning_workflow_advance.FAILURE_MESSAGE,
                      "PodcastIngestCoreError" if isinstance(exc, PodcastIngestCoreError) else "InternalError")
