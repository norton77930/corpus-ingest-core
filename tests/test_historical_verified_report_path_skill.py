"""Portable Skill contract for SPEC 023."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "historical-episode-verified-report-path" / "SKILL.md"
EXPECTED_DESCRIPTION = (
    "Human-controlled path for one named historical episode toward a verified "
    "research report—suggest next step, preview, one approved MCP confirm, then stop."
)


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_skill_frontmatter_is_portable() -> None:
    lines = _text().splitlines()
    assert lines[:4] == [
        "---",
        "name: historical-episode-verified-report-path",
        f"description: {EXPECTED_DESCRIPTION}",
        "---",
    ]


def test_skill_protocol_orders_suggest_preview_approve_one_confirm_stop() -> None:
    skill = _text()
    steps = [
        "suggest_historical_verified_report_next_step",
        "run_episode_verified_research_report_workflow",
        "confirm=false",
        "confirm=true",
        "run_corpus_episode_completion_workflow",
        "Do **not** automatically call publish",
        "One confirmed side-effect MCP call per user request, then stop",
    ]
    positions = [skill.index(step) for step in steps]
    assert positions == sorted(positions)


def test_skill_forbids_fallback_and_latest_automation() -> None:
    lowered = _text().casefold()
    assert "do not use cli" in lowered
    assert "terminal" in lowered
    assert "retry" in lowered
    assert "scheduler" in lowered
    assert "do not resolve `latest`" in lowered or "do not resolve latest" in lowered
    assert "investment advice" in lowered
    for marker in ("```", "python ", "powershell", "scripts/"):
        assert marker not in lowered
