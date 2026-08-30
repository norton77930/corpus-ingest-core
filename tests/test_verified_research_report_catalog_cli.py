"""Contract tests for the read-only verified report catalog CLI."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_verified_research_report_catalog.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("catalog_cli_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("argv", "seam_name", "expected"),
    [
        (
            ["list", "--podcast-id", "gooaye", "--episode-ref", "EP672", "--limit", "7"],
            "list_verified_research_reports",
            {"args": (), "kwargs": {"podcast_id": "gooaye", "episode_ref": "EP672", "limit": 7}},
        ),
        (
            ["search", "TSMC", "--podcast-id", "gooaye", "--limit", "8"],
            "search_verified_research_reports",
            {"args": ("TSMC",), "kwargs": {"podcast_id": "gooaye", "episode_ref": None, "limit": 8}},
        ),
        (
            ["inspect", "gooaye", "EP672", "a" * 64],
            "inspect_verified_research_report",
            {"args": ("gooaye", "EP672", "a" * 64), "kwargs": {}},
        ),
    ],
)
def test_subcommands_delegate_to_exactly_one_public_core_seam(monkeypatch, capsys, argv, seam_name, expected):
    cli = _load_cli()
    calls: list[dict[str, object]] = []

    def fake_seam(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return object()

    for candidate in (
        "list_verified_research_reports",
        "search_verified_research_reports",
        "inspect_verified_research_report",
    ):
        monkeypatch.setattr(
            cli, candidate, fake_seam if candidate == seam_name else lambda: pytest.fail("wrong Core seam called")
        )
    monkeypatch.setattr(cli, "verified_research_report_catalog_result_to_dict", lambda result: {"safe": True})

    assert cli.main(argv) == 0

    assert calls == [expected]
    assert json.loads(capsys.readouterr().out) == {"ok": True, "data": {"safe": True}}


def test_known_core_input_error_is_bounded_json_without_traceback_or_path(monkeypatch, capsys):
    cli = _load_cli()

    def fail(**kwargs):
        raise cli.VerifiedResearchReportCatalogInputError(r"D:\private\manifest.json")

    monkeypatch.setattr(cli, "list_verified_research_reports", fail)

    assert cli.main(["list"]) == 1

    output = capsys.readouterr().out
    assert json.loads(output) == {
        "ok": False,
        "error_type": "VerifiedResearchReportCatalogInputError",
        "message": "verified research report catalog query failed",
    }
    assert "Traceback" not in output
    assert "private" not in output


def test_parser_exposes_only_bounded_catalog_inputs():
    cli = _load_cli()
    help_text = cli.build_parser().format_help()

    for forbidden in (
        "output",
        "export",
        "path",
        "confirm",
        "api-cost-ack",
        "network",
        "provider",
    ):
        assert forbidden not in help_text


def test_subprocess_missing_root_list_succeeds_empty_and_creates_no_files(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "list"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert json.loads(completed.stdout) == {
        "ok": True,
        "data": {
            "items": [],
            "limit": 50,
            "returned_count": 0,
            "catalog_root_status": "missing",
            "traversal_status": "complete",
        },
    }
    assert after == before


def test_subprocess_invalid_input_exits_one_with_bounded_json_and_zero_writes(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "list", "--limit", "0"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert json.loads(completed.stdout) == {
        "ok": False,
        "error_type": "VerifiedResearchReportCatalogInputError",
        "message": "verified research report catalog query failed",
    }
    assert "Traceback" not in completed.stdout
    assert str(tmp_path) not in completed.stdout
    assert after == before


def test_unexpected_core_exception_is_fixed_bounded_json_without_private_path(monkeypatch, capsys):
    cli = _load_cli()

    def fail(**kwargs):
        raise RuntimeError(r"D:\\private\\manifest.json Traceback sentinel")

    monkeypatch.setattr(cli, "list_verified_research_reports", fail)

    assert cli.main(["list"]) == 1

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "ok": False,
        "error_type": "VerifiedResearchReportCatalogInputError",
        "message": "verified research report catalog query failed",
    }
    assert "private" not in captured.out
    assert "Traceback" not in captured.out
