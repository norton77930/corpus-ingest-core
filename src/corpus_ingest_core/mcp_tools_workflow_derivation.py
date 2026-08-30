"""MCP tool group: workflow derivation (Tool 25).

Imported last by the ``mcp_server`` facade so Tools 1-24 keep their slots.

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

from . import mcp_runtime, workflow_derivation
from .errors import PodcastIngestCoreError
from .mcp_runtime import mcp, tool_action_plan, tool_error

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
    """Side-effect tool: confirm=false is a zero-write, zero-network preview. confirm=true calls an external LLM and needs the exact api_cost_ack."""

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
        except PodcastIngestCoreError as exc:
            return tool_error(mcp_runtime._safe_error_message(exc), type(exc).__name__)
        except ValueError as exc:
            return tool_error(str(exc), "ValueError")
        except Exception as exc:
            return tool_error(mcp_runtime._redact_text(str(exc), None), type(exc).__name__)
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
                "Confirmed execution calls an external LLM and incurs cost; it requires the exact api_cost_ack",
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
        # The shared tool_action_plan envelope carries only writes. Reads matter
        # here because one of them is the operator policy file that constrains
        # what 06 may advise, and the agent cannot choose it.
        response["reads"] = result.planned_reads
        return response

    return mcp_runtime._tool_call(
        lambda: workflow_derivation.run_workflow_derivation(
            podcast_id,
            episode_ref,
            confirm=True,
            force=force,
            api_cost_ack=api_cost_ack,
        ),
        warnings=[WORKFLOW_DERIVATION_CACHE_STALE_WARNING, NOT_INVESTMENT_ADVICE],
    )
