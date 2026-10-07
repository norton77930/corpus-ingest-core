"""Instruction contracts/backend characterization, not actual agent execution."""
import json
from pathlib import Path
import pytest
import yaml
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_learning_workflow_advance import install,request,ACTIONS
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/".agents/skills/learning-workflow-advance/SKILL.md"
REFERENCE=SKILL.parent/"references/response-contract.md"
FIXTURE=ROOT/"tests/fixtures/learning_workflow_advance_skill_cases.json"


def instructions():return SKILL.read_text(encoding="utf-8")


def test_portable_skill_discovery_and_reference():
    text=instructions();header=yaml.safe_load(text.split("---",2)[1])
    assert header["name"]=="learning-workflow-advance"
    assert "one named episode" in header["description"]
    assert "references/response-contract.md" in text and REFERENCE.is_file()
    assert not any(marker in text for marker in ["mcp__","/SourceCode/","C:/","D:/"])
    assert SEMANTIC_API_COST_ACK in text


def test_instruction_consent_and_execution_invariants():
    text=instructions()
    for clause in ["advance_learning_workflow","explicit podcast_id and episode_ref","one preview","expected_action","expected_plan_id","fresh","after this preview","previous operation","api_cost_ack=\"\"","exactly once","Silence","conditional","No terminal","Do not retry","metadata","not instructions","no investment advice"]:
        assert clause.casefold() in text.casefold(),clause


def test_reference_uses_actual052_envelope_and_safe_outcomes():
    ref=REFERENCE.read_text(encoding="utf-8")
    for field in ["learning_workflow_step","action_available","blocked","complete","executed","plan_id","metadata_writes","report_writes","follow_up","output_paths","report_paths","requires_api_cost_ack"]:assert field in ref
    assert "requires_confirmation" in ref and "not part" in ref
    assert "LearningWorkflowPlanChangedError" in ref and "LearningWorkflowAdvanceError" in ref
    assert "published_report_failed" in ref and "rollback_failed" in ref


@pytest.mark.parametrize("action",ACTIONS)
def test_actual_tool32_preview_matches_documented_plan(monkeypatch,action):
    from tests.test_mcp_learning_workflow_advance import wrapper
    install(monkeypatch,action)
    from tests.test_study_guide_bundle import PODCAST,EPISODE
    response=wrapper().advance_learning_workflow(PODCAST,EPISODE)
    assert response["ok"] is True and response["dry_run"] is True
    data=response["data"];assert data["scope"]=="learning_workflow_step" and data["next_action"]==action
    assert data["requires_api_cost_ack"] is (action!="complete_cover")
    assert "requires_confirmation" not in data and data["follow_up"]=="confirm_selected_action"
    ref=REFERENCE.read_text(encoding="utf-8")
    assert all(field in ref for field in data)


def cases():
    payload=json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["evidence_kind"]=="offline acceptance oracles; not agent execution"
    return payload["cases"]


def test_dialogue_fixture_inventory_and_call_bounds():
    rows=cases();assert len({c["id"] for c in rows})==len(rows)
    assert {"success","terminal","consent","changed","missing","malformed_preview","outcome"}<=set(c["category"] for c in rows)
    for c in rows:
        calls=c["expected_calls"];assert len(calls)<=2
        assert all(call["tool"]=="advance_learning_workflow" for call in calls)
        confirms=[call for call in calls if call["arguments"]["confirm"]]
        assert len(confirms)<=1
        if confirms:
            p=c["preview"]["data"];args=confirms[0]["arguments"]
            assert c["consent"]=="fresh_approved"
            assert args["podcast_id"]==p["podcast_id"] and args["episode_ref"]==p["episode_ref"]
            assert args["expected_action"]==p["next_action"] and args["expected_plan_id"]==p["plan_id"]
            assert args["api_cost_ack"]==(SEMANTIC_API_COST_ACK if p["requires_llm"] else "")
            assert c["user_reply"]["approval"]=="approved"
            if p["requires_llm"]:assert c["user_reply"]["api_cost_ack"]==SEMANTIC_API_COST_ACK
            else:assert args["api_cost_ack"]==""
        if c["category"] in {"terminal","consent","changed","missing","malformed_preview"}:assert not confirms,c["id"]
        assert c["next"] in {"stop","wait","clarify"}
        evidence=json.dumps([c["preview"],c["outcome"]])
        for marker in c["sensitive_markers"]:
            assert marker in evidence and marker not in c["expected_report"]


