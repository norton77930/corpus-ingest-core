from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> None:
    import corpus_ingest_core.corpus_index as corpus_index
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


def _write_seed(
    monkeypatch,
    tmp_path: Path,
    episode_ref: str = "EP677",
    *,
    has_audio_url: bool = True,
) -> Path:
    from corpus_ingest_core import storage

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
    return path


def _write_real_audio(episode_ref: str = "EP677") -> Path:
    from corpus_ingest_core import storage

    path = storage.AUDIO_DIR / "gooaye" / f"{episode_ref}__{episode_ref} Alpha.mp3"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"mp3")
    return path


def _write_real_transcript(episode_ref: str = "EP677") -> Path:
    from corpus_ingest_core import storage

    paths = storage.transcript_asset_paths("gooaye", episode_ref, f"{episode_ref} Alpha")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": f"{episode_ref} Alpha",
                "language": "zh",
                "segment_count": 1,
                "last_segment_end_seconds": 5.5,
                "completed": True,
                "segments": [
                    {
                        "id": 1,
                        "start": 0.0,
                        "end": 5.5,
                        "text": "integration transcript sentinel",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths.text_path.write_text("integration transcript sentinel", encoding="utf-8")
    paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:05,500\nintegration\n",
        encoding="utf-8",
    )
    return paths.json_path


def _write_real_deterministic_artifacts(
    episode_ref: str = "EP677",
    *,
    include_external: bool = True,
) -> None:
    from corpus_ingest_core import storage

    title = f"{episode_ref} Alpha"
    summary_path = storage.summary_asset_path("gooaye", episode_ref, title)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("# deterministic summary", encoding="utf-8")

    mentions = storage.mention_asset_paths("gooaye", episode_ref, title)
    mentions.json_path.parent.mkdir(parents=True, exist_ok=True)
    mentions.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": title,
                "mention_count": 0,
                "mentions": [],
            }
        ),
        encoding="utf-8",
    )
    mentions.markdown_path.write_text("# mentions", encoding="utf-8")

    intelligence = storage.episode_intelligence_report_asset_paths("gooaye", episode_ref, title)
    intelligence.json_path.parent.mkdir(parents=True, exist_ok=True)
    intelligence.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": title,
                "report_status": "final",
                "transcript_validation": {"status": "valid", "segment_count": 1},
            }
        ),
        encoding="utf-8",
    )
    intelligence.markdown_path.write_text("# intelligence", encoding="utf-8")

    mapping = storage.industry_chain_mapping_asset_paths("gooaye", episode_ref, title)
    mapping.json_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
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

    if not include_external:
        return

    external = storage.external_data_boundary_asset_paths("gooaye", episode_ref, title)
    external.json_path.parent.mkdir(parents=True, exist_ok=True)
    external.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": episode_ref,
                "title": title,
                "boundary_status": "final",
                "candidate_boundaries": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    external.markdown_path.write_text("# external boundary", encoding="utf-8")


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
                        "selected_stage": "completed",
                    }
                ).encode("utf-8")
                if path.suffix == ".json"
                else f"# stale sentinel {index}\n".encode()
            )
            path.write_bytes(payload)
            sentinels[path] = payload
    return sentinels


