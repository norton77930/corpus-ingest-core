from __future__ import annotations

import importlib

import pytest


def query_module():
    return importlib.import_module("corpus_ingest_core.learning_workflow_next_step")


@pytest.mark.parametrize("podcast,episode", [
    ("", "E1"), ("../bad", "E1"), (None, "E1"), ("p", None),
    ("p", ""), ("p", "../E1"), ("p", "latest"), ("p", "NeXt"),
    ("p", "E/1"), ("p", 7), (" p", "E1"),
])
def test_invalid_identity_precedes_any_child_access(monkeypatch, podcast, episode):
    query = query_module()
    def forbidden(*args, **kwargs):
        pytest.fail("invalid identity reached child")
    monkeypatch.setattr(query.study_guide_bundle, "run_study_guide_bundle", forbidden)
    monkeypatch.setattr(query.workflow_derivation, "run_workflow_derivation", forbidden)
    with pytest.raises(ValueError, match="^Invalid explicit episode identity[.]$"):
        query.suggest_learning_workflow_next_step(podcast, episode)


from dataclasses import asdict
import json
from types import SimpleNamespace
from pathlib import Path
from corpus_ingest_core import errors

PODCAST = "demo"
EPISODE = "Ab_C-1"
BUNDLE = "PRIVATE_ROOT/bundle"


def lecture(mode="generation", **changes):
    paths = [str(Path(BUNDLE) / name) for name in (
        "00_video_info.md", "03_full_summary.md", "04_learning_notes.md", "07_final_study_guide.md",
    )]
    obj = dict(podcast_id=PODCAST, episode_ref=EPISODE, confirm=False, run_mode="dry-run",
               bundle_dir=BUNDLE, reused=mode == "reuse",
               planned_writes=paths if mode == "generation" else paths[:1] if mode == "cover" else [],
               planned_reuses=paths if mode == "reuse" else paths[1:] if mode == "cover" else [],
               warnings=["PRIVATE_SENTINEL"], source_summary_path="PRIVATE_ROOT/source")
    obj.update(changes)
    return SimpleNamespace(**obj)


def install_previews(monkeypatch, first, second=None):
    q = query_module()
    calls = []
    def first_call(*args, **kwargs):
        calls.append(("lecture", args, kwargs))
        if isinstance(first, Exception):
            raise first
        return first
    def second_call(*args, **kwargs):
        calls.append(("derivation", args, kwargs))
        if second is None:
            pytest.fail("derivation was not expected")
        if isinstance(second, Exception):
            raise second
        return second
    monkeypatch.setattr(q.study_guide_bundle, "run_study_guide_bundle", first_call)
    monkeypatch.setattr(q.workflow_derivation, "run_workflow_derivation", second_call)
    return q, calls


def assert_safe(result):
    data = asdict(result)
    assert data["read_only"] is True and data["network_read"] is False
    assert data["source_currentness"] == "not_evaluated"
    assert data["completion_basis"] == "existing_preview_contracts"
    assert len(data["warnings"]) == 2
    assert "PRIVATE" not in json.dumps(data)
    if data["status"] != "action_available":
        for field in ("next_action", "suggested_call", "requires_llm", "requires_api_cost_ack"):
            assert data[field] is None
    return data


@pytest.mark.parametrize("mode,action,llm", [
    ("generation", "generate_lecture", True), ("cover", "complete_cover", False),
])
def test_lecture_action_short_circuits_and_preserves_identity(monkeypatch, mode, action, llm):
    q, calls = install_previews(monkeypatch, lecture(mode))
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["status"] == "action_available" and data["next_action"] == action
    assert data["requires_llm"] is llm and data["requires_api_cost_ack"] is llm
    assert data["derivation_mode"] == "not_evaluated"
    assert data["suggested_call"] == {
        "tool": "generate_study_guide_bundle",
        "arguments": {"podcast_id": PODCAST, "episode_ref": EPISODE, "confirm": False, "force": False},
    }
    assert calls == [("lecture", (PODCAST, EPISODE), {"confirm": False, "force": False})]


