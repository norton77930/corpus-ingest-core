"""AI handoff governance docs guards (Batch 2.5, GOV-T1..T7).

Locks the intended guidance of the governance docs framework:
- ``docs/agent-handoff.md`` stays the handoff entrypoint and keeps every
  non-negotiable boundary mapped to its guard test.
- ``docs/ai-development-framework.md`` keeps the instruction hierarchy,
  lifecycle, change classification, and verification commands.
- The ADR index and the six core ADRs exist with the short ADR format.
- README / AGENTS.md / verification matrix keep the cross-links so a new
  agent can find the governance docs.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ADR = DOCS / "architecture-decision-records"

BATCH2_GUARD_TESTS = [
    "test_repository_secret_boundary.py",
    "test_repository_gitignore_policy.py",
    "test_mcp_tool_registry_contract.py",
    "test_llm_ack_guard_contracts.py",
    "test_llm_cli_no_leak.py",
    "test_cache_rebuild_guard.py",
]

ADR_FILES = [
    "ADR-0001-thin-cli-thick-core.md",
    "ADR-0002-dry-run-confirm-boundary.md",
    "ADR-0003-no-investment-advice-boundary.md",
    "ADR-0004-source-of-truth-vs-cache.md",
    "ADR-0005-llm-input-output-boundary.md",
    "ADR-0006-spec-kit-governance.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_agent_handoff_maps_every_boundary_to_guard_tests():
    text = _read(DOCS / "agent-handoff.md")

    for phrase in [
        "AGENTS.md",
        ".specify/memory/constitution.md",
        "docs/verification-matrix.md",
        ".env",
        "api_cost_ack",
        "SEMANTIC_API_COST_ACK",
        "confirm=False",
        "No live market API",
        "No investment advice",
        "No automatic cache rebuild",
        "Thin CLI / thick core",
        "MCP JSON envelope",
        "constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge",
        "SPECIFY_FEATURE_DIRECTORY",
        "F-03",
        "F-14",
        "F-18",
    ]:
        assert phrase in text

    for guard in BATCH2_GUARD_TESTS:
        assert guard in text, f"agent-handoff.md must map a boundary to {guard}"


def test_ai_development_framework_keeps_hierarchy_lifecycle_and_checks():
    text = _read(DOCS / "ai-development-framework.md")

    for phrase in [
        "Instruction Hierarchy",
        "AGENTS.md",
        ".specify/memory/constitution.md",
        "constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge",
        "Definition of Ready",
        "Definition of Done",
        "docs-only",
        "spec-only",
        "deterministic runtime",
        "MCP tool",
        "LLM-facing",
        "side-effect workflow",
        "safety-boundary",
        "docs/verification-matrix.md",
        ".env",
        "git add .",
        "python -m pytest",
        "python -m compileall src scripts",
        "git diff --check",
    ]:
        assert phrase in text

    assert "恰 22 個" in text
    assert "恰 20 個" not in text
    assert "恰 19 個" not in text
    assert "恰 18 個" not in text
    assert "恰 17 個" not in text
    assert "恰 14 個" not in text
    assert "恰 13 個" not in text


def test_adr_index_and_core_adrs_exist_with_short_format():
    index = _read(ADR / "README.md")

    for filename in ADR_FILES:
        assert filename in index, f"ADR index must list {filename}"
        text = _read(ADR / filename)
        for section in [
            "## Status",
            "## Context",
            "## Decision",
            "## Consequences",
            "## Guardrails & Tests",
        ]:
            assert section in text, f"{filename} is missing section {section}"


def test_core_adrs_align_with_runtime_and_guard_facts():
    assert "src/podcast_ingest_core" in _read(ADR / "ADR-0001-thin-cli-thick-core.md")

    adr_0002 = _read(ADR / "ADR-0002-dry-run-confirm-boundary.md")
    assert "confirm=False" in adr_0002
    assert "dry-run" in adr_0002

    adr_0003 = _read(ADR / "ADR-0003-no-investment-advice-boundary.md")
    assert "buy/sell/hold" in adr_0003
    assert "target price" in adr_0003

    adr_0004 = _read(ADR / "ADR-0004-source-of-truth-vs-cache.md")
    assert "rebuild_cache" in adr_0004
    assert "source of truth" in adr_0004

    adr_0005 = _read(ADR / "ADR-0005-llm-input-output-boundary.md")
    assert "SEMANTIC_API_COST_ACK" in adr_0005
    assert "phase-6f-stock-lens-json-only" in adr_0005
    assert "F-03" in adr_0005

    adr_0006 = _read(ADR / "ADR-0006-spec-kit-governance.md")
    assert "full Spec Kit flow" in adr_0006
    assert "SPECIFY_FEATURE_DIRECTORY" in adr_0006
    assert ".specify/feature.json" in adr_0006
    assert "local-only" in adr_0006
    assert "gitignored" in adr_0006
    assert "untracked" in adr_0006


def test_readme_agents_and_verification_matrix_cross_link_governance_docs():
    readme = _read(ROOT / "README.md")
    agents = _read(ROOT / "AGENTS.md")
    matrix = _read(DOCS / "verification-matrix.md")

    for link in [
        "docs/agent-handoff.md",
        "docs/ai-development-framework.md",
        "docs/verification-matrix.md",
        "docs/architecture-decision-records/README.md",
    ]:
        assert link in readme, f"README.md must link {link}"

    assert "docs/agent-handoff.md" in agents
    assert "docs/ai-development-framework.md" in agents
    assert "docs/verification-matrix.md" in agents

    assert "git diff --check" in matrix
    assert "test_ai_governance_docs.py" in matrix

def test_015_docs_preserve_llm_secret_mcp_and_cache_boundaries():
    root = Path(__file__).resolve().parents[1]
    combined = "\n".join(
        (root / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            "README.md",
            "docs/architecture.md",
            "specs/README.md",
            "docs/verification-matrix.md",
        )
    )

    assert "exact api_cost_ack" in combined
    assert "before profile" in combined
    assert "`.env`" in combined
    assert "exact 12" in combined
    assert "does not rebuild" in combined
    assert "not investment advice" in combined
    assert "no generated_at" in combined


def test_016_docs_preserve_human_controlled_mcp_and_skill_boundaries():
    codex_setup = _read(DOCS / "codex-mcp-setup.md")
    readiness = _read(DOCS / "mcp-readiness.md")
    tool_eval = _read(DOCS / "mcp-tool-use-eval.md")
    prompts = _read(DOCS / "mcp-eval-prompts.md")
    quickstart = _read(
        ROOT
        / "specs"
        / "016-corpus-episode-completion-workflow-runner"
        / "quickstart.md"
    )

    assert "run_corpus_episode_completion_workflow" in codex_setup
    assert "corpus-episode-completion" in codex_setup
    assert "exact 13" in readiness
    assert "corpus-episode-completion" in readiness
    assert "run_corpus_episode_completion_workflow" in tool_eval
    assert "run_corpus_episode_completion_workflow" in prompts
    assert "confirm=false" in prompts
    assert "fresh ephemeral" in quickstart
    assert "unsafe podcast id" in quickstart
    assert "no CLI" in quickstart
