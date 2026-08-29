"""Contract tests for the read-only source-revalidation CLI."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "revalidate_verified_research_report_sources.py"
_DIGEST = "a" * 64
_ERROR = {
    "ok": False,
    "error_type": "VerifiedResearchReportSourceRevalidationInputError",
    "message": "verified research report source revalidation failed",
}


def _load_cli():
    spec = importlib.util.spec_from_file_location("source_revalidation_cli_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_forwards_three_locators_to_one_core_call_and_serializes_safe_result(monkeypatch, capsys):
    cli = _load_cli()
    calls: list[tuple[str, str, str]] = []

    def fake_core(podcast_id, episode_ref, source_digest):
        calls.append((podcast_id, episode_ref, source_digest))
        return object()

    monkeypatch.setattr(cli, "revalidate_verified_research_report_sources", fake_core)
    monkeypatch.setattr(
        cli,
        "verified_research_report_source_revalidation_result_to_dict",
        lambda result: {"safe": True, "not_investment_advice": True},
    )

    assert cli.main(["gooaye", "EP672", _DIGEST]) == 0

    assert calls == [("gooaye", "EP672", _DIGEST)]
    assert json.loads(capsys.readouterr().out) == {
        "ok": True,
        "data": {"safe": True, "not_investment_advice": True},
    }


def test_cli_invalid_argv_is_bounded_json_without_usage_path_or_traceback(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "gooaye", "EP672", _DIGEST, "--output", str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert completed.stderr == ""
    assert json.loads(completed.stdout) == _ERROR
    assert "usage" not in completed.stdout.casefold()
    assert str(tmp_path) not in completed.stdout
    assert "traceback" not in completed.stdout.casefold()


def test_cli_oversized_locator_uses_core_fixed_error_without_storage_access(monkeypatch, capsys):
    cli = _load_cli()
    import corpus_ingest_core.verified_research_report_source_revalidation as revalidation

    monkeypatch.setattr(
        revalidation, "_exact_bundle_evidence", lambda locator: (_ for _ in ()).throw(
            AssertionError("oversized locator reached storage")
        )
    )

    assert cli.main(["p" * 129, "EP672", _DIGEST]) == 1
    assert json.loads(capsys.readouterr().out) == _ERROR


def test_cli_exception_is_fixed_bounded_json_without_private_details(monkeypatch, capsys):
    cli = _load_cli()
    monkeypatch.setattr(
        cli,
        "revalidate_verified_research_report_sources",
        lambda *args: (_ for _ in ()).throw(RuntimeError(r"D:\\private\\body.txt traceback")),
    )

    assert cli.main(["gooaye", "EP672", _DIGEST]) == 1

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == _ERROR
    assert "private" not in captured.out
    assert "body" not in captured.out
    assert "traceback" not in captured.out.casefold()


def test_cli_parser_has_only_three_positional_locators():
    cli = _load_cli()
    help_text = cli.build_parser().format_help()

    for forbidden in (
        "path",
        "output",
        "latest",
        "batch",
        "confirm",
        "ack",
        "provider",
        "network",
    ):
        assert forbidden not in help_text.casefold()
