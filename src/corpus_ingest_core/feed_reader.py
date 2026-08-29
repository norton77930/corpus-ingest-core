from __future__ import annotations

from typing import Any
import re

import feedparser

from .config import require_rss_profile
from .errors import EpisodeNotFoundError
from .models import Episode


def list_episodes(podcast_id: str, limit: int = 10) -> list[Episode]:
    """從 podcast RSS 列出 episodes。"""

    profile = require_rss_profile(podcast_id)
    if limit < 1:
        raise ValueError("limit 必須大於 0。")

    return _read_episodes(profile.podcast_id, profile.rss_url, profile.default_episode_prefix)[
        :limit
    ]


def get_episode(podcast_id: str, episode_ref: str) -> Episode:
    """從 podcast RSS 取得單一 episode。"""

    if not episode_ref:
        raise ValueError("episode_ref 不可為空。")

    profile = require_rss_profile(podcast_id)
    episodes = _read_episodes(
        profile.podcast_id, profile.rss_url, profile.default_episode_prefix
    )
    if episode_ref.lower() == "latest":
        if episodes:
            return episodes[0]
        raise EpisodeNotFoundError(f"找不到 podcast_id={podcast_id} 的最新 episode。")

    requested_ref = episode_ref.casefold()
    for episode in episodes:
        if episode.episode_ref.casefold() == requested_ref:
            return episode

    raise EpisodeNotFoundError(f"找不到 podcast_id={podcast_id} 的 episode：{episode_ref}")


def _read_episodes(
    podcast_id: str, rss_url: str, episode_prefix: str
) -> list[Episode]:
    parsed_feed = feedparser.parse(rss_url)
    return [
        _normalize_episode(podcast_id, episode_prefix, entry, index)
        for index, entry in enumerate(_get(parsed_feed, "entries", []))
    ]


def _normalize_episode(
    podcast_id: str, episode_prefix: str, entry: Any, index: int
) -> Episode:
    title = str(_get(entry, "title", "")).strip()
    link = _optional_text(_get(entry, "link"))
    return Episode(
        podcast_id=podcast_id,
        episode_ref=_episode_ref_from_title(title, episode_prefix) or f"item-{index + 1}",
        title=title,
        audio_url=_audio_url(entry),
        published_at=_optional_text(_get(entry, "published"))
        or _optional_text(_get(entry, "updated")),
        description=_optional_text(_get(entry, "description"))
        or _optional_text(_get(entry, "summary")),
        source_url=link,
        duration=_optional_text(_get(entry, "itunes_duration"))
        or _optional_text(_get(entry, "duration")),
        guid=_optional_text(_get(entry, "id")) or _optional_text(_get(entry, "guid")),
        link=link,
    )


def _episode_ref_from_title(title: str, episode_prefix: str) -> str | None:
    match = re.search(rf"\b{re.escape(episode_prefix)}\s*(\d+)\b", title, re.IGNORECASE)
    if match is None:
        return None
    return f"{episode_prefix.upper()}{match.group(1)}"


def _audio_url(entry: Any) -> str | None:
    for collection_name in ("enclosures", "links"):
        for link in _get(entry, collection_name, []) or []:
            href = _optional_text(_get(link, "href"))
            if href is None:
                continue
            link_type = (_optional_text(_get(link, "type")) or "").casefold()
            rel = (_optional_text(_get(link, "rel")) or "").casefold()
            if link_type.startswith("audio/") or rel == "enclosure":
                return href
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _get(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)
