from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"specs/053-learning-workflow-advance-skill"


def test_spec053_traceability_and_artifacts():
    for name in ["spec.md","plan.md","tasks.md","research.md","data-model.md","contracts/protocol.md","quickstart.md","checklists/requirements.md","checklists/safety.md","workflow-record.md"]:
        assert (PKG/name).is_file(),name
    spec=(PKG/"spec.md").read_text(encoding="utf-8")
    tasks=(PKG/"tasks.md").read_text(encoding="utf-8")
    assert set(re.findall(r"FR-\d{3}",spec))<=set(re.findall(r"FR-\d{3}",tasks))


def test_spec053_registry_and_operator_docs():
    registry=(ROOT/"specs/README.md").read_text(encoding="utf-8")
    assert "053-learning-workflow-advance-skill" in registry
    for relative in [".agents/skills/README.md","docs/mcp-usage.md","docs/verification-matrix.md"]:
        text=(ROOT/relative).read_text(encoding="utf-8")
        assert "learning-workflow-advance" in text,relative
        assert "offline" in text.lower()
