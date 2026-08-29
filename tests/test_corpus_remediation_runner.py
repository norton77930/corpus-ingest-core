from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> None:
    from corpus_ingest_core import storage
    import corpus_ingest_core.corpus_index as corpus_index

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


def _write_transcript_fixture(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from corpus_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("raw transcript sentinel must not leak", encoding="utf-8")
    paths.srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\ntext\n", encoding="utf-8")
    _write_json(
        paths.json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "language": "zh",
            "segment_count": 1,
            "last_segment_end_seconds": 1.0,
            "segments": [
                {
                    "id": 1,
                    "start": 0.0,
                    "end": 1.0,
                    "text": "raw transcript sentinel must not leak",
                }
            ],
        },
    )
    return paths.json_path


def _plan_payload(actions: list[dict], *, podcast_id: str = "gooaye") -> dict:
    episodes: dict[str, dict] = {}
    for action in actions:
        episode_ref = action["episode_ref"]
        row = episodes.setdefault(
            episode_ref,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": action.get("title", episode_ref),
                "artifact_status": _artifact_status_for_episode(episode_ref),
                "missing_artifacts": [],
                "blockers": [],
                "warnings": [],
                "actions": [],
            },
        )
        row["actions"].append(
            {
                "action_id": f"{episode_ref}:{action['artifact_family']}",
                "artifact_family": action["artifact_family"],
                "action_type": action.get("action_type", "generate"),
                "status": action.get("status", "ready"),
                "order": action.get("order", _family_order(action["artifact_family"])),
                "reason": action.get("reason", f"{action['artifact_family']} artifact is missing"),
                "blocking_artifacts": action.get("blocking_artifacts", []),
                "suggested_command": action.get("suggested_command", "python scripts/placeholder.py"),
                "manual_only": True,
                "optional": action.get("optional", False),
                "gated": action.get("gated", False),
                "requires_api_cost_ack": action.get("requires_api_cost_ack", False),
            }
        )
    return {
        "podcast_id": podcast_id,
        "plan_mode": "deterministic-corpus-remediation-plan-v1",
        "source_scope": "refreshed-local-corpus-index-only",
        "source_corpus_index_json_path": f"data/corpus/{podcast_id}/corpus-index.json",
        "source_corpus_index_markdown_path": f"data/corpus/{podcast_id}/corpus-index.md",
        "episode_count": len(episodes),
        "action_count": len(actions),
        "blocked_action_count": sum(action.get("status") == "blocked" for action in actions),
        "optional_action_count": sum(action.get("optional", False) for action in actions),
        "gated_action_count": sum(action.get("gated", False) for action in actions),
        "warning_count": 0,
        "episodes": [episodes[key] for key in sorted(episodes)],
        "not_investment_advice": True,
    }


def _artifact_status_for_episode(episode_ref: str) -> dict:
    base = f"data"
    return {
        "audio": {"status": "available", "paths": {"audio": f"{base}/audio/gooaye/{episode_ref}.mp3"}},
        "transcript": {
            "status": "valid",
            "paths": {
                "json": f"{base}/transcripts/gooaye/{episode_ref}__Alpha.json",
                "text": f"{base}/transcripts/gooaye/{episode_ref}__Alpha.txt",
                "srt": f"{base}/transcripts/gooaye/{episode_ref}__Alpha.srt",
            },
        },
        "extractive_summary": {"status": "missing", "paths": {}},
        "mentions": {"status": "missing", "paths": {}},
        "semantic_summary": {"status": "missing", "paths": {}},
        "semantic_review": {"status": "missing", "paths": {}},
        "episode_intelligence": {"status": "missing", "paths": {}},
        "industry_mapping": {"status": "missing", "paths": {}},
        "external_boundary": {"status": "missing", "paths": {}},
    }


def _family_order(family: str) -> int:
    order = {
        "audio": 1,
        "transcript": 2,
        "extractive_summary": 3,
        "mentions": 4,
        "semantic_summary": 5,
        "semantic_review": 6,
        "episode_intelligence": 7,
        "industry_mapping": 8,
        "external_boundary": 9,
    }
    return order.get(family, 99)


