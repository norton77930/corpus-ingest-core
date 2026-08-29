"""Contract tests for the latest-episode deterministic workflow runner."""

from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_public_runner_is_exported_with_dry_run_first_local_options():
    from corpus_ingest_core import run_corpus_latest_episode_deterministic_workflow

    signature = inspect.signature(run_corpus_latest_episode_deterministic_workflow)

    assert list(signature.parameters) == [
        "podcast_id",
        "confirm",
        "transcription_model",
        "transcription_device",
        "transcription_compute_type",
        "transcription_vad_filter",
    ]
    assert signature.parameters["confirm"].default is False
    assert signature.parameters["transcription_device"].default == "cpu"
    assert signature.parameters["transcription_compute_type"].default == "int8"
    assert signature.parameters["transcription_vad_filter"].default is False


def _install_semantic_only_residual_fixture(monkeypatch, tmp_path: Path) -> None:
    import corpus_ingest_core.corpus_episode_intake as intake
    import corpus_ingest_core.corpus_index as corpus_index
    from corpus_ingest_core import storage
    from corpus_ingest_core.models import Episode

    for name, directory in (
        ("AUDIO_DIR", "audio"),
        ("TRANSCRIPTS_DIR", "transcripts"),
        ("SUMMARIES_DIR", "summaries"),
        ("MENTIONS_DIR", "mentions"),
        ("REPORTS_DIR", "reports"),
        ("MAPPINGS_DIR", "mappings"),
        ("EXTERNAL_DIR", "external"),
        ("CORPUS_DIR", "corpus"),
    ):
        monkeypatch.setattr(storage, name, tmp_path / directory, raising=False)
    monkeypatch.setattr(
        corpus_index,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )
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

    seed_path = storage.corpus_episode_seed_asset_path("gooaye", "EP677")
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": "EP677 Alpha",
                "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
                "duration": "00:42:00",
                "guid_status": "present",
                "has_audio_url": True,
                "seed_source": "rss",
                "selector": "latest",
                "warning_count": 0,
                "warnings": [],
                "not_investment_advice": True,
            }
        ),
        encoding="utf-8",
    )
    audio_path = storage.AUDIO_DIR / "gooaye" / "EP677__EP677 Alpha.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"mp3")

    transcript_paths = storage.transcript_asset_paths("gooaye", "EP677", "EP677 Alpha")
    transcript_paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_paths.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "title": "EP677 Alpha",
                "language": "zh",
                "segment_count": 1,
                "last_segment_end_seconds": 5.5,
                "completed": True,
                "segments": [{"id": 1, "start": 0.0, "end": 5.5, "text": "fixture"}],
            }
        ),
        encoding="utf-8",
    )
    transcript_paths.text_path.write_text("fixture", encoding="utf-8")
    transcript_paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:05,500\nfixture\n",
        encoding="utf-8",
    )

    summary_path = storage.summary_asset_path("gooaye", "EP677", "EP677 Alpha")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("# deterministic summary", encoding="utf-8")
    mentions = storage.mention_asset_paths("gooaye", "EP677", "EP677 Alpha")
    mentions.json_path.parent.mkdir(parents=True, exist_ok=True)
    mentions.json_path.write_text(
        json.dumps({"podcast_id": "gooaye", "episode_ref": "EP677", "mentions": []}),
        encoding="utf-8",
    )
    mentions.markdown_path.write_text("# mentions", encoding="utf-8")
    intelligence = storage.episode_intelligence_report_asset_paths(
        "gooaye", "EP677", "EP677 Alpha"
    )
    intelligence.json_path.parent.mkdir(parents=True, exist_ok=True)
    intelligence.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "report_status": "final",
                "transcript_validation": {"status": "valid", "segment_count": 1},
            }
        ),
        encoding="utf-8",
    )
    intelligence.markdown_path.write_text("# intelligence", encoding="utf-8")
    mapping = storage.industry_chain_mapping_asset_paths("gooaye", "EP677", "EP677 Alpha")
    mapping.json_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "mapping_status": "final",
                "industry_chain_nodes": [],
                "stock_candidates": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    mapping.markdown_path.write_text("# mapping", encoding="utf-8")
    external = storage.external_data_boundary_asset_paths(
        "gooaye", "EP677", "EP677 Alpha"
    )
    external.json_path.parent.mkdir(parents=True, exist_ok=True)
    external.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP677",
                "boundary_status": "final",
                "candidate_boundaries": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    external.markdown_path.write_text("# external boundary", encoding="utf-8")


