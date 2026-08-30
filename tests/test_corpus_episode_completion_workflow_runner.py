from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> None:
    import corpus_ingest_core.corpus_index as corpus_index
    import corpus_ingest_core.semantic_summary_smoke_review as semantic_review
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus", raising=False)
    monkeypatch.setattr(
        corpus_index,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )
    monkeypatch.setattr(
        semantic_review,
        "REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )


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


def _write_seed(*, has_audio_url: bool = True) -> None:
    from corpus_ingest_core import storage

    path = storage.corpus_episode_seed_asset_path("gooaye", "EP677")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": "EP677 Alpha",
                "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
                "duration": "00:42:00",
                "guid_status": "present",
                "has_audio_url": has_audio_url,
                "seed_source": "rss",
                "selector": "latest",
                "warning_count": 0,
                "warnings": [],
                "not_investment_advice": True,
            }
        ),
        encoding="utf-8",
    )


def _write_local_audio() -> None:
    from corpus_ingest_core import storage

    path = storage.AUDIO_DIR / "gooaye" / "EP677__EP677 Alpha.mp3"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"mp3")


def _write_transcript() -> None:
    from corpus_ingest_core import storage

    paths = storage.transcript_asset_paths("gooaye", "EP677", "EP677 Alpha")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": "EP677 Alpha",
                "language": "zh",
                "segment_count": 1,
                "last_segment_end_seconds": 5.5,
                "completed": True,
                "segments": [
                    {
                        "id": 1,
                        "start": 0.0,
                        "end": 5.5,
                        "text": "private transcript sentinel",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths.text_path.write_text("private transcript sentinel", encoding="utf-8")
    paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:05,500\nprivate\n",
        encoding="utf-8",
    )


def _write_deterministic_artifacts() -> None:
    from corpus_ingest_core import storage

    title = "EP677 Alpha"
    summary_path = storage.summary_asset_path("gooaye", "EP677", title)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("# deterministic summary", encoding="utf-8")

    mentions = storage.mention_asset_paths("gooaye", "EP677", title)
    mentions.json_path.parent.mkdir(parents=True, exist_ok=True)
    mentions.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": title,
                "mention_count": 0,
                "mentions": [],
            }
        ),
        encoding="utf-8",
    )
    mentions.markdown_path.write_text("# mentions", encoding="utf-8")

    intelligence = storage.episode_intelligence_report_asset_paths("gooaye", "EP677", title)
    intelligence.json_path.parent.mkdir(parents=True, exist_ok=True)
    intelligence.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": title,
                "report_status": "final",
                "transcript_validation": {"status": "valid", "segment_count": 1},
            }
        ),
        encoding="utf-8",
    )
    intelligence.markdown_path.write_text("# intelligence", encoding="utf-8")

    mapping = storage.industry_chain_mapping_asset_paths("gooaye", "EP677", title)
    mapping.json_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": title,
                "mapping_status": "final",
                "industry_chain_nodes": [],
                "stock_candidates": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    mapping.markdown_path.write_text("# mapping", encoding="utf-8")

    external = storage.external_data_boundary_asset_paths("gooaye", "EP677", title)
    external.json_path.parent.mkdir(parents=True, exist_ok=True)
    external.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": title,
                "boundary_status": "final",
                "candidate_boundaries": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    external.markdown_path.write_text("# external", encoding="utf-8")


def _write_semantic_summary() -> None:
    from corpus_ingest_core import storage

    path = storage.semantic_summary_asset_path("gooaye", "EP677", "EP677 Alpha")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# safe semantic fixture", encoding="utf-8")


def _write_passing_semantic_review(tmp_path: Path) -> None:
    from corpus_ingest_core.semantic_summary_smoke_review import (
        review_semantic_summary_smoke,
    )

    # Produce the fixture through the production writer/evaluator rather than a
    # self-authored all-pass payload.
    review_semantic_summary_smoke("gooaye", "EP677")


def _write_stale_corpus_sentinels() -> dict[Path, bytes]:
    from corpus_ingest_core import storage

    asset_pairs = (
        storage.corpus_index_asset_paths("gooaye"),
        storage.corpus_remediation_plan_asset_paths("gooaye"),
        storage.corpus_remediation_run_asset_paths("gooaye"),
        storage.corpus_local_transcription_run_asset_paths("gooaye"),
        storage.corpus_audio_download_run_asset_paths("gooaye"),
        storage.corpus_episode_intake_run_asset_paths("gooaye"),
        storage.corpus_episode_workflow_run_asset_paths("gooaye"),
        storage.corpus_semantic_remediation_run_asset_paths("gooaye"),
        storage.corpus_episode_completion_workflow_run_asset_paths("gooaye"),
    )
    sentinels: dict[Path, bytes] = {}
    for index, paths in enumerate(asset_pairs):
        for path in (paths.json_path, paths.markdown_path):
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = (
                json.dumps(
                    {
                        "sentinel": f"stale-{index}",
                        "episodes": [],
                        "selected_action": "completed",
                    }
                ).encode("utf-8")
                if path.suffix == ".json"
                else f"# stale sentinel {index}\n".encode()
            )
            path.write_bytes(payload)
            sentinels[path] = payload
    return sentinels


def _install_rss_episode(monkeypatch) -> None:
    import corpus_ingest_core.corpus_episode_intake as intake
    from corpus_ingest_core.models import Episode

    monkeypatch.setattr(
        intake,
        "get_episode",
        lambda podcast_id, selector: Episode(
            podcast_id=podcast_id,
            episode_ref="EP677",
            title="EP677 Alpha",
            audio_url="https://example.invalid/episode.mp3",
        ),
    )


