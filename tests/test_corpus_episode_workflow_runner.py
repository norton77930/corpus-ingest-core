from __future__ import annotations

from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> None:
    from podcast_ingest_core import storage
    import podcast_ingest_core.corpus_index as corpus_index

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


def _write_seed(monkeypatch, tmp_path: Path, episode_ref: str = "EP677") -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    path = storage.corpus_episode_seed_asset_path("gooaye", episode_ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": f"{episode_ref} Alpha",
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
    return path


def _stringify(value):
    if isinstance(value, dict):
        return {key: _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _result_payload(result) -> dict:
    from podcast_ingest_core.corpus_episode_workflow_runner import result_to_dict

    return result_to_dict(result)


def _intake_result(
    tmp_path: Path,
    *,
    selector: str = "latest",
    episode_ref: str | None = "EP677",
    status: str = "selected",
    confirm: bool = False,
):
    from podcast_ingest_core.models import (
        CorpusEpisodeIntakeFilter,
        CorpusEpisodeIntakeOutcomeCounts,
        CorpusEpisodeIntakeRunResult,
        CorpusEpisodeIntakeRunRow,
    )

    seeded = 1 if confirm and status == "seeded" else 0
    reused = 1 if confirm and status == "reused" else 0
    failed = 1 if status == "failed" else 0
    rejected = 1 if status == "rejected" else 0
    row = CorpusEpisodeIntakeRunRow(
        podcast_id="gooaye",
        selector=selector,
        episode_ref=episode_ref,
        title=f"{episode_ref or selector} Alpha" if episode_ref else None,
        published_at="Thu, 09 Jul 2026 00:00:00 GMT" if episode_ref else None,
        duration="00:42:00" if episode_ref else None,
        guid_status="present" if episode_ref else "missing",
        has_audio_url=episode_ref is not None,
        outcome_status=status,
        reason="episode resolved from configured feed",
        planned_reads=["configured podcast RSS feed"],
        planned_writes=[str(tmp_path / "corpus" / "gooaye" / "seed.json")]
        if episode_ref
        else [],
        seed_json_path=str(tmp_path / "corpus" / "gooaye" / "seed.json")
        if episode_ref
        else None,
        warnings=[],
    )
    return CorpusEpisodeIntakeRunResult(
        podcast_id="gooaye",
        run_mode="confirmed" if confirm else "dry_run",
        confirm=confirm,
        selector=selector,
        resolved_episode_ref=episode_ref,
        report_json_path=tmp_path / "intake.json" if confirm else None,
        report_markdown_path=tmp_path / "intake.md" if confirm else None,
        filters=CorpusEpisodeIntakeFilter(selector),
        counts=CorpusEpisodeIntakeOutcomeCounts(
            row_count=1,
            selected_count=1 if status in {"selected", "seeded", "reused"} else 0,
            seeded_count=seeded,
            reused_count=reused,
            failed_count=failed,
            skipped_count=0,
            rejected_count=rejected,
            warning_count=0,
        ),
        rows=[row],
        warnings=[],
        not_investment_advice=True,
    )


def _audio_result(
    tmp_path: Path,
    *,
    episode_ref: str = "EP677",
    status: str = "skipped",
    confirm: bool = False,
):
    from podcast_ingest_core.models import (
        CorpusAudioDownloadOutcomeCounts,
        CorpusAudioDownloadRunFilter,
        CorpusAudioDownloadRunResult,
        CorpusAudioDownloadRunRow,
    )

    return CorpusAudioDownloadRunResult(
        podcast_id="gooaye",
        run_mode="confirmed" if confirm else "dry_run",
        confirm=confirm,
        source_remediation_plan_json_path=tmp_path / "plan.json",
        source_remediation_plan_markdown_path=tmp_path / "plan.md",
        report_json_path=tmp_path / "audio.json" if confirm else None,
        report_markdown_path=tmp_path / "audio.md" if confirm else None,
        filters=CorpusAudioDownloadRunFilter(episode_ref),
        counts=CorpusAudioDownloadOutcomeCounts(
            row_count=1,
            selected_count=1 if status == "selected" else 0,
            downloaded_count=1 if status == "downloaded" else 0,
            reused_count=1 if status == "reused" else 0,
            failed_count=1 if status == "failed" else 0,
            skipped_count=1 if status == "skipped" else 0,
            rejected_count=1 if status == "rejected" else 0,
            warning_count=0,
        ),
        rows=[
            CorpusAudioDownloadRunRow(
                action_id=f"{episode_ref}:audio",
                podcast_id="gooaye",
                episode_ref=episode_ref,
                audio_status="missing" if status == "selected" else "available",
                outcome_status=status,
                reason="audio missing and download action ready",
                planned_reads=[str(tmp_path / "plan.json")],
                planned_writes=[str(tmp_path / "audio.mp3")],
                local_audio_path=None,
                content_type=None,
                size_bytes=None,
                warnings=[],
            )
        ],
        warnings=[],
        not_investment_advice=True,
    )


def _transcription_result(
    tmp_path: Path,
    *,
    episode_ref: str = "EP677",
    status: str = "skipped",
    confirm: bool = False,
):
    from podcast_ingest_core.models import (
        CorpusLocalTranscriptionOutcomeCounts,
        CorpusLocalTranscriptionRunFilter,
        CorpusLocalTranscriptionRunResult,
        CorpusLocalTranscriptionRunRow,
    )

    return CorpusLocalTranscriptionRunResult(
        podcast_id="gooaye",
        run_mode="confirmed" if confirm else "dry_run",
        confirm=confirm,
        source_remediation_plan_json_path=tmp_path / "plan.json",
        source_remediation_plan_markdown_path=tmp_path / "plan.md",
        report_json_path=tmp_path / "transcription.json" if confirm else None,
        report_markdown_path=tmp_path / "transcription.md" if confirm else None,
        filters=CorpusLocalTranscriptionRunFilter(episode_ref),
        counts=CorpusLocalTranscriptionOutcomeCounts(
            row_count=1,
            selected_count=1 if status == "selected" else 0,
            executed_count=1 if status == "executed" else 0,
            reused_count=1 if status == "reused" else 0,
            failed_count=1 if status == "failed" else 0,
            skipped_count=1 if status == "skipped" else 0,
            rejected_count=1 if status == "rejected" else 0,
            warning_count=0,
        ),
        rows=[
            CorpusLocalTranscriptionRunRow(
                action_id=f"{episode_ref}:transcript",
                podcast_id="gooaye",
                episode_ref=episode_ref,
                title=episode_ref,
                transcript_status="missing" if status == "selected" else "valid",
                audio_status="available",
                audio_path=str(tmp_path / "audio.mp3"),
                outcome_status=status,
                reason="local audio available and transcript missing",
                planned_reads=[str(tmp_path / "audio.mp3")],
                planned_writes=[str(tmp_path / "transcript.json")],
                output_paths=[str(tmp_path / "transcript.json")]
                if status in {"executed", "reused"}
                else [],
                warnings=[],
            )
        ],
        warnings=[],
        not_investment_advice=True,
    )


def _remediation_result(
    tmp_path: Path,
    *,
    episode_ref: str = "EP677",
    status: str = "skipped",
    family: str = "mentions",
    confirm: bool = False,
):
    from podcast_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
        CorpusRemediationRunRow,
    )

    excluded = 1 if status == "excluded" else 0
    selected = 1 if status == "selected" else 0
    return CorpusRemediationRunResult(
        podcast_id="gooaye",
        run_mode="confirmed" if confirm else "dry_run",
        confirm=confirm,
        source_remediation_plan_json_path=tmp_path / "plan.json",
        source_remediation_plan_markdown_path=tmp_path / "plan.md",
        report_json_path=tmp_path / "remediation.json" if confirm else None,
        report_markdown_path=tmp_path / "remediation.md" if confirm else None,
        filters=CorpusRemediationRunFilter(episode_ref, None, None),
        counts=CorpusRemediationRunCounts(
            row_count=1,
            selected_count=selected,
            executed_count=1 if status == "executed" else 0,
            reused_count=1 if status == "reused" else 0,
            failed_count=1 if status == "failed" else 0,
            skipped_count=1 if status == "skipped" else 0,
            blocked_count=1 if status == "blocked" else 0,
            excluded_count=excluded,
            warning_count=0,
        ),
        rows=[
            CorpusRemediationRunRow(
                action_id=f"{episode_ref}:{family}",
                podcast_id="gooaye",
                episode_ref=episode_ref,
                title=episode_ref,
                artifact_family=family,
                source_status="ready",
                outcome_status=status,
                reason=f"{family} ready",
                planned_reads=[str(tmp_path / "transcript.json")],
                planned_writes=[str(tmp_path / f"{family}.json")],
                output_paths=[str(tmp_path / f"{family}.json")]
                if status in {"executed", "reused"}
                else [],
                warnings=[],
            )
        ],
        warnings=[],
        not_investment_advice=True,
    )


def _install_stage_doubles(
    monkeypatch,
    tmp_path: Path,
    calls: list[tuple[str, dict]],
    *,
    intake=None,
    audio=None,
    transcription=None,
    remediation=None,
):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner

    def fake_intake(podcast_id: str, **kwargs):
        calls.append(("intake", kwargs))
        return intake or _intake_result(
            tmp_path,
            selector=kwargs.get("episode_ref", "latest"),
            confirm=kwargs.get("confirm", False),
            status="seeded" if kwargs.get("confirm", False) else "selected",
        )

    def fake_audio(podcast_id: str, **kwargs):
        calls.append(("audio", kwargs))
        result = audio
        if callable(result):
            return result(kwargs)
        return result or _audio_result(
            tmp_path,
            episode_ref=kwargs.get("episode_ref") or "EP677",
            status="skipped",
            confirm=kwargs.get("confirm", False),
        )

    def fake_transcription(podcast_id: str, **kwargs):
        calls.append(("transcription", kwargs))
        result = transcription
        if callable(result):
            return result(kwargs)
        return result or _transcription_result(
            tmp_path,
            episode_ref=kwargs.get("episode_ref") or "EP677",
            status="skipped",
            confirm=kwargs.get("confirm", False),
        )

    def fake_remediation(podcast_id: str, **kwargs):
        calls.append(("remediation", kwargs))
        result = remediation
        if callable(result):
            return result(kwargs)
        return result or _remediation_result(
            tmp_path,
            episode_ref=kwargs.get("episode_ref") or "EP677",
            status="skipped",
            confirm=kwargs.get("confirm", False),
        )

    monkeypatch.setattr(runner, "run_corpus_episode_intake", fake_intake)
    monkeypatch.setattr(runner, "run_corpus_audio_download", fake_audio)
    monkeypatch.setattr(runner, "run_corpus_local_transcription", fake_transcription)
    monkeypatch.setattr(runner, "run_corpus_remediation", fake_remediation)


def _with_selected_and_terminal_rows(terminal_result, selected_result):
    return replace(
        terminal_result,
        rows=[selected_result.rows[0], terminal_result.rows[0]],
    )


def test_corpus_episode_workflow_run_asset_paths_contract():
    from podcast_ingest_core.storage import corpus_episode_workflow_run_asset_paths

    paths = corpus_episode_workflow_run_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-episode-workflow-run.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-episode-workflow-run.md")


def test_corpus_episode_workflow_public_result_contract_exports(tmp_path):
    from podcast_ingest_core import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunResult,
        CorpusEpisodeWorkflowRunRow,
        CorpusEpisodeWorkflowRunWarning,
        CorpusEpisodeWorkflowRunnerFailedError,
        run_corpus_episode_workflow,
    )

    filters = CorpusEpisodeWorkflowRunFilter(
        episode_ref="latest",
        stage="next",
        max_actions=1,
    )
    counts = CorpusEpisodeWorkflowRunCounts(
        row_count=1,
        selected_count=1,
        executed_count=0,
        reused_count=0,
        failed_count=0,
        skipped_count=0,
        blocked_count=0,
        rejected_count=0,
        manual_only_count=0,
        warning_count=0,
    )
    warning = CorpusEpisodeWorkflowRunWarning(
        scope="run",
        episode_ref="EP677",
        message="cache rebuild remains manual",
    )
    row = CorpusEpisodeWorkflowRunRow(
        stage="intake",
        status="selected",
        reason="episode seed missing",
        planned_reads=["configured podcast RSS feed"],
        planned_writes=[str(tmp_path / "seed.json")],
        output_paths=[],
        source_report_paths=[],
        stage_counts={},
        warnings=[],
    )
    result = CorpusEpisodeWorkflowRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        selector="latest",
        episode_ref="EP677",
        stage="next",
        selected_stage="intake",
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=counts,
        rows=[row],
        warnings=[warning],
        not_investment_advice=True,
    )

    assert asdict(result)["filters"]["episode_ref"] == "latest"
    assert result.counts.selected_count == 1
    assert CorpusEpisodeWorkflowRunnerFailedError.__name__ == (
        "CorpusEpisodeWorkflowRunnerFailedError"
    )
    assert callable(run_corpus_episode_workflow)