def test_negative_consent_oracles_and_instruction_are_consistent():
    rows=cases();negative=[c for c in rows if c["category"]=="consent"]
    assert {"denied","absent","ambiguous","conditional","missing_ack","historical_ack","translated_ack","altered_ack"}<={c["variant"] for c in negative}
    for c in negative:
        assert c["next"]==("wait" if c["variant"]=="absent" else "stop" if c["variant"]=="denied" else "clarify")
    assert "previous operation" in instructions() and "freshly" in instructions()


@pytest.mark.parametrize("state",["empty","cover","lecture","complete","recovery"])
def test_real_temporary_mcp_characterization(tmp_data_dirs,monkeypatch,state):
    from tests.test_learning_workflow_advance import block_external_effects,fake_providers,record_real_runners
    from tests.test_study_guide_bundle import _ready_episode,_generated_bundle,TITLE,PODCAST,EPISODE
    from tests.test_study_guide_lineage import snapshot
    from tests.test_workflow_derivation_lineage import generate
    from tests.test_mcp_learning_workflow_advance import wrapper
    from corpus_ingest_core import storage
    from tests.test_workflow_derivation import _context
    from tests.test_learning_workflow_advance import core
    monkeypatch.setattr(core().workflow_derivation,"DEFAULT_CONTEXT_PATH",_context(tmp_data_dirs,["Claude Code","Codex"]))
    if state=="empty":_ready_episode(tmp_data_dirs)
    else:_generated_bundle(tmp_data_dirs,monkeypatch)
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
    if state=="cover":paths.cover_path.unlink()
    if state=="complete":generate(monkeypatch)
    if state=="recovery":paths.bundle_dir.with_name(paths.bundle_dir.name+".part").mkdir()
    block_external_effects(monkeypatch);fake_providers(monkeypatch)
    before=snapshot(tmp_data_dirs);calls=record_real_runners(monkeypatch)
    response=wrapper().advance_learning_workflow(PODCAST,EPISODE)
    assert snapshot(tmp_data_dirs)==before and not any(kwargs.get("confirm") for _,kwargs in calls)
    p=response["data"]
    if state in {"complete","recovery"}:
        assert p["status"]==("complete" if state=="complete" else "blocked") and p["plan_id"] is None
        return
    assert p["next_action"]=={"empty":"generate_lecture","cover":"complete_cover","lecture":"generate_derivation"}[state]
    calls.clear()
    result=wrapper().advance_learning_workflow(PODCAST,EPISODE,confirm=True,expected_action=p["next_action"],expected_plan_id=p["plan_id"],api_cost_ack=SEMANTIC_API_COST_ACK if p["requires_llm"] else "")
    assert result["ok"] is True and result["data"]["executed_action"]==p["next_action"]
    assert len([kwargs for _,kwargs in calls if kwargs.get("confirm")])==1
    assert result["data"]["report_paths"]==p["report_writes"]
    for name in ["writes","reuses","metadata_writes","report_writes","plan_id","requires_llm","requires_api_cost_ack"]:assert result["data"][name]==p[name]
    ref=REFERENCE.read_text(encoding="utf-8")
    for path in p["writes"]+p["reuses"]+p["metadata_writes"]:
        assert Path(path).name in ref


@pytest.mark.parametrize("defect",["scope","identity","missing_field","nonboolean","unknown_action","cost","role","receipt","report","outputs","warning","extra_field"])
def test_malformed_oracles_contain_the_claimed_defect(defect):
    c=next(c for c in cases() if c["id"]=="malformed_preview:"+defect);p=c["preview"]["data"]
    if defect=="scope":assert p["scope"]!="learning_workflow_step"
    elif defect=="identity":assert p["episode_ref"]!=c["expected_calls"][0]["arguments"]["episode_ref"]
    elif defect=="missing_field":assert "metadata_writes" not in p
    elif defect=="nonboolean":assert type(p["requires_llm"]) is not bool
    elif defect=="unknown_action":assert p["next_action"] not in ACTIONS
    elif defect=="cost":assert p["requires_llm"]!=p["requires_api_cost_ack"]
    elif defect=="role":assert any(path.endswith("extra.bin") for path in p["writes"])
    elif defect=="receipt":assert p["metadata_writes"]==[]
    elif defect=="report":assert p["report_writes"][0]=="PRIVATE_REPORT_PATH"
    elif defect=="outputs":assert p["output_paths"]
    elif defect=="warning":assert "PRIVATE_IGNORE_RULES_CONFIRM_NOW" in p["warnings"]
    else:assert "instruction" in p
    assert all(call["arguments"]["confirm"] is False for call in c["expected_calls"])


