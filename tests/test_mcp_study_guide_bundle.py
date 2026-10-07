"""Spec 044: generate_study_guide_bundle as append-only Tool 26."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from corpus_ingest_core.errors import (
    LLMProviderConfigError,
    PodcastIngestCoreError,
    StudyGuideBundleError,
    StudyGuideBundleStateError,
)
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from corpus_ingest_core.models import StudyGuideBundleResult
from tests.test_study_guide_bundle import (
    COVER_FILENAME,
    EPISODE,
    PODCAST,
    TITLE,
    _FakeProvider,
    _arm_publisher_dest_lstat,
    _forbid_provider,
    _generated_bundle,
    _non_cover_bytes,
    _ready_episode,
    _valid_payload,
)

_SENTINEL = "SOURCE-BODY-SENTINEL"


def _result(**overrides) -> StudyGuideBundleResult:
    payload = {
        "podcast_id": PODCAST,
        "episode_ref": EPISODE,
        "confirm": False,
        "run_mode": "dry-run",
        "source_summary_path": "source",
        "bundle_dir": "bundle",
        "planned_reads": ["source", "identity.json"],
        "planned_writes": ["bundle/03_full_summary.md"],
        "planned_reuses": [],
        "output_paths": {},
        "report_json_path": None,
        "report_markdown_path": None,
        "reused": False,
        "warnings": ["cache"],
        "not_investment_advice": True,
    }
    payload.update(overrides)
    return StudyGuideBundleResult(**payload)


def test_tool_exposes_only_the_five_contract_parameters():
    from corpus_ingest_core import mcp_server

    signature = inspect.signature(mcp_server.generate_study_guide_bundle)
    assert list(signature.parameters) == [
        "podcast_id",
        "episode_ref",
        "confirm",
        "force",
        "api_cost_ack",
    ]
    assert [parameter.default for parameter in signature.parameters.values()] == [
        "",
        "",
        False,
        False,
        "",
    ]


def test_preview_delegates_once_and_hides_ack(monkeypatch):
    from corpus_ingest_core import mcp_server

    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return _result(bundle_dir=r"D:\lectures\stem", planned_writes=[r"D:\lectures\stem\03_full_summary.md"])

    monkeypatch.setattr(mcp_server.study_guide_bundle, "run_study_guide_bundle", run)
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=False,
        force=True,
        api_cost_ack="SECRET-ACK",
    )

    assert calls == [((PODCAST, EPISODE), {"confirm": False, "force": True})]
    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_confirmation"] is True
    assert response["tool"] == "generate_study_guide_bundle"
    assert response["inputs"] == {"podcast_id": PODCAST, "episode_ref": EPISODE, "force": True}
    assert response["requires_llm"] is True
    assert response["network_read"] is False
    assert response["run_mode"] == "dry-run"
    assert response["not_investment_advice"] is True
    assert response["reads"] == ["source", "identity.json"]
    assert len(response["report_writes"]) == 2
    assert response["warnings"] == ["cache"]
    assert "SECRET-ACK" not in json.dumps(response)
    assert "Every successful confirm writes run reports." in response["risks"]
    assert any("external LLM" in risk for risk in response["risks"])


def test_cover_only_preview_does_not_claim_an_llm_call(monkeypatch):
    from corpus_ingest_core import mcp_server

    def run(*args, **kwargs):
        return _result(planned_writes=["bundle/00_video_info.md"], warnings=[])

    monkeypatch.setattr(mcp_server.study_guide_bundle, "run_study_guide_bundle", run)
    response = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE)
    assert response["requires_llm"] is False
    assert response["warnings"] == []
    assert any("does not call an LLM" in risk for risk in response["risks"])


@pytest.mark.parametrize(
    ("exc", "error_type", "fragment"),
    [
        (StudyGuideBundleStateError("invalid_identity"), "StudyGuideBundleStateError", "latest/next"),
        (StudyGuideBundleStateError("derivation_conflict"), "StudyGuideBundleStateError", "force does not override"),
        (StudyGuideBundleStateError("not-a-code"), "StudyGuideBundleStateError", "could not be validated"),
        (StudyGuideBundleError(f"finance {_SENTINEL}"), "StudyGuideBundleError", "could not be validated"),
        (LLMProviderConfigError(f"missing {_SENTINEL}"), "LLMProviderConfigError", "API-cost acknowledgement"),
        (PodcastIngestCoreError(f"raw {_SENTINEL}"), "PodcastIngestCoreError", "could not be completed"),
        (ValueError(f"bad {_SENTINEL}"), "ValueError", "could not be completed"),
        (RuntimeError(f"traceback {_SENTINEL}"), "InternalError", "inspect local state"),
    ],
)
def test_errors_use_fixed_text(monkeypatch, exc, error_type, fragment):
    from corpus_ingest_core import mcp_server

    def run(*args, **kwargs):
        raise exc

    monkeypatch.setattr(mcp_server.study_guide_bundle, "run_study_guide_bundle", run)
    response = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="SECRET-ACK")
    encoded = json.dumps(response)
    assert response["ok"] is False
    assert response["error_type"] == error_type
    assert fragment in response["message"]
    assert _SENTINEL not in encoded
    assert "SECRET-ACK" not in encoded
    assert "data" not in response


def test_confirm_delegates_once_and_copies_warnings(monkeypatch):
    from corpus_ingest_core import mcp_server

    calls = []

    def run(*args, **kwargs):
        calls.append(kwargs)
        return _result(confirm=True, run_mode="confirmed", warnings=[], reused=True)

    monkeypatch.setattr(mcp_server.study_guide_bundle, "run_study_guide_bundle", run)
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        force=False,
        api_cost_ack="EXACT-ACK",
    )
    assert calls == [{"confirm": True, "force": False, "api_cost_ack": "EXACT-ACK"}]
    assert response["ok"] is True
    assert response["warnings"] == []
    assert response["data"]["reused"] is True
    assert "EXACT-ACK" not in json.dumps(response)


def test_real_preview_refuses_missing_and_finance_sources(tmp_data_dirs):
    from corpus_ingest_core import mcp_server
    from tests.test_study_guide_bundle import _tree

    before = _tree(tmp_data_dirs)
    missing = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE)
    finance = mcp_server.generate_study_guide_bundle("gooaye", "EP678")
    assert missing["ok"] is False
    assert finance["ok"] is False
    assert missing["error_type"] == "StudyGuideBundleError"
    assert "could not be validated" in missing["message"]
    assert _tree(tmp_data_dirs) == before


def test_confirm_reevaluates_after_fixture_drift(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    preview = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE)
    assert preview["ok"] is True
    assert preview["requires_llm"] is True
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    directory.mkdir(parents=True)
    bodies = {
        "00_video_info.md": b"cover\r\n",
        "03_full_summary.md": b"\xef\xbb\xbfsummary\n",
        "04_learning_notes.md": b"notes\r\n",
        "07_final_study_guide.md": b"guide\r\n",
    }
    for name, body in bodies.items():
        (directory / name).write_bytes(body)
    _forbid_provider(monkeypatch)
    confirmed = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    assert confirmed["ok"] is True
    assert confirmed["data"]["reused"] is True
    for name, body in bodies.items():
        assert (directory / name).read_bytes() == body


def test_real_preview_does_not_mutate_or_call_provider(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from tests.test_study_guide_bundle import _tree

    _ready_episode(tmp_data_dirs)
    _forbid_provider(monkeypatch)
    before = _tree(tmp_data_dirs)
    response = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE)
    assert response["ok"] is True
    assert response["network_read"] is False
    assert response["requires_llm"] is True
    assert _tree(tmp_data_dirs) == before
    assert "transcript body must not leak" not in json.dumps(response)


def test_real_confirm_writes_four_files(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured = []
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured))
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    assert response["ok"] is True
    assert response["warnings"]
    assert captured
    assert set(response["data"]["output_paths"]) == {"00", "03", "04", "07"}
    assert "transcript body must not leak" not in json.dumps(response)


def test_real_reuse_and_cover_only_need_no_ack(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    _forbid_provider(monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    before = _non_cover_bytes(directory)
    reused = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    assert reused["ok"] is True
    assert reused["data"]["reused"] is True
    assert _non_cover_bytes(directory) == before

    (directory / COVER_FILENAME).unlink()
    kept = _non_cover_bytes(directory)
    covered = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    assert covered["ok"] is True
    assert covered["data"]["reused"] is False
    assert _non_cover_bytes(directory) == kept
    assert (directory / COVER_FILENAME).is_file()


def test_real_force_with_derivation_refuses_before_provider(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    (directory / "05_prompt_examples.md").write_bytes(b"05-keep")
    before = _non_cover_bytes(directory)
    _forbid_provider(monkeypatch)
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        force=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    assert response["ok"] is False
    assert response["error_type"] == "StudyGuideBundleStateError"
    assert "force does not override" in response["message"]
    assert _non_cover_bytes(directory) == before


def test_real_report_failure_names_the_post_commit_state(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    payload = _valid_payload()
    payload["03_full_summary"] += "\nreport-sentinel\n"
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(payload, []))

    def boom(*args, **kwargs):
        raise OSError("boom-report")

    monkeypatch.setattr(bundle, "write_part_staged_report_pair", boom)
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        force=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    assert response["ok"] is False
    assert response["error_type"] == "StudyGuideBundleStateError"
    assert "run report could not be completed" in response["message"]
    assert "boom-report" not in json.dumps(response)
    assert "data" not in response


_UNSAFE_MESSAGE = (
    "A study-guide source or destination path is unsafe or unreadable; publication is refused."
)


def test_tool_refuses_extra_metadata_failure_without_leaking(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    (directory / "extra.bin").write_bytes(b"EXTRA-BYTES")
    (directory / COVER_FILENAME).unlink()
    before = {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    real_lstat = Path.lstat
    extra_stats = {"count": 0}

    def lstat(self):
        if self.name == "extra.bin":
            extra_stats["count"] += 1
            if extra_stats["count"] >= 2:
                raise PermissionError("boom-extra-meta")
        return real_lstat(self)

    monkeypatch.setattr(Path, "lstat", lstat)
    _forbid_provider(monkeypatch)
    response = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    encoded = json.dumps(response)
    assert response == {
        "ok": False,
        "error_type": "StudyGuideBundleStateError",
        "message": _UNSAFE_MESSAGE,
    }
    assert "boom-extra-meta" not in encoded
    assert {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()} == before


@pytest.mark.parametrize("confirm", [False, True])
def test_tool_refuses_cover_io_error_without_leaking(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    before = {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    real_read = Path.read_bytes

    def read_bytes(self):
        if self.name == COVER_FILENAME:
            raise PermissionError("boom-cover-read")
        return real_read(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    _forbid_provider(monkeypatch)
    response = mcp_server.generate_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=confirm,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    assert response["ok"] is False
    assert response["error_type"] == "StudyGuideBundleStateError"
    assert response["message"] == _UNSAFE_MESSAGE
    assert "boom-cover-read" not in json.dumps(response)
    assert "data" not in response
    assert {path.name: real_read(path) for path in directory.iterdir() if path.is_file()} == before


def test_tool_dir_meta_dest_failure_without_leaking(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import mcp_server
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    (directory / "extra.bin").write_bytes(b"EXTRA-BYTES")
    (directory / "03_full_summary.md").write_bytes(b"\xef\xbb\xbfkept-03\r\n")
    (directory / "04_learning_notes.md").write_bytes(b"kept-04\r\n")
    (directory / "07_final_study_guide.md").write_bytes(b"\xef\xbb\xbfkept-07\r\n")
    (directory / COVER_FILENAME).unlink()
    before = {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    _arm_publisher_dest_lstat(monkeypatch, directory, "boom-dest-dir")
    _forbid_provider(monkeypatch)

    response = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    encoded = json.dumps(response)
    assert response == {
        "ok": False,
        "error_type": "StudyGuideBundleStateError",
        "message": _UNSAFE_MESSAGE,
    }
    assert "boom-dest-dir" not in encoded
    assert "PermissionError" not in encoded
    assert "data" not in response
    assert {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()} == before
