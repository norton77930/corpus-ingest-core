"""Bounded, offline evidence retrieval from one prepared transcript.

No index, provider, media workflow or persisted query state is involved.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from typing import Any

from . import storage
from .preparation_transcription import actual
from .secure_local_snapshot import secure_directory_names, secure_read_bytes

_MAX_BYTES = 16 * 1024 * 1024
_MAX_SEGMENTS = 100_000


class SourceContentError(ValueError):
    """Finite public diagnosis; never contains artifact bytes or paths."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> None:
    raise SourceContentError(reason)


def _number(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _bounded_int(value: Any, maximum: int) -> bool:
    return type(value) is int and 1 <= value <= maximum


def _request(podcast_id, episode_ref, action, version, query, start, end, cursor, limit, max_chars):
    if (type(podcast_id) is not str or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}', podcast_id)
        or type(episode_ref) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', episode_ref)
        or episode_ref.casefold() in {'latest', 'next', 'all', 'batch'}
        or type(action) is not str or action not in {'inspect', 'read', 'search'}
        or type(query) is not str or len(query) > 256 or type(version) is not str
        or type(cursor) is not str or len(cursor) > 1024
        or not _bounded_int(limit, 100) or not _bounded_int(max_chars, 12000)
        or (start is not None and not _number(start)) or (end is not None and not _number(end))
        or (end is not None and end <= (start or 0))):
        _fail('invalid_request')
    if action == 'inspect':
        if version or query or cursor or start is not None or end is not None or limit != 40 or max_chars != 8000:
            _fail('invalid_request')
    elif not re.fullmatch(r'[a-f0-9]{64}', version):
        _fail('invalid_request')
    if (action == 'search' and not query.strip()) or (action != 'search' and query):
        _fail('invalid_request')


def _missing(path) -> bool:
    try:
        path.lstat()
        return False
    except FileNotFoundError:
        return True
    except OSError:
        return False


def _load(podcast_id: str, episode_ref: str):
    root = storage.TRANSCRIPTS_DIR
    directory = root / podcast_id
    names = secure_directory_names(root, directory, max_entries=4096)
    if names is None:
        _fail('source_missing' if _missing(root) or _missing(directory) else 'unsafe_source')
    prefix = episode_ref + '__'
    relevant = [name for name in names if name.startswith(prefix)]
    if any(name.endswith(('.part', '.old')) or '.wfderive.' in name for name in relevant):
        _fail('source_incomplete')
    candidates = [name for name in relevant if name.endswith('.json')]
    if not candidates:
        _fail('source_incomplete' if relevant else 'source_missing')
    if len(candidates) > 8:
        _fail('unsafe_source')
    if len(candidates) != 1:
        _fail('source_ambiguous')
    path = directory / candidates[0]
    raw = secure_read_bytes(root, path, max_bytes=_MAX_BYTES, require_single_link=True)
    if raw is None:
        _fail('unsafe_source')
    try:
        payload = json.loads(raw.decode('utf-8'), parse_constant=lambda value: _fail('source_invalid'))
    except (UnicodeDecodeError, ValueError, RecursionError):
        _fail('source_invalid')
    if not isinstance(payload, dict):
        _fail('source_invalid')
    title = payload.get('title')
    if (payload.get('podcast_id') != podcast_id or payload.get('episode_ref') != episode_ref
        or type(title) is not str or not title.strip() or len(title) > 1024):
        _fail('source_invalid')
    paths = storage.transcript_asset_paths(podcast_id, episode_ref, title)
    if paths.json_path != path:
        _fail('source_invalid')
    warnings = []
    if 'completed' in payload and payload['completed'] is not True:
        _fail('source_incomplete')
    if 'completed' not in payload:
        warnings.append('legacy_completion_unknown')
    for companion in (paths.text_path, paths.srt_path):
        if _missing(companion):
            _fail('source_incomplete')
        body = secure_read_bytes(root, companion, max_bytes=_MAX_BYTES, require_single_link=True)
        if body is None:
            _fail('unsafe_source')
        try:
            if not body.decode('utf-8').strip():
                _fail('source_incomplete')
        except UnicodeDecodeError:
            _fail('source_invalid')
    segments = payload.get('segments')
    if not isinstance(segments, list) or len(segments) > _MAX_SEGMENTS:
        _fail('source_invalid')
    if not segments:
        _fail('source_empty')
    if 'segment_count' in payload and (type(payload['segment_count']) is not int or payload['segment_count'] != len(segments)):
        _fail('source_invalid')
    normalized = []
    previous = 0.0
    for ordinal, segment in enumerate(segments):
        if not isinstance(segment, dict):
            _fail('source_invalid')
        start, end, text = segment.get('start'), segment.get('end'), segment.get('text')
        if (not _number(start) or not _number(end) or end < start or start < previous
            or type(text) is not str or not text.strip()):
            _fail('source_invalid')
        identifier = segment.get('id')
        if not ((type(identifier) is str and len(identifier) <= 128)
                or (type(identifier) is int and abs(identifier) <= 2**53)):
            identifier = None
        normalized.append(dict(ordinal=ordinal, segment_id=identifier, start=start, end=end, text=text))
        previous = start
    # Reject discovery changes/recovery markers and JSON replacement during the invocation.
    if (secure_directory_names(root, directory, max_entries=4096) != names
        or secure_read_bytes(root, path, max_bytes=_MAX_BYTES, require_single_link=True) != raw):
        _fail('source_changed')
    language = payload.get('language')
    if type(language) is not str or len(language) > 32:
        language = None
    metadata = dict(podcast_id=podcast_id, episode_ref=episode_ref, title=title, language=language,
                    source_version=hashlib.sha256(raw).hexdigest(), segment_count=len(normalized),
                    start_seconds=min(s['start'] for s in normalized), end_seconds=max(s['end'] for s in normalized),
                    actual_transcription=actual(payload), warnings=warnings,
                    read_only=True, network_access=False)
    return metadata, normalized


