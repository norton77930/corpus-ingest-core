from __future__ import annotations

from dataclasses import fields
import hashlib
import inspect
import json
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> Path:
    from podcast_ingest_core import storage
    import podcast_ingest_core.corpus_index as corpus_index
    import podcast_ingest_core.semantic_summary_smoke_review as semantic_review

    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus", raising=False)
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(
        corpus_index,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        review_dir,
        raising=False,
    )
    monkeypatch.setattr(semantic_review, "REPORTS_DIR", review_dir, raising=False)
    return review_dir


def _tree_manifest(root: Path) -> dict[str, tuple[str, int, int]]:
    manifest: dict[str, tuple[str, int, int]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        stat = path.stat()
        manifest[path.relative_to(root).as_posix()] = (
            hashlib.sha256(payload).hexdigest(),
            stat.st_size,
            stat.st_mtime_ns,
        )
    return manifest


def test_red_private_regeneration_executor_rejects_missing_authority_before_summarizer(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    calls = []
    monkeypatch.setattr(
        runner,
        "semantic_summarize_episode",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner._run_controlled_semantic_summary_regeneration(
            "gooaye",
            "EP700",
            authorization=None,
            expected_summary_path=tmp_path / "EP700.semantic.md",
            api_cost_ack="ack",
            provider="openai-compatible",
            model="fixture-model",
            base_url=None,
            api_key_env="OPENAI_API_KEY",
            reasoning_effort="medium",
            read_timeout_seconds=600,
            chunk_seconds=600,
            max_segments_per_chunk=120,
        )

    assert calls == []


def test_private_regeneration_capability_rejects_wrong_episode_and_reuse(
    monkeypatch, tmp_path
):
    from types import SimpleNamespace

    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError
    from podcast_ingest_core.episode_claim import (
        _mint_controlled_regeneration_capability,
        episode_writer_claim,
    )

    expected = tmp_path / "EP700.semantic.md"
    calls = []

    def fake_summarize(*args, **kwargs):
        calls.append((args, kwargs))
        expected.write_text("replacement", encoding="utf-8")
        return SimpleNamespace(
            podcast_id="gooaye",
            episode_ref="EP700",
            summary_path=expected,
            generated=True,
            already_exists=False,
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", fake_summarize)
    common = {
        "expected_summary_path": expected,
        "api_cost_ack": "ack",
        "provider": "openai-compatible",
        "model": "fixture-model",
        "base_url": None,
        "api_key_env": "OPENAI_API_KEY",
        "reasoning_effort": None,
        "read_timeout_seconds": 120,
        "chunk_seconds": 600,
        "max_segments_per_chunk": 120,
    }
    with episode_writer_claim("gooaye", "EP700"):
        wrong_episode = _mint_controlled_regeneration_capability("gooaye", "EP700")
        with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
            runner._run_controlled_semantic_summary_regeneration(
                "gooaye", "EP701", authorization=wrong_episode, **common
            )
        authorization = _mint_controlled_regeneration_capability("gooaye", "EP700")
        runner._run_controlled_semantic_summary_regeneration(
            "gooaye", "EP700", authorization=authorization, **common
        )
        with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
            runner._run_controlled_semantic_summary_regeneration(
                "gooaye", "EP700", authorization=authorization, **common
            )

    assert len(calls) == 1


def test_red_private_regeneration_executor_forces_exact_canonical_child(monkeypatch, tmp_path):
    from types import SimpleNamespace

    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.episode_claim import (
        _mint_controlled_regeneration_capability,
        episode_writer_claim,
    )
    from podcast_ingest_core.generation_proof import controlled_child_commit_scope

    expected = tmp_path / "EP700.semantic.md"
    expected.write_text("old", encoding="utf-8")
    commits = []

    def fake_summarize(*args, **kwargs):
        assert kwargs["force"] is True
        assert kwargs["reasoning_effort"] == "medium"
        assert kwargs["read_timeout_seconds"] == 600
        expected.write_text("new", encoding="utf-8")
        return SimpleNamespace(
            podcast_id="gooaye",
            episode_ref="EP700",
            summary_path=expected,
            generated=True,
            already_exists=False,
            provider="fixture",
            model="fixture-model",
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", fake_summarize)
    with episode_writer_claim("gooaye", "EP700"):
        authorization = _mint_controlled_regeneration_capability("gooaye", "EP700")
        with controlled_child_commit_scope(commits.append):
            result = runner._run_controlled_semantic_summary_regeneration(
                "gooaye",
                "EP700",
                authorization=authorization,
                expected_summary_path=expected,
                api_cost_ack="ack",
                provider="openai-compatible",
                model="fixture-model",
                base_url=None,
                api_key_env="OPENAI_API_KEY",
                reasoning_effort="medium",
                read_timeout_seconds=600,
                chunk_seconds=600,
                max_segments_per_chunk=120,
            )

    assert result.episode_ref == "EP700"
    assert result.generated is True
    assert [(commit.role, commit.path, commit.generated) for commit in commits] == [
        ("semantic_summary", expected, True)
    ]


def test_semantic_remediation_public_signature_and_exports():
    import podcast_ingest_core as core

    expected = [
        "podcast_id",
        "episode_ref",
        "action",
        "confirm",
        "api_cost_ack",
        "provider",
        "model",
        "base_url",
        "api_key_env",
        "reasoning_effort",
        "read_timeout_seconds",
        "chunk_seconds",
        "max_segments_per_chunk",
        "progress_callback",
    ]
    signature = inspect.signature(core.run_corpus_semantic_remediation)

    assert list(signature.parameters) == expected
    assert signature.parameters["episode_ref"].default is inspect.Parameter.empty
    assert signature.parameters["action"].default == "next"
    assert signature.parameters["confirm"].default is False
    assert signature.parameters["api_cost_ack"].default == ""
    assert signature.parameters["provider"].default == "openai-compatible"
    assert signature.parameters["model"].default is None
    assert signature.parameters["base_url"].default is None
    assert signature.parameters["api_key_env"].default == "OPENAI_API_KEY"
    assert signature.parameters["reasoning_effort"].default is None
    assert signature.parameters["read_timeout_seconds"].default == 120
    assert signature.parameters["chunk_seconds"].default == 600
    assert signature.parameters["max_segments_per_chunk"].default == 120
    assert signature.parameters["progress_callback"].default is None
    assert core.CorpusSemanticRemediationRunnerFailedError.__name__ == (
        "CorpusSemanticRemediationRunnerFailedError"
    )


def test_semantic_remediation_model_field_contracts():
    from podcast_ingest_core import (
        CorpusSemanticRemediationRunCounts,
        CorpusSemanticRemediationRunFilter,
        CorpusSemanticRemediationRunResult,
        CorpusSemanticRemediationRunRow,
        CorpusSemanticRemediationRunWarning,
    )

    assert [field.name for field in fields(CorpusSemanticRemediationRunFilter)] == [
        "episode_ref",
        "action",
        "provider",
        "model",
        "reasoning_effort",
        "read_timeout_seconds",
        "chunk_seconds",
        "max_segments_per_chunk",
    ]
    assert [field.name for field in fields(CorpusSemanticRemediationRunCounts)] == [
        "row_count",
        "selected_count",
        "executed_count",
        "reused_count",
        "completed_count",
        "failed_count",
        "blocked_count",
        "rejected_count",
        "manual_only_count",
        "warning_count",
    ]
    assert [field.name for field in fields(CorpusSemanticRemediationRunWarning)] == [
        "scope",
        "episode_ref",
        "message",
    ]
    assert [field.name for field in fields(CorpusSemanticRemediationRunRow)] == [
        "episode_ref",
        "action",
        "status",
        "reason",
        "requires_api_cost_ack",
        "transcript_transfer_risk",
        "may_incur_api_cost",
        "manual_only",
        "planned_reads",
        "planned_writes",
        "output_paths",
        "source_report_paths",
        "provider",
        "model",
        "failure_category",
        "warnings",
    ]
    assert [field.name for field in fields(CorpusSemanticRemediationRunResult)] == [
        "podcast_id",
        "run_mode",
        "confirm",
        "episode_ref",
        "requested_action",
        "selected_action",
        "executed_action",
        "report_json_path",
        "report_markdown_path",
        "filters",
        "counts",
        "rows",
        "warnings",
        "not_investment_advice",
    ]


def test_semantic_remediation_storage_paths_do_not_create_directories(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = storage.corpus_semantic_remediation_run_asset_paths("gooaye")

    assert paths.json_path == (
        tmp_path / "corpus" / "gooaye" / "corpus-semantic-remediation-run.json"
    )
    assert paths.markdown_path == (
        tmp_path / "corpus" / "gooaye" / "corpus-semantic-remediation-run.md"
    )
    assert not (tmp_path / "corpus").exists()
    assert _tree_manifest(tmp_path) == {}


def test_semantic_preview_from_snapshot_reuses_supplied_payload(monkeypatch):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    def unexpected_builder(*args, **kwargs):
        pytest.fail("snapshot preview called a corpus builder")

    monkeypatch.setattr(
        runner, "_build_corpus_index_snapshot", unexpected_builder, raising=False
    )
    monkeypatch.setattr(
        runner,
        "_build_corpus_remediation_plan_snapshot",
        unexpected_builder,
        raising=False,
    )

    row, action, warnings = runner._preview_corpus_semantic_remediation_from_snapshot(
        "gooaye",
        "EP700",
        plan_payload={
            "episodes": [
                {
                    "podcast_id": "gooaye",
                    "episode_ref": "EP700",
                    "title": "EP700 Alpha",
                    "artifact_status": {
                        "transcript": {"status": "valid", "paths": {}},
                        "semantic_summary": {"status": "missing", "paths": {}},
                        "semantic_review": {
                            "status": "missing",
                            "review_status": "missing",
                            "paths": {},
                        },
                    },
                }
            ]
        },
    )

    assert action == "semantic_summary"
    assert row.status == "selected"
    assert warnings == []


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_seed(
    monkeypatch,
    tmp_path: Path,
    episode_ref: str = "EP700",
    *,
    title: str | None = None,
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    title = title or f"{episode_ref} Alpha"
    return _write_json(
        storage.corpus_episode_seed_asset_path("gooaye", episode_ref),
        {
            "podcast_id": "gooaye",
            "episode_ref": episode_ref,
            "title": title,
            "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
            "duration": "00:42:00",
            "guid_status": "present",
            "has_audio_url": True,
            "seed_source": "rss",
            "selector": episode_ref,
            "warning_count": 0,
            "warnings": [],
            "not_investment_advice": True,
        },
    )


def _write_transcript(
    monkeypatch,
    tmp_path: Path,
    episode_ref: str = "EP700",
    *,
    title: str | None = None,
    text: str = "private transcript sentinel must not leak",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    title = title or f"{episode_ref} Alpha"
    paths = storage.transcript_asset_paths("gooaye", episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        paths.json_path,
        {
            "podcast_id": "gooaye",
            "episode_ref": episode_ref,
            "title": title,
            "language": "zh",
            "segment_count": 1,
            "last_segment_end_seconds": 5.5,
            "completed": True,
            "segments": [
                {"id": 1, "start": 0.0, "end": 5.5, "text": text}
            ],
        },
    )
    paths.text_path.write_text(text, encoding="utf-8")
    paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:05,500\nprivate sentinel\n",
        encoding="utf-8",
    )
    return paths.json_path


def _write_semantic_summary(
    monkeypatch,
    tmp_path: Path,
    episode_ref: str = "EP700",
    *,
    title: str | None = None,
    body: str = "# safe semantic fixture",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    title = title or f"{episode_ref} Alpha"
    path = storage.semantic_summary_asset_path("gooaye", episode_ref, title)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_semantic_review(
    monkeypatch,
    tmp_path: Path,
    episode_ref: str = "EP700",
    *,
    review_status: str = "passed",
    timestamp: str = "20260712-010101",
    raw_bytes: bytes | None = None,
) -> Path:
    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    path = review_dir / (
        f"{timestamp}__gooaye__{episode_ref}.semantic-review.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if raw_bytes is not None:
        path.write_bytes(raw_bytes)
        return path

    from podcast_ingest_core import storage
    from podcast_ingest_core.semantic_summary_smoke_review import (
        review_semantic_summary_smoke,
    )

    summary_path = storage.semantic_summary_asset_path(
        "gooaye", episode_ref, f"{episode_ref} Alpha"
    )
    if review_status == "failed":
        summary_path.write_text("Buy ACME now", encoding="utf-8")
    elif review_status == "blocked":
        summary_path.write_bytes(b"\xff")
    elif review_status != "passed":
        # Deliberately malformed non-success fixture; authentic readers must
        # schedule a real review rather than trust it.
        _write_json(path, {"review_status": review_status})
        return path
    created = review_semantic_summary_smoke("gooaye", episode_ref)
    if created.review_json_path != path:
        created.review_markdown_path.replace(path.with_suffix(".md"))
        created.review_json_path.replace(path)
    return path


def _setup_preview_state(monkeypatch, tmp_path: Path, state: str) -> None:
    _write_seed(monkeypatch, tmp_path)
    if state == "invalid_transcript":
        return
    _write_transcript(monkeypatch, tmp_path)
    if state == "missing_summary":
        return
    summary = _write_semantic_summary(monkeypatch, tmp_path)
    if state == "unreadable_summary":
        summary.write_bytes(b"\xffprivate semantic sentinel")
        return
    if state == "missing_review":
        return
    if state == "passed_review":
        _write_semantic_review(monkeypatch, tmp_path, review_status="passed")
    elif state == "failed_review":
        _write_semantic_review(monkeypatch, tmp_path, review_status="failed")
    elif state == "blocked_review":
        _write_semantic_review(monkeypatch, tmp_path, review_status="blocked")
    elif state == "unknown_review":
        _write_semantic_review(monkeypatch, tmp_path, review_status="available")
    elif state == "unreadable_review":
        _write_semantic_review(
            monkeypatch,
            tmp_path,
            raw_bytes=b"{not-json private review sentinel",
        )
    elif state in {"stale_review", "forged_review"}:
        review_path = _write_semantic_review(
            monkeypatch, tmp_path, review_status="passed"
        )
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
        if state == "stale_review":
            review_payload["semantic_summary_sha256"] = "0" * 64
        else:
            review_payload["review_boundary"] = "forged-review-boundary"
        review_path.write_text(json.dumps(review_payload), encoding="utf-8")


@pytest.mark.parametrize(
    ("state", "selected_action", "row_status", "manual_only"),
    [
        ("invalid_transcript", "blocked", "blocked", True),
        ("missing_summary", "semantic_summary", "selected", False),
        ("unreadable_summary", "blocked", "blocked", True),
        ("missing_review", "semantic_review", "selected", False),
        ("passed_review", "completed", "completed", False),
        ("failed_review", "blocked", "blocked", True),
        ("blocked_review", "blocked", "blocked", True),
        ("unknown_review", "blocked", "blocked", True),
        ("unreadable_review", "blocked", "blocked", True),
        ("stale_review", "blocked", "blocked", True),
        ("forged_review", "blocked", "blocked", True),
    ],
)
def test_semantic_preview_state_table_is_strict_zero_file(
    monkeypatch,
    tmp_path: Path,
    state: str,
    selected_action: str,
    row_status: str,
    manual_only: bool,
):
    from podcast_ingest_core import run_corpus_semantic_remediation

    _setup_preview_state(monkeypatch, tmp_path, state)
    before = _tree_manifest(tmp_path)

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")

    assert result.run_mode == "dry_run"
    assert result.confirm is False
    assert result.episode_ref == "EP700"
    assert result.selected_action == selected_action
    assert result.executed_action is None
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert len(result.rows) == 1
    assert result.rows[0].status == row_status
    assert result.rows[0].manual_only is manual_only
    assert result.not_investment_advice is True
    assert _tree_manifest(tmp_path) == before
    assert not list(tmp_path.rglob("*.part"))


def test_semantic_summary_preview_exposes_only_bounded_risk_metadata(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import run_corpus_semantic_remediation
    from podcast_ingest_core.corpus_semantic_remediation_runner import result_to_dict

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")
    row = result.rows[0]
    payload = result_to_dict(result)

    assert row.action == "semantic_summary"
    assert row.requires_api_cost_ack is True
    assert row.transcript_transfer_risk is True
    assert row.may_incur_api_cost is True
    assert str(transcript_json) in row.planned_reads
    assert row.planned_writes
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "private transcript sentinel must not leak" not in serialized
    assert "generated_at" not in payload


def test_semantic_review_preview_has_no_llm_risk(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import run_corpus_semantic_remediation

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    summary = _write_semantic_summary(monkeypatch, tmp_path)

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")
    row = result.rows[0]

    assert row.action == "semantic_review"
    assert row.requires_api_cost_ack is False
    assert row.transcript_transfer_risk is False
    assert row.may_incur_api_cost is False
    assert str(summary) in row.planned_reads
    assert row.planned_writes == [
        "timestamped semantic review JSON/Markdown reports"
    ]
    assert row.provider is None
    assert row.model is None


@pytest.mark.parametrize(
    "episode_ref",
    ["", "latest", "../EP700", "https://example.invalid/EP700", "\\\\server\\EP700", "EP700?token=secret", "EP700\nsecret"],
)
def test_invalid_episode_ref_rejected_before_snapshot(
    monkeypatch, episode_ref: str
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    calls = {"index": 0, "plan": 0}

    def fail_index(*args, **kwargs):
        calls["index"] += 1
        raise AssertionError("snapshot must not run")

    def fail_plan(*args, **kwargs):
        calls["plan"] += 1
        raise AssertionError("snapshot must not run")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", fail_index, raising=False)
    monkeypatch.setattr(
        runner, "_build_corpus_remediation_plan_snapshot", fail_plan, raising=False
    )

    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner.run_corpus_semantic_remediation(
            "gooaye", episode_ref=episode_ref
        )

    assert calls == {"index": 0, "plan": 0}


def test_invalid_action_and_chunk_settings_rejected_before_snapshot(monkeypatch):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    calls = 0

    def fail_index(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("snapshot must not run")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", fail_index, raising=False)

    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner.run_corpus_semantic_remediation(
            "gooaye", episode_ref="EP700", action="batch"
        )
    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner.run_corpus_semantic_remediation(
            "gooaye", episode_ref="EP700", chunk_seconds=0
        )
    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner.run_corpus_semantic_remediation(
            "gooaye", episode_ref="EP700", max_segments_per_chunk=0
        )

    assert calls == 0


def test_explicit_preview_action_mismatch_is_rejected_without_execution(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import run_corpus_semantic_remediation

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    before = _tree_manifest(tmp_path)

    matching = run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_summary"
    )
    mismatch = run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review"
    )

    assert matching.selected_action == "semantic_summary"
    assert matching.rows[0].status == "selected"
    assert mismatch.selected_action == "semantic_summary"
    assert mismatch.rows[0].status == "rejected"
    assert mismatch.executed_action is None
    assert _tree_manifest(tmp_path) == before


def test_requested_episode_is_isolated_before_state_reduction(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import run_corpus_semantic_remediation

    _write_seed(monkeypatch, tmp_path, "EP700")
    _write_transcript(monkeypatch, tmp_path, "EP700")
    _write_seed(monkeypatch, tmp_path, "EP701")
    _write_transcript(monkeypatch, tmp_path, "EP701")
    _write_semantic_summary(monkeypatch, tmp_path, "EP701")
    _write_semantic_review(
        monkeypatch, tmp_path, "EP701", review_status="failed"
    )

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")
    absent = run_corpus_semantic_remediation("gooaye", episode_ref="EP999")

    assert result.selected_action == "semantic_summary"
    assert result.rows[0].episode_ref == "EP700"
    assert absent.selected_action == "blocked"
    assert absent.rows[0].status == "blocked"
    assert absent.rows[0].manual_only is True


def test_preview_uses_one_shared_index_plan_snapshot_and_no_side_effect_surface(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_index as corpus_index
    import podcast_ingest_core.corpus_remediation_plan as remediation_plan
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    index_calls = []
    plan_calls = []
    real_index = corpus_index._build_corpus_index_snapshot
    real_plan = remediation_plan._build_corpus_remediation_plan_snapshot

    def build_index(podcast_id: str):
        snapshot = real_index(podcast_id)
        index_calls.append(snapshot)
        return snapshot

    def build_plan(podcast_id: str, *, index_result, index_payload):
        plan_calls.append((index_result, index_payload))
        return real_plan(
            podcast_id,
            index_result=index_result,
            index_payload=index_payload,
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run side-effect surface was called")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", build_index)
    monkeypatch.setattr(
        runner, "_build_corpus_remediation_plan_snapshot", build_plan
    )
    monkeypatch.setattr(corpus_index, "_persist_corpus_index_snapshot", forbidden)
    monkeypatch.setattr(
        remediation_plan, "_persist_corpus_remediation_plan_snapshot", forbidden
    )
    monkeypatch.setattr(runner, "semantic_summarize_episode", forbidden, raising=False)
    monkeypatch.setattr(
        runner, "review_semantic_summary_smoke", forbidden, raising=False
    )

    progress_calls = []
    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        progress_callback=lambda *args, **kwargs: progress_calls.append((args, kwargs)),
    )

    assert result.selected_action == "semantic_summary"
    assert len(index_calls) == 1
    assert len(plan_calls) == 1
    assert plan_calls[0][0] is index_calls[0].result
    assert plan_calls[0][1] is index_calls[0].payload
    assert progress_calls == []


def test_stale_persisted_index_plan_and_report_are_not_stage_truth_or_overwritten(
    monkeypatch, tmp_path: Path
):
    from podcast_ingest_core import run_corpus_semantic_remediation, storage

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    paths = [
        storage.corpus_index_asset_paths("gooaye").json_path,
        storage.corpus_index_asset_paths("gooaye").markdown_path,
        storage.corpus_remediation_plan_asset_paths("gooaye").json_path,
        storage.corpus_remediation_plan_asset_paths("gooaye").markdown_path,
        storage.corpus_semantic_remediation_run_asset_paths("gooaye").json_path,
        storage.corpus_semantic_remediation_run_asset_paths("gooaye").markdown_path,
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stale sentinel says completed", encoding="utf-8")
    before = _tree_manifest(tmp_path)

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")

    assert result.selected_action == "semantic_summary"
    assert _tree_manifest(tmp_path) == before
    for path in paths:
        assert path.read_text(encoding="utf-8") == "stale sentinel says completed"


def test_snapshot_exception_is_category_only_blocked_failed_zero_write(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.corpus_semantic_remediation_runner import result_to_dict

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    before = _tree_manifest(tmp_path)

    def explode(*args, **kwargs):
        raise RuntimeError(
            "private transcript https://secret.invalid/?token=super-secret Traceback"
        )

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", explode)
    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700"
    )
    serialized = json.dumps(result_to_dict(result), ensure_ascii=False)

    assert result.selected_action == "blocked"
    assert result.rows[0].action == "blocked"
    assert result.rows[0].status == "failed"
    assert result.rows[0].manual_only is True
    assert result.rows[0].failure_category == "RuntimeError"
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert "super-secret" not in serialized
    assert "secret.invalid" not in serialized
    assert "private transcript" not in serialized
    assert "Traceback" not in serialized
    assert _tree_manifest(tmp_path) == before

def test_confirmed_summary_requires_exact_ack_before_snapshot(monkeypatch):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    calls = {"index": 0, "summary": 0, "writer": 0}

    def index(*args, **kwargs):
        calls["index"] += 1
        raise AssertionError("snapshot must not run before acknowledgement")

    def summary(*args, **kwargs):
        calls["summary"] += 1
        raise AssertionError("summary must not run")

    def writer(*args, **kwargs):
        calls["writer"] += 1
        raise AssertionError("writer must not run")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", index)
    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    monkeypatch.setattr(runner, "_write_run_report", writer, raising=False)

    for acknowledgement in ("", SEMANTIC_API_COST_ACK + " "):
        with pytest.raises(CorpusSemanticRemediationRunnerFailedError) as exc_info:
            runner.run_corpus_semantic_remediation(
                "gooaye",
                episode_ref="EP700",
                action="semantic_summary",
                confirm=True,
                api_cost_ack=acknowledgement,
            )
        assert SEMANTIC_API_COST_ACK in str(exc_info.value)

    assert calls == {"index": 0, "summary": 0, "writer": 0}


def test_confirmed_next_is_rejected_before_snapshot(monkeypatch):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    calls = 0

    def index(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("snapshot must not run")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", index)

    with pytest.raises(CorpusSemanticRemediationRunnerFailedError):
        runner.run_corpus_semantic_remediation(
            "gooaye", episode_ref="EP700", action="next", confirm=True
        )

    assert calls == 0


def test_confirmed_summary_action_drift_writes_rejected_report_without_fallback(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(monkeypatch, tmp_path)
    calls = {"summary": 0, "review": 0}

    def summary(*args, **kwargs):
        calls["summary"] += 1
        raise AssertionError("drift must not execute summary")

    def review(*args, **kwargs):
        calls["review"] += 1
        raise AssertionError("drift must not execute fallback review")

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    monkeypatch.setattr(runner, "review_semantic_summary_smoke", review)

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.selected_action == "semantic_review"
    assert result.executed_action is None
    assert result.rows[0].status == "rejected"
    assert calls == {"summary": 0, "review": 0}
    assert result.report_json_path is not None
    assert result.report_markdown_path is not None
    assert result.report_json_path.exists()
    assert result.report_markdown_path.exists()


def test_confirmed_summary_uses_real_semantic_core_with_mock_provider_once(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    provider_calls = []
    review_calls = []
    progress_events = []

    class FakeProvider:
        provider_name = "openai-compatible"
        model = "safe-model"

        def summarize_chunk(self, chunk):
            return "chunk fact [00:00:00 - 00:00:05]"

        def summarize_final(
            self, *, podcast_display_name, episode_ref, title, chunk_summaries
        ):
            return "final fact [00:00:00 - 00:00:05]"

    def create_provider(
        provider,
        *,
        model,
        base_url,
        api_key_env,
        reasoning_effort,
        read_timeout_seconds,
        api_cost_ack,
        summary_profile,
    ):
        provider_calls.append(
            {
                "provider": provider,
                "model": model,
                "base_url": base_url,
                "api_key_env": api_key_env,
                "api_cost_ack": api_cost_ack,
                "summary_profile": summary_profile,
            }
        )
        return FakeProvider()

    monkeypatch.setattr(semantic_summarizer, "create_provider", create_provider)
    monkeypatch.setattr(
        runner,
        "review_semantic_summary_smoke",
        lambda *args, **kwargs: review_calls.append((args, kwargs)),
    )

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        provider="openai-compatible",
        model="safe-model",
        base_url="https://endpoint.invalid/v1?token=must-not-leak",
        api_key_env="OPENAI_API_KEY",
        chunk_seconds=600,
        max_segments_per_chunk=120,
        progress_callback=lambda event, **payload: progress_events.append(
            (event, payload)
        ),
    )

    assert result.executed_action == "semantic_summary"
    assert result.rows[0].status == "executed"
    assert result.counts.executed_count == 1
    assert len(provider_calls) == 1
    assert provider_calls[0]["api_cost_ack"] is SEMANTIC_API_COST_ACK
    assert provider_calls[0]["model"] == "safe-model"
    assert provider_calls[0]["base_url"].startswith("https://endpoint.invalid")
    assert provider_calls[0]["api_key_env"] == "OPENAI_API_KEY"
    # Spec 037: gooaye has no summary_profile key, so the finance shape reaches
    # the factory unchanged through the remediation runner as well.
    assert provider_calls[0]["summary_profile"] == "finance"
    assert review_calls == []
    assert progress_events
    assert len(result.rows[0].output_paths) == 1
    assert Path(result.rows[0].output_paths[0]).exists()
    serialized = json.dumps(runner.result_to_dict(result), ensure_ascii=False)
    assert "endpoint.invalid" not in serialized
    assert "must-not-leak" not in serialized
    assert "private transcript sentinel" not in serialized


def test_confirmed_summary_race_reuses_existing_artifact_and_stops(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    real_preview = runner._preview_selection
    review_calls = []

    def preview_then_create_summary(podcast_id: str, episode_ref: str):
        selection = real_preview(podcast_id, episode_ref)
        _write_semantic_summary(monkeypatch, tmp_path, episode_ref)
        return selection

    monkeypatch.setattr(runner, "_preview_selection", preview_then_create_summary)
    monkeypatch.setattr(
        runner,
        "review_semantic_summary_smoke",
        lambda *args, **kwargs: review_calls.append((args, kwargs)),
    )

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.selected_action == "semantic_summary"
    assert result.executed_action == "semantic_summary"
    assert result.rows[0].status == "reused"
    assert result.counts.reused_count == 1
    assert review_calls == []


@pytest.mark.parametrize("failure_type", [RuntimeError, OSError])
def test_confirmed_summary_failure_is_category_only_and_reported(
    monkeypatch, tmp_path: Path, failure_type: type[Exception]
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    def explode(*args, **kwargs):
        raise failure_type(
            "private transcript semantic body prompt text raw response "
            "sk-test-secret-value Buy recommendation target price guaranteed return "
            "https://endpoint.invalid/?token=secret Traceback"
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", explode)

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    payload = runner.result_to_dict(result)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert result.executed_action == "semantic_summary"
    assert result.rows[0].status == "failed"
    assert result.rows[0].manual_only is True
    assert result.rows[0].failure_category == failure_type.__name__
    assert result.report_json_path is not None and result.report_json_path.exists()
    assert result.report_markdown_path is not None and result.report_markdown_path.exists()
    assert "private transcript" not in serialized
    assert "endpoint.invalid" not in serialized
    assert "token=secret" not in serialized
    assert "Traceback" not in serialized


def test_confirmed_report_is_metadata_only_timestamp_free_and_atomic(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)
    summary_path = tmp_path / "summaries" / "gooaye" / "EP700__EP700-Alpha.semantic.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    def summary(*args, **kwargs):
        summary_path.write_text("semantic body must not enter report", encoding="utf-8")
        return SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP700",
            title="EP700 Alpha",
            summary_path=summary_path,
            transcript_json_path=transcript_json,
            transcript_text_path=transcript_json.with_suffix(".txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            already_exists=False,
            provider="openai-compatible",
            model="safe-model",
            chunk_count=1,
            evidence_count=1,
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        model="safe-model",
    )

    json_text = result.report_json_path.read_text(encoding="utf-8")
    markdown_text = result.report_markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_text)

    assert "generated_at" not in payload
    assert "generated_at" not in markdown_text
    assert "semantic body must not enter report" not in json_text
    assert "semantic body must not enter report" not in markdown_text
    assert "private transcript sentinel" not in json_text
    assert "private transcript sentinel" not in markdown_text
    assert not list(tmp_path.rglob("*.part"))


def test_confirmed_markdown_report_renders_full_bounded_result_metadata(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)
    summary_path = tmp_path / "summaries" / "gooaye" / "EP700__EP700-Alpha.semantic.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    def summary(*args, **kwargs):
        summary_path.write_text("bounded semantic body", encoding="utf-8")
        return SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP700",
            title="EP700 Alpha",
            summary_path=summary_path,
            transcript_json_path=transcript_json,
            transcript_text_path=transcript_json.with_suffix(".txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            already_exists=False,
            provider="openai-compatible",
            model="safe-model",
            chunk_count=1,
            evidence_count=1,
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        model="safe-model",
        chunk_seconds=321,
        max_segments_per_chunk=45,
    )

    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    for required_label in (
        "Report JSON path",
        "Report Markdown path",
        "Filter episode",
        "Filter action",
        "Provider",
        "Model",
        "Chunk seconds",
        "Max segments per chunk",
        "Requires API cost acknowledgement",
        "Transcript transfer risk",
        "May incur API cost",
        "Manual only",
        "Planned reads",
        "Planned writes",
        "Output paths",
        "Source report paths",
        "Row warnings",
        "Warning scope",
        "Warning episode",
        "Not investment advice",
    ):
        assert required_label in markdown
    assert "safe-model" in markdown
    assert "321" in markdown
    assert "45" in markdown
    assert str(transcript_json) in markdown
    assert str(summary_path) in markdown
    assert "bounded semantic body" not in markdown


def test_runner_report_writer_failure_is_safe_nontransactional_and_no_cleanup_retry(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)
    summary_path = tmp_path / "summaries" / "gooaye" / "EP700__EP700-Alpha.semantic.md"
    summary_calls = 0

    def summary(*args, **kwargs):
        nonlocal summary_calls
        summary_calls += 1
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("created semantic artifact", encoding="utf-8")
        return SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP700",
            title="EP700 Alpha",
            summary_path=summary_path,
            transcript_json_path=transcript_json,
            transcript_text_path=transcript_json.with_suffix(".txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            already_exists=False,
            provider="openai-compatible",
            model=None,
            chunk_count=1,
            evidence_count=1,
        )

    real_write_pair = runner.write_atomic_audit_report_pair

    def fail_commit_marker(json_path: Path, markdown_path: Path, payload: dict, markdown: str):
        # The staged Markdown may have committed, but the JSON marker failure
        # must leave no reader-acceptable pair.
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        raise OSError("https://secret.invalid/?token=must-not-leak")

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    monkeypatch.setattr(runner, "write_atomic_audit_report_pair", fail_commit_marker)

    with pytest.raises(CorpusSemanticRemediationRunnerFailedError) as exc_info:
        runner.run_corpus_semantic_remediation(
            "gooaye",
            episode_ref="EP700",
            action="semantic_summary",
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    report_paths = runner.storage.corpus_semantic_remediation_run_asset_paths("gooaye")
    from podcast_ingest_core.audit_report_pair import is_complete_audit_report_pair

    assert summary_calls == 1
    assert summary_path.exists()
    assert not report_paths.json_path.exists()
    assert report_paths.markdown_path.exists()
    assert not is_complete_audit_report_pair(
        report_paths.json_path, report_paths.markdown_path
    )
    assert not list(tmp_path.rglob("*.part"))
    assert "secret.invalid" not in str(exc_info.value)
    assert "token=" not in str(exc_info.value)


def test_confirmed_summary_warns_manual_index_plan_and_cache_refresh(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)
    summary_path = tmp_path / "summaries" / "gooaye" / "EP700__EP700-Alpha.semantic.md"

    def summary(*args, **kwargs):
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("summary", encoding="utf-8")
        return SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP700",
            title="EP700 Alpha",
            summary_path=summary_path,
            transcript_json_path=transcript_json,
            transcript_text_path=transcript_json.with_suffix(".txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            already_exists=False,
            provider="openai-compatible",
            model=None,
            chunk_count=1,
            evidence_count=1,
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    messages = [warning.message for warning in result.warnings]
    assert any("index" in message and "plan" in message for message in messages)
    assert any("cache" in message for message in messages)
    assert not (tmp_path / "cache").exists()


def test_confirmed_snapshot_exception_writes_bounded_failed_report_and_stops(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    summary_calls = 0

    def explode(*args, **kwargs):
        raise RuntimeError("private transcript https://secret.invalid/?token=secret")

    def summary(*args, **kwargs):
        nonlocal summary_calls
        summary_calls += 1
        raise AssertionError("summary must not run after snapshot failure")

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", explode)
    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.selected_action == "blocked"
    assert result.rows[0].status == "failed"
    assert result.rows[0].failure_category == "RuntimeError"
    assert result.executed_action is None
    assert summary_calls == 0
    assert result.report_json_path is not None and result.report_json_path.exists()
    report_text = result.report_json_path.read_text(encoding="utf-8")
    assert "secret.invalid" not in report_text
    assert "token=secret" not in report_text

def _passing_semantic_review_body() -> str:
    return "\n".join(
        [
            "# Semantic Summary",
            "Summary mode: semantic-llm",
            "Provider: openai-compatible",
            "Model: safe-model",
            "Transcript status: valid",
            "fact [00:00:00 - 00:00:05]",
            "## Chunk Summaries",
            "safe local summary",
        ]
    )


def test_confirmed_review_uses_real_deterministic_core_without_llm(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    import podcast_ingest_core.llm_profiles as llm_profiles
    import podcast_ingest_core.local_env as local_env
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    summary_path = _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    calls = {"summary": 0, "profile": 0, "env": 0, "provider": 0}

    def forbidden(name):
        def call(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"{name} must not run for deterministic review")

        return call

    monkeypatch.setattr(runner, "semantic_summarize_episode", forbidden("summary"))
    monkeypatch.setattr(llm_profiles, "load_llm_profile", forbidden("profile"))
    monkeypatch.setattr(local_env, "load_local_env", forbidden("env"))
    monkeypatch.setattr(semantic_summarizer, "create_provider", forbidden("provider"))

    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_review",
        confirm=True,
        provider="https://ignored.invalid/?token=secret",
        model="ignored secret model",
        base_url="https://ignored.invalid/?token=secret",
        api_key_env="not-inspected",
    )

    assert result.selected_action == "semantic_review"
    assert result.executed_action == "semantic_review"
    assert result.rows[0].status == "executed"
    assert result.rows[0].manual_only is False
    assert result.rows[0].provider is None
    assert result.rows[0].model is None
    assert calls == {"summary": 0, "profile": 0, "env": 0, "provider": 0}
    assert len(result.rows[0].output_paths) == 2
    assert all(Path(path).exists() for path in result.rows[0].output_paths)
    assert str(summary_path) in result.rows[0].planned_reads
    assert result.report_json_path is not None and result.report_json_path.exists()
    serialized = json.dumps(runner.result_to_dict(result), ensure_ascii=False)
    assert "ignored.invalid" not in serialized
    assert "ignored secret model" not in serialized


def test_confirmed_review_action_drift_and_terminal_state_do_not_fallback(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    calls = {"summary": 0, "review": 0}

    def summary(*args, **kwargs):
        calls["summary"] += 1
        raise AssertionError("review drift must not generate summary")

    def review(*args, **kwargs):
        calls["review"] += 1
        raise AssertionError("review drift must not execute review")

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    monkeypatch.setattr(runner, "review_semantic_summary_smoke", review)

    drift = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )
    assert drift.selected_action == "semantic_summary"
    assert drift.rows[0].status == "rejected"
    assert drift.executed_action is None
    assert calls == {"summary": 0, "review": 0}

    _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    _write_semantic_review(monkeypatch, tmp_path, review_status="passed")
    terminal = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )
    assert terminal.selected_action == "completed"
    assert terminal.rows[0].status == "rejected"
    assert terminal.executed_action is None
    assert calls == {"summary": 0, "review": 0}


def test_confirmed_review_real_core_failed_result_is_terminal_manual_only(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(
        monkeypatch,
        tmp_path,
        body=_passing_semantic_review_body() + "\n- Buy ACME now",
    )

    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )

    assert result.executed_action == "semantic_review"
    assert result.rows[0].status == "blocked"
    assert result.rows[0].manual_only is True
    assert result.rows[0].failure_category is None
    assert len(result.rows[0].output_paths) == 2
    review_payload = json.loads(Path(result.rows[0].output_paths[0]).read_text("utf-8"))
    assert review_payload["review_status"] == "failed"


def test_confirmed_review_race_to_missing_summary_maps_real_blocked_result(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    summary_path = _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    real_preview = runner._preview_selection

    def preview_then_remove_summary(podcast_id: str, episode_ref: str):
        selection = real_preview(podcast_id, episode_ref)
        summary_path.unlink()
        return selection

    monkeypatch.setattr(runner, "_preview_selection", preview_then_remove_summary)
    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )

    assert result.selected_action == "semantic_review"
    assert result.executed_action == "semantic_review"
    assert result.rows[0].status == "blocked"
    assert result.rows[0].manual_only is True
    assert len(result.rows[0].output_paths) == 2
    review_payload = json.loads(Path(result.rows[0].output_paths[0]).read_text("utf-8"))
    assert review_payload["review_status"] == "blocked"


def test_duplicate_timestamped_review_uses_latest_state_without_execution(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    older = _write_semantic_review(
        monkeypatch,
        tmp_path,
        review_status="passed",
        timestamp="20260712-010101",
    )
    newer = _write_semantic_review(
        monkeypatch,
        tmp_path,
        review_status="failed",
        timestamp="20260712-020202",
    )
    calls = 0

    def review(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("terminal latest review must not rerun")

    monkeypatch.setattr(runner, "review_semantic_summary_smoke", review)
    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )

    assert result.selected_action == "blocked"
    assert result.rows[0].status == "blocked"
    assert str(newer) in result.rows[0].source_report_paths
    assert str(older) not in result.rows[0].source_report_paths
    assert calls == 0


def test_review_partial_pair_failure_is_category_only_without_rescan_or_cleanup(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    partial_path = review_dir / (
        "20260712-030303__gooaye__EP700.semantic-review.json"
    )
    review_calls = 0

    def partial_review(*args, **kwargs):
        nonlocal review_calls
        review_calls += 1
        partial_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path.write_text("partial review artifact", encoding="utf-8")
        raise OSError(
            "private semantic body https://secret.invalid/?token=secret Traceback"
        )

    monkeypatch.setattr(runner, "review_semantic_summary_smoke", partial_review)
    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )
    serialized = json.dumps(runner.result_to_dict(result), ensure_ascii=False)

    assert review_calls == 1
    assert partial_path.exists()
    assert result.executed_action == "semantic_review"
    assert result.rows[0].status == "failed"
    assert result.rows[0].manual_only is True
    assert result.rows[0].failure_category == "OSError"
    assert result.rows[0].output_paths == []
    assert str(partial_path) not in result.rows[0].output_paths
    assert "secret.invalid" not in serialized
    assert "private semantic body" not in serialized
    assert "Traceback" not in serialized


def test_confirmed_review_report_is_timestamp_free_and_warns_manual_refresh(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )

    result = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    messages = [warning.message for warning in result.warnings]
    assert "generated_at" not in payload
    assert "generated_at" not in markdown
    assert any("index" in message and "plan" in message for message in messages)
    assert any("cache" in message for message in messages)
    assert not (tmp_path / "cache").exists()

def test_semantic_remediation_cli_dry_run_bypasses_profile_env_and_writes(
    monkeypatch, tmp_path: Path, capsys
):
    from scripts import run_corpus_semantic_remediation as cli

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    before = _tree_manifest(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not resolve profile or local env")

    monkeypatch.setattr(cli, "_resolve_llm_options", forbidden)
    monkeypatch.setattr(cli, "_load_local_env_from_args", forbidden)
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--llm-profile",
            "ignored-profile",
            "--env-file",
            "ignored-secret.env",
        ],
    )

    cli.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert captured.err == ""
    assert payload["run_mode"] == "dry_run"
    assert payload["selected_action"] == "semantic_summary"
    assert _tree_manifest(tmp_path) == before


@pytest.mark.parametrize("action", ["semantic_summary", " semantic_summary "])
def test_semantic_remediation_cli_ack_precedes_profile_env_and_core(
    monkeypatch, capsys, action
):
    from scripts import run_corpus_semantic_remediation as cli
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    calls = {"profile": 0, "env": 0, "core": 0}

    def counted(name):
        def call(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"{name} must not run")

        return call

    monkeypatch.setattr(cli, "_resolve_llm_options", counted("profile"))
    monkeypatch.setattr(cli, "_load_local_env_from_args", counted("env"))
    monkeypatch.setattr(cli, "run_corpus_semantic_remediation", counted("core"))
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--action",
            action,
            "--confirm",
            "--api-cost-ack",
            "wrong acknowledgement",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert SEMANTIC_API_COST_ACK in captured.err
    assert "wrong acknowledgement" not in captured.err
    assert calls == {"profile": 0, "env": 0, "core": 0}


def test_semantic_remediation_cli_normalizes_action_before_configuration_and_dispatch(
    monkeypatch, capsys
):
    from scripts import run_corpus_semantic_remediation as cli
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    calls = []
    sentinel = object()

    monkeypatch.setattr(
        cli,
        "_load_local_env_from_args",
        lambda args: calls.append("env"),
    )
    monkeypatch.setattr(
        cli,
        "_resolve_llm_options",
        lambda args: (
            calls.append("profile")
            or ("openai-compatible", "safe-model", None, "OPENAI_API_KEY")
        ),
    )

    def fake_core(podcast_id, **kwargs):
        calls.append((podcast_id, kwargs))
        return sentinel

    monkeypatch.setattr(cli, "run_corpus_semantic_remediation", fake_core)
    monkeypatch.setattr(cli, "result_to_dict", lambda result: {"ok": result is sentinel})
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--action",
            " semantic_summary ",
            "--confirm",
            "--api-cost-ack",
            SEMANTIC_API_COST_ACK,
            "--llm-profile",
            "controlled",
        ],
    )

    cli.main()
    payload = json.loads(capsys.readouterr().out)
    captured_call = calls[-1]

    assert calls[:2] == ["env", "profile"]
    assert captured_call[0] == "gooaye"
    assert captured_call[1]["action"] == "semantic_summary"
    assert payload == {"ok": True}


def test_semantic_remediation_cli_confirmed_summary_resolves_controlled_options_after_ack(
    monkeypatch, tmp_path: Path, capsys
):
    from scripts import run_corpus_semantic_remediation as cli
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    calls = []

    monkeypatch.setattr(
        cli,
        "_load_local_env_from_args",
        lambda args: calls.append("env"),
    )
    monkeypatch.setattr(
        cli,
        "_resolve_llm_options",
        lambda args: (
            calls.append("profile")
            or ("openai-compatible", "safe-model", "https://private.invalid/v1", "OPENAI_API_KEY")
        ),
    )

    def fake_core(podcast_id, **kwargs):
        calls.append((podcast_id, kwargs))
        return runner.run_corpus_semantic_remediation(
            podcast_id,
            episode_ref=kwargs["episode_ref"],
            action="next",
            confirm=False,
            provider=kwargs["provider"],
            model=kwargs["model"],
        )

    monkeypatch.setattr(cli, "run_corpus_semantic_remediation", fake_core)
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--action",
            "semantic_summary",
            "--confirm",
            "--api-cost-ack",
            SEMANTIC_API_COST_ACK,
            "--llm-profile",
            "controlled",
            "--reasoning-effort",
            "medium",
            "--read-timeout-seconds",
            "600",
        ],
    )

    cli.main()
    payload = json.loads(capsys.readouterr().out)
    captured_call = calls[-1]

    assert calls[:2] == ["env", "profile"]
    assert captured_call[0] == "gooaye"
    assert captured_call[1]["confirm"] is True
    assert captured_call[1]["action"] == "semantic_summary"
    assert captured_call[1]["api_cost_ack"] is SEMANTIC_API_COST_ACK
    assert captured_call[1]["provider"] == "openai-compatible"
    assert captured_call[1]["model"] == "safe-model"
    assert captured_call[1]["base_url"] == "https://private.invalid/v1"
    assert captured_call[1]["api_key_env"] == "OPENAI_API_KEY"
    assert captured_call[1]["reasoning_effort"] == "medium"
    assert captured_call[1]["read_timeout_seconds"] == 600
    assert payload["run_mode"] == "dry_run"
    assert "private.invalid" not in json.dumps(payload)


def test_semantic_remediation_cli_confirmed_review_bypasses_all_llm_resolution(
    monkeypatch, tmp_path: Path, capsys
):
    from scripts import run_corpus_semantic_remediation as cli
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )
    captured_kwargs = {}

    def forbidden(*args, **kwargs):
        raise AssertionError("review must bypass LLM resolution")

    def fake_core(podcast_id, **kwargs):
        captured_kwargs.update(kwargs)
        return runner.run_corpus_semantic_remediation(
            podcast_id,
            episode_ref=kwargs["episode_ref"],
            action="next",
            confirm=False,
        )

    monkeypatch.setattr(cli, "_resolve_llm_options", forbidden)
    monkeypatch.setattr(cli, "_load_local_env_from_args", forbidden)
    monkeypatch.setattr(cli, "run_corpus_semantic_remediation", fake_core)
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--action",
            "semantic_review",
            "--confirm",
            "--llm-profile",
            "ignored",
            "--provider",
            "https://ignored.invalid/?token=secret",
            "--model",
            "ignored secret model",
            "--base-url",
            "https://ignored.invalid/?token=secret",
            "--api-key-env",
            "ignored",
        ],
    )

    cli.main()
    captured = capsys.readouterr()

    assert json.loads(captured.out)["selected_action"] == "semantic_review"
    assert captured.err == ""
    assert captured_kwargs["confirm"] is True
    assert captured_kwargs["action"] == "semantic_review"


def test_015_stale_review_remains_manual_only_without_a_collision_rereview(
    monkeypatch, tmp_path: Path
):
    """Only 018 owns automatic authenticity rereview; 015 remains terminal."""
    from datetime import datetime as real_datetime
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    import podcast_ingest_core.semantic_summary_smoke_review as semantic_review

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    summary_path = _write_semantic_summary(
        monkeypatch, tmp_path, body=_passing_semantic_review_body()
    )

    class FixedDateTime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 7, 22, 12, 0, 0)

    monkeypatch.setattr(semantic_review, "datetime", FixedDateTime)

    first = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )
    summary_path.write_text(
        _passing_semantic_review_body() + "\nupdated safe statement",
        encoding="utf-8",
    )
    second = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=True
    )
    final_preview = runner.run_corpus_semantic_remediation(
        "gooaye", episode_ref="EP700", action="semantic_review", confirm=False
    )

    assert first.rows[0].status == "executed"
    assert second.selected_action == "blocked"
    assert second.executed_action is None
    assert second.rows[0].status == "blocked"
    review_names = sorted(
        path.name
        for path in (tmp_path / "evals" / "research-llm-smoke" / "reports").glob("*.json")
    )
    assert review_names == [
        "20260722-120000__gooaye__EP700.semantic-review.json",
    ]
    assert final_preview.selected_action == "blocked"


def test_semantic_remediation_cli_exit_and_error_no_leak_contract(
    monkeypatch, capsys
):
    from scripts import run_corpus_semantic_remediation as cli
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    cases = [
        (
            CorpusSemanticRemediationRunnerFailedError("invalid episode_ref"),
            "invalid episode_ref",
        ),
        (
            RuntimeError(
                "private transcript https://secret.invalid/?token=secret Traceback"
            ),
            "RuntimeError",
        ),
    ]
    for error, expected in cases:
        monkeypatch.setattr(
            cli,
            "run_corpus_semantic_remediation",
            lambda *args, _error=error, **kwargs: (_ for _ in ()).throw(_error),
        )
        monkeypatch.setattr(
            cli.sys,
            "argv",
            [
                "run_corpus_semantic_remediation.py",
                "--podcast",
                "gooaye",
                "--episode",
                "EP700",
            ],
        )
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        captured = capsys.readouterr()
        assert exc_info.value.code == 1
        assert captured.out == ""
        assert expected in captured.err
        assert "secret.invalid" not in captured.err
        assert "token=secret" not in captured.err
        assert "private transcript" not in captured.err
        assert "Traceback" not in captured.err


def test_semantic_remediation_cli_has_no_force_partial_or_automation_surface():
    from scripts import run_corpus_semantic_remediation as cli

    option_strings = {
        option
        for action in cli.build_parser()._actions
        for option in action.option_strings
    }

    assert "--force" not in option_strings
    assert "--allow-partial" not in option_strings
    assert "--batch" not in option_strings
    assert "--retry" not in option_strings
    assert "--schedule" not in option_strings
    assert "--automatic-review" not in option_strings


def test_unsafe_provider_and_model_are_rejected_without_leaking_values(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core import CorpusSemanticRemediationRunnerFailedError

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    for kwargs in (
        {"provider": "https://secret.invalid/?token=value"},
        {"model": "secret-model"},
        {"model": "buy-recommendation"},
    ):
        with pytest.raises(CorpusSemanticRemediationRunnerFailedError) as exc_info:
            runner.run_corpus_semantic_remediation(
                "gooaye", episode_ref="EP700", **kwargs
            )
        message = str(exc_info.value)
        assert "secret.invalid" not in message
        assert "token=" not in message
        assert "buy-recommendation" not in message


def test_safe_cjk_local_paths_are_preserved_in_preview(monkeypatch, tmp_path: Path):
    from podcast_ingest_core import run_corpus_semantic_remediation, storage

    cjk_root = tmp_path / "測試資料"
    _use_tmp_data_dirs(monkeypatch, cjk_root)
    _write_seed(monkeypatch, cjk_root, title="中文標題")
    transcript_json = _write_transcript(
        monkeypatch, cjk_root, title="中文標題"
    )

    result = run_corpus_semantic_remediation("gooaye", episode_ref="EP700")

    assert str(transcript_json) in result.rows[0].planned_reads
    assert any("中文標題" in path for path in result.rows[0].planned_writes)


def test_015_never_calls_cache_rebuild_or_010_014_runners(
    monkeypatch, tmp_path: Path
):
    import podcast_ingest_core.cache as cache
    import podcast_ingest_core.corpus_episode_workflow_runner as workflow_runner
    import podcast_ingest_core.corpus_remediation_runner as remediation_runner
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    transcript_json = _write_transcript(monkeypatch, tmp_path)
    summary_path = tmp_path / "summaries" / "gooaye" / "EP700__EP700-Alpha.semantic.md"

    def forbidden(*args, **kwargs):
        raise AssertionError("excluded integration surface was called")

    monkeypatch.setattr(cache, "rebuild_cache", forbidden)
    monkeypatch.setattr(workflow_runner, "run_corpus_episode_workflow", forbidden)
    monkeypatch.setattr(remediation_runner, "run_corpus_remediation", forbidden)

    def summary(*args, **kwargs):
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("summary", encoding="utf-8")
        return SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP700",
            title="EP700 Alpha",
            summary_path=summary_path,
            transcript_json_path=transcript_json,
            transcript_text_path=transcript_json.with_suffix(".txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            already_exists=False,
            provider="openai-compatible",
            model=None,
            chunk_count=1,
            evidence_count=1,
        )

    monkeypatch.setattr(runner, "semantic_summarize_episode", summary)
    result = runner.run_corpus_semantic_remediation(
        "gooaye",
        episode_ref="EP700",
        action="semantic_summary",
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.rows[0].status == "executed"
    assert not (tmp_path / "cache").exists()

def test_cli_runner_contained_failed_outcome_uses_exit_zero(
    monkeypatch, tmp_path: Path, capsys
):
    from scripts import run_corpus_semantic_remediation as cli
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner
    from podcast_ingest_core.semantic_summarizer import SEMANTIC_API_COST_ACK

    _write_seed(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "_load_local_env_from_args", lambda args: None)
    monkeypatch.setattr(
        cli,
        "_resolve_llm_options",
        lambda args: ("openai-compatible", None, None, "OPENAI_API_KEY"),
    )
    monkeypatch.setattr(
        runner,
        "semantic_summarize_episode",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("private transcript raw response sk-test-secret-value")
        ),
    )
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
            "--action",
            "semantic_summary",
            "--confirm",
            "--api-cost-ack",
            SEMANTIC_API_COST_ACK,
        ],
    )

    cli.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["rows"][0]["status"] == "failed"
    assert payload["rows"][0]["failure_category"] == "RuntimeError"
    assert "private transcript" not in captured.out
    assert "raw response" not in captured.out
    assert "sk-test-secret-value" not in captured.out
    assert "Traceback" not in captured.err


def test_015_module_has_no_010_014_mcp_or_cache_imports():
    import podcast_ingest_core.corpus_semantic_remediation_runner as runner

    source = inspect.getsource(runner)

    assert "corpus_remediation_runner" not in source
    assert "corpus_episode_workflow_runner" not in source
    assert "mcp_server" not in source
    assert "rebuild_cache" not in source
    assert "stock_lens" not in source
