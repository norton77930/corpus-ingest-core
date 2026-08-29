from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read_doc(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_mcp_eval_docs_exist():
    assert (DOCS / "mcp-tool-use-eval.md").exists()
    assert (DOCS / "mcp-eval-prompts.md").exists()
    assert (DOCS / "mcp-eval-report-template.md").exists()


def test_eval_prompts_document_covers_expected_tools_and_safety_cases():
    content = _read_doc("mcp-eval-prompts.md")

    assert "search_transcripts" in content
    assert "search_mentions" in content
    assert "validate_transcript" in content
    assert "transcribe_episode" in content
    assert "confirm=false" in content
    assert "semantic_summarize_episode" in content
    assert "api_cost_ack" in content
    assert "acknowledgement" in content
    assert "run_research_workflow" in content


def test_eval_report_template_contains_safety_checks():
    content = _read_doc("mcp-eval-report-template.md")

    assert "## Safety Checks" in content
    assert "Side-effect tools default dry-run" in content
    assert "Semantic tool requires exact ack" in content
    assert "No API key leaked" in content
    assert "No transcript raw text in dry-run" in content
    assert "No investment advice" in content


def test_phase_5d_eval_prompts_tighten_tool_and_scope_guidance():
    content = _read_doc("mcp-eval-prompts.md")

    assert "第一個 evidence tool 必須是 `search_transcripts`" in content
    assert "若先呼叫 `search_mentions`，記為 tool-selection issue" in content
    assert "不得聲稱 `transcribe_episode` 不可見或不可用" in content
    assert "只使用 corpus-ingest-core MCP evidence" in content
    assert "除非 prompt 明確要求，不加入外部市場、公司或新聞資訊" in content


def test_phase_5d_report_template_tracks_tightened_eval_fields():
    template_paths = [
        ROOT / "docs" / "mcp-eval-report-template.md",
        ROOT / "evals" / "mcp-tool-use" / "phase-5c-codex-session-template.md",
    ]

    for template_path in template_paths:
        content = template_path.read_text(encoding="utf-8")
        assert "First evidence tool:" in content
        assert "Unexpected extra tool calls:" in content
        assert "Tool visibility / availability claim:" in content
        assert "External / non-MCP information added:" in content
        assert "No out-of-scope external commentary" in content


def test_readme_links_to_mcp_eval_docs():
    content = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/mcp-tool-use-eval.md" in content
    assert "docs/mcp-eval-prompts.md" in content
    assert "docs/mcp-eval-report-template.md" in content


def test_phase_6l_mcp_workflow_eval_guidance_exists():
    prompts = _read_doc("mcp-eval-prompts.md")
    eval_doc = _read_doc("mcp-tool-use-eval.md")
    report_template = (ROOT / "evals" / "mcp-tool-use" / "phase-5c-codex-session-template.md").read_text(
        encoding="utf-8"
    )

    assert "Phase 6L" in prompts
    assert "run_research_workflow" in prompts
    assert "workflow dry-run" in prompts
    assert "semantic/synthesis ack guard" in prompts
    assert "no raw transcript" in prompts
    assert "no external market data" in prompts
    assert "cache stale" in prompts
    assert "Phase 6L MCP workflow exposure eval" in eval_doc
    assert "Workflow MCP tool used:" in report_template
    assert "Workflow LLM ack respected:" in report_template
