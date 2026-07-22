"""Portable Skill contract for SPEC 019."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "episode-verified-research-report" / "SKILL.md"


def test_skill_protocol_is_preview_approve_one_confirm_stop():
    text = SKILL.read_text(encoding="utf-8")
    assert "run_episode_verified_research_report_workflow" in text
    assert "confirm=false" in text
    assert "confirm=true" in text
    assert "api_cost_ack" in text
    assert "no" in text.casefold() and "api_cost_ack" in text
    assert "Do not use CLI" in text or "Do not use CLI or a terminal fallback" in text
    assert "latest" in text.casefold()