def _selected_completion_row(action: str):
    from corpus_ingest_core.models import CorpusEpisodeCompletionWorkflowRunRow

    return CorpusEpisodeCompletionWorkflowRunRow(
        episode_ref="EP677",
        action=action,
        status="selected",
        reason="next action is ready",
        requires_confirmation=True,
        requires_api_cost_ack=False,
        network_risk=False,
        local_compute_risk=False,
        transcript_transfer_risk=False,
        may_incur_api_cost=False,
        manual_only=False,
        planned_reads=["in-memory corpus snapshot"],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
        provider=None,
        model=None,
        failure_category=None,
        warnings=[],
    )


def test_completion_workflow_public_signature_and_exports():
    import corpus_ingest_core as core

    expected = [
        "podcast_id",
        "episode_ref",
        "action",
        "confirm",
        "api_cost_ack",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
        "semantic_provider",
        "semantic_model",
        "semantic_base_url",
        "semantic_api_key_env",
        "semantic_chunk_seconds",
        "semantic_max_segments_per_chunk",
        "progress_callback",
    ]
    signature = inspect.signature(core.run_corpus_episode_completion_workflow)

    assert list(signature.parameters) == expected
    assert signature.parameters["episode_ref"].default == "latest"
    assert signature.parameters["action"].default == "next"
    assert signature.parameters["confirm"].default is False
    assert signature.parameters["api_cost_ack"].default == ""
    assert signature.parameters["transcription_model"].default is None
    assert signature.parameters["transcription_device"].default == "cpu"
    assert signature.parameters["transcription_compute_type"].default == "int8"
    assert signature.parameters["transcription_vad_filter"].default is False
    assert signature.parameters["semantic_provider"].default == "openai-compatible"
    assert signature.parameters["semantic_model"].default is None
    assert signature.parameters["semantic_base_url"].default is None
    assert signature.parameters["semantic_api_key_env"].default == "OPENAI_API_KEY"
    assert signature.parameters["semantic_chunk_seconds"].default == 600
    assert signature.parameters["semantic_max_segments_per_chunk"].default == 120
    assert signature.parameters["progress_callback"].default is None
    assert core.CorpusEpisodeCompletionWorkflowRunnerFailedError.__name__ == (
        "CorpusEpisodeCompletionWorkflowRunnerFailedError"
    )
    assert callable(core.corpus_episode_completion_workflow_result_to_dict)


def test_completion_workflow_model_field_contracts():
    from corpus_ingest_core import (
        CorpusEpisodeCompletionWorkflowRunCounts,
        CorpusEpisodeCompletionWorkflowRunFilter,
        CorpusEpisodeCompletionWorkflowRunResult,
        CorpusEpisodeCompletionWorkflowRunRow,
        CorpusEpisodeCompletionWorkflowRunWarning,
    )

    assert [field.name for field in fields(CorpusEpisodeCompletionWorkflowRunFilter)] == [
        "episode_ref",
        "action",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
        "semantic_provider",
        "semantic_model",
        "semantic_chunk_seconds",
        "semantic_max_segments_per_chunk",
    ]
    assert [field.name for field in fields(CorpusEpisodeCompletionWorkflowRunCounts)] == [
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
    assert [field.name for field in fields(CorpusEpisodeCompletionWorkflowRunWarning)] == [
        "scope",
        "episode_ref",
        "message",
    ]
    assert [field.name for field in fields(CorpusEpisodeCompletionWorkflowRunRow)] == [
        "episode_ref",
        "action",
        "status",
        "reason",
        "requires_confirmation",
        "requires_api_cost_ack",
        "network_risk",
        "local_compute_risk",
        "transcript_transfer_risk",
        "may_incur_api_cost",
        "manual_only",
        "planned_reads",
        "planned_writes",
        "output_paths",
        "source_report_paths",
        "stage_counts",
        "provider",
        "model",
        "failure_category",
        "warnings",
    ]
    assert [field.name for field in fields(CorpusEpisodeCompletionWorkflowRunResult)] == [
        "podcast_id",
        "run_mode",
        "confirm",
        "selector",
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


def test_completion_workflow_storage_paths_do_not_create_directories(monkeypatch, tmp_path: Path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus", raising=False)

    paths = storage.corpus_episode_completion_workflow_run_asset_paths("gooaye")

    assert paths.json_path == (tmp_path / "corpus" / "gooaye" / "corpus-episode-completion-workflow-run.json")
    assert paths.markdown_path == (tmp_path / "corpus" / "gooaye" / "corpus-episode-completion-workflow-run.md")
    assert not (tmp_path / "corpus").exists()


def test_dry_run_unseeded_latest_selects_intake_without_writes(monkeypatch, tmp_path: Path):
    import corpus_ingest_core.corpus_episode_intake as intake
    from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
        run_corpus_episode_completion_workflow,
    )
    from corpus_ingest_core.models import Episode

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        intake,
        "get_episode",
        lambda podcast_id, selector: Episode(
            podcast_id=podcast_id,
            episode_ref="EP677",
            title="EP677 Alpha",
            audio_url="https://example.invalid/episode.mp3",
        ),
    )
    before = _tree_manifest(tmp_path)

    result = run_corpus_episode_completion_workflow("gooaye")

    assert result.run_mode == "dry_run"
    assert result.episode_ref == "EP677"
    assert result.selected_action == "intake"
    assert result.executed_action is None
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert result.rows[0].action == "intake"
    assert result.rows[0].status == "selected"
    assert _tree_manifest(tmp_path) == before


@pytest.mark.parametrize(
    ("corpus_state", "expected_action"),
    (
        ("seeded_missing_audio", "audio_download"),
        ("local_audio", "local_transcription"),
        ("transcript_ready", "deterministic_remediation"),
        ("deterministic_complete", "semantic_summary"),
        ("semantic_summary_complete", "semantic_review"),
        ("semantic_review_passed", "completed"),
        ("blocked_no_audio_url", "blocked"),
    ),
)
def test_dry_run_uses_real_snapshot_ladder_without_writes(
    monkeypatch,
    tmp_path: Path,
    corpus_state: str,
    expected_action: str,
):
    from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
        run_corpus_episode_completion_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_rss_episode(monkeypatch)
    _write_seed(has_audio_url=corpus_state != "blocked_no_audio_url")
    if corpus_state in {
        "local_audio",
        "transcript_ready",
        "deterministic_complete",
        "semantic_summary_complete",
        "semantic_review_passed",
    }:
        _write_local_audio()
    if corpus_state in {
        "transcript_ready",
        "deterministic_complete",
        "semantic_summary_complete",
        "semantic_review_passed",
    }:
        _write_transcript()
    if corpus_state in {
        "deterministic_complete",
        "semantic_summary_complete",
        "semantic_review_passed",
    }:
        _write_deterministic_artifacts()
    if corpus_state in {"semantic_summary_complete", "semantic_review_passed"}:
        _write_semantic_summary()
    if corpus_state == "semantic_review_passed":
        _write_passing_semantic_review(tmp_path)
    before = _tree_manifest(tmp_path)

    result = run_corpus_episode_completion_workflow("gooaye", episode_ref="EP677")

    assert result.episode_ref == "EP677"
    assert result.selected_action == expected_action
    assert result.rows[0].action == expected_action
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    if expected_action == "semantic_summary":
        assert result.rows[0].network_risk is True
        assert result.rows[0].transcript_transfer_risk is True
        assert result.rows[0].may_incur_api_cost is True
    assert _tree_manifest(tmp_path) == before


@pytest.mark.parametrize("defect", ("unreadable", "unknown", "forged", "stale"))
def test_contract_inauthentic_review_is_manual_only_for_dry_run_and_confirmation(
    monkeypatch, tmp_path: Path, defect: str
):
    from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
        run_corpus_episode_completion_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_rss_episode(monkeypatch)
    _write_seed()
    _write_local_audio()
    _write_transcript()
    _write_deterministic_artifacts()
    _write_semantic_summary()
    _write_passing_semantic_review(tmp_path)
    review_path = next((tmp_path / "evals" / "research-llm-smoke" / "reports").glob("*.json"))
    if defect == "unreadable":
        review_path.write_bytes(b"{not-json")
    elif defect == "unknown":
        review_path.write_text(json.dumps({"review_status": "available"}), encoding="utf-8")
    else:
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
        if defect == "forged":
            review_payload["review_boundary"] = "forged-review-boundary"
        else:
            review_payload["semantic_summary_sha256"] = "0" * 64
        review_path.write_text(json.dumps(review_payload), encoding="utf-8")
    before = _tree_manifest(tmp_path)

    preview = run_corpus_episode_completion_workflow("gooaye", episode_ref="EP677")
    confirmed = run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="semantic_review",
        confirm=True,
    )

    assert preview.selected_action == "blocked"
    assert preview.rows[0].status == "blocked"
    assert preview.rows[0].manual_only is True
    assert confirmed.selected_action == "blocked"
    assert confirmed.executed_action is None
    assert confirmed.rows[0].status == "blocked"
    assert confirmed.report_json_path is None
    assert confirmed.report_markdown_path is None
    assert _tree_manifest(tmp_path) == before


