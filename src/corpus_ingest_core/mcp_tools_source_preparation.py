"""Thin appended preparation and read-only job tools."""
from __future__ import annotations
from typing import Any
import re

from . import source_preparation
from . import mcp_runtime
from .mcp_runtime import mcp, tool_error, tool_success

_MESSAGES = {
    "invalid_transcription_settings":"The local source transcription settings are invalid; correct them and obtain a new preview.",
    "transcription_runtime_unavailable":"The configured transcription runtime is unavailable. No model fallback or automatic retry was performed.",
    "invalid_request":"Preparation request is invalid; use one supported source and its previewed plan binding.",
    "unsupported_source":"Preparation supports one YouTube or X video URL.",
    "metadata_unavailable":"Source metadata could not be verified. No automatic retry was performed.",
    "profile_missing":"The source profile is missing; configure it locally before preparing this source.",
    "source_type_mismatch":"The configured source type does not match this video source.",
    "inspection_unavailable":"Local preparation state could not be inspected safely.",
    "unsafe_path":"Preparation refused an unsafe managed path.",
    "partial_artifacts":"Partial or recovery artifacts require operator inspection; no cleanup was performed.",
    "previous_outcome_unconfirmed":"Previous preparation outcome requires operator inspection.",
    "plan_changed":"The preparation plan changed; obtain a new preview and fresh approval before submitting again.",
    "busy":"Another preparation source owns the execution slot.",
    "capacity_exceeded":"Preparation history capacity is full; history was preserved.",
    "store_unavailable":"Preparation metadata is unavailable; the recorded outcome cannot be assumed absent.",
    "launch_failed":"Worker start was refused. A job was recorded; this request was not retried.",
    "worker_host_incompatible":"The host does not permit independent workers. Use an independently managed MCP HTTP host; no host policy was changed.",
    "outcome_unconfirmed":"Preparation outcome is unconfirmed. Inspect current state before any new submission.",
}


def _safe_error(error: Exception) -> dict[str,Any]:
    reason = getattr(error,"reason",None) if isinstance(error,source_preparation.PreparationError) else None
    if type(reason) is not str or reason not in _MESSAGES:
        reason = "outcome_unconfirmed"
    response = tool_error(_MESSAGES[reason],"PreparationError" if isinstance(error,source_preparation.PreparationError) else "InternalError")
    response["reason"] = reason
    job_id=getattr(error,"job_id",None)
    if isinstance(error,source_preparation.PreparationError) and isinstance(job_id,str) and re.fullmatch(r"[a-f0-9]{32}",job_id):
        response["job_id"]=job_id
    return response


@mcp.tool()
def prepare_learning_source(url: str, confirm: bool = False, expected_plan_id: str = "") -> dict[str,Any]:
    """Preview one configured YouTube/X video; fresh confirmation starts one background transcript job bound to expected_plan_id. No LLM or learning-document generation."""
    try:
        result = source_preparation.prepare_learning_source(url,confirm=confirm,expected_plan_id=expected_plan_id,host_transport=mcp_runtime.ACTIVE_TRANSPORT)
    except Exception as error:
        return _safe_error(error)
    response = tool_success(result)
    if not confirm:
        response["dry_run"] = True
    return response


@mcp.tool()
def inspect_source_preparation_job(job_id: str) -> dict[str,Any]:
    """Read one preparation job's last recorded progress offline; never executes, retries, repairs or rebuilds cache."""
    try:
        return tool_success(source_preparation.inspect_source_preparation_job(job_id))
    except Exception as error:
        return _safe_error(error)
