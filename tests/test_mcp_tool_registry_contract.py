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
SIDE_EFFECT_TOOLS = {
    "download_audio",
    "transcribe_episode",
    "summarize_episode_extractive",
    "extract_mentions",
    "semantic_summarize_episode",
    "run_research_workflow",
}
EXPECTED_TOOLS = READ_QUERY_TOOLS | SIDE_EFFECT_TOOLS


def _registered_tool_names() -> set[str]:
    from podcast_ingest_core import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    return {tool.name for tool in tools}


def test_mcp_registry_exposes_exactly_the_reviewed_tool_set():
    actual = _registered_tool_names()
    assert len(actual) == 12
    assert actual == EXPECTED_TOOLS


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