def test_dry_run_ignores_stale_sentinels_and_reaches_no_side_effect_surface(
    monkeypatch,
    tmp_path: Path,
):
    import corpus_ingest_core.corpus_audio_download_runner as audio_runner
    import corpus_ingest_core.corpus_episode_intake as intake_runner
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow_runner
    import corpus_ingest_core.corpus_index as corpus_index
    import corpus_ingest_core.corpus_local_transcription_runner as transcription_runner
    import corpus_ingest_core.corpus_remediation_plan as remediation_plan
    import corpus_ingest_core.corpus_remediation_runner as remediation_runner
    import corpus_ingest_core.corpus_semantic_remediation_runner as semantic_runner
    from corpus_ingest_core.corpus_episode_completion_workflow_runner import (
        run_corpus_episode_completion_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_rss_episode(monkeypatch)
    _write_seed()
    sentinels = _write_stale_corpus_sentinels()
    writer_calls: list[str] = []
    for label, module, name in (
        ("008", corpus_index, "_write_index"),
        ("009", remediation_plan, "_write_plan"),
        ("010", remediation_runner, "_write_run_report"),
        ("011", transcription_runner, "_write_run_report"),
        ("012", audio_runner, "_write_run_report"),
        ("013", intake_runner, "_write_run_report"),
        ("014", workflow_runner, "_write_run_report"),
        ("015", semantic_runner, "_write_run_report"),
    ):

        def forbidden_writer(*args, _label=label, **kwargs):
            writer_calls.append(_label)
            pytest.fail(f"dry-run reached writer {_label}")

        monkeypatch.setattr(module, name, forbidden_writer)

    def forbidden_execution(*args, **kwargs):
        pytest.fail("dry-run reached a side-effect executor")

    monkeypatch.setattr(audio_runner, "download_audio", forbidden_execution)
    monkeypatch.setattr(transcription_runner, "transcribe_episode", forbidden_execution)
    for name in (
        "summarize_episode",
        "extract_mentions",
        "generate_episode_intelligence_report",
        "generate_industry_chain_mapping",
        "generate_external_data_boundary",
    ):
        monkeypatch.setattr(remediation_runner, name, forbidden_execution)
    monkeypatch.setattr(semantic_runner, "semantic_summarize_episode", forbidden_execution)
    monkeypatch.setattr(semantic_runner, "review_semantic_summary_smoke", forbidden_execution)
    before = _tree_manifest(tmp_path)

    result = run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        progress_callback=forbidden_execution,
    )

    assert result.selected_action == "audio_download"
    assert writer_calls == []
    assert _tree_manifest(tmp_path) == before
    assert all(path.read_bytes() == payload for path, payload in sentinels.items())
    assert not list(tmp_path.rglob("*.part"))


