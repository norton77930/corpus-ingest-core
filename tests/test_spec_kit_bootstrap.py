from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_spec_kit_scaffold_exists():
    assert (ROOT / ".specify" / "memory" / "constitution.md").exists()
    assert (ROOT / ".agents" / "skills").exists()

    for skill_name in [
        "speckit-analyze",
        "speckit-checklist",
        "speckit-clarify",
        "speckit-constitution",
        "speckit-converge",
        "speckit-implement",
        "speckit-specify",
        "speckit-plan",
        "speckit-tasks",
        "speckit-taskstoissues",
    ]:
        assert (ROOT / ".agents" / "skills" / skill_name / "SKILL.md").exists()


def test_agents_md_documents_spec_kit_and_project_rules():
    agents = _read(ROOT / "AGENTS.md")

    for phrase in [
        "Spec Kit",
        "Codex skills",
        "$speckit-constitution",
        "$speckit-specify",
        "$speckit-clarify",
        "$speckit-plan",
        "$speckit-checklist",
        "$speckit-tasks",
        "$speckit-analyze",
        "$speckit-implement",
        "$speckit-converge",
        "$speckit-taskstoissues",
        ".env",
        "must not be read",
        "must not be committed",
        "no live market API",
        "no investment advice",
        "python -m pytest",
        "python -m compileall src scripts",
    ]:
        assert phrase in agents


def test_existing_gooaye_spec_files_are_preserved():
    spec_dir = ROOT / "specs" / "001-gooaye-research-system"

    for filename in ["spec.md", "plan.md", "data-model.md", "quickstart.md"]:
        path = spec_dir / filename
        assert path.exists()
        assert "Gooaye" in _read(path) or "gooaye" in _read(path)