def test_corpus_episode_workflow_runner_error_contract():
    from podcast_ingest_core import (
        CorpusEpisodeWorkflowRunnerFailedError,
        PodcastIngestCoreError,
    )

    assert issubclass(CorpusEpisodeWorkflowRunnerFailedError, PodcastIngestCoreError)


def test_dry_run_unseeded_latest_selects_intake_and_writes_no_report(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from podcast_ingest_core.storage import corpus_episode_workflow_run_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(monkeypatch, tmp_path, calls)

    result = run_corpus_episode_workflow("gooaye", episode_ref="latest")

    report_paths = corpus_episode_workflow_run_asset_paths("gooaye")
    assert result.run_mode == "dry_run"
    assert result.selector == "latest"
    assert result.episode_ref == "EP677"
    assert result.selected_stage == "intake"
    assert result.counts.selected_count == 1
    assert result.report_json_path is None
    assert not report_paths.json_path.exists()
    assert [name for name, _ in calls] == ["intake"]


def test_dry_run_seeded_missing_audio_selects_audio_download(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="selected"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "audio_download"
    assert result.rows[0].stage == "audio_download"
    assert result.rows[0].status == "selected"
    assert [name for name, _ in calls] == ["intake", "audio"]


def test_dry_run_local_audio_transcript_missing_selects_local_transcription(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="selected"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "local_transcription"
    assert result.rows[0].stage == "local_transcription"
    assert [name for name, _ in calls] == ["intake", "audio", "transcription"]


def test_dry_run_transcript_ready_selects_deterministic_remediation(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=_remediation_result(tmp_path, status="selected"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "deterministic_remediation"
    assert result.rows[0].stage == "deterministic_remediation"
    assert [name for name, _ in calls] == [
        "intake",
        "audio",
        "transcription",
        "remediation",
    ]


def test_dry_run_completed_state_has_no_executable_stage(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=_remediation_result(tmp_path, status="skipped"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "completed"
    assert result.rows[0].status == "completed"
    assert result.counts.selected_count == 0


def test_blank_selector_defaults_to_latest_and_unsupported_stage_rejected(
    monkeypatch, tmp_path
):
    from podcast_ingest_core import CorpusEpisodeWorkflowRunnerFailedError
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(monkeypatch, tmp_path, calls)

    result = run_corpus_episode_workflow("gooaye", episode_ref="   ")
    assert result.selector == "latest"
    assert calls[0][1]["episode_ref"] == "latest"

    with pytest.raises(CorpusEpisodeWorkflowRunnerFailedError, match="stage"):
        run_corpus_episode_workflow("gooaye", stage="all")


def test_dry_run_does_not_execute_confirmed_stage_runners_or_forbidden_surfaces(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="selected"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")
    assert result.selected_stage == "audio_download"
    assert all(not kwargs.get("confirm") for _name, kwargs in calls)

    source = inspect.getsource(runner).lower()
    for forbidden in (
        "from .cache import",
        "from .llm_profiles import",
        "from .local_env import",
        "from .mcp_server import",
        "from .semantic_summarizer import",
        "from .stock_lens",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "rebuild_cache(",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    ('attribute', 'stage'),
    [
        ('run_corpus_audio_download', 'audio_download'),
        ('run_corpus_local_transcription', 'local_transcription'),
        ('run_corpus_remediation', 'deterministic_remediation'),
    ],
)
@pytest.mark.parametrize('confirm', [False, True])
def test_probe_exception_blocks_confirmed_dispatch(
    monkeypatch, tmp_path, attribute, stage, confirm
):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner
    _write_seed(monkeypatch, tmp_path)
    _install_stage_doubles(monkeypatch, tmp_path, [])
    paths = runner.storage.corpus_episode_workflow_run_asset_paths('gooaye')
    seen = []
    def fail(*args, **kwargs):
        seen.append(kwargs['confirm'])
        if not kwargs['confirm']:
            raise RuntimeError('unsafe')
        return _audio_result(tmp_path, status='executed', confirm=True)
    monkeypatch.setattr(runner, attribute, fail)
    result = runner.run_corpus_episode_workflow(
        'gooaye', episode_ref='EP677', confirm=confirm
    )
    assert result.selected_stage == 'blocked'
    assert result.rows[0].status == 'failed'
    assert result.rows[0].stage == stage
    assert seen == [False]
    if confirm:
        assert result.report_json_path is not None
        assert result.report_markdown_path is not None
        assert result.report_json_path.exists()
        assert result.report_markdown_path.exists()
    else:
        assert result.report_json_path is None
        assert result.report_markdown_path is None
        assert not paths.json_path.exists()
        assert not paths.markdown_path.exists()

@pytest.mark.parametrize('confirm', [False, True])
def test_intake_probe_exception_is_bounded(monkeypatch, tmp_path, confirm):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner
    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_stage_doubles(monkeypatch, tmp_path, [])
    paths = runner.storage.corpus_episode_workflow_run_asset_paths('gooaye')
    seen = []
    def fail(*args, **kwargs):
        seen.append(kwargs['confirm'])
        raise RuntimeError('unsafe')
    monkeypatch.setattr(runner, 'run_corpus_episode_intake', fail)
    result = runner.run_corpus_episode_workflow(
        'gooaye', episode_ref='EP677', confirm=confirm
    )
    assert result.selected_stage == 'blocked'
    assert [(row.stage, row.status) for row in result.rows] == [
        ('intake', 'failed')
    ]
    assert seen == [False]
    if confirm:
        assert result.report_json_path is not None
        assert result.report_markdown_path is not None
        assert result.report_json_path.exists()
        assert result.report_markdown_path.exists()
    else:
        assert result.report_json_path is None
        assert result.report_markdown_path is None
        assert not paths.json_path.exists()
        assert not paths.markdown_path.exists()

@pytest.mark.parametrize('confirm', [False, True], ids=['dry_run', 'confirmed'])
@pytest.mark.parametrize('terminal_status', ['failed', 'rejected', 'blocked'])
@pytest.mark.parametrize(
    ('probe_stage', 'expected_calls'),
    [
        ('intake', ['intake']),
        ('audio_download', ['intake', 'audio']),
        (
            'local_transcription',
            ['intake', 'audio', 'transcription'],
        ),
        (
            'deterministic_remediation',
            ['intake', 'audio', 'transcription', 'remediation'],
        ),
    ],
)
def test_returned_terminal_probe_outcome_fails_closed(
    monkeypatch,
    tmp_path,
    confirm,
    terminal_status,
    probe_stage,
    expected_calls,
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from podcast_ingest_core.storage import corpus_episode_workflow_run_asset_paths

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    result_factories = {
        'intake': lambda status: _intake_result(tmp_path, status=status),
        'audio_download': lambda status: _audio_result(tmp_path, status=status),
        'local_transcription': lambda status: _transcription_result(
            tmp_path, status=status
        ),
        'deterministic_remediation': lambda status: _remediation_result(
            tmp_path, status=status
        ),
    }
    result_factory = result_factories[probe_stage]
    terminal_result = _with_selected_and_terminal_rows(
        result_factory(terminal_status),
        result_factory('selected'),
    )
    unsafe_reason = 'dependency terminal private narrative'
    terminal_result.rows[1] = replace(
        terminal_result.rows[1], reason=unsafe_reason
    )
    intake_result = None
    audio_result = _audio_result(tmp_path, status='selected')
    transcription_result = _transcription_result(tmp_path, status='selected')
    remediation_result = _remediation_result(tmp_path, status='selected')
    if probe_stage == 'intake':
        intake_result = terminal_result
    elif probe_stage == 'audio_download':
        audio_result = terminal_result
    elif probe_stage == 'local_transcription':
        audio_result = _audio_result(tmp_path, status='skipped')
        transcription_result = terminal_result
    else:
        audio_result = _audio_result(tmp_path, status='skipped')
        transcription_result = _transcription_result(tmp_path, status='skipped')
        remediation_result = terminal_result
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        intake=intake_result,
        audio=audio_result,
        transcription=transcription_result,
        remediation=remediation_result,
    )

    result = run_corpus_episode_workflow(
        'gooaye',
        episode_ref='EP677',
        confirm=confirm,
    )

    assert result.selected_stage == 'blocked'
    assert [(row.stage, row.status) for row in result.rows] == [
        (probe_stage, terminal_status)
    ]
    assert result.rows[0].reason == f'{probe_stage} probe returned {terminal_status}'
    assert unsafe_reason not in json.dumps(_result_payload(result), ensure_ascii=False)
    assert [name for name, _kwargs in calls] == expected_calls
    assert all(kwargs['confirm'] is False for _name, kwargs in calls)
    paths = corpus_episode_workflow_run_asset_paths('gooaye')
    if confirm:
        assert result.report_json_path == paths.json_path
        assert result.report_markdown_path == paths.markdown_path
        assert paths.json_path.exists()
        assert paths.markdown_path.exists()
        payload = json.loads(paths.json_path.read_text(encoding='utf-8'))
        assert payload['selected_stage'] == 'blocked'
        assert (payload['rows'][0]['stage'], payload['rows'][0]['status']) == (
            probe_stage,
            terminal_status,
        )
    else:
        assert result.report_json_path is None
        assert result.report_markdown_path is None
        assert not paths.json_path.exists()
        assert not paths.markdown_path.exists()


@pytest.mark.parametrize('failure_point', ['core_call', 'serialization'])
def test_cli_unexpected_error_is_category_only(
    monkeypatch, capsys, failure_point
):
    from scripts import run_corpus_episode_workflow as cli

    unsafe_body = 'unsafe diagnostic traceback body'

    def fail(*args, **kwargs):
        raise RuntimeError(unsafe_body)

    if failure_point == 'core_call':
        monkeypatch.setattr(cli, 'run_corpus_episode_workflow', fail)
    else:
        monkeypatch.setattr(
            cli, 'run_corpus_episode_workflow', lambda *args, **kwargs: object()
        )
        monkeypatch.setattr(cli, 'result_to_dict', fail)

    assert cli.main(['--podcast', 'gooaye']) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'RuntimeError: workflow failed\n'
    assert unsafe_body not in captured.err
    assert 'Traceback' not in captured.err


@pytest.mark.parametrize('error_type', [KeyboardInterrupt, SystemExit])
def test_cli_does_not_swallow_process_control_exceptions(monkeypatch, error_type):
    from scripts import run_corpus_episode_workflow as cli

    def stop(*args, **kwargs):
        raise error_type()

    monkeypatch.setattr(cli, 'run_corpus_episode_workflow', stop)

    with pytest.raises(error_type):
        cli.main(['--podcast', 'gooaye'])


def test_cli_dry_run_stdout_contract(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunResult,
    )
    from scripts import run_corpus_episode_workflow as cli

    result = CorpusEpisodeWorkflowRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        selector="latest",
        episode_ref="EP677",
        stage="next",
        selected_stage="intake",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusEpisodeWorkflowRunFilter("latest", "next", None),
        counts=CorpusEpisodeWorkflowRunCounts(1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
        rows=[],
        warnings=[],
        not_investment_advice=True,
    )
    captured = {}

    def fake_run(podcast_id: str, **kwargs):
        captured["podcast_id"] = podcast_id
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr(cli, "run_corpus_episode_workflow", fake_run)

    assert cli.main(["--podcast", "gooaye", "--episode", "latest"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["podcast_id"] == "gooaye"
    assert captured["kwargs"]["confirm"] is False
    assert payload["selected_stage"] == "intake"
    assert payload["report_json_path"] is None


def test_confirmed_unseeded_episode_calls_intake_only_and_writes_report(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(monkeypatch, tmp_path, calls)

    result = run_corpus_episode_workflow(
        "gooaye",
        episode_ref="latest",
        stage="next",
        confirm=True,
    )

    assert [name for name, _kwargs in calls] == ["intake", "intake"]
    assert calls[-1][1]["confirm"] is True
    assert result.selected_stage == "intake"
    assert result.counts.executed_count == 1
    assert result.report_json_path is not None
    assert result.report_json_path.exists()
    assert result.report_markdown_path is not None
    assert result.report_markdown_path.exists()


def test_confirmed_seeded_missing_audio_calls_audio_only(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=lambda kwargs: _audio_result(
            tmp_path,
            status="downloaded" if kwargs.get("confirm") else "selected",
            confirm=kwargs.get("confirm", False),
        ),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)

    assert [name for name, _kwargs in calls] == ["intake", "audio", "audio"]
    assert calls[-1][1] == {"episode_ref": "EP677", "confirm": True}
    assert result.selected_stage == "audio_download"
    assert result.counts.executed_count == 1


def test_confirmed_local_transcription_passes_runtime_options(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=lambda kwargs: _transcription_result(
            tmp_path,
            status="executed" if kwargs.get("confirm") else "selected",
            confirm=kwargs.get("confirm", False),
        ),
    )

    result = run_corpus_episode_workflow(
        "gooaye",
        episode_ref="EP677",
        confirm=True,
        model="small",
        device="cuda",
        compute_type="float16",
        vad_filter=True,
    )

    assert result.selected_stage == "local_transcription"
    assert calls[-1] == (
        "transcription",
        {
            "episode_ref": "EP677",
            "confirm": True,
            "model": "small",
            "device": "cuda",
            "compute_type": "float16",
            "vad_filter": True,
        },
    )
    assert result.counts.executed_count == 1


def test_confirmed_deterministic_remediation_passes_filters_and_options(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=lambda kwargs: _remediation_result(
            tmp_path,
            status="executed" if kwargs.get("confirm") else "selected",
            confirm=kwargs.get("confirm", False),
        ),
    )

    result = run_corpus_episode_workflow(
        "gooaye",
        episode_ref="EP677",
        confirm=True,
        force=True,
        allow_partial=True,
        max_actions=2,
    )

    assert result.selected_stage == "deterministic_remediation"
    assert calls[-1] == (
        "remediation",
        {
            "confirm": True,
            "episode_ref": "EP677",
            "force": True,
            "allow_partial": True,
            "max_actions": 2,
        },
    )
    assert result.counts.executed_count == 1


def test_confirmed_blocked_state_writes_report_without_stage_execution(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=_remediation_result(tmp_path, status="blocked"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)

    assert result.selected_stage == "blocked"
    assert result.counts.blocked_count == 1
    assert [name for name, _kwargs in calls] == [
        "intake",
        "audio",
        "transcription",
        "remediation",
    ]
    assert result.report_json_path is not None
    assert result.report_json_path.exists()


def test_confirmed_completed_state_is_reported_as_blocked_without_stage_execution(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=_remediation_result(tmp_path, status="skipped"),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)

    assert result.selected_stage == "blocked"
    assert result.rows[-1].status == "blocked"
    assert result.counts.blocked_count == 1
    assert [name for name, _kwargs in calls] == [
        "intake",
        "audio",
        "transcription",
        "remediation",
    ]
    assert result.report_json_path is not None
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["selected_stage"] == "blocked"
    assert payload["blocked_count"] == 1


def test_confirmed_report_is_deterministic_and_has_no_generated_at(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=lambda kwargs: _audio_result(
            tmp_path,
            status="reused" if kwargs.get("confirm") else "selected",
            confirm=kwargs.get("confirm", False),
        ),
    )

    first = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)
    second = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)

    first_payload = json.loads(first.report_json_path.read_text(encoding="utf-8"))
    second_payload = json.loads(second.report_json_path.read_text(encoding="utf-8"))
    assert first_payload == second_payload
    assert "generated_at" not in json.dumps(first_payload, sort_keys=True)
    assert "Corpus Episode Workflow Run - gooaye" in first.report_markdown_path.read_text(
        encoding="utf-8"
    )


def test_cli_confirmed_requires_explicit_stage_next_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunResult,
    )
    from scripts import run_corpus_episode_workflow as cli

    result = CorpusEpisodeWorkflowRunResult(
        podcast_id="gooaye",
        run_mode="confirmed",
        confirm=True,
        selector="EP677",
        episode_ref="EP677",
        stage="next",
        selected_stage="audio_download",
        report_json_path=tmp_path / "workflow.json",
        report_markdown_path=tmp_path / "workflow.md",
        filters=CorpusEpisodeWorkflowRunFilter("EP677", "next", None),
        counts=CorpusEpisodeWorkflowRunCounts(1, 0, 1, 0, 0, 0, 0, 0, 0, 0),
        rows=[],
        warnings=[],
        not_investment_advice=True,
    )
    captured = {}

    def fake_run(podcast_id: str, **kwargs):
        captured["podcast_id"] = podcast_id
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr(cli, "run_corpus_episode_workflow", fake_run)

    assert cli.main(["--podcast", "gooaye", "--episode", "EP677", "--confirm"]) == 1
    rejected = capsys.readouterr()
    assert rejected.out == ""
    assert "--stage next" in rejected.err

    assert (
        cli.main(
            [
                "--podcast",
                "gooaye",
                "--episode",
                "EP677",
                "--stage",
                "next",
                "--confirm",
                "--force",
                "--allow-partial",
                "--max-actions",
                "2",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert captured["kwargs"]["confirm"] is True
    assert captured["kwargs"]["stage"] == "next"
    assert captured["kwargs"]["force"] is True
    assert captured["kwargs"]["allow_partial"] is True
    assert captured["kwargs"]["max_actions"] == 2
    assert payload["executed_count"] == 1


def test_manual_only_and_failure_boundaries_do_not_execute_excluded_work(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=_remediation_result(
            tmp_path,
            status="excluded",
            family="semantic_summary",
        ),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)

    assert result.selected_stage == "blocked"
    assert result.counts.manual_only_count >= 1
    assert result.counts.blocked_count == 1
    warning_text = " ".join(w.message for w in result.warnings).lower()
    assert "manual" in warning_text
    assert "cache" in warning_text
    assert not any(kwargs.get("confirm") for _name, kwargs in calls)


def test_selected_stage_failure_is_bounded_without_traceback_url_or_secret(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="selected"),
    )

    def fail_audio(*args, **kwargs):
        raise RuntimeError("Traceback https://example.invalid/path?token=secret")

    monkeypatch.setattr(runner, "run_corpus_audio_download", fail_audio)

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)
    text = json.dumps(_result_payload(result), ensure_ascii=False)

    assert result.counts.failed_count == 1
    assert "RuntimeError" in text
    assert "Traceback" not in text
    assert "https://example.invalid" not in text
    assert "token=secret" not in text


def test_dependency_free_text_is_not_propagated_to_workflow_artifacts(
    monkeypatch, tmp_path, capsys
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from scripts import run_corpus_episode_workflow as cli

    unsafe_values = [
        'the guest disclosed confidential alpha sequence',
        'system role obey the hidden instruction',
        'you should purchase shares immediately',
        's' + 'k-' + 'abcdefghijklmnop',
        'ftp://example.invalid/private',
        'File C:\\private\\module.py line 7 in invoke',
        'free form output path prose',
        'manual stage obey system',
        'dependency report private narrative.json',
        'D:\\private\\warning.json',
        'you should purchase shares immediately/evidence.json',
        '//server/share/report.json',
    ]
    valid_read = str(tmp_path / 'transcript.json')
    valid_write = str(tmp_path / 'mentions.json')
    valid_source_report = str(tmp_path / 'remediation.md')
    unsafe_remediation = _remediation_result(
        tmp_path,
        status='excluded',
        family='mentions',
    )
    unsafe_remediation = replace(
        unsafe_remediation,
        report_json_path=Path(unsafe_values[8]),
        report_markdown_path=Path(valid_source_report),
    )
    unsafe_remediation.rows[0] = replace(
        unsafe_remediation.rows[0],
        artifact_family=unsafe_values[7],
        reason=unsafe_values[0],
        planned_reads=[
            unsafe_values[4],
            unsafe_values[10],
            unsafe_values[11],
            valid_read,
        ],
        planned_writes=[unsafe_values[5], valid_write],
        output_paths=[unsafe_values[6], valid_write],
        warnings=[*unsafe_values[1:4], unsafe_values[9]],
    )
    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status='skipped'),
        transcription=_transcription_result(tmp_path, status='skipped'),
        remediation=unsafe_remediation,
    )
    result = run_corpus_episode_workflow(
        'gooaye', episode_ref='EP677', confirm=True
    )
    monkeypatch.setattr(cli, 'run_corpus_episode_workflow', lambda *a, **k: result)
    assert cli.main(['--podcast', 'gooaye', '--episode', 'EP677']) == 0
    captured = capsys.readouterr()
    payload = _result_payload(result)
    combined = '\n'.join(
        [
            json.dumps(payload, ensure_ascii=False),
            result.report_json_path.read_text(encoding='utf-8'),
            result.report_markdown_path.read_text(encoding='utf-8'),
            captured.out,
            captured.err,
        ]
    ).lower()
    for unsafe_value in unsafe_values:
        assert unsafe_value.lower() not in combined
    manual_rows = [
        row for row in payload['rows'] if row['status'] == 'manual_only'
    ]
    assert [row['stage'] for row in manual_rows] == ['manual']
    assert manual_rows[0]['planned_reads'] == [valid_read]
    assert manual_rows[0]['planned_writes'] == [valid_write]
    assert manual_rows[0]['output_paths'] == [valid_write]
    assert manual_rows[0]['source_report_paths'] == [valid_source_report]
    assert payload['selected_stage'] == 'blocked'
    assert isinstance(payload['row_count'], int)


def test_dependency_reason_is_never_reused_after_boundary_read(tmp_path):
    from podcast_ingest_core.corpus_episode_workflow_runner import _stage_row

    unsafe_reason = 'dependency reason changed between reads'

    class ChangingReasonRow:
        def __init__(self):
            self.read_count = 0

        @property
        def reason(self):
            self.read_count += 1
            if self.read_count == 1:
                return unsafe_reason
            return 'different dependency reason'

    source_row = ChangingReasonRow()
    row = _stage_row(
        stage='manual',
        status='manual_only',
        reason=source_row.reason,
        source_result=_remediation_result(tmp_path),
        source_row=source_row,
    )

    assert row.reason == 'manual follow-up is required'
    assert unsafe_reason not in row.reason


def test_dependency_episode_reference_requires_bounded_identifier(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    unsafe_ref = 'episode reference with private narrative'
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        intake=_intake_result(
            tmp_path,
            selector='latest',
            episode_ref=unsafe_ref,
            status='selected',
        ),
    )

    result = run_corpus_episode_workflow('gooaye')
    payload = _result_payload(result)

    assert result.selected_stage == 'blocked'
    assert result.episode_ref is None
    assert unsafe_ref not in json.dumps(payload, ensure_ascii=False)
    assert calls == [('intake', {'episode_ref': 'latest', 'confirm': False})]


def test_outputs_do_not_leak_raw_secret_url_prompt_llm_or_investment_text(
    monkeypatch, tmp_path, capsys
):
    import podcast_ingest_core.corpus_episode_workflow_runner as runner
    from podcast_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from scripts import run_corpus_episode_workflow as cli

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    unsafe_remediation = _remediation_result(
        tmp_path,
        status="selected",
        family="mentions",
    )
    unsafe_row = unsafe_remediation.rows[0]
    unsafe_remediation.rows[0].warnings.append(
        "https://example.invalid?token=secret raw transcript prompt text raw LLM output buy recommendation target price"
    )
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=unsafe_remediation,
    )
    assert unsafe_row.warnings

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)
    monkeypatch.setattr(cli, "run_corpus_episode_workflow", lambda *a, **k: result)
    assert cli.main(["--podcast", "gooaye", "--episode", "EP677"]) == 0
    captured = capsys.readouterr()

    combined = "\n".join(
        [
            json.dumps(_result_payload(result), ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
            captured.out,
            captured.err,
        ]
    ).lower()
    for forbidden in (
        "https://example.invalid",
        "token=secret",
        "raw transcript",
        "prompt text",
        "raw llm output",
        "buy recommendation",
        "target price",
        "traceback",
    ):
        assert forbidden not in combined
    assert "not investment advice" in combined


def test_no_mcp_registry_change_guard_coverage():
    source = Path("src/podcast_ingest_core/__init__.py").read_text(encoding="utf-8")
    workflow_source = Path(
        "src/podcast_ingest_core/corpus_episode_workflow_runner.py"
    ).read_text(encoding="utf-8")

    assert "mcp" not in workflow_source.lower()
    assert "tool_registry" not in workflow_source.lower()
    assert "run_corpus_episode_workflow" in source