def test_seeded_preview_reuses_one_snapshot_for_deterministic_and_semantic(
    monkeypatch,
    tmp_path: Path,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_seed()
    index_snapshot = SimpleNamespace(result=object(), payload={"index": "fresh"})
    plan_snapshot = SimpleNamespace(
        result=object(),
        payload={"episodes": [{"episode_ref": "EP677"}]},
    )
    build_calls: list[tuple] = []
    preview_calls: list[tuple] = []
    semantic_row = SimpleNamespace(
        planned_reads=["in-memory corpus snapshot"],
        planned_writes=[str(tmp_path / "summaries" / "semantic.md")],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
    )

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: SimpleNamespace(
            resolved_episode_ref="EP677",
            rows=[],
        ),
    )

    def build_index(podcast_id: str):
        build_calls.append(("index", podcast_id))
        return index_snapshot

    def build_plan(podcast_id: str, *, index_result, index_payload):
        build_calls.append(
            (
                "plan",
                podcast_id,
                index_result is index_snapshot.result,
                index_payload is index_snapshot.payload,
            )
        )
        return plan_snapshot

    def deterministic_preview(podcast_id: str, **kwargs):
        preview_calls.append(
            (
                "deterministic",
                podcast_id,
                kwargs["plan_result"] is plan_snapshot.result,
                kwargs["plan_payload"] is plan_snapshot.payload,
                kwargs["max_actions"],
                kwargs["allow_semantic_handoff"],
            )
        )
        return {"selected_stage": "completed", "rows": []}

    def semantic_preview(podcast_id: str, episode_ref: str, **kwargs):
        preview_calls.append(
            (
                "semantic",
                podcast_id,
                episode_ref,
                kwargs["plan_payload"] is plan_snapshot.payload,
            )
        )
        return semantic_row, "semantic_summary", []

    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", build_index)
    monkeypatch.setattr(runner, "_build_corpus_remediation_plan_snapshot", build_plan)
    monkeypatch.setattr(
        runner,
        "_preview_corpus_episode_workflow_from_snapshot",
        deterministic_preview,
    )
    monkeypatch.setattr(
        runner,
        "_preview_corpus_semantic_remediation_from_snapshot",
        semantic_preview,
    )

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
    )

    assert result.selected_action == "semantic_summary"
    assert build_calls == [
        ("index", "gooaye"),
        ("plan", "gooaye", True, True),
    ]
    assert preview_calls == [
        ("deterministic", "gooaye", True, True, 1, True),
        ("semantic", "gooaye", "EP677", True),
    ]


@pytest.mark.parametrize(
    ("podcast_id", "options", "message"),
    (
        ("bad/id", {}, "podcast_id"),
        ("gooaye", {"episode_ref": "../EP677"}, "episode_ref"),
        ("gooaye", {"episode_ref": "latest-2"}, "episode_ref"),
        ("gooaye", {"action": "all"}, "action"),
        (
            "gooaye",
            {"action": "semantic_summary", "semantic_chunk_seconds": 0},
            "semantic_chunk_seconds",
        ),
        (
            "gooaye",
            {
                "action": "semantic_summary",
                "semantic_max_segments_per_chunk": 0,
            },
            "semantic_max_segments_per_chunk",
        ),
    ),
)
def test_preview_rejects_unsafe_common_request_before_selection(
    monkeypatch,
    podcast_id: str,
    options: dict[str, object],
    message: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    def unexpected_read(*args, **kwargs):
        pytest.fail("invalid request reached RSS or snapshot selection")

    monkeypatch.setattr(runner, "run_corpus_episode_intake", unexpected_read)

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError, match=message):
        runner.run_corpus_episode_completion_workflow(podcast_id, **options)


@pytest.mark.parametrize("transcript_state", ("partial", "empty", "incomplete"))
def test_invalid_transcript_blocks_before_semantic_preview(
    monkeypatch,
    tmp_path: Path,
    transcript_state: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_rss_episode(monkeypatch)
    _write_seed()
    _write_local_audio()
    _write_transcript()
    transcript_path = storage.transcript_asset_paths("gooaye", "EP677", "EP677 Alpha").json_path
    payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    if transcript_state == "partial":
        payload["segment_count"] = 2
    elif transcript_state == "empty":
        payload["segments"] = []
        payload["segment_count"] = 0
        payload["last_segment_end_seconds"] = 0.0
    else:
        payload["completed"] = False
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    def unexpected_semantic_preview(*args, **kwargs):
        pytest.fail("invalid transcript reached semantic preview")

    monkeypatch.setattr(
        runner,
        "_preview_corpus_semantic_remediation_from_snapshot",
        unexpected_semantic_preview,
    )
    before = _tree_manifest(tmp_path)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
    )

    assert result.selected_action == "blocked"
    assert result.rows[0].status == "blocked"
    assert result.rows[0].manual_only is True
    assert _tree_manifest(tmp_path) == before


