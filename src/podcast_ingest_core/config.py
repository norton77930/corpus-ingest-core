from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

from .models import PodcastProfile


DEFAULT_CONFIG_PATH = Path("config/podcasts.yaml")
_SAFE_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_podcast_profiles(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, PodcastProfile]:
    """載入所有 podcast profiles。"""

    config_path = Path(path)
    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    podcasts = raw_config.get("podcasts")

    if isinstance(podcasts, dict):
        podcast_items = []
        for podcast_id, profile in podcasts.items():
            if not isinstance(profile, dict):
                raise ValueError("podcasts mapping 的每個值都必須是 mapping。")
            podcast_items.append({**profile, "podcast_id": podcast_id})
    elif isinstance(podcasts, list):
        podcast_items = podcasts
    else:
        raise ValueError("config/podcasts.yaml 必須包含 podcasts mapping 或清單。")

    profiles: dict[str, PodcastProfile] = {}
    for item in podcast_items:
        profile = _parse_profile(item)
        if profile.podcast_id in profiles:
            raise ValueError(f"podcast_id 重複：{profile.podcast_id}")
        profiles[profile.podcast_id] = profile

    return profiles


def load_podcast_profile(
    podcast_id: str, path: str | Path = DEFAULT_CONFIG_PATH
) -> PodcastProfile:
    """載入單一 podcast profile。"""

    profiles = load_podcast_profiles(path)
    try:
        return profiles[podcast_id]
    except KeyError as exc:
        raise KeyError(f"找不到 podcast_id：{podcast_id}") from exc


def _parse_profile(item: Any) -> PodcastProfile:
    if not isinstance(item, dict):
        raise ValueError("podcasts 的每個項目都必須是 mapping。")

    podcast_id = _required_text(item, "podcast_id")
    if not _SAFE_SLUG_PATTERN.fullmatch(podcast_id):
        raise ValueError("podcast_id 必須是小寫 slug，只允許 a-z、0-9 與 -。")

    return PodcastProfile(
        podcast_id=podcast_id,
        display_name=_required_text(item, "display_name"),
        rss_url=_required_text(item, "rss_url"),
        language=_required_text(item, "language"),
        default_episode_prefix=_required_text(item, "default_episode_prefix"),
    )


def _required_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} 必須是非空字串。")
    return value.strip()
