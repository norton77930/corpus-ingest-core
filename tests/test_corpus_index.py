from __future__ import annotations

import json
import sys
from pathlib import Path


def _use_tmp_data_dirs(monkeypatch, tmp_path: Path) -> Path:
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
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    monkeypatch.setattr(
        corpus_index, "SEMANTIC_REVIEW_REPORTS_DIR", review_dir, raising=False
    )
    return review_dir


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_audio(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    path = storage.AUDIO_DIR / podcast_id / f"{episode_ref}__{title}.mp3"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"mp3")
    return path


def _write_transcript(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    segments: list[dict] | None = None,
    json_text: str | None = None,
) -> Path:
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 0.0, "end": 5.5, "text": "transcript body must not leak"},
            {"id": 2, "start": 7.0, "end": 9.0, "text": "second body line"},
        ]
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("\n".join(item["text"] for item in segments), encoding="utf-8")
    paths.srt_path.write_text("1\n00:00:00,000 --> 00:00:05,500\ntext\n", encoding="utf-8")
    if json_text is not None:
        paths.json_path.write_text(json_text, encoding="utf-8")
    else:
        _write_json(
            paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "language": "zh",
                "segment_count": len(segments),
                "last_segment_end_seconds": segments[-1]["end"] if segments else None,
                "generated_at": "2026-01-01T00:00:00Z",
                "segments": segments,
            },
        )
    return paths.json_path


def _write_summary(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    semantic: bool = False,
    body: str = "summary body must not leak",
) -> Path:
    from podcast_ingest_core import storage

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    suffix = ".semantic.md" if semantic else ".md"
    path = storage.SUMMARIES_DIR / podcast_id / f"{episode_ref}__{title}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_mentions(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
    json_text: str | None = None,
) -> Path:
    from podcast_ingest_core.storage import mention_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = mention_asset_paths(podcast_id, episode_ref, title)
    if json_text is None:
        _write_json(
            paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "mention_count": 2,
                "mentions": [
                    {"text": "evidence text must not leak"},
                    {"text": "another evidence text must not leak"},
                ],
            },
        )
    else:
        paths.json_path.parent.mkdir(parents=True, exist_ok=True)
        paths.json_path.write_text(json_text, encoding="utf-8")
    paths.markdown_path.write_text("# mentions body must not leak", encoding="utf-8")
    return paths.json_path


def _write_episode_intelligence(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import episode_intelligence_report_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = episode_intelligence_report_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "report_status": "final",
                "transcript_validation": {"status": "valid", "segment_count": 2},
                "sections": [
                    {
                        "heading": "body",
                        "evidence": [
                            {"text": "episode intelligence evidence must not leak"}
                        ],
                    }
                ],
            },
    )
    paths.markdown_path.write_text("# report body must not leak", encoding="utf-8")
    return paths.json_path


def _write_industry_mapping(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import industry_chain_mapping_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = industry_chain_mapping_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "mapping_status": "final",
                "industry_chain_nodes": [
                    {
                        "node_id": "semiconductor",
                        "evidence": [{"text": "mapping node evidence must not leak"}],
                    }
                ],
                "stock_candidates": [
                    {
                        "company_name": "TSMC",
                        "evidence": [{"text": "mapping candidate evidence must not leak"}],
                    }
                ],
                "warnings": ["mapping warning body must not leak"],
            },
    )
    paths.markdown_path.write_text("# mapping body must not leak", encoding="utf-8")
    return paths.json_path


def _write_external_boundary(
    monkeypatch,
    tmp_path: Path,
    *,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    title: str = "Alpha",
) -> Path:
    from podcast_ingest_core.storage import external_data_boundary_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = external_data_boundary_asset_paths(podcast_id, episode_ref, title)
    _write_json(
        paths.json_path,
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "boundary_status": "final",
                "candidate_boundaries": [
                    {
                        "company_name": "TSMC",
                        "notes": "external boundary candidate body must not leak",
                    }
                ],
                "warnings": [],
            },
    )
    paths.markdown_path.write_text("# boundary body must not leak", encoding="utf-8")
    return paths.json_path


