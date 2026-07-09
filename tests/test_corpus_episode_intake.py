from __future__ import annotations

from dataclasses import asdict
import inspect
import json
from pathlib import Path
import sys


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


def _episode(
    episode_ref: str = "EP677",
    *,
    title: str = "EP677 Alpha",
    audio_url: str | None = "https://media.example.invalid/alpha.mp3?token=secret",
    source_url: str | None = "https://source.example.invalid/episode?token=secret",
    description: str | None = "raw description must not leak",
):
    from podcast_ingest_core.models import Episode

    return Episode(
        podcast_id="gooaye",
        episode_ref=episode_ref,
        title=title,
        audio_url=audio_url,
        published_at="Thu, 09 Jul 2026 00:00:00 GMT",
        description=description,
        source_url=source_url,
        duration="00:42:00",
        guid="episode-guid-value",
        link=source_url,
    )


def _payload(result) -> dict:
    from podcast_ingest_core.corpus_episode_intake import result_to_dict

    return result_to_dict(result)


def test_corpus_episode_seed_storage_paths_contract():
    from podcast_ingest_core.storage import (
        corpus_episode_intake_run_asset_paths,
        corpus_episode_seed_asset_path,
    )

    seed_path = corpus_episode_seed_asset_path("gooaye", "EP677")
    run_paths = corpus_episode_intake_run_asset_paths("gooaye")

    assert seed_path == Path(
        "data/corpus/gooaye/episode-seeds/EP677.episode-seed.json"
    )
    assert run_paths.json_path == Path(
        "data/corpus/gooaye/corpus-episode-intake-run.json"
    )
    assert run_paths.markdown_path == Path(
        "data/corpus/gooaye/corpus-episode-intake-run.md"
    )


def test_corpus_episode_intake_public_result_contract_exports(tmp_path):
    from podcast_ingest_core import (
        CorpusEpisodeIntakeFilter,
        CorpusEpisodeIntakeOutcomeCounts,
        CorpusEpisodeIntakeRunResult,
        CorpusEpisodeIntakeRunRow,
        CorpusEpisodeIntakeRunWarning,
        CorpusEpisodeSeed,
        run_corpus_episode_intake,
    )

    filters = CorpusEpisodeIntakeFilter(episode_ref="latest")
    counts = CorpusEpisodeIntakeOutcomeCounts(
        row_count=1,
        selected_count=1,
        seeded_count=0,
        reused_count=0,
        failed_count=0,
        skipped_count=0,
        rejected_count=0,
        warning_count=1,
    )
    warning = CorpusEpisodeIntakeRunWarning(
        scope="run",
        episode_ref=None,
        message="manual follow-up remains required",
    )
    seed = CorpusEpisodeSeed(
        podcast_id="gooaye",
        episode_ref="EP677",
        title="EP677 Alpha",
        published_at="Thu, 09 Jul 2026 00:00:00 GMT",
        duration="00:42:00",
        guid_status="present",
        has_audio_url=True,
        seed_source="rss",
        selector="latest",
        warning_count=0,
        warnings=[],
        not_investment_advice=True,
    )
    row = CorpusEpisodeIntakeRunRow(
        podcast_id="gooaye",
        selector="latest",
        episode_ref="EP677",
        title="EP677 Alpha",
        published_at="Thu, 09 Jul 2026 00:00:00 GMT",
        duration="00:42:00",
        guid_status="present",
        has_audio_url=True,
        outcome_status="selected",
        reason="episode resolved from configured feed",
        planned_reads=["configured podcast RSS feed"],
        planned_writes=[
            str(tmp_path / "corpus" / "gooaye" / "episode-seeds" / "EP677.episode-seed.json")
        ],
        seed_json_path=str(
            tmp_path / "corpus" / "gooaye" / "episode-seeds" / "EP677.episode-seed.json"
        ),
        warnings=[],
    )
    result = CorpusEpisodeIntakeRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        selector="latest",
        resolved_episode_ref="EP677",
        report_json_path=None,
        report_markdown_path=None,
        filters=filters,
        counts=counts,
        rows=[row],
        warnings=[warning],
        not_investment_advice=True,
    )

    assert asdict(seed)["has_audio_url"] is True
    assert asdict(result)["counts"]["selected_count"] == 1
    assert result.report_json_path is None
    assert callable(run_corpus_episode_intake)


def test_corpus_episode_intake_error_contract():
    from podcast_ingest_core import (
        CorpusEpisodeIntakeFailedError,
        PodcastIngestCoreError,
    )

    assert issubclass(CorpusEpisodeIntakeFailedError, PodcastIngestCoreError)


