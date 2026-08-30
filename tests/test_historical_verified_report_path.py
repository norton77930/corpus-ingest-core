"""Core contracts for SPEC 023 historical verified-report path suggestion."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_suggest_is_zero_write_on_tmp_tree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """FR-006: suggest must not create/modify/delete files under the data root."""
    from corpus_ingest_core import storage, suggest_historical_verified_report_next_step

    reports = tmp_path / "research-reports"
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", reports)
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus)
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    monkeypatch.setattr(
        "corpus_ingest_core.corpus_index.SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
    )

    before = {p: p.stat().st_mtime_ns for p in tmp_path.rglob("*") if p.is_file()}
    before_names = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))

    result = suggest_historical_verified_report_next_step("gooaye", "EP999")

    after = {p: p.stat().st_mtime_ns for p in tmp_path.rglob("*") if p.is_file()}
    after_names = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    assert after_names == before_names
    assert after == before
    assert result.suggestion in {
        "report_present",
        "publish_verified_report",
        "completion_action",
        "blocked",
    }
    assert result.not_investment_advice is True


def test_suggest_rejects_reserved_selectors() -> None:
    from corpus_ingest_core import (
        HistoricalVerifiedReportPathInputError,
        suggest_historical_verified_report_next_step,
    )

    with pytest.raises(HistoricalVerifiedReportPathInputError):
        suggest_historical_verified_report_next_step("gooaye", "latest")
    with pytest.raises(HistoricalVerifiedReportPathInputError):
        suggest_historical_verified_report_next_step("gooaye", "NEXT")


def test_suggest_report_present_when_eligible_bundle_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from corpus_ingest_core import (
        suggest_historical_verified_report_next_step,
    )
    from corpus_ingest_core.models import VerifiedResearchReportCatalogItem

    digests = ["a" * 64]
    item = VerifiedResearchReportCatalogItem(
        podcast_id="gooaye",
        episode_ref="EP1",
        report_version=f"v1-{digests[0]}",
        source_digest=digests[0],
        schema_version="latest-episode-verified-research-report-v1",
        include_fixture_verification=False,
        stock_query_present=False,
        semantic_review_status="passed",
        not_investment_advice=True,
    )
    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.discover_eligible_report_summaries",
        lambda **kwargs: ([item], "available", "complete"),
    )
    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.run_episode_verified_research_report_workflow",
        lambda *a, **k: pytest.fail("must not preview publish when bundle present"),
    )

    result = suggest_historical_verified_report_next_step("gooaye", "EP1")
    assert result.suggestion == "report_present"
    assert result.has_bundle is True
    assert result.source_digests == digests
    assert result.recommended_mcp_tool is None


def test_suggest_publish_when_019_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    from corpus_ingest_core import suggest_historical_verified_report_next_step
    from corpus_ingest_core.models import EpisodeVerifiedResearchReportWorkflowRunResult

    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.discover_eligible_report_summaries",
        lambda **kwargs: ([], "missing", "complete"),
    )

    def fake_019(podcast_id, episode_ref, *, confirm=False, **kwargs):
        assert confirm is False
        return EpisodeVerifiedResearchReportWorkflowRunResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            outcome="ready",
            ready=True,
            missing_roles=[],
            stale_roles=[],
            failed_gates=[],
            report_version=None,
            source_digest=None,
            bundle_dir=None,
            report_json_path=None,
            report_markdown_path=None,
            manifest_path=None,
            stock_query=None,
            include_fixture_verification=False,
            warnings=[],
            not_investment_advice=True,
        )

    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.run_episode_verified_research_report_workflow",
        fake_019,
    )
    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.run_corpus_episode_completion_workflow",
        lambda *a, **k: pytest.fail("must not call 016 when publish-ready"),
    )

    result = suggest_historical_verified_report_next_step("gooaye", "EP2")
    assert result.suggestion == "publish_verified_report"
    assert result.publish_ready is True
    assert result.recommended_mcp_tool == "run_episode_verified_research_report_workflow"
    assert result.requires_api_cost_ack is False


def test_suggest_completion_action_when_not_publish_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from corpus_ingest_core import suggest_historical_verified_report_next_step
    from corpus_ingest_core.models import (
        CorpusEpisodeCompletionWorkflowRunCounts,
        CorpusEpisodeCompletionWorkflowRunFilter,
        CorpusEpisodeCompletionWorkflowRunResult,
        EpisodeVerifiedResearchReportWorkflowRunResult,
    )

    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.discover_eligible_report_summaries",
        lambda **kwargs: ([], "missing", "complete"),
    )
    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.run_episode_verified_research_report_workflow",
        lambda podcast_id, episode_ref, *, confirm=False, **kwargs: EpisodeVerifiedResearchReportWorkflowRunResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            outcome="blocked",
            ready=False,
            missing_roles=["semantic_review"],
            stale_roles=[],
            failed_gates=[],
            report_version=None,
            source_digest=None,
            bundle_dir=None,
            report_json_path=None,
            report_markdown_path=None,
            manifest_path=None,
            stock_query=None,
            include_fixture_verification=False,
            warnings=[],
            not_investment_advice=True,
        ),
    )

    def fake_016(podcast_id, *, episode_ref="latest", action="next", confirm=False, **kwargs):
        assert confirm is False
        assert episode_ref == "EP3"
        return CorpusEpisodeCompletionWorkflowRunResult(
            podcast_id=podcast_id,
            run_mode="dry_run",
            confirm=False,
            selector=episode_ref,
            episode_ref=episode_ref,
            requested_action=action,
            selected_action="semantic_summary",
            executed_action=None,
            report_json_path=None,
            report_markdown_path=None,
            filters=CorpusEpisodeCompletionWorkflowRunFilter(
                episode_ref=episode_ref,
                action=action,
                transcription_model=None,
                transcription_device="cpu",
                transcription_compute_type="int8",
                transcription_vad_filter=False,
                semantic_provider=None,
                semantic_model=None,
                semantic_chunk_seconds=600,
                semantic_max_segments_per_chunk=120,
            ),
            counts=CorpusEpisodeCompletionWorkflowRunCounts(
                row_count=1,
                selected_count=1,
                executed_count=0,
                reused_count=0,
                completed_count=0,
                failed_count=0,
                blocked_count=0,
                rejected_count=0,
                manual_only_count=0,
                warning_count=0,
            ),
            rows=[],
            warnings=[],
            not_investment_advice=True,
        )

    monkeypatch.setattr(
        "corpus_ingest_core.historical_verified_report_path.run_corpus_episode_completion_workflow",
        fake_016,
    )

    result = suggest_historical_verified_report_next_step("gooaye", "EP3")
    assert result.suggestion == "completion_action"
    assert result.completion_action == "semantic_summary"
    assert result.recommended_mcp_tool == "run_corpus_episode_completion_workflow"
    assert result.requires_api_cost_ack is True
    assert result.missing_roles == ["semantic_review"]
