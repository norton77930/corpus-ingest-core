from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVALS = ROOT / "evals"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_safety_eval_docs_exist():
    assert (DOCS / "research-safety-eval.md").exists()
    assert (DOCS / "research-eval-prompts.md").exists()
    assert (DOCS / "research-llm-smoke.md").exists()
    assert (
        EVALS
        / "research-safety"
        / "phase-6h-research-session-template.md"
    ).exists()
    assert (
        EVALS
        / "research-llm-smoke"
        / "phase-6o-llm-smoke-template.md"
    ).exists()


def test_research_eval_prompts_cover_llm_and_research_safety_cases():
    content = _read(DOCS / "research-eval-prompts.md")

    assert "Phase 6G dry-run" in content
    assert "run_research_workflow" in content
    assert "不寫 artifact" in content
    assert "不呼叫 LLM" in content
    assert "不自動 rebuild_cache" in content
    assert "semantic_summarize_episode" in content
    assert "api_cost_ack" in content
    assert "external API" in content
    assert "transcript transfer" in content
    assert "cost risk" in content
    assert "No raw transcript leakage" in content
    assert "not_fetched" in content
    assert "not_requested" in content
    assert "no-direct-podcast-evidence" in content
    assert "partial-draft" in content
    assert "buy/sell/hold" in content
    assert "target price" in content
    assert "guaranteed return" in content


def test_research_session_template_tracks_required_safety_fields():
    content = _read(
        EVALS / "research-safety" / "phase-6h-research-session-template.md"
    )

    assert "LLM tool used / not used" in content
    assert "API-cost acknowledgement status" in content
    assert "Raw transcript leakage" in content
    assert "Evidence traceability" in content
    assert "External data boundary respected" in content
    assert "Podcast evidence vs inference vs external status separation" in content
    assert "Investment-advice refusal result" in content
    assert "Partial transcript handling" in content
    assert "Cache stale handling" in content


def test_research_safety_eval_docs_link_from_readme_and_roadmap():
    readme = _read(ROOT / "README.md")
    roadmap = _read(DOCS / "roadmap.md")

    assert "docs/research-safety-eval.md" in readme
    assert "docs/research-eval-prompts.md" in readme
    assert "evals/research-safety/phase-6h-research-session-template.md" in readme
    assert "LLM 前置 safety gate" in roadmap
    assert "Phase 6I" in roadmap
    assert "optional semantic summary execution inside research workflow" in readme
    assert "no MCP tool changes" in readme
    assert "Phase 6J" in roadmap
    assert "Stock Lens LLM Synthesis" in roadmap
    assert "6F stock lens JSON only" in readme
    assert "exact api_cost_ack" in readme
    assert "no raw transcript" in readme
    assert "no external market data" in readme
    assert "no MCP tool changes" in readme
    assert "Phase 6K" in roadmap
    assert "workflow opt-in synthesis" in readme
    assert "include_stock_lens_synthesis" in readme
    assert "Phase 6L" in roadmap
    assert "MCP exposure" in readme
    assert "run_research_workflow" in readme
    assert "dry-run first" in readme
    assert "exact ack" in readme
    assert "no automatic cache rebuild" in readme
    assert "Phase 6M" in roadmap
    assert "fixture provider" in readme
    assert "confirm guard" in readme
    assert "no live market API" in readme
    assert "no investment advice" in readme
    assert "Phase 6N" in roadmap
    assert "include_external_data_verification" in readme
    assert "optional workflow fixture verification" in readme
    assert "no API key" in readme
    assert "no automatic cache rebuild" in readme
    assert "Phase 6O" in roadmap
    assert "research-llm-smoke" in readme
    assert "OpenAI-compatible smoke" in readme
    assert "Codex manual review" in readme
    assert "no direct Codex-session backend" in readme
    assert "no live market data" in readme
    assert "no investment advice" in readme
    assert "Phase 6R" in roadmap
    assert "Local `.env` Secret Loader" in roadmap
    assert "API_KEY" in readme
    assert "MODEL" in readme
    assert "BASE_URL" in readme
    assert "--env-file" in readme
    assert "--no-env-file" in readme
    assert "不顯示 secret value" in readme
    assert "OPENAI_MODEL" in readme
    assert "OPENAI_BASE_URL" in readme
    assert "Phase 6T" in roadmap
    assert "review report" in readme
    assert "quality gate" in readme
    assert "no LLM call" in readme
    assert "no `.env` read" in readme
    assert "no external market data" in readme
    assert "Phase 6U" in roadmap
    assert "Semantic Summary Smoke Validation" in roadmap
    assert "run_semantic_summary_smoke.py" in readme
    assert "review_semantic_summary_smoke.py" in readme
    assert "transcript text outside this machine" in readme
    assert "semantic summary smoke" in readme
    assert "no raw transcript stdout" in readme
    assert "no MCP tool changes" in readme
    assert "no live market API" in readme
    assert "no investment advice" in readme
    assert "Phase 6U.1" in roadmap
    assert "semantic review guard" in readme
    assert "stderr progress" in readme
    assert "false positive" in readme
    assert "Phase 6V" in roadmap
    assert "Phase 6V.1" in roadmap
    assert "reviewed semantic context" in readme
    assert "phase-6f-stock-lens-json-plus-reviewed-semantic-summary" in readme
    assert "boundary/context consistency" in readme
    assert "no MCP tool changes" in readme
    assert "no live market data" in readme


def test_research_llm_smoke_template_tracks_quality_fields():
    content = _read(
        EVALS
        / "research-llm-smoke"
        / "phase-6o-llm-smoke-template.md"
    )

    assert "Provider / model" in content
    assert "Artifact paths" in content
    assert "LLM input boundary" in content
    assert "Codex manual review notes" in content
    assert "Podcast evidence / inference / external status separation" in content
    assert "External boundary respected" in content
    assert "Prohibited advice check" in content
    assert "Gooaye Lens dimensions covered" in content
    assert "Quality score" in content


def test_phase_6u_spec_package_documents_semantic_smoke_validation():
    package = ROOT / "specs" / "006-llm-safety-synthesis-smoke-review"
    combined = "\n".join(
        _read(package / relative_path)
        for relative_path in [
            "spec.md",
            "plan.md",
            "tasks.md",
            "quickstart.md",
            "checklists/requirements.md",
        ]
    )

    for phrase in [
        "Phase 6U",
        "Semantic Summary Smoke Validation",
        "run_semantic_summary_smoke.py",
        "review_semantic_summary_smoke.py",
        "exact `api_cost_ack`",
        "transcript transfer",
        "no raw transcript stdout",
        "no live market API",
        "no MCP tool changes",
        "no investment advice",
        "Phase 6U.1",
        "semantic review guard",
        "stderr progress",
        "false positive",
        "Phase 6V",
        "Phase 6V.1",
        "reviewed semantic context",
        "phase-6f-stock-lens-json-plus-reviewed-semantic-summary",
        "boundary/context consistency",
        "no raw transcript",
        "no live market API",
        "no MCP tool changes",
    ]:
        assert phrase in combined
