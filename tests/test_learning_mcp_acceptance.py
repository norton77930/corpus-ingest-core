from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


IDS = dict(podcast_id='x-test', episode_ref='123')
VERSION = 'a' * 64
TOOLS = ['prepare_learning_source', 'inspect_source_preparation_job', 'query_source_content']


def metadata():
    return dict(**IDS, title='private title', language='en', source_version=VERSION,
                segment_count=20, start_seconds=0, end_seconds=100,
                actual_transcription=dict(model='medium', device='cuda', compute_type='float16', vad_filter=True),
                warnings=[], read_only=True, network_access=False)


def segment(ordinal=10, text='private transcript', offset=0, complete=True):
    return dict(ordinal=ordinal, segment_id=ordinal, start=20 + ordinal, end=21 + ordinal,
                text=text, text_offset=offset, text_complete=complete)


def page(chunks=None, cursor=None, selected=1, complete=True):
    chunks = [segment()] if chunks is None else chunks
    return dict(**metadata(), action='read', segments=chunks, next_cursor=cursor,
                coverage=dict(scope='time_range', selected_segments=selected,
                              returned_ordinals=[s['ordinal'] for s in chunks],
                              scope_exhausted=cursor is None, complete=complete,
                              truncated=cursor is not None))


class Session:
    def __init__(self, replies=None, tools=None):
        self.replies = replies or [metadata(), page(), metadata()]
        self.tools = TOOLS if tools is None else tools
        self.calls = []

    async def list_tools(self):
        return SimpleNamespace(tools=[SimpleNamespace(name=n) for n in self.tools], nextCursor=None)

    async def call_tool(self, name, arguments):
        assert name == 'query_source_content'
        self.calls.append(deepcopy(arguments))
        value = self.replies[len(self.calls) - 1]
        if isinstance(value, Exception):
            raise value
        payload = value if 'ok' in value else dict(ok=True, data=value)
        return SimpleNamespace(structuredContent=payload, content=[], isError=False)


def verify(session=None, **options):
    from corpus_ingest_core.learning_mcp_acceptance import verify_learning_session
    return asyncio.run(verify_learning_session(session or Session(), **IDS,
        start_seconds=29, end_seconds=40, **options))


def test_selected_delivery_is_metadata_only_and_not_host_acceptance():
    session = Session()
    result = verify(session)
    assert result['ok'] and result['scope_complete']
    assert result['registry_count'] == 3
    assert result['source_version'] == VERSION
    assert result['actual_transcription']['model'] == 'medium'
    assert result['delivered_segments'] == 1
    assert result['whole_source_read'] is False
    assert result['host_acceptance'] == result['content_quality'] == result['preparation_acceptance'] == 'not_evaluated'
    output = json.dumps(result)
    assert 'private title' not in output and 'private transcript' not in output
    assert [c.get('action', 'inspect') for c in session.calls] == ['inspect', 'read', 'inspect']
    assert session.calls[1]['expected_source_version'] == VERSION


def test_split_chunks_are_contiguous_and_accumulated():
    first = page([segment(text='ab', complete=False)], 'opaque-private-cursor', complete=False)
    second = page([segment(text='c', offset=2), segment(11, 'd')], selected=2, complete=False)
    first['coverage']['selected_segments'] = 2
    result = verify(Session([metadata(), first, second, metadata()]))
    assert result['ok'] and result['pages'] == 2
    assert result['delivered_segments'] == 2 and result['delivered_chars'] == 4
    assert 'opaque-private-cursor' not in json.dumps(result)


@pytest.mark.parametrize('field,value', [
    ('podcast_id', 'x-other'), ('episode_ref', '456'), ('source_version', 'secret'),
    ('read_only', False), ('network_access', True), ('segment_count', True),
    ('end_seconds', float('nan')), ('actual_transcription', {'model': 'private-key'}),
])
def test_rejects_contradictory_inspection_without_read(field, value):
    meta = metadata()
    meta[field] = value
    session = Session([meta])
    result = verify(session)
    assert not result['ok'] and result['reason'] == 'protocol_error'
    assert len(session.calls) == 1
    assert 'private-key' not in json.dumps(result)


