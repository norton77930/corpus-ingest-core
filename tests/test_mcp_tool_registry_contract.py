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
SOURCE_REVALIDATION_TOOL = "revalidate_verified_research_report_sources"
COVERAGE_TOOL = "query_verified_research_report_coverage"
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
    SOURCE_REVALIDATION_TOOL,
    COVERAGE_TOOL,
}


def _registered_tool_names() -> set[str]:
    from podcast_ingest_core import mcp_server

    tools = asyncio.run(mcp_server.mcp.list_tools())
    return {tool.name for tool in tools}


def test_mcp_registry_exposes_exactly_the_reviewed_tool_set():
    actual = _registered_tool_names()
    assert len(actual) == 19
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
        SOURCE_REVALIDATION_TOOL,
        COVERAGE_TOOL,
    ]


def test_tools_one_through_eighteen_preserve_exact_signature_order_and_defaults():
    from podcast_ingest_core import mcp_server

    required = "<required>"
    expected = {
        "list_episodes": [("podcast_id", "gooaye"), ("limit", 10)],
        "get_episode": [("podcast_id", "gooaye"), ("episode_ref", "latest")],
        "validate_transcript": [("podcast_id", "gooaye"), ("episode_ref", "latest")],
        "search_transcripts": [("query", required), ("podcast_id", "gooaye"), ("limit", 10), ("search_mode", "auto"), ("context_segments", 0), ("case_sensitive", False)],
        "search_mentions": [("query", required), ("podcast_id", "gooaye"), ("mention_type", None), ("limit", 10), ("case_sensitive", False)],
        "rebuild_cache": [("podcast_id", None), ("force", False)],
        "download_audio": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("confirm", False), ("force", False)],
        "summarize_episode_extractive": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("confirm", False), ("force", False), ("allow_partial", False), ("max_quotes", 10), ("window_seconds", 300)],
        "extract_mentions": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("confirm", False), ("force", False), ("allow_partial", False), ("max_evidence_per_mention", 5)],
        "transcribe_episode": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("confirm", False), ("model", "tiny"), ("device", "cpu"), ("compute_type", "int8"), ("vad_filter", False), ("force", False)],
        "semantic_summarize_episode": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("confirm", False), ("api_cost_ack", ""), ("provider", "openai-compatible"), ("model", None), ("base_url", None), ("api_key_env", "OPENAI_API_KEY"), ("force", False), ("chunk_seconds", 600), ("max_segments_per_chunk", 120), ("allow_partial", False)],
        "run_research_workflow": [("podcast_id", "gooaye"), ("episode_ref", "latest"), ("stock_query", None), ("confirm", False), ("force", False), ("allow_partial", False), ("include_semantic_summary", False), ("include_stock_lens_synthesis", False), ("api_cost_ack", ""), ("semantic_provider", "openai-compatible"), ("semantic_model", None), ("semantic_base_url", None), ("semantic_api_key_env", "OPENAI_API_KEY"), ("semantic_chunk_seconds", 600), ("semantic_max_segments_per_chunk", 120), ("synthesis_provider", "openai-compatible"), ("synthesis_model", None), ("synthesis_base_url", None), ("synthesis_api_key_env", "OPENAI_API_KEY"), ("synthesis_max_prompt_chars", 24000), ("max_evidence_per_mention", 5), ("report_window_seconds", 300), ("max_evidence_per_section", 5), ("max_candidates_per_node", 5), ("max_evidence_per_candidate", 5), ("max_stock_evidence_items", 10)],
        "run_corpus_episode_completion_workflow": [("podcast_id", required), ("episode_ref", "latest"), ("action", "next"), ("confirm", False), ("api_cost_ack", ""), ("transcription_model", None), ("transcription_device", "cpu"), ("transcription_compute_type", "int8"), ("transcription_vad_filter", False), ("semantic_provider", "openai-compatible"), ("semantic_model", None), ("semantic_base_url", None), ("semantic_api_key_env", "OPENAI_API_KEY"), ("semantic_chunk_seconds", 600), ("semantic_max_segments_per_chunk", 120)],
        "run_corpus_latest_episode_deterministic_workflow": [("podcast_id", required), ("confirm", False), ("transcription_model", None), ("transcription_device", "cpu"), ("transcription_compute_type", "int8"), ("transcription_vad_filter", False)],
        "run_latest_episode_verified_research_report_workflow": [("podcast_id", required), ("confirm", False), ("expected_episode_ref", None), ("api_cost_ack", ""), ("stock_query", None), ("include_fixture_verification", False), ("transcription_model", None), ("transcription_device", "cpu"), ("transcription_compute_type", "int8"), ("transcription_vad_filter", False), ("semantic_provider", "openai-compatible"), ("semantic_model", None), ("semantic_chunk_seconds", 600), ("semantic_max_segments_per_chunk", 120)],
        "run_episode_verified_research_report_workflow": [("podcast_id", required), ("episode_ref", required), ("confirm", False), ("stock_query", None), ("include_fixture_verification", False)],
        "query_verified_research_report_catalog": [("action", "list"), ("podcast_id", None), ("episode_ref", None), ("source_digest", None), ("query", None), ("limit", 50)],
        "revalidate_verified_research_report_sources": [("podcast_id", required), ("episode_ref", required), ("source_digest", required)],
        "query_verified_research_report_coverage": [("podcast_id", required), ("has_bundle", None), ("limit", 50)],
    }

    actual = {
        name: [
            (parameter.name, required if parameter.default is inspect.Parameter.empty else parameter.default)
            for parameter in inspect.signature(getattr(mcp_server, name)).parameters.values()
        ]
        for name in expected
    }
    assert actual == expected


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


def test_each_client_setup_doc_locks_the_current_registry_contract():
    for filename in ("claude-mcp-setup.md", "codex-mcp-setup.md"):
        setup = (ROOT / "docs" / filename).read_text(encoding="utf-8")
        assert "exactly 19 tools" in setup
        assert "`query_verified_research_report_coverage`" in setup
        assert "Tools 1–18" in setup
        assert "現在有 exact 13 個 reviewed tools" not in setup
        assert "current registry has exactly 17" not in setup

    framework = (ROOT / "docs" / "ai-development-framework.md").read_text(
        encoding="utf-8"
    )
    assert "恰 14 個" not in framework
    assert "恰 19 個" in framework


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


def test_source_revalidation_tool_is_read_only_and_exposes_only_exact_locator_inputs():
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.revalidate_verified_research_report_sources)
    assert list(signature.parameters) == ["podcast_id", "episode_ref", "source_digest"]
    assert SOURCE_REVALIDATION_TOOL not in SIDE_EFFECT_TOOLS
    for forbidden in (
        "confirm",
        "ack",
        "path",
        "output",
        "latest",
        "limit",
        "query",
        "provider",
        "network",
    ):
        assert forbidden not in signature.parameters
