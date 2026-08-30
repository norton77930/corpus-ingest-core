from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> None:
    import corpus_ingest_core.corpus_index as corpus_index
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus", raising=False)
    monkeypatch.setattr(
        corpus_index,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _plan_payload(episodes: list[dict], *, podcast_id: str = "gooaye") -> dict:
    return {
        "podcast_id": podcast_id,
        "plan_mode": "deterministic-corpus-remediation-plan-v1",
        "source_scope": "refreshed-local-corpus-index-only",
        "source_corpus_index_json_path": f"data/corpus/{podcast_id}/corpus-index.json",
        "source_corpus_index_markdown_path": f"data/corpus/{podcast_id}/corpus-index.md",
        "episode_count": len(episodes),
        "action_count": sum(len(episode.get("actions", [])) for episode in episodes),
        "blocked_action_count": 0,
        "optional_action_count": 0,
        "gated_action_count": 0,
        "warning_count": 0,
        "episodes": sorted(episodes, key=lambda episode: episode["episode_ref"]),
        "not_investment_advice": True,
    }


def _episode_payload(
    episode_ref: str,
    *,
    title: str = "Alpha",
    audio_status: str = "available",
    audio_path: str | None = None,
    transcript_status: str = "missing",
    transcript_action_status: str | None = "ready",
    extra_actions: list[dict] | None = None,
    warnings: list[dict | str] | None = None,
) -> dict:
    actions: list[dict] = []
    if transcript_action_status is not None:
        actions.append(
            {
                "action_id": f"{episode_ref}:transcript",
                "artifact_family": "transcript",
                "action_type": "transcribe",
                "status": transcript_action_status,
                "order": 2,
                "reason": "transcript artifact is missing",
                "blocking_artifacts": [] if transcript_action_status == "ready" else ["audio"],
                "suggested_command": f"python scripts/transcribe_episode.py --podcast gooaye --episode {episode_ref}",
                "manual_only": True,
                "optional": False,
                "gated": False,
                "requires_api_cost_ack": False,
            }
        )
    actions.extend(extra_actions or [])
    audio_paths = {"audio": audio_path} if audio_path is not None else {}
    return {
        "podcast_id": "gooaye",
        "episode_ref": episode_ref,
        "title": title,
        "artifact_status": {
            "audio": {"status": audio_status, "paths": audio_paths},
            "transcript": {"status": transcript_status, "paths": {}},
        },
        "missing_artifacts": ["transcript"] if transcript_status == "missing" else [],
        "blockers": [],
        "warnings": warnings or [],
        "actions": actions,
    }


def _extra_action(episode_ref: str, family: str, status: str = "ready") -> dict:
    return {
        "action_id": f"{episode_ref}:{family}",
        "artifact_family": family,
        "action_type": "generate",
        "status": status,
        "order": 9,
        "reason": f"{family} artifact is missing",
        "blocking_artifacts": [],
        "suggested_command": "python scripts/placeholder.py",
        "manual_only": True,
        "optional": family.startswith("semantic"),
        "gated": family == "semantic_summary",
        "requires_api_cost_ack": family == "semantic_summary",
    }


def _fake_plan_refresh(monkeypatch, tmp_path: Path, payload: dict, calls: list[str] | None = None):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core import storage
    from corpus_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    def fake_generate(podcast_id: str) -> CorpusRemediationPlanResult:
        if calls is not None:
            calls.append(f"refresh:{podcast_id}")
        paths = storage.corpus_remediation_plan_asset_paths(podcast_id)
        _write_json(paths.json_path, payload)
        paths.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        paths.markdown_path.write_text("# fake remediation plan", encoding="utf-8")
        return CorpusRemediationPlanResult(
            podcast_id=podcast_id,
            plan_json_path=paths.json_path,
            plan_markdown_path=paths.markdown_path,
            source_corpus_index_json_path=Path(payload["source_corpus_index_json_path"]),
            source_corpus_index_markdown_path=Path(payload["source_corpus_index_markdown_path"]),
            episode_count=payload["episode_count"],
            warning_count=payload["warning_count"],
            action_counts=CorpusRemediationActionCounts(
                action_count=payload["action_count"],
                blocked_action_count=payload["blocked_action_count"],
                optional_action_count=payload["optional_action_count"],
                gated_action_count=payload["gated_action_count"],
            ),
        )

    monkeypatch.setattr(runner, "generate_corpus_remediation_plan", fake_generate)
    return fake_generate


def _result_payload(result) -> dict:
    return _stringify(asdict(result))


def _stringify(value):
    if isinstance(value, dict):
        return {key: _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _rows_by_episode(result) -> dict[str, object]:
    return {row.episode_ref: row for row in result.rows}


def _transcript_asset(
    tmp_path: Path,
    *,
    episode_ref: str = "EP001",
    already_exists: bool = False,
):
    from corpus_ingest_core.models import TranscriptAsset

    return TranscriptAsset(
        podcast_id="gooaye",
        episode_ref=episode_ref,
        title=episode_ref,
        audio_path=tmp_path / "audio" / f"{episode_ref}.mp3",
        text_path=tmp_path / "transcripts" / f"{episode_ref}.txt",
        srt_path=tmp_path / "transcripts" / f"{episode_ref}.srt",
        json_path=tmp_path / "transcripts" / f"{episode_ref}.json",
        model="tiny",
        language="zh",
        segment_count=1,
        transcribed=not already_exists,
        already_exists=already_exists,
    )


def test_preview_corpus_local_transcription_from_in_memory_plan(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core import storage
    from corpus_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    audio_path = storage.AUDIO_DIR / "gooaye" / "EP677__Alpha.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"mp3")
    payload = _plan_payload([_episode_payload("EP677", title="Alpha", audio_path=str(audio_path))])
    paths = storage.corpus_remediation_plan_asset_paths("gooaye")
    plan_result = CorpusRemediationPlanResult(
        podcast_id="gooaye",
        plan_json_path=paths.json_path,
        plan_markdown_path=paths.markdown_path,
        source_corpus_index_json_path=tmp_path / "corpus-index.json",
        source_corpus_index_markdown_path=tmp_path / "corpus-index.md",
        episode_count=1,
        warning_count=0,
        action_counts=CorpusRemediationActionCounts(
            action_count=1,
            blocked_action_count=0,
            optional_action_count=0,
            gated_action_count=0,
        ),
    )

    result = runner._preview_corpus_local_transcription_from_plan(
        "gooaye",
        plan_result=plan_result,
        plan_payload=payload,
        episode_ref="EP677",
        source_persisted=False,
    )

    assert result.counts.selected_count == 1
    assert "in-memory corpus snapshot" in result.rows[0].planned_reads
    assert str(audio_path) in result.rows[0].planned_reads
    assert not paths.json_path.exists()
    assert not paths.markdown_path.exists()


def test_standalone_dry_run_still_refreshes_index_and_plan_without_stage_report(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_json(
        storage.corpus_episode_seed_asset_path("gooaye", "EP677"),
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP677",
            "title": "Alpha",
            "has_audio_url": True,
            "guid_status": "present",
            "seed_source": "rss",
            "selector": "latest",
            "warning_count": 0,
        },
    )
    audio_path = storage.AUDIO_DIR / "gooaye" / "EP677__Alpha.mp3"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"mp3")
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda *args, **kwargs: pytest.fail("dry-run executed transcriber"),
    )

    result = runner.run_corpus_local_transcription(
        "gooaye",
        episode_ref="EP677",
        confirm=False,
    )

    index_paths = storage.corpus_index_asset_paths("gooaye")
    plan_paths = storage.corpus_remediation_plan_asset_paths("gooaye")
    report_paths = storage.corpus_local_transcription_run_asset_paths("gooaye")
    assert result.counts.selected_count == 1
    assert result.source_remediation_plan_json_path == plan_paths.json_path
    assert result.source_remediation_plan_markdown_path == plan_paths.markdown_path
    assert index_paths.json_path.exists()
    assert index_paths.markdown_path.exists()
    assert plan_paths.json_path.exists()
    assert plan_paths.markdown_path.exists()
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert not report_paths.json_path.exists()
    assert not report_paths.markdown_path.exists()


def test_corpus_local_transcription_run_asset_paths_contract():
    from corpus_ingest_core.storage import corpus_local_transcription_run_asset_paths

    paths = corpus_local_transcription_run_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-local-transcription-run.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-local-transcription-run.md")


def test_corpus_local_transcription_public_result_contract_exports(tmp_path):
    from corpus_ingest_core import (
        CorpusLocalTranscriptionOutcomeCounts,
        CorpusLocalTranscriptionRunFilter,
        CorpusLocalTranscriptionRunnerFailedError,
        CorpusLocalTranscriptionRunResult,
        CorpusLocalTranscriptionRunRow,
        CorpusLocalTranscriptionRunWarning,
        run_corpus_local_transcription,
    )

    filters = CorpusLocalTranscriptionRunFilter(episode_ref="EP672")
    counts = CorpusLocalTranscriptionOutcomeCounts(
        row_count=1,
        selected_count=1,
        executed_count=0,
        reused_count=0,
        failed_count=0,
        skipped_count=0,
        rejected_count=0,
        warning_count=0,
    )
    warning = CorpusLocalTranscriptionRunWarning(
        scope="run",
        episode_ref=None,
        message="cache metadata may be stale",
    )
    row = CorpusLocalTranscriptionRunRow(
        action_id="EP672:transcript",
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Alpha",
        transcript_status="missing",
        audio_status="available",
        audio_path=str(tmp_path / "audio" / "EP672.mp3"),
        outcome_status="selected",
        reason="local audio available and transcript missing",
        planned_reads=[str(tmp_path / "audio" / "EP672.mp3")],
        planned_writes=[str(tmp_path / "transcripts" / "EP672.json")],
        output_paths=[],
        warnings=[],
    )
    result = CorpusLocalTranscriptionRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=counts,
        rows=[row],
        warnings=[warning],
        not_investment_advice=True,
    )

    assert asdict(result)["filters"]["episode_ref"] == "EP672"
    assert result.counts.selected_count == 1
    assert CorpusLocalTranscriptionRunnerFailedError.__name__ == ("CorpusLocalTranscriptionRunnerFailedError")
    assert callable(run_corpus_local_transcription)


