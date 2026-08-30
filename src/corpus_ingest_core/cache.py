from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import storage
from .errors import CacheInitializationError, EpisodeIndexError
from .models import CacheRebuildResult, EpisodeIndexResult
from .validator import validate_transcript

SCHEMA_SQL = """
create table if not exists episodes (
    podcast_id text not null,
    episode_ref text not null,
    title text,
    published_at text,
    duration text,
    guid text,
    link text,
    audio_url text,
    transcript_json_path text,
    transcript_text_path text,
    transcript_srt_path text,
    extractive_summary_path text,
    semantic_summary_path text,
    mentions_json_path text,
    mentions_markdown_path text,
    transcript_status text,
    segment_count integer,
    last_segment_end_seconds real,
    updated_at text not null,
    primary key (podcast_id, episode_ref)
);

create table if not exists transcript_segments (
    podcast_id text not null,
    episode_ref text not null,
    segment_id text not null,
    start real,
    end real,
    timestamp text,
    text text
);

create index if not exists idx_transcript_segments_podcast
on transcript_segments (podcast_id);

create index if not exists idx_transcript_segments_episode
on transcript_segments (podcast_id, episode_ref);

create index if not exists idx_transcript_segments_text
on transcript_segments (text);

create table if not exists mentions (
    podcast_id text not null,
    episode_ref text not null,
    mention_type text not null,
    text text not null,
    normalized_text text not null,
    count integer,
    confidence text
);

create index if not exists idx_mentions_podcast
on mentions (podcast_id);

create index if not exists idx_mentions_type_text
on mentions (podcast_id, mention_type, normalized_text);

create table if not exists mention_evidence (
    podcast_id text not null,
    episode_ref text not null,
    mention_type text not null,
    normalized_text text not null,
    segment_id text,
    start real,
    end real,
    timestamp text,
    text text
);
"""

FTS_SCHEMA_SQL = """
create virtual table if not exists transcript_segments_fts using fts5(
    podcast_id unindexed,
    episode_ref unindexed,
    segment_id unindexed,
    text
);
"""

FTS_UNAVAILABLE_WARNING = "FTS5 不可用，transcript search 將使用 LIKE fallback。"


def initialize_cache(db_path: str | Path | None = None) -> Path:
    """建立 SQLite metadata cache 與 schema。"""

    resolved_path = _resolve_db_path(db_path)
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(resolved_path) as connection:
            connection.executescript(SCHEMA_SQL)
            if is_fts5_available(resolved_path):
                connection.executescript(FTS_SCHEMA_SQL)
    except (OSError, sqlite3.Error) as exc:
        raise CacheInitializationError(f"初始化 SQLite cache 失敗：{exc}") from exc
    return resolved_path


def is_fts5_available(db_path: str | Path | None = None) -> bool:
    """檢查目前 SQLite runtime 是否支援 FTS5。"""

    try:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("create virtual table fts5_probe using fts5(text)")
    except sqlite3.Error:
        return False
    return True