@pytest.mark.parametrize("changes", [
    {"confirm": True}, {"confirm": 0}, {"run_mode": "preview"}, {"podcast_id": "other"},
    {"episode_ref": "other"}, {"reused": 1}, {"planned_writes": []},
    {"planned_writes": "PRIVATE"}, {"planned_writes": ["a", "a", "a", "a"]},
    {"planned_writes": [None, "a", "b", "c"]}, {"planned_reuses": ["extra"]},
    {"reused": True}, {"bundle_dir": None},
])
def test_inconsistent_lecture_is_blocked(monkeypatch, changes):
    q, calls = install_previews(monkeypatch, lecture(**changes))
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["status"] == "blocked" and data["reason_code"] == "unexpected_preview"
    assert data["blocked_stage"] == "lecture" and len(calls) == 1


@pytest.mark.parametrize("first", [None, {}, SimpleNamespace()])
def test_missing_lecture_shape_is_blocked(monkeypatch, first):
    q, calls = install_previews(monkeypatch, first)
    result = q.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert result.reason_code == "unexpected_preview" and len(calls) == 1


@pytest.mark.parametrize("exc,reason", [
    (errors.StudyGuideBundleError("PRIVATE"), "lecture_prerequisite_failed"),
    (errors.PodcastIngestCoreError("PRIVATE"), "lecture_prerequisite_failed"),
    (ValueError("PRIVATE"), "lecture_prerequisite_failed"),
    (errors.StudyGuideBundleStateError("unsafe_path"), "unsafe_path"),
    (errors.StudyGuideBundleStateError("recovery_required"), "recovery_required"),
    (errors.StudyGuideBundleStateError("derivation_conflict"), "derivation_conflict"),
    (errors.StudyGuideBundleStateError("published_report_failed"), "unexpected_preview"),
    (errors.StudyGuideBundleStateError("PRIVATE"), "unexpected_preview"),
])
def test_lecture_failure_mapping_is_finite(monkeypatch, exc, reason):
    q, calls = install_previews(monkeypatch, exc)
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["status"] == "blocked" and data["reason_code"] == reason
    assert data["blocked_stage"] == "lecture" and len(calls) == 1


def test_child_invalid_identity_remains_fixed(monkeypatch):
    q, calls = install_previews(monkeypatch, errors.StudyGuideBundleStateError("invalid_identity"))
    with pytest.raises(ValueError, match="^Invalid explicit episode identity[.]$"):
        q.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert len(calls) == 1


@pytest.mark.parametrize("exc", [RuntimeError("PRIVATE"), OSError("PRIVATE"), KeyError("PRIVATE")])
def test_unknown_lecture_failure_is_fixed(monkeypatch, exc):
    q, calls = install_previews(monkeypatch, exc)
    with pytest.raises(q.LearningWorkflowQueryError) as caught:
        q.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert str(caught.value) == q.QUERY_ERROR_MESSAGE and len(calls) == 1



def derivation(mode="generation", **changes):
    paths = [str(Path(BUNDLE) / name) for name in ("05_prompt_examples.md", "06_apply_to_my_workflow.md")]
    obj = dict(podcast_id=PODCAST, episode_ref=EPISODE, confirm=False, run_mode="preview",
               lecture_dir=BUNDLE, reused=mode == "reuse",
               planned_writes=paths if mode == "generation" else [],
               planned_reuses=paths if mode == "reuse" else [], warnings=["PRIVATE_SENTINEL"])
    obj.update(changes)
    return SimpleNamespace(**obj)


