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
    # The research boundary claims and the Phase 6H-6V.1 history moved out of
    # README.md: contract wording now lives in docs/api.md and the phase
    # history in docs/agent-handoff.md. README keeps the entry-point links.
    operator_docs = "\n".join(
        [readme, _read(DOCS / "api.md"), _read(DOCS / "agent-handoff.md")]
    )

    assert "docs/research-safety-eval.md" in readme
    assert "docs/research-eval-prompts.md" in readme
    assert "evals/research-safety/phase-6h-research-session-template.md" in operator_docs
    assert "LLM 前置 safety gate" in roadmap
    assert "Phase 6I" in roadmap
    assert "optional semantic summary execution inside research workflow" in operator_docs
    assert "no MCP tool changes" in operator_docs
    assert "Phase 6J" in roadmap
    assert "Stock Lens LLM Synthesis" in roadmap
    assert "6F stock lens JSON only" in operator_docs
    assert "exact api_cost_ack" in operator_docs
    assert "no raw transcript" in operator_docs
    assert "no external market data" in operator_docs
    assert "no MCP tool changes" in operator_docs
    assert "Phase 6K" in roadmap
    assert "workflow opt-in synthesis" in operator_docs
    assert "include_stock_lens_synthesis" in operator_docs
    assert "Phase 6L" in roadmap
    assert "MCP exposure" in operator_docs
    assert "run_research_workflow" in operator_docs
    assert "dry-run first" in operator_docs
    assert "exact ack" in operator_docs
    assert "no automatic cache rebuild" in operator_docs
    assert "Phase 6M" in roadmap
    assert "fixture provider" in operator_docs
    assert "confirm guard" in operator_docs
    assert "no live market API" in operator_docs
    assert "no investment advice" in operator_docs
    assert "Phase 6N" in roadmap
    assert "include_external_data_verification" in operator_docs
    assert "optional workflow fixture verification" in operator_docs
    assert "no API key" in operator_docs
    assert "no automatic cache rebuild" in operator_docs
    assert "Phase 6O" in roadmap
    assert "research-llm-smoke" in operator_docs
    assert "OpenAI-compatible smoke" in operator_docs
    assert "Codex manual review" in operator_docs
    assert "no direct Codex-session backend" in operator_docs
    assert "no live market data" in operator_docs
    assert "no investment advice" in operator_docs
    assert "Phase 6R" in roadmap
    assert "Local `.env` Secret Loader" in roadmap
    assert "API_KEY" in operator_docs
    assert "MODEL" in operator_docs
    assert "BASE_URL" in operator_docs
    assert "--env-file" in operator_docs
    assert "--no-env-file" in operator_docs
    assert "不顯示 secret value" in operator_docs
    assert "OPENAI_MODEL" in operator_docs
    assert "OPENAI_BASE_URL" in operator_docs
    assert "Phase 6T" in roadmap
    assert "review report" in operator_docs
    assert "quality gate" in operator_docs
    assert "no LLM call" in operator_docs
    assert "no `.env` read" in operator_docs
    assert "no external market data" in operator_docs
    assert "Phase 6U" in roadmap
    assert "Semantic Summary Smoke Validation" in roadmap
    assert "run_semantic_summary_smoke.py" in operator_docs
    assert "review_semantic_summary_smoke.py" in operator_docs
    assert "transcript text outside this machine" in operator_docs
    assert "semantic summary smoke" in operator_docs
    assert "no raw transcript stdout" in operator_docs
    assert "no MCP tool changes" in operator_docs
    assert "no live market API" in operator_docs
    assert "no investment advice" in operator_docs
    assert "Phase 6U.1" in roadmap
    assert "semantic review guard" in operator_docs
    assert "stderr progress" in operator_docs
    assert "false positive" in operator_docs
    assert "Phase 6V" in roadmap
    assert "Phase 6V.1" in roadmap
    assert "reviewed semantic context" in operator_docs
    assert "phase-6f-stock-lens-json-plus-reviewed-semantic-summary" in operator_docs
    assert "boundary/context consistency" in operator_docs
    assert "no MCP tool changes" in operator_docs
    assert "no live market data" in operator_docs


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
