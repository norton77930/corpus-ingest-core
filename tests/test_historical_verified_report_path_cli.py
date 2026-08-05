"""CLI contract for SPEC 023 suggestion."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "suggest_historical_verified_report_next_step.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("historical_path_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_delegates_once(monkeypatch, capsys) -> None:
    cli = _load_cli()
    calls: list[tuple[str, str]] = []

    def fake(podcast_id: str, episode_ref: str):
        calls.append((podcast_id, episode_ref))
        return object()

    monkeypatch.setattr(cli, "suggest_historical_verified_report_next_step", fake)
    monkeypatch.setattr(
        cli,
        "historical_verified_report_path_result_to_dict",
        lambda result: {"suggestion": "report_present"},
    )
    assert cli.main(["gooaye", "EP1"]) == 0
    assert calls == [("gooaye", "EP1")]
    assert json.loads(capsys.readouterr().out) == {"suggestion": "report_present"}


def test_cli_maps_input_error(monkeypatch, capsys) -> None:
    cli = _load_cli()

    def fail(podcast_id: str, episode_ref: str):
        raise cli.HistoricalVerifiedReportPathInputError("bad")

    monkeypatch.setattr(cli, "suggest_historical_verified_report_next_step", fail)
    assert cli.main(["gooaye", "latest"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_type"] == "HistoricalVerifiedReportPathInputError"
