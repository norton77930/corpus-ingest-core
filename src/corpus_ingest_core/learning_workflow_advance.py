"""One explicitly approved learning action over existing Core runners (SPEC052)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from . import (learning_bundle_recovery, learning_workflow_next_step, learning_workflow_status, llm_provider, storage, study_guide_bundle,
               study_guide_lineage, workflow_derivation, workflow_derivation_lineage)
from .errors import PodcastIngestCoreError
from .models import StudyGuideBundleResult, WorkflowDerivationResult

INVALID_REQUEST_MESSAGE = "Invalid learning workflow request."
PLAN_CHANGED_MESSAGE = "Learning workflow plan changed; preview again before confirming."
UNCERTAIN_MESSAGE = "The action may have changed local files; inspect local state before retrying."
FAILURE_MESSAGE = "Learning workflow action failed; inspect local state before retrying."
ACTIONS = {
    "generate_lecture": ("generation", "not_evaluated", "lecture_generation_needed"),
    "complete_cover": ("cover_only", "not_evaluated", "cover_completion_needed"),
    "generate_derivation": ("reuse", "generation", "derivation_generation_needed"),
}
ATTENTION = {
    "recovery_blocked", "recovery_present", "next_step_blocked", "study_guide_lineage_blocked",
    "study_guide_lineage_stale", "study_guide_lineage_untracked", "workflow_derivation_lineage_blocked",
    "workflow_derivation_lineage_stale", "workflow_derivation_lineage_untracked",
    "workflow_derivation_context_not_evaluated", "observations_conflict",
}
WARNINGS = ["single_action_only", "metadata_plan_binding_only", "non_atomic_observation",
            "summary_transcript_freshness_not_evaluated", "caller_must_serialize_writers",
            study_guide_bundle.CACHE_STALE_WARNING]


class LearningWorkflowPlanChangedError(PodcastIngestCoreError):
    """Detected approval metadata drift before confirmed dispatch."""


class LearningWorkflowAdvanceError(PodcastIngestCoreError):
    """An executor returned an unrecognizable outcome; local state is uncertain."""


def _validate(podcast_id: object, episode_ref: object, confirm: object,
              expected_action: object, expected_plan_id: object, api_cost_ack: object) -> None:
    if (type(podcast_id) is not str or type(episode_ref) is not str
            or not storage.is_safe_episode_ref(episode_ref) or episode_ref.casefold() in {"latest", "next"}
            or type(confirm) is not bool
            or any(type(value) is not str for value in (expected_action, expected_plan_id, api_cost_ack))):
        raise ValueError(INVALID_REQUEST_MESSAGE)
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "identity")
    except (TypeError, ValueError):
        raise ValueError(INVALID_REQUEST_MESSAGE) from None
    if (not confirm and (expected_action or expected_plan_id)) or (confirm and
            (expected_action not in ACTIONS or re.fullmatch(r"[0-9a-f]{64}", expected_plan_id) is None)):
        raise ValueError(INVALID_REQUEST_MESSAGE)


def _base(podcast_id: str, episode_ref: str, confirm: bool) -> dict[str, Any]:
    return dict(podcast_id=podcast_id, episode_ref=episode_ref, confirm=confirm,
                status="blocked", reason="inspection_unavailable", next_action=None, plan_id=None,
                requires_llm=False, requires_api_cost_ack=False,
                reads=["local recovery and lineage metadata", "existing learning previews"],
                writes=[], reuses=[], metadata_writes=[], report_writes=[], executed_action=None,
                output_paths={}, report_paths=[], follow_up="manual_review", diagnostic_reasons=[],
                scope="learning_workflow_step", dry_run=not confirm, network_read=False, warnings=list(WARNINGS))


def _observation(value: Any, podcast_id: str, episode_ref: str) -> tuple[str | None, list[str]]:
    if (type(value) is not dict or any(type(value.get(k)) is not str for k in ("podcast_id", "episode_ref", "scope", "status"))
            or value["podcast_id"] != podcast_id or value["episode_ref"] != episode_ref
            or value["scope"] != "learning_workflow_status" or value.get("read_only") is not True
            or value.get("network_access") is not False):
        raise ValueError("invalid observation")
    reasons = value.get("attention_reasons")
    if (type(reasons) is not list or any(type(r) is not str or r not in ATTENTION for r in reasons)
            or len(set(reasons)) != len(reasons) or type(value.get("attention_required")) is not bool):
        raise ValueError("invalid observation")
    if value["status"] in {"blocked", "attention_required"} and value["attention_required"] and reasons:
        return None, list(reasons)
    if value["status"] != "observed" or value["attention_required"] or reasons:
        raise ValueError("invalid observation")
    recovery = value.get("recovery")
    if (type(recovery) is not dict or any(type(recovery.get(k)) is not str for k in ("status", "reason"))
            or recovery.get("manual_review_required") is not False
            or recovery != {"status":"clear", "reason":"no_recovery_entries", "manual_review_required":False}):
        raise ValueError("invalid observation")
    states = {}
    for family, absent in (("study_guide", "no_study_guide"), ("workflow_derivation", "no_derivation")):
        item = value.get(family + "_lineage")
        if (type(item) is not dict or type(item.get("status")) is not str or type(item.get("reason")) is not str
                or item.get("changed_roles") != [] or type(item.get("changed_roles")) is not list
                or (item["status"], item["reason"]) not in {("current", "matches_record"), ("not_generated", absent)}):
            raise ValueError("invalid observation")
        states[family] = item["status"]
    step = value.get("next_step")
    step_keys = {"status", "reason", "lecture_mode", "derivation_mode", "blocked_stage", "next_action", "requires_llm", "requires_api_cost_ack"}
    if (type(step) is not dict or not step_keys <= step.keys()
            or any(type(step.get(k)) is not str for k in ("status", "reason", "lecture_mode", "derivation_mode"))):
        raise ValueError("invalid observation")
    action = step.get("next_action")
    if action is None:
        if (step["status"] != "complete" or (step["lecture_mode"], step["derivation_mode"], step["reason"]) != ("reuse", "reuse", "previews_reusable")
                or any(step.get(k) is not None for k in ("blocked_stage", "requires_llm", "requires_api_cost_ack"))
                or any(state != "current" for state in states.values())):
            raise ValueError("invalid observation")
        return None, []
    if type(action) is not str or action not in ACTIONS:
        raise ValueError("invalid observation")
    llm = action != "complete_cover"
    if (step["status"] != "action_available" or step.get("blocked_stage") is not None
            or (step["lecture_mode"], step["derivation_mode"], step["reason"]) != ACTIONS[action]
            or step.get("requires_llm") is not llm or step.get("requires_api_cost_ack") is not llm
            or states["study_guide"] != ("not_generated" if action == "generate_lecture" else "current")
            or states["workflow_derivation"] != "not_generated"):
        raise ValueError("invalid observation")
    return action, []



def _query_base(value: Any, podcast_id: str, episode_ref: str, scope: str) -> bool:
    return (type(value) is dict and all(type(value.get(k)) is str for k in ("podcast_id", "episode_ref", "scope"))
            and value["podcast_id"] == podcast_id and value["episode_ref"] == episode_ref and value["scope"] == scope
            and value.get("read_only") is True and value.get("network_access") is False)


def _record_matches(record: Any, status: str, output: str) -> bool:
    return (type(record) is dict and type(record.get("status")) is str and type(record.get("output_status")) is str
            and record["status"] == status and record["output_status"] == output
            and type(record.get("changed_roles")) is list and record["changed_roles"] == [])


def _cover_action(podcast_id: str, episode_ref: str) -> bool:
    """Qualify missing00 only; do not reinterpret a recovery or unknown location as safe."""
    try:
        detail = learning_bundle_recovery.inspect_learning_bundle_recovery(podcast_id, episode_ref)
        if (not _query_base(detail, podcast_id, episode_ref, "learning_bundle_recovery")
                or type(detail.get("status")) is not str or detail["status"] != "blocked"
                or type(detail.get("reason")) is not str or detail["reason"] != "manual_review_required"
                or detail.get("manual_review_required") is not True):
            return False
        rows = detail.get("locations")
        tags = [tag for tag, _ in learning_bundle_recovery.LOCATIONS]
        if type(rows) is not list or len(rows) != len(tags):
            return False
        for row, tag in zip(rows, tags):
            public = tag == "public"
            if (type(row) is not dict or any(type(row.get(k)) is not str for k in ("location", "status", "reason", "lecture_state", "derivation_state"))
                    or row["location"] != tag or row["status"] != ("observed" if public else "absent")
                    or row["reason"] != ("observed" if public else "missing")
                    or type(row.get("extra_files")) is not int or not 0 <= row["extra_files"] <= learning_bundle_recovery.MAX_DIRECTORY_ENTRIES):
                return False
            roles, records = row.get("roles"), row.get("records")
            if (type(roles) is not dict or set(roles) != set(learning_bundle_recovery.ROLE_FILES)
                    or any(type(value) is not bool for value in roles.values()) or type(records) is not dict
                    or set(records) != {"study_guide", "workflow_derivation"}):
                return False
            if not public:
                if (any(roles.values()) or row["lecture_state"] != "absent" or row["derivation_state"] != "absent"
                        or row["extra_files"] != 0 or any(not _record_matches(r, "absent", "not_evaluated") for r in records.values())):
                    return False
            else:
                if (roles["00"] or not all(roles[k] for k in ("03", "04", "07")) or roles["05"] is not roles["06"]
                        or row["lecture_state"] != "partial" or row["derivation_state"] != ("complete" if roles["05"] else "absent")
                        or not _record_matches(records["study_guide"], "valid", "match")
                        or not _record_matches(records["workflow_derivation"], "valid" if roles["05"] else "absent",
                                               "match" if roles["05"] else "not_evaluated")):
                    return False
        pair_present = rows[0]["roles"]["05"]
        step = learning_workflow_next_step.suggest_learning_workflow_next_step(podcast_id, episode_ref)
        if (type(step) is not learning_workflow_next_step.LearningWorkflowNextStep
                or any(type(getattr(step, k)) is not str for k in ("podcast_id", "episode_ref", "status", "lecture_mode", "derivation_mode", "reason_code", "next_action", "source_currentness", "completion_basis"))
                or step.podcast_id != podcast_id or step.episode_ref != episode_ref or step.status != "action_available"
                or step.next_action != "complete_cover" or step.blocked_stage is not None
                or (step.lecture_mode, step.derivation_mode, step.reason_code) != ACTIONS["complete_cover"]
                or step.requires_llm is not False or step.requires_api_cost_ack is not False
                or step.read_only is not True or step.network_read is not False
                or step.source_currentness != "not_evaluated" or step.completion_basis != "existing_preview_contracts"):
            return False
        for family, call, expected in (
            ("study_guide", study_guide_bundle.inspect_study_guide_lineage, ("current", "matches_record")),
            ("workflow_derivation", workflow_derivation.inspect_workflow_derivation_lineage,
             ("current", "matches_record") if pair_present else ("not_generated", "no_derivation")),
        ):
            value = call(podcast_id, episode_ref)
            if (not _query_base(value, podcast_id, episode_ref, family + "_inputs_outputs")
                    or type(value.get("status")) is not str or type(value.get("reason")) is not str
                    or (value["status"], value["reason"]) != expected
                    or type(value.get("changed_roles")) is not list or value["changed_roles"] != []):
                return False
        return True
    except Exception:
        return False


def _selected_plan(value: Any, podcast_id: str, episode_ref: str, action: str,
                   confirmed: bool = False) -> tuple[dict[str, Any], dict[str, str]]:
    derivation = action == "generate_derivation"
    model = WorkflowDerivationResult if derivation else StudyGuideBundleResult
    if (type(value) is not model or type(value.podcast_id) is not str or type(value.episode_ref) is not str
            or value.podcast_id != podcast_id or value.episode_ref != episode_ref or value.confirm is not confirmed
            or type(value.run_mode) is not str or value.run_mode != ("confirmed" if confirmed else "preview" if derivation else "dry-run")
            or value.reused is not False or value.not_investment_advice is not True):
        raise ValueError("invalid plan")
    directory = value.lecture_dir if derivation else value.bundle_dir
    if type(directory) is not str:
        raise ValueError("invalid plan")
    stem = Path(directory).name
    if stem != episode_ref and not stem.startswith(episode_ref + "__"):
        raise ValueError("invalid plan")
    lecture = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    if directory != str(lecture.bundle_dir):
        raise ValueError("invalid plan")
    outputs = {"00":str(lecture.cover_path), "03":str(lecture.summary_path), "04":str(lecture.notes_path), "07":str(lecture.guide_path)}
    if derivation:
        pair = storage.workflow_derivation_paths_from_stem(podcast_id, stem)
        outputs = {"05":str(pair.prompt_examples_path), "06":str(pair.apply_path)}
        receipt = workflow_derivation_lineage.RECEIPT_FILENAME
        reports = storage.workflow_derivation_run_asset_paths(podcast_id, episode_ref)
    else:
        receipt = study_guide_lineage.RECEIPT_FILENAME
        reports = storage.study_guide_run_asset_paths(podcast_id, episode_ref)
    writes = [outputs["00"]] if action == "complete_cover" else list(outputs.values())
    reuses = [outputs[k] for k in ("03", "04", "07")] if action == "complete_cover" else []
    metadata = [] if action == "complete_cover" else [str(lecture.bundle_dir / receipt)]
    for name, expected in (("planned_writes", writes), ("planned_reuses", reuses), ("metadata_writes", metadata)):
        paths = getattr(value, name)
        if type(paths) is not list or any(type(p) is not str for p in paths) or paths != expected:
            raise ValueError("invalid plan")
    if not confirmed:
        if (value.report_json_path is not None or value.report_markdown_path is not None
                or (derivation and (value.prompt_examples_path is not None or value.apply_path is not None))
                or (not derivation and (type(value.output_paths) is not dict or value.output_paths))):
            raise ValueError("invalid plan")
    info = dict(writes=writes, reuses=reuses, metadata_writes=metadata,
                report_writes=[str(reports.json_path), str(reports.markdown_path)])
    return info, outputs


def _plan_id(result: dict[str, Any]) -> str:
    fields = ("podcast_id", "episode_ref", "next_action", "requires_llm", "requires_api_cost_ack",
              "writes", "reuses", "metadata_writes", "report_writes")
    payload = {key:result[key] for key in fields}
    raw = "learning-step-plan-v1:" + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def advance_learning_workflow(podcast_id: str, episode_ref: str, *, confirm: bool = False,
                              expected_action: str = "", expected_plan_id: str = "", api_cost_ack: str = "") -> dict[str, Any]:
    """Preview a metadata-bound plan or execute exactly one explicitly approved action."""
    _validate(podcast_id, episode_ref, confirm, expected_action, expected_plan_id, api_cost_ack)
    if confirm and expected_action != "complete_cover":
        llm_provider.require_exact_api_cost_ack(api_cost_ack)
    result = _base(podcast_id, episode_ref, confirm)
    try:
        observation = learning_workflow_status.inspect_learning_workflow_status(podcast_id, episode_ref)
        action, reasons = _observation(observation, podcast_id, episode_ref)
    except Exception:
        return result
    if (reasons == ["recovery_blocked"] and observation.get("recovery") ==
            {"status":"blocked", "reason":"manual_review_required", "manual_review_required":True}
            and _cover_action(podcast_id, episode_ref)):
        action, reasons = "complete_cover", []
        result["warnings"].append("cover_absence_checked_separately")
    if reasons:
        result.update(reason="workflow_requires_attention", diagnostic_reasons=reasons)
        return result
    if action is None:
        if confirm:
            raise LearningWorkflowPlanChangedError(PLAN_CHANGED_MESSAGE)
        result.update(status="complete", reason="previews_reusable", follow_up="none")
        return result
    runner = workflow_derivation.run_workflow_derivation if action == "generate_derivation" else study_guide_bundle.run_study_guide_bundle
    try:
        info, _ = _selected_plan(runner(podcast_id, episode_ref, confirm=False, force=False), podcast_id, episode_ref, action)
    except Exception:
        return result
    llm = action != "complete_cover"
    reads = ["existing lecture03/04/07", "configured default operator workflow context"] if action == "generate_derivation" else ["canonical learning-notes semantic summary", "canonical identity metadata", "optional episode seed and audio metadata"]
    result.update(info)
    result.update(status="action_available", reason="next_action_available", next_action=action,
                  requires_llm=llm, requires_api_cost_ack=llm, follow_up="confirm_selected_action")
    result["reads"].extend(reads)
    result["plan_id"] = _plan_id(result)
    if not confirm:
        return result
    if action != expected_action or result["plan_id"] != expected_plan_id:
        raise LearningWorkflowPlanChangedError(PLAN_CHANGED_MESSAGE)
    # Existing runner owns all publication/recovery/report phases; never retry it.
    try:
        actual = runner(podcast_id, episode_ref, confirm=True, force=False,
                        api_cost_ack=api_cost_ack if llm else "")
    except PodcastIngestCoreError:
        raise
    except Exception:
        raise LearningWorkflowAdvanceError(UNCERTAIN_MESSAGE) from None
    try:
        actual_info, outputs = _selected_plan(actual, podcast_id, episode_ref, action, confirmed=True)
        if actual_info != info:
            raise ValueError("changed result plan")
        if action == "generate_derivation":
            if (type(actual.prompt_examples_path) is not str or type(actual.apply_path) is not str
                    or actual.prompt_examples_path != outputs["05"] or actual.apply_path != outputs["06"]):
                raise ValueError("invalid outputs")
        elif (type(actual.output_paths) is not dict or any(type(k) is not str or type(v) is not str for k,v in actual.output_paths.items())
              or actual.output_paths != outputs):
            raise ValueError("invalid outputs")
        reports = (actual.report_json_path, actual.report_markdown_path)
        if any(type(p) is not type(Path()) for p in reports) or [str(p) for p in reports] != info["report_writes"]:
            raise ValueError("invalid reports")
    except Exception:
        raise LearningWorkflowAdvanceError(UNCERTAIN_MESSAGE) from None
    result.update(status="executed", reason="step_executed", executed_action=action,
                  output_paths=outputs, report_paths=list(info["report_writes"]), follow_up="preview_again", network_read=llm)
    return result