@pytest.mark.parametrize('fault', ['offset', 'ordinal', 'selection', 'repeat_cursor', 'coverage', 'timestamp', 'changed_version'])
def test_rejects_broken_paging(fault):
    first = page([segment(text='ab', complete=False)], 'next', selected=2, complete=False)
    second = page([segment(text='c', offset=2), segment(11, 'd')], selected=2, complete=False)
    if fault == 'offset':
        second['segments'][0]['text_offset'] = 3
    elif fault == 'ordinal':
        second['segments'][1]['ordinal'] = 9
        second['coverage']['returned_ordinals'][1] = 9
    elif fault == 'selection':
        second['coverage']['selected_segments'] = 3
    elif fault == 'repeat_cursor':
        second['next_cursor'] = 'next'
        second['coverage'].update(scope_exhausted=False, truncated=True)
    elif fault == 'coverage':
        second['coverage']['scope_exhausted'] = False
    elif fault == 'timestamp':
        second['segments'][0]['start'] = 35
    else:
        second['source_version'] = 'b' * 64
    result = verify(Session([metadata(), first, second, metadata()]))
    assert not result['ok'] and not result['scope_complete']
    assert result['reason'] in {'protocol_error', 'source_changed'}


def test_final_inspect_catches_drift():
    changed = metadata()
    changed['source_version'] = 'b' * 64
    result = verify(Session([metadata(), page(), changed]))
    assert not result['ok'] and result['reason'] == 'source_changed'
    assert not result['scope_complete']


@pytest.mark.parametrize('options', [{'max_calls': 3}, {'max_total_chars': 2}])
def test_budget_stops_without_extra_read_or_complete_claim(options):
    first = page([segment(text='ab', complete=False)], 'next', complete=False)
    session = Session([metadata(), first])
    result = verify(session, **options)
    assert result['status'] == 'partial' and result['reason'] == 'budget_exhausted'
    assert not result['ok'] and not result['scope_complete'] and len(session.calls) == 2


def test_empty_selection_is_valid_zero_delivery():
    result = verify(Session([metadata(), page([], selected=0), metadata()]))
    assert result['ok'] and result['delivered_segments'] == result['delivered_chars'] == 0


def test_missing_capability_stops_before_tool_calls():
    session = Session(tools=TOOLS[1:])
    result = verify(session)
    assert result['reason'] == 'missing_tools' and not result['ok']
    assert not session.calls


@pytest.mark.parametrize('reply,reason', [
    ({'ok': False, 'reason': 'source_missing', 'message': 'secret text'}, 'source_missing'),
    ({'ok': False, 'reason': 'secret text'}, 'protocol_error'),
    (RuntimeError('private exception'), 'transport_error'),
])
def test_diagnostics_never_echo_server_or_exception_text(reply, reason):
    result = verify(Session([reply]))
    assert not result['ok'] and result['reason'] == reason
    assert 'secret text' not in json.dumps(result) and 'private exception' not in json.dumps(result)


@pytest.mark.parametrize('options', [{'start_seconds': float('inf')}, {'episode_ref': 'latest'}, {'max_calls': True}])
def test_invalid_request_never_contacts_session(options):
    from corpus_ingest_core.learning_mcp_acceptance import verify_learning_session
    session = Session()
    request = dict(**IDS, start_seconds=29, end_seconds=40)
    request.update(options)
    result = asyncio.run(verify_learning_session(session, **request))
    assert result['reason'] == 'invalid_request' and not session.calls


@pytest.mark.parametrize('url', ['https://example.com/mcp', 'http://user:secret@127.0.0.1/mcp',
    'http://127.0.0.1/mcp?token=secret', 'http://localhost/mcp', 'http://127.0.0.1/mcp#fragment',
    'http://127.0.0.2/mcp', 'http://127.0.0.1:99999/mcp'])
def test_only_explicit_credential_free_numeric_loopback_is_accepted(url):
    from corpus_ingest_core.learning_mcp_acceptance import valid_loopback_url
    assert not valid_loopback_url(url)


def test_loopback_ipv4_and_ipv6_accepted():
    from corpus_ingest_core.learning_mcp_acceptance import valid_loopback_url
    assert valid_loopback_url('http://127.0.0.1:8765/mcp')
    assert valid_loopback_url('http://[::1]:8765/mcp')


def make_skills(root):
    for name in ('source-learning-entry', 'source-preparation', 'source-content-qa'):
        directory = root / name
        (directory / 'references').mkdir(parents=True)
        (directory / 'SKILL.md').write_text(f'---\nname: {name}\n---\n[protocol](references/protocol.md)', encoding='utf-8')
        (directory / 'references/protocol.md').write_text('[extra](extra.md)', encoding='utf-8')
        (directory / 'references/extra.md').write_text('resource', encoding='utf-8')
    (root / 'source-content-qa/references/learning-notes-template.md').write_text('template', encoding='utf-8')


def test_inventory_includes_transitive_references_and_template(tmp_path):
    from corpus_ingest_core.learning_mcp_acceptance import inventory_learning_skills
    make_skills(tmp_path)
    result = inventory_learning_skills(tmp_path)
    assert result['ok'] and len(result['resources']) == 10
    assert all(r['available'] for r in result['resources'])
    assert not result['host_loaded']