def test_semantic_only_residual_hands_off_without_confirmed_executor_calls(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _install_semantic_only_residual_fixture(monkeypatch, tmp_path)

    public_probe = run_corpus_episode_workflow("gooaye", episode_ref="EP677")
    assert public_probe.selected_stage == "blocked"

    confirmed_executor_calls: list[str] = []
    original_intake = runner.run_corpus_episode_intake

    def intake(podcast_id: str, *, episode_ref: str, confirm: bool):
        if confirm:
            confirmed_executor_calls.append("intake")
            pytest.fail("ready episode must not confirm intake")
        return original_intake(podcast_id, episode_ref=episode_ref, confirm=confirm)

    monkeypatch.setattr(runner, "run_corpus_episode_intake", intake)
    for name in (
        "run_corpus_audio_download",
        "run_corpus_local_transcription",
        "run_corpus_remediation",
    ):
        monkeypatch.setattr(
            runner,
            name,
            lambda *args, _name=name, **kwargs: pytest.fail(
                f"ready episode must not confirm {_name}"
            ),
        )

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "ready_for_semantic_summary"
    assert result.rows[-1].stage == "ready_for_semantic_summary"
    assert confirmed_executor_calls == []


@pytest.mark.parametrize(
    "selection",
    (
        {"selected_stage": "completed", "rows": [], "warnings": []},
        {
            "selected_stage": "completed",
            "episode_ref": "ep099",
            "rows": [],
            "warnings": [],
        },
    ),
    ids=("missing-episode-ref", "mismatched-episode-ref"),
)
def test_probe_fails_closed_when_selector_does_not_return_pinned_episode(
    monkeypatch,
    selection,
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda **kwargs: selection,
    )

    row, selected_stage = runner._probe_stage("gooaye", "ep100")

    assert selected_stage == "blocked"
    assert row.episode_ref == "ep100"
    assert row.status == "blocked"
    assert row.reason == "deterministic stage inspection episode mismatch"


def test_probe_fails_closed_on_malformed_selected_action_identity(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    malformed_action_id = "EP677:mentions/invalid"
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda **kwargs: {
            "selected_stage": "deterministic_remediation",
            "episode_ref": "EP677",
            "action_id": malformed_action_id,
            "rows": [],
            "warnings": [],
        },
    )

    row, selected_stage = runner._probe_stage("gooaye", "EP677")

    assert selected_stage == runner.STAGE_BLOCKED
    assert row.stage == runner.STAGE_BLOCKED
    assert row.status == "blocked"
    assert row.reason == "deterministic stage inspection action identity invalid"
    assert row.action_id is None
    assert malformed_action_id not in str(row)


def _stage_probe(stage: str) -> SimpleNamespace:
    return SimpleNamespace(
        selected_stage=stage,
        rows=[
            SimpleNamespace(
                episode_ref="ep100",
                stage=stage,
                status="selected",
                reason=f"{stage} selected",
                planned_reads=["in-memory corpus snapshot"],
                planned_writes=[f"data/{stage}"],
                output_paths=[],
                source_report_paths=[],
                failure_category=None,
                warnings=[],
            )
        ],
        warnings=[],
    )


def _stage_selection(stage: str) -> dict[str, object]:
    probe = _stage_probe(stage)
    return {
        "selected_stage": probe.selected_stage,
        "episode_ref": "ep100",
        "rows": probe.rows,
        "warnings": probe.warnings,
    }


def _source_execution_row(
    episode_ref: str,
    status: str,
    *,
    action_id: str | None = None,
    reason: str | None = None,
    planned_reads: list[str] | None = None,
    planned_writes: list[str] | None = None,
    output_paths: list[str] | None = None,
    source_report_paths: list[str] | None = None,
    failure_category: str | None = None,
    warnings: list[str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        episode_ref=episode_ref,
        status=status,
        outcome_status=status,
        action_id=action_id,
        reason=reason if reason is not None else f"{status} result",
        planned_reads=list(planned_reads or []),
        planned_writes=list(planned_writes or []),
        output_paths=list(output_paths or []),
        source_report_paths=list(source_report_paths or []),
        failure_category=(
            failure_category
            if failure_category is not None
            else "FakeFailure" if status == "failed" else None
        ),
        warnings=list(warnings or []),
    )


def _stage_result(
    status: str = "executed",
    *,
    action_id: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                status,
                action_id=action_id,
                output_paths=["data/output.md"] if status == "executed" else [],
            )
        ],
        warnings=[],
    )


