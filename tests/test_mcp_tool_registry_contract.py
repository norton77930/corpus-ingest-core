"""MCP tool registry and docs alignment contract (Batch 2, B2-T3).

Invariants protected:
- The MCP server exposes exactly the reviewed tool set: adding or removing a
  tool must be a deliberate, test-visible change (audit F-07 guard).
- Every side-effect tool defaults to ``confirm=False`` (dry-run first).
- MCP responses keep the documented JSON envelope shapes.
- ``README.md`` and ``docs/mcp-usage.md`` list every registered tool, so the
  docs cannot drift away from the implementation again.
- The MCP ``run_research_workflow`` wrapper intentionally exposes only a
  subset of the core workflow parameters (audit F-08 characterization).
"""

from __future__ import annotations

import asyncio
import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

READ_QUERY_TOOLS = {
    "list_episodes",
    "get_episode",
    "validate_transcript",
    "search_transcripts",
    "search_mentions",
    "rebuild_cache",
}
LEGACY_SIDE_EFFECT_TOOLS = {
    "download_audio",
    "transcribe_episode",
    "summarize_episode_extractive",
    "extract_mentions",
    "semantic_summarize_episode",
    "run_research_workflow",
}
COMPLETION_WORKFLOW_TOOL = "run_corpus_episode_completion_workflow"
LATEST_DETERMINISTIC_WORKFLOW_TOOL = "run_corpus_latest_episode_deterministic_workflow"
VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL = "run_latest_episode_verified_research_report_workflow"
EPISODE_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL = (
    "run_episode_verified_research_report_workflow"
)
VERIFIED_RESEARCH_REPORT_CATALOG_TOOL = "query_verified_research_report_catalog"
LEGACY_TOOL_ORDER = [
    "list_episodes",
    "get_episode",
    "validate_transcript",
    "search_transcripts",
    "search_mentions",
    "rebuild_cache",
    "download_audio",
    "summarize_episode_extractive",
    "extract_mentions",
    "transcribe_episode",
    "semantic_summarize_episode",
    "run_research_workflow",
]
LEGACY_EXPECTED_TOOLS = READ_QUERY_TOOLS | LEGACY_SIDE_EFFECT_TOOLS
SIDE_EFFECT_TOOLS = LEGACY_SIDE_EFFECT_TOOLS | {
    COMPLETION_WORKFLOW_TOOL,
    LATEST_DETERMINISTIC_WORKFLOW_TOOL,
    VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
    EPISODE_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
}
EXPECTED_TOOLS = LEGACY_EXPECTED_TOOLS | {
    COMPLETION_WORKFLOW_TOOL,
    LATEST_DETERMINISTIC_WORKFLOW_TOOL,
    VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
    EPISODE_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
    VERIFIED_RESEARCH_REPORT_CATALOG_TOOL,
}


def _registered_tool_names() -> set[str]:
    from podcast_ingest_core import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    return {tool.name for tool in tools}


def test_mcp_registry_exposes_exactly_the_reviewed_tool_set():
    actual = _registered_tool_names()
    assert len(actual) == 17
    assert actual == EXPECTED_TOOLS
    assert LEGACY_EXPECTED_TOOLS <= actual


def test_workflow_tools_are_appended_after_the_preserved_twelve_tool_order():
    from podcast_ingest_core import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())

    assert [tool.name for tool in tools] == [
        *LEGACY_TOOL_ORDER,
        COMPLETION_WORKFLOW_TOOL,
        LATEST_DETERMINISTIC_WORKFLOW_TOOL,
        VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
        EPISODE_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL,
        VERIFIED_RESEARCH_REPORT_CATALOG_TOOL,
    ]


def test_side_effect_tools_default_to_dry_run_confirm_false():
    from podcast_ingest_core import mcp_server

    for name in sorted(SIDE_EFFECT_TOOLS):
        signature = inspect.signature(getattr(mcp_server, name))
        assert "confirm" in signature.parameters, f"{name} must take a confirm flag"
        assert signature.parameters["confirm"].default is False, (
            f"{name} must default to confirm=False (dry-run first)"
        )


def test_success_envelope_shape():
    from podcast_ingest_core.mcp_server import tool_success

    response = tool_success({"value": 1})
    assert response == {"ok": True, "data": {"value": 1}}

    with_warnings = tool_success([], warnings=["Cache may be stale"])
    assert with_warnings["ok"] is True
    assert with_warnings["warnings"] == ["Cache may be stale"]


