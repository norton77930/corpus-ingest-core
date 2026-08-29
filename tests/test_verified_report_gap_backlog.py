"""Core contracts for SPEC 024 gap backlog."""

from __future__ import annotations

from pathlib import Path

import pytest


def _isolate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", tmp_path / "research-reports")
    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus")
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


def test_gap_backlog_reuses_coverage_gaps_and_is_zero_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core import list_verified_report_gap_backlog, storage
    from corpus_ingest_core.models import (
        VerifiedResearchReportCoveragePage,
        VerifiedResearchReportCoverageRow,
    )

    _isolate(monkeypatch, tmp_path)
    calls: list[dict[str, object]] = []

    def fake_coverage(podcast_id, *, has_bundle=None, limit=50):
        calls.append({"podcast_id": podcast_id, "has_bundle": has_bundle, "limit": limit})
        return VerifiedResearchReportCoveragePage(
            podcast_id=podcast_id,
            items=[
                VerifiedResearchReportCoverageRow(
                    podcast_id=podcast_id,
                    episode_ref="EP2",
                    inventory_present=True,
                    has_bundle=False,
                    bundle_count=0,
                    source_digests=[],
                )
            ],
            limit=limit,
            returned_count=1,
            inventory_episode_count=2,
            bundle_episode_count=1,
            with_bundle_count=1,
            without_bundle_count=1,
            orphan_bundle_episode_count=0,
            coverage_status="complete",
            catalog_root_status="available",
        )

    monkeypatch.setattr(
        "corpus_ingest_core.verified_report_gap_backlog.list_verified_research_report_coverage",
        fake_coverage,
    )
    before = list(tmp_path.rglob("*"))
    page = list_verified_report_gap_backlog("gooaye", limit=10)
    assert calls == [{"podcast_id": "gooaye", "has_bundle": False, "limit": 10}]
    assert [row.episode_ref for row in page.items] == ["EP2"]
    assert page.gap_count == 1
    assert page.inventory_episode_count == 2
    assert page.not_investment_advice is True
    assert list(tmp_path.rglob("*")) == before


def test_gap_backlog_maps_coverage_input_errors() -> None:
    from corpus_ingest_core import (
        VerifiedReportGapBacklogInputError,
        list_verified_report_gap_backlog,
    )

    with pytest.raises(VerifiedReportGapBacklogInputError):
        list_verified_report_gap_backlog("gooaye", limit=0)