def test_confirmed_run_pins_latest_and_advances_every_deterministic_stage(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(runner, "resolve_canonical_transcript_asset_paths", lambda *args: object())
    calls: list[tuple[str, str, bool]] = []
    stages = iter(
        [
            "intake",
            "audio_download",
            "local_transcription",
            "deterministic_remediation",
            "completed",
        ]
    )

    def intake(podcast_id: str, *, episode_ref: str, confirm: bool):
        calls.append(("intake", episode_ref, confirm))
        if not confirm:
            return SimpleNamespace(resolved_episode_ref="ep100", rows=[], warnings=[])
        return _stage_result("seeded")

    def probe(
        *,
        podcast_id: str,
        selector: str,
        max_actions: int,
        allow_semantic_handoff: bool,
    ):
        assert podcast_id == "gooaye"
        assert max_actions == 1
        assert allow_semantic_handoff is True
        calls.append(("probe", selector, allow_semantic_handoff))
        return _stage_selection(next(stages))

    monkeypatch.setattr(runner, "run_corpus_episode_intake", intake)
    monkeypatch.setattr(runner, "_select_episode_workflow_stage", probe)
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda podcast_id, *, episode_ref, confirm: calls.append(
            ("audio", episode_ref, confirm)
        )
        or _stage_result("downloaded"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_local_transcription",
        lambda podcast_id, *, episode_ref, confirm, model, device, compute_type, vad_filter: calls.append(("transcription", episode_ref, confirm)) or _stage_result(),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_remediation",
        lambda podcast_id, *, episode_ref, confirm, max_actions: calls.append(("remediation", episode_ref, confirm)) or _stage_result(action_id="ep100:extractive_summary"),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.episode_ref == "ep100"
    assert result.outcome == "ready_for_semantic_summary"
    assert calls == [
        ("intake", "latest", False),
        ("probe", "ep100", True),
        ("intake", "ep100", True),
        ("probe", "ep100", True),
        ("audio", "ep100", True),
        ("probe", "ep100", True),
        ("transcription", "ep100", True),
        ("probe", "ep100", True),
        ("remediation", "ep100", True),
        ("probe", "ep100", True),
    ]


def test_execution_composition_ignores_non_target_episode_rows():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "audio_download",
        _stage_probe("audio_download").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep099",
                "failed",
                action_id="ep099:other",
                reason="other episode reason",
                planned_reads=["other-read"],
                planned_writes=["other-write"],
                output_paths=["data/other-episode.md"],
                source_report_paths=["other-report"],
                failure_category="OtherFailure",
                warnings=["other-warning"],
            ),
            _source_execution_row(
                "ep100",
                "executed",
                action_id="ep100:target",
                reason="target episode reason",
                planned_reads=["data/target-read.json"],
                planned_writes=["data/target-write.json"],
                output_paths=["data/target-episode.md"],
                source_report_paths=["data/target-report.json"],
                failure_category="TargetFailure",
                warnings=["target-warning"],
            ),
            _source_execution_row("ep101", "blocked"),
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "executed"
    assert result_row.action_id == "ep100:target"
    assert result_row.reason == "target episode reason"
    assert result_row.planned_reads == ["data/target-read.json"]
    assert result_row.planned_writes == ["data/target-write.json"]
    assert result_row.output_paths == ["data/target-episode.md"]
    assert result_row.source_report_paths == ["data/target-report.json"]
    assert result_row.failure_category == "TargetFailure"
    assert result_row.warnings == ["target-warning"]


def test_execution_composition_fails_closed_on_action_id_mismatch():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "deterministic_remediation",
        _stage_probe("deterministic_remediation").rows[0],
        action_id="ep100:extractive_summary",
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "executed",
                action_id="ep100:mentions",
                reason="mentions executed",
                planned_reads=["data/mentions-input.json"],
                planned_writes=["data/mentions.json"],
                output_paths=["data/mentions.md"],
                source_report_paths=["data/mentions-report.json"],
                failure_category="MismatchedFailure",
                warnings=["mismatched warning"],
            )
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "blocked"
    assert result_row.action_id == "ep100:extractive_summary"
    assert result_row.reason == "deterministic stage execution action mismatch"
    assert result_row.requires_confirmation is False
    assert result_row.planned_reads == []
    assert result_row.planned_writes == []
    assert result_row.output_paths == []
    assert result_row.source_report_paths == []
    assert result_row.failure_category is None
    assert result_row.warnings == []