def test_dry_run_latest_resolution_writes_no_seed_or_report(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from podcast_ingest_core.storage import (
        corpus_episode_intake_run_asset_paths,
        corpus_episode_seed_asset_path,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[tuple[str, str]] = []

    def fake_get_episode(podcast_id: str, episode_ref: str):
        calls.append((podcast_id, episode_ref))
        return _episode()

    monkeypatch.setattr(runner, "get_episode", fake_get_episode, raising=False)

    result = run_corpus_episode_intake("gooaye")

    seed_path = corpus_episode_seed_asset_path("gooaye", "EP677")
    report_paths = corpus_episode_intake_run_asset_paths("gooaye")
    assert calls == [("gooaye", "latest")]
    assert result.run_mode == "dry_run"
    assert result.resolved_episode_ref == "EP677"
    assert result.counts.selected_count == 1
    assert result.rows[0].outcome_status == "selected"
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert not seed_path.exists()
    assert not report_paths.json_path.exists()
    assert not report_paths.markdown_path.exists()


def test_dry_run_explicit_episode_resolution(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: calls.append(episode_ref) or _episode("EP677"),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", episode_ref="EP677")

    assert calls == ["EP677"]
    assert result.selector == "EP677"
    assert result.filters.episode_ref == "EP677"
    assert result.rows[0].episode_ref == "EP677"


def test_dry_run_blank_selector_defaults_to_latest(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: calls.append(episode_ref) or _episode("EP677"),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", episode_ref="   ")

    assert calls == ["latest"]
    assert result.selector == "latest"
    assert result.resolved_episode_ref == "EP677"


def test_dry_run_unresolved_selector_is_rejected_without_writes(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from podcast_ingest_core.errors import EpisodeNotFoundError
    from podcast_ingest_core.storage import (
        corpus_episode_intake_run_asset_paths,
        corpus_episode_seed_asset_path,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    def fake_get_episode(podcast_id: str, episode_ref: str):
        raise EpisodeNotFoundError(
            "missing https://source.example.invalid/episode?token=secret"
        )

    monkeypatch.setattr(runner, "get_episode", fake_get_episode, raising=False)

    result = run_corpus_episode_intake("gooaye", episode_ref="EP999")

    report_paths = corpus_episode_intake_run_asset_paths("gooaye")
    assert result.resolved_episode_ref is None
    assert result.counts.rejected_count == 1
    assert result.rows[0].outcome_status == "rejected"
    assert not corpus_episode_seed_asset_path("gooaye", "EP999").exists()
    assert not report_paths.json_path.exists()
    assert "https://" not in json.dumps(_payload(result), ensure_ascii=False)
    assert "token=secret" not in json.dumps(_payload(result), ensure_ascii=False)


def test_dry_run_does_not_call_side_effect_boundaries(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    def forbidden(name):
        def fail(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"dry-run must not call {name}")

        return fail

    for name in (
        "download_audio",
        "transcribe_episode",
        "run_corpus_remediation",
        "rebuild_cache",
    ):
        monkeypatch.setattr(runner, name, forbidden(name), raising=False)

    result = run_corpus_episode_intake("gooaye")
    source = inspect.getsource(runner)

    assert result.counts.selected_count == 1
    assert calls == []
    for forbidden_text in ("dotenv", "os.environ", "import mcp", "from mcp"):
        assert forbidden_text not in source.lower()


def test_dry_run_is_deterministic_and_has_no_generated_at(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    first = _payload(run_corpus_episode_intake("gooaye"))
    second = _payload(run_corpus_episode_intake("gooaye"))
    text = json.dumps(first, ensure_ascii=False, sort_keys=True)

    assert first == second
    assert first["resolved_episode_ref"] == "EP677"
    assert "generated_at" not in text
    assert "https://" not in text
    assert "raw description must not leak" not in text


def test_run_corpus_episode_intake_cli_dry_run_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import (
        CorpusEpisodeIntakeFilter,
        CorpusEpisodeIntakeOutcomeCounts,
        CorpusEpisodeIntakeRunResult,
    )
    from scripts import run_corpus_episode_intake as cli

    result = CorpusEpisodeIntakeRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        selector="latest",
        resolved_episode_ref="EP677",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusEpisodeIntakeFilter("latest"),
        counts=CorpusEpisodeIntakeOutcomeCounts(
            row_count=1,
            selected_count=1,
            seeded_count=0,
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
    captured = {}

    def fake_run(podcast_id: str, **kwargs):
        captured["podcast_id"] = podcast_id
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr(cli, "run_corpus_episode_intake", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_corpus_episode_intake.py", "--podcast", "gooaye"])

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["podcast_id"] == "gooaye"
    assert captured["kwargs"] == {"episode_ref": "latest", "confirm": False}
    assert payload["run_mode"] == "dry_run"
    assert payload["resolved_episode_ref"] == "EP677"
    assert payload["report_json_path"] is None
    assert payload["selected_count"] == 1


def test_confirmed_run_writes_deterministic_seed_metadata_and_report(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from podcast_ingest_core.storage import (
        corpus_episode_intake_run_asset_paths,
        corpus_episode_seed_asset_path,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", confirm=True)

    seed_path = corpus_episode_seed_asset_path("gooaye", "EP677")
    report_paths = corpus_episode_intake_run_asset_paths("gooaye")
    seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    report_payload = json.loads(report_paths.json_path.read_text(encoding="utf-8"))
    markdown = report_paths.markdown_path.read_text(encoding="utf-8")
    serialized = json.dumps(report_payload, ensure_ascii=False, sort_keys=True)

    assert result.run_mode == "confirmed"
    assert result.counts.seeded_count == 1
    assert result.report_json_path == report_paths.json_path
    assert result.report_markdown_path == report_paths.markdown_path
    assert seed_payload == {
        "duration": "00:42:00",
        "episode_ref": "EP677",
        "guid_status": "present",
        "has_audio_url": True,
        "not_investment_advice": True,
        "podcast_id": "gooaye",
        "published_at": "Thu, 09 Jul 2026 00:00:00 GMT",
        "seed_source": "rss",
        "selector": "latest",
        "title": "EP677 Alpha",
        "warning_count": 0,
        "warnings": [],
    }
    assert report_payload["seeded_count"] == 1
    assert "Corpus Episode Intake Run - gooaye" in markdown
    assert "generated_at" not in serialized
    assert "https://" not in serialized
    assert "token=secret" not in serialized
    assert "raw description must not leak" not in serialized


def test_repeated_confirmed_run_records_reused_without_duplicate_seed(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from podcast_ingest_core.storage import corpus_episode_seed_asset_path

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    first = run_corpus_episode_intake("gooaye", confirm=True)
    second = run_corpus_episode_intake("gooaye", confirm=True)
    seed_path = corpus_episode_seed_asset_path("gooaye", "EP677")

    assert first.counts.seeded_count == 1
    assert second.counts.reused_count == 1
    assert second.counts.seeded_count == 0
    assert list(seed_path.parent.glob("*.episode-seed.json")) == [seed_path]


def test_confirmed_unresolved_selector_writes_rejected_report_without_seed(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from podcast_ingest_core.errors import EpisodeNotFoundError
    from podcast_ingest_core.storage import (
        corpus_episode_intake_run_asset_paths,
        corpus_episode_seed_asset_path,
    )

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: (_ for _ in ()).throw(
            EpisodeNotFoundError("missing https://example.invalid?token=secret")
        ),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", episode_ref="EP999", confirm=True)

    report_paths = corpus_episode_intake_run_asset_paths("gooaye")
    report_payload = json.loads(report_paths.json_path.read_text(encoding="utf-8"))
    assert result.counts.rejected_count == 1
    assert result.report_json_path == report_paths.json_path
    assert report_payload["rejected_count"] == 1
    assert not corpus_episode_seed_asset_path("gooaye", "EP999").exists()
    assert "https://" not in json.dumps(report_payload, ensure_ascii=False)


def test_confirmed_intake_does_not_call_downstream_side_effects(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    def forbidden(name):
        def fail(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"confirmed intake must not call {name}")

        return fail

    for name in (
        "download_audio",
        "transcribe_episode",
        "run_corpus_remediation",
        "rebuild_cache",
    ):
        monkeypatch.setattr(runner, name, forbidden(name), raising=False)

    result = run_corpus_episode_intake("gooaye", confirm=True)

    assert calls == []
    assert result.counts.seeded_count == 1


def test_run_corpus_episode_intake_cli_confirmed_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import (
        CorpusEpisodeIntakeFilter,
        CorpusEpisodeIntakeOutcomeCounts,
        CorpusEpisodeIntakeRunResult,
    )
    from scripts import run_corpus_episode_intake as cli

    result = CorpusEpisodeIntakeRunResult(
        podcast_id="gooaye",
        run_mode="confirmed",
        confirm=True,
        selector="EP677",
        resolved_episode_ref="EP677",
        report_json_path=tmp_path / "corpus-episode-intake-run.json",
        report_markdown_path=tmp_path / "corpus-episode-intake-run.md",
        filters=CorpusEpisodeIntakeFilter("EP677"),
        counts=CorpusEpisodeIntakeOutcomeCounts(
            row_count=1,
            selected_count=0,
            seeded_count=1,
            reused_count=0,
            failed_count=0,
            skipped_count=0,
            rejected_count=0,
            warning_count=1,
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

    monkeypatch.setattr(cli, "run_corpus_episode_intake", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_corpus_episode_intake.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP677",
            "--confirm",
        ],
    )

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["kwargs"] == {"episode_ref": "EP677", "confirm": True}
    assert payload["run_mode"] == "confirmed"
    assert payload["seeded_count"] == 1
    assert payload["report_json_path"].endswith("corpus-episode-intake-run.json")


def test_no_unsafe_feed_content_leaks(
    monkeypatch, capsys, tmp_path
):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core import CorpusEpisodeIntakeFailedError
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake
    from scripts import run_corpus_episode_intake as cli

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    malicious_episode = _episode(
        "EP677",
        title=(
            "EP677 https://source.example.invalid/path?token=secret "
            "prompt text raw LLM output Traceback secret"
        ),
        source_url="https://source.example.invalid/episode?token=secret",
        audio_url="https://media.example.invalid/audio.mp3?token=secret",
        description="raw description must not leak prompt text raw LLM output",
    )
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: malicious_episode,
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", confirm=True)
    cli_payload = runner.result_to_dict(result)
    print(json.dumps(cli_payload, ensure_ascii=False))
    captured = capsys.readouterr()
    output_text = "\n".join(
        [
            json.dumps(cli_payload, ensure_ascii=False, sort_keys=True),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
            Path(result.rows[0].seed_json_path).read_text(encoding="utf-8"),
            captured.out,
            captured.err,
        ]
    ).lower()

    for forbidden in (
        "https://",
        "?token",
        "token=secret",
        "raw description must not leak",
        "prompt text",
        "raw llm output",
        "traceback",
        "secret",
    ):
        assert forbidden not in output_text

    def fake_run(*args, **kwargs):
        raise CorpusEpisodeIntakeFailedError(
            "failed https://source.example.invalid?token=secret"
        )

    monkeypatch.setattr(cli, "run_corpus_episode_intake", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_corpus_episode_intake.py", "--podcast", "gooaye"])

    assert cli.main() == 1
    stderr = capsys.readouterr().err.lower()
    assert "https://" not in stderr
    assert "token=secret" not in stderr


def test_feed_reader_dependency_failure_is_bounded(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    def fake_get_episode(podcast_id: str, episode_ref: str):
        raise RuntimeError(
            "Traceback body https://source.example.invalid/path?token=secret prompt text"
        )

    monkeypatch.setattr(runner, "get_episode", fake_get_episode, raising=False)

    result = run_corpus_episode_intake("gooaye", confirm=True)
    text = json.dumps(runner.result_to_dict(result), ensure_ascii=False).lower()

    assert result.counts.failed_count == 1
    assert result.report_json_path is not None
    assert result.report_json_path.exists()
    assert "runtimeerror" in result.rows[0].reason.lower()
    assert "https://" not in text
    assert "token=secret" not in text
    assert "traceback body" not in text


def test_episode_intake_boundary_source_has_no_side_effect_imports():
    import podcast_ingest_core.corpus_episode_intake as runner

    source = inspect.getsource(runner).lower()

    for forbidden in (
        "download_audio(",
        "transcribe_episode(",
        "run_corpus_remediation(",
        "rebuild_cache(",
        "semantic_summarize",
        "stock_lens",
        "synthesis",
        "dotenv",
        "os.environ",
        "import mcp",
        "from mcp",
    ):
        assert forbidden not in source


def test_no_investment_advice_or_market_claims(monkeypatch, tmp_path):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode(
            "EP677",
            title="EP677 buy recommendation target price guaranteed return",
        ),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", confirm=True)
    text = "\n".join(
        [
            json.dumps(runner.result_to_dict(result), ensure_ascii=False),
            result.report_markdown_path.read_text(encoding="utf-8"),
            Path(result.rows[0].seed_json_path).read_text(encoding="utf-8"),
        ]
    ).lower()

    assert result.not_investment_advice is True
    assert "not investment advice" in text
    assert "buy recommendation" not in text
    assert "target price" not in text
    assert "guaranteed return" not in text


def test_confirmed_seed_adds_manual_follow_up_warning_without_running_chain(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.corpus_episode_intake as runner
    from podcast_ingest_core.corpus_episode_intake import run_corpus_episode_intake

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "get_episode",
        lambda podcast_id, episode_ref: _episode("EP677"),
        raising=False,
    )

    result = run_corpus_episode_intake("gooaye", confirm=True)
    warning_text = " ".join(warning.message for warning in result.warnings).lower()

    assert result.counts.warning_count == 1
    assert "manual follow-up" in warning_text
    assert "cache rebuild remain manual" in warning_text
