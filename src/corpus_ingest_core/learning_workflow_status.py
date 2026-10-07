"""Read-only overview of existing learning diagnostics (SPEC051)."""
from __future__ import annotations

from typing import Any, Callable

from . import (learning_bundle_recovery, learning_workflow_next_step, storage,
               study_guide_bundle, study_guide_lineage, workflow_derivation,
               workflow_derivation_lineage)

INVALID_IDENTITY_MESSAGE = "Invalid explicit episode identity."
QUERY_ERROR_MESSAGE = "Learning workflow status could not be inspected safely."
WARNINGS = ["non_atomic_observation", "summary_transcript_freshness_not_evaluated",
            "no_execution_authorization", "publication_outcome_not_proven"]
LINEAGE_BLOCKERS = {"identity_unavailable", "unsafe_path", "recovery_required", "invalid_record",
                    "unsupported_schema", "record_unreadable", "identity_mismatch",
                    "inputs_unavailable", "outputs_unavailable"}


def _identity(podcast_id: object, episode_ref: object) -> None:
    if (not isinstance(podcast_id, str) or not isinstance(episode_ref, str)
            or episode_ref.casefold() in {"latest", "next"} or not storage.is_safe_episode_ref(episode_ref)):
        raise ValueError(INVALID_IDENTITY_MESSAGE)
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "identity")
    except (ValueError, TypeError):
        raise ValueError(INVALID_IDENTITY_MESSAGE) from None


def _base(value: Any, podcast_id: str, episode_ref: str, scope: str) -> bool:
    return (type(value) is dict and all(type(value.get(key)) is str for key in ("podcast_id", "episode_ref", "scope"))
            and value.get("podcast_id") == podcast_id
            and value.get("episode_ref") == episode_ref and value.get("scope") == scope
            and value.get("read_only") is True and value.get("network_access") is False)


def _recovery(value: Any, podcast_id: str, episode_ref: str) -> dict[str, Any]:
    if not _base(value, podcast_id, episode_ref, "learning_bundle_recovery"):
        raise ValueError("invalid observation")
    allowed = {"clear": {"no_recovery_entries"}, "recovery_present": {"recovery_entries_present"},
               "blocked": {"identity_unavailable", "unsafe_path", "inspection_unavailable", "manual_review_required"}}
    status, reason = value.get("status"), value.get("reason")
    if (type(status) is not str or type(reason) is not str or status not in allowed
            or reason not in allowed[status] or value.get("manual_review_required") is not (status != "clear")):
        raise ValueError("invalid observation")
    return {"status": status, "reason": reason, "manual_review_required": status != "clear"}


def _next(value: Any, podcast_id: str, episode_ref: str) -> dict[str, Any]:
    if (type(value) is not learning_workflow_next_step.LearningWorkflowNextStep
            or any(type(getattr(value, key)) is not str for key in
                   ("podcast_id", "episode_ref", "status", "lecture_mode", "derivation_mode",
                    "reason_code", "source_currentness", "completion_basis"))
            or value.podcast_id != podcast_id or value.episode_ref != episode_ref
            or value.read_only is not True or value.network_read is not False
            or value.source_currentness != "not_evaluated" or value.completion_basis != "existing_preview_contracts"):
        raise ValueError("invalid observation")
    mode = (value.lecture_mode, value.derivation_mode, value.reason_code)
    if value.status == "complete":
        valid = mode == ("reuse", "reuse", "previews_reusable") and value.blocked_stage is None and value.next_action is None
        valid = valid and value.requires_llm is None and value.requires_api_cost_ack is None
    elif value.status == "action_available":
        actions = {"generate_lecture": ("generation", "not_evaluated", "lecture_generation_needed"),
                   "complete_cover": ("cover_only", "not_evaluated", "cover_completion_needed"),
                   "generate_derivation": ("reuse", "generation", "derivation_generation_needed")}
        valid = type(value.next_action) is str and value.next_action in actions
        if valid:
            llm = value.next_action != "complete_cover"
            valid = (mode == actions[value.next_action] and value.blocked_stage is None
                     and value.requires_llm is llm and value.requires_api_cost_ack is llm)
    elif value.status == "blocked":
        stage_modes = {"lecture": ("blocked", "not_evaluated"), "derivation": ("reuse", "blocked")}
        common_reasons = {"unsafe_path", "recovery_required", "unexpected_preview"}
        reasons = {"lecture": common_reasons | {"lecture_prerequisite_failed", "derivation_conflict"},
                   "derivation": common_reasons | {"derivation_prerequisite_failed"}}
        valid = type(value.blocked_stage) is str and value.blocked_stage in stage_modes
        valid = (valid and mode[:2] == stage_modes[value.blocked_stage]
                 and type(value.reason_code) is str and value.reason_code in reasons[value.blocked_stage]
                 and value.next_action is None and value.requires_llm is None and value.requires_api_cost_ack is None)
    else:
        valid = False
    if not valid:
        raise ValueError("invalid observation")
    return {"status": value.status, "reason": value.reason_code, "lecture_mode": value.lecture_mode,
            "derivation_mode": value.derivation_mode, "blocked_stage": value.blocked_stage,
            "next_action": value.next_action, "requires_llm": value.requires_llm,
            "requires_api_cost_ack": value.requires_api_cost_ack}


