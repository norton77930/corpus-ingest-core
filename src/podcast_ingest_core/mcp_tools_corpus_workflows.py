"""MCP tool group: corpus workflow tools 13-16 (registration order is import order).

Tools: run_corpus_episode_completion_workflow,
run_corpus_latest_episode_deterministic_workflow,
run_latest_episode_verified_research_report_workflow,
run_episode_verified_research_report_workflow. Bounded envelopes only —
dependency details and tracebacks never leak.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from . import corpus_episode_completion_workflow_runner as completion_workflow_runner
from . import corpus_latest_episode_deterministic_workflow_runner as latest_deterministic_workflow_runner
from . import latest_episode_verified_research_report_workflow_runner as verified_research_report_workflow_runner
from . import mcp_episode_verified_research_report
from .mcp_runtime import SEMANTIC_API_COST_ACK, mcp, tool_error, tool_success


_COMPLETION_EXECUTABLE_ACTIONS = {
    "intake",
    "audio_download",
    "local_transcription",
    "deterministic_remediation",
    "semantic_summary",
    "semantic_review",
}
_COMPLETION_TOOL_ERROR_TYPE = "CorpusEpisodeCompletionWorkflowRunnerFailedError"
_COMPLETION_TOOL_ERROR_MESSAGE = "corpus episode completion workflow command failed"
_LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_TYPE = (
    "CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError"
)
_LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_MESSAGE = (
    "corpus latest episode deterministic workflow command failed"
)
_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_TYPE = (
    "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError"
)
_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_MESSAGE = (
    "latest episode verified research report workflow command failed"
)
_SAFE_EPISODE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")


@mcp.tool()
def run_corpus_episode_completion_workflow(
    podcast_id: str,
    episode_ref: str = "latest",
    action: str = "next",
    confirm: bool = False,
    api_cost_ack: str = "",
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> dict[str, Any]:
    """Preview or advance one episode by one explicitly confirmed action."""

    if _completion_request_rejected_early(
        episode_ref=episode_ref,
        action=action,
        confirm=confirm,
        api_cost_ack=api_cost_ack,
    ):
        return _completion_tool_error()

    return _completion_workflow_tool_call(
        operation=lambda: completion_workflow_runner.run_corpus_episode_completion_workflow(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            action=action,
            confirm=confirm,
            api_cost_ack=api_cost_ack,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            progress_callback=None,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_corpus_latest_episode_deterministic_workflow(
    podcast_id: str,
    confirm: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
) -> dict[str, Any]:
    """Preview or process one current latest episode through local deterministic stages."""

    return _latest_deterministic_workflow_tool_call(
        operation=lambda: latest_deterministic_workflow_runner.run_corpus_latest_episode_deterministic_workflow(
            podcast_id,
            confirm=confirm,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_latest_episode_verified_research_report_workflow(
    podcast_id: str,
    confirm: bool = False,
    expected_episode_ref: str | None = None,
    api_cost_ack: str = "",
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> dict[str, Any]:
    """Preview or complete one approved latest verified research report workflow."""

    if _verified_research_report_request_rejected_early(
        confirm=confirm,
        expected_episode_ref=expected_episode_ref,
        api_cost_ack=api_cost_ack,
    ):
        return _verified_research_report_tool_error()
    return _verified_research_report_workflow_tool_call(
        operation=lambda: verified_research_report_workflow_runner.run_latest_episode_verified_research_report_workflow(
            podcast_id,
            confirm=confirm,
            expected_episode_ref=expected_episode_ref,
            api_cost_ack=api_cost_ack,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_episode_verified_research_report_workflow(
    podcast_id: str,
    episode_ref: str,
    confirm: bool = False,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
) -> dict[str, Any]:
    """Preview or publish one explicit-episode verified research report (assemble only)."""

    return mcp_episode_verified_research_report.dispatch(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=confirm,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
    )


def _completion_workflow_tool_call(
    *,
    operation: Callable[[], Any],
    confirm: bool,
) -> dict[str, Any]:
    """Map 016 Core results into bounded envelopes without dependency details."""

    try:
        result = operation()
        payload = completion_workflow_runner.result_to_dict(result)
    except Exception:
        return _completion_tool_error()

    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": _completion_result_requires_confirmation(result),
        "data": payload,
    }


def _latest_deterministic_workflow_tool_call(
    *,
    operation: Callable[[], Any],
    confirm: bool,
) -> dict[str, Any]:
    """Map 017 Core results into the existing bounded MCP envelope."""

    try:
        result = operation()
        payload = latest_deterministic_workflow_runner.result_to_dict(result)
    except Exception:
        return tool_error(
            _LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_MESSAGE,
            _LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_TYPE,
        )

    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": payload,
    }


def _verified_research_report_workflow_tool_call(
    *, operation: Callable[[], Any], confirm: bool
) -> dict[str, Any]:
    """Map SPEC 018 Core results into a category-only bounded MCP envelope."""

    try:
        result = operation()
        payload = verified_research_report_workflow_runner.result_to_dict(result)
    except Exception:
        return _verified_research_report_tool_error()
    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": payload,
    }


def _verified_research_report_request_rejected_early(
    *, confirm: bool, expected_episode_ref: str | None, api_cost_ack: str
) -> bool:
    """Reject unapproved confirmed requests before RSS or Core access."""

    if not confirm:
        return False
    return (
        not isinstance(expected_episode_ref, str)
        or not _SAFE_EPISODE_REF_PATTERN.fullmatch(expected_episode_ref)
        or expected_episode_ref.casefold() == "latest"
        or api_cost_ack != SEMANTIC_API_COST_ACK
    )


def _verified_research_report_tool_error() -> dict[str, Any]:
    return tool_error(
        _VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_MESSAGE,
        _VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_TYPE,
    )


def _completion_request_rejected_early(
    *,
    episode_ref: str,
    action: str,
    confirm: bool,
    api_cost_ack: str,
) -> bool:
    """Keep invalid confirmed requests away from selection and provider work.

    Normalizes agent-facing inputs, then delegates the rejection rules to the
    Core single source (specs/025-core-consolidation FR-006).
    """

    if not confirm:
        return False
    normalized_action = action.strip().casefold() if isinstance(action, str) else ""
    normalized_selector = (
        episode_ref.strip().casefold() if isinstance(episode_ref, str) else ""
    )
    return (
        completion_workflow_runner.confirmed_request_rejection_reason(
            selector=normalized_selector,
            action=normalized_action,
            api_cost_ack=api_cost_ack,
        )
        is not None
    )


def _completion_result_requires_confirmation(result: Any) -> bool:
    selected_action = getattr(result, "selected_action", None)
    if selected_action not in _COMPLETION_EXECUTABLE_ACTIONS:
        return False
    return any(
        getattr(row, "status", None) == "selected"
        and getattr(row, "requires_confirmation", False) is True
        for row in (getattr(result, "rows", None) or ())
    )


def _completion_tool_error() -> dict[str, Any]:
    return tool_error(_COMPLETION_TOOL_ERROR_MESSAGE, _COMPLETION_TOOL_ERROR_TYPE)
