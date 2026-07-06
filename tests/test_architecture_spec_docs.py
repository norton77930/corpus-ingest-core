from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SPEC = ROOT / "specs" / "001-gooaye-research-system"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_architecture_doc_reflects_phase_6t_research_system():
    text = _read(DOCS / "architecture.md")

    assert "Phase 6T" in text
    assert "Phase 0 僅固定" not in text
    for phrase in [
        "ingestion",
        "transcript",
        "mentions",
        "episode intelligence",
        "industry mapping",
        "external boundary",
        "stock lens",
        "LLM synthesis",
        "research workflow",
        "MCP",
        "review gate",
    ]:
        assert phrase in text

    assert "deterministic" in text
    assert "optional LLM" in text
    assert "Phase 6V" in text
    assert "Phase 6V.1" in text
    assert "reviewed semantic context" in text
    assert "phase-6f-stock-lens-json-plus-reviewed-semantic-summary" in text
    assert "boundary/context consistency" in text
    assert "local fixture" in text
    assert "no live market API" in text


def test_spec_kit_plan_documents_phase_7a_boundary():
    text = _read(SPEC / "plan.md")

    assert "Phase 7A" in text
    assert "Architecture / Spec Kit Stabilization" in text
    assert "docs/spec-only" in text
    assert "no runtime behavior change" in text
    assert "no MCP behavior change" in text
    assert "no LLM call" in text
    assert "no `.env` read" in text
    assert "Phase 6U semantic summary smoke" in text


def test_spec_kit_data_model_separates_evidence_inference_external_and_llm():
    text = _read(SPEC / "data-model.md")

    for phrase in [
        "podcast evidence",
        "timestamp evidence",
        "inferred_from_industry",
        "needs_verification",
        "external verification status",
        "not_requested",
        "not_fetched",
        "data_date=null",
        "stock lens synthesis",
        "phase-6f-stock-lens-json-only",
    ]:
        assert phrase in text

    assert "no investment advice" in text
    assert "no live market API" in text


def test_spec_kit_quickstart_covers_llm_smoke_and_review_gate():
    text = _read(SPEC / "quickstart.md")

    assert "run_research_llm_smoke.py" in text
    assert "review_research_llm_smoke.py" in text
    assert "I understand this may call an external LLM API" in text
    assert "--llm-profile gb10" in text
    assert "--debug-llm-output" in text
    assert "Phase 6T review gate" in text
    assert "no `.env` read" in text
    assert "no live market API" in text
    assert "no investment advice" in text


def test_docs_do_not_treat_local_secrets_as_committable_configuration():
    combined = "\n".join(
        _read(path)
        for path in [
            DOCS / "architecture.md",
            SPEC / "plan.md",
            SPEC / "data-model.md",
            SPEC / "quickstart.md",
        ]
    )

    assert ".env" in combined
    assert "must not be committed" in combined
    assert "API key" in combined
    assert "api_key:" not in combined
    assert "token:" not in combined
    assert "secret:" not in combined


def test_readme_and_roadmap_document_phase_7a():
    readme = _read(ROOT / "README.md")
    roadmap = _read(DOCS / "roadmap.md")

    for text in (readme, roadmap):
        assert "Phase 7A" in text
        assert "Architecture / Spec Kit Stabilization" in text
        assert "docs/spec-only" in text
        assert "Phase 6U semantic summary smoke" in text


def test_readme_and_roadmap_document_phase_7b_spec_kit_bootstrap():
    readme = _read(ROOT / "README.md")
    roadmap = _read(DOCS / "roadmap.md")

    for text in (readme, roadmap):
        assert "Phase 7B" in text
        assert "Official Spec Kit Bootstrap" in text
        assert "specify init" in text
        assert ".specify" in text
        assert ".agents/skills" in text
        assert "AGENTS.md" in text


def test_phase_7c_documents_constitution_and_workflow_alignment():
    combined = "\n".join(
        _read(path)
        for path in [
            ROOT / "README.md",
            DOCS / "roadmap.md",
            DOCS / "architecture.md",
            SPEC / "plan.md",
        ]
    )

    for phrase in [
        "Phase 7C",
        "Spec Kit Constitution + Workflow Alignment",
        "constitution",
        "$speckit-clarify",
        "$speckit-checklist",
        "$speckit-analyze",
        "$speckit-converge",
        "$speckit-taskstoissues",
        "full Spec Kit flow",
        "no runtime behavior change",
        "no `.env` read",
        "no live market API",
        "no investment advice",
    ]:
        assert phrase in combined


def test_phase_7d_documents_existing_capability_backfill():
    combined = "\n".join(
        _read(path)
        for path in [
            ROOT / "README.md",
            DOCS / "roadmap.md",
            DOCS / "architecture.md",
            SPEC / "plan.md",
        ]
    )

    for phrase in [
        "Phase 7D",
        "Spec Kit Backfill via Full Workflow",
        "capability-group backfill",
        "specs/README.md",
        "002-ingestion-transcript-core",
        "006-llm-safety-synthesis-smoke-review",
        "full Spec Kit flow",
        "$speckit-clarify",
        "$speckit-analyze",
        "$speckit-converge",
        "no runtime behavior change",
        "no `.env` read",
        "no live market API",
        "no investment advice",
    ]:
        assert phrase in combined


def test_phase_7d1_documents_active_feature_guidance():
    combined = "\n".join(
        _read(path)
        for path in [
            ROOT / "README.md",
            DOCS / "roadmap.md",
            DOCS / "architecture.md",
            SPEC / "plan.md",
        ]
    )

    for phrase in [
        "Phase 7D.1",
        "Spec Kit Active Feature Guidance",
        "Spec Kit command usability",
        "active feature",
        "SPECIFY_FEATURE_DIRECTORY",
        ".specify/feature.json",
        "specs/<feature>",
        "no runtime behavior change",
        "no `.env` read",
        "no live market API",
        "no investment advice",
        "Phase 6U semantic summary smoke",
    ]:
        assert phrase in combined