def _stringify(value):
    if isinstance(value, dict):
        return {key: _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _result_payload(result) -> dict:
    from corpus_ingest_core.corpus_episode_workflow_runner import result_to_dict

    return result_to_dict(result)


def _intake_result(
    tmp_path: Path,
    *,
    selector: str = "latest",
    episode_ref: str | None = "EP677",
    status: str = "selected",
    confirm: bool = False,
):
    from corpus_ingest_core.models import (
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
        planned_writes=[str(tmp_path / "corpus" / "gooaye" / "seed.json")] if episode_ref else [],
        seed_json_path=str(tmp_path / "corpus" / "gooaye" / "seed.json") if episode_ref else None,
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
    from corpus_ingest_core.models import (
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
                local_audio_path=(str(tmp_path / "audio.mp3") if status in {"downloaded", "reused"} else None),
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
    from corpus_ingest_core.models import (
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
                output_paths=[str(tmp_path / "transcript.json")] if status in {"executed", "reused"} else [],
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
    from corpus_ingest_core.models import (
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
                output_paths=[str(tmp_path / f"{family}.json")] if status in {"executed", "reused"} else [],
                warnings=[],
            )
        ],
        warnings=[],
        not_investment_advice=True,
    )


def _remediation_result_families(
    tmp_path: Path,
    *,
    episode_ref: str = "EP677",
    selected: tuple[str, ...] = (),
    blocked: tuple[str, ...] = (),
):
    from corpus_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
        CorpusRemediationRunRow,
    )

    rows = []
    for family in selected:
        rows.append(
            CorpusRemediationRunRow(
                action_id=f"{episode_ref}:{family}",
                podcast_id="gooaye",
                episode_ref=episode_ref,
                title=episode_ref,
                artifact_family=family,
                source_status="ready",
                outcome_status="selected",
                reason=f"{family} artifact is missing",
                planned_reads=[str(tmp_path / "transcript.json")],
                planned_writes=[str(tmp_path / f"{family}.json")],
                output_paths=[],
                warnings=[],
            )
        )
    for family in blocked:
        rows.append(
            CorpusRemediationRunRow(
                action_id=f"{episode_ref}:{family}",
                podcast_id="gooaye",
                episode_ref=episode_ref,
                title=episode_ref,
                artifact_family=family,
                source_status="blocked",
                outcome_status="blocked",
                reason="blocked by upstream artifact",
                planned_reads=[str(tmp_path / "transcript.json")],
                planned_writes=[],
                output_paths=[],
                warnings=[],
            )
        )
    return CorpusRemediationRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        source_remediation_plan_json_path=tmp_path / "plan.json",
        source_remediation_plan_markdown_path=tmp_path / "plan.md",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusRemediationRunFilter(episode_ref, None, None),
        counts=CorpusRemediationRunCounts(
            row_count=len(rows),
            selected_count=len(selected),
            executed_count=0,
            reused_count=0,
            failed_count=0,
            skipped_count=0,
            blocked_count=len(blocked),
            excluded_count=0,
            warning_count=0,
        ),
        rows=rows,
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
    import corpus_ingest_core.corpus_episode_workflow_runner as runner

    def fake_intake(podcast_id: str, **kwargs):
        calls.append(("intake", kwargs))
        result = intake
        if callable(result):
            return result(kwargs)
        return result or _intake_result(
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

    def fake_audio_preview(podcast_id: str, **kwargs):
        return runner.run_corpus_audio_download(
            podcast_id,
            episode_ref=kwargs.get("episode_ref"),
            confirm=False,
        )

    def fake_transcription_preview(podcast_id: str, **kwargs):
        return runner.run_corpus_local_transcription(
            podcast_id,
            episode_ref=kwargs.get("episode_ref"),
            confirm=False,
        )

    def fake_remediation_preview(podcast_id: str, **kwargs):
        return runner.run_corpus_remediation(
            podcast_id,
            confirm=False,
            episode_ref=kwargs.get("episode_ref"),
            max_actions=kwargs.get("max_actions"),
        )

    monkeypatch.setattr(runner, "run_corpus_episode_intake", fake_intake)
    monkeypatch.setattr(runner, "run_corpus_audio_download", fake_audio)
    monkeypatch.setattr(runner, "run_corpus_local_transcription", fake_transcription)
    monkeypatch.setattr(runner, "run_corpus_remediation", fake_remediation)
    monkeypatch.setattr(
        runner,
        "_preview_corpus_audio_download_from_plan",
        fake_audio_preview,
    )
    monkeypatch.setattr(
        runner,
        "_preview_corpus_local_transcription_from_plan",
        fake_transcription_preview,
    )
    monkeypatch.setattr(
        runner,
        "_preview_corpus_remediation_from_plan",
        fake_remediation_preview,
    )


def _with_selected_and_terminal_rows(terminal_result, selected_result):
    return replace(
        terminal_result,
        rows=[selected_result.rows[0], terminal_result.rows[0]],
    )


def test_corpus_episode_workflow_run_asset_paths_contract():
    from corpus_ingest_core.storage import corpus_episode_workflow_run_asset_paths

    paths = corpus_episode_workflow_run_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-episode-workflow-run.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-episode-workflow-run.md")


def test_corpus_episode_workflow_public_result_contract_exports(tmp_path):
    from corpus_ingest_core import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunnerFailedError,
        CorpusEpisodeWorkflowRunResult,
        CorpusEpisodeWorkflowRunRow,
        CorpusEpisodeWorkflowRunWarning,
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
    assert CorpusEpisodeWorkflowRunnerFailedError.__name__ == ("CorpusEpisodeWorkflowRunnerFailedError")
    assert callable(run_corpus_episode_workflow)


def test_corpus_episode_workflow_runner_error_contract():
    from corpus_ingest_core import (
        CorpusEpisodeWorkflowRunnerFailedError,
        PodcastIngestCoreError,
    )

    assert issubclass(CorpusEpisodeWorkflowRunnerFailedError, PodcastIngestCoreError)


@pytest.mark.parametrize(
    ("corpus_state", "expected_stage"),
    (
        ("unseeded", "intake"),
        ("seeded_missing_audio", "audio_download"),
        ("local_audio", "local_transcription"),
        ("transcript_ready", "deterministic_remediation"),
        ("complete", "completed"),
        ("blocked_no_audio_url", "blocked"),
    ),
)
def test_dry_run_uses_fresh_real_corpus_state_without_any_writes(
    monkeypatch,
    tmp_path,
    corpus_state,
    expected_stage,
):
    import corpus_ingest_core.cache as cache
    import corpus_ingest_core.corpus_audio_download_runner as audio_runner
    import corpus_ingest_core.corpus_episode_intake as intake_runner
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow
    import corpus_ingest_core.corpus_index as corpus_index
    import corpus_ingest_core.corpus_local_transcription_runner as transcription_runner
    import corpus_ingest_core.corpus_remediation_plan as remediation_plan
    import corpus_ingest_core.corpus_remediation_runner as remediation_runner
    from corpus_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if corpus_state != "unseeded":
        _write_seed(
            monkeypatch,
            tmp_path,
            has_audio_url=corpus_state != "blocked_no_audio_url",
        )
    if corpus_state in {"local_audio", "transcript_ready", "complete"}:
        _write_real_audio()
    if corpus_state in {"transcript_ready", "complete"}:
        _write_real_transcript()
        semantic_path = storage.semantic_summary_asset_path("gooaye", "EP677", "EP677 Alpha")
        semantic_path.parent.mkdir(parents=True, exist_ok=True)
        semantic_path.write_text("# existing semantic summary", encoding="utf-8")
    if corpus_state == "transcript_ready":
        _write_real_deterministic_artifacts(include_external=False)
    if corpus_state == "complete":
        _write_real_deterministic_artifacts()

    sentinel_bytes = _write_stale_corpus_sentinels()
    before = _tree_manifest(tmp_path)
    writer_calls: list[str] = []
    for label, module, name in (
        ("008-index", corpus_index, "_write_index"),
        ("009-plan", remediation_plan, "_write_plan"),
        ("010-report", remediation_runner, "_write_run_report"),
        ("011-report", transcription_runner, "_write_run_report"),
        ("012-report", audio_runner, "_write_run_report"),
        ("013-report", intake_runner, "_write_run_report"),
        ("014-report", workflow, "_write_run_report"),
    ):
        original = getattr(module, name)

        def recording_writer(
            *args,
            _label=label,
            _original=original,
            **kwargs,
        ):
            writer_calls.append(_label)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, recording_writer)

    def forbidden_execution(*args, **kwargs):
        pytest.fail("014 dry-run reached a forbidden execution surface")

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
    monkeypatch.setattr(cache, "rebuild_cache", forbidden_execution)

    intake_calls: list[dict] = []

    def fake_intake(podcast_id: str, **kwargs):
        assert podcast_id == "gooaye"
        intake_calls.append(kwargs)
        return _intake_result(
            tmp_path,
            selector=kwargs.get("episode_ref", "latest"),
            episode_ref="EP677",
            status="selected",
            confirm=False,
        )

    monkeypatch.setattr(workflow, "run_corpus_episode_intake", fake_intake)

    result = workflow.run_corpus_episode_workflow(
        "gooaye",
        episode_ref="latest",
        confirm=False,
    )

    assert result.run_mode == "dry_run"
    assert result.confirm is False
    assert result.episode_ref == "EP677"
    assert result.selected_stage == expected_stage
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert intake_calls == [{"episode_ref": "latest", "confirm": False}]
    expected_read_label = "configured podcast RSS feed" if expected_stage == "intake" else "in-memory corpus snapshot"
    assert any(expected_read_label in row.planned_reads for row in result.rows)
    allowed_non_path_reads = {
        "configured podcast RSS feed",
        "in-memory corpus snapshot",
    }
    for row in result.rows:
        for planned_read in row.planned_reads:
            assert planned_read in allowed_non_path_reads or workflow._is_safe_local_path(planned_read)

    if expected_stage in {
        "intake",
        "audio_download",
        "local_transcription",
        "deterministic_remediation",
    }:
        assert result.counts.selected_count == 1
    else:
        assert result.counts.selected_count == 0
    if expected_stage == "blocked":
        assert result.counts.blocked_count == 1
    if expected_stage == "completed":
        assert any(row.status == "completed" for row in result.rows)

    assert writer_calls == []
    assert _tree_manifest(tmp_path) == before
    assert all(path.read_bytes() == payload for path, payload in sentinel_bytes.items())
    assert not list(tmp_path.rglob("*.part"))

    index_paths = storage.corpus_index_asset_paths("gooaye")
    plan_paths = storage.corpus_remediation_plan_asset_paths("gooaye")
    assert index_paths.json_path.read_bytes() == sentinel_bytes[index_paths.json_path]
    assert plan_paths.json_path.read_bytes() == sentinel_bytes[plan_paths.json_path]


def test_seeded_probe_builds_one_snapshot_and_reuses_it_across_previews(monkeypatch, tmp_path):
    from types import SimpleNamespace

    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    _write_seed(monkeypatch, tmp_path)
    index_result = object()
    index_payload = {"index": object()}
    plan_result = object()
    plan_payload = {"plan": object()}
    index_snapshot = SimpleNamespace(
        result=index_result,
        payload=index_payload,
        markdown="# index",
    )
    plan_snapshot = SimpleNamespace(
        result=plan_result,
        payload=plan_payload,
        markdown="# plan",
    )
    build_calls: list[tuple] = []
    preview_calls: list[tuple] = []

    def fake_intake(podcast_id: str, **kwargs):
        return _intake_result(
            tmp_path,
            selector=kwargs["episode_ref"],
            episode_ref="EP677",
            status="selected",
            confirm=False,
        )

    def fake_build_index(podcast_id: str):
        build_calls.append(("index", podcast_id))
        return index_snapshot

    def fake_build_plan(podcast_id: str, *, index_result, index_payload):
        build_calls.append(
            (
                "plan",
                podcast_id,
                index_result is index_snapshot.result,
                index_payload is index_snapshot.payload,
            )
        )
        return plan_snapshot

    def record_preview(stage, result):
        def preview(podcast_id: str, **kwargs):
            preview_calls.append(
                (
                    stage,
                    podcast_id,
                    kwargs["plan_result"] is plan_snapshot.result,
                    kwargs["plan_payload"] is plan_snapshot.payload,
                    kwargs["source_persisted"],
                )
            )
            return result

        return preview

    monkeypatch.setattr(workflow, "run_corpus_episode_intake", fake_intake)
    monkeypatch.setattr(workflow, "_build_corpus_index_snapshot", fake_build_index, raising=False)
    monkeypatch.setattr(
        workflow,
        "_build_corpus_remediation_plan_snapshot",
        fake_build_plan,
        raising=False,
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        record_preview("audio", _audio_result(tmp_path, status="skipped")),
        raising=False,
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        record_preview(
            "transcription",
            _transcription_result(tmp_path, status="skipped"),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        record_preview(
            "remediation",
            _remediation_result(tmp_path, status="selected"),
        ),
        raising=False,
    )

    def unexpected_public_runner(*args, **kwargs):
        pytest.fail("stage selection called a public side-effect runner")

    monkeypatch.setattr(workflow, "run_corpus_audio_download", unexpected_public_runner)
    monkeypatch.setattr(workflow, "run_corpus_local_transcription", unexpected_public_runner)
    monkeypatch.setattr(workflow, "run_corpus_remediation", unexpected_public_runner)

    result = workflow.run_corpus_episode_workflow(
        "gooaye",
        episode_ref="EP677",
        confirm=False,
    )

    assert result.selected_stage == "deterministic_remediation"
    assert build_calls == [
        ("index", "gooaye"),
        ("plan", "gooaye", True, True),
    ]
    assert preview_calls == [
        ("audio", "gooaye", True, True, False),
        ("transcription", "gooaye", True, True, False),
        ("remediation", "gooaye", True, True, False),
    ]


def test_snapshot_preview_seam_bounds_deterministic_actions_to_one(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    calls: list[tuple[str, int | None]] = []
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        lambda *args, **kwargs: _audio_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        lambda *args, **kwargs: _transcription_result(tmp_path, status="skipped"),
    )

    def remediation_preview(*args, **kwargs):
        calls.append(("remediation", kwargs["max_actions"]))
        return _remediation_result(tmp_path, status="selected")

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        remediation_preview,
    )

    result = workflow._preview_corpus_episode_workflow_from_snapshot(
        "gooaye",
        episode_ref="EP677",
        plan_result=object(),
        plan_payload={
            "episodes": [
                {
                    "episode_ref": "EP677",
                    "artifact_status": {"transcript": {"status": "valid"}},
                }
            ]
        },
        max_actions=None,
        allow_semantic_handoff=True,
    )

    assert result["selected_stage"] == "deterministic_remediation"
    assert calls == [("remediation", 1)]


def test_snapshot_remediation_selection_exposes_internal_action_identity(
    monkeypatch,
    tmp_path,
):
    """017 receives identity from the private mapping, not the public 014 row."""
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        lambda *args, **kwargs: _audio_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        lambda *args, **kwargs: _transcription_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        lambda *args, **kwargs: _remediation_result(
            tmp_path,
            status="selected",
            family="mentions",
        ),
    )

    selection = workflow._preview_corpus_episode_workflow_from_snapshot(
        "gooaye",
        episode_ref="EP677",
        plan_result=object(),
        plan_payload={
            "episodes": [
                {
                    "episode_ref": "EP677",
                    "artifact_status": {"transcript": {"status": "valid"}},
                }
            ]
        },
        max_actions=1,
        allow_semantic_handoff=True,
    )

    assert selection["selected_stage"] == "deterministic_remediation"
    assert selection["action_id"] == "EP677:mentions"
    assert not hasattr(selection["rows"][0], "action_id")


