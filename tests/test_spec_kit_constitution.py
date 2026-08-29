from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECIFY = ROOT / ".specify"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_constitution_is_project_specific_and_versioned():
    text = _read(SPECIFY / "memory" / "constitution.md")

    assert "Podcast Ingestion Core / Gooaye Research System Constitution" in text
    assert "Sync Impact Report" in text
    assert "Version change: template -> 1.0.0" in text
    assert "**Version**: 1.0.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-06-30" in text
    assert not re.search(r"\[[A-Z0-9_]+\]", text)


def test_constitution_captures_research_and_llm_safety_principles():
    text = _read(SPECIFY / "memory" / "constitution.md")

    for phrase in [
        "Local Artifacts and Evidence Traceability",
        "Thin Interfaces over Thick Core",
        "Dry-Run First Side Effects",
        "LLM Opt-In and Secret Boundary",
        "Evidence, Inference, and External Status Separation",
        "No Investment Advice",
        "Manual Cache Rebuild",
        "TDD and Verification Gates",
        "exact `api_cost_ack`",
        ".env",
        "no live market API",
        "podcast evidence",
        "inferred_from_industry",
        "not_fetched",
        "python -m pytest",
        "python -m compileall src scripts",
    ]:
        assert phrase in text


def test_constitution_documents_full_spec_kit_workflow():
    text = _read(SPECIFY / "memory" / "constitution.md")

    for phrase in [
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
    ]:
        assert phrase in text


def test_spec_kit_templates_are_aligned_with_constitution_gates():
    combined = "\n".join(
        _read(path)
        for path in [
            SPECIFY / "templates" / "plan-template.md",
            SPECIFY / "templates" / "spec-template.md",
            SPECIFY / "templates" / "tasks-template.md",
            SPECIFY / "templates" / "checklist-template.md",
        ]
    )

    for phrase in [
        "dry-run",
        "exact `api_cost_ack`",
        "secret boundary",
        "external-data boundary",
        "investment safety",
        "evidence separation",
        "podcast evidence",
        "inference",
        "external status",
        ".env",
        "targeted tests",
        "review gate",
    ]:
        assert phrase in combined
