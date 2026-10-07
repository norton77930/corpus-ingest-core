from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/048-workflow-derivation-lineage"


def test_lineage_planning_artifacts_exist():
    for name in ("spec.md", "plan.md", "research.md", "data-model.md", "contracts/lineage.md", "tasks.md", "quickstart.md", "checklists/requirements.md", "checklists/safety.md", "workflow-record.md", "capability-map.md", "handoff.md"):
        assert (PACKAGE / name).is_file(), name


def test_lineage_scope_distinguishes_history_from_currentness():
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    contract = (PACKAGE / "contracts/lineage.md").read_text(encoding="utf-8")
    for phrase in ("authorized2026-10-04", "no automatic regeneration", "no backfill", "Tool 27"):
        assert phrase in spec
    for phrase in ("metadata_writes", "untracked", "not_evaluated", "custom_context", "same directory publication", "effective allowed_tools"):
        assert phrase in contract
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    assert set(re.findall(r"FR-\d{3}", spec)) <= set(re.findall(r"FR-\d{3}", tasks))
    ids = re.findall(r"^- \[[ xX]\] (T\d{3})", tasks, re.M)
    assert len(ids) >= 12 and ids == [f"T{i:03}" for i in range(1, len(ids) + 1)]
    assert "implementation-log.md" in tasks


def test_lineage_registry_entry_tracks_authorized_scope():
    text = (ROOT / "specs/README.md").read_text(encoding="utf-8")
    entry = next(line for line in text.splitlines() if line.startswith('- `048-workflow-derivation-lineage`'))
    assert ("Implementation in progress" in entry or "Implemented" in entry) and "27" in entry and "28" in entry
