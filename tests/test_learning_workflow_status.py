"""SPEC051 closed overview with public-query fixtures and real temporary integrations."""
import importlib
import json
from copy import deepcopy
from dataclasses import replace
import pytest
from corpus_ingest_core.learning_workflow_next_step import LearningWorkflowNextStep
from tests.test_study_guide_bundle import PODCAST, EPISODE, _ready_episode, _generated_bundle
from tests.test_study_guide_lineage import snapshot, tripwire


def core():
    return importlib.import_module("corpus_ingest_core.learning_workflow_status")


def recovery(status="clear", reason="no_recovery_entries"):
    return dict(podcast_id=PODCAST, episode_ref=EPISODE, status=status, reason=reason,
                manual_review_required=status!="clear", scope="learning_bundle_recovery",
                read_only=True, network_access=False, locations=[], warnings=[])


def lineage(family="study_guide", status="current", reason="matches_record", roles=None):
    return dict(podcast_id=PODCAST, episode_ref=EPISODE, status=status, reason=reason,
                changed_roles=roles or [], scope=family+"_inputs_outputs",
                read_only=True, network_access=False, warnings=["PRIVATE_CHILD_WARNING"])


def progress(action=None):
    lecture="reuse";derivation="reuse";reason="previews_reusable"
    if action in ["generate_lecture","complete_cover"]:
        lecture="generation" if action=="generate_lecture" else "cover_only";derivation="not_evaluated"
        reason="lecture_generation_needed" if action=="generate_lecture" else "cover_completion_needed"
    elif action=="generate_derivation":derivation="generation";reason="derivation_generation_needed"
    llm=None if action is None else action!="complete_cover"
    return LearningWorkflowNextStep(PODCAST,EPISODE,"complete" if action is None else "action_available",
        lecture,derivation,None,reason,action,{"PRIVATE_CALL":"PRIVATE_PATH"},llm,llm,True,False,
        "not_evaluated","existing_preview_contracts",["PRIVATE_WARNING"])


def install(monkeypatch, rec=None, nxt=None, study=None, deriv=None):
    q=core();calls=[]
    values=[recovery() if rec is None else rec,progress() if nxt is None else nxt,
            lineage() if study is None else study,lineage("workflow_derivation") if deriv is None else deriv]
    endpoints=[(q.learning_bundle_recovery,"inspect_learning_bundle_recovery","recovery"),
               (q.learning_workflow_next_step,"suggest_learning_workflow_next_step","next_step"),
               (q.study_guide_bundle,"inspect_study_guide_lineage","study_guide_lineage"),
               (q.workflow_derivation,"inspect_workflow_derivation_lineage","workflow_derivation_lineage")]
    for (module,name,tag),value in zip(endpoints,values):
        def observe(*args,_tag=tag,_value=value,**kwargs):
            calls.append((_tag,args,kwargs))
            if isinstance(_value,Exception):raise _value
            return deepcopy(_value)
        monkeypatch.setattr(module,name,observe)
    return q,calls


def query():
    return core().inspect_learning_workflow_status(PODCAST,EPISODE)


@pytest.mark.parametrize("podcast,episode",[(None,EPISODE),(PODCAST,None),("",EPISODE),("bad/path",EPISODE),(" padded",EPISODE),(PODCAST,"latest"),(PODCAST,"NEXT"),(PODCAST," padded"),(PODCAST,"../file"),(PODCAST,42)])
def test_invalid_identity_before_any_child_query(monkeypatch,podcast,episode):
    q,calls=install(monkeypatch)
    with pytest.raises(ValueError,match="Invalid explicit episode identity"):
        q.inspect_learning_workflow_status(podcast,episode)
    assert calls==[]


@pytest.mark.parametrize("status,reason",[("recovery_present","recovery_entries_present"),("blocked","unsafe_path"),("blocked","inspection_unavailable"),("blocked","identity_unavailable"),("blocked","manual_review_required")])
def test_recovery_gate_skips_three_queries(monkeypatch,status,reason):
    q,calls=install(monkeypatch,rec=recovery(status,reason),nxt=RuntimeError("PRIVATE"))
    result=query()
    assert [c[0] for c in calls]==["recovery"]
    assert result["status"]==("attention_required" if status=="recovery_present" else "blocked")
    assert result["attention_required"] is True
    assert result["attention_reasons"]==["recovery_present" if status=="recovery_present" else "recovery_blocked"]
    for name in ["next_step","study_guide_lineage","workflow_derivation_lineage"]:
        assert result[name]["status"]=="not_evaluated" and result[name]["reason"]=="recovery_gate"
    assert "PRIVATE" not in json.dumps(result)


