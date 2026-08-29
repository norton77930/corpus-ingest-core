from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"

CAPABILITY_PACKAGES = [
    "002-ingestion-transcript-core",
    "003-metadata-search-mcp-core",
    "004-deterministic-research-artifacts",
    "005-research-workflow-orchestration",
    "006-llm-safety-synthesis-smoke-review",
    "007-spec-kit-governance",
]

REQUIRED_FILES = [
    "spec.md",
    "plan.md",
    "data-model.md",
    "quickstart.md",
    "tasks.md",
    "checklists/requirements.md",
]

FORBIDDEN_TEMPLATE_RESIDUE = [
    "[FEATURE NAME]",
    "[FEATURE]",
    "[DATE]",
    "[###-feature-name]",
    "[###-feature]",
    "[CHECKLIST TYPE]",
    "NEEDS CLARIFICATION",
    "ACTION REQUIRED",
    "SAMPLE TASKS",
    "First checklist item",
    "Another category item",
    "Create project structure per implementation plan",
    "TBD",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_spec_registry_lists_all_backfilled_capability_packages():
    registry = _read(SPECS / "README.md")

    assert "Phase 7D" in registry
    assert "Spec Kit Backfill via Full Workflow" in registry
    assert "001-gooaye-research-system" in registry
    assert "umbrella product spec" in registry
    for package in CAPABILITY_PACKAGES:
        assert package in registry

    for phrase in [
        "roadmap phase",
        "core modules",
        "CLI/scripts",
        "tests",
        "deterministic",
        "optional LLM",
        "local fixture",
        "MCP exposed",
        "eval/review only",
        "constitution reviewed, no amendment",
        "taskstoissues: not used",
    ]:
        assert phrase in registry


def test_registry_documents_official_active_feature_selection_for_backfilled_specs():
    registry = _read(SPECS / "README.md")

    for phrase in [
        "specs/<feature>",
        ".specify",
        "scaffold, memory, templates, scripts, integration, and workflow metadata",
        "not the feature spec directory",
        "checklists/requirements.md",
        "SPECIFY_FEATURE_DIRECTORY",
        "$env:SPECIFY_FEATURE_DIRECTORY=\"specs/003-metadata-search-mcp-core\"",
        ".specify/feature.json",
        "local-only",
        "gitignored",
        "untracked",
        "check-prerequisites.ps1",
        "backfilled packages do not pin a single active feature by default",
    ]:
        assert phrase in registry


def test_each_backfilled_package_has_required_spec_kit_artifacts():
    for package in CAPABILITY_PACKAGES:
        package_dir = SPECS / package
        for relative_path in REQUIRED_FILES:
            path = package_dir / relative_path
            assert path.exists(), f"{package}/{relative_path} is missing"

        combined = "\n".join(_read(package_dir / relative_path) for relative_path in REQUIRED_FILES)
        assert "Status: Backfilled / As-built" in combined
        assert "Spec Kit workflow record" in combined
        for step in [
            "$speckit-constitution",
            "$speckit-specify",
            "$speckit-clarify",
            "$speckit-plan",
            "$speckit-checklist",
            "$speckit-tasks",
            "$speckit-analyze",
            "$speckit-implement",
            "$speckit-converge",
        ]:
            assert step in combined

        for forbidden in FORBIDDEN_TEMPLATE_RESIDUE:
            assert forbidden not in combined, f"{package} contains template residue: {forbidden}"


def test_registry_maps_existing_code_scripts_and_tests_to_packages():
    registry = _read(SPECS / "README.md")

    for phrase in [
        "feed_reader.py",
        "downloader.py",
        "transcriber.py",
        "validator.py",
        "entity_extractor.py",
        "cache.py",
        "search.py",
        "mcp_server.py",
        "episode_intelligence.py",
        "industry_mapping.py",
        "external_data_boundary.py",
        "external_data_verification.py",
        "research_workflow.py",
        "semantic_summarizer.py",
        "stock_lens_synthesis.py",
        "research_llm_smoke_review.py",
        "download_episode.py",
        "run_research_workflow.py",
        "run_research_llm_smoke.py",
        "test_feed_reader.py",
        "test_mcp_server.py",
        "test_stock_lens_synthesis.py",
        "test_spec_kit_constitution.py",
    ]:
        assert phrase in registry


def test_safety_boundaries_are_recorded_in_relevant_backfill_packages():
    safety_text = "\n".join(
        _read(SPECS / package / relative_path)
        for package in CAPABILITY_PACKAGES
        for relative_path in REQUIRED_FILES
    )

    for phrase in [
        "dry-run",
        "exact `api_cost_ack`",
        "secret boundary",
        "evidence separation",
        "external status",
        "no live market API",
        "no investment advice",
        "manual cache rebuild",
        ".env",
        "phase-6f-stock-lens-json-only",
        "not_fetched",
        "not_requested",
    ]:
        assert phrase in safety_text


def test_umbrella_spec_is_preserved_and_links_to_backfill_registry():
    umbrella = SPECS / "001-gooaye-research-system"
    for relative_path in ["spec.md", "plan.md", "data-model.md", "quickstart.md"]:
        assert (umbrella / relative_path).exists()

    plan = _read(umbrella / "plan.md")
    assert "Phase 7D" in plan
    assert "capability-group backfill" in plan
    assert "specs/README.md" in plan
