from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_hermes_integration.py"


def _protected_snapshot(
    *,
    data_digest: str = "a",
    config_digest: str = "b",
    skills_digest: str = "c",
) -> dict[str, dict[str, object]]:
    return {
        "podcast_data": {
            "metadata": {"entry_count": 3, "sha256": data_digest * 64},
            "content_token": b"data-content-token".ljust(32, b"0"),
        },
        "hermes_config": {
            "metadata": {"entry_count": 1, "sha256": config_digest * 64},
            "content_token": b"config-content-token".ljust(32, b"0"),
        },
        "managed_skills": {
            "metadata": {"entry_count": 9, "sha256": skills_digest * 64},
            "content_token": b"skills-content-token".ljust(32, b"0"),
        },
    }


EXPECTED_TOOL_ORDER = [
    "list_episodes",
    "get_episode",
    "validate_transcript",
    "search_transcripts",
    "search_mentions",
    "rebuild_cache",
    "download_audio",
    "summarize_episode_extractive",
    "extract_mentions",
    "transcribe_episode",
    "semantic_summarize_episode",
    "run_research_workflow",
    "run_corpus_episode_completion_workflow",
    "run_corpus_latest_episode_deterministic_workflow",
    "run_latest_episode_verified_research_report_workflow",
    "run_episode_verified_research_report_workflow",
    "query_verified_research_report_catalog",
    "revalidate_verified_research_report_sources",
    "query_verified_research_report_coverage",
    "suggest_historical_verified_report_next_step",
    "list_verified_report_gap_backlog",
]


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_hermes_integration", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_descriptor_traversal(validator) -> None:
    if not validator._protected_content_access_supported():
        pytest.skip("descriptor-only protected-content traversal is unavailable")


def test_validator_cli_requires_only_explicit_protected_surface_paths():
    validator = _load_validator()

    args = validator.parse_args(
        [
            "--data-path",
            "data",
            "--config-path",
            "config.yaml",
            "--skills-path",
            "managed-skills",
        ]
    )

    assert args.data_path == Path("data")
    assert args.config_path == Path("config.yaml")
    assert args.skills_path == Path("managed-skills")
    assert args.podcast == "gooaye"
    assert not hasattr(args, "url")


def test_content_token_windows_fails_closed_before_any_path_access(
    tmp_path,
    monkeypatch,
):
    validator = _load_validator()
    protected = tmp_path / "config.yaml"
    protected.write_bytes(b"synthetic-secret-value\n")

    def path_access_forbidden(*args, **kwargs):
        pytest.fail("Windows must fail closed before protected path access")

    monkeypatch.setattr(validator.os, "name", "nt")
    monkeypatch.setattr(Path, "lstat", path_access_forbidden)
    monkeypatch.setattr(Path, "open", path_access_forbidden)
    monkeypatch.setattr(validator.os, "scandir", path_access_forbidden)

    with pytest.raises(ValueError, match="protected content snapshot failed"):
        validator._content_token(protected)


def test_content_token_detects_same_metadata_content_change(tmp_path):
    validator = _load_validator()
    _require_descriptor_traversal(validator)
    protected = tmp_path / "config.yaml"
    protected.write_bytes(b"synthetic-secret-a\n")
    original = protected.stat()
    before_metadata = validator.metadata_manifest(protected)
    before_token = validator._content_token(protected)

    protected.write_bytes(b"synthetic-secret-b\n")
    os.utime(
        protected,
        ns=(original.st_atime_ns, original.st_mtime_ns),
    )

    assert validator.metadata_manifest(protected) == before_metadata
    assert validator._content_token(protected) != before_token


def test_content_token_is_deterministic_for_directory_trees(tmp_path):
    validator = _load_validator()
    _require_descriptor_traversal(validator)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    (first / "empty").mkdir()
    (first / "nested").mkdir()
    (first / "nested" / "value.bin").write_bytes(b"same-content")

    second.mkdir()
    (second / "nested").mkdir()
    (second / "nested" / "value.bin").write_bytes(b"same-content")
    (second / "empty").mkdir()

    assert validator._content_token(first) == validator._content_token(second)

    (second / "nested" / "value.bin").write_bytes(b"changed-content")
    assert validator._content_token(first) != validator._content_token(second)


def test_content_token_distinguishes_file_boundaries(tmp_path):
    validator = _load_validator()
    _require_descriptor_traversal(validator)
    two_files = tmp_path / "two-files"
    one_file = tmp_path / "one-file"
    two_files.mkdir()
    one_file.mkdir()
    (two_files / "a").write_bytes(b"alpha")
    (two_files / "b").write_bytes(b"beta")
    embedded_next_entry = b"F" + (1).to_bytes(8, "big") + b"b" + b"beta"
    (one_file / "a").write_bytes(b"alpha" + embedded_next_entry)

    assert validator._content_token(two_files) != validator._content_token(one_file)