@pytest.mark.parametrize("failure_point", ("selector", "snapshot"))
def test_preview_failure_fails_closed_without_raw_dependency_leak(
    monkeypatch,
    tmp_path: Path,
    failure_point: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    raw_error = RuntimeError("https://invalid.example/?token=leak-token raw body")
    downstream_calls: list[str] = []
    if failure_point == "selector":
        monkeypatch.setattr(
            runner,
            "run_corpus_episode_intake",
            lambda *args, **kwargs: (_ for _ in ()).throw(raw_error),
        )
    else:
        _install_rss_episode(monkeypatch)
        _write_seed()
        monkeypatch.setattr(
            runner,
            "_build_corpus_index_snapshot",
            lambda *args, **kwargs: (_ for _ in ()).throw(raw_error),
        )

    def unexpected_downstream(*args, **kwargs):
        downstream_calls.append("called")
        pytest.fail("preview continued after a fail-closed boundary")

    monkeypatch.setattr(
        runner,
        "_preview_corpus_episode_workflow_from_snapshot",
        unexpected_downstream,
    )
    monkeypatch.setattr(
        runner,
        "_preview_corpus_semantic_remediation_from_snapshot",
        unexpected_downstream,
    )
    before = _tree_manifest(tmp_path)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
    )

    assert result.selected_action == "blocked"
    assert result.rows[0].status == "failed"
    assert result.rows[0].failure_category == "RuntimeError"
    assert downstream_calls == []
    serialized = repr(result)
    for forbidden in ("https://", "token", "leak-token", "raw body", "traceback"):
        assert forbidden not in serialized
    assert _tree_manifest(tmp_path) == before


@pytest.mark.parametrize("failure_point", ("deterministic", "semantic"))
def test_preview_probe_failure_fails_closed_without_later_dispatch(
    monkeypatch,
    tmp_path: Path,
    failure_point: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_seed()
    index_snapshot = SimpleNamespace(result=object(), payload={"index": "fresh"})
    plan_snapshot = SimpleNamespace(result=object(), payload={"episodes": []})
    raw_error = RuntimeError("https://invalid.example/?token=leak-token raw body")
    later_calls: list[str] = []

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: SimpleNamespace(resolved_episode_ref="EP677", rows=[]),
    )
    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", lambda *args: index_snapshot)
    monkeypatch.setattr(
        runner,
        "_build_corpus_remediation_plan_snapshot",
        lambda *args, **kwargs: plan_snapshot,
    )
    if failure_point == "deterministic":
        monkeypatch.setattr(
            runner,
            "_preview_corpus_episode_workflow_from_snapshot",
            lambda *args, **kwargs: (_ for _ in ()).throw(raw_error),
        )
        monkeypatch.setattr(
            runner,
            "_preview_corpus_semantic_remediation_from_snapshot",
            lambda *args, **kwargs: pytest.fail("semantic preview must not run after deterministic probe failure"),
        )
    else:
        monkeypatch.setattr(
            runner,
            "_preview_corpus_episode_workflow_from_snapshot",
            lambda *args, **kwargs: {"selected_stage": "completed", "rows": []},
        )
        monkeypatch.setattr(
            runner,
            "_preview_corpus_semantic_remediation_from_snapshot",
            lambda *args, **kwargs: (_ for _ in ()).throw(raw_error),
        )

    def unexpected_executor(*args, **kwargs):
        later_calls.append("executor")
        pytest.fail("dry-run reached a stage executor")

    monkeypatch.setattr(runner, "run_corpus_audio_download", unexpected_executor)
    before = _tree_manifest(tmp_path)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
    )

    assert result.selected_action == "blocked"
    assert result.rows[0].status == "failed"
    assert result.rows[0].failure_category == "RuntimeError"
    assert later_calls == []
    assert _tree_manifest(tmp_path) == before


def test_result_to_dict_is_json_compatible_and_bounded(monkeypatch, tmp_path: Path):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_rss_episode(monkeypatch)

    result = runner.run_corpus_episode_completion_workflow("gooaye")
    payload = runner.result_to_dict(result)

    assert payload["podcast_id"] == "gooaye"
    assert payload["selected_action"] == "intake"
    assert payload["row_count"] == 1
    assert payload["selected_count"] == 1
    assert "counts" not in payload
    assert payload["not_investment_advice"] is True
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in ("https://", "token", "secret", "private transcript"):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    ("options", "message"),
    (
        ({"episode_ref": "EP677", "action": "next", "confirm": True}, "action"),
        (
            {"episode_ref": "latest", "action": "intake", "confirm": True},
            "episode_ref",
        ),
        (
            {
                "episode_ref": "EP677",
                "action": "semantic_summary",
                "confirm": True,
                "api_cost_ack": "wrong acknowledgement",
            },
            "api_cost_ack",
        ),
    ),
)
def test_confirmed_early_guards_precede_all_selection_work(
    monkeypatch,
    options: dict[str, object],
    message: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    def unexpected_work(*args, **kwargs):
        pytest.fail("invalid confirmed request reached selection or writing")

    monkeypatch.setattr(runner, "run_corpus_episode_intake", unexpected_work)
    monkeypatch.setattr(runner, "_build_corpus_index_snapshot", unexpected_work)

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError, match=message):
        runner.run_corpus_episode_completion_workflow("gooaye", **options)


def test_confirmed_action_drift_rejects_without_dispatch_or_report(monkeypatch):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("audio_download")
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "audio_download", "EP677", []),
    )

    def unexpected_call(*args, **kwargs):
        calls.append("called")
        pytest.fail("drifted confirmation reached dispatch or report writing")

    monkeypatch.setattr(runner, "_write_run_report", unexpected_call, raising=False)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="intake",
        confirm=True,
    )

    assert result.run_mode == "confirmed"
    assert result.selected_action == "audio_download"
    assert result.executed_action is None
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert result.rows[0].status == "rejected"
    assert calls == []


def test_confirmed_target_disappearance_rejects_without_dispatch_or_report(monkeypatch):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("audio_download")
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "audio_download", None, []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: calls.append("audio_download"),
    )
    monkeypatch.setattr(
        runner,
        "_write_run_report",
        lambda *args, **kwargs: pytest.fail("disappeared target must not write a report"),
    )

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="audio_download",
        confirm=True,
    )

    assert result.executed_action is None
    assert result.report_json_path is None
    assert result.rows[0].status == "rejected"
    assert calls == []