def _fake_plan_refresh(monkeypatch, tmp_path: Path, payload: dict, calls: list[str] | None = None):
    from corpus_ingest_core import storage
    from corpus_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )
    import corpus_ingest_core.corpus_remediation_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    def fake_generate(podcast_id: str) -> CorpusRemediationPlanResult:
        if calls is not None:
            calls.append(f"refresh:{podcast_id}")
        paths = storage.corpus_remediation_plan_asset_paths(podcast_id)
        _write_json(paths.json_path, payload)
        paths.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        paths.markdown_path.write_text("# fake plan", encoding="utf-8")
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


def _rows_by_family(result) -> dict[str, list]:
    rows: dict[str, list] = {}
    for row in result.rows:
        rows.setdefault(row.artifact_family, []).append(row)
    return rows


def _asset(
    *,
    generated: bool = True,
    already_exists: bool = False,
    json_path: Path | None = None,
    markdown_path: Path | None = None,
    summary_path: Path | None = None,
):
    class Asset:
        pass

    asset = Asset()
    asset.generated = generated
    asset.already_exists = already_exists
    if json_path is not None:
        asset.json_path = json_path
    if markdown_path is not None:
        asset.markdown_path = markdown_path
    if summary_path is not None:
        asset.summary_path = summary_path
    asset.mentions_json_path = json_path
    asset.mentions_markdown_path = markdown_path
    asset.report_json_path = json_path
    asset.report_markdown_path = markdown_path
    asset.mapping_json_path = json_path
    asset.mapping_markdown_path = markdown_path
    asset.boundary_json_path = json_path
    asset.boundary_markdown_path = markdown_path
    return asset


def _install_successful_generators(monkeypatch, tmp_path: Path, calls: list[tuple[str, str, dict]]):
    import corpus_ingest_core.corpus_remediation_runner as runner

    def fake_generator(family: str):
        def generate(podcast_id: str, episode_ref: str, **kwargs):
            calls.append((family, episode_ref, kwargs))
            base = tmp_path / "generated" / family / episode_ref
            return _asset(
                generated=not kwargs.get("already_exists", False),
                already_exists=kwargs.get("already_exists", False),
                json_path=base.with_suffix(".json"),
                markdown_path=base.with_suffix(".md"),
                summary_path=base.with_suffix(".md"),
            )

        return generate

    monkeypatch.setattr(runner, "summarize_episode", fake_generator("extractive_summary"))
    monkeypatch.setattr(runner, "extract_mentions", fake_generator("mentions"))
    monkeypatch.setattr(
        runner,
        "generate_episode_intelligence_report",
        fake_generator("episode_intelligence"),
    )
    monkeypatch.setattr(
        runner,
        "generate_industry_chain_mapping",
        fake_generator("industry_mapping"),
    )
    monkeypatch.setattr(
        runner,
        "generate_external_data_boundary",
        fake_generator("external_boundary"),
    )


def test_preview_corpus_remediation_from_in_memory_plan(monkeypatch, tmp_path):
    from corpus_ingest_core import storage
    from corpus_ingest_core.models import (
        CorpusRemediationActionCounts,
        CorpusRemediationPlanResult,
    )
    import corpus_ingest_core.corpus_remediation_runner as runner

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    payload = _plan_payload(
        [
            {
                "episode_ref": "EP672",
                "title": "Alpha",
                "artifact_family": "extractive_summary",
            }
        ]
    )
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

    result = runner._preview_corpus_remediation_from_plan(
        "gooaye",
        plan_result=plan_result,
        plan_payload=payload,
        episode_ref="EP672",
        action_family=None,
        max_actions=None,
        source_persisted=False,
    )

    assert result.counts.selected_count == 1
    assert "in-memory corpus snapshot" in result.rows[0].planned_reads
    assert not paths.json_path.exists()
    assert not paths.markdown_path.exists()


def test_standalone_dry_run_still_refreshes_index_and_plan_without_stage_report(
    monkeypatch, tmp_path
):
    from corpus_ingest_core import storage
    import corpus_ingest_core.corpus_remediation_runner as runner

    _write_transcript_fixture(
        monkeypatch,
        tmp_path,
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Alpha",
    )

    def forbidden_execution(*args, **kwargs):
        pytest.fail("dry-run executed deterministic remediation")

    for name in (
        "summarize_episode",
        "extract_mentions",
        "generate_episode_intelligence_report",
        "generate_industry_chain_mapping",
        "generate_external_data_boundary",
    ):
        monkeypatch.setattr(runner, name, forbidden_execution)

    result = runner.run_corpus_remediation(
        "gooaye",
        episode_ref="EP672",
        confirm=False,
    )

    index_paths = storage.corpus_index_asset_paths("gooaye")
    plan_paths = storage.corpus_remediation_plan_asset_paths("gooaye")
    report_paths = storage.corpus_remediation_run_asset_paths("gooaye")
    assert result.counts.selected_count >= 1
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



