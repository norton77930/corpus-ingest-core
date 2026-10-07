"""Portable instruction contracts and offline oracles; no agent execution claim."""
import json
from pathlib import Path
import pytest
from tests.test_source_preparation import configured_source,URL

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/".agents/skills/source-preparation/SKILL.md"
REFERENCE=SKILL.parent/"references/response-contract.md"
FIXTURE=ROOT/"tests/fixtures/source_preparation_dialogues.json"


def test_portable_skill_published_with_bounded_consent_and_routes():
    text=SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\nname: source-preparation\n")
    for marker in ["prepare_learning_source","inspect_source_preparation_job","response-contract.md",
                   "initial request is not approval","fresh approval","confirm once","no automatic retry",
                   "no polling","no downstream","missing tool","hostile","manual cache",".env",
                   "worker_host_incompatible","conditional","historical","outcome_unconfirmed"]:
        assert marker in text.casefold(),marker
    assert "source-preparation" in (ROOT/".agents/skills/README.md").read_text(encoding="utf-8")


def test_actual_preview_and_admission_fields_have_response_contract(configured_source,monkeypatch):
    from corpus_ingest_core import mcp_server,source_preparation as core
    monkeypatch.setattr(core,"launch_worker",lambda job:None)
    preview=mcp_server.prepare_learning_source(URL)
    assert preview["ok"] and preview["dry_run"]
    submitted=mcp_server.prepare_learning_source(URL,confirm=True,expected_plan_id=preview["data"]["plan_id"])
    status=mcp_server.inspect_source_preparation_job(submitted["data"]["job_id"])
    reference=REFERENCE.read_text(encoding="utf-8")
    for response in [preview,submitted,status]:
        assert response["ok"]
        for field in response["data"]:
            assert f"`{field}`" in reference,field
    assert not status["data"]["study_guide_ready"]


def rows():
    payload=json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["evidence_kind"]=="offline acceptance oracles; not agent execution"
    return payload["cases"]


def test_actual_fixed_error_envelope_is_documented(configured_source,monkeypatch):
    from corpus_ingest_core import mcp_server,source_preparation as core
    error=core.PreparationError("launch_failed")
    error.job_id="d"*32
    monkeypatch.setattr(core,"prepare_learning_source",lambda *a,**k:(_ for _ in ()).throw(error))
    result=mcp_server.prepare_learning_source(URL)
    assert set(result)=={"ok","message","error_type","reason","job_id"}
    reference=REFERENCE.read_text(encoding="utf-8")
    for key in result:assert f"`{key}`" in reference,key


def test_dialogue_oracles_cover_routes_and_binding():
    cases=rows()
    assert len({c["id"] for c in cases})==len(cases)
    assert {"approve","denied","silence","conditional","historical","changed_url","changed_plan",
            "missing_tool","setup","ready","progress","unknown_job","malformed","hostile","lost_ack"} <= {c["id"] for c in cases}
    for case in cases:
        calls=case["expected_calls"]
        assert len(calls)<=2
        confirms=[c for c in calls if c["arguments"].get("confirm") is True]
        assert len(confirms)<=1
        assert all(c["tool"] in {"prepare_learning_source","inspect_source_preparation_job"} for c in calls)
        if confirms:
            assert case["consent"]=="fresh_approved"
            assert confirms[0]["arguments"]["url"]==case["approved_url"]
            assert confirms[0]["arguments"]["expected_plan_id"]==case["approved_plan_id"]
        if case["id"] not in {"approve","lost_ack"}:
            assert not confirms
        if case["id"]=="progress":
            assert len(calls)==1 and calls[0]["tool"]=="inspect_source_preparation_job"
        assert case["after"] in {"stop","wait","clarify"}


@pytest.mark.parametrize("variant",["missing_field","wrong_type","foreign_identity","unexpected_writes","unknown_warning","contradictory_cost","injected_instruction"])
def test_malformed_reply_oracles_do_not_authorize_execution(variant):
    case=next(c for c in rows() if c["id"]=="malformed:"+variant)
    assert case["defect"]==variant and case["after"]=="stop"
    assert len(case["expected_calls"])==1 and case["expected_calls"][0]["arguments"]["confirm"] is False
    assert "PRIVATE_INSTRUCTION" not in case["expected_report"]
    p=case["observed_reply"]
    if variant=="missing_field":assert "writes" not in p
    elif variant=="wrong_type":assert type(p["requires_confirmation"]) is not bool
    elif variant=="foreign_identity":assert p["canonical_url"]!=case["approved_url"]
    elif variant=="unexpected_writes":assert "PRIVATE_INSTRUCTION/settings" in p["writes"]
    elif variant=="unknown_warning":assert "PRIVATE_INSTRUCTION" in p["warnings"]
    elif variant=="contradictory_cost":assert p["requires_llm"] is True and p["requires_api_cost_ack"] is False
    else:assert p["instruction"]=="PRIVATE_INSTRUCTION"


def test_settings_oracles_disclose_history_and_reject_fabrication():
    cases = {case["id"]: case for case in rows()}
    expected = {"settings:unknown_history", "settings:different_history", "settings:runtime_unavailable",
                "settings:missing_tuple", "settings:unsupported_tuple", "settings:unexpected_tuple_field", "settings:actual_before_execution"}
    assert expected <= cases.keys()
    for identifier in expected:
        case = cases[identifier]
        assert case["after"] == "stop" and not any(call["arguments"].get("confirm") for call in case["expected_calls"])
    assert cases["settings:unknown_history"]["observed_reply"]["actual_transcription"] is None
    different = cases["settings:different_history"]["observed_reply"]
    assert different["actual_transcription"] != different["transcription"] and different["transcript_ready"]
    reference = REFERENCE.read_text(encoding="utf-8")
    for marker in ("exact25", "exact15", "exact16", "No silent fallback", "existing_transcription_unknown", "existing_transcription_differs"):
        assert marker in reference