def test_all_clear_observations_are_compact_and_not_readiness_claim(monkeypatch):
    q,calls=install(monkeypatch);result=query()
    assert [c[0] for c in calls]==["recovery","next_step","study_guide_lineage","workflow_derivation_lineage"]
    assert all(c[1]==(PODCAST,EPISODE) and c[2]=={} for c in calls)
    assert result["status"]=="observed" and result["attention_required"] is False and result["attention_reasons"]==[]
    assert result["scope"]=="learning_workflow_status" and result["read_only"] is True and result["network_access"] is False
    assert result["warnings"]==["non_atomic_observation","summary_transcript_freshness_not_evaluated","no_execution_authorization","publication_outcome_not_proven"]
    assert set(result)=={"podcast_id","episode_ref","status","attention_required","attention_reasons","recovery","next_step","study_guide_lineage","workflow_derivation_lineage","scope","read_only","network_access","warnings"}
    assert set(result["recovery"])=={"status","reason","manual_review_required"}
    assert set(result["next_step"])=={"status","reason","lecture_mode","derivation_mode","blocked_stage","next_action","requires_llm","requires_api_cost_ack"}
    assert set(result["study_guide_lineage"])=={"status","reason","changed_roles"}
    assert "PRIVATE" not in json.dumps(result) and "suggested_call" not in json.dumps(result)


@pytest.mark.parametrize("action",["generate_lecture","complete_cover","generate_derivation"])
def test_pending_work_preserves_preview_metadata_without_executable_call(monkeypatch,action):
    study=lineage(status="not_generated",reason="no_study_guide") if action=="generate_lecture" else lineage()
    install(monkeypatch,nxt=progress(action),study=study,deriv=lineage("workflow_derivation","not_generated","no_derivation"))
    result=query()
    assert result["status"]=="observed" and result["next_step"]["next_action"]==action
    assert result["next_step"]["requires_llm"] is (action!="complete_cover")
    assert "suggested_call" not in json.dumps(result)


@pytest.mark.parametrize("family",["study_guide","workflow_derivation"])
@pytest.mark.parametrize("status,reason,role,suffix",[("stale","observed_changes","recipe","stale"),("untracked","no_record",None,"untracked"),("blocked","inputs_unavailable",None,"blocked")])
def test_lineage_attention_distinctions(monkeypatch,family,status,reason,role,suffix):
    value=lineage(family,status,reason,[role] if role else [])
    install(monkeypatch,**{"study" if family=="study_guide" else "deriv":value})
    result=query();key=family+"_lineage"
    assert result[key]["status"]==status and result[key]["changed_roles"]==([role] if role else [])
    assert result["status"]==("blocked" if status=="blocked" else "attention_required")
    assert result["attention_reasons"]==[key+"_"+suffix]


def test_custom_context_is_explicit_attention(monkeypatch):
    install(monkeypatch,deriv=lineage("workflow_derivation","not_evaluated","custom_context"))
    assert query()["attention_reasons"]==["workflow_derivation_context_not_evaluated"]


@pytest.mark.parametrize("stage",["recovery","next_step","study","deriv"])
def test_each_child_exception_is_private_finite_and_once(monkeypatch,stage):
    q,calls=install(monkeypatch,**{{"recovery":"rec","next_step":"nxt","study":"study","deriv":"deriv"}[stage]:RuntimeError("PRIVATE_EXCEPTION")})
    result=query();assert result["status"]=="blocked" and "PRIVATE" not in json.dumps(result)
    assert len(calls)==(1 if stage=="recovery" else 4)
    key={"study":"study_guide_lineage","deriv":"workflow_derivation_lineage"}.get(stage,stage)
    assert result[key]["reason"]=="inspection_unavailable"


@pytest.mark.parametrize("family",["study_guide","workflow_derivation"])
@pytest.mark.parametrize("bad",["foreign-id","scope","network","readonly","status","reason","roles","role-order","stale-empty","not-stale-roles"])
def test_lineage_shape_drift_is_blocked_without_private_values(monkeypatch,family,bad):
    value=lineage(family)
    if bad=="foreign-id":value["episode_ref"]="other"
    elif bad=="scope":value["scope"]="PRIVATE_SCOPE"
    elif bad=="network":value["network_access"]=True
    elif bad=="readonly":value["read_only"]=1
    elif bad=="status":value["status"]="PRIVATE_STATE"
    elif bad=="reason":value["reason"]="PRIVATE_REASON"
    elif bad=="roles":value.update(status="stale",reason="observed_changes",changed_roles=["PRIVATE_PATH"])
    elif bad=="role-order":value.update(status="stale",reason="observed_changes",changed_roles=["request","recipe"])
    elif bad=="stale-empty":value.update(status="stale",reason="observed_changes")
    else:value["changed_roles"]=["recipe"]
    install(monkeypatch,**{"study" if family=="study_guide" else "deriv":value})
    result=query();assert result[family+"_lineage"]=={"status":"blocked","reason":"inspection_unavailable","changed_roles":[]}
    assert "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("bad",["identity","flag","reason","mode","action","llm","shape"])
