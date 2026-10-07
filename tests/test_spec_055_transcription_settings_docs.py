"""Keep the approved configuration/compatibility scope in the delivery docs."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/055-source-preparation-transcription-settings"


def test_spec_package_has_design_contracts_and_complete_task_coverage():
    for name in ("spec.md", "plan.md", "research.md", "data-model.md", "quickstart.md",
                 "tasks.md", "implementation-log.md", "contracts/mcp.md", "contracts/worker.md",
                 "checklists/requirements.md", "checklists/safety.md"):
        assert (PACKAGE / name).is_file(), name
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    assert set(re.findall(r"FR-\d{3}|SC-\d{3}", spec)) <= set(re.findall(r"FR-\d{3}|SC-\d{3}", tasks))
    identifiers = re.findall(r"^- \[[ x]\] (T\d{3})", tasks, re.MULTILINE)
    assert identifiers and len(identifiers) == len(set(identifiers))
    for name in ("spec.md", "plan.md", "tasks.md"):
        assert "NEEDS CLARIFICATION" not in (PACKAGE / name).read_text(encoding="utf-8")


def test_package_preserves_history_and_limits_and_is_registered():
    contract = (PACKAGE / "contracts/mcp.md").read_text(encoding="utf-8")
    for term in ("transcription", "actual_transcription", "null", "legacy", "34", "no silent fallback"):
        assert term in contract
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    for term in ("historical jobs", "no automatic regeneration", "No LLM", "manual cache"):
        assert term in spec
    assert PACKAGE.name in (ROOT / "specs/README.md").read_text(encoding="utf-8")