def test_corpus_remediation_run_asset_paths_contract():
    from corpus_ingest_core.storage import corpus_remediation_run_asset_paths

    paths = corpus_remediation_run_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-remediation-run.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-remediation-run.md")


def test_corpus_remediation_runner_public_result_contract_exports(tmp_path):
    from corpus_ingest_core import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
        CorpusRemediationRunRow,
        CorpusRemediationRunWarning,
        CorpusRemediationRunnerFailedError,
        run_corpus_remediation,
    )

    filters = CorpusRemediationRunFilter(
        episode_ref="EP672",
        action_family="mentions",
        max_actions=1,
    )
    counts = CorpusRemediationRunCounts(
        row_count=1,
        selected_count=1,
        executed_count=0,
        reused_count=0,
        failed_count=0,
        skipped_count=0,
        blocked_count=0,
        excluded_count=0,
        warning_count=0,
    )
    warning = CorpusRemediationRunWarning(
        scope="run",
        episode_ref=None,
        artifact_family=None,
        message="cache metadata may be stale",
    )
    row = CorpusRemediationRunRow(
        action_id="EP672:mentions",
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Alpha",
        artifact_family="mentions",
        source_status="ready",
        outcome_status="selected",
        reason="ready deterministic action",
        planned_reads=["data/transcripts/gooaye/EP672__Alpha.json"],
        planned_writes=["data/mentions/gooaye/EP672__Alpha.mentions.json"],
        output_paths=[],
        warnings=[],
    )
    result = CorpusRemediationRunResult(
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

    assert asdict(result)["filters"]["action_family"] == "mentions"
    assert result.counts.selected_count == 1
    assert CorpusRemediationRunnerFailedError.__name__ == "CorpusRemediationRunnerFailedError"
    assert callable(run_corpus_remediation)


def test_corpus_remediation_runner_error_contract():
    from corpus_ingest_core import CorpusRemediationRunnerFailedError, PodcastIngestCoreError

    assert issubclass(CorpusRemediationRunnerFailedError, PodcastIngestCoreError)


def test_run_corpus_remediation_empty_corpus_dry_run_writes_no_report(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation
    from corpus_ingest_core.storage import corpus_remediation_run_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    result = run_corpus_remediation("gooaye")

    report_paths = corpus_remediation_run_asset_paths("gooaye")
    assert result.run_mode == "dry_run"
    assert result.counts.row_count == 0
    assert result.counts.selected_count == 0
    assert result.counts.executed_count == 0
    assert result.report_json_path is None
    assert result.report_markdown_path is None
    assert not report_paths.json_path.exists()
    assert not report_paths.markdown_path.exists()


def test_run_corpus_remediation_refreshes_plan_before_selection(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[str] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {
                    "episode_ref": "EP001",
                    "artifact_family": "mentions",
                    "status": "ready",
                }
            ]
        ),
        calls,
    )

    result = run_corpus_remediation("gooaye")

    assert calls == ["refresh:gooaye"]
    assert result.counts.selected_count == 1
    assert result.rows[0].action_id == "EP001:mentions"