def test_error_envelope_shape():
    from podcast_ingest_core.mcp_server import tool_error

    response = tool_error("boom", "ValueError")
    assert response == {"ok": False, "error_type": "ValueError", "message": "boom"}


def test_action_plan_envelope_shape():
    from podcast_ingest_core.mcp_server import tool_action_plan

    response = tool_action_plan(
        tool_name="example_tool",
        action="Do something locally.",
        inputs={"podcast_id": "gooaye"},
        writes=["data/example/..."],
        risks=["Writes local artifacts"],
    )
    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_confirmation"] is True
    assert set(response) >= {
        "ok",
        "dry_run",
        "requires_confirmation",
        "tool",
        "action",
        "inputs",
        "writes",
        "risks",
        "next_step",
    }


def test_readme_and_mcp_usage_doc_list_every_registered_tool():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = (ROOT / "docs" / "mcp-usage.md").read_text(encoding="utf-8")

    for name in sorted(EXPECTED_TOOLS):
        assert f"`{name}`" in readme, f"README.md must document MCP tool {name}"
        assert f"`{name}`" in usage, f"docs/mcp-usage.md must document MCP tool {name}"


def test_mcp_workflow_tool_exposes_deliberate_core_parameter_subset():
    # Audit F-08 characterization: the MCP workflow wrapper intentionally does
    # NOT expose the fixture external-data verification and reviewed semantic
    # context opt-ins of the core run_research_workflow. Exposing them through
    # MCP is a safety-boundary change that needs its own review (Batch 3).
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.run_research_workflow)
    for hidden_parameter in (
        "include_external_data_verification",
        "include_semantic_context_in_synthesis",
        "external_data_provider",
        "external_fixture_path",
        "synthesis_semantic_context_max_chars",
    ):
        assert hidden_parameter not in signature.parameters, (
            f"MCP run_research_workflow unexpectedly exposes {hidden_parameter}; "
            "this widens the reviewed MCP surface (see audit F-08)"
        )


def test_completion_workflow_tool_mirrors_the_bounded_core_schema():
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.run_corpus_episode_completion_workflow)
    assert list(signature.parameters) == [
        "podcast_id",
        "episode_ref",
        "action",
        "confirm",
        "api_cost_ack",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
        "semantic_provider",
        "semantic_model",
        "semantic_base_url",
        "semantic_api_key_env",
        "semantic_chunk_seconds",
        "semantic_max_segments_per_chunk",
    ]
    assert signature.parameters["confirm"].default is False
    for forbidden in (
        "force",
        "partial",
        "batch",
        "latest_n",
        "retry",
        "scheduler",
        "loop",
        "full_chain",
        "progress_callback",
    ):
        assert forbidden not in signature.parameters


def test_latest_deterministic_workflow_tool_exposes_only_local_inputs():
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(
        mcp_server.run_corpus_latest_episode_deterministic_workflow
    )
    assert list(signature.parameters) == [
        "podcast_id",
        "confirm",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
    ]
    assert signature.parameters["confirm"].default is False
    for forbidden in (
        "episode_ref",
        "force",
        "allow_partial",
        "semantic_provider",
        "semantic_model",
        "semantic_base_url",
        "semantic_api_key_env",
        "provider",
        "endpoint",
        "credential",
        "api_cost_ack",
        "retry",
        "scheduler",
        "progress_callback",
    ):
        assert forbidden not in signature.parameters


def test_catalog_tool_is_read_only_and_exposes_only_bounded_query_inputs():
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.query_verified_research_report_catalog)
    assert list(signature.parameters) == [
        "action",
        "podcast_id",
        "episode_ref",
        "source_digest",
        "query",
        "limit",
    ]
    assert signature.parameters["action"].default == "list"
    assert signature.parameters["podcast_id"].default is None
    assert signature.parameters["episode_ref"].default is None
    assert signature.parameters["source_digest"].default is None
    assert signature.parameters["query"].default is None
    assert signature.parameters["limit"].default == 50
    assert VERIFIED_RESEARCH_REPORT_CATALOG_TOOL not in SIDE_EFFECT_TOOLS
    for forbidden in (
        "confirm",
        "ack",
        "path",
        "output",
        "export",
        "provider",
        "network",
    ):
        assert forbidden not in signature.parameters
