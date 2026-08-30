"""MCP tool group: X video ingest (Tool 23).

Imported after Tools 1-22 and before ``mcp_tools_youtube_video``. New groups
still append last so earlier slots stay put.

``ingest_x_video`` exposes Spec 036 ``run_x_video_ingest``. Preview is
zero-write and resolves public metadata over the network — it is not the
corpus runner zero-network dry-run.
"""

from __future__ import annotations

from typing import Any

from . import mcp_runtime, x_video_ingest
from .errors import PodcastIngestCoreError
from .mcp_runtime import mcp, tool_action_plan, tool_error

X_VIDEO_CACHE_STALE_WARNING = x_video_ingest.CACHE_STALE_WARNING
NOT_INVESTMENT_ADVICE = "Research framework only: no buy/sell/hold, target price, or guaranteed return."
PREVIEW_NETWORK_SCOPE = "public_metadata_only"


@mcp.tool()
def ingest_x_video(
    url: str = "",
    confirm: bool = False,
    title: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Side-effect tool: confirm=false is a zero-write preview that still reads public metadata over the network. No api_cost_ack: this tool calls no LLM."""

    inputs = {
        "url": url,
        "title": title,
        "force": force,
    }
    if not confirm:
        try:
            result = x_video_ingest.run_x_video_ingest(
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
            tool_name="ingest_x_video",
            action=(
                "Resolve public X video metadata and plan corpus writes. Preview is zero-write but not zero-network."
            ),
            inputs=inputs,
            writes=result.planned_writes,
            risks=[
                "Preview reads public metadata over the network and writes nothing; it is not a corpus zero-network dry-run",
                "Confirmed execution downloads with a guest token, extracts audio, transcribes locally, and writes corpus artifacts",
                "The source video is never written under data/",
                X_VIDEO_CACHE_STALE_WARNING,
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
        lambda: x_video_ingest.run_x_video_ingest(
            url,
            confirm=True,
            title=title,
            force=force,
        ),
        warnings=[X_VIDEO_CACHE_STALE_WARNING, NOT_INVESTMENT_ADVICE],
    )