@pytest.mark.parametrize("protected_name", [".env", ".env.local", ".ENV.TEST"])
def test_content_token_rejects_env_before_opening_it(
    tmp_path,
    monkeypatch,
    protected_name,
):
    validator = _load_validator()
    surface = tmp_path / "surface"
    surface.mkdir()
    protected_env = surface / protected_name
    protected_env.write_bytes(b"synthetic-secret-value\n")
    real_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.name.casefold().startswith(".env"):
            pytest.fail(".env files must be rejected before opening")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    with pytest.raises(ValueError, match="protected content snapshot failed"):
        validator._content_token(surface)


def test_content_token_rejects_nested_symlink(tmp_path):
    validator = _load_validator()
    surface = tmp_path / "surface"
    surface.mkdir()
    target = surface / "target.txt"
    target.write_text("synthetic-value\n", encoding="utf-8")
    link = surface / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(ValueError, match="protected content snapshot failed"):
        validator._content_token(surface)


def test_windows_reparse_attribute_is_rejected():
    validator = _load_validator()
    reparse = SimpleNamespace(
        st_mode=0,
        st_file_attributes=getattr(
            validator.stat,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0x400,
        ),
    )

    assert validator._is_reparse_or_symlink(reparse) is True


def test_content_token_rejects_special_entry(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO creation is unavailable")
    validator = _load_validator()
    surface = tmp_path / "surface"
    surface.mkdir()
    os.mkfifo(surface / "pipe")

    with pytest.raises(ValueError, match="protected content snapshot failed"):
        validator._content_token(surface)


def test_metadata_manifest_detects_surface_metadata_changes_without_returning_values(tmp_path):
    validator = _load_validator()
    _require_descriptor_traversal(validator)
    surface = tmp_path / "surface"
    surface.mkdir()
    protected = surface / "config.yaml"
    protected.write_text("synthetic-secret-value\n", encoding="utf-8")

    before = validator.metadata_manifest(surface)
    protected.write_text("replacement-secret-value\n", encoding="utf-8")
    after = validator.metadata_manifest(surface)

    assert before != after
    serialized = json.dumps({"before": before, "after": after})
    assert "synthetic-secret-value" not in serialized
    assert "replacement-secret-value" not in serialized
    assert set(before) == {"entry_count", "sha256"}


def test_tool_result_requires_protocol_and_application_success():
    validator = _load_validator()

    application_failure = SimpleNamespace(
        isError=False,
        structuredContent={"ok": False},
    )
    application_success = SimpleNamespace(
        isError=False,
        structuredContent={"ok": True},
    )
    protocol_failure = SimpleNamespace(
        isError=True,
        structuredContent={"ok": True},
    )

    assert validator.tool_result_ok(application_failure) is False
    assert validator.tool_result_ok(application_success) is True
    assert validator.tool_result_ok(protocol_failure) is False


def test_tool_result_flag_requires_exact_true_boolean():
    validator = _load_validator()
    malformed = SimpleNamespace(
        structuredContent={"dry_run": "false"},
    )
    valid = SimpleNamespace(
        structuredContent={"dry_run": True},
    )

    assert validator.tool_result_flag(malformed, "dry_run") is False
    assert validator.tool_result_flag(valid, "dry_run") is True


def test_build_evidence_v2_emits_only_surface_equality_booleans():
    validator = _load_validator()
    snapshot = _protected_snapshot()

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=snapshot,
        after=snapshot,
    )

    assert result["schema_version"] == "hermes-direct-smoke-v2"
    assert result["protected_surface_evidence_scope"] == (
        "metadata_and_content_equality"
    )
    assert result["protected_surfaces"] == {
        "podcast_data": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
        "hermes_config": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
        "managed_skills": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
    }
    assert "surface_manifests" not in result
    serialized = json.dumps(result)
    assert "data-content-token" not in serialized
    assert "config-content-token" not in serialized
    assert "skills-content-token" not in serialized


def test_build_evidence_accepts_only_exact_registry_preview_and_unchanged_surfaces():
    validator = _load_validator()
    snapshot = _protected_snapshot()

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=snapshot,
        after=snapshot,
    )

    assert result["ok"] is True
    assert result["tool_count"] == 21
    assert result["tool_names"] == EXPECTED_TOOL_ORDER
    assert result["readonly_call_count"] == 1
    assert result["preview_call_count"] == 1
    assert result["preview_confirm"] is False
    assert result["protected_surface_evidence_scope"] == (
        "metadata_and_content_equality"
    )
    assert result["protected_surfaces"] == {
        "podcast_data": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
        "hermes_config": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
        "managed_skills": {
            "metadata_unchanged": True,
            "content_unchanged": True,
        },
    }
    serialized = json.dumps(result)
    assert "http://" not in serialized
    assert "prompt" not in serialized
    assert "response" not in serialized
    assert "session" not in serialized


