from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".agents" / "skills" / "corpus-latest-episode-processing" / "SKILL.md"
EXPECTED_DESCRIPTION = (
    "Process one configured podcast's latest deterministic workflow once with "
    "confirmed MCP execution after an explicit request."
)


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def test_latest_episode_processing_skill_has_portable_frontmatter():
    lines = _skill_text().splitlines()

    assert lines[:4] == [
        "---",
        "name: corpus-latest-episode-processing",
        f"description: {EXPECTED_DESCRIPTION}",
        "---",
    ]


def test_latest_episode_processing_skill_uses_one_confirmed_mcp_call_then_stops():
    skill = _skill_text()
    required_steps = [
        "Map the spoken podcast name to a configured podcast id",
        "Acknowledge once that the explicit natural-language request is a one-time execution authorization",
        "Call `run_corpus_latest_episode_deterministic_workflow` exactly once with `confirm=true`",
        "Report the metadata-only result once and stop",
    ]

    positions = [skill.index(step) for step in required_steps]
    assert positions == sorted(positions)
    assert "MCP tool itself remains dry-run by default" in skill
    assert "Do not call with `confirm=false` before the confirmed call" in skill


def test_latest_episode_processing_skill_forbids_fallback_and_semantic_work():
    lowered = _skill_text().casefold()

    for required in (
        "do not call this tool more than once",
        "do not use a terminal, cli, another side-effect tool, cron/scheduler, retry, batch, cache rebuild, or autonomous loop as a fallback",
        "do not invoke semantic summary or semantic review",
        "do not resolve a new latest episode during the same request",
    ):
        assert required in lowered
    for command_marker in ("```", "python ", "powershell", "scripts/"):
        assert command_marker not in lowered