def test_dry_run_selects_deterministic_and_excludes_non_deterministic(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "extractive_summary"},
                {"episode_ref": "EP001", "artifact_family": "mentions"},
                {"episode_ref": "EP001", "artifact_family": "episode_intelligence"},
                {"episode_ref": "EP001", "artifact_family": "industry_mapping"},
                {"episode_ref": "EP001", "artifact_family": "external_boundary"},
                {"episode_ref": "EP001", "artifact_family": "audio", "action_type": "download"},
                {"episode_ref": "EP001", "artifact_family": "transcript", "action_type": "transcribe"},
                {
                    "episode_ref": "EP001",
                    "artifact_family": "semantic_summary",
                    "optional": True,
                    "gated": True,
                    "requires_api_cost_ack": True,
                },
                {
                    "episode_ref": "EP001",
                    "artifact_family": "semantic_review",
                    "optional": True,
                },
                {"episode_ref": "EP001", "artifact_family": "stock_lens_report"},
            ]
        ),
    )

    result = run_corpus_remediation("gooaye")

    rows = _rows_by_family(result)
    assert result.counts.selected_count == 5
    assert result.counts.excluded_count == 5
    assert rows["extractive_summary"][0].outcome_status == "selected"
    assert rows["mentions"][0].outcome_status == "selected"
    assert rows["audio"][0].outcome_status == "excluded"
    assert rows["transcript"][0].outcome_status == "excluded"
    assert rows["semantic_summary"][0].outcome_status == "excluded"
    assert rows["semantic_review"][0].outcome_status == "excluded"
    assert rows["stock_lens_report"][0].outcome_status == "excluded"


def test_dry_run_keeps_blocked_and_skipped_rows_visible(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "extractive_summary"},
                {
                    "episode_ref": "EP001",
                    "artifact_family": "mentions",
                    "status": "blocked",
                    "blocking_artifacts": ["transcript"],
                },
                {"episode_ref": "EP001", "artifact_family": "episode_intelligence"},
            ]
        ),
    )

    result = run_corpus_remediation("gooaye", action_family="episode_intelligence")

    rows = _rows_by_family(result)
    assert rows["episode_intelligence"][0].outcome_status == "selected"
    assert rows["extractive_summary"][0].outcome_status == "skipped"
    assert rows["mentions"][0].outcome_status == "blocked"
    assert result.counts.selected_count == 1
    assert result.counts.skipped_count == 1
    assert result.counts.blocked_count == 1


def test_episode_filter_skips_other_episode_blocked_action(monkeypatch, tmp_path):
    """A different episode's blocked action must not leak past the episode filter.

    Regression for finding (a): the workflow's per-episode dry-run judgment was
    misled because another episode's blocked deterministic action was reported as
    ``blocked`` instead of ``skipped`` (the ``blocked`` short-circuit ran before the
    episode filter).
    """
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {
                    "episode_ref": "EP672",
                    "artifact_family": "mentions",
                    "status": "blocked",
                    "blocking_artifacts": ["transcript"],
                },
                {"episode_ref": "EP677", "artifact_family": "extractive_summary"},
            ]
        ),
    )

    result = run_corpus_remediation("gooaye", episode_ref="EP677")

    rows = _rows_by_family(result)
    assert rows["extractive_summary"][0].outcome_status == "selected"
    assert rows["extractive_summary"][0].episode_ref == "EP677"
    assert rows["mentions"][0].episode_ref == "EP672"
    assert rows["mentions"][0].outcome_status == "skipped"
    assert result.counts.blocked_count == 0
    assert result.counts.selected_count == 1