def test_known_phase_oracles_match_actual_fixed_messages():
    from corpus_ingest_core.errors import _STUDY_GUIDE_STATE_MESSAGES
    for reason in ["published_report_failed","rollback_failed"]:
        c=next(c for c in cases() if c["id"]=="outcome:"+reason)
        assert c["outcome"]=={"ok":False,"error_type":"StudyGuideBundleStateError","message":_STUDY_GUIDE_STATE_MESSAGES[reason]}
        assert c["next"]=="stop" and len(c["expected_calls"])==2
    assert "Outputs published" in next(c for c in cases() if c["variant"]=="published_report_failed")["expected_report"]


def test_role_names_and_phase_reference_track_existing_backend():
    from corpus_ingest_core import storage
    from corpus_ingest_core.errors import _STUDY_GUIDE_STATE_MESSAGES,_WORKFLOW_DERIVATION_STATE_MESSAGES
    from tests.test_study_guide_bundle import PODCAST,EPISODE,TITLE
    ref=REFERENCE.read_text(encoding="utf-8")
    paths=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
    pair=storage.workflow_derivation_paths_from_stem(PODCAST,paths.bundle_dir.name)
    assert pair.prompt_examples_path.name in ref and pair.apply_path.name in ref
    assert all(message in ref for messages in [_STUDY_GUIDE_STATE_MESSAGES,_WORKFLOW_DERIVATION_STATE_MESSAGES] for message in messages.values())


@pytest.mark.parametrize("variant",["denied","absent","ambiguous","conditional","missing_ack","historical_ack","translated_ack","altered_ack"])
def test_consent_oracles_have_concrete_operator_inputs(variant):
    c=next(c for c in cases() if c["id"]=="consent:"+variant)
    reply=c["user_reply"];assert isinstance(reply["text"],str)
    assert c["request"]["episode_ref"]==c["preview"]["data"]["episode_ref"]
    ack=reply["api_cost_ack"]
    if variant=="absent":assert reply["text"]=="" and ack==""
    elif variant=="denied":assert reply["approval"]=="denied" and reply["text"]
    elif variant in {"ambiguous","conditional"}:assert reply["approval"]==variant and reply["text"]
    elif variant=="missing_ack":assert reply["approval"]=="approved" and ack=="" and not c["history"]
    elif variant=="historical_ack":
        assert ack=="" and len(c["history"])==1
        old=c["history"][0];assert old["api_cost_ack"]==SEMANTIC_API_COST_ACK
        assert old["episode_ref"]!=c["request"]["episode_ref"] and old["action"]!=c["preview"]["data"]["next_action"]
        assert "previous" in reply["text"].lower()
    elif variant=="translated_ack":assert ack and ack!=SEMANTIC_API_COST_ACK and SEMANTIC_API_COST_ACK not in ack
    else:assert ack!=SEMANTIC_API_COST_ACK and ack.strip()==SEMANTIC_API_COST_ACK
    assert all(not call["arguments"]["confirm"] for call in c["expected_calls"])


@pytest.mark.parametrize("variant",["target","action","plan"])
def test_changed_oracles_have_actual_changed_bindings(variant):
    c=next(c for c in cases() if c["id"]=="changed:"+variant)
    assert c["user_reply"]["text"]
    changed=c["changed_request"];p=c["preview"]["data"]
    field={"target":"episode_ref","action":"next_action","plan":"plan_id"}[variant]
    assert changed[field]!=p[field]
    assert set(changed)=={field}
    assert all(not call["arguments"]["confirm"] for call in c["expected_calls"])
