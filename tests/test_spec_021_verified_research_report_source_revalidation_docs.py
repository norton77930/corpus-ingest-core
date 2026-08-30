"""Documentation contract for planned SPEC 021 source revalidation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "021-verified-research-report-source-revalidation"


def _read(relative_path: str) -> str:
    return (FEATURE / relative_path).read_text(encoding="utf-8")


def test_spec_021_package_locks_exact_source_revalidation_boundaries() -> None:
    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/verified-research-report-source-revalidation.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / relative_path).is_file(), f"missing {relative_path}"

    spec = _read("spec.md")
    plan = _read("plan.md")
    research = _read("research.md")
    data_model = _read("data-model.md")
    quickstart = _read("quickstart.md")
    tasks = _read("tasks.md")
    contract = _read("contracts/verified-research-report-source-revalidation.md")
    requirements = _read("checklists/requirements.md")
    safety = _read("checklists/safety.md")
    package = "\n".join((spec, plan, research, data_model, quickstart, tasks, contract, requirements, safety))

    for seam in (
        "revalidate_verified_research_report_sources",
        "VerifiedResearchReportSourceRevalidation",
        "revalidate_verified_research_report_sources.py",
        "Tool 18",
        "Tools 1–17 unchanged",
    ):
        assert seam in package

    for boundary in (
        "exact `(podcast_id, episode_ref, lowercase-64-hex source_digest)`",
        "bundle_self_consistency_status",
        "lineage_revalidation_status",
        "source_currentness_status",
        "bundle/currentness separation",
        "hostile paths never dereferenced",
        "read-only/offline/zero-write",
        "append-only",
        "not_evaluated",
        "no raw manifest",
        "absolute paths",
        "stock query",
        "no latest",
        "no DB/FTS/vector/cache",
        "no RSS/HTTP/LLM/.env/download/transcription/remediation",
        "not investment advice",
    ):
        assert boundary in package

    for check in (
        "bundle_self_consistency",
        "assembly_options",
        "current_lineage",
        "published_lineage_match",
        "source_artifact_metadata_match",
        "source_digest_match",
    ):
        assert check in data_model

    for claim in range(9):
        assert f"C{claim}" in tasks
        assert f"C{claim}" in requirements

    assert "**Status**: Implemented" in spec
    assert tasks.count("| PASS-current |") == 9
    assert "| planned |" not in tasks
    assert "TDD" in tasks
    assert "specify → clarify → plan → checklist → tasks → analyze → implement → converge" in tasks
    assert tasks.count("## Final Verification (run exactly once)") == 1
    assert (
        "python -m pytest; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; python -m compileall src scripts; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; git diff --check; exit $LASTEXITCODE"
        in tasks
    )