@pytest.mark.parametrize('fault', ['missing', 'traversal', 'symlink'])
def test_inventory_fails_on_missing_or_unsafe_reference(tmp_path, fault):
    from corpus_ingest_core.learning_mcp_acceptance import inventory_learning_skills
    make_skills(tmp_path)
    resource = tmp_path / 'source-preparation/references/extra.md'
    if fault == 'missing':
        resource.unlink()
    elif fault == 'traversal':
        resource.write_text('[outside](../../../private.md)', encoding='utf-8')
    else:
        resource.unlink()
        try:
            resource.symlink_to(tmp_path / 'source-content-qa/references/extra.md')
        except OSError:
            pytest.skip('native symlink unavailable: OSError')
    result = inventory_learning_skills(tmp_path)
    assert not result['ok']
    assert 'private.md' not in json.dumps(result)


def test_cli_inventory_outputs_json_without_verifying_source(monkeypatch, capsys):
    from scripts import verify_learning_mcp
    assert verify_learning_mcp.main(['inventory']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['ok'] and result['host_loaded'] is False


def test_cli_requires_explicit_connection():
    from scripts import verify_learning_mcp
    with pytest.raises(SystemExit) as failure:
        verify_learning_mcp.parse_args(['verify', '--podcast', 'x-test', '--episode', '123', '--start', '0', '--end', '10'])
    assert failure.value.code == 2


def test_connection_defaults_reach_selected_transport(monkeypatch):
    from corpus_ingest_core import learning_mcp_acceptance as core
    calls = []
    async def connect(**kwargs):
        calls.append(kwargs)
        return await core.verify_learning_session(Session(), **IDS, start_seconds=29, end_seconds=40)
    monkeypatch.setattr(core, '_connect_and_verify', connect)
    result = asyncio.run(core.verify_learning_connection(mcp_url='http://127.0.0.1:8765/mcp',
        **IDS, start_seconds=29, end_seconds=40))
    assert result['ok'] and len(calls) == 1
    assert result['evidence_kind'] == 'existing_loopback'


def test_inventory_never_reads_env_link(tmp_path, monkeypatch):
    from corpus_ingest_core import learning_mcp_acceptance as core
    make_skills(tmp_path)
    (tmp_path / 'source-preparation/SKILL.md').write_text('[secret](.env)', encoding='utf-8')
    original = core.secure_read_bytes
    def guarded(root, path, **kwargs):
        assert path.name != '.env', 'must reject secret resource before reading'
        return original(root, path, **kwargs)
    monkeypatch.setattr(core, 'secure_read_bytes', guarded)
    assert not core.inventory_learning_skills(tmp_path)['ok']


def test_inventory_rejects_wrong_installed_name(tmp_path):
    from corpus_ingest_core.learning_mcp_acceptance import inventory_learning_skills
    make_skills(tmp_path)
    (tmp_path / 'source-preparation/SKILL.md').write_text('---\nname: wrong-name\n---', encoding='utf-8')
    assert not inventory_learning_skills(tmp_path)['ok']


def test_timeout_cancels_without_raw_diagnostic(monkeypatch):
    from corpus_ingest_core import learning_mcp_acceptance as core
    cancelled = []
    async def slow(**kwargs):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)
    monkeypatch.setattr(core, '_connect_and_verify', slow)
    result = asyncio.run(core.verify_learning_connection(mcp_url='http://127.0.0.1:8765/mcp',
        **IDS, start_seconds=29, end_seconds=40, max_calls=20, max_total_chars=60000, timeout_seconds=1))
    assert result['reason'] == 'timeout' and cancelled == [True]


def test_redirect_rejected_before_sdk_can_follow_it():
    from corpus_ingest_core.learning_mcp_acceptance import _reject_redirect
    with pytest.raises(ValueError, match='^transport_error$'):
        asyncio.run(_reject_redirect(SimpleNamespace(is_redirect=True)))


