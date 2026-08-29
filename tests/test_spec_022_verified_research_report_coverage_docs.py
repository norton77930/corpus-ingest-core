"""Documentation contract for SPEC 022 verified research report coverage index."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "022-verified-research-report-coverage-index"


def _read(relative_path: str) -> str:
    return (FEATURE / relative_path).read_text(encoding="utf-8")


def test_spec_022_package_locks_coverage_contract() -> None:
    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/verified-research-report-coverage.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / relative_path).is_file(), f"missing {relative_path}"

    package = "\n".join(
        _read(path)
        for path in (
            "spec.md",
            "plan.md",
            "data-model.md",
            "contracts/verified-research-report-coverage.md",
            "tasks.md",
            "checklists/safety.md",
        )
    )
    for phrase in (
        "list_verified_research_report_coverage",
        "query_verified_research_report_coverage.py",
        "query_verified_research_report_coverage",
        "Tool 19",
        "has_bundle",
        "source_digests",
        "read-only/offline",
        "zero-write",
        "no DB/FTS/vector/cache",
        "not_investment_advice",
        "Tools 1–18",
    ):
        assert phrase in package


def test_spec_022_status_tracks_implementation() -> None:
    spec = _read("spec.md")
    tasks = _read("tasks.md")
    # During implementation this flips to Implemented and tasks close.
    assert "**Status**:" in spec
    assert "C7" in tasks
