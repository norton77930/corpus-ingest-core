"""CLI contract for SPEC 022 coverage index."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_verified_research_report_coverage.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("coverage_cli_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_delegates_to_exactly_one_public_core_seam(monkeypatch, capsys) -> None:
    cli = _load_cli()
    calls: list[dict[str, object]] = []

    def fake_coverage(podcast_id: str, *, has_bundle=None, limit=50):
        calls.append(
            {"podcast_id": podcast_id, "has_bundle": has_bundle, "limit": limit}
        )
        return object()

    monkeypatch.setattr(cli, "list_verified_research_report_coverage", fake_coverage)
    monkeypatch.setattr(
        cli,
        "verified_research_report_coverage_result_to_dict",
        lambda result: {"safe": True, "not_investment_advice": True},
    )

    assert cli.main(["gooaye", "--has-bundle", "false", "--limit", "10"]) == 0

    assert calls == [{"podcast_id": "gooaye", "has_bundle": False, "limit": 10}]
    assert json.loads(capsys.readouterr().out) == {
        "safe": True,
        "not_investment_advice": True,
    }


def test_known_core_input_error_is_bounded_json_without_traceback_or_path(
    monkeypatch, capsys
) -> None:
    cli = _load_cli()

    def fail(podcast_id: str, *, has_bundle=None, limit=50):
        raise cli.VerifiedResearchReportCoverageInputError(r"D:\private\seed.json")

    monkeypatch.setattr(cli, "list_verified_research_report_coverage", fail)

    assert cli.main(["gooaye"]) == 1

    output = capsys.readouterr().out
    assert json.loads(output) == {
        "ok": False,
        "error_type": "VerifiedResearchReportCoverageInputError",
        "message": "verified research report coverage query failed",
    }
    assert "Traceback" not in output
    assert "private" not in output


def test_cli_rejects_bad_limit(monkeypatch, capsys) -> None:
    cli = _load_cli()

    def raise_limit(podcast_id, *, has_bundle=None, limit=50):
        raise cli.VerifiedResearchReportCoverageInputError(
            "limit must be an integer from 1 to 100"
        )

    monkeypatch.setattr(cli, "list_verified_research_report_coverage", raise_limit)
    assert cli.main(["gooaye", "--limit", "0"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error_type"] == "VerifiedResearchReportCoverageInputError"