def test_corpus_local_transcription_runner_error_contract():
    from corpus_ingest_core import (
        CorpusLocalTranscriptionRunnerFailedError,
        PodcastIngestCoreError,
    )

    assert issubclass(CorpusLocalTranscriptionRunnerFailedError, PodcastIngestCoreError)


def test_dry_run_empty_corpus_writes_no_report(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )
    from corpus_ingest_core.storage import corpus_local_transcription_run_asset_paths

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([]))

    result = run_corpus_local_transcription("gooaye")

    paths = corpus_local_transcription_run_asset_paths("gooaye")
    assert result.run_mode == "dry_run"
    assert result.counts.row_count == 0
    assert result.counts.selected_count == 0
    assert result.counts.executed_count == 0
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert not paths.json_path.exists()
    assert not paths.markdown_path.exists()


def test_dry_run_refreshes_remediation_plan_before_selection(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    calls: list[str] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
        calls,
    )

    result = run_corpus_local_transcription("gooaye")

    assert calls == ["refresh:gooaye"]
    assert result.counts.selected_count == 1
    assert result.rows[0].episode_ref == "EP001"


def test_dry_run_selects_only_local_audio_transcript_missing(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    selected_audio = tmp_path / "audio" / "EP001.mp3"
    selected_audio.parent.mkdir(parents=True)
    selected_audio.write_bytes(b"audio")
    missing_path = tmp_path / "audio" / "missing.mp3"
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                _episode_payload("EP001", audio_path=str(selected_audio)),
                _episode_payload("EP002", audio_status="missing", audio_path=None),
                _episode_payload("EP003", audio_path=str(missing_path)),
                _episode_payload(
                    "EP004", audio_path=str(selected_audio), transcript_status="valid", transcript_action_status=None
                ),
                _episode_payload(
                    "EP005", audio_path=str(selected_audio), transcript_status="empty", transcript_action_status=None
                ),
            ]
        ),
    )

    result = run_corpus_local_transcription("gooaye")
    rows = _rows_by_episode(result)

    assert rows["EP001"].outcome_status == "selected"
    assert rows["EP002"].outcome_status == "skipped"
    assert rows["EP003"].outcome_status == "skipped"
    assert rows["EP004"].outcome_status == "skipped"
    assert rows["EP005"].outcome_status == "skipped"
    assert result.counts.selected_count == 1
    assert result.counts.skipped_count == 4