@pytest.mark.parametrize("selected_action", ("completed", "blocked"))
def test_confirmed_terminal_selection_stops_without_fallback_or_report(
    monkeypatch,
    selected_action: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row(selected_action)
    selected = replace(
        selected,
        action=selected_action,
        status=selected_action,
        requires_confirmation=False,
    )
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, selected_action, "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: pytest.fail("terminal selection must not dispatch"),
    )
    monkeypatch.setattr(
        runner,
        "_write_run_report",
        lambda *args, **kwargs: pytest.fail("terminal selection must not write a report"),
    )

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="audio_download",
        confirm=True,
    )

    assert result.selected_action == selected_action
    assert result.executed_action is None
    assert result.rows[0].status == selected_action


@pytest.mark.parametrize(
    ("action", "expected_runner"),
    (
        ("intake", "run_corpus_episode_intake"),
        ("audio_download", "run_corpus_audio_download"),
        ("local_transcription", "run_corpus_local_transcription"),
        ("deterministic_remediation", "run_corpus_remediation"),
        ("semantic_summary", "run_corpus_semantic_remediation"),
        ("semantic_review", "run_corpus_semantic_remediation"),
    ),
)
def test_confirmed_matching_action_dispatches_exactly_one_runner_then_reports(
    monkeypatch,
    action: str,
    expected_runner: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row(action)
    calls: list[tuple[str, dict]] = []
    report_calls: list[object] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, action, "EP677", []),
    )

    def stage_result():
        if action.startswith("semantic_"):
            row = SimpleNamespace(
                episode_ref="EP677",
                status="executed",
                planned_reads=["in-memory corpus snapshot"],
                planned_writes=[],
                output_paths=[],
                source_report_paths=[],
                stage_counts={},
            )
        else:
            outcome = {
                "intake": "seeded",
                "audio_download": "downloaded",
                "local_transcription": "executed",
                "deterministic_remediation": "executed",
            }[action]
            row = SimpleNamespace(
                episode_ref="EP677",
                outcome_status=outcome,
                planned_reads=["in-memory corpus snapshot"],
                planned_writes=[],
                output_paths=[],
                source_report_paths=[],
                stage_counts={},
            )
        return SimpleNamespace(rows=[row], warnings=[])

    def fake_runner(name: str):
        def invoke(*args, **kwargs):
            assert args == ("gooaye",)
            calls.append((name, kwargs))
            return stage_result()

        return invoke

    for name in (
        "run_corpus_episode_intake",
        "run_corpus_audio_download",
        "run_corpus_local_transcription",
        "run_corpus_remediation",
        "run_corpus_semantic_remediation",
    ):
        monkeypatch.setattr(
            runner,
            name,
            fake_runner(name)
            if name == expected_runner
            else (lambda *args, _name=name, **kwargs: pytest.fail(f"unexpected runner {_name}")),
            raising=False,
        )
    monkeypatch.setattr(
        runner,
        "_write_run_report",
        lambda result: report_calls.append(result),
        raising=False,
    )
    options: dict[str, object] = {}
    if action == "semantic_summary":
        options["api_cost_ack"] = runner.SEMANTIC_API_COST_ACK

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action=action,
        confirm=True,
        **options,
    )

    assert [name for name, _ in calls] == [expected_runner]
    if action == "deterministic_remediation":
        assert calls[0][1]["max_actions"] == 1
    assert result.executed_action == action
    assert result.rows[0].status == "executed"
    assert len(report_calls) == 1


@pytest.mark.parametrize(
    ("source_status", "expected_status"),
    (
        ("downloaded", "executed"),
        ("reused", "reused"),
        ("completed", "completed"),
        ("blocked", "blocked"),
        ("rejected", "rejected"),
        ("failed", "failed"),
    ),
)
def test_confirmed_stage_status_maps_one_outcome_and_stops(
    monkeypatch,
    source_status: str,
    expected_status: str,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("audio_download")
    reports: list[object] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "audio_download", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: SimpleNamespace(
            rows=[
                SimpleNamespace(
                    episode_ref="EP677",
                    outcome_status=source_status,
                    planned_reads=[],
                    planned_writes=[],
                    output_paths=[],
                    source_report_paths=[],
                    stage_counts={},
                )
            ],
            warnings=[],
        ),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: reports.append(result))

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="audio_download",
        confirm=True,
    )

    assert result.executed_action == "audio_download"
    assert result.rows[0].status == expected_status
    assert len(reports) == 1


def test_confirmed_stage_exception_is_contained_and_stops_after_one_attempt(monkeypatch):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("audio_download")
    reports: list[object] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "audio_download", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("https://invalid.example/?token=leak-token")),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: reports.append(result))

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="audio_download",
        confirm=True,
    )

    assert result.executed_action == "audio_download"
    assert result.rows[0].status == "failed"
    assert result.rows[0].failure_category == "RuntimeError"
    assert len(reports) == 1
    assert "https://" not in repr(result)
    assert "token" not in repr(result)


def test_confirmed_stage_attempt_writes_atomic_metadata_only_report(
    monkeypatch,
    tmp_path: Path,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    selected = _selected_completion_row("intake")
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "intake", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: SimpleNamespace(
            rows=[
                SimpleNamespace(
                    episode_ref="EP677",
                    outcome_status="seeded",
                    planned_reads=["configured podcast RSS feed"],
                    planned_writes=[],
                    output_paths=[],
                    source_report_paths=[],
                    stage_counts={},
                )
            ],
            warnings=[],
        ),
    )

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="intake",
        confirm=True,
    )

    assert result.report_json_path is not None
    assert result.report_markdown_path is not None
    assert result.report_json_path.exists()
    assert result.report_markdown_path.exists()
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["executed_action"] == "intake"
    assert payload["rows"][0]["status"] == "executed"
    assert "generated_at" not in payload
    assert "generated_at" not in result.report_markdown_path.read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("*.part"))


