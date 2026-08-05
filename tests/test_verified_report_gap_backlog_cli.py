"""CLI contract for SPEC 024 gap backlog."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "list_verified_report_gap_backlog.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("gap_backlog_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_delegates_once(monkeypatch, capsys) -> None:
    cli = _load_cli()
    calls: list[dict[str, object]] = []

    def fake(podcast_id: str, *, limit=50):
        calls.append({"podcast_id": podcast_id, "limit": limit})
        return object()

    monkeypatch.setattr(cli, "list_verified_report_gap_backlog", fake)
    monkeypatch.setattr(
        cli,
        "verified_report_gap_backlog_result_to_dict",
        lambda result: {"gap_count": 0},
    )
    assert cli.main(["gooaye", "--limit", "7"]) == 0
    assert calls == [{"podcast_id": "gooaye", "limit": 7}]
    assert json.loads(capsys.readouterr().out) == {"gap_count": 0}


def test_cli_maps_errors(monkeypatch, capsys) -> None:
    cli = _load_cli()

    def fail(podcast_id: str, *, limit=50):
        raise cli.VerifiedReportGapBacklogInputError("bad")

    monkeypatch.setattr(cli, "list_verified_report_gap_backlog", fail)
    assert cli.main(["gooaye", "--limit", "0"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_type"] == "VerifiedReportGapBacklogInputError"
