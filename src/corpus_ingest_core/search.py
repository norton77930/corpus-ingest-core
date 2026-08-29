from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from . import storage
from .cache import is_fts5_available
from .errors import SearchError
from .models import MentionSearchResult, TranscriptSearchResult

_VALID_TRANSCRIPT_SEARCH_MODES = {"auto", "like", "fts"}
_MAX_CONTEXT_SEGMENTS = 5


def search_transcripts(
    query: str,
    podcast_id: str | None = None,
    limit: int = 20,
    db_path: str | Path | None = None,
    search_mode: str = "auto",
    context_segments: int = 0,
    case_sensitive: bool = False,
) -> list[TranscriptSearchResult]:
    """搜尋 SQLite cache 中的 transcript segments。"""

    _validate_search_input(query, limit)
    _validate_context_segments(context_segments)
    resolved_path = _resolve_existing_db_path(db_path)
    effective_mode = _resolve_transcript_search_mode(
        query=query,
        db_path=resolved_path,
        requested_mode=search_mode,
        case_sensitive=case_sensitive,
    )

    try:
        with sqlite3.connect(resolved_path) as connection:
            rows = (
                _search_transcripts_with_fts(connection, query, podcast_id, limit)
                if effective_mode == "fts"
                else _search_transcripts_with_like(
                    connection,
                    query,
                    podcast_id,
                    limit,
                    case_sensitive=case_sensitive,
                )
            )
            return [
                _transcript_result_from_row(
                    connection,
                    row,
                    query=query,
                    case_sensitive=case_sensitive,
                    search_mode=effective_mode,
                    context_segments=context_segments,
                )
                for row in rows
            ]
    except sqlite3.Error as exc:
        raise SearchError(f"搜尋 transcript cache 失敗：{exc}") from exc


def search_mentions(
    query: str,
    podcast_id: str | None = None,
    mention_type: str | None = None,
    limit: int = 20,
    db_path: str | Path | None = None,
    case_sensitive: bool = False,
) -> list[MentionSearchResult]:
    """搜尋 SQLite cache 中的 mentions 與 evidence。"""

    _validate_search_input(query, limit)
    resolved_path = _resolve_existing_db_path(db_path)
    where_expression = _substring_where_expression(
        ("m.text", "m.normalized_text", "ev.text"),
        case_sensitive=case_sensitive,
    )
    sql = f"""
        select m.podcast_id, m.episode_ref, coalesce(ep.title, m.episode_ref) as title,
               m.mention_type, m.text, m.normalized_text, m.count,
               coalesce(ev.timestamp, '') as evidence_timestamp,
               coalesce(ev.text, '') as evidence_text
        from mentions m
        left join episodes ep
          on ep.podcast_id = m.podcast_id and ep.episode_ref = m.episode_ref
        left join mention_evidence ev
          on ev.podcast_id = m.podcast_id
         and ev.episode_ref = m.episode_ref
         and ev.mention_type = m.mention_type
         and ev.normalized_text = m.normalized_text
        where {where_expression}
    """
    parameters: list[object] = [query, query, query]
    if podcast_id is not None:
        sql += " and m.podcast_id = ?"
        parameters.append(podcast_id)
    if mention_type is not None:
        sql += " and m.mention_type = ?"
        parameters.append(mention_type)
    sql += " order by m.episode_ref, m.mention_type, m.text limit ?"
    parameters.append(limit)

    try:
        with sqlite3.connect(resolved_path) as connection:
            rows = connection.execute(sql, parameters).fetchall()
    except sqlite3.Error as exc:
        raise SearchError(f"搜尋 mention cache 失敗：{exc}") from exc

    return [
        MentionSearchResult(
            podcast_id=row[0],
            episode_ref=row[1],
            title=row[2],
            mention_type=row[3],
            text=row[4],
            normalized_text=row[5],
            count=row[6],
            evidence_timestamp=row[7],
            evidence_text=row[8],
            highlighted_text=_highlight_text(row[8] or row[4], query, case_sensitive)[1],
            search_mode="like",
        )
        for row in rows
    ]


def _search_transcripts_with_like(
    connection: sqlite3.Connection,
    query: str,
    podcast_id: str | None,
    limit: int,
    *,
    case_sensitive: bool,
) -> list[tuple]:
    where_expression = _substring_where_expression(("s.text",), case_sensitive=case_sensitive)
    sql = f"""
        select s.podcast_id, s.episode_ref, coalesce(e.title, s.episode_ref) as title,
               s.segment_id, s.start, s.end, s.timestamp, s.text, null as score
        from transcript_segments s
        left join episodes e
          on e.podcast_id = s.podcast_id and e.episode_ref = s.episode_ref
        where {where_expression}
    """
    parameters: list[object] = [query]
    if podcast_id is not None:
        sql += " and s.podcast_id = ?"
        parameters.append(podcast_id)
    sql += " order by s.episode_ref, s.start limit ?"
    parameters.append(limit)
    return connection.execute(sql, parameters).fetchall()


