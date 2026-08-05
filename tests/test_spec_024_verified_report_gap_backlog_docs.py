"""Documentation contract for SPEC 024."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "024-verified-report-gap-backlog"


def test_spec_024_package_locks_b_lite_contract() -> None:
    for rel in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/verified-report-gap-backlog.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / rel).is_file(), rel
    text = "\n".join(
        (FEATURE / n).read_text(encoding="utf-8")
        for n in ("spec.md", "plan.md", "contracts/verified-report-gap-backlog.md", "checklists/safety.md")
    )
    for phrase in (
        "list_verified_report_gap_backlog",
        "B-lite",
        "has_bundle=False",
        "Tool 21",
        "zero-write",
        "not_investment_advice",
        "023",
    ):
        assert phrase in text
