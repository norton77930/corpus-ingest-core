from __future__ import annotations

import importlib
from dataclasses import replace
from copy import deepcopy
import json
from pathlib import Path

import pytest
from corpus_ingest_core import storage
from corpus_ingest_core.models import StudyGuideBundleResult, WorkflowDerivationResult
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_study_guide_bundle import PODCAST, EPISODE, _ready_episode, _generated_bundle
from tests.test_study_guide_lineage import snapshot, tripwire

STEM = EPISODE + "__fixture"
ACTIONS = ["generate_lecture", "complete_cover", "generate_derivation"]


def core():
    return importlib.import_module("corpus_ingest_core.learning_workflow_advance")


def overview(action="generate_lecture", attention=None):
    lecture = "generation" if action == "generate_lecture" else "cover_only" if action == "complete_cover" else "reuse"
    derivation = "generation" if action == "generate_derivation" else "reuse" if action is None else "not_evaluated"
    reason = {"generate_lecture":"lecture_generation_needed", "complete_cover":"cover_completion_needed", "generate_derivation":"derivation_generation_needed", None:"previews_reusable"}[action]
    lineage = lambda present, absent: {"status":"current" if present else "not_generated", "reason":"matches_record" if present else absent, "changed_roles":[]}
    return dict(podcast_id=PODCAST, episode_ref=EPISODE, status="attention_required" if attention else "observed",
        attention_required=bool(attention), attention_reasons=[attention] if attention else [],
        recovery={"status":"clear", "reason":"no_recovery_entries", "manual_review_required":False},
        next_step=dict(status="complete" if action is None else "action_available", reason=reason, lecture_mode=lecture,
                       derivation_mode=derivation, blocked_stage=None, next_action=action,
                       requires_llm=None if action is None else action!="complete_cover",
                       requires_api_cost_ack=None if action is None else action!="complete_cover"),
        study_guide_lineage=lineage(action!="generate_lecture", "no_study_guide"), workflow_derivation_lineage=lineage(action is None, "no_derivation"),
        scope="learning_workflow_status", read_only=True, network_access=False, warnings=["PRIVATE_CHILD_WARNING"])


def plan(action, confirm=False, stem=STEM):
    lecture = storage.study_guide_bundle_paths_from_stem(PODCAST, stem)
    reports = storage.study_guide_run_asset_paths(PODCAST, EPISODE)
    outputs = {"00":str(lecture.cover_path), "03":str(lecture.summary_path), "04":str(lecture.notes_path), "07":str(lecture.guide_path)}
    if action == "generate_derivation":
        pair = storage.workflow_derivation_paths_from_stem(PODCAST, stem)
        reports = storage.workflow_derivation_run_asset_paths(PODCAST, EPISODE)
        return WorkflowDerivationResult(PODCAST, EPISODE, confirm, "confirmed" if confirm else "preview",
            str(lecture.bundle_dir), "PRIVATE_CONTEXT", ["PRIVATE_READ"], [str(pair.prompt_examples_path),str(pair.apply_path)], [],
            str(pair.prompt_examples_path) if confirm else None, str(pair.apply_path) if confirm else None,
            reports.json_path if confirm else None, reports.markdown_path if confirm else None, False, ["PRIVATE_WARNING"], True,
            [str(lecture.bundle_dir / "workflow_derivation.lineage.json")])
    return StudyGuideBundleResult(PODCAST, EPISODE, confirm, "confirmed" if confirm else "dry-run", "PRIVATE_SOURCE",
        str(lecture.bundle_dir), ["PRIVATE_READ"], list(outputs.values()) if action=="generate_lecture" else [outputs["00"]],
        [] if action=="generate_lecture" else [outputs[k] for k in ["03","04","07"]], outputs if confirm else {},
        reports.json_path if confirm else None, reports.markdown_path if confirm else None, False,["PRIVATE_WARNING"],True,
        [str(lecture.bundle_dir / "study_guide.lineage.json")] if action=="generate_lecture" else [])