def _write_semantic_review(
    review_dir: Path,
    *,
    timestamp: str,
    podcast_id: str = "gooaye",
    episode_ref: str = "EP672",
    review_status: str = "passed",
    check_count: int = 3,
    failed_check_count: int = 0,
    warning_count: int = 0,
    blocked_check_count: int = 0,
) -> Path:
    json_path = review_dir / f"{timestamp}__{podcast_id}__{episode_ref}.semantic-review.json"
    _write_json(
        json_path,
        {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "review_status": review_status,
            "check_count": check_count,
            "failed_check_count": failed_check_count,
            "warning_count": warning_count,
            "blocked_check_count": blocked_check_count,
            "checks": [{"name": "safe", "status": "pass", "message": "body omitted"}],
        },
    )
    json_path.with_suffix(".md").write_text("# review body must not leak", encoding="utf-8")
    return json_path


def _payload(result) -> dict:
    return json.loads(result.index_json_path.read_text(encoding="utf-8"))


def test_corpus_index_asset_paths_contract():
    from podcast_ingest_core.storage import corpus_index_asset_paths

    paths = corpus_index_asset_paths("gooaye")

    assert paths.json_path == Path("data/corpus/gooaye/corpus-index.json")
    assert paths.markdown_path == Path("data/corpus/gooaye/corpus-index.md")


def test_corpus_index_public_result_contract_exports(tmp_path):
    from podcast_ingest_core import (
        CorpusArtifactFamilyCounts,
        CorpusEpisodeRow,
        CorpusIndexFailedError,
        CorpusIndexResult,
        generate_corpus_index,
    )

    counts = CorpusArtifactFamilyCounts(available=1, missing=2, unreadable=3)
    row = CorpusEpisodeRow(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Alpha",
        artifact_status={},
        missing_artifacts=[],
        warnings=[],
    )
    result = CorpusIndexResult(
        podcast_id="gooaye",
        index_json_path=tmp_path / "corpus-index.json",
        index_markdown_path=tmp_path / "corpus-index.md",
        episode_count=1,
        warning_count=0,
        artifact_family_counts={"transcript": counts},
    )

    assert row.episode_ref == "EP672"
    assert result.artifact_family_counts["transcript"].available == 1
    assert CorpusIndexFailedError.__name__ == "CorpusIndexFailedError"
    assert callable(generate_corpus_index)