@pytest.mark.parametrize(
    ("selected_action_id", "source_action_id", "expected_action_id"),
    (
        (
            "ep100:extractive_summary",
            "ep100:mentions/invalid",
            "ep100:extractive_summary",
        ),
        (
            "ep100:extractive_summary/invalid",
            "ep100:extractive_summary",
            None,
        ),
    ),
    ids=("malformed-source", "malformed-selected"),
)
def test_execution_composition_fails_closed_on_malformed_action_identity(
    selected_action_id,
    source_action_id,
    expected_action_id,
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = replace(
        runner._row_from_source(
            "ep100",
            "deterministic_remediation",
            _stage_probe("deterministic_remediation").rows[0],
        ),
        action_id=selected_action_id,
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "executed",
                action_id=source_action_id,
                reason="private source reason",
                planned_reads=["data/private-read.json"],
                planned_writes=["data/private-write.json"],
                output_paths=["data/private-output.json"],
                source_report_paths=["data/private-report.json"],
                failure_category="PrivateFailure",
                warnings=["private warning"],
            )
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "blocked"
    assert result_row.action_id == expected_action_id
    assert result_row.reason == "deterministic stage execution action mismatch"
    assert result_row.requires_confirmation is False
    assert result_row.planned_reads == []
    assert result_row.planned_writes == []
    assert result_row.output_paths == []
    assert result_row.source_report_paths == []
    assert result_row.failure_category is None
    assert result_row.warnings == []


def test_execution_composition_uses_downloaded_winner_metadata():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "audio_download",
        _stage_probe("audio_download").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "blocked",
                action_id="ep100:blocked",
                reason="blocked reason",
                planned_reads=["blocked-read"],
                planned_writes=["blocked-write"],
                output_paths=["blocked-output"],
                source_report_paths=["blocked-report"],
                failure_category="BlockedFailure",
                warnings=["blocked-warning"],
            ),
            _source_execution_row(
                "ep100",
                "downloaded",
                action_id="ep100:downloaded",
                reason="downloaded reason",
                planned_reads=["data/downloaded-read.json"],
                planned_writes=["data/downloaded-write.json"],
                output_paths=["data/downloaded-output.json"],
                source_report_paths=["data/downloaded-report.json"],
                failure_category="DownloadedFailure",
                warnings=["downloaded-warning"],
            ),
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "executed"
    assert result_row.action_id == "ep100:downloaded"
    assert result_row.reason == "downloaded reason"
    assert result_row.planned_reads == ["data/downloaded-read.json"]
    assert result_row.planned_writes == ["data/downloaded-write.json"]
    assert result_row.output_paths == ["data/downloaded-output.json"]
    assert result_row.source_report_paths == ["data/downloaded-report.json"]
    assert result_row.failure_category == "DownloadedFailure"
    assert result_row.warnings == ["downloaded-warning"]


def test_execution_composition_uses_failed_winner_metadata():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "deterministic_remediation",
        _stage_probe("deterministic_remediation").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "executed",
                action_id="ep100:executed",
                reason="executed reason",
                planned_reads=["executed-read"],
                planned_writes=["executed-write"],
                output_paths=["executed-output"],
                source_report_paths=["executed-report"],
                failure_category="ExecutedFailure",
                warnings=["executed-warning"],
            ),
            _source_execution_row(
                "ep100",
                "failed",
                action_id="ep100:failed",
                reason="failed reason",
                planned_reads=["data/failed-read.json"],
                planned_writes=["data/failed-write.json"],
                output_paths=["data/failed-output.json"],
                source_report_paths=["data/failed-report.json"],
                failure_category="FailedFailure",
                warnings=["failed-warning"],
            ),
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "failed"
    assert result_row.action_id == "ep100:failed"
    assert result_row.reason == "failed reason"
    assert result_row.planned_reads == ["data/failed-read.json"]
    assert result_row.planned_writes == ["data/failed-write.json"]
    assert result_row.output_paths == ["data/failed-output.json"]
    assert result_row.source_report_paths == ["data/failed-report.json"]
    assert result_row.failure_category == "FailedFailure"
    assert result_row.warnings == ["failed-warning"]