def test_snapshot_semantic_handoff_ignores_non_target_semantic_skips(
    monkeypatch,
    tmp_path,
):
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        lambda *args, **kwargs: _audio_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        lambda *args, **kwargs: _transcription_result(tmp_path, status="skipped"),
    )
    remediation_result = _remediation_result(
        tmp_path,
        status="excluded",
        family="semantic_summary",
    )
    remediation_result = replace(
        remediation_result,
        counts=replace(
            remediation_result.counts,
            row_count=4,
            skipped_count=2,
            blocked_count=1,
        ),
        rows=[
            remediation_result.rows[0],
            _remediation_result(
                tmp_path,
                status="blocked",
                family="semantic_review",
            ).rows[0],
            _remediation_result(
                tmp_path,
                episode_ref="EP676",
                status="skipped",
                family="semantic_summary",
            ).rows[0],
            _remediation_result(
                tmp_path,
                episode_ref="EP676",
                status="skipped",
                family="semantic_review",
            ).rows[0],
        ],
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        lambda *args, **kwargs: remediation_result,
    )

    result = workflow._preview_corpus_episode_workflow_from_snapshot(
        "gooaye",
        episode_ref="EP677",
        plan_result=object(),
        plan_payload={
            "episodes": [
                {
                    "episode_ref": "EP677",
                    "artifact_status": {"transcript": {"status": "valid"}},
                }
            ]
        },
        max_actions=None,
        allow_semantic_handoff=True,
    )

    assert result["selected_stage"] == "completed"
    assert result["episode_ref"] == "EP677"
    assert result["rows"][-1].status == "completed"


