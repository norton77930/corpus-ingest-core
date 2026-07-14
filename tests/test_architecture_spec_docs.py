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


def test_c1_docs_drift_remediation_current_status_and_batch_traceability():
    roadmap = _read(DOCS / "roadmap.md")
    mvp = _read(DOCS / "mvp-requirements.md")
    specs_readme = _read(ROOT / "specs" / "README.md")

    # roadmap gains an authoritative current-status/next section and records the
    # post-6V.1 Batch 3A/3B hardening; the earlier Phase 7A/7C/7D.1 "6U is next"
    # pointers are historical planning notes because 6U/6U.1 已完成.
    assert "目前狀態與下一步" in roadmap
    assert "Batch 3A" in roadmap
    assert "Batch 3B" in roadmap
    assert "6U/6U.1 已完成" in roadmap

    # mvp-requirements is labelled a Phase 1-4A historical snapshot.
    assert "歷史快照" in mvp

    # specs registry maps the Batch guard tests to their safety boundaries.
    assert "Batch Guard Tests" in specs_readme


def test_corpus_runtime_lifecycle_status_matches_registry_and_roadmap():
    for package in [
        "010-corpus-remediation-runner",
        "011-corpus-local-transcription-runner",
        "012-corpus-audio-download-runner",
        "013-corpus-episode-intake-bootstrap",
        "014-corpus-fresh-episode-workflow-runner",
        "015-corpus-semantic-remediation-runner",
        "016-corpus-episode-completion-workflow-runner",
    ]:
        spec = _read(ROOT / "specs" / package / "spec.md")
        assert "**Status**: Implemented" in spec

    roadmap = _read(DOCS / "roadmap.md")
    assert "015-corpus-semantic-remediation-runner" in roadmap
    assert "Latest implemented corpus package is **016-corpus-episode-completion-workflow-runner**" in roadmap
    assert "next unused feature package number is **017**" in roadmap

def test_014_stabilization_docs_define_strict_zero_file_dry_run():
    feature = ROOT / "specs" / "014-corpus-fresh-episode-workflow-runner"
    spec = _read(feature / "spec.md")
    package_docs = "\n".join(
        _read(path)
        for path in [
            feature / "spec.md",
            feature / "plan.md",
            feature / "research.md",
            feature / "data-model.md",
            feature / "contracts" / "corpus-episode-workflow-runner.md",
            feature / "quickstart.md",
            feature / "checklists" / "safety.md",
        ]
    )

    assert "creates, modifies, or deletes zero files" in spec
    for phrase in [
        "in-memory corpus snapshot",
        "configured podcast RSS feed",
        "source_persisted=False",
        "standalone 010-012",
    ]:
        assert phrase in package_docs

    direct_docs = [
        _read(ROOT / "README.md"),
        _read(ROOT / "specs" / "README.md"),
        _read(DOCS / "architecture.md"),
        _read(DOCS / "verification-matrix.md"),
    ]
    assert all("zero-file" in text for text in direct_docs)
    matrix = direct_docs[-1]
    assert "tree manifest" in matrix
    assert "writer call count" in matrix
    assert "one shared snapshot" in matrix
    assert "exact 12 MCP tools" in matrix

def test_015_semantic_remediation_docs_and_registry_contract():
    feature = ROOT / "specs" / "015-corpus-semantic-remediation-runner"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    registry = (ROOT / "specs" / "README.md").read_text(encoding="utf-8")
    verification = (ROOT / "docs" / "verification-matrix.md").read_text(
        encoding="utf-8"
    )
    handoff = (ROOT / "docs" / "agent-handoff.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/corpus-semantic-remediation.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (feature / relative_path).is_file()

    assert "run_corpus_semantic_remediation" in readme
    assert "run_corpus_semantic_remediation.py" in readme
    assert "strict zero-file" in readme
    assert "semantic_summary" in readme
    assert "semantic_review" in readme
    assert "corpus-semantic-remediation-run.json" in readme
    assert "corpus_semantic_remediation_runner.py" in architecture
    assert "exactly one" in architecture
    assert "does not call 010 or 014" in architecture
    assert "015-corpus-semantic-remediation-runner" in registry
    assert "corpus_semantic_remediation_runner.py" in registry
    assert "run_corpus_semantic_remediation.py" in registry
    assert "test_corpus_semantic_remediation_runner.py" in registry
    assert "corpus semantic remediation runner" in verification
    assert "test_corpus_semantic_remediation_runner.py" in verification
    assert "015-corpus-semantic-remediation-runner" in handoff
    assert "015-corpus-semantic-remediation-runner" in roadmap
    assert "016" in roadmap
    assert "specs/016-corpus-episode-completion-workflow-runner/plan.md" in agents


def test_016_completion_workflow_docs_and_agent_surface_contract():
    feature = ROOT / "specs" / "016-corpus-episode-completion-workflow-runner"
    readme = _read(ROOT / "README.md")
    architecture = _read(DOCS / "architecture.md")
    handoff = _read(DOCS / "agent-handoff.md")
    roadmap = _read(DOCS / "roadmap.md")
    registry = _read(ROOT / "specs" / "README.md")
    verification = _read(DOCS / "verification-matrix.md")
    mcp_usage = _read(DOCS / "mcp-usage.md")
    agents = _read(ROOT / "AGENTS.md")

    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/corpus-episode-completion-workflow.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (feature / relative_path).is_file()

    assert "run_corpus_episode_completion_workflow" in readme
    assert "run_corpus_episode_completion_workflow.py" in readme
    assert "corpus-episode-completion-workflow-run.json" in readme
    assert "strict zero-file" in readme
    assert "corpus_episode_completion_workflow_runner.py" in architecture
    assert "one explicit action" in architecture
    assert "exact 13" in architecture
    assert "016-corpus-episode-completion-workflow-runner" in handoff
    assert "13 reviewed tools" in handoff
    assert "016-corpus-episode-completion-workflow-runner" in roadmap
    assert "next unused feature package number is **017**" in roadmap
    assert "016-corpus-episode-completion-workflow-runner" in registry
    assert "run_corpus_episode_completion_workflow.py" in registry
    assert "run_corpus_episode_completion_workflow" in registry
    assert "test_corpus_episode_completion_workflow_runner.py" in verification
    assert "test_corpus_episode_completion_skill.py" in verification
    assert "run_corpus_episode_completion_workflow" in mcp_usage
    assert "corpus-episode-completion" in mcp_usage
    assert "specs/016-corpus-episode-completion-workflow-runner/plan.md" in agents
