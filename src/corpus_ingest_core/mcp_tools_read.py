"""MCP tool group: read-only tools 1-6 (registration order is import order).

Tools: list_episodes, get_episode, validate_transcript, search_transcripts,
search_mentions, rebuild_cache. Registered on import via ``mcp_runtime.mcp``;
``mcp_server`` (the facade) controls group import order.
"""

from __future__ import annotations

from typing import Any

from . import cache as cache_module
from . import feed_reader, mcp_runtime, validator
from . import search as search_module
from .mcp_runtime import mcp, tool_error
from .models import Episode


@mcp.tool()
def list_episodes(podcast_id: str = "gooaye", limit: int = 10) -> dict[str, Any]:
    """Read-only tool: list one podcast's recent episodes. Never returns the full audio_url."""

    return mcp_runtime._tool_call(
        lambda: [
            _episode_to_safe_dict(episode)
            for episode in feed_reader.list_episodes(podcast_id, mcp_runtime._clamp_limit(limit))
        ]
    )


@mcp.tool()
def get_episode(podcast_id: str = "gooaye", episode_ref: str = "latest") -> dict[str, Any]:
    """Read-only tool: look up one podcast episode's metadata. Accepts latest and a case-insensitive EP ref."""

    return mcp_runtime._tool_call(lambda: _episode_to_safe_dict(feed_reader.get_episode(podcast_id, episode_ref)))


@mcp.tool()
def validate_transcript(podcast_id: str = "gooaye", episode_ref: str = "latest") -> dict[str, Any]:
    """Read-only tool: report whether the existing transcript artifacts are complete, valid, or likely partial."""

    return mcp_runtime._tool_call(lambda: validator.validate_transcript(podcast_id, episode_ref))


@mcp.tool()
def search_transcripts(
    query: str,
    podcast_id: str | None = "gooaye",
    limit: int = 10,
    search_mode: str = "auto",
    context_segments: int = 0,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """Read-only tool: search transcript segments in the SQLite cache. Never rebuilds the cache automatically."""

    if not query.strip():
        return tool_error("query must not be empty.", "ValueError")
    return mcp_runtime._tool_call(
        lambda: search_module.search_transcripts(
            query=query,
            podcast_id=podcast_id,
            limit=mcp_runtime._clamp_limit(limit),
            search_mode=search_mode,
            context_segments=mcp_runtime._clamp_context_segments(context_segments),
            case_sensitive=case_sensitive,
        )
    )


@mcp.tool()
def search_mentions(
    query: str,
    podcast_id: str | None = "gooaye",
    mention_type: str | None = None,
    limit: int = 10,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """Read-only tool: search deterministic mentions and their timestamp evidence in the SQLite cache."""

    if not query.strip():
        return tool_error("query must not be empty.", "ValueError")
    return mcp_runtime._tool_call(
        lambda: search_module.search_mentions(
            query=query,
            podcast_id=podcast_id,
            mention_type=mention_type,
            limit=mcp_runtime._clamp_limit(limit),
            case_sensitive=case_sensitive,
        )
    )


@mcp.tool()
def rebuild_cache(podcast_id: str | None = None, force: bool = False) -> dict[str, Any]:
    """Maintenance tool: rebuild the SQLite cache. Indexes existing artifacts only: no download, no transcription, no summary."""

    return mcp_runtime._tool_call(lambda: cache_module.rebuild_cache(podcast_id=podcast_id, force=force))


def _episode_to_safe_dict(episode: Episode) -> dict[str, Any]:
    return {
        "podcast_id": episode.podcast_id,
        "episode_ref": episode.episode_ref,
        "title": episode.title,
        "published_at": episode.published_at,
        "duration": episode.duration,
        "guid": episode.guid,
        "link": episode.link,
        "audio_url_present": bool(episode.audio_url),
    }