def test_confirmed_stage_attempt_warns_that_derived_metadata_requires_manual_refresh(
    monkeypatch,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("intake")
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "intake", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: SimpleNamespace(
            rows=[
                SimpleNamespace(
                    episode_ref="EP677",
                    outcome_status="seeded",
                    planned_reads=[],
                    planned_writes=[],
                    output_paths=[],
                    source_report_paths=[],
                    stage_counts={},
                )
            ],
            warnings=[],
        ),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="intake",
        confirm=True,
    )

    assert [(warning.scope, warning.episode_ref, warning.message) for warning in result.warnings] == [
        (
            "corpus",
            "EP677",
            "Persisted corpus index and remediation plan may be stale; refresh them manually.",
        ),
        (
            "cache",
            "EP677",
            "SQLite cache may be stale; rebuild cache manually.",
        ),
    ]


def test_confirmed_report_write_failure_is_safe_and_does_not_compensate(
    monkeypatch,
    tmp_path: Path,
):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    selected = _selected_completion_row("intake")
    attempts: list[str] = []
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "intake", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: (
            attempts.append("intake")
            or SimpleNamespace(
                rows=[
                    SimpleNamespace(
                        episode_ref="EP677",
                        outcome_status="seeded",
                        planned_reads=[],
                        planned_writes=[],
                        output_paths=[],
                        source_report_paths=[],
                        stage_counts={},
                    )
                ],
                warnings=[],
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "_render_markdown",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("https://invalid.example/?token=leak-token")),
    )

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError) as exc_info:
        runner.run_corpus_episode_completion_workflow(
            "gooaye",
            episode_ref="EP677",
            action="intake",
            confirm=True,
        )

    assert attempts == ["intake"]
    assert "OSError" in str(exc_info.value)
    assert "https://" not in str(exc_info.value)
    assert "token" not in str(exc_info.value)
    assert not list(tmp_path.rglob("*.part"))


def test_confirmed_semantic_review_ignores_all_llm_only_options(monkeypatch):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("semantic_review")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "semantic_review", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: (
            captured.update(kwargs)
            or SimpleNamespace(
                rows=[
                    SimpleNamespace(
                        episode_ref="EP677",
                        status="executed",
                        planned_reads=["in-memory corpus snapshot"],
                        planned_writes=[],
                        output_paths=[],
                        source_report_paths=[],
                        stage_counts={},
                    )
                ],
                warnings=[],
            )
        ),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="semantic_review",
        confirm=True,
        api_cost_ack="not-used",
        semantic_provider="https://provider.invalid/?token=never-use",
        semantic_model="not-a-safe-model?",
        semantic_base_url="https://endpoint.invalid/?token=never-use",
        semantic_api_key_env="not_valid",
        semantic_chunk_seconds=0,
        semantic_max_segments_per_chunk=0,
    )

    assert captured == {
        "episode_ref": "EP677",
        "action": "semantic_review",
        "confirm": True,
    }
    assert result.filters.semantic_provider is None
    assert result.filters.semantic_model is None
    assert result.filters.semantic_chunk_seconds == 600
    assert result.filters.semantic_max_segments_per_chunk == 120


def test_completion_workflow_outputs_filter_untrusted_paths_and_advice_text(monkeypatch, tmp_path: Path):
    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    selected = _selected_completion_row("intake")
    safe_path = str(tmp_path / "reports" / "safe.json")
    unsafe_values = [
        "https://private.example.test/report.json?token=secret",
        "../private-report.json",
        "free form metadata",
        "you should buy immediately",
        "C:\\private\\token-report.json",
        "buy-recommendation",
    ]
    source_row = SimpleNamespace(
        episode_ref="EP677",
        outcome_status="seeded",
        planned_reads=[safe_path, *unsafe_values[:4]],
        planned_writes=[safe_path, unsafe_values[1]],
        output_paths=[safe_path, unsafe_values[4]],
        source_report_paths=[safe_path, unsafe_values[0]],
        stage_counts={"intake": 1},
    )

    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "intake", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda *args, **kwargs: SimpleNamespace(rows=[source_row], warnings=[]),
    )

    result = runner.run_corpus_episode_completion_workflow(
        "gooaye",
        episode_ref="EP677",
        action="intake",
        confirm=True,
        semantic_model=unsafe_values[-1],
    )
    payload = runner.result_to_dict(result)
    combined = "\n".join(
        [
            repr(result),
            json.dumps(payload, ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
        ]
    ).casefold()

    for forbidden in (
        "https://",
        "token=secret",
        "../private-report.json",
        "free form metadata",
        "you should buy immediately",
        "token-report.json",
        "buy-recommendation",
        "traceback",
    ):
        assert forbidden not in combined
    assert payload["rows"][0]["planned_reads"] == [safe_path]
    assert payload["rows"][0]["planned_writes"] == [safe_path]
    assert payload["rows"][0]["output_paths"] == [safe_path]
    assert payload["rows"][0]["source_report_paths"] == [safe_path]


def test_completion_cli_forwards_defaults_without_loading_local_env(
    monkeypatch,
    capsys,
):
    from scripts import run_corpus_episode_completion_workflow as cli

    captured: dict[str, object] = {}
    env_calls: list[object] = []
    monkeypatch.setattr(
        cli,
        "run_corpus_episode_completion_workflow",
        lambda podcast_id, **kwargs: captured.update({"podcast_id": podcast_id, **kwargs}) or SimpleNamespace(),
    )
    monkeypatch.setattr(cli, "result_to_dict", lambda result: {"ok": True})
    monkeypatch.setattr(cli, "load_local_env", lambda *args: env_calls.append(args))

    status = cli.main(["--podcast", "gooaye"])

    assert status == 0
    assert captured == {
        "podcast_id": "gooaye",
        "episode_ref": "latest",
        "action": "next",
        "confirm": False,
        "api_cost_ack": "",
        "transcription_model": None,
        "transcription_device": "cpu",
        "transcription_compute_type": "int8",
        "transcription_vad_filter": False,
        "semantic_provider": "openai-compatible",
        "semantic_model": None,
        "semantic_base_url": None,
        "semantic_api_key_env": "OPENAI_API_KEY",
        "semantic_chunk_seconds": 600,
        "semantic_max_segments_per_chunk": 120,
        "progress_callback": None,
    }
    assert env_calls == []
    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_completion_cli_parser_excludes_unsupported_automation_switches():
    from scripts import run_corpus_episode_completion_workflow as cli

    destinations = {argument.dest for argument in cli.build_parser()._actions}

    assert not destinations.intersection(
        {
            "force",
            "partial",
            "batch",
            "latest_n",
            "retry",
            "scheduler",
            "loop",
            "full_chain",
        }
    )


def test_completion_cli_rejects_summary_ack_before_local_env(
    monkeypatch,
    capsys,
):
    from scripts import run_corpus_episode_completion_workflow as cli

    monkeypatch.setattr(
        cli,
        "load_local_env",
        lambda *args: pytest.fail("invalid acknowledgement loaded local env"),
    )

    status = cli.main(
        [
            "--podcast",
            "gooaye",
            "--episode",
            "EP677",
            "--action",
            "semantic_summary",
            "--confirm",
            "--api-cost-ack",
            "wrong",
        ]
    )

    assert status == 1
    stderr = capsys.readouterr().err
    assert "api_cost_ack" in stderr
    assert "traceback" not in stderr.lower()


def test_completion_cli_uses_category_only_error_output(monkeypatch, capsys):
    from scripts import run_corpus_episode_completion_workflow as cli

    monkeypatch.setattr(
        cli,
        "run_corpus_episode_completion_workflow",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("https://invalid.example/?token=leak-token")),
    )

    status = cli.main(["--podcast", "gooaye"])

    assert status == 1
    stderr = capsys.readouterr().err
    assert "RuntimeError" in stderr
    for forbidden in ("https://", "token", "leak-token", "traceback"):
        assert forbidden not in stderr.lower()