def install(monkeypatch, action="generate_lecture", observation=None, preview=None, confirmed=None):
    q=core();calls=[]
    def observe(*args):
        calls.append(("observe", args, {}))
        value=overview(action) if observation is None else observation
        if isinstance(value, Exception):raise value
        return deepcopy(value)
    monkeypatch.setattr(q.learning_workflow_status, "inspect_learning_workflow_status", observe)
    for module, name, stage in [(q.study_guide_bundle,"run_study_guide_bundle","lecture"),(q.workflow_derivation,"run_workflow_derivation","derivation")]:
        def run(*args, _stage=stage, **kwargs):
            calls.append((_stage, args, kwargs))
            value=(plan(action,True) if confirmed is None else confirmed) if kwargs.get("confirm") else (plan(action) if preview is None else preview)
            if isinstance(value,Exception):raise value
            return value
        monkeypatch.setattr(module,name,run)
    return q,calls


def request(**kwargs):
    return core().advance_learning_workflow(PODCAST, EPISODE, **kwargs)


@pytest.mark.parametrize("podcast,episode", [(None,EPISODE),(PODCAST,None),("",EPISODE),(" padded",EPISODE),("bad/path",EPISODE),(PODCAST,"latest"),(PODCAST,"NEXT"),(PODCAST,"../bad"),(PODCAST," padded"),(PODCAST,42)])
def test_identity_rejected_before_observation(monkeypatch,podcast,episode):
    q,calls=install(monkeypatch)
    with pytest.raises(ValueError):q.advance_learning_workflow(podcast,episode)
    assert calls==[]


@pytest.mark.parametrize("kwargs", [{"confirm":1},{"confirm":"false"},{"api_cost_ack":None},{"expected_action":None},{"expected_plan_id":None},{"expected_action":"generate_lecture"},{"expected_plan_id":"a"*64},{"confirm":True},{"confirm":True,"expected_action":"PRIVATE"},{"confirm":True,"expected_action":"complete_cover","expected_plan_id":"wrong"}])
def test_invalid_control_binding_before_observation(monkeypatch,kwargs):
    _,calls=install(monkeypatch)
    with pytest.raises(ValueError):request(**kwargs)
    assert calls==[]


@pytest.mark.parametrize("action", ACTIONS)
def test_preview_closed_plan_no_confirm_ack_or_private_fields(monkeypatch,action):
    _,calls=install(monkeypatch,action)
    result=request(api_cost_ack="PRIVATE_ACK")
    assert result["status"]=="action_available" and result["next_action"]==action
    assert result["confirm"] is False and result["dry_run"] is True and result["network_read"] is False
    assert result["requires_llm"] is (action!="complete_cover") and result["requires_api_cost_ack"] is (action!="complete_cover")
    assert len(result["plan_id"])==64 and result["plan_id"]==request()["plan_id"]
    assert result["writes"]==plan(action).planned_writes and result["metadata_writes"]==plan(action).metadata_writes
    assert len(result["report_writes"])==2 and result["report_paths"]==[] and result["output_paths"]=={}
    assert result["executed_action"] is None and result["follow_up"]=="confirm_selected_action"
    assert "PRIVATE" not in json.dumps(result)
    assert all(c[2]=={"confirm":False,"force":False} for c in calls if c[0]!="observe")


@pytest.mark.parametrize("attention", ["recovery_present","recovery_blocked","next_step_blocked","study_guide_lineage_stale","study_guide_lineage_untracked","workflow_derivation_lineage_blocked","workflow_derivation_lineage_stale","workflow_derivation_lineage_untracked","workflow_derivation_context_not_evaluated","observations_conflict"])
def test_attention_requires_manual_review_without_extra_preview(monkeypatch,attention):
    _,calls=install(monkeypatch,observation=overview(attention=attention))
    result=request()
    assert result["status"]=="blocked" and result["reason"]=="workflow_requires_attention"
    assert result["diagnostic_reasons"]==[attention] and result["follow_up"]=="manual_review"
    assert len(calls)==1 and result["writes"]==[] and result["plan_id"] is None


