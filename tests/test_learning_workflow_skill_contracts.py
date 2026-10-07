"""045: backend characterization and static instruction/fixture contracts.

These checks do not execute an agent or prove model obedience.
"""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from corpus_ingest_core import mcp_server, storage, study_guide_bundle, workflow_derivation
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_study_guide_bundle import EPISODE, PODCAST, TITLE, _generated_bundle, _ready_episode
from tests.test_workflow_derivation import _context, _ready_lecture

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "study-guide-bundle": "generate_study_guide_bundle",
    "workflow-derivation-bundle": "derive_workflow_bundle",
}
LECTURE = {"00_video_info.md", "03_full_summary.md", "04_learning_notes.md", "07_final_study_guide.md"}
PAIR = {"05_prompt_examples.md", "06_apply_to_my_workflow.md"}


def skill_text(name: str) -> str:
    path = ROOT / ".agents" / "skills" / name / "SKILL.md"
    assert path.is_file(), f"Missing portable Skill: {name}"
    return path.read_text(encoding="utf-8")


def rule_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^## (P\d{2})\b.*$", text, re.M))
    return {
        match[1]: text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, match in enumerate(matches)
    }


def assert_portable(name: str, description: str) -> None:
    text = skill_text(name)
    assert text.splitlines()[:4] == ["---", f"name: {name}", f"description: {description}", "---"]
    assert list(rule_sections(text)) == [f"P{i:02d}" for i in range(1, 11)]
    assert SKILLS[name] in text
    assert all(tool not in text for skill, tool in SKILLS.items() if skill != name)
    assert SEMANTIC_API_COST_ACK in rule_sections(text)["P05"]
    for marker in ("```", "codex-only", "hermes-only", "scripts/", "python ", "powershell"):
        assert marker not in text.lower()


def assert_clauses(name: str, clauses: dict[str, tuple[str, ...]]) -> None:
    sections = rule_sections(skill_text(name))
    for rule, fragments in clauses.items():
        for fragment in fragments:
            assert fragment in sections[rule], f"{name} {rule} lacks: {fragment}"


def _forbid_provider(*args, **kwargs):
    pytest.fail("This characterization must not construct a provider")


@pytest.mark.parametrize("tool_name", SKILLS.values())
def test_existing_five_parameter_surface(tool_name):
    parameters = inspect.signature(getattr(mcp_server, tool_name)).parameters
    assert list(parameters) == ["podcast_id", "episode_ref", "confirm", "force", "api_cost_ack"]
    assert [p.default for p in parameters.values()] == ["", "", False, False, ""]


@pytest.mark.parametrize("branch", ["generate", "reuse", "cover-only", "force"])
def test_real_lecture_preview_cost_roles_and_reports(tmp_data_dirs, monkeypatch, branch):
    if branch == "generate":
        _ready_episode(tmp_data_dirs)
    else:
        _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    if branch == "cover-only":
        (directory / "00_video_info.md").unlink()
    monkeypatch.setattr(study_guide_bundle, "create_provider", _forbid_provider)
    before = {str(p): p.read_bytes() for p in tmp_data_dirs.rglob("*") if p.is_file()}
    result = mcp_server.generate_study_guide_bundle(PODCAST, EPISODE, force=branch == "force")
    assert result["ok"] is True
    assert result["run_mode"] == "dry-run"
    assert result["inputs"] == {"podcast_id": PODCAST, "episode_ref": EPISODE, "force": branch == "force"}
    assert result["requires_llm"] is (branch in {"generate", "force"})
    writes = {Path(p).name for p in result["writes"]}
    reuses = {Path(p).name for p in result["reuses"]}
    assert writes == (set() if branch == "reuse" else {"00_video_info.md"} if branch == "cover-only" else LECTURE)
    assert reuses == LECTURE - writes
    assert len(set(result["report_writes"])) == 2
    assert result["network_read"] is False
    assert before == {str(p): p.read_bytes() for p in tmp_data_dirs.rglob("*") if p.is_file()}


