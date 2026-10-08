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
    'source_changed': 'The source changed during inspection or does not match the pinned version. Stop this request; do not mix versions or automatically restart.',
    'invalid_cursor': 'The continuation is invalid for this source version and query scope.',
    'internal_error': 'Source content inspection failed; no content was returned.',
}

_DIAGNOSES = {
    ('invalid_request', 'inspect_arguments'): 'inspect 只接受 podcast_id、episode_ref；請省略其他查詢與分頁參數。',
    ('invalid_request', 'version_format'): 'expected_source_version must be exactly 64 lowercase hexadecimal characters copied unchanged from inspection; this is a parameter format error.',
    ('invalid_cursor', 'cursor_format'): 'Invalid cursor format; copy next_cursor unchanged from the last successful response, without constructing or editing it.',
    ('invalid_cursor', 'cursor_binding'): 'The cursor does not match this source version, query scope or continuation position; keep the original identity, action, query and time window.',
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
        diagnosis = getattr(error, 'diagnosis', None) if isinstance(error, source_content_query.SourceContentError) else None
        message = _DIAGNOSES.get((reason, diagnosis), _MESSAGES[reason]) if type(diagnosis) is str else _MESSAGES[reason]
        result = tool_error(message, 'SourceContentError' if isinstance(error, source_content_query.SourceContentError) else 'InternalError')
        result['reason'] = reason
        return result