def test_scoped_complete_is_noop_no_runner_or_reports(monkeypatch):
    _,calls=install(monkeypatch,action=None)
    result=request()
    assert result["status"]=="complete" and result["reason"]=="previews_reusable"
    assert result["report_writes"]==[] and result["next_action"] is None and len(calls)==1
    assert "summary_transcript_freshness_not_evaluated" in result["warnings"]


@pytest.mark.parametrize("bad", ["identity","scope","readonly","network","attention","recovery","action","cost","mode","status","private-reason","exception"])
def test_malformed_observation_is_finite_and_no_runner(monkeypatch,bad):
    value=overview()
    if bad in ["identity","scope","readonly","network"]:
        key,new={"identity":("episode_ref","other"),"scope":("scope","PRIVATE"),"readonly":("read_only",1),"network":("network_access",True)}[bad];value[key]=new
    elif bad=="attention":value["attention_required"]=True
    elif bad=="recovery":value["recovery"]["status"]="blocked"
    elif bad=="action":value["next_step"]["next_action"]="PRIVATE_ACTION"
    elif bad=="cost":value["next_step"]["requires_llm"]=False
    elif bad=="mode":value["next_step"]["lecture_mode"]="reuse"
    elif bad=="status":value["status"]="PRIVATE_STATUS"
    elif bad=="private-reason":value.update(status="blocked",attention_required=True,attention_reasons=["PRIVATE_REASON"])
    else:value=RuntimeError("PRIVATE_EXCEPTION")
    _,calls=install(monkeypatch,observation=value);result=request()
    assert result["status"]=="blocked" and result["reason"]=="inspection_unavailable" and len(calls)==1
    assert "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("bad", ["identity","confirm","mode","reuse","writes","metadata","directory","shape","exception"])
def test_selected_preview_drift_or_private_path_is_blocked(monkeypatch,bad):
    value=plan("generate_lecture")
    changes={"identity":{"episode_ref":"other"},"confirm":{"confirm":True},"mode":{"run_mode":"confirmed"},"reuse":{"reused":True},"writes":{"planned_writes":["PRIVATE_PATH"]},"metadata":{"metadata_writes":[]},"directory":{"bundle_dir":"PRIVATE_PATH"}}
    value={} if bad=="shape" else RuntimeError("PRIVATE_EXCEPTION") if bad=="exception" else replace(value,**changes[bad])
    _,calls=install(monkeypatch,preview=value);result=request()
    assert result["status"]=="blocked" and result["reason"]=="inspection_unavailable"
    assert result["writes"]==[] and result["plan_id"] is None and "PRIVATE" not in json.dumps(result)
    assert all(not c[2].get("confirm") for c in calls)


