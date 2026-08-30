from __future__ import annotations

import re
from typing import Any

import feedparser

from .config import require_rss_profile
from .errors import EpisodeNotFoundError
from .models import Episode, PodcastProfile


def list_episodes(podcast_id: str, limit: int = 10) -> list[Episode]:
    """從 podcast RSS 列出 episodes。"""

    profile = require_rss_profile(podcast_id)
    if limit < 1:
        raise ValueError("limit must be greater than 0.")

    rss_url, episode_prefix = _rss_feed_fields(profile)
    return _read_episodes(profile.podcast_id, rss_url, episode_prefix)[:limit]


def get_episode(podcast_id: str, episode_ref: str) -> Episode:
    """從 podcast RSS 取得單一 episode。"""

    if not episode_ref:
        raise ValueError("episode_ref must not be empty.")

    profile = require_rss_profile(podcast_id)
    rss_url, episode_prefix = _rss_feed_fields(profile)
    episodes = _read_episodes(profile.podcast_id, rss_url, episode_prefix)
    if episode_ref.lower() == "latest":
        if episodes:
            return episodes[0]
        raise EpisodeNotFoundError(f"No latest episode for podcast_id={podcast_id}.")

    requested_ref = episode_ref.casefold()
    for episode in episodes:
        if episode.episode_ref.casefold() == requested_ref:
            return episode

    raise EpisodeNotFoundError(f"No episode {episode_ref} for podcast_id={podcast_id}")


def _rss_feed_fields(profile: PodcastProfile) -> tuple[str, str]:
    """取出 RSS 讀取真正需要的兩個欄位，缺一就當場說清楚。

    ``config._parse_profile`` 對 RSS 來源是用 ``_required_text`` 讀 ``rss_url``
    與 ``default_episode_prefix``，所以走設定檔的路徑不會是 None；但
    ``PodcastProfile`` 的型別允許 None（非 RSS 來源沒有 feed），手工建構或
    未來新增的載入路徑就可能漏掉。與其把 None 餵進 ``feedparser.parse``、
    換來一個沒有 entries 的空 feed 和「找不到 episode」這種誤導訊息，不如在
    這裡直接指出是 profile 缺欄位。
    """

    if profile.rss_url is None or profile.default_episode_prefix is None:
        raise ValueError(
            f"{profile.podcast_id} is an RSS source, but its profile is missing rss_url or default_episode_prefix."
        )
    return profile.rss_url, profile.default_episode_prefix


def _read_episodes(podcast_id: str, rss_url: str, episode_prefix: str) -> list[Episode]:
    parsed_feed = feedparser.parse(rss_url)
    return [
        _normalize_episode(podcast_id, episode_prefix, entry, index)
        for index, entry in enumerate(_get(parsed_feed, "entries", []))
    ]


def _normalize_episode(podcast_id: str, episode_prefix: str, entry: Any, index: int) -> Episode:
    title = str(_get(entry, "title", "")).strip()
    link = _optional_text(_get(entry, "link"))
    return Episode(
        podcast_id=podcast_id,
        episode_ref=_episode_ref_from_title(title, episode_prefix) or f"item-{index + 1}",
        title=title,
        audio_url=_audio_url(entry),
        published_at=_optional_text(_get(entry, "published")) or _optional_text(_get(entry, "updated")),
        description=_optional_text(_get(entry, "description")) or _optional_text(_get(entry, "summary")),
        source_url=link,
        duration=_optional_text(_get(entry, "itunes_duration")) or _optional_text(_get(entry, "duration")),
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
