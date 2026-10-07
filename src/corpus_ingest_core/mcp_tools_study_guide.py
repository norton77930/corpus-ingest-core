"""MCP tool group: study-guide bundle (Tool 26).

Imported last by the ``mcp_server`` facade so Tools 1-25 keep their slots.
Preview and confirm each delegate once to Core. This module does not read
files, choose a provider, or synthesize an acknowledgement.
"""

from __future__ import annotations

from typing import Any

from . import study_guide_bundle
from .errors import (
    LLMProviderConfigError,
    PodcastIngestCoreError,
    StudyGuideBundleError,
    StudyGuideBundleStateError,
    _STUDY_GUIDE_STATE_GENERIC,
    _STUDY_GUIDE_STATE_MESSAGES,
)
from .mcp_runtime import mcp, tool_action_plan, tool_error, tool_success

NOT_INVESTMENT_ADVICE = "Research framework only: no buy/sell/hold, target price, or guaranteed return."
_BUNDLE_MESSAGE = _STUDY_GUIDE_STATE_GENERIC
_LLM_MESSAGE = (
    "Confirmed generation requires the exact API-cost acknowledgement "
    "and a valid local provider configuration."
)
_OPERATION_MESSAGE = (
    "The requested study-guide operation could not be completed "
    "with the supplied identifiers or local configuration."
)
_UNKNOWN_MESSAGE = "Study-guide operation failed; inspect local state before retrying."
_CACHE_RISK = (
    "SQLite cache may be stale; rebuild cache manually. This workflow never rebuilds it automatically."
)


@mcp.tool()
def generate_study_guide_bundle(
    podcast_id: str = "",
    episode_ref: str = "",
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
) -> dict[str, Any]:
    """Side-effect tool: confirm=false is a zero-write, zero-network preview. confirm=true may call an external LLM and then needs the exact api_cost_ack."""

    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "force": force,
    }
    if not confirm:
        try:
            result = study_guide_bundle.run_study_guide_bundle(
                podcast_id,
                episode_ref,
                confirm=False,
                force=force,
            )
        except Exception as exc:
            return _safe_error(exc)
        plan = study_guide_bundle.describe_study_guide_plan(result)
        if plan["requires_llm"]:
            llm_risk = (
                "Confirmed generation calls an external LLM and requires the exact api_cost_ack. "
                "Reuse and cover-only do not."
            )
        else:
            llm_risk = "This confirm does not call an LLM and does not need an API-cost acknowledgement."
        response = tool_action_plan(
            tool_name="generate_study_guide_bundle",
            action=(
                "Plan one study-guide lecture from the existing learning-notes summary. "
                "Preview reads local metadata only and writes nothing."
            ),
            inputs=inputs,
            writes=result.planned_writes,
            risks=[
                "Every successful confirm writes run reports.",
                llm_risk,
                _CACHE_RISK,
                NOT_INVESTMENT_ADVICE,
            ],
        )
        response["reads"] = list(result.planned_reads)
        response["reuses"] = list(result.planned_reuses)
        response["metadata_writes"] = list(result.metadata_writes)
        response["report_writes"] = list(plan["report_writes"])
        response["requires_llm"] = plan["requires_llm"]
        response["run_mode"] = result.run_mode
        response["network_read"] = False
        response["not_investment_advice"] = result.not_investment_advice
        response["warnings"] = list(result.warnings)
        return response

    try:
        result = study_guide_bundle.run_study_guide_bundle(
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
    if isinstance(exc, StudyGuideBundleStateError):
        message = _STUDY_GUIDE_STATE_MESSAGES.get(exc.reason_code, _STUDY_GUIDE_STATE_GENERIC)
        return tool_error(message, "StudyGuideBundleStateError")
    if isinstance(exc, LLMProviderConfigError):
        return tool_error(_LLM_MESSAGE, "LLMProviderConfigError")
    if isinstance(exc, StudyGuideBundleError):
        return tool_error(_BUNDLE_MESSAGE, "StudyGuideBundleError")
    if isinstance(exc, PodcastIngestCoreError):
        return tool_error(_OPERATION_MESSAGE, "PodcastIngestCoreError")
    if isinstance(exc, ValueError):
        return tool_error(_OPERATION_MESSAGE, "ValueError")
    return tool_error(_UNKNOWN_MESSAGE, "InternalError")
