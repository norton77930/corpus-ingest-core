"""SPEC054 design contracts; these checks do not prove runtime implementation."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "specs/054-source-preparation-jobs"


def test_spec054_artifacts_are_complete_without_template_residue():
    paths = ["spec.md", "plan.md", "research.md", "data-model.md", "contracts/mcp.md",
             "contracts/worker.md", "quickstart.md", "tasks.md",
             "checklists/requirements.md", "checklists/safety.md", "workflow-record.md"]
    for name in paths:
        path = PACKAGE / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        for marker in ["[FEATURE NAME]", "[DATE]", "NEEDS CLARIFICATION", "ACTION REQUIRED", "TBD"]:
            assert marker not in text, (name, marker)


def test_spec054_requirements_and_success_criteria_have_tasks():
    spec = (PACKAGE / "spec.md").read_text(encoding="utf-8")
    tasks = (PACKAGE / "tasks.md").read_text(encoding="utf-8")
    requirements = set(re.findall(r"FR-\d{3}", spec))
    criteria = set(re.findall(r"SC-\d{3}", spec))
    assert len(requirements) >= 12 and len(criteria) >= 5
    assert requirements <= set(re.findall(r"FR-\d{3}", tasks))
    assert criteria <= set(re.findall(r"SC-\d{3}", tasks))
    task_ids = re.findall(r"^- \[[ x]\] (T\d{3})", tasks, re.M)
    assert len(task_ids) == len(set(task_ids))


def test_spec054_separates_transcript_readiness_and_background_uncertainty():
    model = (PACKAGE / "data-model.md").read_text(encoding="utf-8")
    contract = (PACKAGE / "contracts/mcp.md").read_text(encoding="utf-8")
    worker = (PACKAGE / "contracts/worker.md").read_text(encoding="utf-8")
    for state in ["queued", "downloading", "transcribing", "validating", "transcript_ready", "failed", "attention_required"]:
        assert state in model, state
    for invariant in ["read-only", "expected_plan_id", "confirm=false", "no LLM", "manual cache"]:
        assert invariant.casefold() in contract.casefold(), invariant
    assert "study_guide_ready=false" in model
    assert "no automatic retry" in worker and "one active source" in worker


def test_spec054_runtime_and_selector_match_implemented_scope():
    registry = (ROOT / "specs/README.md").read_text(encoding="utf-8")
    agent = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "054-source-preparation-jobs" in registry and "054-source-preparation-jobs/plan.md" in agent
    assert "Implemented" in (PACKAGE / "spec.md").read_text(encoding="utf-8")
    selected=next(line for line in registry.splitlines() if line.startswith("- 054-source-preparation-jobs:"))
    assert "Implemented" in selected and "34" in selected
    assert (ROOT/"src/corpus_ingest_core/source_preparation_worker.py").is_file()
    assert (ROOT/".agents/skills/source-preparation/SKILL.md").is_file()
    assert "worker_host_incompatible" in (PACKAGE/"contracts/mcp.md").read_text(encoding="utf-8")