@pytest.mark.parametrize("branch", ["generate", "reuse", "force"])
def test_real_derivation_preview_pair_is_cost_authority(tmp_data_dirs, monkeypatch, branch):
    _ready_lecture(tmp_data_dirs)
    monkeypatch.setattr(workflow_derivation, "DEFAULT_CONTEXT_PATH", _context(tmp_data_dirs, ["Claude Code", "Codex"]))
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    if branch != "generate":
        for name in PAIR:
            (directory / name).write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(workflow_derivation, "create_provider", _forbid_provider)
    result = mcp_server.derive_workflow_bundle(PODCAST, EPISODE, force=branch == "force")
    assert result["ok"] is True
    assert result["run_mode"] == "preview"
    assert "requires_llm" not in result and "report_writes" not in result
    assert {Path(p).name for p in result["writes"]} == (set() if branch == "reuse" else PAIR)
    assert {Path(p).name for p in result["reuses"]} == (PAIR if branch == "reuse" else set())
    assert any("external LLM" in risk for risk in result["risks"])
    if branch == "reuse":
        confirmed = mcp_server.derive_workflow_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
        assert confirmed["ok"] is True and confirmed["data"]["reused"] is True
        assert Path(confirmed["data"]["report_json_path"]).is_file()
        assert Path(confirmed["data"]["report_markdown_path"]).is_file()


CASES_PATH = ROOT / "tests/fixtures/learning_workflow_skill_cases.json"


def _dialogue_cases():
    assert CASES_PATH.is_file(), "Missing C01-C20 offline dialogue oracle"
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert payload["evidence_kind"] == "offline acceptance oracle; not agent execution"
    return payload["cases"]


def test_dialogue_oracle_covers_cases_and_real_instruction_rules():
    cases = _dialogue_cases()
    assert {case["case_id"] for case in cases} == {f"C{i:02d}" for i in range(1, 21)}
    assert len({case["id"] for case in cases}) == len(cases)
    for case_id in ("C06", "C07", "C08", "C09", "C10", "C12", "C13", "C14", "C15", "C17", "C18", "C20"):
        assert {c["skill"] for c in cases if c["case_id"] == case_id} == set(SKILLS), case_id
    for case in cases:
        assert case["rule_ids"]
        assert set(case["rule_ids"]) <= set(rule_sections(skill_text(case["skill"]))), case["id"]


def test_dialogue_oracle_call_and_response_evidence_is_consistent():
    # Validate supplied expected traces, never execute a fake agent.
    for case in _dialogue_cases():
        calls = case["expected_calls"]
        confirms = [c for c in calls if c["arguments"]["confirm"]]
        previews = [c for c in calls if not c["arguments"]["confirm"]]
        assert len(confirms) <= 1 and len(previews) <= 1, case["id"]
        for call in calls:
            assert call["tool"] == SKILLS[case["skill"]], case["id"]
            args = call["arguments"]
            assert set(args) == {"podcast_id", "episode_ref", "force", "confirm", "api_cost_ack"}
            assert {k: args[k] for k in case["request"]} == case["request"], case["id"]
        if previews:
            assert calls[0] == previews[0] and previews[0]["arguments"]["api_cost_ack"] == ""
        outcome = case["transport_outcome"]
        assert outcome in {"not_called", "response", "timeout", "disconnected"}
        if not confirms:
            assert outcome == "not_called" and case["confirm_fixture"] is None, case["id"]
        else:
            assert len(previews) == 1 and calls[-1] == confirms[0]
            assert case["preview_fixture"]["ok"] is True
            assert case["user_reply"]["approval"] == "approved"
            assert outcome != "not_called"
            if case["cost_class"] == "generate":
                assert case["user_reply"]["api_cost_ack"] == SEMANTIC_API_COST_ACK
                assert confirms[0]["arguments"]["api_cost_ack"] == case["user_reply"]["api_cost_ack"]
            else:
                assert confirms[0]["arguments"]["api_cost_ack"] == "", case["id"]
        assert (case["confirm_fixture"] is not None) == (outcome == "response"), case["id"]
        assert case["expected_report"]
        evidence = json.dumps([case["preview_fixture"], case["confirm_fixture"]])
        for marker in case.get("sensitive_markers", []):
            assert marker in evidence and marker not in case["expected_report"], case["id"]