def test_generate_corpus_index_writes_empty_index(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    result = generate_corpus_index("gooaye")

    payload = _payload(result)
    markdown = result.index_markdown_path.read_text(encoding="utf-8")
    assert result.episode_count == 0
    assert payload["episode_count"] == 0
    assert payload["episodes"] == []
    assert payload["warning_count"] == 0
    assert payload["not_investment_advice"] is True
    assert "generated_at" not in result.index_json_path.read_text(encoding="utf-8")
    assert "not investment advice" in markdown.lower()


def test_generate_corpus_index_discovers_supported_episode_artifacts(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_audio(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_summary(monkeypatch, tmp_path)
    _write_summary(monkeypatch, tmp_path, semantic=True)
    _write_mentions(monkeypatch, tmp_path)
    _write_episode_intelligence(monkeypatch, tmp_path)
    _write_industry_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)
    _write_semantic_review(review_dir, timestamp="20260701-000000")
    _write_summary(monkeypatch, tmp_path, episode_ref="EP673", title="Beta")

    result = generate_corpus_index("gooaye")

    payload = _payload(result)
    markdown = result.index_markdown_path.read_text(encoding="utf-8")
    rows = {row["episode_ref"]: row for row in payload["episodes"]}
    ep672 = rows["EP672"]
    ep673 = rows["EP673"]
    assert list(rows) == ["EP672", "EP673"]
    assert ep672["artifact_status"]["audio"]["status"] == "available"
    assert ep672["artifact_status"]["transcript"]["validation_status"] == "valid"
    assert ep672["artifact_status"]["transcript"]["segment_count"] == 2
    assert ep672["artifact_status"]["extractive_summary"]["status"] == "available"
    assert ep672["artifact_status"]["semantic_summary"]["status"] == "available"
    assert ep672["artifact_status"]["mentions"]["mention_count"] == 2
    assert ep672["artifact_status"]["episode_intelligence"]["report_status"] == "final"
    assert ep672["artifact_status"]["industry_mapping"]["node_count"] == 1
    assert ep672["artifact_status"]["external_boundary"]["candidate_count"] == 1
    assert ep672["missing_artifacts"] == []
    assert ep673["artifact_status"]["extractive_summary"]["status"] == "available"
    assert "transcript" in ep673["missing_artifacts"]
    assert payload["artifact_family_counts"]["transcript"] == {
        "available": 1,
        "missing": 1,
        "unreadable": 0,
    }
    assert (
        "| EP672 | Alpha | valid | available | passed | 2 | final | final | final | none | 0 |"
        in markdown
    )


def test_generate_corpus_index_is_deterministic_and_has_no_timestamp(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    first = generate_corpus_index("gooaye")
    first_json = first.index_json_path.read_text(encoding="utf-8")
    first_md = first.index_markdown_path.read_text(encoding="utf-8")
    first.index_json_path.write_text("stale", encoding="utf-8")
    second = generate_corpus_index("gooaye")

    assert second.index_json_path.read_text(encoding="utf-8") == first_json
    assert second.index_markdown_path.read_text(encoding="utf-8") == first_md
    assert "generated_at" not in first_json
    assert "2026-01-01T00:00:00Z" not in first_json


def test_generate_corpus_index_reports_missing_artifact_families(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)

    result = generate_corpus_index("gooaye")

    row = _payload(result)["episodes"][0]
    assert row["artifact_status"]["transcript"]["status"] == "valid"
    assert row["missing_artifacts"] == [
        "audio",
        "extractive_summary",
        "semantic_summary",
        "semantic_review",
        "mentions",
        "episode_intelligence",
        "industry_mapping",
        "external_boundary",
    ]


def test_generate_corpus_index_contains_unreadable_json_to_affected_family(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path, json_text="{not-json")

    result = generate_corpus_index("gooaye")

    row = _payload(result)["episodes"][0]
    assert row["artifact_status"]["transcript"]["status"] == "valid"
    assert row["artifact_status"]["mentions"]["status"] == "unreadable"
    assert row["artifact_status"]["mentions"]["warning_count"] == 1
    assert result.warning_count == 1


def test_generate_corpus_index_selects_duplicate_candidates_deterministically(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(monkeypatch, tmp_path, title="Zulu")
    selected_path = _write_transcript(monkeypatch, tmp_path, title="Alpha")

    result = generate_corpus_index("gooaye")

    transcript = _payload(result)["episodes"][0]["artifact_status"]["transcript"]
    assert transcript["candidate_count"] == 2
    assert transcript["paths"]["json"] == str(selected_path)
    assert transcript["warnings"]


def test_generate_corpus_index_selects_latest_semantic_review(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    review_dir = _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_summary(monkeypatch, tmp_path, semantic=True)
    _write_semantic_review(
        review_dir,
        timestamp="20260701-000000",
        review_status="passed",
        check_count=2,
    )
    ignored = review_dir / "zzzz__gooaye__EP672.semantic-review.json"
    _write_json(
        ignored,
        {
            "podcast_id": "gooaye",
            "episode_ref": "EP672",
            "review_status": "passed",
            "check_count": 99,
        },
    )
    latest = _write_semantic_review(
        review_dir,
        timestamp="20260702-000000",
        review_status="failed",
        check_count=4,
        failed_check_count=1,
        warning_count=2,
    )

    result = generate_corpus_index("gooaye")

    semantic_review = _payload(result)["episodes"][0]["artifact_status"]["semantic_review"]
    assert semantic_review["status"] == "failed"
    assert semantic_review["review_status"] == "failed"
    assert semantic_review["review_json_path"] == str(latest)
    assert semantic_review["check_count"] == 4
    assert semantic_review["failed_check_count"] == 1
    assert semantic_review["warning_count"] == 2
    assert semantic_review["candidate_count"] == 2
    assert semantic_review["warnings"] == [
        f"ignored non-timestamped semantic review candidate: {ignored}"
    ]


def test_generate_corpus_index_excludes_semantic_summary_body(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_summary(
        monkeypatch,
        tmp_path,
        semantic=True,
        body="semantic body sentinel must not leak\nraw transcript dump: forbidden",
    )

    result = generate_corpus_index("gooaye")

    json_text = result.index_json_path.read_text(encoding="utf-8")
    markdown = result.index_markdown_path.read_text(encoding="utf-8")
    assert "semantic body sentinel" not in json_text
    assert "semantic body sentinel" not in markdown
    assert "raw transcript dump" not in json_text
    assert "raw transcript dump" not in markdown


def test_generate_corpus_index_excludes_body_text_from_json_metadata_artifacts(
    monkeypatch, tmp_path
):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    _write_transcript(
        monkeypatch,
        tmp_path,
        segments=[
            {
                "id": 1,
                "start": 0.0,
                "end": 1.0,
                "text": "transcript segment sentinel must not leak",
            }
        ],
    )
    _write_mentions(monkeypatch, tmp_path)
    _write_episode_intelligence(monkeypatch, tmp_path)
    _write_industry_mapping(monkeypatch, tmp_path)
    _write_external_boundary(monkeypatch, tmp_path)

    result = generate_corpus_index("gooaye")

    json_text = result.index_json_path.read_text(encoding="utf-8")
    markdown = result.index_markdown_path.read_text(encoding="utf-8")
    forbidden = [
        "transcript segment sentinel must not leak",
        "evidence text must not leak",
        "episode intelligence evidence must not leak",
        "mapping node evidence must not leak",
        "mapping candidate evidence must not leak",
        "mapping warning body must not leak",
        "external boundary candidate body must not leak",
    ]
    for text in forbidden:
        assert text not in json_text
        assert text not in markdown


def test_generate_corpus_index_reports_missing_semantic_review(monkeypatch, tmp_path):
    from podcast_ingest_core.corpus_index import generate_corpus_index

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    semantic_path = _write_summary(monkeypatch, tmp_path, semantic=True)

    result = generate_corpus_index("gooaye")

    row = _payload(result)["episodes"][0]
    assert row["artifact_status"]["semantic_summary"]["path"] == str(semantic_path)
    assert row["artifact_status"]["semantic_review"]["status"] == "missing"
    assert row["artifact_status"]["semantic_review"]["review_status"] == "missing"
    assert row["artifact_status"]["semantic_review"]["review_json_path"] is None


def test_generate_corpus_index_cli_prints_output_paths_and_counts(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import CorpusArtifactFamilyCounts, CorpusIndexResult
    from scripts import generate_corpus_index as cli

    result = CorpusIndexResult(
        podcast_id="gooaye",
        index_json_path=tmp_path / "corpus-index.json",
        index_markdown_path=tmp_path / "corpus-index.md",
        episode_count=2,
        warning_count=1,
        artifact_family_counts={
            "transcript": CorpusArtifactFamilyCounts(
                available=1, missing=1, unreadable=0
            )
        },
    )
    captured = {}

    def fake_generate(podcast_id: str):
        captured["podcast_id"] = podcast_id
        return result

    monkeypatch.setattr(cli, "generate_corpus_index", fake_generate)
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_corpus_index.py", "--podcast", "gooaye"],
    )

    exit_code = cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["podcast_id"] == "gooaye"
    assert payload["index_json_path"] == str(tmp_path / "corpus-index.json")
    assert payload["episode_count"] == 2
    assert payload["warning_count"] == 1
    assert payload["artifact_family_counts"]["transcript"]["available"] == 1


def test_generate_corpus_index_cli_reports_invalid_podcast(capsys, monkeypatch):
    from scripts import generate_corpus_index as cli

    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_corpus_index.py", "--podcast", "../bad"],
    )

    exit_code = cli.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "podcast_id" in captured.err