@pytest.mark.parametrize(
    ("row_episode_ref", "family", "status", "expected_invalid"),
    (
        (None, None, None, True),
        ("EP676", "mentions", "skipped", True),
        ("EP677", "mentions", "skipped", False),
        ("EP677", "mentions", "reused", False),
        ("EP677", "mentions", "executed", False),
        ("EP677", "semantic_summary", "blocked", False),
        ("EP677", "semantic_summary", "excluded", False),
        ("EP677", "semantic_summary", "selected", True),
    ),
)
def test_semantic_handoff_validator_requires_well_formed_canonical_target_evidence(
    tmp_path,
    row_episode_ref,
    family,
    status,
    expected_invalid,
):
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    rows = []
    if status is not None:
        rows = [
            _remediation_result(
                tmp_path,
                episode_ref=row_episode_ref,
                family=family,
                status=status,
            ).rows[0]
        ]

    assert (
        workflow._semantic_handoff_result_is_invalid(
            SimpleNamespace(rows=rows),
            {"semantic_summary", "semantic_review"},
            "EP677",
        )
        is expected_invalid
    )


def test_snapshot_semantic_handoff_accepts_explicit_empty_target_actions_with_unrelated_rows(
    monkeypatch,
    tmp_path,
):
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        lambda *args, **kwargs: _audio_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        lambda *args, **kwargs: _transcription_result(tmp_path, status="skipped"),
    )
    unrelated = _remediation_result(
        tmp_path,
        episode_ref="EP676",
        family="semantic_summary",
        status="skipped",
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        lambda *args, **kwargs: unrelated,
    )

    result = workflow._preview_corpus_episode_workflow_from_snapshot(
        "gooaye",
        episode_ref="EP677",
        plan_result=object(),
        plan_payload={
            "episodes": [
                {
                    "episode_ref": "EP677",
                    "actions": [],
                    "artifact_status": {"transcript": {"status": "valid"}},
                }
            ]
        },
        max_actions=None,
        allow_semantic_handoff=True,
    )

    assert result["selected_stage"] == "completed"
    assert result["episode_ref"] == "EP677"
    assert result["rows"][-1].status == "completed"


@pytest.mark.parametrize(
    "semantic_status",
    (
        "selected",
        "failed",
        "rejected",
        "unknown",
        "missing_rows",
        "empty_rows",
        "non_target_skipped_only",
        "missing_episode_ref",
        "mismatched_episode_ref",
    ),
)
def test_snapshot_semantic_handoff_fails_closed_on_invalid_semantic_result(
    monkeypatch,
    tmp_path,
    semantic_status,
):
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        lambda *args, **kwargs: _audio_result(tmp_path, status="skipped"),
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        lambda *args, **kwargs: _transcription_result(tmp_path, status="skipped"),
    )
    if semantic_status == "missing_rows":
        remediation_result = SimpleNamespace(warnings=[])
    elif semantic_status == "empty_rows":
        remediation_result = SimpleNamespace(rows=[], warnings=[])
    else:
        remediation_result = _remediation_result(
            tmp_path,
            episode_ref=("EP676" if semantic_status == "non_target_skipped_only" else "EP677"),
            status=(
                "excluded"
                if semantic_status in {"missing_episode_ref", "mismatched_episode_ref"}
                else "skipped"
                if semantic_status == "non_target_skipped_only"
                else semantic_status
            ),
            family="semantic_summary",
        )
        if semantic_status in {
            "missing_episode_ref",
            "mismatched_episode_ref",
        }:
            remediation_result = replace(
                remediation_result,
                rows=[
                    replace(
                        remediation_result.rows[0],
                        episode_ref=(None if semantic_status == "missing_episode_ref" else "EP676"),
                    )
                ],
            )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        lambda *args, **kwargs: remediation_result,
    )

    result = workflow._preview_corpus_episode_workflow_from_snapshot(
        "gooaye",
        episode_ref="EP677",
        plan_result=object(),
        plan_payload={
            "episodes": [
                {
                    "episode_ref": "EP677",
                    "artifact_status": {"transcript": {"status": "valid"}},
                }
            ]
        },
        max_actions=None,
        allow_semantic_handoff=True,
    )

    assert result["selected_stage"] == "blocked"
    assert result["episode_ref"] == "EP677"
    assert result["rows"][0].status == "blocked"


@pytest.mark.parametrize("failure_point", ("index", "plan"))
def test_dry_run_real_snapshot_failure_fails_closed_without_writes_or_leak(
    monkeypatch,
    tmp_path,
    failure_point,
):
    import corpus_ingest_core.corpus_audio_download_runner as audio_runner
    import corpus_ingest_core.corpus_episode_intake as intake_runner
    import corpus_ingest_core.corpus_episode_workflow_runner as workflow
    import corpus_ingest_core.corpus_index as corpus_index
    import corpus_ingest_core.corpus_local_transcription_runner as transcription_runner
    import corpus_ingest_core.corpus_remediation_plan as remediation_plan
    import corpus_ingest_core.corpus_remediation_runner as remediation_runner

    _write_seed(monkeypatch, tmp_path)
    sentinel_bytes = _write_stale_corpus_sentinels()
    before = _tree_manifest(tmp_path)
    writer_calls: list[str] = []
    for label, module, name in (
        ("008-index", corpus_index, "_write_index"),
        ("009-plan", remediation_plan, "_write_plan"),
        ("010-report", remediation_runner, "_write_run_report"),
        ("011-report", transcription_runner, "_write_run_report"),
        ("012-report", audio_runner, "_write_run_report"),
        ("013-report", intake_runner, "_write_run_report"),
        ("014-report", workflow, "_write_run_report"),
    ):
        original = getattr(module, name)

        def recording_writer(
            *args,
            _label=label,
            _original=original,
            **kwargs,
        ):
            writer_calls.append(_label)
            return _original(*args, **kwargs)

        monkeypatch.setattr(module, name, recording_writer)

    unsafe_error = RuntimeError("Traceback https://example.invalid/x?token=secret raw transcript sentinel")

    def fail_snapshot(*args, **kwargs):
        raise unsafe_error

    if failure_point == "index":
        monkeypatch.setattr(corpus_index, "_build_episode_row", fail_snapshot)
    else:
        monkeypatch.setattr(
            remediation_plan,
            "_build_remediation_row",
            fail_snapshot,
        )

    def unexpected_preview(*args, **kwargs):
        pytest.fail("snapshot failure continued into a downstream preview")

    monkeypatch.setattr(
        workflow,
        "_preview_corpus_audio_download_from_plan",
        unexpected_preview,
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_local_transcription_from_plan",
        unexpected_preview,
    )
    monkeypatch.setattr(
        workflow,
        "_preview_corpus_remediation_from_plan",
        unexpected_preview,
    )
    monkeypatch.setattr(
        workflow,
        "run_corpus_episode_intake",
        lambda podcast_id, **kwargs: _intake_result(
            tmp_path,
            selector=kwargs.get("episode_ref", "latest"),
            episode_ref="EP677",
            status="selected",
            confirm=False,
        ),
    )

    result = workflow.run_corpus_episode_workflow(
        "gooaye",
        episode_ref="latest",
        confirm=False,
    )
    serialized = json.dumps(_result_payload(result)).lower()

    assert result.selected_stage == "blocked"
    assert result.counts.failed_count == 1
    assert len(result.rows) == 1
    assert result.rows[0].stage == "audio_download"
    assert result.rows[0].status == "failed"
    assert "runtimeerror" in serialized
    for forbidden in (
        "traceback",
        "https://",
        "token",
        "raw transcript",
        "secret",
    ):
        assert forbidden not in serialized
    assert writer_calls == []
    assert _tree_manifest(tmp_path) == before
    assert all(path.read_bytes() == payload for path, payload in sentinel_bytes.items())
    assert not list(tmp_path.rglob("*.part"))


