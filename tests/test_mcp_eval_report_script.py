from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scripts import new_mcp_eval_report


def _write_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Phase 5C Codex MCP Tool-use Eval Report",
                "",
                "## Safety Checks",
                "",
                "### Case 1: Transcript evidence search",
                "",
                "### Case 10: Investment advice refusal",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_parse_args_reads_name():
    args = new_mcp_eval_report.parse_args(["--name", "codex session 001"])

    assert args.name == "codex session 001"


def test_create_report_creates_reports_dir_and_copies_template(tmp_path):
    template_path = tmp_path / "evals" / "mcp-tool-use" / "phase-5c-codex-session-template.md"
    reports_dir = tmp_path / "evals" / "mcp-tool-use" / "reports"
    _write_template(template_path)

    result = new_mcp_eval_report.create_report(
        "codex session 001",
        project_root=tmp_path,
        template_path=template_path,
        reports_dir=reports_dir,
        now=datetime(2026, 6, 22, 1, 2, 3),
    )

    assert result["ok"] is True
    assert result["report_path"] == "evals/mcp-tool-use/reports/20260622-010203-codex-session-001.md"
    report_path = tmp_path / result["report_path"]
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == template_path.read_text(encoding="utf-8")


def test_create_report_sanitizes_name_and_avoids_overwrite(tmp_path):
    template_path = tmp_path / "template.md"
    reports_dir = tmp_path / "reports"
    _write_template(template_path)

    first = new_mcp_eval_report.create_report(
        "codex/session 001!",
        project_root=tmp_path,
        template_path=template_path,
        reports_dir=reports_dir,
        now=datetime(2026, 6, 22, 1, 2, 3),
    )
    second = new_mcp_eval_report.create_report(
        "codex/session 001!",
        project_root=tmp_path,
        template_path=template_path,
        reports_dir=reports_dir,
        now=datetime(2026, 6, 22, 1, 2, 3),
    )

    assert first["report_path"] == "reports/20260622-010203-codexsession-001.md"
    assert second["report_path"] == "reports/20260622-010203-codexsession-001-2.md"
    assert (tmp_path / first["report_path"]).exists()
    assert (tmp_path / second["report_path"]).exists()


def test_create_report_uses_default_name_when_sanitized_name_is_empty(tmp_path):
    template_path = tmp_path / "template.md"
    reports_dir = tmp_path / "reports"
    _write_template(template_path)

    result = new_mcp_eval_report.create_report(
        "///",
        project_root=tmp_path,
        template_path=template_path,
        reports_dir=reports_dir,
        now=datetime(2026, 6, 22, 1, 2, 3),
    )

    assert result["report_path"] == "reports/20260622-010203-codex-session.md"


def test_main_outputs_parseable_json(tmp_path, monkeypatch, capsys):
    template_path = tmp_path / "evals" / "mcp-tool-use" / "phase-5c-codex-session-template.md"
    reports_dir = tmp_path / "evals" / "mcp-tool-use" / "reports"
    _write_template(template_path)

    monkeypatch.setattr(new_mcp_eval_report, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(new_mcp_eval_report, "TEMPLATE_PATH", template_path)
    monkeypatch.setattr(new_mcp_eval_report, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(new_mcp_eval_report, "_now", lambda: datetime(2026, 6, 22, 1, 2, 3))

    exit_code = new_mcp_eval_report.main(["--name", "codex session 001"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["report_path"] == "evals/mcp-tool-use/reports/20260622-010203-codex-session-001.md"
    assert (tmp_path / payload["report_path"]).exists()


def test_generated_report_contains_required_sections(tmp_path):
    template_path = tmp_path / "template.md"
    reports_dir = tmp_path / "reports"
    _write_template(template_path)

    result = new_mcp_eval_report.create_report(
        "codex-session-001",
        project_root=tmp_path,
        template_path=template_path,
        reports_dir=reports_dir,
        now=datetime(2026, 6, 22, 1, 2, 3),
    )
    content = (tmp_path / result["report_path"]).read_text(encoding="utf-8")

    assert "## Safety Checks" in content
    assert "Case 1" in content
    assert "Case 10" in content
