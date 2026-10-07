import importlib
import inspect
import pytest
from corpus_ingest_core.errors import (LLMProviderConfigError,StudyGuideBundleStateError,WorkflowDerivationStateError,PodcastIngestCoreError)
from tests.test_study_guide_bundle import PODCAST, EPISODE, _ready_episode


def wrapper():
    from corpus_ingest_core import mcp_server  # Initialize the canonical registration order.
    return importlib.import_module("corpus_ingest_core.mcp_tools_learning_advance")


def test_public_signature_and_defaults():
    params=inspect.signature(wrapper().advance_learning_workflow).parameters
    assert list(params)==["podcast_id","episode_ref","confirm","expected_action","expected_plan_id","api_cost_ack"]
    assert all(params[k].default is inspect.Parameter.empty for k in ["podcast_id","episode_ref"])
    assert params["confirm"].default is False
    assert all(params[k].default=="" for k in ["expected_action","expected_plan_id","api_cost_ack"])


@pytest.mark.parametrize("confirm",[False,True])
def test_thin_delegation_once_without_ack_echo(monkeypatch,confirm):
    calls=[];payload={"status":"fixture"}
    def run(*args,**kwargs):calls.append((args,kwargs));return payload
    q=wrapper();monkeypatch.setattr(q.learning_workflow_advance,"advance_learning_workflow",run)
    response=q.advance_learning_workflow(PODCAST,EPISODE,confirm=confirm,expected_action="complete_cover",expected_plan_id="a"*64,api_cost_ack="PRIVATE_ACK")
    expected={"ok":True,"data":payload}
    if not confirm:expected["dry_run"]=True
    assert response==expected
    assert calls==[((PODCAST,EPISODE),dict(confirm=confirm,expected_action="complete_cover",expected_plan_id="a"*64,api_cost_ack="PRIVATE_ACK"))]
    assert "PRIVATE" not in str(response)


@pytest.mark.parametrize("kind,message",[
    ("value","Invalid learning workflow request."),
    ("llm","Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration."),
    ("drift","Learning workflow plan changed; preview again before confirming."),
    ("uncertain","The action may have changed local files; inspect local state before retrying."),
    ("generic","Learning workflow action failed; inspect local state before retrying."),
    ("unexpected","Learning workflow action failed; inspect local state before retrying."),
])
def test_fixed_error_mapping_no_private_text(monkeypatch,kind,message):
    q=wrapper();classes={"value":ValueError,"llm":LLMProviderConfigError,"drift":q.learning_workflow_advance.LearningWorkflowPlanChangedError,"uncertain":q.learning_workflow_advance.LearningWorkflowAdvanceError,"generic":PodcastIngestCoreError,"unexpected":RuntimeError}
    def fail(*a,**k):raise classes[kind]("PRIVATE_PATH_EXCEPTION")
    monkeypatch.setattr(q.learning_workflow_advance,"advance_learning_workflow",fail)
    response=q.advance_learning_workflow(PODCAST,EPISODE)
    assert response=={"ok":False,"error_type":classes[kind].__name__ if kind!="unexpected" else "InternalError","message":message}


@pytest.mark.parametrize("family",["lecture","derivation"])
@pytest.mark.parametrize("reason",["unsafe_path","recovery_required","publish_failed","rollback_failed","published_cleanup_failed","published_report_failed"])
def test_existing_publication_phase_errors_preserved(monkeypatch,family,reason):
    from corpus_ingest_core.errors import _STUDY_GUIDE_STATE_MESSAGES,_WORKFLOW_DERIVATION_STATE_MESSAGES
    q=wrapper();cls=StudyGuideBundleStateError if family=="lecture" else WorkflowDerivationStateError
    messages=_STUDY_GUIDE_STATE_MESSAGES if family=="lecture" else _WORKFLOW_DERIVATION_STATE_MESSAGES
    def fail(*a,**k):raise cls(reason) from RuntimeError("PRIVATE_CAUSE")
    monkeypatch.setattr(q.learning_workflow_advance,"advance_learning_workflow",fail)
    assert q.advance_learning_workflow(PODCAST,EPISODE)=={"ok":False,"error_type":cls.__name__,"message":messages[reason]}


def test_real_temporary_preview_and_identity(tmp_data_dirs):
    _ready_episode(tmp_data_dirs)
    response=wrapper().advance_learning_workflow(PODCAST,EPISODE)
    assert response["ok"] and response["dry_run"] and response["data"]["next_action"]=="generate_lecture"
    assert wrapper().advance_learning_workflow(PODCAST,"latest")["error_type"]=="ValueError"



def test_tool32_final_slot_schema_and_facade():
    import asyncio
    from corpus_ingest_core import mcp_server
    tools=asyncio.run(mcp_server.mcp.list_tools())
    assert len(tools)==35 and tools[31].name=="advance_learning_workflow"
    assert tools[30].name=="inspect_learning_workflow_status"
    assert list(tools[31].inputSchema["properties"])==["podcast_id","episode_ref","confirm","expected_action","expected_plan_id","api_cost_ack"]
    assert set(tools[31].inputSchema["required"])=={"podcast_id","episode_ref"}
    assert mcp_server.advance_learning_workflow is wrapper().advance_learning_workflow