@pytest.mark.parametrize("mode", ["generation", "reuse"])
def test_derivation_follows_lecture_reuse_only(monkeypatch, mode):
    q, calls = install_previews(monkeypatch, lecture("reuse"), derivation(mode))
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["lecture_mode"] == "reuse" and data["derivation_mode"] == mode
    assert calls == [(stage, (PODCAST, EPISODE), {"confirm": False, "force": False})
                     for stage in ("lecture", "derivation")]
    if mode == "reuse":
        assert data["status"] == "complete" and data["reason_code"] == "previews_reusable"
    else:
        assert data["status"] == "action_available" and data["next_action"] == "generate_derivation"
        assert data["requires_api_cost_ack"] is True
        assert data["suggested_call"]["tool"] == "derive_workflow_bundle"
        assert data["suggested_call"]["arguments"] == {
            "podcast_id": PODCAST, "episode_ref": EPISODE, "confirm": False, "force": False,
        }


@pytest.mark.parametrize("changes", [
    {"confirm": True}, {"run_mode": "dry-run"}, {"episode_ref": "OTHER"},
    {"lecture_dir": "PRIVATE_OTHER"}, {"planned_writes": []}, {"reused": 1},
    {"reused": True}, {"planned_reuses": ["extra"]}, {"planned_writes": ["a", "a"]},
    {"planned_writes": ["a", ""]}, {"planned_writes": ("a", "b")},
])
def test_inconsistent_derivation_is_blocked(monkeypatch, changes):
    q, calls = install_previews(monkeypatch, lecture("reuse"), derivation(**changes))
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["status"] == "blocked" and data["reason_code"] == "unexpected_preview"
    assert data["blocked_stage"] == "derivation" and len(calls) == 2


@pytest.mark.parametrize("exc,reason", [
    (errors.WorkflowDerivationError("PRIVATE"), "derivation_prerequisite_failed"),
    (ValueError("PRIVATE"), "derivation_prerequisite_failed"),
    (errors.WorkflowDerivationStateError("unsafe_path"), "unsafe_path"),
    (errors.WorkflowDerivationStateError("recovery_required"), "recovery_required"),
    (errors.WorkflowDerivationStateError("rollback_failed"), "unexpected_preview"),
])
def test_derivation_failure_is_stage_specific(monkeypatch, exc, reason):
    q, calls = install_previews(monkeypatch, lecture("reuse"), exc)
    data = assert_safe(q.suggest_learning_workflow_next_step(PODCAST, EPISODE))
    assert data["reason_code"] == reason and data["blocked_stage"] == "derivation"
    assert len(calls) == 2


def test_unknown_derivation_failure_is_safe(monkeypatch):
    q, calls = install_previews(monkeypatch, lecture("reuse"), RuntimeError("PRIVATE"))
    with pytest.raises(q.LearningWorkflowQueryError, match="^Learning workflow query could not be evaluated safely[.]$"):
        q.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert len(calls) == 2


def test_child_cannot_return_a_query_decision_as_a_preview(monkeypatch):
    q = query_module()
    forged = q._decision(PODCAST, EPISODE, lecture_mode="reuse", derivation_mode="reuse", reason="previews_reusable")
    q, calls = install_previews(monkeypatch, forged)
    result = q.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert result.status == "blocked" and result.reason_code == "unexpected_preview"


def test_mutated_state_reason_is_not_trusted(monkeypatch):
    exc = errors.StudyGuideBundleStateError("unsafe_path")
    exc.reason_code = ["PRIVATE"]
    q, calls = install_previews(monkeypatch, exc)
    assert q.suggest_learning_workflow_next_step(PODCAST, EPISODE).reason_code == "unexpected_preview"


def ready_real(root, monkeypatch):
    from tests.test_workflow_derivation import _ready_lecture, _context, PODCAST as real_podcast, EPISODE as real_episode, TITLE
    from tests.test_study_guide_bundle import _ready_episode
    from corpus_ingest_core import storage
    _ready_lecture(root)
    _ready_episode(root)
    context = _context(root, ["Codex"])
    monkeypatch.setattr(query_module().workflow_derivation, "DEFAULT_CONTEXT_PATH", context)
    return real_podcast, real_episode, storage.study_guide_bundle_paths(real_podcast, real_episode, TITLE), context


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() if p.is_file() else None
            for p in root.rglob("*") if not p.is_symlink()}


