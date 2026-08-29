"""MCP tool group: verified-report read-query tools 17-21 (import order = registration).

Tools: query_verified_research_report_catalog,
revalidate_verified_research_report_sources,
query_verified_research_report_coverage,
suggest_historical_verified_report_next_step,
list_verified_report_gap_backlog. Thin dispatchers over the per-spec adapter
modules; read-only, offline, no confirm/ack.
"""

from __future__ import annotations

from typing import Any

from . import (
    mcp_historical_verified_report_path,
    mcp_verified_report_gap_backlog,
    mcp_verified_research_report_catalog,
    mcp_verified_research_report_coverage,
    mcp_verified_research_report_source_revalidation,
)
from .mcp_runtime import mcp, tool_success


@mcp.tool()
def query_verified_research_report_catalog(
    action: str = "list",
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    source_digest: str | None = None,
    query: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List, search, or inspect read-only verified research report bundles."""

    return mcp_verified_research_report_catalog.dispatch(
        success=tool_success,
        action=action,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        source_digest=source_digest,
        query=query,
        limit=limit,
    )


@mcp.tool()
def revalidate_verified_research_report_sources(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> dict[str, Any]:
    """Revalidate one exact verified-report bundle's local source metadata."""

    return mcp_verified_research_report_source_revalidation.dispatch(
        success=tool_success,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        source_digest=source_digest,
    )


@mcp.tool()
def query_verified_research_report_coverage(
    podcast_id: str,
    has_bundle: bool | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List episode-centric coverage of local verified research report bundles."""

    return mcp_verified_research_report_coverage.dispatch(
        success=tool_success,
        podcast_id=podcast_id,
        has_bundle=has_bundle,
        limit=limit,
    )


@mcp.tool()
def suggest_historical_verified_report_next_step(
    podcast_id: str,
    episode_ref: str,
) -> dict[str, Any]:
    """Suggest one next human-gated step for a named historical episode."""

    return mcp_historical_verified_report_path.dispatch(
        success=tool_success,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
    )


@mcp.tool()
def list_verified_report_gap_backlog(
    podcast_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    """List inventory episodes missing a verified research report bundle."""

    return mcp_verified_report_gap_backlog.dispatch(
        success=tool_success,
        podcast_id=podcast_id,
        limit=limit,
    )
