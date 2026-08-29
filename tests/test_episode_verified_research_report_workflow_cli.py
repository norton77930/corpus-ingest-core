"""Public CLI contracts for SPEC 019 explicit-episode verified reports."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_episode_verified_research_report_workflow.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("spec019_cli_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_forwards_confirm_and_optional_arguments_to_core(monkeypatch, capsys):
    cli = _load_cli_module()
    received: dict[str, object] = {}
    result = object()

    def run_core(podcast_id, episode_ref, **kwargs):
        received.update(podcast_id=podcast_id, episode_ref=episode_ref, **kwargs)
        return result

    monkeypatch.setattr(cli, "run_episode_verified_research_report_workflow", run_core)
    monkeypatch.setattr(
        cli,
        "result_to_dict",
        lambda value: {"result_identity_matches": value is result},
    )

    exit_code = cli.main(
        [
            "gooaye",
            "EP700",
            "--confirm",
            "--stock-query",
            "NVDA",
            "--include-fixture-verification",
        ]
    )

    assert exit_code == 0
    assert received == {
        "podcast_id": "gooaye",
        "episode_ref": "EP700",
        "confirm": True,
        "stock_query": "NVDA",
        "include_fixture_verification": True,
    }
    assert json.loads(capsys.readouterr().out) == {
        "ok": True,
        "data": {"result_identity_matches": True},
    }


def test_subprocess_default_preview_is_metadata_only_and_writes_nothing(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "gooaye", "EP-cli-preview"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["data"]["episode_ref"] == "EP-cli-preview"
    assert payload["data"]["confirm"] is False
    assert payload["data"]["outcome"] == "blocked"
    assert payload["data"]["bundle_dir"] is None
    assert "private transcript sentinel" not in completed.stdout
    assert list(tmp_path.iterdir()) == []


def test_subprocess_reserved_selector_returns_structured_error(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "gooaye", "LATEST"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 1
    assert json.loads(completed.stdout) == {
        "ok": False,
        "error_type": "episode_verified_research_report_workflow_failed",
    }
    assert "LATEST" not in completed.stdout
    assert "Traceback" not in completed.stdout
    assert list(tmp_path.iterdir()) == []


def test_main_rejects_invalid_argv_with_bounded_json_and_no_usage(monkeypatch, capsys):
    cli = _load_cli_module()

    assert cli.main(["--private-option", r"D:\\private\\report.json"]) == 1

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "ok": False,
        "error_type": "episode_verified_research_report_workflow_failed",
    }
    assert "usage" not in captured.out.casefold()
    assert "private" not in captured.out
    assert "Traceback" not in captured.out


def test_main_bounds_unexpected_core_exception_without_private_message(monkeypatch, capsys):
    cli = _load_cli_module()

    def fail(*args, **kwargs):
        raise RuntimeError(r"D:\\private\\report.json Traceback sentinel")

    monkeypatch.setattr(cli, "run_episode_verified_research_report_workflow", fail)

    assert cli.main(["gooaye", "EP700"]) == 1

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "ok": False,
        "error_type": "episode_verified_research_report_workflow_failed",
    }
    assert "private" not in captured.out
    assert "Traceback" not in captured.out