@pytest.mark.parametrize("action", ACTIONS)
def test_confirm_delegates_exactly_once_and_stops(monkeypatch, action):
    _,calls=install(monkeypatch,action)
    preview=request();calls.clear()
    result=request(confirm=True,expected_action=action,expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert result["status"]=="executed" and result["executed_action"]==action and result["follow_up"]=="preview_again"
    assert result["confirm"] is True and result["dry_run"] is False
    assert result["network_read"] is (action!="complete_cover")
    assert result["report_paths"]==result["report_writes"] and result["output_paths"]
    assert [c[0] for c in calls]==["observe","derivation" if action=="generate_derivation" else "lecture","derivation" if action=="generate_derivation" else "lecture"]
    assert calls[-1][2]=={"confirm":True,"force":False,"api_cost_ack":"" if action=="complete_cover" else SEMANTIC_API_COST_ACK}
    assert "PRIVATE" not in json.dumps(result) and "api_cost_ack" not in result


@pytest.mark.parametrize("action", ["generate_lecture", "generate_derivation"])
@pytest.mark.parametrize("ack", ["", "PRIVATE", SEMANTIC_API_COST_ACK+"\n"])
def test_generation_ack_before_any_observation(monkeypatch,action,ack):
    from corpus_ingest_core.errors import LLMProviderConfigError
    _,calls=install(monkeypatch,action)
    with pytest.raises(LLMProviderConfigError):
        request(confirm=True,expected_action=action,expected_plan_id="a"*64,api_cost_ack=ack)
    assert calls==[]


@pytest.mark.parametrize("old,new", [("generate_lecture","complete_cover"),("complete_cover","generate_lecture"),("complete_cover","generate_derivation"),("generate_derivation","generate_lecture")])
def test_changed_action_cost_stops_before_confirm_dispatch(monkeypatch,old,new):
    q,calls=install(monkeypatch,old);preview=request()
    q,calls=install(monkeypatch,new)
    with pytest.raises(q.LearningWorkflowPlanChangedError):
        request(confirm=True,expected_action=old,expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert all(not c[2].get("confirm") for c in calls)


def test_same_action_changed_write_plan_stops(monkeypatch):
    q,calls=install(monkeypatch);preview=request()
    q,calls=install(monkeypatch,preview=plan("generate_lecture",stem=EPISODE+"__changed_title"))
    with pytest.raises(q.LearningWorkflowPlanChangedError):
        request(confirm=True,expected_action="generate_lecture",expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert all(not c[2].get("confirm") for c in calls)


def test_wrong_metadata_binding_stops(monkeypatch):
    q,calls=install(monkeypatch)
    with pytest.raises(q.LearningWorkflowPlanChangedError):
        request(confirm=True,expected_action="generate_lecture",expected_plan_id="a"*64,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert all(not c[2].get("confirm") for c in calls)


def test_action_became_complete_requires_new_preview(monkeypatch):
    q,calls=install(monkeypatch,action=None)
    with pytest.raises(q.LearningWorkflowPlanChangedError):
        request(confirm=True,expected_action="generate_lecture",expected_plan_id="a"*64,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert len(calls)==1


@pytest.mark.parametrize("attention", ["recovery_present","study_guide_lineage_stale","workflow_derivation_lineage_untracked"])
def test_new_attention_prevents_confirm_dispatch(monkeypatch,attention):
    _,calls=install(monkeypatch,observation=overview(attention=attention))
    result=request(confirm=True,expected_action="generate_lecture",expected_plan_id="a"*64,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert result["status"]=="blocked" and len(calls)==1


@pytest.mark.parametrize("stage", ["lecture","derivation"])
def test_child_confirmation_errors_propagate_without_retry(monkeypatch,stage):
    from corpus_ingest_core.errors import StudyGuideBundleStateError, WorkflowDerivationStateError
    action="generate_lecture" if stage=="lecture" else "generate_derivation"
    error=(StudyGuideBundleStateError if stage=="lecture" else WorkflowDerivationStateError)("published_report_failed")
    _,calls=install(monkeypatch,action,confirmed=error);preview=request();calls.clear()
    with pytest.raises(type(error)) as caught:
        request(confirm=True,expected_action=action,expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert caught.value is error and len(calls)==3


@pytest.mark.parametrize("bad", ["shape","identity","confirm","reused","outputs","reports","changed-plan"])
def test_post_dispatch_invalid_result_warns_possible_side_effects(monkeypatch,bad):
    action="generate_lecture";value=plan(action,True)
    changes={"identity":{"podcast_id":"other"},"confirm":{"confirm":False},"reused":{"reused":True},"outputs":{"output_paths":{"PRIVATE":"PRIVATE_PATH"}},"reports":{"report_json_path":Path("PRIVATE_PATH")}}
    value={} if bad=="shape" else plan(action,True,stem=EPISODE+"__changed") if bad=="changed-plan" else replace(value,**changes[bad])
    q,calls=install(monkeypatch,confirmed=value);preview=request();calls.clear()
    with pytest.raises(q.LearningWorkflowAdvanceError,match="may have changed local files"):
        request(confirm=True,expected_action=action,expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert len(calls)==3


def test_preview_plan_binding_ignores_private_child_fields(monkeypatch):
    _,_=install(monkeypatch);before=request()
    value=replace(plan("generate_lecture"),source_summary_path="OTHER_PRIVATE_SOURCE",planned_reads=["OTHER_PRIVATE_READ"],warnings=["OTHER_PRIVATE_WARNING"])
    _,_=install(monkeypatch,preview=value);after=request()
    assert before["plan_id"]==after["plan_id"] and before["reads"]==after["reads"]
    assert "PRIVATE" not in json.dumps(after)


class PretendText(str):
    def __eq__(self, other):return True


@pytest.mark.parametrize("field", ["podcast_id","episode_ref","scope","status","recovery-status","recovery-reason","manual-review","missing-blocked-stage"])
def test_observation_plain_types_and_complete_shape_required(monkeypatch,field):
    value=overview()
    if field in ["podcast_id","episode_ref","scope","status"]:value[field]=PretendText("PRIVATE")
    elif field=="manual-review":value["recovery"]["manual_review_required"]=0
    elif field=="missing-blocked-stage":del value["next_step"]["blocked_stage"]
    else:value["recovery"][field.split("-")[1]]=PretendText("PRIVATE")
    _,calls=install(monkeypatch,observation=value);result=request()
    assert result["status"]=="blocked" and result["reason"]=="inspection_unavailable"
    assert len(calls)==1 and "PRIVATE" not in json.dumps(result)


@pytest.mark.parametrize("action", ["generate_lecture","generate_derivation"])
def test_preview_must_not_contain_confirmed_outputs(monkeypatch,action):
    value=plan(action)
    value=replace(value,output_paths={"PRIVATE":"PRIVATE_PATH"}) if action=="generate_lecture" else replace(value,prompt_examples_path="PRIVATE_PATH")
    install(monkeypatch,action,preview=value)
    assert request()["status"]=="blocked"



def block_external_effects(monkeypatch):
    import socket
    from corpus_ingest_core import cache, local_env, llm_provider
    monkeypatch.setattr(socket,"create_connection",tripwire)
    monkeypatch.setattr(socket.socket,"connect",tripwire)
    monkeypatch.setattr(local_env,"load_local_env",tripwire)
    monkeypatch.setattr(llm_provider,"create_provider",tripwire)
    monkeypatch.setattr(cache,"rebuild_cache",tripwire)
    monkeypatch.setattr(cache,"initialize_cache",tripwire)


def fake_providers(monkeypatch):
    from tests.test_study_guide_bundle import _FakeProvider as LectureProvider, _valid_payload as lecture_payload
    from tests.test_workflow_derivation import _FakeProvider as DerivationProvider, _valid_payload as derivation_payload
    lecture_calls=[];derivation_calls=[]
    monkeypatch.setattr(core().study_guide_bundle,"create_provider",lambda *a,**k:LectureProvider(lecture_payload(),lecture_calls))
    monkeypatch.setattr(core().workflow_derivation,"create_provider",lambda *a,**k:DerivationProvider(derivation_payload(),derivation_calls))
    return lecture_calls,derivation_calls


def record_real_runners(monkeypatch):
    calls=[];q=core()
    for module,name,stage in [(q.study_guide_bundle,"run_study_guide_bundle","lecture"),(q.workflow_derivation,"run_workflow_derivation","derivation")]:
        original=getattr(module,name)
        def record(*args,_original=original,_stage=stage,**kwargs):
            calls.append((_stage,kwargs.copy()));return _original(*args,**kwargs)
        monkeypatch.setattr(module,name,record)
    return calls


def confirm_preview(preview,ack=SEMANTIC_API_COST_ACK):
    return request(confirm=True,expected_action=preview["next_action"],expected_plan_id=preview["plan_id"],api_cost_ack=ack)


def test_real_one_action_each_time_lecture_then_derivation(tmp_data_dirs,monkeypatch):
    from tests.test_study_guide_bundle import TITLE
    from tests.test_workflow_derivation import _context
    _ready_episode(tmp_data_dirs)
    context=_context(tmp_data_dirs,["Claude Code","Codex"])
    monkeypatch.setattr(core().workflow_derivation,"DEFAULT_CONTEXT_PATH",context)
    block_external_effects(monkeypatch);lecture_calls,derivation_calls=fake_providers(monkeypatch)
    calls=record_real_runners(monkeypatch)
    before=snapshot(tmp_data_dirs);preview=request()
    assert snapshot(tmp_data_dirs)==before and preview["next_action"]=="generate_lecture"
    calls.clear();result=confirm_preview(preview)
    assert result["status"]=="executed" and len([c for c in calls if c[1].get("confirm")])==1
    assert len(lecture_calls)==1 and derivation_calls==[]
    pair=storage.workflow_derivation_paths_from_stem(PODCAST,storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir.name)
    assert not pair.prompt_examples_path.exists() and not pair.apply_path.exists()
    assert all(Path(p).is_file() for p in result["report_paths"]+list(result["output_paths"].values()))
    before=snapshot(tmp_data_dirs);preview=request()
    assert snapshot(tmp_data_dirs)==before and preview["next_action"]=="generate_derivation"
    calls.clear();result=confirm_preview(preview)
    assert result["status"]=="executed" and len([c for c in calls if c[1].get("confirm")])==1
    assert len(lecture_calls)==1 and len(derivation_calls)==1
    assert pair.prompt_examples_path.is_file() and pair.apply_path.is_file()
    assert "transcript body must not leak" not in json.dumps(lecture_calls+derivation_calls)
    before=snapshot(tmp_data_dirs);calls.clear();complete=request()
    assert complete["status"]=="complete" and complete["report_writes"]==[] and snapshot(tmp_data_dirs)==before
    assert not any(c[1].get("confirm") for c in calls)


def test_real_cover_only_preserves_bytes_and_has_no_provider(tmp_data_dirs,monkeypatch):
    from tests.test_study_guide_bundle import TITLE
    _generated_bundle(tmp_data_dirs,monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
    paths.cover_path.unlink()
    before={p:p.read_bytes() for p in [paths.summary_path,paths.notes_path,paths.guide_path,paths.bundle_dir/"study_guide.lineage.json"]}
    block_external_effects(monkeypatch)
    monkeypatch.setattr(core().study_guide_bundle,"create_provider",tripwire)
    monkeypatch.setattr(core().workflow_derivation,"create_provider",tripwire)
    calls=record_real_runners(monkeypatch)
    preview=request();assert preview["next_action"]=="complete_cover"
    calls.clear();result=confirm_preview(preview)
    assert result["status"]=="executed" and paths.cover_path.is_file()
    assert before=={p:p.read_bytes() for p in before}
    executed=[c for c in calls if c[1].get("confirm")]
    assert len(executed)==1 and executed[0][1]["api_cost_ack"]==""


@pytest.mark.parametrize("state", ["empty","lecture","complete","legacy","custom","stale-summary","recovery","missing","finance"])
def test_real_preview_refusal_and_complete_are_zero_effects(tmp_data_dirs,monkeypatch,state):
    from corpus_ingest_core import run_report_io
    from tests.test_study_guide_bundle import TITLE
    from tests.test_workflow_derivation import _context
    from tests.test_workflow_derivation_lineage import generate
    context=_context(tmp_data_dirs,["Claude Code","Codex"])
    monkeypatch.setattr(core().workflow_derivation,"DEFAULT_CONTEXT_PATH",context)
    if state in ["empty","finance"]:_ready_episode(tmp_data_dirs,finance_body=state=="finance")
    elif state!="missing":_generated_bundle(tmp_data_dirs,monkeypatch)
    directory=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir
    if state in ["complete","legacy","custom"]:
        generate(monkeypatch,**({"workflow_context":context} if state=="custom" else {}))
    if state=="legacy":
        for name in ["study_guide.lineage.json","workflow_derivation.lineage.json"]:(directory/name).unlink()
    elif state=="stale-summary":
        source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
        source.write_bytes(source.read_bytes()+b"\nNew topic.\n")
    elif state=="recovery":directory.with_name(directory.name+".part").mkdir()
    before=snapshot(tmp_data_dirs);calls=record_real_runners(monkeypatch)
    block_external_effects(monkeypatch)
    for module in [core().study_guide_bundle,core().workflow_derivation,run_report_io]:
        for name in ["create_provider","write_part_staged_report_pair"]:
            if hasattr(module,name):monkeypatch.setattr(module,name,tripwire)
    for name in ["write_bytes","write_text","mkdir","rename","replace","unlink","rmdir"]:monkeypatch.setattr(Path,name,tripwire)
    result=request()
    assert snapshot(tmp_data_dirs)==before and not any(c[1].get("confirm") for c in calls)
    expected="action_available" if state in ["empty","lecture"] else "complete" if state=="complete" else "blocked"
    assert result["status"]==expected
    assert "transcript body must not leak" not in json.dumps(result)
    if state in ["recovery","missing"]:assert calls==[]


def test_real_cover_to_generation_race_never_uses_supplied_ack(tmp_data_dirs,monkeypatch):
    from corpus_ingest_core.errors import LLMProviderConfigError
    from tests.test_study_guide_bundle import TITLE
    _generated_bundle(tmp_data_dirs,monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE);paths.cover_path.unlink()
    preview=request();assert preview["next_action"]=="complete_cover"
    block_external_effects(monkeypatch);monkeypatch.setattr(core().study_guide_bundle,"create_provider",tripwire)
    original=core().study_guide_bundle.run_study_guide_bundle
    executed=[]
    def race(*args,**kwargs):
        if kwargs.get("confirm"):
            executed.append(kwargs.copy())
            # Simulate another writer changing only this owned fixture after the last preview.
            for path in [paths.summary_path,paths.notes_path,paths.guide_path]:path.unlink()
        return original(*args,**kwargs)
    monkeypatch.setattr(core().study_guide_bundle,"run_study_guide_bundle",race)
    with pytest.raises(LLMProviderConfigError):confirm_preview(preview)
    assert len(executed)==1 and executed[0]["api_cost_ack"]==""
    assert not paths.cover_path.exists()


def test_real_post_publication_report_failure_stops_without_retry(tmp_data_dirs,monkeypatch):
    from corpus_ingest_core.errors import StudyGuideBundleStateError
    from tests.test_study_guide_bundle import TITLE
    _ready_episode(tmp_data_dirs);block_external_effects(monkeypatch);fake_providers(monkeypatch)
    calls=record_real_runners(monkeypatch);preview=request();calls.clear()
    def report_failure(*args):raise OSError("PRIVATE_REPORT_FAILURE")
    monkeypatch.setattr(core().study_guide_bundle,"_write_run_report",report_failure)
    with pytest.raises(StudyGuideBundleStateError) as caught:confirm_preview(preview)
    assert caught.value.reason_code=="published_report_failed"
    assert len([c for c in calls if c[1].get("confirm")])==1
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
    assert paths.summary_path.is_file() and (paths.bundle_dir/"study_guide.lineage.json").is_file()


@pytest.mark.parametrize("anomaly", ["recovery","partial-pair","missing-body","untracked","stale","custom"])
def test_cover_exception_never_accepts_other_anomalies(tmp_data_dirs,monkeypatch,anomaly):
    from tests.test_study_guide_bundle import TITLE
    from tests.test_workflow_derivation import _context
    from tests.test_workflow_derivation_lineage import generate
    _generated_bundle(tmp_data_dirs,monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
    context=_context(tmp_data_dirs,["Claude Code","Codex"])
    monkeypatch.setattr(core().workflow_derivation,"DEFAULT_CONTEXT_PATH",context)
    if anomaly=="recovery":paths.bundle_dir.with_name(paths.bundle_dir.name+".old").mkdir()
    elif anomaly=="partial-pair":(paths.bundle_dir/"05_prompt_examples.md").write_text("fixture",encoding="utf-8")
    elif anomaly=="missing-body":paths.notes_path.unlink()
    elif anomaly=="untracked":(paths.bundle_dir/"study_guide.lineage.json").unlink()
    elif anomaly=="stale":
        source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE);source.write_bytes(source.read_bytes()+b"\nChanged input.\n")
    else:generate(monkeypatch,workflow_context=context)
    paths.cover_path.unlink()
    before=snapshot(tmp_data_dirs)
    block_external_effects(monkeypatch)
    monkeypatch.setattr(core().study_guide_bundle,"create_provider",tripwire)
    monkeypatch.setattr(core().workflow_derivation,"create_provider",tripwire)
    assert request()["status"]=="blocked" and snapshot(tmp_data_dirs)==before


@pytest.mark.parametrize("bad", ["missing-row","unsafe-row","recovery-row","unknown-role","bool-extra","wrong-record","mismatch","missing-output","foreign-id","network","readonly","plain-types"])
def test_cover_detail_unknown_or_unsafe_never_confirms(tmp_data_dirs,monkeypatch,bad):
    from tests.test_study_guide_bundle import TITLE
    _generated_bundle(tmp_data_dirs,monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE);paths.cover_path.unlink()
    q=core();value=q.learning_bundle_recovery.inspect_learning_bundle_recovery(PODCAST,EPISODE)
    assert value["status"]=="blocked" and value["reason"]=="manual_review_required"
    if bad=="missing-row":value["locations"].pop()
    elif bad=="unsafe-row":value["locations"][1].update(status="blocked",reason="unsafe_path")
    elif bad=="recovery-row":value["locations"][1].update(status="observed",reason="observed")
    elif bad=="unknown-role":value["locations"][0]["roles"]["03"]=None
    elif bad=="bool-extra":value["locations"][0]["extra_files"]=False
    elif bad in ["wrong-record","mismatch","missing-output"]:
        record=value["locations"][0]["records"]["study_guide"]
        if bad=="wrong-record":record["status"]="invalid_record"
        else:record["output_status"]="mismatch" if bad=="mismatch" else "missing"
    elif bad=="foreign-id":value["episode_ref"]="other"
    elif bad=="network":value["network_access"]=True
    elif bad=="readonly":value["read_only"]=1
    else:value["locations"][0]["reason"]=PretendText("PRIVATE")
    monkeypatch.setattr(q.learning_bundle_recovery,"inspect_learning_bundle_recovery",lambda *a:deepcopy(value))
    calls=record_real_runners(monkeypatch);before=snapshot(tmp_data_dirs)
    block_external_effects(monkeypatch)
    monkeypatch.setattr(q.study_guide_bundle,"create_provider",tripwire)
    result=request(confirm=True,expected_action="complete_cover",expected_plan_id="a"*64,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert result["status"]=="blocked" and not any(c[1].get("confirm") for c in calls)
    assert snapshot(tmp_data_dirs)==before and "PRIVATE" not in json.dumps(result)


def test_real_cover_with_current_pair_preserves_all_existing_bytes(tmp_data_dirs,monkeypatch):
    from tests.test_study_guide_bundle import TITLE
    from tests.test_workflow_derivation import _context
    from tests.test_workflow_derivation_lineage import generate
    _generated_bundle(tmp_data_dirs,monkeypatch)
    context=_context(tmp_data_dirs,["Claude Code","Codex"])
    monkeypatch.setattr(core().workflow_derivation,"DEFAULT_CONTEXT_PATH",context)
    generate(monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE);paths.cover_path.unlink()
    before={p:p.read_bytes() for p in paths.bundle_dir.iterdir()}
    block_external_effects(monkeypatch)
    monkeypatch.setattr(core().study_guide_bundle,"create_provider",tripwire)
    monkeypatch.setattr(core().workflow_derivation,"create_provider",tripwire)
    preview=request();assert preview["next_action"]=="complete_cover"
    assert "cover_absence_checked_separately" in preview["warnings"]
    result=confirm_preview(preview)
    assert result["status"]=="executed" and all(p.read_bytes()==raw for p,raw in before.items())


@pytest.mark.parametrize("error_type", [ValueError, RuntimeError])
def test_unknown_confirmed_executor_error_warns_uncertain_state(monkeypatch, error_type):
    q,calls=install(monkeypatch,confirmed=error_type("PRIVATE_AFTER_DISPATCH"))
    preview=request();calls.clear()
    with pytest.raises(q.LearningWorkflowAdvanceError,match="may have changed local files") as caught:
        request(confirm=True,expected_action="generate_lecture",expected_plan_id=preview["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK)
    assert len(calls)==3 and calls[-1][2]["confirm"] is True
    assert "PRIVATE" not in str(caught.value)