def test_next_step_drift_is_closed(monkeypatch,bad):
    value=progress()
    updates={"identity":{"episode_ref":"other"},"flag":{"network_read":True},"reason":{"reason_code":"PRIVATE_REASON"},"mode":{"lecture_mode":"PRIVATE_MODE"},"action":{"next_action":"generate_lecture"},"llm":{"requires_llm":True},"shape":{}}
    value={} if bad=="shape" else replace(value,**updates[bad])
    install(monkeypatch,nxt=value)
    result=query();assert result["next_step"]["status"]=="blocked" and result["next_step"]["reason"]=="inspection_unavailable"
    assert "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("bad",["identity","scope","status","reason","manual","network","readonly","shape"])
def test_recovery_shape_drift_stops_followups(monkeypatch,bad):
    value=recovery()
    key,new={"identity":("podcast_id","other"),"scope":("scope","PRIVATE_SCOPE"),"status":("status","PRIVATE_STATUS"),"reason":("reason","PRIVATE_REASON"),"manual":("manual_review_required",True),"network":("network_access",True),"readonly":("read_only",1),"shape":("shape",None)}[bad]
    value={} if bad=="shape" else {**value,key:new}
    q,calls=install(monkeypatch,rec=value);result=query()
    assert len(calls)==1 and result["recovery"]=={"status":"blocked","reason":"inspection_unavailable","manual_review_required":True}
    assert "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("mode,family,status,reason",[(None,"study_guide","not_generated","no_study_guide"),(None,"workflow_derivation","not_generated","no_derivation"),("generate_lecture","study_guide","current","matches_record"),("generate_derivation","workflow_derivation","current","matches_record")])
def test_conflicting_observations_require_attention(monkeypatch,mode,family,status,reason):
    kwargs={"study" if family=="study_guide" else "deriv":lineage(family,status,reason)}
    install(monkeypatch,nxt=progress(mode),**kwargs)
    result=query();assert result["status"]=="attention_required" and "observations_conflict" in result["attention_reasons"]


def test_multiple_attention_reasons_have_stable_order(monkeypatch):
    install(monkeypatch,study=lineage(status="stale",reason="observed_changes",roles=["recipe"]),deriv=lineage("workflow_derivation","untracked","no_record"))
    assert query()["attention_reasons"]==["study_guide_lineage_stale","workflow_derivation_lineage_untracked"]


