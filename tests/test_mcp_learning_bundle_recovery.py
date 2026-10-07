"""Tool30 thin-envelope contract."""
import importlib
import inspect
import pytest
from tests.test_learning_bundle_recovery import PODCAST,EPISODE,_ready_episode

def wrapper():
    from corpus_ingest_core import mcp_server  # Preserve append-only import order.
    return importlib.import_module('corpus_ingest_core.mcp_tools_learning_recovery')

def test_signature_has_only_two_required_identity_parameters():
    signature=inspect.signature(wrapper().inspect_learning_bundle_recovery)
    assert list(signature.parameters)==['podcast_id','episode_ref']
    assert all(p.default is inspect.Parameter.empty for p in signature.parameters.values())

def test_wrapper_delegates_exact_arguments(monkeypatch):
    calls=[];payload={'sentinel':'owned'}
    def inspect_core(*args):calls.append(args);return payload
    monkeypatch.setattr(wrapper().learning_bundle_recovery,'inspect_learning_bundle_recovery',inspect_core)
    assert wrapper().inspect_learning_bundle_recovery(PODCAST,EPISODE)=={'ok':True,'data':payload}
    assert calls==[(PODCAST,EPISODE)]

@pytest.mark.parametrize('error,kind,message',[(ValueError('PRIVATE_ERROR'),'ValueError','Invalid explicit episode identity.'),(RuntimeError('PRIVATE_ERROR'),'InternalError','Learning bundle recovery could not be inspected safely.')])
def test_errors_have_fixed_no_leak_envelopes(monkeypatch,error,kind,message):
    def fail(*a):raise error
    monkeypatch.setattr(wrapper().learning_bundle_recovery,'inspect_learning_bundle_recovery',fail)
    assert wrapper().inspect_learning_bundle_recovery(PODCAST,EPISODE)=={'ok':False,'error_type':kind,'message':message}

def test_real_query_is_read_only_and_explicit(tmp_data_dirs):
    _ready_episode(tmp_data_dirs)
    response=wrapper().inspect_learning_bundle_recovery(PODCAST,EPISODE)
    assert response['ok'] and response['data']['read_only'] and len(response['data']['locations'])==5
    assert not wrapper().inspect_learning_bundle_recovery(PODCAST,'latest')['ok']


def test_tool30_slot_and_schema_are_read_only():
    import asyncio
    from corpus_ingest_core import mcp_server
    tools=asyncio.run(mcp_server.mcp.list_tools())
    assert len(tools)==35 and tools[29].name=='inspect_learning_bundle_recovery'
    assert tools[28].name=='inspect_study_guide_lineage'
    schema=tools[29].inputSchema
    assert list(schema['properties'])==['podcast_id','episode_ref']
    assert set(schema['required'])=={'podcast_id','episode_ref'}
    assert mcp_server.inspect_learning_bundle_recovery is wrapper().inspect_learning_bundle_recovery
