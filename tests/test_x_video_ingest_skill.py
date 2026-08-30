from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".agents" / "skills" / "x-video-ingest" / "SKILL.md"
EXPECTED_DESCRIPTION = "Safely preview and ingest one X post video into the corpus with one explicit human approval."


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def test_x_video_skill_has_only_portable_required_frontmatter():
    lines = _skill_text().splitlines()

    assert lines[:4] == [
        "---",
        "name: x-video-ingest",
        f"description: {EXPECTED_DESCRIPTION}",
        "---",
    ]


def test_x_video_skill_requires_the_ordered_human_control_protocol():
    skill = _skill_text()
    required_steps = [
        "`ingest_x_video` with the exact `url` the user gave and `confirm=false`",
        "zero-write but not zero-network",
        "Ask one explicit approval question and wait for the answer",
        "Treat absent, ambiguous, conditional, or negative replies as no approval",
        "the same `url` and `confirm=true`, exactly once",
        "no `api_cost_ack`",
        "Report the bounded result and stop",
    ]

    positions = [skill.index(step) for step in required_steps]
    assert positions == sorted(positions)


def test_x_video_skill_never_uses_an_automatic_or_local_fallback_path():
    skill = _skill_text()
    lowered = skill.casefold()

    assert "do not start another preview or action unless the user makes a new request" in lowered
    assert (
        "do not use a terminal, cli, another side-effect tool, cron/scheduler, retry, "
        "or autonomous loop as a fallback" in lowered
    )
    for client_specific_or_command_marker in (
        "codex-only",
        "openclaw-only",
        "hermes-only",
        "```",
        "python ",
        "powershell",
        "scripts/",
    ):
        assert client_specific_or_command_marker not in lowered