def index_episode(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    db_path: str | Path | None = None,
) -> EpisodeIndexResult:
    """將單一 episode 的既有 artifacts 寫入 SQLite cache。"""

    resolved_path = initialize_cache(db_path)
    validation = validate_transcript(podcast_id, episode_ref)
    problems = list(validation.problems)
    warnings = list(validation.warnings)
    fts_available = is_fts5_available(resolved_path)
    if not fts_available:
        warnings.append(FTS_UNAVAILABLE_WARNING)
    transcript_paths = storage.find_transcript_asset_paths(podcast_id, episode_ref)
    title = episode_ref
    transcript_segment_count = 0
    segments: list[dict[str, Any]] = []
    transcript_payload: dict[str, Any] | None = None

    if validation.status in {"valid", "partial", "empty"} and transcript_paths is not None:
        try:
            transcript_payload = _load_json_object(transcript_paths.json_path)
            title = _optional_text(transcript_payload.get("title")) or episode_ref
            segments = _normalize_segments(transcript_payload.get("segments", []))
            transcript_segment_count = len(segments)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            problems.append(f"transcript JSON 無法索引：{exc}")
            segments = []
            transcript_segment_count = 0
    elif transcript_paths is not None:
        try:
            transcript_payload = _load_json_object(transcript_paths.json_path)
            title = _optional_text(transcript_payload.get("title")) or episode_ref
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            title = episode_ref

    summary_paths = _find_summary_paths(podcast_id, episode_ref)
    mention_paths = _find_mention_paths(podcast_id, episode_ref)
    mentions, mention_evidence = _load_mentions(
        mention_paths["json_path"],
        problems,
        warnings,
    )
    mention_count = len(mentions)

    try:
        with sqlite3.connect(resolved_path) as connection:
            if force:
                _delete_episode_index(connection, podcast_id, episode_ref)
            _upsert_episode(
                connection=connection,
                podcast_id=podcast_id,
                episode_ref=episode_ref,
                title=title,
                transcript_paths=transcript_paths,
                summary_paths=summary_paths,
                mention_paths=mention_paths,
                validation_status=validation.status,
                segment_count=validation.segment_count,
                last_segment_end_seconds=validation.last_segment_end_seconds,
            )
            _replace_segments(
                connection,
                podcast_id,
                episode_ref,
                segments,
                fts_available=fts_available,
            )
            _replace_mentions(connection, podcast_id, episode_ref, mentions, mention_evidence)
    except sqlite3.Error as exc:
        raise EpisodeIndexError(f"索引 episode 失敗：{podcast_id}/{episode_ref}: {exc}") from exc

    return EpisodeIndexResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        indexed=validation.status not in {"missing", "corrupt", "incomplete_outputs"} and not problems,
        transcript_segment_count=transcript_segment_count,
        mention_count=mention_count,
        problems=problems,
        warnings=warnings,
    )


def rebuild_cache(
    podcast_id: str | None = None,
    *,
    force: bool = False,
    db_path: str | Path | None = None,
) -> CacheRebuildResult:
    """掃描既有 artifacts 並重建 SQLite metadata cache。"""

    resolved_path = initialize_cache(db_path)
    episode_keys = _discover_episode_keys(podcast_id)
    indexed_episode_count = 0
    skipped_episode_count = 0
    problems: list[str] = []
    warnings: list[str] = []

    for discovered_podcast_id, episode_ref in sorted(episode_keys):
        try:
            result = index_episode(
                discovered_podcast_id,
                episode_ref,
                force=force,
                db_path=resolved_path,
            )
        except EpisodeIndexError as exc:
            skipped_episode_count += 1
            problems.append(str(exc))
            continue
        if result.indexed:
            indexed_episode_count += 1
        else:
            skipped_episode_count += 1
        problems.extend(result.problems)
        warnings.extend(result.warnings)

    return CacheRebuildResult(
        db_path=str(resolved_path),
        indexed_episode_count=indexed_episode_count,
        skipped_episode_count=skipped_episode_count,
        problems=problems,
        warnings=warnings,
    )


def _resolve_db_path(db_path: str | Path | None) -> Path:
    return Path(db_path) if db_path is not None else storage.cache_db_path()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root 必須是 object")
    return payload


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _normalize_segments(raw_segments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_segments, list):
        raise ValueError("segments 必須是 list")
    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments, start=1):
        if not isinstance(segment, dict):
            raise ValueError(f"segment {index} 必須是 object")
        start = _optional_float(segment.get("start"))
        end = _optional_float(segment.get("end"))
        text = str(segment.get("text", "")).strip()
        segments.append(
            {
                "id": segment.get("id", index),
                "start": start,
                "end": end,
                "timestamp": f"[{_format_clock(start)} - {_format_clock(end)}]",
                "text": text,
            }
        )
    return segments


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _format_clock(seconds: float | None) -> str:
    whole_seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _find_summary_paths(podcast_id: str, episode_ref: str) -> dict[str, Path | None]:
    summary_dir = storage.SUMMARIES_DIR / podcast_id
    semantic_matches = sorted(summary_dir.glob(f"{episode_ref}__*.semantic.md"))
    extractive_matches = [
        path for path in sorted(summary_dir.glob(f"{episode_ref}__*.md")) if not path.name.endswith(".semantic.md")
    ]
    return {
        "extractive_summary_path": extractive_matches[0] if extractive_matches else None,
        "semantic_summary_path": semantic_matches[0] if semantic_matches else None,
    }