def test_build_evidence_fails_closed_on_registry_or_surface_drift():
    validator = _load_validator()
    before = _protected_snapshot()
    after = _protected_snapshot(skills_digest="d")

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER[:-1],
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=before,
        after=after,
    )

    assert result["ok"] is False
    assert result["tool_registry_matches"] is False
    assert result["protected_surfaces"]["managed_skills"] == {
        "metadata_unchanged": False,
        "content_unchanged": True,
    }


def test_build_evidence_fails_closed_when_required_surface_is_missing():
    validator = _load_validator()
    incomplete = _protected_snapshot()
    del incomplete["managed_skills"]

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=incomplete,
        after=incomplete,
    )

    assert result["ok"] is False
    assert result["protected_surfaces"]["managed_skills"] == {
        "metadata_unchanged": False,
        "content_unchanged": False,
    }


def test_build_evidence_fails_closed_on_content_only_drift():
    validator = _load_validator()
    before = _protected_snapshot()
    after = _protected_snapshot()
    after["hermes_config"]["content_token"] = b"changed-config-content-token".ljust(
        32,
        b"0",
    )

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=before,
        after=after,
    )

    assert result["ok"] is False
    assert result["protected_surfaces"]["hermes_config"] == {
        "metadata_unchanged": True,
        "content_unchanged": False,
    }


def test_build_evidence_fails_closed_on_malformed_snapshot_container():
    validator = _load_validator()

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=None,
        after=_protected_snapshot(),
    )

    assert result["ok"] is False
    assert result["protected_surfaces"] == {
        name: {
            "metadata_unchanged": False,
            "content_unchanged": False,
        }
        for name in ("podcast_data", "hermes_config", "managed_skills")
    }


def test_build_evidence_rejects_malformed_content_token_without_leaking_values():
    validator = _load_validator()
    before = _protected_snapshot()
    after = _protected_snapshot()
    before["hermes_config"]["content_token"] = "synthetic-secret-token"

    result = validator.build_evidence(
        protocol_version="2025-11-25",
        server_version="1.28.1",
        tool_names=EXPECTED_TOOL_ORDER,
        readonly_ok=True,
        preview_ok=True,
        preview_dry_run=True,
        preview_requires_confirmation=True,
        before=before,
        after=after,
    )

    assert result["ok"] is False
    assert result["protected_surfaces"]["hermes_config"] == {
        "metadata_unchanged": False,
        "content_unchanged": False,
    }
    serialized = json.dumps(result)
    assert "synthetic-secret-token" not in serialized
    assert "a" * 64 not in serialized
    assert "b" * 64 not in serialized
    assert "c" * 64 not in serialized


def test_main_parse_failure_uses_bounded_json_without_echoing_input(
    monkeypatch,
    capsys,
):
    validator = _load_validator()
    protected_path = "synthetic-protected-path"
    protected_token = "synthetic-secret-token"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--data-path",
            protected_path,
            "--unknown-option",
            protected_token,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        validator.main()

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exc_info.value.code == 1
    assert captured.err == ""
    assert result == {
        "schema_version": "hermes-direct-smoke-v2",
        "ok": False,
        "error": "direct_validation_failed",
        "hermes_natural_language_claim": "not_evaluated",
    }
    assert protected_path not in captured.out
    assert protected_path not in captured.err
    assert protected_token not in captured.out
    assert protected_token not in captured.err


def test_main_failure_uses_v2_bounded_schema(monkeypatch, capsys):
    validator = _load_validator()
    args = SimpleNamespace(
        data_path=Path("protected-data"),
        config_path=Path("protected-config.yaml"),
        skills_path=Path("protected-skills"),
        podcast="gooaye",
    )
    monkeypatch.setattr(validator, "parse_args", lambda: args)

    def fail_validation(**kwargs):
        raise ValueError("synthetic-secret-value")

    monkeypatch.setattr(validator, "run_validation", fail_validation)

    with pytest.raises(SystemExit) as exc_info:
        validator.main()

    result = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 1
    assert result == {
        "schema_version": "hermes-direct-smoke-v2",
        "ok": False,
        "error": "direct_validation_failed",
        "hermes_natural_language_claim": "not_evaluated",
    }
    assert "synthetic-secret-value" not in json.dumps(result)
    assert "protected-config.yaml" not in json.dumps(result)


def test_validator_source_never_enables_confirmed_or_session_dump_paths():
    text = SCRIPT.read_text(encoding="utf-8")

    assert '"confirm": False' in text
    assert '"confirm": True' not in text
    assert "session dump" not in text.lower()
    assert "hermes chat" not in text.lower()
    assert "raw_response" not in text
