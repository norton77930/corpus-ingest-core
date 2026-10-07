"""Tool31 thin delegation and bounded public schema."""
import importlib
import inspect
import pytest
from tests.test_learning_workflow_status import PODCAST,EPISODE,_ready_episode


def wrapper():
    from corpus_ingest_core import mcp_server  # Ordered facade import is intentional.
    return importlib.import_module("corpus_ingest_core.mcp_tools_learning_status")


def test_signature_only_two_required_identities():
    signature=inspect.signature(wrapper().inspect_learning_workflow_status)
    assert list(signature.parameters)==["podcast_id","episode_ref"]
    assert all(p.default is inspect.Parameter.empty for p in signature.parameters.values())


def test_wrapper_delegates_once(monkeypatch):
    calls=[];payload={"owned":"fixture"}
    def observe(*args):calls.append(args);return payload
    monkeypatch.setattr(wrapper().learning_workflow_status,"inspect_learning_workflow_status",observe)
    assert wrapper().inspect_learning_workflow_status(PODCAST,EPISODE)=={"ok":True,"data":payload}
    assert calls==[(PODCAST,EPISODE)]


@pytest.mark.parametrize("error,kind,message",[(ValueError("PRIVATE"),"ValueError","Invalid explicit episode identity."),(RuntimeError("PRIVATE"),"InternalError","Learning workflow status could not be inspected safely.")])
def test_fixed_private_error_mapping(monkeypatch,error,kind,message):
    def fail(*a):raise error
    monkeypatch.setattr(wrapper().learning_workflow_status,"inspect_learning_workflow_status",fail)
    assert wrapper().inspect_learning_workflow_status(PODCAST,EPISODE)=={"ok":False,"error_type":kind,"message":message}


def test_real_temp_query_and_explicit_identity(tmp_data_dirs):
    _ready_episode(tmp_data_dirs);response=wrapper().inspect_learning_workflow_status(PODCAST,EPISODE)
    assert response["ok"] and response["data"]["status"]=="observed" and response["data"]["read_only"] is True
    assert wrapper().inspect_learning_workflow_status(PODCAST,"latest")["error_type"]=="ValueError"



def test_tool31_append_only_slot_schema_and_facade():
    import asyncio
    from corpus_ingest_core import mcp_server
    tools=asyncio.run(mcp_server.mcp.list_tools())
    assert len(tools)==35 and tools[30].name=="inspect_learning_workflow_status"
    assert tools[29].name=="inspect_learning_bundle_recovery"
    assert list(tools[30].inputSchema["properties"])==["podcast_id","episode_ref"]
    assert set(tools[30].inputSchema["required"])=={"podcast_id","episode_ref"}
    assert mcp_server.inspect_learning_workflow_status is wrapper().inspect_learning_workflow_status
