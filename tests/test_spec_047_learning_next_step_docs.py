from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/047-learning-workflow-next-step"


def test_planned_package_has_design_and_handoff():
    for name in ("spec.md", "plan.md", "research.md", "data-model.md", "contracts/next-step.md", "quickstart.md", "tasks.md", "checklists/requirements.md", "checklists/safety.md", "handoff.md", "workflow-record.md", "capability-map.md"):
        assert (PACKAGE / name).is_file(), name


def test_proposal_preserves_read_only_and_freshness_boundaries():
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    for requirement in ("confirm=False", "force=False", "source_currentness=not_evaluated", "no automatic chaining"):
        assert requirement.casefold() in spec.casefold()
    contract = (PACKAGE / "contracts/next-step.md").read_text(encoding="utf-8")
    for field in ("action_available", "complete", "blocked", "requires_api_cost_ack", "lecture_prerequisite_failed", "derivation_prerequisite_failed"):
        assert field in contract


def test_tasks_cover_every_requirement_with_sequential_ids():
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    requirements = set(re.findall(r"FR-\d{3}", spec))
    assert requirements
    assert requirements <= set(re.findall(r"FR-\d{3}", tasks))
    ids = re.findall(r"^- \[[ xX]\] (T\d{3})", tasks, re.M)
    assert ids == [f"T{i:03}" for i in range(1, len(ids) + 1)]
    assert len(ids) >= 10
    if "**Status**: Implemented" in spec:
        assert not re.search(r"^- \[ \] T", tasks, re.M)


def test_registry_names_append_only_query_scope():
    registry = (ROOT / "specs/README.md").read_text(encoding="utf-8")
    entry = next(line for line in registry.splitlines() if line.startswith('- `047-learning-workflow-next-step`'))
    assert "Tool 27" in entry and "Tools 1-26" in entry and "read-query" in entry
