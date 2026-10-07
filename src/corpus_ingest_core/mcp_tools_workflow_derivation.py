"""MCP tool group: workflow derivation (Tool 25).

Imported by the ``mcp_server`` facade so Tools 1-24 keep their slots.

Unlike Tools 23 and 24, Core here calls an LLM. Two consequences shape this
module. Preview returns before any provider is constructed, so it declares
``network_read=false`` rather than copying the video tools' ``true``. And the
exact ``api_cost_ack`` gate stays in ``llm_provider.require_exact_api_cost_ack``:
this module forwards the operator's value and never checks, defaults, or
transforms it, so the two can never drift apart. Core applies that gate only
where it will actually call a provider -- confirming a complete existing pair
reuses the files and legitimately needs no ack.
"""

from __future__ import annotations

from typing import Any

from . import workflow_derivation
from .errors import (
    PodcastIngestCoreError, WorkflowDerivationError, WorkflowDerivationStateError,
    LLMProviderConfigError, _WORKFLOW_DERIVATION_STATE_MESSAGES, _WORKFLOW_DERIVATION_STATE_GENERIC,
)
from .mcp_runtime import mcp, tool_action_plan, tool_error, tool_success

WORKFLOW_DERIVATION_CACHE_STALE_WARNING = workflow_derivation.CACHE_STALE_WARNING
NOT_INVESTMENT_ADVICE = "Research framework only: no buy/sell/hold, target price, or guaranteed return."


@mcp.tool()
def derive_workflow_bundle(
    podcast_id: str = "",
    episode_ref: str = "",
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
) -> dict[str, Any]:
    """Side-effect tool: confirm=false is a zero-write, zero-network preview. confirmed generation calls an external LLM and needs exact api_cost_ack; reuse does not."""

    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "force": force,
    }
    if not confirm:
        try:
            result = workflow_derivation.run_workflow_derivation(
                podcast_id,
                episode_ref,
                confirm=False,
                force=force,
            )
        except Exception as exc:
            return _safe_error(exc)
        response = tool_action_plan(
            tool_name="derive_workflow_bundle",
            action=(
                "Plan the 05/06 workflow derivation for one learning-notes lecture. "
                "Preview is zero-write and zero-network."
            ),
            inputs=inputs,
            writes=result.planned_writes,
            risks=[
                "Preview constructs no provider and writes nothing",
                "Confirmed generation calls an external LLM and requires exact api_cost_ack; complete-pair reuse does not. Every successful confirm writes run reports",
                "The operator workflow context is read from the repository default; this tool accepts no path",
                WORKFLOW_DERIVATION_CACHE_STALE_WARNING,
                NOT_INVESTMENT_ADVICE,
            ],
        )
        response["run_mode"] = result.run_mode
        response["network_read"] = False
        response["not_investment_advice"] = result.not_investment_advice
        response["warnings"] = result.warnings
        response["reuses"] = result.planned_reuses
        response["metadata_writes"] = result.metadata_writes
        # The shared tool_action_plan envelope carries only writes. Reads matter
        # here because one of them is the operator policy file that constrains
        # what 06 may advise, and the agent cannot choose it.
        response["reads"] = result.planned_reads
        return response

    try:
        result = workflow_derivation.run_workflow_derivation(
            podcast_id,
            episode_ref,
            confirm=True,
            force=force,
            api_cost_ack=api_cost_ack,
        )
    except Exception as exc:
        return _safe_error(exc)
    response = tool_success(result)
    response["warnings"] = list(result.warnings)
    return response


def _safe_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, WorkflowDerivationStateError):
        return tool_error(
            _WORKFLOW_DERIVATION_STATE_MESSAGES.get(exc.reason_code, _WORKFLOW_DERIVATION_STATE_GENERIC),
            "WorkflowDerivationStateError",
        )
    if isinstance(exc, LLMProviderConfigError):
        return tool_error(
            "Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration.",
            "LLMProviderConfigError",
        )
    if isinstance(exc, WorkflowDerivationError):
        return tool_error(_WORKFLOW_DERIVATION_STATE_GENERIC, "WorkflowDerivationError")
    operation_message = (
        "The requested workflow-derivation operation could not be completed "
        "with the supplied identifiers or local configuration."
    )
    if isinstance(exc, PodcastIngestCoreError):
        return tool_error(operation_message, "PodcastIngestCoreError")
    if isinstance(exc, ValueError):
        return tool_error(operation_message, "ValueError")
    return tool_error("Workflow-derivation operation failed; inspect local state before retrying.", "InternalError")