def test_dry_run_is_deterministic_and_has_no_generated_at(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    payload = _plan_payload(
        [
            {"episode_ref": "EP002", "artifact_family": "mentions"},
            {"episode_ref": "EP001", "artifact_family": "extractive_summary"},
        ]
    )
    _fake_plan_refresh(monkeypatch, tmp_path, payload)

    first = _result_payload(run_corpus_remediation("gooaye"))
    second = _result_payload(run_corpus_remediation("gooaye"))
    text = json.dumps(first, ensure_ascii=False, sort_keys=True)

    assert first == second
    assert "generated_at" not in text


def test_run_corpus_remediation_cli_dry_run_outputs_json(monkeypatch, capsys, tmp_path):
    from corpus_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
    )
    from scripts import run_corpus_remediation as cli

    result = CorpusRemediationRunResult(
        podcast_id="gooaye",
        run_mode="dry_run",
        confirm=False,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=None,
        report_markdown_path=None,
        filters=CorpusRemediationRunFilter(None, None, None),
        counts=CorpusRemediationRunCounts(
            row_count=2,
            selected_count=1,
            executed_count=0,
            reused_count=0,
            failed_count=0,
            skipped_count=1,
            blocked_count=0,
            excluded_count=0,
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

    monkeypatch.setattr(cli, "run_corpus_remediation", fake_run)
    monkeypatch.setattr(sys, "argv", ["run_corpus_remediation.py", "--podcast", "gooaye"])

    exit_code = cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["podcast_id"] == "gooaye"
    assert captured["kwargs"]["confirm"] is False
    assert payload["run_mode"] == "dry_run"
    assert payload["report_json_path"] is None
    assert payload["selected_count"] == 1
    assert payload["skipped_count"] == 1


def test_confirmed_execution_rejects_missing_filter(monkeypatch, tmp_path):
    from corpus_ingest_core import CorpusRemediationRunnerFailedError
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([{"episode_ref": "EP001", "artifact_family": "mentions"}]),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    with pytest.raises(CorpusRemediationRunnerFailedError, match="episode or action_family"):
        run_corpus_remediation("gooaye", confirm=True)

    assert calls == []


def test_confirmed_action_family_filter_and_max_actions_ordering(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP002", "artifact_family": "mentions"},
                {"episode_ref": "EP001", "artifact_family": "mentions"},
                {"episode_ref": "EP001", "artifact_family": "extractive_summary"},
            ]
        ),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation(
        "gooaye",
        confirm=True,
        action_family="mentions",
        max_actions=1,
    )

    assert [(family, episode_ref) for family, episode_ref, _ in calls] == [
        ("mentions", "EP001")
    ]
    assert result.counts.selected_count == 1
    assert result.counts.executed_count == 1
    assert result.counts.skipped_count == 2
    assert result.report_json_path is not None
    assert result.report_json_path.exists()


def test_confirmed_episode_filter_executes_only_matching_ready_actions(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "mentions"},
                {"episode_ref": "EP002", "artifact_family": "mentions"},
            ]
        ),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation("gooaye", confirm=True, episode_ref="EP002")

    assert [(family, episode_ref) for family, episode_ref, _ in calls] == [
        ("mentions", "EP002")
    ]
    assert result.counts.selected_count == 1
    assert result.counts.executed_count == 1
    assert _rows_by_family(result)["mentions"][0].outcome_status == "skipped"


def test_confirmed_run_report_json_and_markdown_are_written(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([{"episode_ref": "EP001", "artifact_family": "mentions"}]),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation("gooaye", confirm=True, action_family="mentions")

    assert result.report_json_path is not None
    assert result.report_markdown_path is not None
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    markdown = result.report_markdown_path.read_text(encoding="utf-8")
    assert payload["run_mode"] == "confirmed"
    assert payload["confirm"] is True
    assert payload["executed_count"] == 1
    assert "generated_at" not in result.report_json_path.read_text(encoding="utf-8")
    assert "Corpus Remediation Run - gooaye" in markdown
    assert "not investment advice" in markdown.lower()


def test_confirmed_execution_calls_core_functions_directly_without_shelling_out(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([{"episode_ref": "EP001", "artifact_family": "extractive_summary"}]),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    def forbidden_shell(*args, **kwargs):
        raise AssertionError("runner must not shell out")

    monkeypatch.setattr(subprocess, "run", forbidden_shell)
    monkeypatch.setattr(subprocess, "Popen", forbidden_shell)

    result = run_corpus_remediation(
        "gooaye",
        confirm=True,
        action_family="extractive_summary",
    )

    source = Path("src/corpus_ingest_core/corpus_remediation_runner.py").read_text(
        encoding="utf-8"
    )
    assert "subprocess" not in source
    assert calls[0][0] == "extractive_summary"
    assert result.counts.executed_count == 1


def test_confirmed_execution_propagates_force_and_allow_partial(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    calls: list[tuple[str, str, dict]] = []
    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "extractive_summary"},
                {"episode_ref": "EP001", "artifact_family": "mentions"},
                {"episode_ref": "EP001", "artifact_family": "episode_intelligence"},
                {"episode_ref": "EP001", "artifact_family": "industry_mapping"},
                {"episode_ref": "EP001", "artifact_family": "external_boundary"},
            ]
        ),
    )
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation(
        "gooaye",
        confirm=True,
        episode_ref="EP001",
        force=True,
        allow_partial=True,
    )

    assert result.counts.executed_count == 5
    assert {family for family, _episode_ref, _kwargs in calls} == {
        "extractive_summary",
        "mentions",
        "episode_intelligence",
        "industry_mapping",
        "external_boundary",
    }
    assert all(kwargs["force"] is True for _family, _episode_ref, kwargs in calls)
    assert all(kwargs["allow_partial"] is True for _family, _episode_ref, kwargs in calls)


