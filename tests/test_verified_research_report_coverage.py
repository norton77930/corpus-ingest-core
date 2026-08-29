"""Focused Core contracts for SPEC 022 verified report coverage index."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64


def _use_tmp_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    from corpus_ingest_core import corpus_index, storage

    reports = tmp_path / "research-reports"
    corpus = tmp_path / "corpus"
    transcripts = tmp_path / "transcripts"
    monkeypatch.setattr(storage, "RESEARCH_REPORTS_DIR", reports)
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus)
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", transcripts)
    monkeypatch.setattr(storage, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "MAPPINGS_DIR", tmp_path / "mappings")
    monkeypatch.setattr(storage, "EXTERNAL_DIR", tmp_path / "external")
    # Isolate inventory discovery from real evals/ reports under the repo CWD.
    monkeypatch.setattr(
        corpus_index,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
    )
    return reports, corpus


def _write_seed(corpus: Path, podcast_id: str, episode_ref: str) -> None:
    seed_dir = corpus / podcast_id / "episode-seeds"
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / f"{episode_ref}.episode-seed.json").write_text(
        json.dumps({"episode_ref": episode_ref}), encoding="utf-8"
    )


def _write_transcript(transcripts: Path, podcast_id: str, episode_ref: str) -> None:
    directory = transcripts / podcast_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{episode_ref}.json").write_text("{}", encoding="utf-8")


def _write_bundle(root: Path, podcast_id: str, episode_ref: str, digest: str) -> Path:
    bundle = root / podcast_id / episode_ref / f"v1-{digest}"
    bundle.mkdir(parents=True)
    manifest = {
        "schema_version": "latest-episode-verified-research-report-v1",
        "report_version": f"v1-{digest}",
        "source_digest": digest,
        "episode_identity": {"podcast_id": podcast_id, "episode_ref": episode_ref},
        "assembly_options": {"include_fixture_verification": False, "stock_query": None},
        "quality_gates": {
            "semantic_review_status": "passed",
            "not_investment_advice": True,
        },
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (bundle / "report.json").write_text("report body sentinel", encoding="utf-8")
    (bundle / "report.md").write_text("markdown body sentinel", encoding="utf-8")
    return bundle


def test_coverage_joins_inventory_and_bundles_with_filters_and_zero_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core import list_verified_research_report_coverage

    reports, corpus = _use_tmp_data(monkeypatch, tmp_path)
    from corpus_ingest_core import storage

    _write_seed(corpus, "gooaye", "EP1")
    _write_seed(corpus, "gooaye", "EP2")
    _write_transcript(storage.TRANSCRIPTS_DIR, "gooaye", "EP3")
    _write_bundle(reports, "gooaye", "EP1", _DIGEST_A)
    _write_bundle(reports, "gooaye", "EP1", _DIGEST_B)
    _write_bundle(reports, "gooaye", "EP9", _DIGEST_A)  # orphan
    (reports / "gooaye" / "EP1" / f"v1-{_DIGEST_A}" / "report.json").write_text(
        "report body sentinel", encoding="utf-8"
    )

    before = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}

    page = list_verified_research_report_coverage("gooaye")

    assert page.podcast_id == "gooaye"
    assert page.coverage_status == "complete"
    assert page.catalog_root_status == "available"
    assert page.inventory_episode_count == 3
    assert page.bundle_episode_count == 2
    assert page.with_bundle_count == 1
    assert page.without_bundle_count == 2
    assert page.orphan_bundle_episode_count == 1
    assert page.not_investment_advice is True
    by_ref = {row.episode_ref: row for row in page.items}
    assert set(by_ref) == {"EP1", "EP2", "EP3", "EP9"}
    assert by_ref["EP1"].inventory_present is True
    assert by_ref["EP1"].has_bundle is True
    assert by_ref["EP1"].bundle_count == 2
    assert by_ref["EP1"].source_digests == sorted([_DIGEST_A, _DIGEST_B])
    assert by_ref["EP2"].has_bundle is False
    assert by_ref["EP9"].inventory_present is False
    assert by_ref["EP9"].has_bundle is True
    assert "report body sentinel" not in repr(page)

    gaps = list_verified_research_report_coverage("gooaye", has_bundle=False)
    assert [row.episode_ref for row in gaps.items] == ["EP2", "EP3"]
    assert gaps.with_bundle_count == 1
    assert gaps.without_bundle_count == 2

    covered = list_verified_research_report_coverage("gooaye", has_bundle=True, limit=1)
    assert covered.returned_count == 1
    assert covered.limit == 1
    assert covered.items[0].has_bundle is True

    after = {path: path.stat().st_mtime_ns for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


def test_coverage_missing_sides_and_input_validation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core import (
        VerifiedResearchReportCoverageInputError,
        list_verified_research_report_coverage,
        verified_research_report_coverage_result_to_dict,
    )

    _use_tmp_data(monkeypatch, tmp_path)
    before = list(tmp_path.rglob("*"))

    page = list_verified_research_report_coverage("gooaye")
    assert page.items == []
    assert page.catalog_root_status == "missing"
    assert page.inventory_episode_count == 0
    assert page.returned_count == 0
    assert list(tmp_path.rglob("*")) == before

    payload = verified_research_report_coverage_result_to_dict(page)
    assert payload["not_investment_advice"] is True
    assert "items" in payload

    for kwargs in (
        {"limit": 0},
        {"limit": 101},
        {"limit": True},
        {"has_bundle": "yes"},  # type: ignore[arg-type]
    ):
        with pytest.raises(VerifiedResearchReportCoverageInputError):
            list_verified_research_report_coverage("gooaye", **kwargs)  # type: ignore[arg-type]

    with pytest.raises(VerifiedResearchReportCoverageInputError):
        list_verified_research_report_coverage("")
    with pytest.raises(VerifiedResearchReportCoverageInputError):
        list_verified_research_report_coverage("../escape")
    with pytest.raises(VerifiedResearchReportCoverageInputError):
        list_verified_research_report_coverage("Not_A_Slug")
