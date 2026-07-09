from __future__ import annotations

from dataclasses import asdict
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


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_episode_seed(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP677",
    title: str = "EP677 Alpha",
    has_audio_url: bool = True,
) -> Path:
    from podcast_ingest_core.storage import corpus_episode_seed_asset_path

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    return _write_json(
        corpus_episode_seed_asset_path(podcast_id, episode_ref),
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
            "duration": "00:42:00",
            "guid_status": "present",
            "has_audio_url": has_audio_url,
            "seed_source": "rss",
            "selector": "latest",
            "warning_count": 0,
            "warnings": [],
            "not_investment_advice": True,
        },
    )


def _extra_action(episode_ref: str, family: str, status: str = "ready") -> dict:
    return {
        "action_id": f"{episode_ref}:{family}",
        "artifact_family": family,
        "action_type": "download" if family == "audio" else "generate",
        "status": status,
        "order": 1 if family == "audio" else 9,
        "reason": f"{family} artifact is missing",
        "blocking_artifacts": [] if status == "ready" else ["audio"],
        "suggested_command": "python scripts/placeholder.py",
        "manual_only": True,
        "optional": family.startswith("semantic"),
        "gated": family == "semantic_summary",
        "requires_api_cost_ack": family == "semantic_summary",
    }


def _episode_payload(
    episode_ref: str,
    *,
    title: str = "Alpha",
    audio_status: str = "missing",
    audio_path: str | None = None,
    audio_action_status: str | None = "ready",
    extra_actions: list[dict] | None = None,
    warnings: list[dict | str] | None = None,
) -> dict:
    actions: list[dict] = []
    if audio_action_status is not None:
        actions.append(_extra_action(episode_ref, "audio", audio_action_status))
    actions.extend(extra_actions or [])
    audio_paths = {"audio": audio_path} if audio_path is not None else {}
    return {
        "podcast_id": "gooaye",
        "episode_ref": episode_ref,
        "title": title,
        "artifact_status": {
            "audio": {
                "status": audio_status,
                "path": audio_path,
                "paths": audio_paths,
            },
            "transcript": {"status": "missing", "paths": {}},
        },
        "missing_artifacts": ["audio"] if audio_status == "missing" else [],
        "blockers": [],
        "warnings": warnings or [],
        "actions": actions,
    }


def _plan_payload(episodes: list[dict], *, podcast_id: str = "gooaye") -> dict:
    action_count = sum(len(episode.get("actions", [])) for episode in episodes)
    return {
        "podcast_id": podcast_id,
        "plan_mode": "deterministic-corpus-remediation-plan-v1",
        "source_scope": "refreshed-local-corpus-index-only",
        "source_corpus_index_json_path": f"data/corpus/{podcast_id}/corpus-index.json",
        "source_corpus_index_markdown_path": f"data/corpus/{podcast_id}/corpus-index.md",
        "episode_count": len(episodes),
        "action_count": action_count,
        "blocked_action_count": sum(
            action.get("status") == "blocked"
            for episode in episodes
            for action in episode.get("actions", [])
        ),
        "optional_action_count": sum(
            action.get("optional", False)
            for episode in episodes
            for action in episode.get("actions", [])
        ),
        "gated_action_count": sum(
            action.get("gated", False)
            for episode in episodes
            for action in episode.get("actions", [])
        ),
        "warning_count": 0,
        "episodes": sorted(episodes, key=lambda episode: episode["episode_ref"]),
        "not_investment_advice": True,
    }


def _fake_plan_refresh(
    monkeypatch,
    tmp_path: Path,
    payload: dict,
    calls: list[str] | None = None,
):
    from podcast_ingest_core import storage
    from podcast_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )
    import podcast_ingest_core.corpus_audio_download_runner as runner

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
            source_corpus_index_markdown_path=Path(
                payload["source_corpus_index_markdown_path"]
            ),
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