@pytest.mark.parametrize("state",["empty","lecture","complete","legacy","custom","stale-summary","recovery"])
def test_real_fixture_overview_is_zero_side_effect(tmp_data_dirs,monkeypatch,state):
    import socket
    from pathlib import Path
    from corpus_ingest_core import cache,local_env,llm_provider,run_report_io,storage,study_guide_bundle,workflow_derivation
    from tests.test_study_guide_bundle import TITLE
    from tests.test_workflow_derivation import _context
    from tests.test_workflow_derivation_lineage import generate
    if state=="empty":_ready_episode(tmp_data_dirs)
    else:_generated_bundle(tmp_data_dirs,monkeypatch)
    directory=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir
    if state in ["complete","legacy","custom","stale-summary"]:
        context=_context(tmp_data_dirs,["Claude Code","Codex"])
        monkeypatch.setattr(workflow_derivation,"DEFAULT_CONTEXT_PATH",context)
        generate(monkeypatch,**({"workflow_context":context} if state=="custom" else {}))
    if state=="legacy":
        for name in ["study_guide.lineage.json","workflow_derivation.lineage.json"]:(directory/name).unlink()
    elif state=="stale-summary":
        source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
        source.write_bytes(source.read_bytes()+b"\nAdditional learning topic.\n")
    elif state=="recovery":directory.with_name(directory.name+".part").mkdir()
    before=snapshot(tmp_data_dirs);previews=[]
    for module,name in [(study_guide_bundle,"run_study_guide_bundle"),(workflow_derivation,"run_workflow_derivation")]:
        real=getattr(module,name)
        def preview(*args,_real=real,_name=name,**kwargs):
            assert kwargs.get("confirm") is False and kwargs.get("force") is False
            previews.append(_name);return _real(*args,**kwargs)
        monkeypatch.setattr(module,name,preview)
    for name in ["write_bytes","write_text","mkdir","rename","replace","unlink","rmdir"]:monkeypatch.setattr(Path,name,tripwire)
    monkeypatch.setattr(socket,"create_connection",tripwire);monkeypatch.setattr(socket.socket,"connect",tripwire)
    monkeypatch.setattr(local_env,"load_local_env",tripwire)
    for module in [cache,llm_provider,study_guide_bundle,workflow_derivation,run_report_io]:
        for name in ["create_provider","rebuild_cache","initialize_cache","write_part_staged_report_pair"]:
            if hasattr(module,name):monkeypatch.setattr(module,name,tripwire)
    result=query();assert before==snapshot(tmp_data_dirs)
    if state=="recovery":
        assert result["status"]=="attention_required" and previews==[]
        assert result["attention_reasons"]==["recovery_present"]
    else:
        assert previews==(["run_study_guide_bundle"] if state=="empty" else ["run_study_guide_bundle","run_workflow_derivation"])
        if state in ["empty","lecture","complete"]:assert result["status"]=="observed"
        elif state=="legacy":assert result["attention_reasons"]==["study_guide_lineage_untracked","workflow_derivation_lineage_untracked"]
        elif state=="custom":assert result["attention_reasons"]==["workflow_derivation_context_not_evaluated"]
        else:
            assert result["attention_reasons"]==["study_guide_lineage_stale"]
            assert result["next_step"]["status"]=="complete"
            assert "semantic_summary" in result["study_guide_lineage"]["changed_roles"]
    assert str(tmp_data_dirs) not in json.dumps(result)


def test_missing_and_finance_identity_gate(tmp_data_dirs):
    assert query()["recovery"]["reason"]=="identity_unavailable"
    assert core().inspect_learning_workflow_status("gooaye","EP678")["recovery"]["reason"]=="identity_unavailable"


class PretendText(str):
    def __eq__(self, other):
        return True


@pytest.mark.parametrize("field",["status","reason_code","lecture_mode","derivation_mode","podcast_id","episode_ref","source_currentness","completion_basis"])
def test_nonplain_child_text_cannot_spoof_contract_or_leak(monkeypatch,field):
    install(monkeypatch,nxt=replace(progress(),**{field:PretendText("PRIVATE_CHILD_TEXT")}))
    result=query()
    assert result["next_step"]["status"]=="blocked" and "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("family",["recovery","study_guide","workflow_derivation"])
@pytest.mark.parametrize("field",["podcast_id","episode_ref","scope"])
def test_nonplain_child_identity_scope_is_closed(monkeypatch,family,field):
    value=recovery() if family=="recovery" else lineage(family)
    value[field]=PretendText("PRIVATE_IDENTITY")
    install(monkeypatch,**{{"recovery":"rec","study_guide":"study","workflow_derivation":"deriv"}[family]:value})
    result=query();key=family if family=="recovery" else family+"_lineage"
    assert result[key]["status"]=="blocked" and "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("stage,reason", [
    ("lecture", "derivation_prerequisite_failed"),
    ("derivation", "lecture_prerequisite_failed"),
    ("derivation", "derivation_conflict"),
])
def test_blocked_next_reason_must_match_stage(monkeypatch, stage, reason):
    modes = ("blocked", "not_evaluated") if stage == "lecture" else ("reuse", "blocked")
    value = replace(progress(), status="blocked", blocked_stage=stage,
                    lecture_mode=modes[0], derivation_mode=modes[1], reason_code=reason)
    _, calls = install(monkeypatch, nxt=value)
    result = query()
    assert result["next_step"]["reason"] == "inspection_unavailable"
    assert result["status"] == "blocked"
    assert [c[0] for c in calls] == ["recovery", "next_step", "study_guide_lineage", "workflow_derivation_lineage"]


@pytest.mark.parametrize("stage,reason", [
    ("lecture", "lecture_prerequisite_failed"),
    ("lecture", "derivation_conflict"),
    ("derivation", "derivation_prerequisite_failed"),
])
def test_valid_stage_specific_blocked_reason_is_preserved(monkeypatch, stage, reason):
    modes = ("blocked", "not_evaluated") if stage == "lecture" else ("reuse", "blocked")
    value = replace(progress(), status="blocked", blocked_stage=stage,
                    lecture_mode=modes[0], derivation_mode=modes[1], reason_code=reason)
    install(monkeypatch, nxt=value)
    assert query()["next_step"]["reason"] == reason
