"""Tool35 protocol and actual MCP SDK acceptance; no host AI execution."""
import asyncio
import json
import os
import sys
from pathlib import Path
import pytest
from tests.test_source_content_query import prepared


def server():
    from corpus_ingest_core import mcp_server
    assert hasattr(mcp_server,'query_source_content'), 'Tool35 facade is missing'
    return mcp_server


def test_append_only_registry_and_schema():
    tools=asyncio.run(server().mcp.list_tools())
    assert len(tools)==35 and tools[-1].name=='query_source_content'
    assert [tool.name for tool in tools][32:34]==['prepare_learning_source','inspect_source_preparation_job']
    assert set(tools[-1].inputSchema['properties'])=={'podcast_id','episode_ref','action','expected_source_version','query','start_seconds','end_seconds','cursor','limit','max_chars'}
    assert 'confirm' not in tools[-1].inputSchema['properties']


def test_wrapper_real_offline_pages(prepared):
    prepared[1]()
    tool=server().query_source_content
    metadata=tool('show','EP1');assert metadata['ok']
    page=tool('show','EP1',action='read',expected_source_version=metadata['data']['source_version'],limit=1)
    assert page['ok'] and page['data']['next_cursor']
    assert page['data']['segments'][0]['start']==0


@pytest.mark.parametrize('reason',['invalid_request','source_missing','source_ambiguous','unsafe_source','source_invalid','source_incomplete','source_empty','source_changed','invalid_cursor','private diagnostic',[]])
def test_fixed_safe_errors(prepared,monkeypatch,reason):
    facade=server()
    from corpus_ingest_core import source_content_query as core
    def refused(*a,**k):raise core.SourceContentError(reason)
    monkeypatch.setattr(core,'query_source_content',refused)
    result=facade.query_source_content('show','EP1')
    assert not result['ok'] and 'private diagnostic' not in json.dumps(result)
    assert result['reason'] in {'invalid_request','source_missing','source_ambiguous','unsafe_source','source_invalid','source_incomplete','source_empty','source_changed','invalid_cursor','internal_error'}


def test_unexpected_exception_does_not_expose_paths(prepared,monkeypatch):
    facade=server()
    from corpus_ingest_core import source_content_query as core
    def refused(*a,**k):raise RuntimeError('PRIVATE_PATH_OR_TOKEN')
    monkeypatch.setattr(core,'query_source_content',refused)
    result=facade.query_source_content('show','EP1')
    assert not result['ok'] and result['reason']=='internal_error'
    assert 'PRIVATE_PATH_OR_TOKEN' not in json.dumps(result)


def test_sdk_read_without_index_and_bool_rejection(prepared):
    server()
    root,write=prepared;write()
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    environment=os.environ.copy()
    environment['CORPUS_INGEST_DATA_DIR']=str(root.parent)
    environment['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src')
    def data(result):return result.structuredContent or json.loads(result.content[0].text)
    async def run():
        params=StdioServerParameters(command=sys.executable,args=['-c','from corpus_ingest_core import mcp_server; mcp_server.run()'],env=environment)
        async with stdio_client(params) as (incoming,outgoing):
            async with ClientSession(incoming,outgoing) as session:
                await session.initialize()
                tools=(await session.list_tools()).tools
                assert len(tools)==35 and tools[-1].name=='query_source_content'
                inspected=data(await session.call_tool('query_source_content',dict(podcast_id='show',episode_ref='EP1')))
                assert inspected['ok']
                args=dict(podcast_id='show',episode_ref='EP1',action='read',expected_source_version=inspected['data']['source_version'])
                page=data(await session.call_tool('query_source_content',args))
                assert page['ok'] and len(page['data']['segments'])==3
                rejected=await session.call_tool('query_source_content',dict(args,limit=True))
                assert rejected.isError or not data(rejected)['ok']
    asyncio.run(run())
    assert not list(root.parent.rglob('*.sqlite3'))