def test_http_sdk_logging_cannot_expose_remote_body(monkeypatch, caplog):
    import mcp.client.streamable_http  # SDK subclass must load before client substitution.
    import httpx
    from corpus_ingest_core import learning_mcp_acceptance as core
    original = httpx.AsyncClient
    sent = []
    def handler(request):
        sent.append(request.method)
        return httpx.Response(200, json={'private': 'SYNTHETIC_PRIVATE_SENTINEL'})
    def client(**kwargs):
        return original(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr(httpx, 'AsyncClient', client)
    result = asyncio.run(core.verify_learning_connection(mcp_url='http://127.0.0.1:8765/mcp',
        **IDS, start_seconds=29, end_seconds=40, timeout_seconds=1))
    assert not result['ok'] and sent == ['POST']
    assert 'SYNTHETIC_PRIVATE_SENTINEL' not in caplog.text


def test_transport_replay_guard_rejects_duplicate_network_requests():
    import httpx
    from corpus_ingest_core.learning_mcp_acceptance import _RequestGuard
    guard = _RequestGuard()
    request = httpx.Request('GET', 'http://127.0.0.1:8765/mcp')
    asyncio.run(guard(request))
    with pytest.raises(ValueError, match='^transport_error$'):
        asyncio.run(guard(request))
    post = httpx.Request('POST', 'http://127.0.0.1:8765/mcp', json={'id': 1, 'method': 'tools/list'})
    asyncio.run(guard(post))
    with pytest.raises(ValueError, match='^transport_error$'):
        asyncio.run(guard(post))


def test_inventory_checks_reference_style_markdown(tmp_path):
    from corpus_ingest_core.learning_mcp_acceptance import inventory_learning_skills
    make_skills(tmp_path)
    path = tmp_path / 'source-preparation/SKILL.md'
    path.write_text('---\nname: source-preparation\n---\n[protocol][p]\n[p]: references/missing.md\n', encoding='utf-8')
    assert not inventory_learning_skills(tmp_path)['ok']


def test_legal_overlap_selection_can_have_ordinal_gap():
    from corpus_ingest_core.source_content_query import _in_range
    earlier = segment(10, 'a')
    earlier.update(start=20, end=35)
    excluded = segment(11, 'b')
    excluded.update(start=21, end=22)
    later = segment(12, 'c')
    later.update(start=30, end=32)
    selected = [s for s in (earlier, excluded, later) if _in_range(s, 29, 40)]
    assert [s['ordinal'] for s in selected] == [10, 12]
    result = verify(Session([metadata(), page(selected, selected=2), metadata()]))
    assert result['ok'] and result['delivered_segments'] == 2


def test_http_mock_server_success_has_safe_client_policy(monkeypatch):
    import mcp.client.streamable_http
    import httpx
    from corpus_ingest_core import learning_mcp_acceptance as core
    original = httpx.AsyncClient
    settings = []
    replies = iter([metadata(), page(), metadata()])
    def handler(request):
        body = json.loads(request.content)
        method = body['method']
        if method == 'notifications/initialized':
            return httpx.Response(202)
        if method == 'initialize':
            result = dict(protocolVersion=body['params']['protocolVersion'], capabilities={'tools': {}},
                          serverInfo={'name': 'fixture', 'version': '1'})
        elif method == 'tools/list':
            result = dict(tools=[dict(name=name, inputSchema={'type': 'object'}) for name in TOOLS])
        else:
            assert method == 'tools/call' and body['params']['name'] == 'query_source_content'
            result = dict(content=[], structuredContent=dict(ok=True, data=next(replies)))
        return httpx.Response(200, json=dict(jsonrpc='2.0', id=body['id'], result=result))
    def client(**kwargs):
        settings.append(kwargs)
        return original(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr(httpx, 'AsyncClient', client)
    result = asyncio.run(core.verify_learning_connection(mcp_url='http://127.0.0.1:8765/mcp',
        **IDS, start_seconds=29, end_seconds=40))
    assert result['ok'] and result['registry_count'] == 3
    assert settings[0]['trust_env'] is False and settings[0]['follow_redirects'] is False
    assert settings[0]['event_hooks']['request'] and settings[0]['event_hooks']['response']


def test_stdio_sdk_logging_is_suppressed_and_filters_restored(tmp_path, monkeypatch, caplog):
    from contextlib import asynccontextmanager
    import logging
    import mcp.client.stdio
    from corpus_ingest_core import learning_mcp_acceptance as core
    logger = logging.getLogger('mcp.client.stdio')
    previous = list(logger.filters)
    @asynccontextmanager
    async def bad_transport(*args, **kwargs):
        logger.error('SYNTHETIC_STDIO_PRIVATE_SENTINEL')
        raise RuntimeError('SYNTHETIC_STDIO_PRIVATE_SENTINEL')
        yield
    monkeypatch.setattr(mcp.client.stdio, 'stdio_client', bad_transport)
    result = asyncio.run(core.verify_learning_connection(data_dir=tmp_path, **IDS,
        start_seconds=29, end_seconds=40))
    assert not result['ok'] and result['reason'] == 'transport_error'
    assert 'SYNTHETIC_STDIO_PRIVATE_SENTINEL' not in caplog.text
    assert list(logger.filters) == previous
