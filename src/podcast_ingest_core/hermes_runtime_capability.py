"""Offline, fail-closed capability gate for Hermes runtime observation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Final


class CapabilityRequirement(str, Enum):
    CANONICAL_SKILL_IDENTITY = "canonical_skill_identity"
    SKILL_TO_TOOL_LINKAGE = "skill_to_tool_linkage"
    FALLBACK_USED = "fallback_used"
    FALLBACK_NOT_USED = "fallback_not_used"
    GUARANTEED_SKILL_TOOL_CORRELATION = "guaranteed_skill_tool_correlation"
    OFFICIAL_NO_SIDE_EFFECT_POSITIVE_CONTROL = "official_no_side_effect_positive_control"


class ObservationState(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


class CapabilityVerdict(str, Enum):
    PASS_CANONICAL_COVERAGE = "PASS_CANONICAL_COVERAGE"
    BLOCKED_CAPABILITY = "BLOCKED_CAPABILITY"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


class FailureCode(str, Enum):
    NONE = "none"
    BLOCKED_CAPABILITY = "blocked_capability"
    INVALID_EVIDENCE = "invalid_evidence"
    INVALID_SOURCE_IDENTITY = "invalid_source_identity"
    INVALID_MODE = "invalid_mode"
    INTERNAL_FAILURE = "internal_failure"


class CapabilityMode(str, Enum):
    CAPABILITY = "capability"
    SYNTHETIC = "synthetic"
    REJECTED = "rejected"


@dataclass(frozen=True)
class SourceIdentity:
    repository: str
    release: str
    annotated_tag: str
    annotated_tag_object_sha: str
    tag_target_commit_sha: str
    hooks_path: str
    hooks_blob_sha: str


@dataclass(frozen=True)
class RequirementObservation:
    requirement: CapabilityRequirement
    state: ObservationState
    official_source: bool


@dataclass(frozen=True)
class SyntheticChecks:
    all_present_passes: bool = False
    missing_fail_closed: bool = False
    ambiguous_fail_closed: bool = False
    invalid_fail_closed: bool = False
    non_boolean_fail_closed: bool = False
    source_identity_malformed_fail_closed: bool = False


@dataclass(frozen=True)
class CapabilityEvaluation:
    mode: CapabilityMode
    verdict: CapabilityVerdict
    failure: FailureCode
    source_identity_verified: bool
    coverage_complete: bool
    states: tuple[ObservationState, ...]
    synthetic_checks: SyntheticChecks = SyntheticChecks()


@dataclass(frozen=True)
class PinnedSourceManifest:
    source_identity: object
    observations: object
    terminal_verdict: object


_MANIFEST_PATH: Final = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "028-hermes-runtime-skill-routing-observation"
    / "contracts"
    / "hermes-v2026.8.3-source-manifest.json"
)
_CANONICAL_SOURCE_IDENTITY: Final = SourceIdentity(
    repository="NousResearch/hermes-agent",
    release="Hermes Agent v0.20.0",
    annotated_tag="v2026.8.3",
    annotated_tag_object_sha="7de39e700d2c329e15d32eb0b96e2f7cdd9fbdb2",
    tag_target_commit_sha="3c27eb6234bf91b8ceee9e9071591b31e9b148cb",
    hooks_path="website/docs/user-guide/features/hooks.md",
    hooks_blob_sha="be8b9c0caa2792a24bb34dba9400400acdf91eaa",
)
_REQUIREMENTS: Final = tuple(CapabilityRequirement)
_MANIFEST_SCHEMA_VERSION: Final = "hermes-v2026.8.3-source-manifest-v1"
_MANIFEST_KEYS: Final = frozenset(
    {
        "schema_version",
        "repository",
        "release",
        "annotated_tag",
        "annotated_tag_object_sha",
        "tag_target_commit_sha",
        "hooks_path",
        "hooks_blob_sha",
        "terminal_verdict",
        "requirements",
    }
)
_SPEC_ID: Final = "028-hermes-runtime-skill-routing-observation"
_RUNTIME_TARGET: Final = "hermes-agent"
_RELEASE_TAG: Final = "v2026.8.3"


def canonical_source_identity() -> SourceIdentity:
    """Return the fixed, reviewed source identity without accepting overrides."""

    return _CANONICAL_SOURCE_IDENTITY


def load_pinned_hermes_source_manifest() -> PinnedSourceManifest:
    """Load only the repository-pinned local manifest; paths and URLs are not inputs."""

    try:
        raw = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return PinnedSourceManifest(None, None, None)
    if (
        not isinstance(raw, dict)
        or set(raw) != _MANIFEST_KEYS
        or raw.get("schema_version") != _MANIFEST_SCHEMA_VERSION
        or raw.get("terminal_verdict") != FailureCode.BLOCKED_CAPABILITY.value
    ):
        return PinnedSourceManifest(None, None, None)
    statuses = raw["requirements"]
    if not isinstance(statuses, dict) or set(statuses) != {
        requirement.value for requirement in _REQUIREMENTS
    }:
        return PinnedSourceManifest(None, None, None)
    identity = SourceIdentity(
        raw["repository"],
        raw["release"],
        raw["annotated_tag"],
        raw["annotated_tag_object_sha"],
        raw["tag_target_commit_sha"],
        raw["hooks_path"],
        raw["hooks_blob_sha"],
    )
    observations: list[RequirementObservation] = []
    try:
        for requirement in _REQUIREMENTS:
            observations.append(
                RequirementObservation(
                    requirement,
                    ObservationState(statuses[requirement.value]),
                    True,
                )
            )
    except (KeyError, TypeError, ValueError):
        return PinnedSourceManifest(identity, None, raw.get("terminal_verdict"))
    return PinnedSourceManifest(
        identity,
        tuple(observations),
        raw.get("terminal_verdict"),
    )


def _invalid_evaluation(
    failure: FailureCode = FailureCode.INVALID_EVIDENCE,
    *,
    mode: CapabilityMode = CapabilityMode.CAPABILITY,
) -> CapabilityEvaluation:
    return CapabilityEvaluation(
        mode,
        CapabilityVerdict.INVALID_EVIDENCE,
        failure,
        False,
        False,
        tuple(ObservationState.INVALID for _ in _REQUIREMENTS),
    )


def _source_identity_is_canonical(source_identity: object) -> bool:
    return isinstance(source_identity, SourceIdentity) and source_identity == _CANONICAL_SOURCE_IDENTITY


def _closed_observations(
    observations: object,
) -> tuple[RequirementObservation, ...] | None:
    if not isinstance(observations, tuple) or len(observations) > len(_REQUIREMENTS):
        return None
    if not all(isinstance(item, RequirementObservation) for item in observations):
        return None
    if any(
        not isinstance(item.requirement, CapabilityRequirement)
        or not isinstance(item.state, ObservationState)
        or type(item.official_source) is not bool
        for item in observations
    ):
        return None
    requirements = tuple(item.requirement for item in observations)
    if len(set(requirements)) != len(requirements):
        return None
    return observations


def evaluate_hermes_capability(
    observations: object,
    source_identity: object,
    *,
    mode: CapabilityMode = CapabilityMode.CAPABILITY,
) -> CapabilityEvaluation:
    """Evaluate only bounded source-derived observations and fail closed by default."""

    if not isinstance(mode, CapabilityMode):
        return _invalid_evaluation()
    if not _source_identity_is_canonical(source_identity):
        return _invalid_evaluation(FailureCode.INVALID_SOURCE_IDENTITY, mode=mode)
    closed = _closed_observations(observations)
    if closed is None:
        return _invalid_evaluation(mode=mode)
    states = tuple(
        next(
            (
                item.state
                for item in closed
                if item.requirement is requirement
            ),
            ObservationState.MISSING,
        )
        for requirement in _REQUIREMENTS
    )
    if any(item.state is ObservationState.INVALID or not item.official_source for item in closed):
        return _invalid_evaluation(mode=mode)
    complete = all(state is ObservationState.PRESENT for state in states)
    if complete:
        return CapabilityEvaluation(
            mode,
            CapabilityVerdict.PASS_CANONICAL_COVERAGE,
            FailureCode.NONE,
            True,
            True,
            states,
        )
    return CapabilityEvaluation(
        mode,
        CapabilityVerdict.BLOCKED_CAPABILITY,
        FailureCode.BLOCKED_CAPABILITY,
        True,
        False,
        states,
    )


def _synthetic_evaluation() -> CapabilityEvaluation:
    identity = canonical_source_identity()
    present = tuple(
        RequirementObservation(requirement, ObservationState.PRESENT, True)
        for requirement in _REQUIREMENTS
    )
    all_present = evaluate_hermes_capability(present, identity, mode=CapabilityMode.SYNTHETIC)
    missing = evaluate_hermes_capability(present[1:], identity, mode=CapabilityMode.SYNTHETIC)
    ambiguous = evaluate_hermes_capability(
        (RequirementObservation(_REQUIREMENTS[0], ObservationState.AMBIGUOUS, True),)
        + present[1:],
        identity,
        mode=CapabilityMode.SYNTHETIC,
    )
    invalid = evaluate_hermes_capability((object(),), identity, mode=CapabilityMode.SYNTHETIC)
    non_boolean = evaluate_hermes_capability(
        (RequirementObservation(_REQUIREMENTS[0], ObservationState.PRESENT, "true"),)
        + present[1:],
        identity,
        mode=CapabilityMode.SYNTHETIC,
    )
    malformed_identity = evaluate_hermes_capability(
        present,
        SourceIdentity("invalid", "", "", "", "", "", ""),
        mode=CapabilityMode.SYNTHETIC,
    )
    checks = SyntheticChecks(
        all_present_passes=all_present.verdict is CapabilityVerdict.PASS_CANONICAL_COVERAGE,
        missing_fail_closed=missing.verdict is CapabilityVerdict.BLOCKED_CAPABILITY,
        ambiguous_fail_closed=ambiguous.verdict is CapabilityVerdict.BLOCKED_CAPABILITY,
        invalid_fail_closed=invalid.verdict is CapabilityVerdict.INVALID_EVIDENCE,
        non_boolean_fail_closed=non_boolean.verdict is CapabilityVerdict.INVALID_EVIDENCE,
        source_identity_malformed_fail_closed=(
            malformed_identity.failure is FailureCode.INVALID_SOURCE_IDENTITY
        ),
    )
    return CapabilityEvaluation(
        CapabilityMode.SYNTHETIC,
        all_present.verdict if all(checks.__dict__.values()) else CapabilityVerdict.INVALID_EVIDENCE,
        FailureCode.NONE if all(checks.__dict__.values()) else FailureCode.INVALID_EVIDENCE,
        all_present.source_identity_verified,
        all_present.coverage_complete,
        all_present.states,
        checks,
    )


def evaluate_pinned_hermes_capability() -> CapabilityEvaluation:
    """Evaluate the only local source manifest and preserve its blocked terminal state."""

    manifest = load_pinned_hermes_source_manifest()
    result = evaluate_hermes_capability(manifest.observations, manifest.source_identity)
    if (
        manifest.terminal_verdict != FailureCode.BLOCKED_CAPABILITY.value
        or result.verdict is not CapabilityVerdict.BLOCKED_CAPABILITY
    ):
        return _invalid_evaluation()
    return result


def evaluate_synthetic_hermes_capability() -> CapabilityEvaluation:
    """Exercise all bounded pass and fail-closed projections without runtime access."""

    return _synthetic_evaluation()


def _evaluation_has_consistent_cross_fields(evaluation: object) -> bool:
    if not isinstance(evaluation, CapabilityEvaluation):
        return False
    if not (
        isinstance(evaluation.mode, CapabilityMode)
        and isinstance(evaluation.verdict, CapabilityVerdict)
        and isinstance(evaluation.failure, FailureCode)
        and type(evaluation.source_identity_verified) is bool
        and type(evaluation.coverage_complete) is bool
        and isinstance(evaluation.states, tuple)
        and len(evaluation.states) == len(_REQUIREMENTS)
        and all(isinstance(state, ObservationState) for state in evaluation.states)
        and isinstance(evaluation.synthetic_checks, SyntheticChecks)
        and all(
            type(value) is bool
            for value in evaluation.synthetic_checks.__dict__.values()
        )
    ):
        return False
    all_present = all(state is ObservationState.PRESENT for state in evaluation.states)
    has_gap = any(
        state in {ObservationState.MISSING, ObservationState.AMBIGUOUS}
        for state in evaluation.states
    )
    synthetic_checks_pass = all(evaluation.synthetic_checks.__dict__.values())
    if evaluation.verdict is CapabilityVerdict.PASS_CANONICAL_COVERAGE:
        return (
            evaluation.mode is not CapabilityMode.REJECTED
            and evaluation.failure is FailureCode.NONE
            and evaluation.source_identity_verified
            and evaluation.coverage_complete
            and all_present
            and (
                evaluation.mode is not CapabilityMode.SYNTHETIC
                or synthetic_checks_pass
            )
        )
    if evaluation.verdict is CapabilityVerdict.BLOCKED_CAPABILITY:
        return (
            evaluation.mode is not CapabilityMode.REJECTED
            and evaluation.failure is FailureCode.BLOCKED_CAPABILITY
            and evaluation.source_identity_verified
            and not evaluation.coverage_complete
            and has_gap
            and all(
                state is not ObservationState.INVALID
                for state in evaluation.states
            )
        )
    return (
        evaluation.failure
        in {
            FailureCode.INVALID_EVIDENCE,
            FailureCode.INVALID_SOURCE_IDENTITY,
            FailureCode.INVALID_MODE,
            FailureCode.INTERNAL_FAILURE,
        }
        and not evaluation.source_identity_verified
        and not evaluation.coverage_complete
        and all(state is ObservationState.INVALID for state in evaluation.states)
        and (
            evaluation.mode is not CapabilityMode.REJECTED
            or evaluation.failure
            in {FailureCode.INVALID_MODE, FailureCode.INTERNAL_FAILURE}
        )
    )


def _terminal_status_for(verdict: CapabilityVerdict) -> str:
    return {
        CapabilityVerdict.PASS_CANONICAL_COVERAGE: "pass_canonical_coverage",
        CapabilityVerdict.BLOCKED_CAPABILITY: "blocked_capability",
        CapabilityVerdict.INVALID_EVIDENCE: "invalid_evidence",
    }[verdict]


def build_capability_evidence(evaluation: object) -> dict[str, str | bool | int]:
    """Project a fixed, bounded schema that never returns manifest or input content."""

    mode = evaluation.mode if isinstance(evaluation, CapabilityEvaluation) and isinstance(
        evaluation.mode, CapabilityMode
    ) else CapabilityMode.CAPABILITY
    if not _evaluation_has_consistent_cross_fields(evaluation):
        evaluation = _invalid_evaluation(mode=mode)
    states = evaluation.states
    checks = evaluation.synthetic_checks
    return {
        "schema_version": "hermes-runtime-capability-evidence-v1",
        "spec_id": _SPEC_ID,
        "terminal_status": _terminal_status_for(evaluation.verdict),
        "runtime_target": _RUNTIME_TARGET,
        "release_tag": _RELEASE_TAG,
        "missing_requirement_count": sum(
            state is ObservationState.MISSING for state in states
        ),
        "ok": evaluation.verdict is not CapabilityVerdict.INVALID_EVIDENCE,
        "mode": evaluation.mode.value,
        "verdict": evaluation.verdict.value,
        "failure_code": evaluation.failure.value,
        "source_identity_verified": evaluation.source_identity_verified,
        "coverage_complete": evaluation.coverage_complete,
        **{
            requirement.value: state.value
            for requirement, state in zip(_REQUIREMENTS, states, strict=True)
        },
        "live_actions_authorized": False,
        "hermes_runtime_observation": "not_run",
        "c6_status": "pass_current_not_rerun",
        "synthetic_all_present_passes": checks.all_present_passes,
        "synthetic_missing_fail_closed": checks.missing_fail_closed,
        "synthetic_ambiguous_fail_closed": checks.ambiguous_fail_closed,
        "synthetic_invalid_fail_closed": checks.invalid_fail_closed,
        "synthetic_non_boolean_fail_closed": checks.non_boolean_fail_closed,
        "synthetic_source_identity_malformed_fail_closed": checks.source_identity_malformed_fail_closed,
    }


def rejected_capability_evidence(failure: FailureCode) -> dict[str, str | bool | int]:
    """Return the same fixed schema for a locally rejected CLI invocation."""

    code = failure if isinstance(failure, FailureCode) else FailureCode.INVALID_EVIDENCE
    return build_capability_evidence(
        _invalid_evaluation(code, mode=CapabilityMode.REJECTED)
    )