def _audio_asset(
    tmp_path: Path,
    *,
    episode_ref: str = "EP001",
    downloaded: bool = True,
    already_exists: bool = False,
    source_url: str = "https://example.invalid/audio.mp3?token=secret-value",
    local_name: str | None = None,
):
    from podcast_ingest_core.models import AudioAsset

    local_path = tmp_path / "audio" / "gooaye" / (local_name or f"{episode_ref}__Alpha.mp3")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(b"audio")
    return AudioAsset(
        podcast_id="gooaye",
        episode_ref=episode_ref,
        title="Alpha",
        source_url=source_url,
        local_path=local_path,
        content_type="audio/mpeg",
        size_bytes=local_path.stat().st_size,
        downloaded=downloaded,
        already_exists=already_exists,
    )


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


def test_corpus_audio_download_run_asset_paths_contract():
    from podcast_ingest_core.storage import corpus_audio_download_run_asset_paths

    paths = corpus_audio_download_run_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-audio-download-run.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-audio-download-run.md")


def test_corpus_audio_download_public_result_contract_exports(tmp_path):
    from podcast_ingest_core import (
        CorpusAudioDownloadOutcomeCounts,
        CorpusAudioDownloadRunFilter,
        CorpusAudioDownloadRunResult,
        CorpusAudioDownloadRunRow,
        CorpusAudioDownloadRunWarning,
        CorpusAudioDownloadRunnerFailedError,
        run_corpus_audio_download,
    )

    filters = CorpusAudioDownloadRunFilter(episode_ref="EP672")
    counts = CorpusAudioDownloadOutcomeCounts(
        row_count=1,
        selected_count=1,
        downloaded_count=0,
        reused_count=0,
        failed_count=0,
        skipped_count=0,
        rejected_count=0,
        warning_count=0,
    )
    warning = CorpusAudioDownloadRunWarning(
        scope="run",
        episode_ref=None,
        message="downstream corpus work remains manual",
    )
    row = CorpusAudioDownloadRunRow(
        action_id="EP672:audio",
        podcast_id="gooaye",
        episode_ref="EP672",
        audio_status="missing",
        outcome_status="selected",
        reason="audio missing and download action ready",
        planned_reads=[str(tmp_path / "corpus-remediation-plan.json")],
        planned_writes=[str(tmp_path / "audio" / "EP672.mp3")],
        local_audio_path=None,
        content_type=None,
        size_bytes=None,
        warnings=[],
    )
    result = CorpusAudioDownloadRunResult(
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
    assert CorpusAudioDownloadRunnerFailedError.__name__ == (
        "CorpusAudioDownloadRunnerFailedError"
    )
    assert callable(run_corpus_audio_download)


def test_corpus_audio_download_runner_error_contract():
    from podcast_ingest_core import (
        CorpusAudioDownloadRunnerFailedError,
        PodcastIngestCoreError,
    )

    assert issubclass(CorpusAudioDownloadRunnerFailedError, PodcastIngestCoreError)


def test_dry_run_empty_corpus_writes_no_report(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )
    from podcast_ingest_core.storage import corpus_audio_download_run_asset_paths

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([]))

    result = run_corpus_audio_download("gooaye")

    paths = corpus_audio_download_run_asset_paths("gooaye")
    assert result.run_mode == "dry_run"
    assert result.counts.row_count == 0
    assert result.counts.selected_count == 0
    assert result.counts.downloaded_count == 0
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert not paths.json_path.exists()
    assert not paths.markdown_path.exists()


def test_dry_run_refreshes_remediation_plan_before_selection(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    calls: list[str] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001")]),
        calls,
    )

    result = run_corpus_audio_download("gooaye")

    assert calls == ["refresh:gooaye"]
    assert result.counts.selected_count == 1
    assert result.rows[0].episode_ref == "EP001"


def test_dry_run_selects_only_missing_audio_ready_actions(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                _episode_payload("EP001"),
                _episode_payload("EP002", audio_status="available", audio_action_status=None),
                _episode_payload("EP003", audio_status="unreadable"),
                _episode_payload("EP004", audio_action_status="blocked"),
                _episode_payload("EP005", audio_action_status="manual"),
            ]
        ),
    )

    result = run_corpus_audio_download("gooaye")
    rows = _rows_by_episode(result)

    assert rows["EP001"].outcome_status == "selected"
    assert rows["EP002"].outcome_status == "skipped"
    assert rows["EP003"].outcome_status == "skipped"
    assert rows["EP004"].outcome_status == "skipped"
    assert rows["EP005"].outcome_status == "skipped"
    assert result.counts.selected_count == 1
    assert result.counts.skipped_count == 4