def test_execution_composition_uses_unknown_blocked_winner_metadata():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "audio_download",
        _stage_probe("audio_download").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "rejected",
                action_id="ep100:rejected",
                reason="rejected reason",
                planned_reads=["rejected-read"],
                planned_writes=["rejected-write"],
                output_paths=["rejected-output"],
                source_report_paths=["rejected-report"],
                failure_category="RejectedFailure",
                warnings=["rejected-warning"],
            ),
            _source_execution_row(
                "ep100",
                "skipped",
                action_id="ep100:skipped",
                reason="skipped reason",
                planned_reads=["data/skipped-read.json"],
                planned_writes=["data/skipped-write.json"],
                output_paths=["data/skipped-output.json"],
                source_report_paths=["data/skipped-report.json"],
                failure_category="SkippedFailure",
                warnings=["skipped-warning"],
            ),
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "blocked"
    assert result_row.action_id == "ep100:skipped"
    assert result_row.reason == "skipped reason"
    assert result_row.planned_reads == ["data/skipped-read.json"]
    assert result_row.planned_writes == ["data/skipped-write.json"]
    assert result_row.output_paths == ["data/skipped-output.json"]
    assert result_row.source_report_paths == ["data/skipped-report.json"]
    assert result_row.failure_category == "SkippedFailure"
    assert result_row.warnings == ["skipped-warning"]


def test_execution_composition_uses_first_metadata_for_deterministic_tie():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "audio_download",
        _stage_probe("audio_download").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "downloaded",
                action_id="ep100:downloaded",
                reason="downloaded reason",
                planned_reads=["data/downloaded-read.json"],
                planned_writes=["data/downloaded-write.json"],
                output_paths=["data/downloaded-output.json"],
                source_report_paths=["data/downloaded-report.json"],
                failure_category="DownloadedFailure",
                warnings=["downloaded-warning"],
            ),
            _source_execution_row(
                "ep100",
                "seeded",
                action_id="ep100:seeded",
                reason="seeded reason",
                planned_reads=["seeded-read"],
                planned_writes=["seeded-write"],
                output_paths=["seeded-output"],
                source_report_paths=["seeded-report"],
                failure_category="SeededFailure",
                warnings=["seeded-warning"],
            ),
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "executed"
    assert result_row.action_id == "ep100:downloaded"
    assert result_row.reason == "downloaded reason"
    assert result_row.planned_reads == ["data/downloaded-read.json"]
    assert result_row.planned_writes == ["data/downloaded-write.json"]
    assert result_row.output_paths == ["data/downloaded-output.json"]
    assert result_row.source_report_paths == ["data/downloaded-report.json"]
    assert result_row.failure_category == "DownloadedFailure"
    assert result_row.warnings == ["downloaded-warning"]


@pytest.mark.parametrize(
    ("statuses", "expected_status"),
    [
        (("failed", "executed"), "failed"),
        (("blocked", "executed"), "executed"),
        (("rejected", "downloaded"), "executed"),
        (("blocked", "seeded"), "executed"),
        (("blocked", "reused"), "reused"),
        (("blocked", "rejected"), "blocked"),
        (("rejected",), "rejected"),
        (("skipped",), "blocked"),
    ],
)
def test_execution_composition_uses_target_episode_status_priority(
    statuses,
    expected_status,
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "deterministic_remediation",
        _stage_probe("deterministic_remediation").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[_source_execution_row("ep100", status) for status in statuses]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == expected_status


def test_execution_composition_fails_closed_when_target_episode_is_absent():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "audio_download",
        _stage_probe("audio_download").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep099",
                "executed",
                action_id="ep099:audio",
                reason="ep099 sibling reason",
                planned_reads=["ep099-read"],
                planned_writes=["ep099-write"],
                output_paths=["data/ep099-audio.mp3"],
                source_report_paths=["ep099-report"],
                failure_category="SiblingFailure",
                warnings=["ep099-warning"],
            )
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.status == "blocked"
    assert result_row.action_id is None
    assert result_row.reason == "audio_download blocked"
    assert result_row.planned_reads == []
    assert result_row.planned_writes == []
    assert result_row.output_paths == []
    assert result_row.source_report_paths == []
    assert result_row.failure_category is None
    assert result_row.warnings == []