def test_negative_consent_and_schema_cases_have_no_confirm():
    for case in _dialogue_cases():
        if case["case_id"] in {"C07", "C08", "C09", "C10", "C12", "C13", "C14", "C15"}:
            assert not any(c["arguments"]["confirm"] for c in case["expected_calls"]), case["id"]
        if case["case_id"] == "C08":
            expected = {"denied": "stop", "absent": "wait", "ambiguous": "clarify", "conditional": "clarify"}
            assert case["expected_next"] == expected[case["user_reply"]["approval"]]
        if case["case_id"] in {"C11", "C16", "C17", "C18", "C19"}:
            assert case["expected_next"] == "stop"


def test_generic_configuration_error_does_not_establish_state_drift():
    for case in _dialogue_cases():
        if case["case_id"] == "C11":
            assert "State changed" not in case["expected_report"]
            assert "uncertain" in case["expected_report"]
            assert case["expected_calls"][-1]["arguments"]["api_cost_ack"] == ""
            assert case["expected_next"] == "stop"



def test_malformed_preview_examples_have_the_claimed_defects_and_instruction():
    required = {"missing-field", "wrong-type", "duplicate-role", "mixed-directories", "identity", "cost-combination", "extra-role", "missing-role"}
    cases = _dialogue_cases()
    for skill in SKILLS:
        negative = [c for c in cases if c["skill"] == skill and c["case_id"] == "C13"]
        assert required <= {c["variant"] for c in negative}
        instruction = rule_sections(skill_text(skill))["P03"]
        for clause in ("Missing fields", "wrong types", "identity mismatch", "duplicates", "extra/missing roles", "mixed directories", "stop without confirm"):
            assert clause in instruction
        for c in negative:
            preview, defect = c["preview_fixture"], c["variant"]
            if defect == "missing-field": assert "run_mode" not in preview
            elif defect == "wrong-type": assert not isinstance(preview["writes"], list)
            elif defect == "duplicate-role": assert len(set(preview["writes"])) < len(preview["writes"])
            elif defect == "mixed-directories": assert len({p.rsplit("/", 1)[0] for p in preview["writes"]}) > 1
            elif defect == "identity": assert preview["inputs"]["episode_ref"] != c["request"]["episode_ref"]
            elif defect == "cost-combination":
                assert preview.get("requires_llm") is False if skill == "study-guide-bundle" else bool(preview["reuses"])
            elif defect == "extra-role": assert any(p.endswith("extra.bin") for p in preview["writes"])
            elif defect == "missing-role": assert len(preview["writes"]) < (4 if skill == "study-guide-bundle" else 2)
            elif defect == "missing-cost": assert "requires_llm" not in preview
            elif defect == "nonboolean-cost": assert type(preview["requires_llm"]) is not bool
            elif defect == "missing-reports": assert "report_writes" not in preview
            else: pytest.fail(defect)
    windows = [c for c in cases if c["variant"] == "windows-paths"]
    assert windows and all(chr(92) in p for p in windows[0]["preview_fixture"]["writes"])
    assert all("either slash style" in rule_sections(skill_text(s))["P03"] for s in SKILLS)


@pytest.mark.parametrize("relative", [".agents/skills/README.md", "docs/mcp-usage.md", "docs/agent-handoff.md", "docs/verification-matrix.md"])
def test_operator_docs_explain_both_skills_and_limits(relative):
    text = (ROOT / relative).read_text(encoding="utf-8").lower()
    for fragment in ("study-guide-bundle", "workflow-derivation-bundle", "independent requests", "run reports", "pre-existing recovery", "offline"):
        assert fragment in text, (relative, fragment)


def test_derivation_published_outcomes_use_fixed_backend_evidence():
    from corpus_ingest_core.errors import _WORKFLOW_DERIVATION_STATE_MESSAGES
    cases = [c for c in _dialogue_cases() if c["skill"] == "workflow-derivation-bundle" and c["case_id"] == "C16"]
    expected = {"published_cleanup_failed", "published_report_failed", "reused_report_failed"}
    assert {c["variant"] for c in cases} == expected
    for c in cases:
        assert c["confirm_fixture"] == {"ok": False, "error_type": "WorkflowDerivationStateError", "message": _WORKFLOW_DERIVATION_STATE_MESSAGES[c["variant"]]}
        assert c["expected_next"] == "stop"
