from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/052-learning-workflow-advance"


def test_spec052_package_traceability():
    for name in ["spec.md", "plan.md", "tasks.md", "research.md", "data-model.md", "contracts/advance.md", "quickstart.md", "checklists/requirements.md", "checklists/safety.md", "workflow-record.md"]:
        assert (PACKAGE / name).is_file(), name
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    assert set(re.findall(r"FR-\d{3}", spec)) <= set(re.findall(r"FR-\d{3}", tasks))
    for phrase in ["single action", "metadata-only", "Tools1-31", "no automatic repair"]:
        assert phrase.casefold() in spec.casefold()


def test_authorized038044_completion_bookkeeping():
    old = ROOT / "specs/038-multi-document-study-guide"
    tasks = (old / "tasks.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^- \[x\] T\d{3}", tasks, re.M)) == 32
    assert "**Status**: Implemented" in (ROOT / "specs/044-study-guide-mcp/spec.md").read_text(encoding="utf-8")
    assert (old / "completion-record.md").is_file()


def test_registry052_lifecycle():
    entries = [line for line in (ROOT / "specs/README.md").read_text(encoding="utf-8").splitlines() if line.startswith("- `052-learning-workflow-advance`:")]
    assert len(entries) == 1 and "32" in entries[0]
    assert "Implementation in progress" in entries[0] or "Implemented" in entries[0]
