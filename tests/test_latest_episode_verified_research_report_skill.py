"""SPEC 018 thin CLI, MCP, and portable Skill contracts."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_cli_defaults_to_preview_forwards_only_bounded_inputs(monkeypatch, capsys):
    from scripts import run_latest_episode_verified_research_report_workflow as cli

    captured = {}
    monkeypatch.setattr(
        cli,
        "run_latest_episode_verified_research_report_workflow",
        lambda podcast_id, **kwargs: captured.update({"podcast_id": podcast_id, **kwargs})
        or SimpleNamespace(outcome="dry_run"),
    )
    monkeypatch.setattr(cli, "result_to_dict", lambda result: {"outcome": result.outcome})

    assert cli.main(["--podcast", "gooaye"]) == 0
    assert json.loads(capsys.readouterr().out) == {"outcome": "dry_run"}
    assert captured == {
        "podcast_id": "gooaye", "confirm": False, "expected_episode_ref": None,
        "api_cost_ack": "", "stock_query": None, "include_fixture_verification": False,
        "transcription_model": None, "transcription_device": "cpu",
        "transcription_compute_type": "int8", "transcription_vad_filter": False,
        "semantic_provider": "openai-compatible", "semantic_model": None,
        "semantic_chunk_seconds": 600, "semantic_max_segments_per_chunk": 120,
    }
    options = {option for action in cli.build_parser()._actions for option in action.option_strings}
    for forbidden in ("--force", "--allow-partial", "--retry", "--schedule", "--output-path", "--base-url", "--env-file"):
        assert forbidden not in options


def test_cli_rejects_bad_confirmed_ack_before_core(monkeypatch, capsys):
    from scripts import run_latest_episode_verified_research_report_workflow as cli

    monkeypatch.setattr(
        cli,
        "run_latest_episode_verified_research_report_workflow",
        lambda *args, **kwargs: pytest.fail("invalid acknowledgement must not call core"),
    )

    assert cli.main(["--podcast", "gooaye", "--confirm", "--expected-episode-ref", "EP700", "--api-cost-ack", "wrong"]) == 1
    assert capsys.readouterr().out == ""


def test_mcp_tool_is_fifteenth_bounded_dry_run_surface(monkeypatch):
    from podcast_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.run_latest_episode_verified_research_report_workflow)
    assert list(signature.parameters) == [
        "podcast_id", "confirm", "expected_episode_ref", "api_cost_ack", "stock_query",
        "include_fixture_verification", "transcription_model", "transcription_device",
        "transcription_compute_type", "transcription_vad_filter", "semantic_provider",
        "semantic_model", "semantic_chunk_seconds", "semantic_max_segments_per_chunk",
    ]
    assert signature.parameters["confirm"].default is False
    for forbidden in ("force", "allow_partial", "retry", "scheduler", "base_url", "api_key_env", "output_path", "progress_callback"):
        assert forbidden not in signature.parameters

    captured = {}
    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "run_latest_episode_verified_research_report_workflow",
        lambda podcast_id, **kwargs: captured.update({"podcast_id": podcast_id, **kwargs})
        or SimpleNamespace(outcome="dry_run"),
    )
    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "result_to_dict",
        lambda result: {"outcome": result.outcome},
    )

    response = mcp_server.run_latest_episode_verified_research_report_workflow("gooaye")

    assert response == {"ok": True, "dry_run": True, "requires_confirmation": True, "data": {"outcome": "dry_run"}}
    assert captured["confirm"] is False


def test_mcp_bad_confirmed_request_is_rejected_before_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "run_latest_episode_verified_research_report_workflow",
        lambda *args, **kwargs: pytest.fail("invalid acknowledgement must not reach core"),
    )

    response = mcp_server.run_latest_episode_verified_research_report_workflow(
        "gooaye", confirm=True, expected_episode_ref="EP700", api_cost_ack="wrong"
    )

    assert response == {
        "ok": False,
        "error_type": "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError",
        "message": "latest episode verified research report workflow command failed",
    }


def test_portable_skill_requires_preview_then_episode_scoped_exact_ack_and_one_call():
    skill = (ROOT / ".agents" / "skills" / "latest-episode-verified-research-report" / "SKILL.md").read_text(encoding="utf-8")

    assert "name: latest-episode-verified-research-report" in skill
    assert "run_latest_episode_verified_research_report_workflow" in skill
    assert "confirm=true" in skill
    assert "expected_episode_ref" in skill
    assert "api_cost_ack" in skill
    assert "exact" in skill
    for prohibited in ("CLI", "terminal", "retry", "scheduler", "fallback", "another side-effect tool"):
        assert prohibited in skill
