from __future__ import annotations

import json
import sqlite3
import sys

import pytest


def _create_search_db(tmp_path):
    from corpus_ingest_core.cache import initialize_cache, is_fts5_available

    db_path = initialize_cache(tmp_path / "cache.sqlite3")
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            insert into episodes (podcast_id, episode_ref, title, transcript_status, segment_count, updated_at)
            values ('gooaye', 'EP672', 'EP672 title', 'valid', 1, 'now')
            """
        )
        connection.execute(
            """
            insert into transcript_segments (podcast_id, episode_ref, segment_id, start, end, timestamp, text)
            values ('gooaye', 'EP672', '1', 0.0, 1.0, '[00:00:00 - 00:00:01]', '前文')
            """
        )
        connection.execute(
            """
            insert into transcript_segments (podcast_id, episode_ref, segment_id, start, end, timestamp, text)
            values ('gooaye', 'EP672', '2', 1.0, 5.0, '[00:00:01 - 00:00:05]', '台積電 很重要')
            """
        )
        connection.execute(
            """
            insert into transcript_segments (podcast_id, episode_ref, segment_id, start, end, timestamp, text)
            values ('gooaye', 'EP672', '3', 6.0, 8.0, '[00:00:06 - 00:00:08]', '後文 NVIDIA')
            """
        )
        connection.execute(
            """
            insert into mentions (podcast_id, episode_ref, mention_type, text, normalized_text, count, confidence)
            values ('gooaye', 'EP672', 'company', '台積電', '台積電', 2, 'rule')
            """
        )
        connection.execute(
            """
            insert into mentions (podcast_id, episode_ref, mention_type, text, normalized_text, count, confidence)
            values ('gooaye', 'EP672', 'company', 'NVIDIA', 'nvidia', 1, 'rule')
            """
        )
        connection.execute(
            """
            insert into mention_evidence (podcast_id, episode_ref, mention_type, normalized_text, segment_id, start, end, timestamp, text)
            values ('gooaye', 'EP672', 'company', '台積電', '1', 1.0, 5.0, '[00:00:01 - 00:00:05]', '台積電 很重要')
            """
        )
        connection.execute(
            """
            insert into mention_evidence (podcast_id, episode_ref, mention_type, normalized_text, segment_id, start, end, timestamp, text)
            values ('gooaye', 'EP672', 'company', 'nvidia', '3', 6.0, 8.0, '[00:00:06 - 00:00:08]', '後文 NVIDIA')
            """
        )
        if is_fts5_available(db_path):
            connection.executemany(
                """
                insert into transcript_segments_fts (podcast_id, episode_ref, segment_id, text)
                values (?, ?, ?, ?)
                """,
                [
                    ("gooaye", "EP672", "1", "前文"),
                    ("gooaye", "EP672", "2", "台積電 很重要"),
                    ("gooaye", "EP672", "3", "後文 NVIDIA"),
                ],
            )
    return db_path


def test_search_transcripts_finds_segment(tmp_path):
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)

    results = search_transcripts(
        "台積電",
        podcast_id="gooaye",
        limit=10,
        db_path=db_path,
        search_mode="like",
    )

    assert len(results) == 1
    assert results[0].title == "EP672 title"
    assert results[0].timestamp == "[00:00:01 - 00:00:05]"
    assert results[0].matched_text == "台積電"
    assert results[0].highlighted_text == "[[台積電]] 很重要"
    assert results[0].search_mode == "like"
    assert results[0].score is None


def test_search_transcripts_auto_falls_back_to_like_for_chinese_query(tmp_path):
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)

    results = search_transcripts("台積電", db_path=db_path, search_mode="auto")

    assert len(results) == 1
    assert results[0].search_mode == "fallback"


def test_search_transcripts_fts_unavailable_raises_search_error(monkeypatch, tmp_path):
    from corpus_ingest_core.errors import SearchError
    from corpus_ingest_core import search as search_module
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)
    monkeypatch.setattr(search_module, "is_fts5_available", lambda db_path=None: False)

    with pytest.raises(SearchError):
        search_transcripts("NVIDIA", db_path=db_path, search_mode="fts")


def test_search_transcripts_fts_finds_english_query_when_available(tmp_path):
    from corpus_ingest_core.cache import is_fts5_available
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)
    if not is_fts5_available(db_path):
        pytest.skip("SQLite FTS5 is not available in this environment")

    results = search_transcripts("NVIDIA", db_path=db_path, search_mode="fts")

    assert len(results) == 1
    assert results[0].search_mode == "fts"
    assert results[0].highlighted_text == "後文 [[NVIDIA]]"


def test_search_transcripts_unknown_search_mode_raises_search_error(tmp_path):
    from corpus_ingest_core.errors import SearchError
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)

    with pytest.raises(SearchError):
        search_transcripts("台積電", db_path=db_path, search_mode="unknown")


def test_search_transcripts_case_sensitivity_for_english_query(tmp_path):
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)

    insensitive_results = search_transcripts(
        "nvidia",
        db_path=db_path,
        search_mode="like",
        case_sensitive=False,
    )
    sensitive_results = search_transcripts(
        "nvidia",
        db_path=db_path,
        search_mode="like",
        case_sensitive=True,
    )

    assert len(insensitive_results) == 1
    assert insensitive_results[0].highlighted_text == "後文 [[NVIDIA]]"
    assert sensitive_results == []


def test_search_transcripts_context_segments(tmp_path):
    from corpus_ingest_core.search import search_transcripts

    db_path = _create_search_db(tmp_path)

    results = search_transcripts(
        "台積電",
        db_path=db_path,
        search_mode="like",
        context_segments=1,
    )

    assert results[0].context_before == ["前文"]
    assert results[0].context_after == ["後文 NVIDIA"]


def test_search_mentions_finds_mention_and_evidence(tmp_path):
    from corpus_ingest_core.search import search_mentions

    db_path = _create_search_db(tmp_path)

    results = search_mentions("台積電", podcast_id="gooaye", db_path=db_path)

    assert len(results) == 1
    assert results[0].mention_type == "company"
    assert results[0].evidence_timestamp == "[00:00:01 - 00:00:05]"
    assert results[0].highlighted_text == "[[台積電]] 很重要"
    assert results[0].search_mode == "like"


def test_search_mentions_filters_by_type(tmp_path):
    from corpus_ingest_core.search import search_mentions

    db_path = _create_search_db(tmp_path)

    assert search_mentions("台積電", mention_type="company", db_path=db_path)
    assert search_mentions("台積電", mention_type="place", db_path=db_path) == []


def test_search_mentions_case_insensitive_query(tmp_path):
    from corpus_ingest_core.search import search_mentions

    db_path = _create_search_db(tmp_path)

    insensitive_results = search_mentions("nVidia", db_path=db_path, case_sensitive=False)
    sensitive_results = search_mentions("nVidia", db_path=db_path, case_sensitive=True)

    assert len(insensitive_results) == 1
    assert insensitive_results[0].highlighted_text == "後文 [[NVIDIA]]"
    assert sensitive_results == []


def test_search_missing_db_raises_search_error(tmp_path):
    from corpus_ingest_core.errors import SearchError
    from corpus_ingest_core.search import search_transcripts

    with pytest.raises(SearchError):
        search_transcripts("台積電", db_path=tmp_path / "missing.sqlite3")


def test_search_transcripts_cli_parses_options(monkeypatch, capsys):
    from corpus_ingest_core.models import TranscriptSearchResult
    from scripts import search_transcripts

    captured = {}

    def fake_search(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return [
            TranscriptSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="EP672 title",
                segment_id="1",
                start=1.0,
                end=5.0,
                timestamp="[00:00:01 - 00:00:05]",
                text="台積電",
            )
        ]

    monkeypatch.setattr(search_transcripts, "search_transcripts", fake_search)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "search_transcripts.py",
            "--podcast",
            "gooaye",
            "--query",
            "台積電",
            "--limit",
            "10",
            "--search-mode",
            "like",
            "--context-segments",
            "1",
            "--case-sensitive",
        ],
    )

    search_transcripts.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["episode_ref"] == "EP672"
    assert captured["args"] == ("台積電",)
    assert captured["kwargs"] == {
        "podcast_id": "gooaye",
        "limit": 10,
        "search_mode": "like",
        "context_segments": 1,
        "case_sensitive": True,
    }


def test_search_mentions_cli_parses_options(monkeypatch, capsys):
    from corpus_ingest_core.models import MentionSearchResult
    from scripts import search_mentions

    captured = {}

    def fake_search(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return [
            MentionSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="EP672 title",
                mention_type="company",
                text="台積電",
                normalized_text="台積電",
                count=2,
                evidence_timestamp="[00:00:01 - 00:00:05]",
                evidence_text="台積電",
            )
        ]

    monkeypatch.setattr(search_mentions, "search_mentions", fake_search)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "search_mentions.py",
            "--podcast",
            "gooaye",
            "--query",
            "台積電",
            "--type",
            "company",
            "--limit",
            "10",
            "--case-sensitive",
        ],
    )

    search_mentions.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["mention_type"] == "company"
    assert captured["args"] == ("台積電",)
    assert captured["kwargs"] == {
        "podcast_id": "gooaye",
        "mention_type": "company",
        "limit": 10,
        "case_sensitive": True,
    }