def test_dry_run_selects_seeded_ready_audio_and_skips_seeded_no_audio(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _write_episode_seed(
        monkeypatch,
        tmp_path,
        episode_ref="EP677",
        title="EP677 Alpha",
        has_audio_url=True,
    )
    _write_episode_seed(
        monkeypatch,
        tmp_path,
        episode_ref="EP678",
        title="EP678 No Audio",
        has_audio_url=False,
    )

    result = run_corpus_audio_download("gooaye")
    rows = {row.action_id: row for row in result.rows}

    assert rows["EP677:audio"].outcome_status == "selected"
    assert rows["EP678:audio"].outcome_status == "skipped"
    assert "source action status is blocked" in rows["EP678:audio"].reason
    assert result.counts.selected_count == 1


def test_dry_run_skips_unsafe_states_and_other_families(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                _episode_payload(
                    "EP001",
                    extra_actions=[
                        _extra_action("EP001", "transcript"),
                        _extra_action("EP001", "semantic_summary"),
                        _extra_action("EP001", "semantic_review"),
                        _extra_action("EP001", "mentions"),
                        _extra_action("EP001", "episode_intelligence"),
                        _extra_action("EP001", "industry_mapping"),
                        _extra_action("EP001", "external_boundary"),
                        _extra_action("EP001", "stock_lens_report"),
                        _extra_action("EP001", "stock_lens_synthesis"),
                        _extra_action("EP001", "synthesis"),
                        _extra_action("EP001", "unknown_family"),
                    ],
                )
            ]
        ),
    )

    result = run_corpus_audio_download("gooaye")
    reasons = " ".join(row.reason for row in result.rows).lower()

    assert result.counts.selected_count == 1
    assert result.counts.skipped_count == 11
    for expected in (
        "transcript",
        "semantic_summary",
        "semantic_review",
        "mentions",
        "episode_intelligence",
        "industry_mapping",
        "external_boundary",
        "stock_lens_report",
        "stock_lens_synthesis",
        "synthesis",
        "unknown_family",
    ):
        assert expected in reasons


def test_dry_run_no_rss_network_downloader_or_report_write(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )
    from podcast_ingest_core.storage import corpus_audio_download_run_asset_paths

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))

    def forbidden_download(*args, **kwargs):
        raise AssertionError("dry-run must not call downloader")

    monkeypatch.setattr(runner, "download_audio", forbidden_download)

    result = run_corpus_audio_download("gooaye")

    report_paths = corpus_audio_download_run_asset_paths("gooaye")
    assert result.counts.selected_count == 1
    assert not report_paths.json_path.exists()
    assert not report_paths.markdown_path.exists()


