"""Append-only read-query Tool29 for lecture lineage."""
from __future__ import annotations
from typing import Any
from . import study_guide_bundle
from .mcp_runtime import mcp,tool_error,tool_success

@mcp.tool()
def inspect_study_guide_lineage(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Read-only offline lecture versus recorded summary comparison. No generation, backfill, repair or upstream transcript-freshness claim."""
    try:
        return tool_success(study_guide_bundle.inspect_study_guide_lineage(podcast_id,episode_ref))
    except ValueError:
        return tool_error(study_guide_bundle.LINEAGE_INVALID_IDENTITY_MESSAGE,"ValueError")
    except Exception:
        return tool_error(study_guide_bundle.LINEAGE_QUERY_ERROR_MESSAGE,"InternalError")
