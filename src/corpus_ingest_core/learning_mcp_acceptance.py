"""Read-only MCP delivery verification; never a host or content-quality certificate."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

from .preparation_transcription import InvalidTranscriptionSettings, parse
from .secure_local_snapshot import secure_read_bytes

REQUIRED_TOOLS = ('prepare_learning_source', 'inspect_source_preparation_job', 'query_source_content')
SKILLS = ('source-learning-entry', 'source-preparation', 'source-content-qa')
SOURCE_REASONS = frozenset({'invalid_request', 'source_missing', 'source_ambiguous', 'unsafe_source',
    'source_invalid', 'source_incomplete', 'source_empty', 'source_changed', 'invalid_cursor', 'internal_error'})
META_KEYS = frozenset({'podcast_id', 'episode_ref', 'title', 'language', 'source_version', 'segment_count',
    'start_seconds', 'end_seconds', 'actual_transcription', 'warnings', 'read_only', 'network_access'})


class _Failure(ValueError):
    pass


def _require(condition, reason='protocol_error'):
    if not condition:
        raise _Failure(reason)


def _finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def _request(podcast_id, episode_ref, start_seconds, end_seconds, max_calls=20, max_total_chars=60000):
    _require(type(podcast_id) is str and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}', podcast_id), 'invalid_request')
    _require(type(episode_ref) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', episode_ref)
        and episode_ref.casefold() not in {'latest', 'next', 'all', 'batch'}, 'invalid_request')
    _require(_finite(start_seconds) and _finite(end_seconds) and end_seconds > start_seconds
        and _integer(max_calls, 3, 100) and _integer(max_total_chars, 1, 1200000), 'invalid_request')


def _report():
    return dict(ok=False, status='blocked', reason=None, evidence_kind='session_delivery',
        podcast_id=None, episode_ref=None, source_version=None, actual_transcription=None,
        registry_count=0, missing_tools=[], requested_range=None, pages=0,
        delivered_segments=0, delivered_chars=0, selected_segments=None, scope_complete=False,
        whole_source_read=False, read_only=True, host_acceptance='not_evaluated',
        content_quality='not_evaluated', preparation_acceptance='not_evaluated', trace=[])


def _unpack(reply):
    _require(not getattr(reply, 'isError', False))
    payload = getattr(reply, 'structuredContent', None)
    if payload is None:
        content = getattr(reply, 'content', [])
        _require(len(content) == 1 and isinstance(getattr(content[0], 'text', None), str))
        try:
            payload = json.loads(content[0].text)
        except (ValueError, RecursionError):
            raise _Failure('protocol_error') from None
    _require(isinstance(payload, dict) and type(payload.get('ok')) is bool)
    if payload['ok'] is False:
        reason = payload.get('reason')
        raise _Failure(reason if type(reason) is str and reason in SOURCE_REASONS else 'protocol_error')
    _require(isinstance(payload.get('data'), dict))
    return payload['data']


def _metadata(data, identity, *, page=False, pinned=None):
    expected = META_KEYS | ({'action', 'segments', 'next_cursor', 'coverage'} if page else set())
    _require(set(data) == expected and all(data[k] == v for k, v in identity.items()))
    _require(data['read_only'] is True and data['network_access'] is False)
    _require(type(data['source_version']) is str and re.fullmatch(r'[a-f0-9]{64}', data['source_version']))
    if pinned is not None:
        _require(data['source_version'] == pinned['source_version'], 'source_changed')
    _require(_integer(data['segment_count'], 1, 100000) and _finite(data['start_seconds'])
        and _finite(data['end_seconds']) and data['end_seconds'] >= data['start_seconds'])
    _require(type(data['title']) is str and 0 < len(data['title'].strip()) <= 1024)
    _require(data['language'] is None or (type(data['language']) is str and len(data['language']) <= 32))
    _require(type(data['warnings']) is list and len(data['warnings']) <= 16
        and all(type(w) is str and len(w) <= 128 for w in data['warnings']))
    recorded = data['actual_transcription']
    if recorded is not None:
        try:
            parse(recorded, language=data['language'], recorded=True)
        except InvalidTranscriptionSettings:
            raise _Failure('protocol_error') from None
    if pinned is not None:
        _require(all(data[k] == pinned[k] for k in META_KEYS))
    return {k: data[k] for k in META_KEYS}


async def verify_learning_session(session, *, podcast_id, episode_ref, start_seconds, end_seconds,
                                  max_calls=20, max_total_chars=60000):
    """Verify one initialized session, retaining counts only, never source text."""
    result = _report()
    try:
        _request(podcast_id, episode_ref, start_seconds, end_seconds, max_calls, max_total_chars)
        identity = dict(podcast_id=podcast_id, episode_ref=episode_ref)
        result.update(identity, requested_range=[start_seconds, end_seconds])
        registry = await session.list_tools()
        _require(not getattr(registry, 'nextCursor', None))
        names = [tool.name for tool in registry.tools]
        _require(len(names) <= 1000 and all(type(name) is str for name in names) and len(names) == len(set(names)))
        result['registry_count'] = len(names)
        result['missing_tools'] = [name for name in REQUIRED_TOOLS if name not in names]
        _require(not result['missing_tools'], 'missing_tools')

        async def call(arguments):
            _require(len(result['trace']) < max_calls, 'budget_exhausted')
            result['trace'].append(dict(action=arguments.get('action', 'inspect')))
            return _unpack(await session.call_tool('query_source_content', arguments))

        pinned = _metadata(await call(identity), identity)
        result.update(source_version=pinned['source_version'], actual_transcription=pinned['actual_transcription'])
        cursor, seen, last, offset, completed, times = '', set(), None, 0, True, None
        while True:
            remaining = max_total_chars - result['delivered_chars']
            _require(len(result['trace']) + 2 <= max_calls and remaining > 0, 'budget_exhausted')
            data = await call(dict(identity, action='read', expected_source_version=pinned['source_version'],
                start_seconds=start_seconds, end_seconds=end_seconds, cursor=cursor,
                limit=100, max_chars=min(12000, remaining)))
            _metadata(data, identity, page=True, pinned=pinned)
            _require(data['action'] == 'read' and type(data['segments']) is list and len(data['segments']) <= 100)
            coverage = data['coverage']
            _require(isinstance(coverage, dict) and set(coverage) == {'scope', 'selected_segments',
                'returned_ordinals', 'scope_exhausted', 'complete', 'truncated'})
            _require(coverage['scope'] == 'time_range' and _integer(coverage['selected_segments'], 0, pinned['segment_count'])
                and all(type(coverage[k]) is bool for k in ('scope_exhausted', 'complete', 'truncated')))
            if result['selected_segments'] is None:
                result['selected_segments'] = coverage['selected_segments']
            _require(result['selected_segments'] == coverage['selected_segments'])
            next_cursor = data['next_cursor']
            _require(next_cursor is None or (type(next_cursor) is str and 0 < len(next_cursor) <= 1024))
            exhausted = next_cursor is None
            _require(coverage['scope_exhausted'] == exhausted and coverage['truncated'] == (not exhausted)
                and coverage['complete'] == (not cursor and exhausted))
            _require(coverage['returned_ordinals'] == [s.get('ordinal') for s in data['segments'] if isinstance(s, dict)])
            _require(bool(data['segments']) or (exhausted and result['selected_segments'] == 0))
            page_chars = 0
            for chunk in data['segments']:
                _require(isinstance(chunk, dict) and set(chunk) == {'ordinal', 'segment_id', 'start', 'end',
                    'text', 'text_offset', 'text_complete'})
                ordinal, text = chunk['ordinal'], chunk['text']
                _require(_integer(ordinal, 0, pinned['segment_count'] - 1) and type(text) is str and len(text) > 0
                    and _integer(chunk['text_offset'], 0, 16777216) and type(chunk['text_complete']) is bool)
                _require(_finite(chunk['start']) and _finite(chunk['end']) and chunk['end'] >= chunk['start']
                    and chunk['start'] >= pinned['start_seconds'] and chunk['end'] <= pinned['end_seconds'])
                _require((chunk['end'] > start_seconds and chunk['start'] < end_seconds)
                    if chunk['start'] != chunk['end'] else start_seconds <= chunk['start'] < end_seconds)
                current_times = (chunk['start'], chunk['end'])
                if last is None or completed:
                    _require(chunk['text_offset'] == 0 and (last is None or ordinal > last)
                        and (times is None or chunk['start'] >= times[0]))
                    offset = 0
                else:
                    _require(ordinal == last and current_times == times)
                _require(chunk['text_offset'] == offset)
                page_chars += len(text)
                _require(page_chars <= min(12000, remaining))
                offset += len(text)
                last, times, completed = ordinal, current_times, chunk['text_complete']
                result['delivered_chars'] += len(text)
                if completed:
                    result['delivered_segments'] += 1
            result['pages'] += 1
            _require(result['delivered_segments'] <= result['selected_segments'])
            if exhausted:
                _require(completed and result['delivered_segments'] == result['selected_segments'])
                break
            _require(next_cursor not in seen)
            seen.add(next_cursor)
            cursor = next_cursor
        _metadata(await call(identity), identity, pinned=pinned)
        result.update(ok=True, status='passed', reason=None, scope_complete=True)
    except _Failure as failure:
        result.update(reason=str(failure), status='partial' if str(failure) == 'budget_exhausted' else 'blocked')
    except Exception:
        result.update(reason='transport_error')
    return result


def valid_loopback_url(value):
    if type(value) is not str or len(value) > 2048 or any(ord(c) < 33 for c in value) or '\\' in value:
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == 'http' and url.hostname in {'127.0.0.1', '::1'} and url.username is None
            and url.password is None and not url.query and not url.fragment and '?' not in value and '#' not in value
            and (url.port is None or 1 <= url.port <= 65535))
    except ValueError:
        return False


def _safe_directory(path):
    try:
        candidate = Path(path).absolute()
        for parent in (candidate, *candidate.parents):
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                return None
        return candidate
    except (OSError, ValueError, TypeError):
        return None


async def _reject_redirect(response):
    _require(not response.is_redirect, 'transport_error')


class _RequestGuard:
    """Reject SDK reconnection/replay before another request reaches the network."""

    def __init__(self):
        self.seen = set()

    async def __call__(self, request):
        body_key = None
        if request.method == 'POST':
            try:
                payload = json.loads(request.content)
                identifier = payload.get('id')
                body_key = ('id', identifier) if type(identifier) in (int, str) else (
                    'notification', hashlib.sha256(request.content).hexdigest())
            except (ValueError, AttributeError):
                raise _Failure('transport_error') from None
        key = (request.method, str(request.url), body_key)
        _require(request.method in {'GET', 'POST', 'DELETE'} and key not in self.seen
            and len(self.seen) < 512, 'transport_error')
        self.seen.add(key)


class _QuietSDK(logging.Filter):
    def filter(self, record):
        return False


@contextmanager
def _quiet_sdk():
    # ValidationError representations include response bodies. Attach only an
    # owned temporary filter; concurrent calls each retain their own filter.
    guard = _QuietSDK()
    loggers = [logging.getLogger(name) for name in ('mcp.client.streamable_http',
        'mcp.client.stdio', 'mcp.client.session', 'mcp.shared.session')]
    for logger in loggers:
        logger.addFilter(guard)
    try:
        yield
    finally:
        for logger in loggers:
            logger.removeFilter(guard)


async def _connect_and_verify(*, data_dir, mcp_url, request, timeout_seconds):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamable_http_client
    import httpx

    if data_dir is not None:
        root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env['CORPUS_INGEST_DATA_DIR'] = str(data_dir)
        parameters = StdioServerParameters(command=sys.executable,
            args=[str(root / 'scripts/run_mcp_server.py')], cwd=str(root), env=env)
        with _quiet_sdk(), open(os.devnull, 'w') as errors:
            async with stdio_client(parameters, errlog=errors) as (incoming, outgoing):
                async with ClientSession(incoming, outgoing) as session:
                    await session.initialize()
                    return await verify_learning_session(session, **request)
    with _quiet_sdk():
        async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=False, follow_redirects=False,
                event_hooks={'request': [_RequestGuard()], 'response': [_reject_redirect]}) as client:
            async with streamable_http_client(mcp_url, http_client=client) as (incoming, outgoing, _):
                async with ClientSession(incoming, outgoing) as session:
                    await session.initialize()
                    return await verify_learning_session(session, **request)


async def verify_learning_connection(*, data_dir=None, mcp_url=None, timeout_seconds=60, **request):
    result = _report()
    try:
        _request(**request)
        _require(_finite(timeout_seconds) and 1 <= timeout_seconds <= 300, 'invalid_request')
        _require((data_dir is None) != (mcp_url is None), 'invalid_request')
        if data_dir is not None:
            data_dir = _safe_directory(data_dir)
            _require(data_dir is not None, 'unsafe_data_root')
        else:
            _require(valid_loopback_url(mcp_url), 'invalid_connection')
        result = await asyncio.wait_for(_connect_and_verify(data_dir=data_dir, mcp_url=mcp_url,
            request=request, timeout_seconds=timeout_seconds), timeout=timeout_seconds)
    except _Failure as failure:
        result['reason'] = str(failure)
    except TimeoutError:
        result['reason'] = 'timeout'
    except Exception:
        result['reason'] = 'transport_error'
    result['evidence_kind'] = 'owned_stdio' if data_dir is not None else 'existing_loopback'
    return result


def inventory_learning_skills(skills_root):
    """Validate transitive relative resources; return paths/availability, not bytes."""
    root = _safe_directory(skills_root)
    if root is None:
        return dict(ok=False, reason='missing_or_unsafe_skill_resource', host_loaded=False,
                    skills=list(SKILLS), resources=[])
    resources, ready = [], True
    for name in SKILLS:
        skill_root = root / name
        pending = [Path('SKILL.md')]
        if name == 'source-content-qa':
            pending.append(Path('references/learning-notes-template.md'))
        visited = set()
        while pending:
            relative = pending.pop(0)
            if relative in visited:
                continue
            visited.add(relative)
            if len(visited) > 64:
                ready = False
                break
            raw = secure_read_bytes(skill_root, skill_root / relative, max_bytes=65536, require_single_link=True)
            available = raw is not None
            resources.append(dict(path=f'{name}/{relative.as_posix()}', available=available))
            if not available:
                ready = False
                continue
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                ready = False
                continue
            if relative == Path('SKILL.md'):
                lines = text.splitlines()
                header_end = next((i for i in range(1, len(lines)) if lines[i] == '---'), None)
                if (not lines or lines[0] != '---' or header_end is None
                    or not any(re.fullmatch(r'name:\s*[\"\']?' + re.escape(name) + r'[\"\']?\s*', line)
                               for line in lines[1:header_end])):
                    ready = False
            targets = re.findall(r'\]\(([^)]+)\)', text)
            definitions = re.findall(r'(?m)^\s{0,3}\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|([^\s]+))', text)
            targets.extend(bracketed or plain for bracketed, plain in definitions)
            for target in targets:
                if target.startswith('<') and target.endswith('>'):
                    target = target[1:-1]
                if target.startswith(('#', 'https://', 'http://')):
                    continue
                target = target.split('#', 1)[0]
                parts = (relative.parent / target).parts
                if (not target or Path(target).is_absolute() or '..' in parts or ':' in target or '\\' in target
                    or Path(target).suffix.lower() != '.md' or any(part.startswith('.') for part in parts)):
                    ready = False
                    continue
                pending.append(relative.parent / target)
    return dict(ok=ready, reason=None if ready else 'missing_or_unsafe_skill_resource', host_loaded=False,
                skills=list(SKILLS), resources=resources)