def test_dry_run_is_deterministic_and_has_no_generated_at(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    payload = _plan_payload(
        [
            _episode_payload("EP002"),
            _episode_payload("EP001", audio_status="available", audio_action_status=None),
        ]
    )
    _fake_plan_refresh(monkeypatch, tmp_path, payload)

    first = _result_payload(run_corpus_audio_download("gooaye"))
    second = _result_payload(run_corpus_audio_download("gooaye"))
    text = json.dumps(first, ensure_ascii=False, sort_keys=True)

    assert first == second
    assert "generated_at" not in text


def test_run_corpus_audio_download_cli_dry_run_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import (
        CorpusAudioDownloadOutcomeCounts,
        CorpusAudioDownloadRunFilter,
        CorpusAudioDownloadRunResult,
    )
    from scripts import run_corpus_audio_download as cli

    result = CorpusAudioDownloadRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusAudioDownloadRunFilter(None),
        counts=CorpusAudioDownloadOutcomeCounts(
            row_count=2,
            selected_count=1,
            downloaded_count=0,
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

    monkeypatch.setattr(cli, "run_corpus_audio_download", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_corpus_audio_download.py", "--podcast", "gooaye"])

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["podcast_id"] == "gooaye"
    assert captured["kwargs"]["confirm"] is False
    assert payload["run_mode"] == "dry_run"
    assert payload["report_json_path"] is None
    assert payload["selected_count"] == 1
    assert payload["skipped_count"] == 1


@pytest.mark.parametrize("episode_ref", [None, "", "   "])
def test_confirmed_execution_rejects_missing_or_blank_episode_before_download(
    monkeypatch, tmp_path, episode_ref
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core import CorpusAudioDownloadRunnerFailedError
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    calls: list[str] = []
    monkeypatch.setattr(runner, "download_audio", lambda *args, **kwargs: calls.append("download"))

    with pytest.raises(CorpusAudioDownloadRunnerFailedError, match="episode"):
        run_corpus_audio_download("gooaye", confirm=True, episode_ref=episode_ref)

    assert calls == []


def test_confirmed_execution_records_absent_requested_episode_as_rejected(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    calls: list[str] = []
    monkeypatch.setattr(runner, "download_audio", lambda *args, **kwargs: calls.append("download"))

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP999")

    assert calls == []
    assert result.counts.rejected_count == 1
    assert result.rows[-1].episode_ref == "EP999"
    assert result.rows[-1].outcome_status == "rejected"
    assert result.report_json_path is not None
    assert result.report_json_path.exists()


def test_confirmed_execution_records_non_selected_episode_as_rejected(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([_episode_payload("EP001", audio_status="available", audio_action_status=None)]),
    )
    calls: list[str] = []
    monkeypatch.setattr(runner, "download_audio", lambda *args, **kwargs: calls.append("download"))

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert calls == []
    assert result.counts.rejected_count == 1
    assert result.counts.downloaded_count == 0
    assert result.rows[0].outcome_status == "rejected"
    assert "audio status is available" in result.rows[0].reason


def test_confirmed_execution_calls_download_audio_once_without_shell(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    calls: list[tuple[str, str]] = []

    def fake_download(podcast_id: str, episode_ref: str):
        calls.append((podcast_id, episode_ref))
        return _audio_asset(tmp_path, episode_ref=episode_ref)

    monkeypatch.setattr(runner, "download_audio", fake_download)

    def forbidden_shell(*args, **kwargs):
        raise AssertionError("runner must not shell out")

    monkeypatch.setattr(subprocess, "run", forbidden_shell)
    monkeypatch.setattr(subprocess, "Popen", forbidden_shell)

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert calls == [("gooaye", "EP001")]
    assert result.counts.downloaded_count == 1
    assert result.rows[0].local_audio_path is not None
    source = Path("src/podcast_ingest_core/corpus_audio_download_runner.py").read_text(
        encoding="utf-8"
    )
    assert "subprocess" not in source


def test_confirmed_execution_maps_downloaded_and_reused_outcomes(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(
            tmp_path,
            episode_ref=episode_ref,
            downloaded=False,
            already_exists=True,
        ),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert result.counts.reused_count == 1
    assert result.counts.downloaded_count == 0
    assert result.rows[0].outcome_status == "reused"
    assert result.rows[0].content_type == "audio/mpeg"
    assert result.rows[0].size_bytes == 5


def test_confirmed_run_report_json_and_markdown_are_written(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert result.report_json_path is not None
    assert result.report_markdown_path is not None
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    assert payload["run_mode"] == "confirmed"
    assert payload["downloaded_count"] == 1
    assert payload["rejected_count"] == 0
    assert "generated_at" not in result.report_json_path.read_text(encoding="utf-8")
    assert "Corpus Audio Download Run - gooaye" in markdown
    assert "not investment advice" in markdown.lower()


def test_cli_confirmed_stdout_and_stderr_contract(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core import CorpusAudioDownloadRunnerFailedError
    from podcast_ingest_core.models import (
        CorpusAudioDownloadOutcomeCounts,
        CorpusAudioDownloadRunFilter,
        CorpusAudioDownloadRunResult,
    )
    from scripts import run_corpus_audio_download as cli

    result = CorpusAudioDownloadRunResult(
        podcast_id="gooaye",
        run_mode="confirmed",
        confirm=True,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=tmp_path / "corpus-audio-download-run.json",
        report_markdown_path=tmp_path / "corpus-audio-download-run.md",
        filters=CorpusAudioDownloadRunFilter("EP001"),
        counts=CorpusAudioDownloadOutcomeCounts(
            row_count=1,
            selected_count=1,
            downloaded_count=1,
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
        return result

    monkeypatch.setattr(cli, "run_corpus_audio_download", fake_run)
    assert cli.main(["--podcast", "gooaye", "--episode", "EP001", "--confirm"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_json_path"] == str(tmp_path / "corpus-audio-download-run.json")
    assert payload["downloaded_count"] == 1

    def rejected(*args, **kwargs):
        raise CorpusAudioDownloadRunnerFailedError("confirm requires episode")

    monkeypatch.setattr(cli, "run_corpus_audio_download", rejected)
    assert cli.main(["--podcast", "gooaye", "--confirm"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "confirm requires episode" in captured.err


def test_download_failure_records_metadata_without_traceback_or_url(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))

    def fail_download(*args, **kwargs):
        raise RuntimeError(
            "https://example.invalid/audio.mp3?token=secret-value Traceback raw"
        )

    monkeypatch.setattr(runner, "download_audio", fail_download)

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert result.counts.failed_count == 1
    assert result.rows[0].outcome_status == "failed"
    combined = json.dumps(_result_payload(result), ensure_ascii=False)
    assert "RuntimeError" in combined
    assert "https://example.invalid" not in combined
    assert "token=secret-value" not in combined
    assert "Traceback raw" not in combined


def test_outputs_do_not_leak_source_url_secret_prompt_llm_or_traceback(
    monkeypatch, tmp_path, capsys
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )
    from scripts import run_corpus_audio_download as cli

    payload = _plan_payload(
        [
            _episode_payload(
                "EP001",
                title="Bearer abc123 TOKEN=title-secret",
                warnings=[
                    {
                        "scope": "episode",
                        "episode_ref": "EP001",
                        "artifact_family": "audio",
                        "message": "API_KEY=secret-value prompt text raw LLM output",
                    }
                ],
            )
        ]
    )
    _fake_plan_refresh(monkeypatch, tmp_path, payload)
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(
            tmp_path,
            episode_ref=episode_ref,
            source_url="https://example.invalid/audio.mp3?TOKEN=secret-value",
        ),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")
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
        "https://example.invalid",
        "TOKEN=secret-value",
        "API_KEY=secret-value",
        "prompt text",
        "raw LLM output",
        "Bearer abc123",
        "Traceback",
    ):
        assert forbidden not in combined


def test_confirmed_output_sanitizes_secret_like_local_audio_path(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(
            tmp_path,
            episode_ref=episode_ref,
            local_name="EP001__TOKEN=secret-value.mp3",
        ),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")
    combined = "\n".join(
        [
            json.dumps(_result_payload(result), ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
        ]
    )

    assert "TOKEN=secret-value" not in combined
    assert result.rows[0].local_audio_path == "path omitted by safety boundary"


def test_boundary_guard_excludes_forbidden_surfaces_without_execution(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert result.counts.downloaded_count == 1
    source = Path("src/podcast_ingest_core/corpus_audio_download_runner.py").read_text(
        encoding="utf-8"
    )
    forbidden_fragments = [
        "from .cache import",
        "from .feed_reader import",
        "from .llm_profiles import",
        "from .local_env import",
        "from .mcp_server import",
        "from .semantic_summarizer import",
        "from .transcriber import",
        "from .stock_lens",
        "requests",
        "urllib",
        "httpx",
        "run_corpus_remediation(",
        "rebuild_cache(",
        "transcribe_episode(",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_confirmed_writes_manual_follow_up_warning_without_downstream_calls(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

    assert any("manual" in warning.message.lower() for warning in result.warnings)
    assert any("cache" in warning.message.lower() for warning in result.warnings)
    source = Path("src/podcast_ingest_core/corpus_audio_download_runner.py").read_text(
        encoding="utf-8"
    )
    assert "rebuild_cache(" not in source
    assert "transcribe_episode(" not in source


def test_outputs_keep_no_investment_advice_boundary(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_audio_download_runner as runner
    from podcast_ingest_core.corpus_audio_download_runner import (
        run_corpus_audio_download,
    )

    _fake_plan_refresh(monkeypatch, tmp_path, _plan_payload([_episode_payload("EP001")]))
    monkeypatch.setattr(
        runner,
        "download_audio",
        lambda podcast_id, episode_ref: _audio_asset(tmp_path, episode_ref=episode_ref),
    )

    result = run_corpus_audio_download("gooaye", confirm=True, episode_ref="EP001")

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
