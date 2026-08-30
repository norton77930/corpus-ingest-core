"""MCP tool group: YouTube video ingest (Tool 24).

Imported last by the ``mcp_server`` facade so Tools 1-23 keep their slots.

Preview is zero-write and resolves public metadata over the network — it is
not the corpus runner zero-network dry-run.
"""

from __future__ import annotations

from typing import Any

from . import mcp_runtime, youtube_video_ingest
from .errors import PodcastIngestCoreError
from .mcp_runtime import mcp, tool_action_plan, tool_error

YOUTUBE_VIDEO_CACHE_STALE_WARNING = youtube_video_ingest.CACHE_STALE_WARNING
NOT_INVESTMENT_ADVICE = "Research framework only: no buy/sell/hold, target price, or guaranteed return."
PREVIEW_NETWORK_SCOPE = "public_metadata_only"


@mcp.tool()
def ingest_youtube_video(
    url: str = "",
    confirm: bool = False,
    title: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Side-effect tool：confirm=false 是 preview（零寫入，會讀公開 metadata）。"""

    inputs = {
        "url": url,
        "title": title,
        "force": force,
    }
    if not confirm:
        try:
            result = youtube_video_ingest.run_youtube_video_ingest(
                url,
                confirm=False,
                title=title,
                force=force,
            )
        except PodcastIngestCoreError as exc:
            return tool_error(mcp_runtime._safe_error_message(exc), type(exc).__name__)
        except ValueError as exc:
            return tool_error(str(exc), "ValueError")
        except Exception as exc:
            return tool_error(mcp_runtime._redact_text(str(exc), None), type(exc).__name__)
        response = tool_action_plan(
            tool_name="ingest_youtube_video",
            action=(
                "Resolve public YouTube video metadata and plan corpus writes. "
                "Preview is zero-write but not zero-network."
            ),
            inputs=inputs,
            writes=result.planned_writes,
            risks=[
                "Preview reads public metadata over the network and writes nothing; it is not a corpus zero-network dry-run",
                "Confirmed execution downloads with a guest token, extracts audio, transcribes locally, and writes corpus artifacts",
                "The source video is never written under data/",
                YOUTUBE_VIDEO_CACHE_STALE_WARNING,
                NOT_INVESTMENT_ADVICE,
            ],
        )
        response["run_mode"] = result.run_mode
        response["network_read"] = True
        response["network_read_scope"] = PREVIEW_NETWORK_SCOPE
        response["not_investment_advice"] = result.not_investment_advice
        response["warnings"] = result.warnings
        return response

    return mcp_runtime._tool_call(
        lambda: youtube_video_ingest.run_youtube_video_ingest(
            url,
            confirm=True,
            title=title,
            force=force,
        ),
        warnings=[YOUTUBE_VIDEO_CACHE_STALE_WARNING, NOT_INVESTMENT_ADVICE],
    )