def test_red_confirmed_stage_preserves_safe_child_provenance_warnings_and_failure_category():
    """016 dispatch reports contained child outcome metadata without raw exception text."""

    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner

    selected = _selected_completion_row("audio_download")
    safe_report = "data/corpus/gooaye/child-report.json"
    source_result = SimpleNamespace(
        report_json_path=safe_report,
        report_markdown_path="data/corpus/gooaye/child-report.md",
        warnings=[SimpleNamespace(message="child report warning")],
        rows=[
            SimpleNamespace(
                episode_ref="EP677",
                outcome_status="failed",
                planned_reads=[],
                planned_writes=[],
                output_paths=[],
                source_report_paths=[safe_report, "https://invalid.example/?token=leak"],
                failure_category="RuntimeError",
                warnings=["child row warning", "token=leak"],
                stage_counts={},
            )
        ],
    )

    row = runner._confirmed_row_from_stage_result(
        selected_row=selected,
        selected_action="audio_download",
        episode_ref="EP677",
        source_result=source_result,
    )

    assert row.status == "failed"
    assert row.failure_category == "RuntimeError"
    assert row.source_report_paths == [
        safe_report,
        "data/corpus/gooaye/child-report.md",
    ]
    assert row.warnings == ["child row warning", "child report warning"]
    assert "token" not in repr(row)


@pytest.mark.parametrize(
    ("options", "message"),
    (
        ({"semantic_chunk_seconds": 0}, "semantic_chunk_seconds"),
        ({"semantic_max_segments_per_chunk": 0}, "semantic_max_segments_per_chunk"),
        ({"semantic_provider": "provider?bad"}, "semantic_provider"),
        ({"semantic_model": "model?bad"}, "semantic_model"),
    ),
)
def test_red_next_preview_validates_actual_semantic_summary_settings_after_fresh_selection(
    monkeypatch, options, message
):
    """A `next` preview may not advertise an impossible semantic-summary action."""

    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    selected = _selected_completion_row("semantic_summary")
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "semantic_summary", "EP677", []),
    )

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError, match=message):
        runner.run_corpus_episode_completion_workflow("gooaye", episode_ref="EP677", action="next", **options)


@pytest.mark.parametrize(
    ("options", "message"),
    (
        ({"semantic_provider": "provider?bad"}, "semantic_provider"),
        ({"semantic_model": "model?bad"}, "semantic_model"),
    ),
)
def test_red_confirmed_semantic_summary_validates_provider_model_before_child_dispatch(monkeypatch, options, message):
    """Selected-action validation must complete before a provider-capable child runs."""

    import corpus_ingest_core.corpus_episode_completion_workflow_runner as runner
    from corpus_ingest_core import CorpusEpisodeCompletionWorkflowRunnerFailedError

    selected = _selected_completion_row("semantic_summary")
    monkeypatch.setattr(
        runner,
        "_preview_selection",
        lambda *args, **kwargs: (selected, "semantic_summary", "EP677", []),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: pytest.fail("invalid semantic settings reached child dispatch"),
    )

    with pytest.raises(CorpusEpisodeCompletionWorkflowRunnerFailedError, match=message):
        runner.run_corpus_episode_completion_workflow(
            "gooaye",
            episode_ref="EP677",
            action="semantic_summary",
            confirm=True,
            api_cost_ack=runner.SEMANTIC_API_COST_ACK,
            **options,
        )