def _search_transcripts_with_fts(
    connection: sqlite3.Connection,
    query: str,
    podcast_id: str | None,
    limit: int,
) -> list[tuple]:
    sql = """
        select s.podcast_id, s.episode_ref, coalesce(e.title, s.episode_ref) as title,
               s.segment_id, s.start, s.end, s.timestamp, s.text,
               bm25(transcript_segments_fts) as score
        from transcript_segments_fts
        join transcript_segments s
          on s.podcast_id = transcript_segments_fts.podcast_id
         and s.episode_ref = transcript_segments_fts.episode_ref
         and s.segment_id = transcript_segments_fts.segment_id
        left join episodes e
          on e.podcast_id = s.podcast_id and e.episode_ref = s.episode_ref
        where transcript_segments_fts match ?
    """
    parameters: list[object] = [_fts_phrase_query(query)]
    if podcast_id is not None:
        sql += " and transcript_segments_fts.podcast_id = ?"
        parameters.append(podcast_id)
    sql += " order by score, s.episode_ref, s.start limit ?"
    parameters.append(limit)
    return connection.execute(sql, parameters).fetchall()


def _transcript_result_from_row(
    connection: sqlite3.Connection,
    row: tuple,
    *,
    query: str,
    case_sensitive: bool,
    search_mode: str,
    context_segments: int,
) -> TranscriptSearchResult:
    context_before: list[str] | None = None
    context_after: list[str] | None = None
    if context_segments:
        context_before, context_after = _fetch_context_segments(
            connection,
            podcast_id=row[0],
            episode_ref=row[1],
            segment_id=str(row[3]),
            context_segments=context_segments,
        )
    matched_text, highlighted_text = _highlight_text(row[7], query, case_sensitive)
    return TranscriptSearchResult(
        podcast_id=row[0],
        episode_ref=row[1],
        title=row[2],
        segment_id=row[3],
        start=row[4],
        end=row[5],
        timestamp=row[6],
        text=row[7],
        matched_text=matched_text,
        highlighted_text=highlighted_text,
        context_before=context_before,
        context_after=context_after,
        search_mode=search_mode,
        score=row[8],
    )


def _fetch_context_segments(
    connection: sqlite3.Connection,
    *,
    podcast_id: str,
    episode_ref: str,
    segment_id: str,
    context_segments: int,
) -> tuple[list[str], list[str]]:
    rows = connection.execute(
        """
        select segment_id, text
        from transcript_segments
        where podcast_id = ? and episode_ref = ?
        order by case when start is null then 1 else 0 end, start, segment_id
        """,
        (podcast_id, episode_ref),
    ).fetchall()
    index = next(
        (row_index for row_index, row in enumerate(rows) if str(row[0]) == segment_id),
        None,
    )
    if index is None:
        return [], []
    before = rows[max(0, index - context_segments) : index]
    after = rows[index + 1 : index + 1 + context_segments]
    return [row[1] for row in before], [row[1] for row in after]


def _resolve_transcript_search_mode(
    *,
    query: str,
    db_path: Path,
    requested_mode: str,
    case_sensitive: bool,
) -> str:
    if requested_mode not in _VALID_TRANSCRIPT_SEARCH_MODES:
        raise SearchError(f"未知 search_mode：{requested_mode}")
    if requested_mode == "like":
        return "like"
    if requested_mode == "fts":
        if not _is_fts_ready(db_path):
            raise SearchError("SQLite FTS5 不可用或 cache 尚未建立 FTS table，無法使用 search_mode=fts。")
        return "fts"
    if case_sensitive or _contains_non_ascii(query) or not _is_fts_ready(db_path):
        return "fallback"
    return "fts"


def _is_fts_ready(db_path: Path) -> bool:
    if not is_fts5_available(db_path):
        return False
    try:
        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                """
                select 1
                from sqlite_master
                where type = 'table' and name = 'transcript_segments_fts'
                """
            ).fetchone()
    except sqlite3.Error:
        return False
    return row is not None


def _substring_where_expression(columns: tuple[str, ...], *, case_sensitive: bool) -> str:
    if case_sensitive:
        return "(" + " or ".join(f"instr({column}, ?) > 0" for column in columns) + ")"
    return "(" + " or ".join(f"instr(lower({column}), lower(?)) > 0" for column in columns) + ")"


def _highlight_text(text: str, query: str, case_sensitive: bool) -> tuple[str | None, str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    match = re.search(re.escape(query), text, flags)
    if match is None:
        return None, text
    highlighted = re.sub(
        re.escape(query),
        lambda found: f"[[{found.group(0)}]]",
        text,
        flags=flags,
    )
    return match.group(0), highlighted


def _contains_non_ascii(value: str) -> bool:
    return any(ord(character) > 127 for character in value)


def _fts_phrase_query(query: str) -> str:
    escaped_query = query.replace('"', '""')
    return f'"{escaped_query}"'


def _validate_search_input(query: str, limit: int) -> None:
    if not query.strip():
        raise SearchError("query 不可為空。")
    if limit < 1:
        raise SearchError("limit 必須大於 0。")


def _validate_context_segments(context_segments: int) -> None:
    if context_segments < 0 or context_segments > _MAX_CONTEXT_SEGMENTS:
        raise SearchError("context_segments 必須介於 0 到 5。")


def _resolve_existing_db_path(db_path: str | Path | None) -> Path:
    resolved_path = Path(db_path) if db_path is not None else storage.cache_db_path()
    if not resolved_path.exists():
        raise SearchError(f"SQLite cache 不存在：{resolved_path}")
    return resolved_path