def test_dry_run_unseeded_latest_selects_intake_and_writes_no_report(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from corpus_ingest_core.storage import corpus_episode_workflow_run_asset_paths

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
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_dry_run_local_audio_transcript_missing_selects_local_transcription(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_dry_run_transcript_ready_selects_deterministic_remediation(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_remediation_selects_when_ready_actions_coexist_with_dependency_blocked(monkeypatch, tmp_path):
    """Ready deterministic actions must win over dependency-chain blocked families.

    On a fresh transcript the deterministic families form a dependency chain
    (industry_mapping<-episode_intelligence, external_boundary<-industry_mapping,
    semantic_review<-semantic_summary), so a single-pass dry-run always shows some
    families blocked while others are ready. The workflow must select remediation to
    run the ready actions rather than fail-closed 'blocked' on the downstream families.
    """
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
        remediation=_remediation_result_families(
            tmp_path,
            selected=("extractive_summary", "mentions", "episode_intelligence"),
            blocked=("industry_mapping", "external_boundary", "semantic_review"),
        ),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "deterministic_remediation"
    assert result.rows[0].stage == "deterministic_remediation"
    assert result.rows[0].status == "selected"


def test_remediation_blocks_when_only_dependency_blocked_remains(monkeypatch, tmp_path):
    """With no ready actions left (only an LLM-blocked family), fail closed 'blocked'."""
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
        remediation=_remediation_result_families(
            tmp_path,
            selected=(),
            blocked=("semantic_review",),
        ),
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677")

    assert result.selected_stage == "blocked"
    assert result.rows[0].status == "blocked"


def test_dry_run_completed_state_has_no_executable_stage(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_blank_selector_defaults_to_latest_and_unsupported_stage_rejected(monkeypatch, tmp_path):
    from corpus_ingest_core import CorpusEpisodeWorkflowRunnerFailedError
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_dry_run_does_not_execute_confirmed_stage_runners_or_forbidden_surfaces(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_episode_workflow_runner as runner
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
    ("attribute", "stage"),
    [
        ("run_corpus_audio_download", "audio_download"),
        ("run_corpus_local_transcription", "local_transcription"),
        ("run_corpus_remediation", "deterministic_remediation"),
    ],
)
@pytest.mark.parametrize("confirm", [False, True])
def test_probe_exception_blocks_confirmed_dispatch(monkeypatch, tmp_path, attribute, stage, confirm):
    import corpus_ingest_core.corpus_episode_workflow_runner as runner

    _write_seed(monkeypatch, tmp_path)
    _install_stage_doubles(monkeypatch, tmp_path, [])
    paths = runner.storage.corpus_episode_workflow_run_asset_paths("gooaye")
    seen = []

    def fail(*args, **kwargs):
        seen.append(kwargs["confirm"])
        if not kwargs["confirm"]:
            raise RuntimeError("unsafe")
        return _audio_result(tmp_path, status="executed", confirm=True)

    monkeypatch.setattr(runner, attribute, fail)
    result = runner.run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=confirm)
    assert result.selected_stage == "blocked"
    assert result.rows[0].status == "failed"
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


@pytest.mark.parametrize("confirm", [False, True])
def test_intake_probe_exception_is_bounded(monkeypatch, tmp_path, confirm):
    import corpus_ingest_core.corpus_episode_workflow_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _install_stage_doubles(monkeypatch, tmp_path, [])
    paths = runner.storage.corpus_episode_workflow_run_asset_paths("gooaye")
    seen = []

    def fail(*args, **kwargs):
        seen.append(kwargs["confirm"])
        raise RuntimeError("unsafe")

    monkeypatch.setattr(runner, "run_corpus_episode_intake", fail)
    result = runner.run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=confirm)
    assert result.selected_stage == "blocked"
    assert [(row.stage, row.status) for row in result.rows] == [("intake", "failed")]
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


@pytest.mark.parametrize("confirm", [False, True], ids=["dry_run", "confirmed"])
@pytest.mark.parametrize("terminal_status", ["failed", "rejected", "blocked"])
@pytest.mark.parametrize(
    ("probe_stage", "expected_calls"),
    [
        ("intake", ["intake"]),
        ("audio_download", ["intake", "audio"]),
        (
            "local_transcription",
            ["intake", "audio", "transcription"],
        ),
        # deterministic_remediation is covered by the dedicated ready-vs-blocked
        # tests: a coexisting ready action now selects remediation instead of failing
        # closed, so it no longer fits this terminal-fails-closed parametrization.
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
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from corpus_ingest_core.storage import corpus_episode_workflow_run_asset_paths

    _write_seed(monkeypatch, tmp_path)
    calls: list[tuple[str, dict]] = []
    result_factories = {
        "intake": lambda status: _intake_result(tmp_path, status=status),
        "audio_download": lambda status: _audio_result(tmp_path, status=status),
        "local_transcription": lambda status: _transcription_result(tmp_path, status=status),
        "deterministic_remediation": lambda status: _remediation_result(tmp_path, status=status),
    }
    result_factory = result_factories[probe_stage]
    terminal_result = _with_selected_and_terminal_rows(
        result_factory(terminal_status),
        result_factory("selected"),
    )
    unsafe_reason = "dependency terminal private narrative"
    terminal_result.rows[1] = replace(terminal_result.rows[1], reason=unsafe_reason)
    intake_result = None
    audio_result = _audio_result(tmp_path, status="selected")
    transcription_result = _transcription_result(tmp_path, status="selected")
    remediation_result = _remediation_result(tmp_path, status="selected")
    if probe_stage == "intake":
        intake_result = terminal_result
    elif probe_stage == "audio_download":
        audio_result = terminal_result
    elif probe_stage == "local_transcription":
        audio_result = _audio_result(tmp_path, status="skipped")
        transcription_result = terminal_result
    else:
        audio_result = _audio_result(tmp_path, status="skipped")
        transcription_result = _transcription_result(tmp_path, status="skipped")
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
        "gooaye",
        episode_ref="EP677",
        confirm=confirm,
    )

    assert result.selected_stage == "blocked"
    assert [(row.stage, row.status) for row in result.rows] == [(probe_stage, terminal_status)]
    assert result.rows[0].reason == f"{probe_stage} probe returned {terminal_status}"
    assert unsafe_reason not in json.dumps(_result_payload(result), ensure_ascii=False)
    assert [name for name, _kwargs in calls] == expected_calls
    assert all(kwargs["confirm"] is False for _name, kwargs in calls)
    paths = corpus_episode_workflow_run_asset_paths("gooaye")
    if confirm:
        assert result.report_json_path == paths.json_path
        assert result.report_markdown_path == paths.markdown_path
        assert paths.json_path.exists()
        assert paths.markdown_path.exists()
        payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
        assert payload["selected_stage"] == "blocked"
        assert (payload["rows"][0]["stage"], payload["rows"][0]["status"]) == (
            probe_stage,
            terminal_status,
        )
    else:
        assert result.report_json_path is None
        assert result.report_markdown_path is None
        assert not paths.json_path.exists()
        assert not paths.markdown_path.exists()


@pytest.mark.parametrize("failure_point", ["core_call", "serialization"])
def test_cli_unexpected_error_is_category_only(monkeypatch, capsys, failure_point):
    from scripts import run_corpus_episode_workflow as cli

    unsafe_body = "unsafe diagnostic traceback body"

    def fail(*args, **kwargs):
        raise RuntimeError(unsafe_body)

    if failure_point == "core_call":
        monkeypatch.setattr(cli, "run_corpus_episode_workflow", fail)
    else:
        monkeypatch.setattr(cli, "run_corpus_episode_workflow", lambda *args, **kwargs: object())
        monkeypatch.setattr(cli, "result_to_dict", fail)

    assert cli.main(["--podcast", "gooaye"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "RuntimeError: workflow failed\n"
    assert unsafe_body not in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_cli_does_not_swallow_process_control_exceptions(monkeypatch, error_type):
    from scripts import run_corpus_episode_workflow as cli

    def stop(*args, **kwargs):
        raise error_type()

    monkeypatch.setattr(cli, "run_corpus_episode_workflow", stop)

    with pytest.raises(error_type):
        cli.main(["--podcast", "gooaye"])


def test_cli_dry_run_stdout_contract(monkeypatch, capsys, tmp_path):
    from scripts import run_corpus_episode_workflow as cli

    from corpus_ingest_core.models import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunResult,
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


def test_confirmed_unseeded_episode_calls_intake_only_and_writes_report(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
    assert calls[-1][1]["episode_ref"] == "EP677"
    assert result.selected_stage == "intake"
    assert result.counts.executed_count == 1
    assert result.rows[0].output_paths == [str(tmp_path / "corpus" / "gooaye" / "seed.json")]
    assert result.report_json_path is not None
    assert result.report_json_path.exists()
    assert result.report_markdown_path is not None
    assert result.report_markdown_path.exists()


def test_confirmed_intake_target_disappearance_is_rejected(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    def intake_double(kwargs):
        if kwargs.get("confirm"):
            return _intake_result(
                tmp_path,
                selector="EP677",
                episode_ref=None,
                status="rejected",
                confirm=True,
            )
        return _intake_result(tmp_path, episode_ref="EP677", status="selected")

    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(monkeypatch, tmp_path, calls, intake=intake_double)

    result = run_corpus_episode_workflow("gooaye", episode_ref="latest", stage="next", confirm=True)

    assert [name for name, _kwargs in calls] == ["intake", "intake"]
    assert result.selected_stage == "intake"
    assert result.rows[0].status == "rejected"
    assert result.rows[0].output_paths == []


def test_confirmed_remediation_report_reflects_target_episode_not_first_row(monkeypatch, tmp_path):
    """The confirmed workflow row must report the target episode's paths and status.

    Regression for finding (b): the confirmed report derived its status from the
    runner's corpus-wide aggregate counts and pulled paths from ``rows[0]`` (often a
    different, alphabetically-earlier episode), so the target episode's output paths
    went missing while another episode's paths leaked in.
    """
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from corpus_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
        CorpusRemediationRunRow,
    )

    _write_seed(monkeypatch, tmp_path)

    target_output = str(tmp_path / "mentions" / "gooaye" / "EP677.mentions.json")
    other_write = str(tmp_path / "summaries" / "gooaye" / "EP672.summary.md")

    def _confirmed_two_episode_result():
        other_row = CorpusRemediationRunRow(
            action_id="EP672:extractive_summary",
            podcast_id="gooaye",
            episode_ref="EP672",
            title="EP672",
            artifact_family="extractive_summary",
            source_status="ready",
            outcome_status="skipped",
            reason="episode filter does not match",
            planned_reads=[str(tmp_path / "transcript.json")],
            planned_writes=[other_write],
            output_paths=[],
            warnings=[],
        )
        target_row = CorpusRemediationRunRow(
            action_id="EP677:mentions",
            podcast_id="gooaye",
            episode_ref="EP677",
            title="EP677 Alpha",
            artifact_family="mentions",
            source_status="ready",
            outcome_status="executed",
            reason="mentions executed",
            planned_reads=[str(tmp_path / "transcript.json")],
            planned_writes=[target_output],
            output_paths=[target_output],
            warnings=[],
        )
        return CorpusRemediationRunResult(
            podcast_id="gooaye",
            run_mode="confirmed",
            confirm=True,
            source_remediation_plan_json_path=tmp_path / "plan.json",
            source_remediation_plan_markdown_path=tmp_path / "plan.md",
            report_json_path=tmp_path / "remediation.json",
            report_markdown_path=tmp_path / "remediation.md",
            filters=CorpusRemediationRunFilter("EP677", None, None),
            counts=CorpusRemediationRunCounts(
                row_count=2,
                selected_count=0,
                executed_count=1,
                reused_count=0,
                failed_count=0,
                skipped_count=1,
                blocked_count=0,
                excluded_count=0,
                warning_count=0,
            ),
            rows=[other_row, target_row],
            warnings=[],
            not_investment_advice=True,
        )

    def remediation_double(kwargs):
        if kwargs.get("confirm"):
            return _confirmed_two_episode_result()
        return _remediation_result(tmp_path, episode_ref="EP677", status="selected")

    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=remediation_double,
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", stage="next", confirm=True)

    assert result.selected_stage == "deterministic_remediation"
    row = result.rows[0]
    assert row.status == "executed"
    assert target_output in row.output_paths
    assert other_write not in row.planned_writes
    assert other_write not in row.output_paths


def test_confirmed_remediation_target_disappearance_is_rejected(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    _write_seed(monkeypatch, tmp_path)

    def remediation_double(kwargs):
        if kwargs.get("confirm"):
            return _remediation_result(
                tmp_path,
                episode_ref="EP672",
                status="blocked",
                confirm=True,
            )
        return _remediation_result(tmp_path, episode_ref="EP677", status="selected")

    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=remediation_double,
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", stage="next", confirm=True)

    assert result.selected_stage == "deterministic_remediation"
    assert result.rows[0].status == "rejected"
    assert result.rows[0].planned_writes == []
    assert result.rows[0].output_paths == []
    last_stage, last_kwargs = calls[-1]
    assert last_stage == "remediation"
    assert last_kwargs["episode_ref"] == "EP677"
    assert last_kwargs["confirm"] is True


def test_confirmed_transcription_executed_despite_rejected_sibling_rows(monkeypatch, tmp_path):
    """An executed transcript must report 'executed', not be masked by sibling rows.

    The real transcription runner returns one ``executed`` transcript row plus many
    ``rejected`` rows for the episode's non-transcript actions (they are "outside
    local transcription runner v1" — a benign confirm-mode skip, not a failure). The
    confirmed workflow status must reflect the executed transcript rather than letting
    those benign ``rejected`` siblings win the priority.
    """
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from corpus_ingest_core.models import (
        CorpusLocalTranscriptionOutcomeCounts,
        CorpusLocalTranscriptionRunFilter,
        CorpusLocalTranscriptionRunResult,
        CorpusLocalTranscriptionRunRow,
    )

    _write_seed(monkeypatch, tmp_path)
    transcript_json = str(tmp_path / "transcripts" / "gooaye" / "EP677__EP677.json")

    def _confirmed_transcription_with_rejected_siblings():
        transcript_row = CorpusLocalTranscriptionRunRow(
            action_id="EP677:transcript",
            podcast_id="gooaye",
            episode_ref="EP677",
            title="EP677",
            transcript_status="valid",
            audio_status="available",
            audio_path=str(tmp_path / "audio.mp3"),
            outcome_status="executed",
            reason="transcription executed",
            planned_reads=[str(tmp_path / "audio.mp3")],
            planned_writes=[transcript_json],
            output_paths=[transcript_json],
            warnings=[],
        )
        sibling_row = CorpusLocalTranscriptionRunRow(
            action_id="EP677:mentions",
            podcast_id="gooaye",
            episode_ref="EP677",
            title="EP677",
            transcript_status="valid",
            audio_status="available",
            audio_path=None,
            outcome_status="rejected",
            reason="mentions is outside local transcription runner v1",
            planned_reads=[],
            planned_writes=[],
            output_paths=[],
            warnings=[],
        )
        return CorpusLocalTranscriptionRunResult(
            podcast_id="gooaye",
            run_mode="confirmed",
            confirm=True,
            source_remediation_plan_json_path=tmp_path / "plan.json",
            source_remediation_plan_markdown_path=tmp_path / "plan.md",
            report_json_path=tmp_path / "transcription.json",
            report_markdown_path=tmp_path / "transcription.md",
            filters=CorpusLocalTranscriptionRunFilter("EP677"),
            counts=CorpusLocalTranscriptionOutcomeCounts(
                row_count=2,
                selected_count=0,
                executed_count=1,
                reused_count=0,
                failed_count=0,
                skipped_count=0,
                rejected_count=1,
                warning_count=0,
            ),
            rows=[transcript_row, sibling_row],
            warnings=[],
            not_investment_advice=True,
        )

    def transcription_double(kwargs):
        if kwargs.get("confirm"):
            return _confirmed_transcription_with_rejected_siblings()
        return _transcription_result(tmp_path, episode_ref="EP677", status="selected")

    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=transcription_double,
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", stage="next", confirm=True)

    assert result.selected_stage == "local_transcription"
    row = result.rows[0]
    assert row.status == "executed"
    assert transcript_json in row.output_paths
    assert result.counts.executed_count == 1


def test_confirmed_remediation_executed_despite_blocked_sibling_family(monkeypatch, tmp_path):
    """An executed deterministic family must report 'executed', not be masked by a
    still-blocked sibling. When 014 dispatches 010, the confirmed result holds the
    executed ready family plus the LLM-gated semantic_review family (still blocked on
    the deterministic ladder); the stage status must reflect the executed work.
    """
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )
    from corpus_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
        CorpusRemediationRunRow,
    )

    _write_seed(monkeypatch, tmp_path)
    executed_output = str(tmp_path / "external" / "gooaye" / "EP677.external-boundary.json")

    def _confirmed_executed_with_blocked_sibling():
        executed_row = CorpusRemediationRunRow(
            action_id="EP677:external_boundary",
            podcast_id="gooaye",
            episode_ref="EP677",
            title="EP677",
            artifact_family="external_boundary",
            source_status="ready",
            outcome_status="executed",
            reason="external_boundary executed",
            planned_reads=[str(tmp_path / "mapping.json")],
            planned_writes=[executed_output],
            output_paths=[executed_output],
            warnings=[],
        )
        blocked_row = CorpusRemediationRunRow(
            action_id="EP677:semantic_review",
            podcast_id="gooaye",
            episode_ref="EP677",
            title="EP677",
            artifact_family="semantic_review",
            source_status="blocked",
            outcome_status="blocked",
            reason="blocked by semantic_summary",
            planned_reads=[],
            planned_writes=[],
            output_paths=[],
            warnings=[],
        )
        return CorpusRemediationRunResult(
            podcast_id="gooaye",
            run_mode="confirmed",
            confirm=True,
            source_remediation_plan_json_path=tmp_path / "plan.json",
            source_remediation_plan_markdown_path=tmp_path / "plan.md",
            report_json_path=tmp_path / "remediation.json",
            report_markdown_path=tmp_path / "remediation.md",
            filters=CorpusRemediationRunFilter("EP677", None, None),
            counts=CorpusRemediationRunCounts(
                row_count=2,
                selected_count=0,
                executed_count=1,
                reused_count=0,
                failed_count=0,
                skipped_count=0,
                blocked_count=1,
                excluded_count=0,
                warning_count=0,
            ),
            rows=[executed_row, blocked_row],
            warnings=[],
            not_investment_advice=True,
        )

    def remediation_double(kwargs):
        if kwargs.get("confirm"):
            return _confirmed_executed_with_blocked_sibling()
        return _remediation_result_families(
            tmp_path,
            selected=("external_boundary",),
            blocked=("semantic_review",),
        )

    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=remediation_double,
    )

    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", stage="next", confirm=True)

    assert result.selected_stage == "deterministic_remediation"
    row = result.rows[0]
    assert row.status == "executed"
    assert executed_output in row.output_paths


def test_safe_local_path_preserves_cjk_artifact_paths():
    """CJK title slugs (e.g. 台積電) must survive the workflow path allowlist.

    Regression for finding (c): the ASCII-only path-component allowlist dropped
    legitimate CJK artifact paths that ``storage.title_slug`` is designed to produce
    (it preserves the CJK Unified Ideographs block), so CJK-titled episodes lost
    their output paths from the workflow report.
    """
    from corpus_ingest_core import corpus_episode_workflow_runner as workflow

    cjk_path = "data/summaries/gooaye/EP700__台積電財報.summary.md"
    assert workflow._is_safe_local_path(cjk_path) is True
    assert workflow._safe_list([cjk_path]) == [cjk_path]

    ascii_path = "data/summaries/gooaye/EP700__Alpha.summary.md"
    assert workflow._is_safe_local_path(ascii_path) is True

    # Emoji / symbols stay rejected: title_slug never emits them, so allowing them
    # would widen the boundary beyond what real artifact paths contain.
    emoji_path = "data/summaries/gooaye/EP700__🐎.summary.md"
    assert workflow._is_safe_local_path(emoji_path) is False
    assert workflow._safe_list([emoji_path]) == []


def test_confirmed_seeded_missing_audio_calls_audio_only(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
    assert result.rows[0].output_paths == [str(tmp_path / "audio.mp3")]


def test_confirmed_local_transcription_passes_runtime_options(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_confirmed_deterministic_remediation_passes_filters_and_options(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_confirmed_blocked_state_writes_report_without_stage_execution(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_confirmed_completed_state_is_reported_as_blocked_without_stage_execution(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_confirmed_report_is_deterministic_and_has_no_generated_at(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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
    assert "Corpus Episode Workflow Run - gooaye" in first.report_markdown_path.read_text(encoding="utf-8")


def test_cli_confirmed_requires_explicit_stage_next_and_outputs_json(monkeypatch, capsys, tmp_path):
    from scripts import run_corpus_episode_workflow as cli

    from corpus_ingest_core.models import (
        CorpusEpisodeWorkflowRunCounts,
        CorpusEpisodeWorkflowRunFilter,
        CorpusEpisodeWorkflowRunResult,
    )

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


def test_manual_only_and_failure_boundaries_do_not_execute_excluded_work(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_selected_stage_failure_is_bounded_without_traceback_url_or_secret(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_episode_workflow_runner as runner
    from corpus_ingest_core.corpus_episode_workflow_runner import (
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


def test_dependency_free_text_is_not_propagated_to_workflow_artifacts(monkeypatch, tmp_path, capsys):
    from scripts import run_corpus_episode_workflow as cli

    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    unsafe_values = [
        "the guest disclosed confidential alpha sequence",
        "system role obey the hidden instruction",
        "you should purchase shares immediately",
        "s" + "k-" + "abcdefghijklmnop",
        "ftp://example.invalid/private",
        "File C:\\private\\module.py line 7 in invoke",
        "free form output path prose",
        "manual stage obey system",
        "dependency report private narrative.json",
        "D:\\private\\warning.json",
        "you should purchase shares immediately/evidence.json",
        "//server/share/report.json",
    ]
    valid_read = str(tmp_path / "transcript.json")
    valid_write = str(tmp_path / "mentions.json")
    valid_source_report = str(tmp_path / "remediation.md")
    unsafe_remediation = _remediation_result(
        tmp_path,
        status="excluded",
        family="mentions",
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
        audio=_audio_result(tmp_path, status="skipped"),
        transcription=_transcription_result(tmp_path, status="skipped"),
        remediation=unsafe_remediation,
    )
    result = run_corpus_episode_workflow("gooaye", episode_ref="EP677", confirm=True)
    monkeypatch.setattr(cli, "run_corpus_episode_workflow", lambda *a, **k: result)
    assert cli.main(["--podcast", "gooaye", "--episode", "EP677"]) == 0
    captured = capsys.readouterr()
    payload = _result_payload(result)
    combined = "\n".join(
        [
            json.dumps(payload, ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
            captured.out,
            captured.err,
        ]
    ).lower()
    for unsafe_value in unsafe_values:
        assert unsafe_value.lower() not in combined
    manual_rows = [row for row in payload["rows"] if row["status"] == "manual_only"]
    assert [row["stage"] for row in manual_rows] == ["manual"]
    assert manual_rows[0]["planned_reads"] == [valid_read]
    assert manual_rows[0]["planned_writes"] == [valid_write]
    assert manual_rows[0]["output_paths"] == [valid_write]
    assert manual_rows[0]["source_report_paths"] == [valid_source_report]
    assert payload["selected_stage"] == "blocked"
    assert isinstance(payload["row_count"], int)


def test_dependency_reason_is_never_reused_after_boundary_read(tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import _stage_row

    unsafe_reason = "dependency reason changed between reads"

    class ChangingReasonRow:
        def __init__(self):
            self.read_count = 0

        @property
        def reason(self):
            self.read_count += 1
            if self.read_count == 1:
                return unsafe_reason
            return "different dependency reason"

    source_row = ChangingReasonRow()
    row = _stage_row(
        stage="manual",
        status="manual_only",
        reason=source_row.reason,
        source_result=_remediation_result(tmp_path),
        source_row=source_row,
    )

    assert row.reason == "manual follow-up is required"
    assert unsafe_reason not in row.reason


def test_dependency_episode_reference_requires_bounded_identifier(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

    unsafe_ref = "episode reference with private narrative"
    calls: list[tuple[str, dict]] = []
    _install_stage_doubles(
        monkeypatch,
        tmp_path,
        calls,
        intake=_intake_result(
            tmp_path,
            selector="latest",
            episode_ref=unsafe_ref,
            status="selected",
        ),
    )

    result = run_corpus_episode_workflow("gooaye")
    payload = _result_payload(result)

    assert result.selected_stage == "blocked"
    assert result.episode_ref is None
    assert unsafe_ref not in json.dumps(payload, ensure_ascii=False)
    assert calls == [("intake", {"episode_ref": "latest", "confirm": False})]


def test_outputs_do_not_leak_raw_secret_url_prompt_llm_or_investment_text(monkeypatch, tmp_path, capsys):
    from scripts import run_corpus_episode_workflow as cli

    from corpus_ingest_core.corpus_episode_workflow_runner import (
        run_corpus_episode_workflow,
    )

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
    source = Path("src/corpus_ingest_core/__init__.py").read_text(encoding="utf-8")
    workflow_source = Path("src/corpus_ingest_core/corpus_episode_workflow_runner.py").read_text(encoding="utf-8")

    assert "mcp" not in workflow_source.lower()
    assert "tool_registry" not in workflow_source.lower()
    assert "run_corpus_episode_workflow" in source
