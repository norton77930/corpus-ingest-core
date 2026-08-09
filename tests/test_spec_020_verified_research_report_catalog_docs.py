"""Documentation contract for implemented SPEC 020 catalog surfaces."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "020-verified-research-report-catalog"


def _read(relative_path: str) -> str:
    return (FEATURE / relative_path).read_text(encoding="utf-8")


def test_spec_020_catalog_package_locks_the_read_only_contract() -> None:
    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/verified-research-report-catalog.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / relative_path).is_file(), f"missing {relative_path}"

    spec = _read("spec.md")
    plan = _read("plan.md")
    data_model = _read("data-model.md")
    contract = _read("contracts/verified-research-report-catalog.md")
    tasks = _read("tasks.md")
    safety = _read("checklists/safety.md")

    for seam in (
        "list_verified_research_reports",
        "search_verified_research_reports",
        "inspect_verified_research_report",
        "query_verified_research_report_catalog.py",
        "query_verified_research_report_catalog",
    ):
        assert seam in "\n".join((spec, plan, contract, tasks))

    for boundary in (
        "source_currentness_status=not_evaluated",
        "v1-[a-f0-9]{64}",
        "exactly `report.json`, `report.md`, and `manifest.json`",
        "no raw manifest",
        "absolute paths",
        "symlink",
        "junction",
        "no DB/FTS/vector/cache",
        "no RSS/HTTP/LLM/.env/download/transcription/remediation",
        "no latest selector",
        "read-only/offline",
        "REPORT_SCHEMA_VERSION",
        "latest-episode-verified-research-report-v1",
        "16 MiB",
    ):
        assert boundary in "\n".join((spec, data_model, contract, safety))

    assert "**Status**: Implemented" in spec
    assert "Tool 17" in contract
    assert "TDD" in tasks
    assert "C2" in tasks and "C7" in tasks
    assert "- [ ]" not in tasks
    assert "1084 passed, 3 skipped" in tasks


def test_spec_020_user_docs_and_setup_align_with_the_current_catalog_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = (ROOT / "docs" / "mcp-usage.md").read_text(encoding="utf-8")
    setup_docs = "\n".join(
        (ROOT / "docs" / filename).read_text(encoding="utf-8")
        for filename in ("claude-mcp-setup.md", "codex-mcp-setup.md")
    )
    registry = (ROOT / "specs" / "README.md").read_text(encoding="utf-8")

    for text in (readme, usage, setup_docs):
        assert "query_verified_research_report_catalog" in text
        assert "17" in text

    for text in (readme, usage):
        assert "query_verified_research_report_catalog.py" in text
        assert "source_currentness_status=not_evaluated" in text
        assert "no raw manifest" in text
        assert "no DB/FTS/vector/cache" in text
        assert "no RSS/HTTP/LLM/.env/download/transcription/remediation" in text
        assert "no latest selector" in text
        assert 'search "EP672" --podcast-id gooaye' in text
        assert 'search "台積電"' not in text

    assert "020-verified-research-report-catalog" in registry
    assert "query_verified_research_report_catalog.py" in registry


def test_spec_020_implemented_docs_and_handoff_keep_current_contracts() -> None:
    spec = _read("spec.md")
    plan = _read("plan.md")
    quickstart = _read("quickstart.md")
    requirements = _read("checklists/requirements.md")
    handoff = (ROOT / "docs" / "agent-handoff.md").read_text(encoding="utf-8")

    implemented_docs = "\n".join((spec, plan, quickstart, requirements))
    assert "future implementation" not in implemented_docs.casefold()
    assert "not yet implemented" not in implemented_docs.casefold()
    assert 'search "EP650" --podcast-id gooaye --limit 50' in quickstart
    assert 'search "gooaye EP650"' not in quickstart
    assert "Do not change runtime/CLI/MCP in this specification-delivery phase." not in spec
    assert "This package documents a future implementation" not in plan
    # 025 doc-count consolidation: the stale "恰好 18 個" claims were synced to
    # the live registry; the registry-derived checker
    # (tests/test_docs_registry_count_consistency.py) now owns count drift.
    assert "stdio-only MCP server（目前恰好 21 個 reviewed tools）" in handoff
    assert "stdio-only MCP server（21 tools）" in handoff
    assert "恰好 18 個 reviewed tools" not in handoff
    assert "MCP tool 16 + portable Skill" not in handoff
    assert "historically MCP Tool 16" in handoff