def test_dry_run_skips_unsafe_transcript_states_and_other_families(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    episodes = [
        _episode_payload(
            f"EP00{index}",
            audio_path=str(audio),
            transcript_status=status,
            transcript_action_status="ready" if status in {"missing", "unreadable"} else None,
        )
        for index, status in enumerate(
            ["unreadable", "corrupt", "partial", "incomplete", "valid", "empty"],
            start=1,
        )
    ]
    episodes.append(
        _episode_payload(
            "EP099",
            audio_path=str(audio),
            transcript_status="missing",
            extra_actions=[
                _extra_action("EP099", "semantic_summary"),
                _extra_action("EP099", "mentions"),
                _extra_action("EP099", "stock_lens_synthesis"),
            ],
        )
    )
    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload(episodes))

    result = run_corpus_local_transcription("gooaye")
    statuses = [row.outcome_status for row in result.rows]
    reasons = " ".join(row.reason for row in result.rows).lower()

    assert result.counts.selected_count == 1
    assert statuses.count("skipped") >= 8
    assert "unreadable" in reasons
    assert "corrupt" in reasons
    assert "partial" in reasons
    assert "incomplete" in reasons
    assert "valid" in reasons
    assert "empty" in reasons
    assert "semantic_summary" in reasons
    assert "stock_lens_synthesis" in reasons