def test_run_corpus_remediation_cli_confirmed_stdout_and_error_contract(
    monkeypatch, capsys, tmp_path
):
    from corpus_ingest_core import CorpusRemediationRunnerFailedError
    from corpus_ingest_core.models import (
        CorpusRemediationRunCounts,
        CorpusRemediationRunFilter,
        CorpusRemediationRunResult,
    )
    from scripts import run_corpus_remediation as cli

    result = CorpusRemediationRunResult(
        podcast_id="gooaye",
        run_mode="confirmed",
        confirm=True,
        source_remediation_plan_json_path=tmp_path / "corpus-remediation-plan.json",
        source_remediation_plan_markdown_path=tmp_path / "corpus-remediation-plan.md",
        report_json_path=tmp_path / "corpus-remediation-run.json",
        report_markdown_path=tmp_path / "corpus-remediation-run.md",
        filters=CorpusRemediationRunFilter(None, "mentions", None),
        counts=CorpusRemediationRunCounts(
            row_count=1,
            selected_count=1,
            executed_count=1,
            reused_count=0,
            failed_count=0,
            skipped_count=0,
            blocked_count=0,
            excluded_count=0,
            warning_count=0,
        ),
        rows=[],
        warnings=[],
        not_investment_advice=True,
    )

    def fake_run(podcast_id: str, **kwargs):
        assert kwargs["confirm"] is True
        assert kwargs["action_family"] == "mentions"
        assert kwargs["force"] is True
        assert kwargs["allow_partial"] is True
        return result

    monkeypatch.setattr(cli, "run_corpus_remediation", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_corpus_remediation.py",
            "--podcast",
            "gooaye",
            "--action-family",
            "mentions",
            "--confirm",
            "--force",
            "--allow-partial",
        ],
    )

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run_mode"] == "confirmed"
    assert payload["report_json_path"] == str(tmp_path / "corpus-remediation-run.json")
    assert payload["executed_count"] == 1

    def rejected(*args, **kwargs):
        raise CorpusRemediationRunnerFailedError("confirm requires episode or action_family")

    monkeypatch.setattr(cli, "run_corpus_remediation", rejected)
    assert cli.main(["--podcast", "gooaye", "--confirm"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "confirm requires episode or action_family" in captured.err


def test_single_action_failure_records_failure_and_continues_unrelated(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.corpus_remediation_runner as runner
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "mentions"},
                {"episode_ref": "EP002", "artifact_family": "mentions"},
            ]
        ),
    )
    calls: list[str] = []

    def fake_mentions(podcast_id: str, episode_ref: str, **kwargs):
        calls.append(episode_ref)
        if episode_ref == "EP001":
            raise RuntimeError("raw transcript sentinel must not leak")
        return _asset(
            generated=True,
            json_path=tmp_path / f"{episode_ref}.mentions.json",
            markdown_path=tmp_path / f"{episode_ref}.mentions.md",
        )

    monkeypatch.setattr(runner, "extract_mentions", fake_mentions)

    result = run_corpus_remediation("gooaye", confirm=True, action_family="mentions")

    statuses = {row.episode_ref: row.outcome_status for row in result.rows}
    assert calls == ["EP001", "EP002"]
    assert statuses["EP001"] == "failed"
    assert statuses["EP002"] == "executed"
    assert result.counts.failed_count == 1
    assert result.counts.executed_count == 1
    assert "raw transcript sentinel" not in json.dumps(_result_payload(result))


def test_failed_dependency_skips_same_run_downstream_actions(monkeypatch, tmp_path):
    import corpus_ingest_core.corpus_remediation_runner as runner
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "episode_intelligence"},
                {"episode_ref": "EP001", "artifact_family": "industry_mapping"},
                {"episode_ref": "EP001", "artifact_family": "external_boundary"},
            ]
        ),
    )

    def fail_report(*args, **kwargs):
        raise RuntimeError("report failed")

    monkeypatch.setattr(runner, "generate_episode_intelligence_report", fail_report)

    result = run_corpus_remediation("gooaye", confirm=True, episode_ref="EP001")

    rows = {row.artifact_family: row for row in result.rows}
    assert rows["episode_intelligence"].outcome_status == "failed"
    assert rows["industry_mapping"].outcome_status == "skipped"
    assert rows["external_boundary"].outcome_status == "skipped"
    assert "failed dependency" in rows["industry_mapping"].reason
    assert result.counts.failed_count == 1
    assert result.counts.skipped_count == 2