def run_real_read_only(root, monkeypatch, podcast, episode):
    from corpus_ingest_core import cache, llm_provider
    import socket
    q = query_module()
    def forbidden(*args, **kwargs):
        pytest.fail("query attempted a forbidden side effect")
    for module in (q.study_guide_bundle, q.workflow_derivation):
        monkeypatch.setattr(module, "create_provider", forbidden)
        monkeypatch.setattr(module, "_write_run_report", forbidden)
    monkeypatch.setattr(llm_provider, "create_provider", forbidden)
    monkeypatch.setattr(cache, "rebuild_cache", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    before = snapshot(root)
    result = q.suggest_learning_workflow_next_step(podcast, episode)
    assert snapshot(root) == before
    assert str(root) not in json.dumps(asdict(result))
    assert_safe(result)
    return result


@pytest.mark.parametrize("case,action", [
    ("generation", "generate_lecture"), ("cover", "complete_cover"),
    ("derivation", "generate_derivation"), ("reuse", None),
])
def test_real_previews_four_normal_decisions(tmp_data_dirs, monkeypatch, case, action):
    podcast, episode, paths, context = ready_real(tmp_data_dirs, monkeypatch)
    if case == "generation":
        for file in paths.bundle_dir.iterdir():
            file.unlink()
    elif case == "cover":
        paths.cover_path.unlink()
    elif case == "reuse":
        # Existing derivation reuse is presence-based; this is not quality/freshness validation.
        (paths.bundle_dir / "05_prompt_examples.md").write_bytes(b"")
        (paths.bundle_dir / "06_apply_to_my_workflow.md").write_bytes(b"outdated fixture")
    result = run_real_read_only(tmp_data_dirs, monkeypatch, podcast, episode)
    assert result.next_action == action
    assert result.status == ("complete" if case == "reuse" else "action_available")


@pytest.mark.parametrize("case,stage,reason", [
    ("partial_lecture", "lecture", "lecture_prerequisite_failed"),
    ("partial_pair", "derivation", "derivation_prerequisite_failed"),
    ("bad_context", "derivation", "derivation_prerequisite_failed"),
    ("missing_summary", "lecture", "lecture_prerequisite_failed"),
    ("nested_extra", "lecture", "unsafe_path"),
    ("conflict", "lecture", "derivation_conflict"),
    ("recovery", "lecture", "recovery_required"),
])
def test_real_refusals_are_read_only(tmp_data_dirs, monkeypatch, case, stage, reason):
    from corpus_ingest_core import storage
    from tests.test_workflow_derivation import TITLE
    podcast, episode, paths, context = ready_real(tmp_data_dirs, monkeypatch)
    if case == "partial_lecture":
        paths.notes_path.unlink()
    elif case == "partial_pair":
        (paths.bundle_dir / "05_prompt_examples.md").write_bytes(b"existing")
    elif case == "bad_context":
        context.write_text("allowed_tools: []", encoding="utf-8")
        for name in ("05_prompt_examples.md", "06_apply_to_my_workflow.md"):
            (paths.bundle_dir / name).write_bytes(b"existing")
    elif case == "missing_summary":
        storage.semantic_summary_asset_path(podcast, episode, TITLE).unlink()
    elif case == "nested_extra":
        (paths.bundle_dir / "nested").mkdir()
    elif case == "conflict":
        for file in paths.bundle_dir.iterdir():
            file.unlink()
        (paths.bundle_dir / "05_prompt_examples.md").write_bytes(b"existing")
    else:
        paths.bundle_dir.with_name(paths.bundle_dir.name + ".wfderive.old").mkdir()
    result = run_real_read_only(tmp_data_dirs, monkeypatch, podcast, episode)
    assert result.status == "blocked" and result.blocked_stage == stage and result.reason_code == reason