def test_dry_run_no_transcription_download_model_load_or_report_write(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )
    from corpus_ingest_core.storage import corpus_local_transcription_run_asset_paths

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run must not execute transcription")

    monkeypatch.setattr(runner, "transcribe_episode", forbidden)

    result = run_corpus_local_transcription("gooaye")

    report_paths = corpus_local_transcription_run_asset_paths("gooaye")
    assert result.counts.selected_count == 1
    assert not report_paths.json_path.exists()
    assert not report_paths.markdown_path.exists()


def test_dry_run_is_deterministic_and_has_no_generated_at(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP002.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    payload = _plan_payload(
        [
            _episode_payload("EP002", audio_path=str(audio)),
            _episode_payload("EP001", audio_path=str(audio), transcript_status="valid", transcript_action_status=None),
        ]
    )
    _fake_plan_refresh(monkeypatch, tmp_path, payload)

    first = _result_payload(run_corpus_local_transcription("gooaye"))
    second = _result_payload(run_corpus_local_transcription("gooaye"))
    text = json.dumps(first, ensure_ascii=False, sort_keys=True)

    assert first == second
    assert "generated_at" not in text


def test_run_corpus_local_transcription_cli_dry_run_outputs_json(monkeypatch, capsys, tmp_path):
    from scripts import run_corpus_local_transcription as cli

    from corpus_ingest_core.models import (
        CorpusLocalTranscriptionOutcomeCounts,
        CorpusLocalTranscriptionRunFilter,
        CorpusLocalTranscriptionRunResult,
    )

    result = CorpusLocalTranscriptionRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusLocalTranscriptionRunFilter(None),
        counts=CorpusLocalTranscriptionOutcomeCounts(
            row_count=2,
            selected_count=1,
            executed_count=0,
            reused_count=0,
            failed_count=0,
            skipped_count=1,
            rejected_count=0,
            warning_count=0,
        ),
        rows=[],
        warnings=[],
        not_investment_advice=True,
    )
    captured = {}

    def fake_run(podcast_id: str, **kwargs):
        captured["podcast_id"] = podcast_id
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr(cli, "run_corpus_local_transcription", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_corpus_local_transcription.py", "--podcast", "gooaye"],
    )

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["podcast_id"] == "gooaye"
    assert captured["kwargs"]["confirm"] is False
    assert payload["run_mode"] == "dry_run"
    assert payload["report_json_path"] is None
    assert payload["selected_count"] == 1
    assert payload["skipped_count"] == 1


