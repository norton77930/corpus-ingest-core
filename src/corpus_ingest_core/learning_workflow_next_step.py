"""Read-only next-step decisions over the existing learning previews."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import storage, study_guide_bundle, workflow_derivation
from .errors import (
    PodcastIngestCoreError, StudyGuideBundleStateError, WorkflowDerivationStateError,
)

INVALID_IDENTITY_MESSAGE = "Invalid explicit episode identity."
QUERY_ERROR_MESSAGE = "Learning workflow query could not be evaluated safely."
WARNINGS = (
    "Completion reflects existing preview reuse only; content quality and source freshness are not verified.",
    "This query authorizes no execution; preview and approve the selected operation separately.",
)


class LearningWorkflowQueryError(PodcastIngestCoreError):
    """The query could not safely obtain a preview decision."""


@dataclass(frozen=True)
class LearningWorkflowNextStep:
    podcast_id: str
    episode_ref: str
    status: str
    lecture_mode: str
    derivation_mode: str
    blocked_stage: str | None
    reason_code: str
    next_action: str | None
    suggested_call: dict[str, Any] | None
    requires_llm: bool | None
    requires_api_cost_ack: bool | None
    read_only: bool
    network_read: bool
    source_currentness: str
    completion_basis: str
    warnings: list[str]


def _validate_identity(podcast_id: object, episode_ref: object) -> None:
    if (
        not isinstance(podcast_id, str)
        or not storage.is_safe_episode_ref(episode_ref)
        or episode_ref.casefold() in {"latest", "next"}
    ):
        raise ValueError(INVALID_IDENTITY_MESSAGE)
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "title")
    except (TypeError, ValueError):
        raise ValueError(INVALID_IDENTITY_MESSAGE) from None


def _decision(
    podcast_id: str, episode_ref: str, *, lecture_mode: str,
    derivation_mode: str = "not_evaluated", reason: str,
    action: str | None = None, blocked_stage: str | None = None,
) -> LearningWorkflowNextStep:
    call = None
    llm = None
    if action is not None:
        tool = "derive_workflow_bundle" if action == "generate_derivation" else "generate_study_guide_bundle"
        call = {"tool": tool, "arguments": {
            "podcast_id": podcast_id, "episode_ref": episode_ref, "confirm": False, "force": False,
        }}
        llm = action != "complete_cover"
    return LearningWorkflowNextStep(
        podcast_id=podcast_id, episode_ref=episode_ref,
        status="blocked" if blocked_stage else "action_available" if action else "complete",
        lecture_mode=lecture_mode, derivation_mode=derivation_mode,
        blocked_stage=blocked_stage, reason_code=reason, next_action=action,
        suggested_call=call, requires_llm=llm, requires_api_cost_ack=llm,
        read_only=True, network_read=False, source_currentness="not_evaluated",
        completion_basis="existing_preview_contracts", warnings=list(WARNINGS),
    )


def _blocked(podcast_id: str, episode_ref: str, stage: str, reason: str) -> LearningWorkflowNextStep:
    return _decision(
        podcast_id, episode_ref, lecture_mode="blocked" if stage == "lecture" else "reuse",
        derivation_mode="not_evaluated" if stage == "lecture" else "blocked",
        blocked_stage=stage, reason=reason,
    )


def _preview(
    podcast_id: str, episode_ref: str, stage: str,
) -> tuple[Any, LearningWorkflowNextStep | None]:
    runner = (study_guide_bundle.run_study_guide_bundle if stage == "lecture"
              else workflow_derivation.run_workflow_derivation)
    try:
        return runner(podcast_id, episode_ref, confirm=False, force=False), None
    except (StudyGuideBundleStateError, WorkflowDerivationStateError) as exc:
        if exc.reason_code == "invalid_identity":
            raise ValueError(INVALID_IDENTITY_MESSAGE) from None
        allowed = {"unsafe_path", "recovery_required"}
        if stage == "lecture":
            allowed.add("derivation_conflict")
        reason = exc.reason_code if type(exc.reason_code) is str and exc.reason_code in allowed else "unexpected_preview"
        return None, _blocked(podcast_id, episode_ref, stage, reason)
    except (PodcastIngestCoreError, ValueError):
        return None, _blocked(podcast_id, episode_ref, stage, f"{stage}_prerequisite_failed")
    except Exception:
        raise LearningWorkflowQueryError(QUERY_ERROR_MESSAGE) from None


def _mode(result: Any, podcast_id: str, episode_ref: str, stage: str) -> str | None:
    """Validate known preview shapes; never dereference child-returned paths."""
    try:
        if (result.podcast_id != podcast_id or result.episode_ref != episode_ref
                or result.confirm is not False
                or result.run_mode != ("dry-run" if stage == "lecture" else "preview")
                or type(result.reused) is not bool):
            return None
        directory = result.bundle_dir if stage == "lecture" else result.lecture_dir
        if type(directory) is not str or not directory:
            return None
        writes, reuses = result.planned_writes, result.planned_reuses
        for paths in (writes, reuses):
            if (type(paths) is not list or any(type(path) is not str or not path for path in paths)
                    or len(set(paths)) != len(paths)):
                return None
        if set(writes).intersection(reuses):
            return None
        if result.reused:
            return "reuse" if not writes and len(reuses) == (4 if stage == "lecture" else 2) else None
        if stage == "derivation":
            return "generation" if len(writes) == 2 and not reuses else None
        requires_llm = study_guide_bundle.describe_study_guide_plan(result)["requires_llm"]
        if len(writes) == 4 and not reuses and requires_llm is True:
            return "generation"
        if len(writes) == 1 and len(reuses) == 3 and requires_llm is False:
            return "cover_only"
    except Exception:
        # A malformed result/projection is a blocked observation, not safe readiness.
        return None
    return None


def suggest_learning_workflow_next_step(
    podcast_id: str, episode_ref: str,
) -> LearningWorkflowNextStep:
    """Evaluate at most one lecture and one derivation preview, without execution."""
    _validate_identity(podcast_id, episode_ref)
    lecture, failure = _preview(podcast_id, episode_ref, "lecture")
    if failure is not None:
        return failure
    mode = _mode(lecture, podcast_id, episode_ref, "lecture")
    if mode is None:
        return _blocked(podcast_id, episode_ref, "lecture", "unexpected_preview")
    if mode != "reuse":
        return _decision(
            podcast_id, episode_ref, lecture_mode=mode,
            reason="lecture_generation_needed" if mode == "generation" else "cover_completion_needed",
            action="generate_lecture" if mode == "generation" else "complete_cover",
        )
    derivation, failure = _preview(podcast_id, episode_ref, "derivation")
    if failure is not None:
        return failure
    derivation_mode = _mode(derivation, podcast_id, episode_ref, "derivation")
    if derivation_mode is None or derivation.lecture_dir != lecture.bundle_dir:
        return _blocked(podcast_id, episode_ref, "derivation", "unexpected_preview")
    return _decision(
        podcast_id, episode_ref, lecture_mode="reuse", derivation_mode=derivation_mode,
        reason="previews_reusable" if derivation_mode == "reuse" else "derivation_generation_needed",
        action=None if derivation_mode == "reuse" else "generate_derivation",
    )