def _find_mention_paths(podcast_id: str, episode_ref: str) -> dict[str, Path | None]:
    mention_dir = storage.MENTIONS_DIR / podcast_id
    matches = sorted(mention_dir.glob(f"{episode_ref}__*.mentions.json"))
    if not matches:
        return {"json_path": None, "markdown_path": None}
    json_path = matches[0]
    markdown_name = json_path.name.removesuffix(".mentions.json") + ".mentions.md"
    return {"json_path": json_path, "markdown_path": json_path.with_name(markdown_name)}


def _load_mentions(
    mentions_json_path: Path | None,
    problems: list[str],
    warnings: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if mentions_json_path is None:
        warnings.append("找不到 mentions JSON，略過 mention index。")
        return [], []
    try:
        payload = _load_json_object(mentions_json_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        problems.append(f"mentions JSON 無法索引：{exc}")
        return [], []
    raw_mentions = payload.get("mentions")
    if not isinstance(raw_mentions, list):
        problems.append("mentions JSON 的 mentions 必須是 list。")
        return [], []

    mentions: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for mention in raw_mentions:
        if not isinstance(mention, dict):
            continue
        mention_type = str(mention.get("type", "unknown"))
        normalized_text = str(mention.get("normalized_text", "")).strip()
        text = str(mention.get("text", "")).strip()
        if not normalized_text or not text:
            continue
        mentions.append(
            {
                "mention_type": mention_type,
                "text": text,
                "normalized_text": normalized_text,
                "count": int(mention.get("count", 0) or 0),
                "confidence": str(mention.get("confidence", "")),
            }
        )
        raw_evidence = mention.get("evidence", [])
        if not isinstance(raw_evidence, list):
            continue
        for evidence in raw_evidence:
            if not isinstance(evidence, dict):
                continue
            evidence_rows.append(
                {
                    "mention_type": mention_type,
                    "normalized_text": normalized_text,
                    "segment_id": str(evidence.get("segment_id", "")),
                    "start": _optional_float(evidence.get("start")),
                    "end": _optional_float(evidence.get("end")),
                    "timestamp": str(evidence.get("timestamp", "")),
                    "text": str(evidence.get("text", "")),
                }
            )
    return mentions, evidence_rows


def _delete_episode_index(connection: sqlite3.Connection, podcast_id: str, episode_ref: str) -> None:
    for table_name in ("transcript_segments", "mentions", "mention_evidence", "episodes"):
        connection.execute(
            f"delete from {table_name} where podcast_id = ? and episode_ref = ?",
            (podcast_id, episode_ref),
        )
    _delete_fts_segments(connection, podcast_id, episode_ref)


def _upsert_episode(
    *,
    connection: sqlite3.Connection,
    podcast_id: str,
    episode_ref: str,
    title: str,
    transcript_paths,
    summary_paths: dict[str, Path | None],
    mention_paths: dict[str, Path | None],
    validation_status: str,
    segment_count: int,
    last_segment_end_seconds: float | None,
) -> None:
    connection.execute(
        """
        insert or replace into episodes (
            podcast_id, episode_ref, title, published_at, duration, guid, link, audio_url,
            transcript_json_path, transcript_text_path, transcript_srt_path,
            extractive_summary_path, semantic_summary_path,
            mentions_json_path, mentions_markdown_path,
            transcript_status, segment_count, last_segment_end_seconds, updated_at
        )
        values (?, ?, ?, null, null, null, null, null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            podcast_id,
            episode_ref,
            title,
            str(transcript_paths.json_path) if transcript_paths else None,
            str(transcript_paths.text_path) if transcript_paths else None,
            str(transcript_paths.srt_path) if transcript_paths else None,
            _path_to_str(summary_paths["extractive_summary_path"]),
            _path_to_str(summary_paths["semantic_summary_path"]),
            _path_to_str(mention_paths["json_path"]),
            _path_to_str(mention_paths["markdown_path"]),
            validation_status,
            segment_count,
            last_segment_end_seconds,
            datetime.now(UTC).isoformat(),
        ),
    )


def _path_to_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _replace_segments(
    connection: sqlite3.Connection,
    podcast_id: str,
    episode_ref: str,
    segments: list[dict[str, Any]],
    *,
    fts_available: bool,
) -> None:
    connection.execute(
        "delete from transcript_segments where podcast_id = ? and episode_ref = ?",
        (podcast_id, episode_ref),
    )
    connection.executemany(
        """
        insert into transcript_segments (podcast_id, episode_ref, segment_id, start, end, timestamp, text)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                podcast_id,
                episode_ref,
                str(segment["id"]),
                segment["start"],
                segment["end"],
                segment["timestamp"],
                segment["text"],
            )
            for segment in segments
        ],
    )
    _replace_fts_segments(connection, podcast_id, episode_ref, segments, fts_available=fts_available)