def test_outputs_do_not_leak_raw_or_secret_text(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    payload = _plan_payload([{"episode_ref": "EP001", "artifact_family": "mentions"}])
    payload["episodes"][0]["artifact_status"]["transcript"]["body"] = (
        "raw transcript sentinel must not leak"
    )
    payload["episodes"][0]["artifact_status"]["mentions"]["evidence"] = [
        "evidence sentinel must not leak"
    ]
    payload["episodes"][0]["artifact_status"]["semantic_summary"]["body"] = (
        "semantic body sentinel must not leak"
    )
    payload["episodes"][0]["warnings"] = [
        {
            "scope": "episode",
            "episode_ref": "EP001",
            "artifact_family": "mentions",
            "message": "API_KEY=secret-value must not leak",
        }
    ]
    _fake_plan_refresh(monkeypatch, tmp_path, payload)
    calls: list[tuple[str, str, dict]] = []
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation("gooaye", confirm=True, action_family="mentions")

    assert result.report_json_path is not None
    combined = "\n".join(
        [
            json.dumps(_result_payload(result), ensure_ascii=False),
            result.report_json_path.read_text(encoding="utf-8"),
            result.report_markdown_path.read_text(encoding="utf-8"),
        ]
    )
    forbidden = [
        "raw transcript sentinel",
        "evidence sentinel",
        "semantic body sentinel",
        "API_KEY=secret-value",
        "raw LLM output sentinel",
        "prompt text sentinel",
    ]
    for text in forbidden:
        assert text not in combined


def test_boundary_guard_excludes_forbidden_families_without_execution(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload(
            [
                {"episode_ref": "EP001", "artifact_family": "audio", "action_type": "download"},
                {"episode_ref": "EP001", "artifact_family": "transcript", "action_type": "transcribe"},
                {
                    "episode_ref": "EP001",
                    "artifact_family": "semantic_summary",
                    "optional": True,
                    "gated": True,
                    "requires_api_cost_ack": True,
                },
                {"episode_ref": "EP001", "artifact_family": "semantic_review", "optional": True},
                {"episode_ref": "EP001", "artifact_family": "stock_lens_synthesis"},
            ]
        ),
    )

    result = run_corpus_remediation("gooaye", confirm=True, action_family="audio")

    assert result.counts.selected_count == 0
    assert result.counts.executed_count == 0
    assert result.counts.excluded_count == 5
    source = Path("src/corpus_ingest_core/corpus_remediation_runner.py").read_text(
        encoding="utf-8"
    )
    forbidden_fragments = [
        "from .cache import",
        "from .downloader import",
        "from .feed_reader import",
        "from .llm_profiles import",
        "from .local_env import",
        "from .mcp_server import",
        "from .semantic_summarizer import",
        "from .stock_lens import",
        "from .stock_lens_synthesis import",
        "from .transcriber import",
        "requests",
        "urllib",
        "httpx",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_outputs_keep_no_investment_advice_boundary(monkeypatch, tmp_path):
    from corpus_ingest_core.corpus_remediation_runner import run_corpus_remediation

    _fake_plan_refresh(
        monkeypatch,
        tmp_path,
        _plan_payload([{"episode_ref": "EP001", "artifact_family": "external_boundary"}]),
    )
    calls: list[tuple[str, str, dict]] = []
    _install_successful_generators(monkeypatch, tmp_path, calls)

    result = run_corpus_remediation(
        "gooaye",
        confirm=True,
        action_family="external_boundary",
    )

    assert result.not_investment_advice is True
    assert result.report_markdown_path is not None
    combined = json.dumps(_result_payload(result), ensure_ascii=False).lower()
    combined += result.report_markdown_path.read_text(encoding="utf-8").lower()
    assert "not investment advice" in combined
    for forbidden in ("buy recommendation", "sell recommendation", "target price", "guaranteed return"):
        assert forbidden not in combined
