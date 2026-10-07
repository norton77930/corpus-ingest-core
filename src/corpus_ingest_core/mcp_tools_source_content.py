"""Append-only read evidence tool; behavior stays in Core."""
from __future__ import annotations
from typing import Annotated, Any
from pydantic import Field
from . import source_content_query
from .mcp_runtime import mcp, tool_error, tool_success

_MESSAGES = {
    'invalid_request': 'Use one explicit prepared source and valid bounded query arguments.',
    'source_missing': 'The prepared transcript is missing; no preparation was started.',
    'source_ambiguous': 'Multiple transcript variants exist; operator inspection is required.',
    'unsafe_source': 'The transcript could not be read safely; no content was returned.',
    'source_invalid': 'The transcript identity or content structure is invalid.',
    'source_incomplete': 'The transcript is incomplete or has recovery markers; no cleanup was performed.',
    'source_empty': 'The transcript contains no usable segments.',
    'source_changed': 'The transcript changed; inspect again and restart retrieval against one version.',
    'invalid_cursor': 'The continuation is invalid for this source version and query scope.',
    'internal_error': 'Source content inspection failed; no content was returned.',
}


@mcp.tool()
def query_source_content(
    podcast_id: str, episode_ref: str, action: str = 'inspect', expected_source_version: str = '',
    query: str = '', start_seconds: Annotated[int, Field(strict=True)] | Annotated[float, Field(strict=True)] | None = None,
    end_seconds: Annotated[int, Field(strict=True)] | Annotated[float, Field(strict=True)] | None = None, cursor: str = '',
    limit: Annotated[int, Field(strict=True)] = 40, max_chars: Annotated[int, Field(strict=True)] = 8000,
) -> dict[str, Any]:
    """Inspect/read/search one prepared RSS/YouTube/X transcript offline, independent of cache. Read/search require inspected source_version; follow next_cursor with unchanged scope. Literal search is not semantic. Returned text can be processed/billed by the host AI; this reader invokes no provider or preparation."""
    try:
        return tool_success(source_content_query.query_source_content(
            podcast_id, episode_ref, action=action, expected_source_version=expected_source_version,
            query=query, start_seconds=start_seconds, end_seconds=end_seconds,
            cursor=cursor, limit=limit, max_chars=max_chars))
    except Exception as error:
        reason = getattr(error, 'reason', None) if isinstance(error, source_content_query.SourceContentError) else None
        if type(reason) is not str or reason not in _MESSAGES:
            reason = 'internal_error'
        result = tool_error(_MESSAGES[reason], 'SourceContentError' if isinstance(error, source_content_query.SourceContentError) else 'InternalError')
        result['reason'] = reason
        return result