def _replace_fts_segments(
    connection: sqlite3.Connection,
    podcast_id: str,
    episode_ref: str,
    segments: list[dict[str, Any]],
    *,
    fts_available: bool,
) -> None:
    if not fts_available:
        return
    _delete_fts_segments(connection, podcast_id, episode_ref)
    connection.executemany(
        """
        insert into transcript_segments_fts (podcast_id, episode_ref, segment_id, text)
        values (?, ?, ?, ?)
        """,
        [
            (
                podcast_id,
                episode_ref,
                str(segment["id"]),
                segment["text"],
            )
            for segment in segments
        ],
    )


def _delete_fts_segments(connection: sqlite3.Connection, podcast_id: str, episode_ref: str) -> None:
    try:
        connection.execute(
            "delete from transcript_segments_fts where podcast_id = ? and episode_ref = ?",
            (podcast_id, episode_ref),
        )
    except sqlite3.Error:
        return


def _replace_mentions(
    connection: sqlite3.Connection,
    podcast_id: str,
    episode_ref: str,
    mentions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> None:
    connection.execute(
        "delete from mentions where podcast_id = ? and episode_ref = ?",
        (podcast_id, episode_ref),
    )
    connection.execute(
        "delete from mention_evidence where podcast_id = ? and episode_ref = ?",
        (podcast_id, episode_ref),
    )
    connection.executemany(
        """
        insert into mentions (podcast_id, episode_ref, mention_type, text, normalized_text, count, confidence)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                podcast_id,
                episode_ref,
                mention["mention_type"],
                mention["text"],
                mention["normalized_text"],
                mention["count"],
                mention["confidence"],
            )
            for mention in mentions
        ],
    )
    connection.executemany(
        """
        insert into mention_evidence (
            podcast_id, episode_ref, mention_type, normalized_text,
            segment_id, start, end, timestamp, text
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                podcast_id,
                episode_ref,
                evidence["mention_type"],
                evidence["normalized_text"],
                evidence["segment_id"],
                evidence["start"],
                evidence["end"],
                evidence["timestamp"],
                evidence["text"],
            )
            for evidence in evidence_rows
        ],
    )


def _discover_episode_keys(podcast_id: str | None) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    candidate_roots = [
        storage.TRANSCRIPTS_DIR,
        storage.SUMMARIES_DIR,
        storage.MENTIONS_DIR,
    ]
    for root in candidate_roots:
        if podcast_id is not None:
            podcast_dirs = [root / podcast_id]
        else:
            podcast_dirs = [path for path in root.iterdir()] if root.exists() else []
        for podcast_dir in podcast_dirs:
            if not podcast_dir.exists() or not podcast_dir.is_dir():
                continue
            for path in podcast_dir.iterdir():
                episode_ref = _episode_ref_from_artifact_name(path.name)
                if episode_ref is not None:
                    keys.add((podcast_dir.name, episode_ref))
    return keys


_ARTIFACT_NAME_SUFFIXES = (".json", ".md", ".srt", ".txt")


def _episode_ref_from_artifact_name(name: str) -> str | None:
    """Name an episode only from a real artifact, never a transient sibling.

    Compensating writers stage and quarantine beside their target using a
    leading dot and a trailing marker (``.part``, ``.superseded``).  Those share
    the ``<ref>__<slug>`` stem, so matching on the stem alone would invent an
    episode reference that no storage helper can resolve.
    """

    if name.startswith(".") or not name.endswith(_ARTIFACT_NAME_SUFFIXES):
        return None
    if "__" not in name:
        return None
    prefix = name.split("__", 1)[0]
    return prefix or None