def _in_range(segment, start, end):
    lower = start if start is not None else 0
    if segment['end'] == segment['start']:
        return segment['start'] >= lower and (end is None or segment['start'] < end)
    return segment['end'] > lower and (end is None or segment['start'] < end)


def _binding(metadata, action, query, start, end):
    fields = [metadata['podcast_id'], metadata['episode_ref'], metadata['source_version'], action, query,
              start, end]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def _encode(binding, index, offset):
    raw = json.dumps([binding, index, offset], separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def _decode(cursor, binding, selected):
    if not cursor:
        return 0, 0
    try:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', cursor):
            _fail('invalid_cursor')
        values = json.loads(base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True))
        if (not isinstance(values, list) or len(values) != 3 or values[0] != binding
            or type(values[1]) is not int or type(values[2]) is not int
            or not 0 <= values[1] < len(selected) or not 0 <= values[2] < len(selected[values[1]]['text'])):
            _fail('invalid_cursor')
        return values[1], values[2]
    except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
        _fail('invalid_cursor')


def query_source_content(
    podcast_id: str, episode_ref: str, action: str = 'inspect', expected_source_version: str = '',
    query: str = '', start_seconds: float | None = None, end_seconds: float | None = None,
    cursor: str = '', limit: int = 40, max_chars: int = 8000,
) -> dict[str, Any]:
    """Read one prepared source; host-model use of evidence is outside this reader."""
    _request(podcast_id, episode_ref, action, expected_source_version, query,
             start_seconds, end_seconds, cursor, limit, max_chars)
    metadata, segments = _load(podcast_id, episode_ref)
    if action == 'inspect':
        return metadata
    if metadata['source_version'] != expected_source_version:
        _fail('source_changed')
    scope = [s for s in segments if _in_range(s, start_seconds, end_seconds)]
    selected = [s for s in scope if query.casefold() in s['text'].casefold()] if action == 'search' else scope
    binding = _binding(metadata, action, query, start_seconds, end_seconds)
    index, offset = _decode(cursor, binding, selected)
    page, remaining = [], max_chars
    while index < len(selected) and len(page) < limit and remaining:
        segment = selected[index]
        text = segment['text'][offset:offset + remaining]
        complete = offset + len(text) == len(segment['text'])
        page.append(dict(segment, text=text, text_offset=offset, text_complete=complete))
        remaining -= len(text)
        if complete:
            index += 1
            offset = 0
        else:
            offset += len(text)
    exhausted = index == len(selected)
    result = dict(metadata, action=action, segments=page,
                  next_cursor=None if exhausted else _encode(binding, index, offset),
                  coverage=dict(scope='full_source' if start_seconds is None and end_seconds is None else 'time_range',
                                selected_segments=len(selected), returned_ordinals=[s['ordinal'] for s in page],
                                scope_exhausted=exhausted, complete=not cursor and exhausted, truncated=not exhausted))
    if action == 'search':
        result['search'] = dict(mode='literal_keyword', query=query, scanned_segments=len(scope), total_matches=len(selected),
                                full_source_understanding=False)
    return result