def _lineage(value: Any, podcast_id: str, episode_ref: str, family: str) -> dict[str, Any]:
    if not _base(value, podcast_id, episode_ref, family + "_inputs_outputs"):
        raise ValueError("invalid observation")
    allowed = {"current": {"matches_record"}, "stale": {"observed_changes"}, "untracked": {"no_record"},
               "not_generated": {"no_study_guide" if family == "study_guide" else "no_derivation"},
               "blocked": LINEAGE_BLOCKERS | {"incomplete_lecture" if family == "study_guide" else "incomplete_pair"}}
    if family == "workflow_derivation":
        allowed["not_evaluated"] = {"custom_context"}
    status, reason, changed = value.get("status"), value.get("reason"), value.get("changed_roles")
    codec = study_guide_lineage if family == "study_guide" else workflow_derivation_lineage
    roles = codec.CHANGED_ROLES
    if (type(status) is not str or type(reason) is not str or status not in allowed or reason not in allowed[status]
            or type(changed) is not list or any(type(role) is not str or role not in roles for role in changed)
            or changed != [role for role in roles if role in changed]
            or (bool(changed) != (status == "stale"))):
        raise ValueError("invalid observation")
    return {"status": status, "reason": reason, "changed_roles": list(changed)}


def _empty_next(status: str, reason: str) -> dict[str, Any]:
    blocked = status == "blocked"
    return {"status": status, "reason": reason, "lecture_mode": "blocked" if blocked else "not_evaluated",
            "derivation_mode": "not_evaluated", "blocked_stage": "inspection" if blocked else None,
            "next_action": None, "requires_llm": None, "requires_api_cost_ack": None}


def _empty_lineage(status: str, reason: str) -> dict[str, Any]:
    return {"status": status, "reason": reason, "changed_roles": []}


def _attempt(call: Callable, project: Callable, fallback: dict[str, Any], podcast_id: str, episode_ref: str) -> dict[str, Any]:
    try:
        return project(call(podcast_id, episode_ref))
    except Exception:
        # A child failure or contract drift is unknown, never a safe readiness claim.
        return fallback


def _conflict(step: dict[str, Any], study: dict[str, Any], deriv: dict[str, Any]) -> bool:
    if step["status"] == "blocked":
        return False
    existing = {"current", "stale", "untracked", "not_evaluated"}
    return ((step["lecture_mode"] in {"reuse", "cover_only"} and study["status"] == "not_generated")
            or (step["lecture_mode"] == "generation" and study["status"] in existing)
            or (step["derivation_mode"] == "reuse" and deriv["status"] == "not_generated")
            or (step["derivation_mode"] == "generation" and deriv["status"] in existing))


def inspect_learning_workflow_status(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Compose four scoped observations, never authorize or execute an action."""
    _identity(podcast_id, episode_ref)
    recovery = _attempt(learning_bundle_recovery.inspect_learning_bundle_recovery,
                        lambda v: _recovery(v, podcast_id, episode_ref),
                        {"status": "blocked", "reason": "inspection_unavailable", "manual_review_required": True},
                        podcast_id, episode_ref)
    reasons = []
    if recovery["status"] != "clear":
        step = _empty_next("not_evaluated", "recovery_gate")
        study = _empty_lineage("not_evaluated", "recovery_gate")
        deriv = _empty_lineage("not_evaluated", "recovery_gate")
        reasons.append("recovery_blocked" if recovery["status"] == "blocked" else "recovery_present")
    else:
        step = _attempt(learning_workflow_next_step.suggest_learning_workflow_next_step,
                        lambda v: _next(v, podcast_id, episode_ref), _empty_next("blocked", "inspection_unavailable"),
                        podcast_id, episode_ref)
        study = _attempt(study_guide_bundle.inspect_study_guide_lineage,
                         lambda v: _lineage(v, podcast_id, episode_ref, "study_guide"),
                         _empty_lineage("blocked", "inspection_unavailable"), podcast_id, episode_ref)
        deriv = _attempt(workflow_derivation.inspect_workflow_derivation_lineage,
                         lambda v: _lineage(v, podcast_id, episode_ref, "workflow_derivation"),
                         _empty_lineage("blocked", "inspection_unavailable"), podcast_id, episode_ref)
        if step["status"] == "blocked":
            reasons.append("next_step_blocked")
        for key, observation in (("study_guide_lineage", study), ("workflow_derivation_lineage", deriv)):
            if observation["status"] in {"blocked", "stale", "untracked"}:
                reasons.append(key + "_" + observation["status"])
            elif observation["status"] == "not_evaluated":
                reasons.append("workflow_derivation_context_not_evaluated")
        if _conflict(step, study, deriv):
            reasons.append("observations_conflict")
    blocked = any(section["status"] == "blocked" for section in (recovery, step, study, deriv))
    return {"podcast_id": podcast_id, "episode_ref": episode_ref,
            "status": "blocked" if blocked else "attention_required" if reasons else "observed",
            "attention_required": bool(reasons), "attention_reasons": reasons, "recovery": recovery,
            "next_step": step, "study_guide_lineage": study, "workflow_derivation_lineage": deriv,
            "scope": "learning_workflow_status", "read_only": True, "network_access": False,
            "warnings": list(WARNINGS)}
