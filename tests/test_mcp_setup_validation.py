from __future__ import annotations

import json
import sys
from pathlib import Path

from podcast_ingest_core.models import MentionSearchResult, TranscriptSearchResult


def test_validate_mcp_setup_parse_args_reads_podcast_and_query():
    from scripts import validate_mcp_setup

    args = validate_mcp_setup.parse_args(["--podcast", "gooaye", "--query", "台積電"])

    assert args.podcast == "gooaye"
    assert args.query == "台積電"


def test_run_validation_reports_imports_and_mcp_server_ready(tmp_path, monkeypatch):
    from scripts import validate_mcp_setup

    cache_path = tmp_path / "podcast_ingest.sqlite3"
    cache_path.write_text("", encoding="utf-8")
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")
    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: cache_path)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)
    monkeypatch.setattr(validate_mcp_setup, "search_transcripts", lambda *args, **kwargs: [])
    monkeypatch.setattr(validate_mcp_setup, "search_mentions", lambda *args, **kwargs: [])

    result = validate_mcp_setup.run_validation(podcast_id="gooaye", query="台積電")

    checks = {check["name"]: check for check in result["checks"]}
    assert checks["package_import"]["ok"] is True
    assert checks["mcp_server_import"]["ok"] is True
    assert checks["mcp_server_object"]["ok"] is True
    assert checks["run_mcp_server_exists"]["ok"] is True


def test_run_validation_reports_cache_missing_warning(tmp_path, monkeypatch):
    from scripts import validate_mcp_setup

    missing_cache = tmp_path / "missing.sqlite3"
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")
    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: missing_cache)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)

    result = validate_mcp_setup.run_validation(podcast_id="gooaye", query="台積電")

    checks = {check["name"]: check for check in result["checks"]}
    assert result["ok"] is False
    assert checks["cache_db_exists"]["ok"] is False
    assert any("rebuild_cache.py --podcast gooaye --force" in item for item in result["warnings"])


def test_run_validation_records_search_result_counts(tmp_path, monkeypatch):
    from scripts import validate_mcp_setup

    cache_path = tmp_path / "podcast_ingest.sqlite3"
    cache_path.write_text("", encoding="utf-8")
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")

    def fake_search_transcripts(*args, **kwargs):
        return [
            TranscriptSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="EP672",
                segment_id="1",
                start=1.0,
                end=2.0,
                timestamp="[00:00:01 - 00:00:02]",
                text="台積電",
            )
        ]

    def fake_search_mentions(*args, **kwargs):
        return [
            MentionSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="EP672",
                mention_type="company",
                text="台積電",
                normalized_text="台積電",
                count=1,
                evidence_timestamp="[00:00:01 - 00:00:02]",
                evidence_text="台積電",
            )
        ]

    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: cache_path)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)
    monkeypatch.setattr(validate_mcp_setup, "search_transcripts", fake_search_transcripts)
    monkeypatch.setattr(validate_mcp_setup, "search_mentions", fake_search_mentions)

    result = validate_mcp_setup.run_validation(podcast_id="gooaye", query="台積電")

    checks = {check["name"]: check for check in result["checks"]}
    assert checks["search_transcripts"]["ok"] is True
    assert checks["search_transcripts"]["result_count"] == 1
    assert checks["search_mentions"]["ok"] is True
    assert checks["search_mentions"]["result_count"] == 1


def test_run_validation_checks_dry_run_and_semantic_ack_guard(tmp_path, monkeypatch):
    from scripts import validate_mcp_setup

    cache_path = tmp_path / "podcast_ingest.sqlite3"
    cache_path.write_text("", encoding="utf-8")
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")
    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: cache_path)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)
    monkeypatch.setattr(validate_mcp_setup, "search_transcripts", lambda *args, **kwargs: [])
    monkeypatch.setattr(validate_mcp_setup, "search_mentions", lambda *args, **kwargs: [])

    result = validate_mcp_setup.run_validation(podcast_id="gooaye", query="台積電")

    checks = {check["name"]: check for check in result["checks"]}
    assert checks["side_effect_dry_run_protection"]["ok"] is True
    assert checks["semantic_ack_guard"]["ok"] is True


def test_run_validation_checks_completion_tool_skill_and_early_guard(tmp_path, monkeypatch):
    from scripts import validate_mcp_setup

    cache_path = tmp_path / "podcast_ingest.sqlite3"
    cache_path.write_text("", encoding="utf-8")
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")
    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: cache_path)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)
    monkeypatch.setattr(validate_mcp_setup, "search_transcripts", lambda *args, **kwargs: [])
    monkeypatch.setattr(validate_mcp_setup, "search_mentions", lambda *args, **kwargs: [])

    result = validate_mcp_setup.run_validation(podcast_id="gooaye", query="台積電")

    checks = {check["name"]: check for check in result["checks"]}
    assert checks["completion_tool_registry"]["ok"] is True
    assert checks["completion_tool_registry"]["tool_count"] == 13
    assert checks["completion_skill_metadata"]["ok"] is True
    assert checks["completion_confirmed_next_guard"]["ok"] is True


def test_validate_mcp_setup_main_outputs_json(monkeypatch, capsys, tmp_path):
    from scripts import validate_mcp_setup

    cache_path = tmp_path / "podcast_ingest.sqlite3"
    cache_path.write_text("", encoding="utf-8")
    runner_path = tmp_path / "run_mcp_server.py"
    runner_path.write_text("print('ok')", encoding="utf-8")
    monkeypatch.setattr(validate_mcp_setup.storage, "cache_db_path", lambda: cache_path)
    monkeypatch.setattr(validate_mcp_setup, "RUNNER_PATH", runner_path)
    monkeypatch.setattr(validate_mcp_setup, "search_transcripts", lambda *args, **kwargs: [])
    monkeypatch.setattr(validate_mcp_setup, "search_mentions", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_mcp_setup.py", "--podcast", "gooaye", "--query", "台積電"],
    )

    validate_mcp_setup.main()

    payload = json.loads(capsys.readouterr().out)
    assert "ok" in payload
    assert isinstance(payload["checks"], list)
    assert payload["next_steps"]
