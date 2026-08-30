from __future__ import annotations

import json
import sqlite3
import sys


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "CACHE_DIR", tmp_path / "cache")


def _write_transcript(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    segments=None,
    json_text=None,
):
    from corpus_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 1.0, "end": 5.0, "text": "台積電 第一段"},
            {"id": 2, "start": 8.0, "end": 12.0, "text": "第二段文字"},
        ]
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("\n".join(s["text"] for s in segments), encoding="utf-8")
    paths.srt_path.write_text("1\n00:00:01,000 --> 00:00:05,000\n字幕\n", encoding="utf-8")
    if json_text is None:
        payload = {
            "podcast_id": podcast_id,
            "episode_ref": episode_ref,
            "title": title,
            "segment_count": len(segments),
            "last_segment_end_seconds": segments[-1]["end"] if segments else None,
            "segments": segments,
        }
        json_text = json.dumps(payload, ensure_ascii=False)
    paths.json_path.write_text(json_text, encoding="utf-8")
    return paths


def _write_mentions(monkeypatch, tmp_path, *, podcast_id="gooaye", episode_ref="EP672", title="EP672 title"):
    from corpus_ingest_core.storage import mention_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = mention_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "extraction_mode": "deterministic-rules",
        "segment_count": 2,
        "mention_count": 1,
        "mentions": [
            {
                "type": "company",
                "text": "台積電",
                "normalized_text": "台積電",
                "count": 2,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 1.0,
                        "end": 5.0,
                        "timestamp": "[00:00:01 - 00:00:05]",
                        "text": "台積電 第一段",
                    }
                ],
            }
        ],
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# mentions", encoding="utf-8")
    return paths


def test_initialize_cache_creates_schema(tmp_path):
    from corpus_ingest_core.cache import initialize_cache

    db_path = initialize_cache(tmp_path / "cache.sqlite3")

    with sqlite3.connect(db_path) as connection:
        tables = {row[0] for row in connection.execute("select name from sqlite_master where type = 'table'")}
    assert {"episodes", "transcript_segments", "mentions", "mention_evidence"} <= tables


def test_is_fts5_available_returns_boolean(tmp_path):
    from corpus_ingest_core.cache import initialize_cache, is_fts5_available

    db_path = initialize_cache(tmp_path / "cache.sqlite3")

    assert isinstance(is_fts5_available(db_path), bool)