def test_dry_run_resolves_latest_once_without_dispatching_stage_executor(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: _stage_selection("audio_download"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: pytest.fail("dry-run must not dispatch audio"),
    )

    result = runner.run_corpus_latest_episode_deterministic_workflow("gooaye")

    assert result.run_mode == "dry_run"
    assert result.episode_ref == "ep100"
    assert result.outcome == "dry_run"
    assert result.rows[0].stage == "audio_download"
    assert result.report_json_path is None


def test_failed_stage_stops_before_later_transcription_or_remediation(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: _stage_selection("audio_download"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda podcast_id, *, episode_ref, confirm: _stage_result("failed"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_local_transcription",
        lambda *args, **kwargs: pytest.fail("must stop before transcription"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_remediation",
        lambda *args, **kwargs: pytest.fail("must stop before remediation"),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "failed"
    assert result.rows[-1].stage == "audio_download"
    assert result.rows[-1].status == "failed"


def test_partial_episode_resumes_at_first_missing_stage(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(runner, "resolve_canonical_transcript_asset_paths", lambda *args: object())
    stages = iter(["local_transcription", "completed"])
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: _stage_selection(next(stages)),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_audio_download",
        lambda *args, **kwargs: pytest.fail("must preserve existing audio"),
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_local_transcription",
        lambda podcast_id, *, episode_ref, confirm, model, device, compute_type, vad_filter: _stage_result(),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "ready_for_semantic_summary"
    assert [row.stage for row in result.rows] == [
        "local_transcription",
        "ready_for_semantic_summary",
    ]


def test_already_deterministic_ready_episode_runs_no_stage_executor(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    monkeypatch.setattr(runner, "resolve_canonical_transcript_asset_paths", lambda *args: object())
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: _stage_selection("completed"),
    )
    for name in (
        "run_corpus_audio_download",
        "run_corpus_local_transcription",
        "run_corpus_remediation",
    ):
        monkeypatch.setattr(
            runner,
            name,
            lambda *args, **kwargs: pytest.fail("ready episode must not execute"),
        )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "ready_for_semantic_summary"
    assert result.counts.executed_count == 0


def test_failed_remediation_action_stops_without_second_remediation_probe(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    probe_calls = 0

    def probe(
        *, podcast_id, selector, max_actions, allow_semantic_handoff
    ):
        nonlocal probe_calls
        probe_calls += 1
        return _stage_selection("deterministic_remediation")

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(runner, "_select_episode_workflow_stage", probe)
    monkeypatch.setattr(
        runner,
        "run_corpus_remediation",
        lambda podcast_id, *, episode_ref, confirm, max_actions: _stage_result(
            "failed", action_id="ep100:extractive_summary"
        ),
    )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "failed"
    assert probe_calls == 1
    assert result.rows[-1].action_id == "ep100:extractive_summary"


def test_repeated_remediation_action_stops_without_automatic_retry(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner
    from corpus_ingest_core.models import CorpusEpisodeWorkflowRunRow

    remediation_calls = 0
    selected_public_row = CorpusEpisodeWorkflowRunRow(
        stage="deterministic_remediation",
        status="selected",
        reason="deterministic remediation is the next ready action",
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
        warnings=[],
    )

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: {
            "selected_stage": "deterministic_remediation",
            "episode_ref": "ep100",
            "action_id": "ep100:extractive_summary",
            "rows": [selected_public_row],
            "warnings": [],
        },
    )

    def remediation(podcast_id, *, episode_ref, confirm, max_actions):
        nonlocal remediation_calls
        remediation_calls += 1
        if remediation_calls > 1:
            pytest.fail("repeated remediation must be blocked before a second executor call")
        return _stage_result("executed")

    monkeypatch.setattr(runner, "run_corpus_remediation", remediation)
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "blocked"
    assert remediation_calls == 1
    assert result.rows[-1].reason == "deterministic remediation made no bounded progress"


def test_remediation_execution_cap_blocks_sixth_action_before_executor(monkeypatch):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner
    from corpus_ingest_core.models import CorpusEpisodeWorkflowRunRow

    remediation_calls = 0
    probe_calls = 0
    selected_public_row = CorpusEpisodeWorkflowRunRow(
        stage="deterministic_remediation",
        status="selected",
        reason="deterministic remediation is the next ready action",
        planned_reads=[],
        planned_writes=[],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
        warnings=[],
    )

    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )

    def probe(*, podcast_id, selector, max_actions, allow_semantic_handoff):
        nonlocal probe_calls
        probe_calls += 1
        return {
            "selected_stage": "deterministic_remediation",
            "episode_ref": "ep100",
            "action_id": f"ep100:family-{probe_calls}",
            "rows": [selected_public_row],
            "warnings": [],
        }

    def remediation(podcast_id, *, episode_ref, confirm, max_actions):
        nonlocal remediation_calls
        remediation_calls += 1
        return _stage_result("executed")

    monkeypatch.setattr(runner, "_select_episode_workflow_stage", probe)
    monkeypatch.setattr(runner, "run_corpus_remediation", remediation)
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "blocked"
    assert remediation_calls == 5
    assert probe_calls == 6
    assert result.rows[-1].reason == "deterministic remediation made no bounded progress"


@pytest.mark.parametrize(
    "selected_stage, executor_name",
    [
        ("intake", "run_corpus_episode_intake"),
        ("audio_download", "run_corpus_audio_download"),
        ("local_transcription", "run_corpus_local_transcription"),
        ("deterministic_remediation", "run_corpus_remediation"),
    ],
)
def test_blocked_deterministic_stage_stops_without_later_executor(
    monkeypatch,
    selected_stage,
    executor_name,
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    calls = []

    def intake(podcast_id, *, episode_ref, confirm):
        if episode_ref == "latest" and not confirm:
            return SimpleNamespace(resolved_episode_ref="ep100", rows=[], warnings=[])
        calls.append("run_corpus_episode_intake")
        return _stage_result("blocked")

    monkeypatch.setattr(runner, "run_corpus_episode_intake", intake)
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: _stage_selection(selected_stage),
    )
    for name in (
        "run_corpus_audio_download",
        "run_corpus_local_transcription",
        "run_corpus_remediation",
    ):
        if name == executor_name:
            monkeypatch.setattr(
                runner,
                name,
                lambda *args, _name=name, **kwargs: (
                    calls.append(_name),
                    _stage_result("blocked"),
                )[1],
            )
        else:
            monkeypatch.setattr(
                runner,
                name,
                lambda *args, _name=name, **kwargs: pytest.fail(
                    f"{_name} must not run after a blocked stage"
                ),
            )
    monkeypatch.setattr(runner, "_write_run_report", lambda result: None)

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    assert result.outcome == "blocked"
    assert calls == [executor_name]


def test_latest_runner_has_no_llm_env_or_automatic_cache_dependencies():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    source = Path(runner.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "local_env",
        "llm_provider",
        "semantic_summarizer",
        "run_corpus_semantic_remediation",
        "rebuild_cache",
    ):
        assert forbidden not in source


def test_result_and_confirmed_report_omit_url_query_and_secret_like_text(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    report_paths = SimpleNamespace(
        json_path=tmp_path / "latest.json",
        markdown_path=tmp_path / "latest.md",
    )
    monkeypatch.setattr(
        runner.storage,
        "corpus_latest_episode_deterministic_workflow_run_asset_paths",
        lambda podcast_id: report_paths,
    )
    monkeypatch.setattr(
        runner,
        "run_corpus_episode_intake",
        lambda podcast_id, *, episode_ref, confirm: SimpleNamespace(
            resolved_episode_ref="ep100", rows=[], warnings=[]
        ),
    )
    monkeypatch.setattr(
        runner,
        "_select_episode_workflow_stage",
        lambda *, podcast_id, selector, max_actions, allow_semantic_handoff: {
            "selected_stage": "completed",
            "episode_ref": "ep100",
            "rows": [
                SimpleNamespace(
                    episode_ref="ep100",
                    status="selected",
                    reason="https://example.invalid/?token=secret-value",
                    planned_reads=["https://example.invalid/?token=secret-value"],
                    planned_writes=[],
                    warnings=[],
                )
            ],
            "warnings": [],
        },
    )

    result = runner.run_corpus_latest_episode_deterministic_workflow(
        "gooaye",
        confirm=True,
    )

    payload = runner.result_to_dict(result)
    assert "secret-value" not in str(payload)
    assert "https://" not in str(payload)
    assert report_paths.json_path.exists()
    assert "secret-value" not in report_paths.json_path.read_text(encoding="utf-8")
    assert "secret-value" not in report_paths.markdown_path.read_text(encoding="utf-8")


def test_execution_metadata_keeps_only_safe_paths_labels_and_text():
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    secret = "sk-" + "not-for-output"
    selected_row = runner._row_from_source(
        "ep100",
        "deterministic_remediation",
        _stage_probe("deterministic_remediation").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "executed",
                reason=f"password={secret}",
                planned_reads=[
                    "configured podcast RSS feed",
                    "in-memory corpus snapshot",
                    "data/corpus/gooaye/EP100.seed.json",
                    "C:/private/credentials.json",
                    "data/corpus/../private.json",
                    "data/corpus/gooaye/.env",
                ],
                planned_writes=[
                    "data/corpus/gooaye/EP100.workflow.json",
                    "//private/share/report.json",
                    "data/corpus/gooaye/secret-report.json",
                ],
                output_paths=[
                    "data/reports/gooaye/EP100.report.json",
                    "https://example.invalid/report.json",
                    "data/reports/gooaye/EP100.report.json?token=hidden",
                ],
                source_report_paths=[
                    "data/corpus/gooaye/EP100.plan.json",
                    "data/corpus/gooaye/client_secret.json",
                ],
                warnings=[
                    "safe bounded warning",
                    f"authorization: Bearer {secret}",
                    "private_key=hidden",
                ],
            )
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.planned_reads == [
        "configured podcast RSS feed",
        "in-memory corpus snapshot",
        "data/corpus/gooaye/EP100.seed.json",
    ]
    assert result_row.planned_writes == ["data/corpus/gooaye/EP100.workflow.json"]
    assert result_row.output_paths == ["data/reports/gooaye/EP100.report.json"]
    assert result_row.source_report_paths == ["data/corpus/gooaye/EP100.plan.json"]
    assert result_row.warnings[0] == "safe bounded warning"
    assert result_row.reason == "value omitted by safety boundary"
    assert all(
        marker not in str(result_row)
        for marker in (secret, "authorization", "private_key")
    )


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "token: private-value",
        "password: private-value",
        "ftp://example.invalid/file?sig=private-value",
        "custom://example.invalid/file#sig=private-value",
        "mailto:user@example.com?subject=quarterly-plan",
        "urn:example:item#private-data",
    ),
)
def test_execution_metadata_omits_sensitive_assignments_and_uri_query_fragments(
    unsafe_text,
):
    import corpus_ingest_core.corpus_latest_episode_deterministic_workflow_runner as runner

    selected_row = runner._row_from_source(
        "ep100",
        "deterministic_remediation",
        _stage_probe("deterministic_remediation").rows[0],
    )
    source_result = SimpleNamespace(
        rows=[
            _source_execution_row(
                "ep100",
                "executed",
                reason=unsafe_text,
                warnings=[unsafe_text, "safe bounded warning"],
            )
        ]
    )

    result_row = runner._row_from_execution(selected_row, source_result)

    assert result_row.reason == "value omitted by safety boundary"
    assert result_row.warnings == [
        "value omitted by safety boundary",
        "safe bounded warning",
    ]


def test_latest_workflow_cli_is_thin_and_forwards_only_local_options(monkeypatch, capsys):
    from scripts import run_corpus_latest_episode_deterministic_workflow as cli

    captured = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(outcome="dry_run", episode_ref="EP100")

    monkeypatch.setattr(cli, "run_corpus_latest_episode_deterministic_workflow", fake_run)
    monkeypatch.setattr(
        cli,
        "result_to_dict",
        lambda result: {"outcome": result.outcome, "episode_ref": result.episode_ref},
    )

    assert cli.main(["--podcast", "gooaye", "--transcription-model", "tiny"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "outcome": "dry_run",
        "episode_ref": "EP100",
    }
    assert captured == {
        "args": ("gooaye",),
        "confirm": False,
        "transcription_model": "tiny",
        "transcription_device": "cpu",
        "transcription_compute_type": "int8",
        "transcription_vad_filter": False,
    }
    assert "local_env" not in Path(cli.__file__).read_text(encoding="utf-8")
