"""SPEC060 planning integrity; does not certify runtime or Hermes behavior."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs/060-source-learning-host-reliability"


def test_spec060_has_complete_design_and_requirement_task_coverage():
    for name in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "quickstart.md",
        "tasks.md",
        "contracts/learning.md",
        "checklists/requirements.md",
        "checklists/reliability.md",
    ):
        text = (FEATURE / name).read_text(encoding="utf-8")
        assert not re.search(r"\[NEEDS CLARIFICATION|\bTBD\b|\bTODO\b", text), name
    spec = (FEATURE / "spec.md").read_text(encoding="utf-8")
    tasks = (FEATURE / "tasks.md").read_text(encoding="utf-8")
    requirements = set(re.findall(r"^- \*\*(FR-\d{3})\*\*", spec, re.MULTILINE))
    assert requirements
    rows = dict(re.findall(r"^\| (FR-\d{3}) \| ([^\n]+) \|$", tasks, re.MULTILINE))
    assert requirements == set(rows)
    ids = re.findall(r"^- \[[ xX]\] (T\d{3}) ", tasks, re.MULTILINE)
    assert ids == [f"T{i:03}" for i in range(1, len(ids) + 1)] and ids
    for requirement, task_refs in rows.items():
        assert re.findall(r"T\d{3}", task_refs), requirement
        assert set(re.findall(r"T\d{3}", task_refs)) <= set(ids), requirement


def test_spec060_discovery_and_validation_distinguish_host_acceptance():
    for path in ("AGENTS.md", "specs/README.md"):
        assert "060-source-learning-host-reliability" in (ROOT / path).read_text(encoding="utf-8")
    contract = (FEATURE / "contracts/learning.md").read_text(encoding="utf-8")
    for term in (
        "expected_source_version",
        "legacy",
        "text_offset",
        "57",
        "last successful",
        "delegate_task",
        "confirm=false",
        "AI 補充",
    ):
        assert term in contract, term
    guide = (FEATURE / "quickstart.md").read_text(encoding="utf-8")
    for term in (
        "scope_complete=true",
        "selected_segments",
        "Hermes",
        "pytest -q",
        "compileall",
        "git diff --check",
        "pending",
        "does not prove",
    ):
        assert term in guide, term