def test_index_episode_indexes_valid_transcript_segments(monkeypatch, tmp_path):
    from corpus_ingest_core.cache import index_episode

    _write_transcript(monkeypatch, tmp_path)
    db_path = tmp_path / "cache.sqlite3"

    result = index_episode("gooaye", "EP672", db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        segment_count = connection.execute("select count(*) from transcript_segments").fetchone()[0]
        title = connection.execute("select title from episodes").fetchone()[0]
    assert result.indexed is True
    assert result.transcript_segment_count == 2
    assert segment_count == 2
    assert title == "EP672 title"


def test_index_episode_indexes_mentions_json(monkeypatch, tmp_path):
    from corpus_ingest_core.cache import index_episode

    _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path)
    db_path = tmp_path / "cache.sqlite3"

    result = index_episode("gooaye", "EP672", db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        mention_count = connection.execute("select count(*) from mentions").fetchone()[0]
        evidence_count = connection.execute("select count(*) from mention_evidence").fetchone()[0]
        markdown_path = connection.execute("select mentions_markdown_path from episodes").fetchone()[0]
    assert result.mention_count == 1
    assert mention_count == 1
    assert evidence_count == 1
    assert markdown_path.endswith("EP672__EP672_title.mentions.md")
    assert ".mentions.mentions.md" not in markdown_path


def test_index_episode_records_corrupt_transcript_problem(monkeypatch, tmp_path):
    from corpus_ingest_core.cache import index_episode

    _write_transcript(monkeypatch, tmp_path, json_text="{not-json")

    result = index_episode("gooaye", "EP672", db_path=tmp_path / "cache.sqlite3")

    assert result.indexed is False
    assert result.problems


def test_index_episode_force_replaces_old_segments(monkeypatch, tmp_path):
    from corpus_ingest_core.cache import index_episode

    db_path = tmp_path / "cache.sqlite3"
    _write_transcript(monkeypatch, tmp_path)
    index_episode("gooaye", "EP672", db_path=db_path)
    _write_transcript(
        monkeypatch,
        tmp_path,
        segments=[{"id": 1, "start": 2.0, "end": 3.0, "text": "台積電 updated"}],
    )

    result = index_episode("gooaye", "EP672", force=True, db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        segment_count = connection.execute("select count(*) from transcript_segments").fetchone()[0]
    assert result.transcript_segment_count == 1
    assert segment_count == 1


def test_index_episode_records_warning_when_fts5_unavailable(monkeypatch, tmp_path):
    from corpus_ingest_core import cache

    db_path = tmp_path / "cache.sqlite3"
    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(cache, "is_fts5_available", lambda db_path=None: False)

    result = cache.index_episode("gooaye", "EP672", db_path=db_path)

    assert result.indexed is True
    assert any("FTS5" in warning for warning in result.warnings)


def test_rebuild_cache_scans_fixture_artifacts(monkeypatch, tmp_path):
    from corpus_ingest_core.cache import rebuild_cache

    _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path)

    result = rebuild_cache(podcast_id="gooaye", force=True, db_path=tmp_path / "cache.sqlite3")

    assert result.indexed_episode_count == 1
    assert result.skipped_episode_count == 0


def test_red_rebuild_cache_ignores_transient_artifact_siblings(monkeypatch, tmp_path):
    from corpus_ingest_core import storage
    from corpus_ingest_core.cache import rebuild_cache

    transcript = _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path)
    # Crash leftovers from the compensating writers: same directory, same
    # "<ref>__<slug>" stem, but never an artifact the cache should index.
    for leftover in (
        transcript.json_path.with_name(f".{transcript.json_path.name}.deadbeef.superseded"),
        transcript.json_path.with_name(f".{transcript.json_path.name}.deadbeef.restore.part"),
        (storage.MENTIONS_DIR / "gooaye" / "EP672__EP672-title.mentions.json.deadbeef.part"),
    ):
        leftover.write_bytes(b"{}")

    result = rebuild_cache(podcast_id="gooaye", force=True, db_path=tmp_path / "cache.sqlite3")

    assert result.indexed_episode_count == 1
    assert result.skipped_episode_count == 0
    assert result.problems == []


def test_rebuild_cache_does_not_fail_when_fts5_unavailable(monkeypatch, tmp_path):
    from corpus_ingest_core import cache

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(cache, "is_fts5_available", lambda db_path=None: False)

    result = cache.rebuild_cache(
        podcast_id="gooaye",
        force=True,
        db_path=tmp_path / "cache.sqlite3",
    )

    assert result.indexed_episode_count == 1
    assert any("FTS5" in warning for warning in result.warnings)


def test_rebuild_cache_cli_parses_options(monkeypatch, capsys, tmp_path):
    from scripts import rebuild_cache

    from corpus_ingest_core.models import CacheRebuildResult

    captured = {}

    def fake_rebuild_cache(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return CacheRebuildResult(
            db_path=str(tmp_path / "cache.sqlite3"),
            indexed_episode_count=1,
            skipped_episode_count=0,
            problems=[],
            warnings=[],
        )

    monkeypatch.setattr(rebuild_cache, "rebuild_cache", fake_rebuild_cache)
    monkeypatch.setattr(
        sys,
        "argv",
        ["rebuild_cache.py", "--podcast", "gooaye", "--force"],
    )

    rebuild_cache.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["indexed_episode_count"] == 1
    assert captured["args"] == ()
    assert captured["kwargs"] == {"podcast_id": "gooaye", "force": True}