def test_confirmed_execution_rejects_missing_episode_before_transcription(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core import CorpusLocalTranscriptionRunnerFailedError
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([]))
    calls: list[str] = []

    def fake_transcribe(*args, **kwargs):
        calls.append("transcribe")
        return _transcript_asset(tmp_path)

    monkeypatch.setattr(runner, "transcribe_episode", fake_transcribe)

    with pytest.raises(CorpusLocalTranscriptionRunnerFailedError, match="episode"):
        run_corpus_local_transcription("gooaye", confirm=True)

    assert calls == []


@pytest.mark.parametrize("episode_ref", ["", "   "])
def test_confirmed_execution_rejects_blank_episode_before_transcription(monkeypatch, tmp_path, episode_ref):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core import CorpusLocalTranscriptionRunnerFailedError
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([]))
    calls: list[str] = []
    monkeypatch.setattr(runner, "transcribe_episode", lambda *args, **kwargs: calls.append("transcribe"))

    with pytest.raises(CorpusLocalTranscriptionRunnerFailedError, match="episode"):
        run_corpus_local_transcription("gooaye", confirm=True, episode_ref=episode_ref)

    assert calls == []


def test_confirmed_execution_records_absent_requested_episode_as_rejected(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    calls: list[str] = []
    monkeypatch.setattr(runner, "transcribe_episode", lambda *args, **kwargs: calls.append("transcribe"))

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP999")

    assert calls == []
    assert result.counts.rejected_count == 1
    assert result.rows[-1].episode_ref == "EP999"
    assert result.rows[-1].outcome_status == "rejected"
    assert result.rows[-1].reason == "requested episode is not present in refreshed remediation plan"


def test_confirmed_execution_records_non_eligible_episode_without_transcription(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [_episode_payload("EP001", audio_path=str(audio), transcript_status="valid", transcript_action_status=None)]
        ),
    )
    calls: list[str] = []
    monkeypatch.setattr(runner, "transcribe_episode", lambda *args, **kwargs: calls.append("transcribe"))

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert calls == []
    assert result.counts.rejected_count == 1
    assert result.counts.executed_count == 0
    assert result.rows[0].outcome_status == "rejected"
    assert result.report_json_path is not None
    assert result.report_json_path.exists()


def test_dry_run_planned_writes_match_local_transcriber_output_paths(monkeypatch, tmp_path):
    from corpus_ingest_core import storage
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                _episode_payload(
                    "EP001",
                    title="Human Title",
                    audio_path=str(audio),
                )
            ]
        ),
    )

    result = run_corpus_local_transcription("gooaye")

    paths = storage.transcript_asset_paths("gooaye", "EP001", "Human Title")
    assert result.rows[0].planned_writes == [
        str(paths.json_path),
        str(paths.text_path),
        str(paths.srt_path),
    ]


def test_confirmed_execution_passes_explicit_audio_path_and_force_false(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    calls: list[dict] = []

    def fake_transcribe(podcast_id: str, episode_ref: str, **kwargs):
        calls.append({"podcast_id": podcast_id, "episode_ref": episode_ref, **kwargs})
        return _transcript_asset(tmp_path, episode_ref=episode_ref)

    monkeypatch.setattr(runner, "transcribe_episode", fake_transcribe)

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert result.counts.executed_count == 1
    assert calls == [
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP001",
            "model": None,
            "device": "cpu",
            "compute_type": "int8",
            "vad_filter": False,
            "force": False,
            "audio_path": audio,
            "title": "Alpha",
        }
    ]


def test_confirmed_execution_never_calls_download_or_shell(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: _transcript_asset(tmp_path, episode_ref=episode_ref),
    )

    def forbidden_shell(*args, **kwargs):
        raise AssertionError("runner must not shell out")

    monkeypatch.setattr(subprocess, "run", forbidden_shell)
    monkeypatch.setattr(subprocess, "Popen", forbidden_shell)

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    source = Path("src/corpus_ingest_core/corpus_local_transcription_runner.py").read_text(encoding="utf-8")
    assert "download_audio" not in source
    assert "subprocess" not in source
    assert result.counts.executed_count == 1


