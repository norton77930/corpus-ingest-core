"""Documentation contract for SPEC 023."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "023-historical-episode-verified-report-path"


def test_spec_023_package_exists_and_locks_path_contract() -> None:
    for relative in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/historical-verified-report-path.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / relative).is_file(), relative

    package = "\n".join(
        (FEATURE / name).read_text(encoding="utf-8")
        for name in (
            "spec.md",
            "plan.md",
            "contracts/historical-verified-report-path.md",
            "checklists/safety.md",
        )
    )
    for phrase in (
        "suggest_historical_verified_report_next_step",
        "Tool 20",
        "confirm=false",
        "one",
        "historical-episode-verified-report-path",
        "zero-write",
        "not_investment_advice",
    ):
        assert phrase in package
