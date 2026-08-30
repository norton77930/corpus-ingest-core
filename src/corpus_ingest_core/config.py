from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .errors import UnsupportedSourceTypeError
from .local_env_names import CONFIG_ENV, read_env
from .models import PodcastProfile
from .summary_profiles import UNSET as _SUMMARY_PROFILE_UNSET
from .summary_profiles import resolve_summary_profile

# Same shape as storage.DATA_DIR: an operator can point the profile registry
# somewhere gitignored instead of editing the committed config. That matters
# because tests/test_contracts.py asserts the exact profile set of the
# committed file -- a deliberate guard against committing a personal profile
# by accident -- while a live confirm (spec 039) needs a profile registered
# first. Without this the only route was edit-run-remember-to-revert.
#
# Read at import time, so a subprocess is the only way to exercise it; see
# tests/test_data_dir_fixture_contract.py.
DEFAULT_CONFIG_PATH = Path(read_env(CONFIG_ENV) or "config/podcasts.yaml")
RSS_SOURCE_TYPE = "rss"
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


def load_podcast_profile(podcast_id: str, path: str | Path = DEFAULT_CONFIG_PATH) -> PodcastProfile:
    """載入單一 podcast profile。"""

    profiles = load_podcast_profiles(path)
    try:
        return profiles[podcast_id]
    except KeyError as exc:
        raise KeyError(f"找不到 podcast_id：{podcast_id}") from exc


def require_rss_profile(podcast_id: str, path: str | Path = DEFAULT_CONFIG_PATH) -> PodcastProfile:
    """載入 profile，並確認它確實是 RSS 來源。

    RSS 專用入口（``list_episodes`` / ``get_episode`` / ``download_audio``）對
    非 RSS 來源沒有意義。在這裡明確拒絕，呼叫端才會拿到「為什麼不適用」，
    而不是在 feedparser 深處因為 ``rss_url`` 是 None 而失敗。
    """

    profile = load_podcast_profile(podcast_id, path)
    if profile.source_type != RSS_SOURCE_TYPE:
        ingest_hint = (
            "請改用 scripts/run_youtube_video_ingest.py。"
            if profile.source_type == "yt-video"
            else "請改用該來源自己的擷取流程。"
        )
        raise UnsupportedSourceTypeError(
            f"{podcast_id} 的 source_type 是 {profile.source_type}，不是 RSS 來源。"
            "list_episodes、get_episode 與 download_audio 只適用於 RSS podcast；"
            f"{ingest_hint}"
        )
    return profile


def _parse_profile(item: Any) -> PodcastProfile:
    if not isinstance(item, dict):
        raise ValueError("podcasts 的每個項目都必須是 mapping。")

    podcast_id = _required_text(item, "podcast_id")
    if not _SAFE_SLUG_PATTERN.fullmatch(podcast_id):
        raise ValueError("podcast_id 必須是小寫 slug，只允許 a-z、0-9 與 -。")

    source_type = _optional_text(item, "source_type") or RSS_SOURCE_TYPE
    is_rss = source_type == RSS_SOURCE_TYPE

    # 刻意不走 _optional_text：它會把 `summary_profile: 123` 靜默變成 None。
    # 也刻意用哨兵而非 None 當預設，因為 YAML 的 `summary_profile:` 是操作者
    # 寫了 key 卻留空，和完全沒寫這個 key 是兩件事；後者才該回退到預設。
    summary_profile = resolve_summary_profile(item.get("summary_profile", _SUMMARY_PROFILE_UNSET)).name

    return PodcastProfile(
        podcast_id=podcast_id,
        display_name=_required_text(item, "display_name"),
        rss_url=_required_text(item, "rss_url") if is_rss else _optional_text(item, "rss_url"),
        language=_required_text(item, "language"),
        default_episode_prefix=(
            _required_text(item, "default_episode_prefix") if is_rss else _optional_text(item, "default_episode_prefix")
        ),
        source_type=source_type,
        summary_profile=summary_profile,
    )


def _required_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} 必須是非空字串。")
    return value.strip()


def _optional_text(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()