def test_confirmed_execution_propagates_runtime_options(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    calls: list[dict] = []

    def fake_transcribe(podcast_id: str, episode_ref: str, **kwargs):
        calls.append(kwargs)
        return _transcript_asset(tmp_path, episode_ref=episode_ref)

    monkeypatch.setattr(runner, "transcribe_episode", fake_transcribe)

    run_corpus_local_transcription(
        "gooaye",
        confirm=True,
        episode_ref="EP001",
        model="small",
        device="cuda",
        compute_type="float16",
        vad_filter=True,
    )

    assert calls[0]["model"] == "small"
    assert calls[0]["device"] == "cuda"
    assert calls[0]["compute_type"] == "float16"
    assert calls[0]["vad_filter"] is True


def test_confirmed_run_report_json_and_markdown_are_written(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: _transcript_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert result.report_json_path is not None
    assert result.report_markdown_path is not None
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    assert payload["run_mode"] == "confirmed"
    assert payload["executed_count"] == 1
    assert payload["rejected_count"] == 0
    assert "generated_at" not in result.report_json_path.read_text(encoding="utf-8")
    assert "Corpus Local Transcription Run - gooaye" in markdown
    assert "not investment advice" in markdown.lower()


def test_cli_confirmed_stdout_and_stderr_contract(monkeypatch, capsys, tmp_path):
    from scripts import run_corpus_local_transcription as cli

    from corpus_ingest_core import CorpusLocalTranscriptionRunnerFailedError
    from corpus_ingest_core.models import (
        CorpusLocalTranscriptionOutcomeCounts,
        CorpusLocalTranscriptionRunFilter,
        CorpusLocalTranscriptionRunResult,
    )

    result = CorpusLocalTranscriptionRunResult(
        podcast_id="gooaye",
        run_mode="confirmed",
        confirm=True,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=tmp_path / "corpus-local-transcription-run.json",
        report_markdown_path=tmp_path / "corpus-local-transcription-run.md",
        filters=CorpusLocalTranscriptionRunFilter("EP001"),
        counts=CorpusLocalTranscriptionOutcomeCounts(
            row_count=1,
            selected_count=1,
            executed_count=1,
            reused_count=0,
            failed_count=0,
            skipped_count=0,
            rejected_count=0,
            warning_count=0,
        ),
        rows=[],
        warnings=[],
        not_investment_advice=True,
    )

    def fake_run(podcast_id: str, **kwargs):
        assert kwargs["confirm"] is True
        assert kwargs["episode_ref"] == "EP001"
        assert kwargs["model"] == "small"
        assert kwargs["device"] == "cuda"
        assert kwargs["compute_type"] == "float16"
        assert kwargs["vad_filter"] is True
        return result

    monkeypatch.setattr(cli, "run_corpus_local_transcription", fake_run)
    assert (
        cli.main(
            [
                "--podcast",
                "gooaye",
                "--episode",
                "EP001",
                "--confirm",
                "--model",
                "small",
                "--device",
                "cuda",
                "--compute-type",
                "float16",
                "--vad-filter",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_json_path"] == str(tmp_path / "corpus-local-transcription-run.json")
    assert payload["executed_count"] == 1

    def rejected(*args, **kwargs):
        raise CorpusLocalTranscriptionRunnerFailedError("confirm requires episode")

    monkeypatch.setattr(cli, "run_corpus_local_transcription", rejected)
    assert cli.main(["--podcast", "gooaye", "--confirm"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "confirm requires episode" in captured.err


def test_transcription_failure_records_metadata_without_traceback(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )

    def fail_transcribe(*args, **kwargs):
        raise RuntimeError("raw transcript sentinel must not leak")

    monkeypatch.setattr(runner, "transcribe_episode", fail_transcribe)

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert result.counts.failed_count == 1
    assert result.rows[0].outcome_status == "failed"
    combined = json.dumps(_result_payload(result), ensure_ascii=False)
    assert "RuntimeError" in combined
    assert "raw transcript sentinel" not in combined
    assert "Traceback" not in combined


def test_outputs_do_not_leak_raw_transcript_prompt_llm_secret_or_traceback(monkeypatch, tmp_path, capsys):
    from scripts import run_corpus_local_transcription as cli

    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    payload = _plan_payload(
        [
            _episode_payload(
                "EP001",
                title="Safe Title",
                audio_path=str(audio),
                warnings=[
                    {
                        "scope": "episode",
                        "episode_ref": "EP001",
                        "artifact_family": "transcript",
                        "message": "API_KEY=secret-value raw transcript sentinel must not leak",
                    },
                    {
                        "scope": "episode",
                        "episode_ref": "EP001",
                        "artifact_family": "transcript",
                        "message": "TOKEN=abc123 bearer xyz provider_config=hidden",
                    },
                ],
            )
        ]
    )
    payload["episodes"][0]["artifact_status"]["transcript"]["body"] = "raw transcript sentinel must not leak"
    payload["episodes"][0]["artifact_status"]["semantic_summary"] = {
        "status": "missing",
        "body": "prompt text sentinel raw LLM output sentinel",
    }
    _fake_plan_refresh(monkeypatch, tmp_path, payload)
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: _transcript_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")
    assert cli.main(["--podcast", "gooaye"]) == 0
    captured = capsys.readouterr()
    combined = "\n".join(
        [
            json.dumps(_result_payload(result), ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
            captured.out,
            captured.err,
        ]
    )
    for forbidden in (
        "raw transcript sentinel",
        "prompt text sentinel",
        "raw LLM output sentinel",
        "API_KEY=secret-value",
        "TOKEN=abc123",
        "bearer xyz",
        "provider_config=hidden",
        "Bearer abc123",
        "Traceback",
    ):
        assert forbidden not in combined


def test_boundary_guard_excludes_forbidden_surfaces_without_execution(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                _episode_payload(
                    "EP001",
                    audio_path=str(audio),
                    extra_actions=[
                        _extra_action("EP001", "audio"),
                        _extra_action("EP001", "semantic_summary"),
                        _extra_action("EP001", "semantic_review"),
                        _extra_action("EP001", "mentions"),
                        _extra_action("EP001", "stock_lens_synthesis"),
                    ],
                )
            ]
        ),
    )
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: (
            calls.append("transcribe") or _transcript_asset(tmp_path, episode_ref=episode_ref)
        ),
    )

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert calls == ["transcribe"]
    assert result.counts.executed_count == 1
    source = Path("src/corpus_ingest_core/corpus_local_transcription_runner.py").read_text(encoding="utf-8")
    forbidden_fragments = [
        "from .cache import",
        "from .downloader import",
        "from .feed_reader import",
        "from .llm_profiles import",
        "from .local_env import",
        "from .mcp_server import",
        "from .semantic_summarizer import",
        "from .stock_lens",
        "requests",
        "urllib",
        "httpx",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_confirmed_writes_manual_cache_stale_warning_without_rebuild(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: _transcript_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert any("cache" in warning.message.lower() for warning in result.warnings)
    source = Path("src/corpus_ingest_core/corpus_local_transcription_runner.py").read_text(encoding="utf-8")
    assert "rebuild_cache(" not in source


def test_outputs_keep_no_investment_advice_boundary(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_local_transcription_runner as runner
    from corpus_ingest_core.corpus_local_transcription_runner import (
        run_corpus_local_transcription,
    )

    audio = tmp_path / "audio" / "EP001.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_path=str(audio))]),
    )
    monkeypatch.setattr(
        runner,
        "transcribe_episode",
        lambda podcast_id, episode_ref, **kwargs: _transcript_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_local_transcription("gooaye", confirm=True, episode_ref="EP001")

    assert result.not_investment_advice is True
    combined = json.dumps(_result_payload(result), ensure_ascii=False).lower()
    combined += result.report_markdown_path.read_text(encoding="utf-8").lower()
    assert "not investment advice" in combined
    for forbidden in (
        "buy recommendation",
        "sell recommendation",
        "target price",
        "guaranteed return",
    ):
        assert forbidden not in combined
