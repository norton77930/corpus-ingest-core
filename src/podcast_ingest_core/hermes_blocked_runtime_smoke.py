"""Closed, offline scenario projector/reducer for Spec 029."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final
import weakref

from podcast_ingest_core.hermes_mcp_deny_interposer import (
    verified_tripwire_count,
)
from podcast_ingest_core.hermes_skill_protocol import (
    Skill,
    Tool,
    canonical_skill_bindings,
)


class ScenarioId(str, Enum):
    READ_ONLY_NO_SKILL = "READ_ONLY_NO_SKILL"
    UNKNOWN_OR_CONFLICTING = "UNKNOWN_OR_CONFLICTING"
    S016_PREVIEW_BLOCKED = "S016_PREVIEW_BLOCKED"
    S017_CONFIRMED_BLOCKED = "S017_CONFIRMED_BLOCKED"
    S018_PREVIEW_BLOCKED = "S018_PREVIEW_BLOCKED"
    S019_PREVIEW_BLOCKED = "S019_PREVIEW_BLOCKED"


class ProjectionStatus(str, Enum):
    ACCEPTED = "accepted"
    ABORTED = "aborted"


class ScenarioStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ABORTED = "aborted"


class SurfaceStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class ResponseDisposition(str, Enum):
    """Closed synthetic response classification; raw response text is not accepted."""

    CLARIFICATION_ONLY = "clarification_only"
    UNCLASSIFIED = "unclassified"


_POLICY_TOKEN: Final = object()
_EVALUATION_TOKEN: Final = object()
_SURFACE_TOKEN: Final = object()
_SCENARIO_EVIDENCE: dict[int, tuple[weakref.ReferenceType, dict[str, object]]] = {}
_SURFACE_EVIDENCE: dict[int, tuple[weakref.ReferenceType, dict[str, object]]] = {}


def _register_evidence(
    registry: dict[int, tuple[weakref.ReferenceType, dict[str, object]]],
    evaluation: object,
    payload: dict[str, object],
) -> None:
    key = id(evaluation)

    def discard(reference, *, evidence_key=key) -> None:
        current = registry.get(evidence_key)
        if current is not None and current[0] is reference:
            registry.pop(evidence_key, None)

    registry[key] = (weakref.ref(evaluation, discard), dict(payload))


def _issued_evidence(
    registry: dict[int, tuple[weakref.ReferenceType, dict[str, object]]],
    evaluation: object,
) -> dict[str, object] | None:
    current = registry.get(id(evaluation))
    if current is None or current[0]() is not evaluation:
        return None
    return dict(current[1])


@dataclass(frozen=True, init=False)
class ScenarioPolicy:
    scenario: ScenarioId
    expected_tool: Tool | None
    expected_confirm: bool | None
    requires_next_action: bool
    ephemeral_episode_ref: str | None
    attempt_budget: int
    turn_budget: int
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use scenario_policy()")


@dataclass(frozen=True)
class AttemptProjection:
    status: ProjectionStatus
    attempted_tool: Tool | None
    confirm: bool | None
    policy_blocked: bool
    raw_persisted: bool = False

    def to_evidence(self) -> dict[str, str | bool | None]:
        return {
            "projection_status": self.status.value,
            "attempted_tool": (
                self.attempted_tool.value if self.attempted_tool else None
            ),
            "confirm": self.confirm,
            "policy_blocked": self.policy_blocked,
            "raw_persisted": False,
        }


@dataclass(frozen=True, init=False)
class ScenarioEvaluation:
    status: ScenarioStatus
    scenario: ScenarioId
    attempt_count: int
    mcp_tripwire_call_count: int | None
    projection: AttemptProjection | None
    expected_tool: Tool | None
    expected_confirm: bool | None
    attempt_budget: int
    turn_budget: int
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_scenario()")


@dataclass(frozen=True, init=False)
class SurfaceEvaluation:
    status: SurfaceStatus
    toolset_exact: bool
    terminal_shell_exposed: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_tool_surface()")


_SKILLS: Final = {
    ScenarioId.S016_PREVIEW_BLOCKED: Skill.COMPLETION,
    ScenarioId.S017_CONFIRMED_BLOCKED: Skill.LATEST_DETERMINISTIC,
    ScenarioId.S018_PREVIEW_BLOCKED: Skill.LATEST_VERIFIED_REPORT,
    ScenarioId.S019_PREVIEW_BLOCKED: Skill.NAMED_VERIFIED_REPORT,
}
_FORBIDDEN_SURFACE_NAMES: Final = frozenset(
    {
        "terminal",
        "shell",
        "execute_code",
        "file_write",
        "browser",
        "web",
    }
)


def _create_policy(
    scenario: ScenarioId,
    expected_tool: Tool | None,
    expected_confirm: bool | None,
    *,
    requires_next_action: bool,
    ephemeral_episode_ref: str | None,
    attempt_budget: int,
    turn_budget: int,
) -> ScenarioPolicy:
    policy = object.__new__(ScenarioPolicy)
    object.__setattr__(policy, "scenario", scenario)
    object.__setattr__(policy, "expected_tool", expected_tool)
    object.__setattr__(policy, "expected_confirm", expected_confirm)
    object.__setattr__(policy, "requires_next_action", requires_next_action)
    object.__setattr__(policy, "ephemeral_episode_ref", ephemeral_episode_ref)
    object.__setattr__(policy, "attempt_budget", attempt_budget)
    object.__setattr__(policy, "turn_budget", turn_budget)
    object.__setattr__(policy, "_factory_token", _POLICY_TOKEN)
    return policy


def scenario_policy(
    scenario: object,
    *,
    ephemeral_episode_ref: object = None,
) -> ScenarioPolicy:
    if not isinstance(scenario, ScenarioId):
        raise ValueError("closed scenario required")
    skill = _SKILLS.get(scenario)
    if skill is None:
        return _create_policy(
            scenario,
            None,
            None,
            requires_next_action=False,
            ephemeral_episode_ref=None,
            attempt_budget=0,
            turn_budget=1,
        )
    tool = next(
        binding.tool
        for binding in canonical_skill_bindings()
        if binding.skill is skill
    )
    if scenario is ScenarioId.S019_PREVIEW_BLOCKED and (
        type(ephemeral_episode_ref) is not str or not ephemeral_episode_ref
    ):
        raise ValueError("ephemeral reference required")
    return _create_policy(
        scenario,
        tool,
        scenario is ScenarioId.S017_CONFIRMED_BLOCKED,
        requires_next_action=scenario is ScenarioId.S016_PREVIEW_BLOCKED,
        ephemeral_episode_ref=(
            ephemeral_episode_ref
            if scenario is ScenarioId.S019_PREVIEW_BLOCKED
            else None
        ),
        attempt_budget=1,
        turn_budget=1,
    )


def _policy_is_canonical(policy: object) -> bool:
    if (
        not isinstance(policy, ScenarioPolicy)
        or getattr(policy, "_factory_token", None) is not _POLICY_TOKEN
    ):
        return False
    try:
        expected = scenario_policy(
            policy.scenario,
            ephemeral_episode_ref=policy.ephemeral_episode_ref,
        )
    except (TypeError, ValueError):
        return False
    return policy == expected


def project_pre_tool_attempt(
    policy: object,
    raw: object,
) -> AttemptProjection:
    aborted = AttemptProjection(ProjectionStatus.ABORTED, None, None, True)
    if (
        not _policy_is_canonical(policy)
        or policy.expected_tool is None
        or not isinstance(raw, dict)
    ):
        return aborted
    if (
        set(raw) != {"name", "arguments"}
        or raw.get("name") != policy.expected_tool.value
        or not isinstance(raw.get("arguments"), dict)
    ):
        return aborted
    args = raw["arguments"]
    confirm = args.get("confirm")
    if type(confirm) is not bool or confirm is not policy.expected_confirm:
        return aborted
    if policy.requires_next_action and args.get("action") != "next":
        return aborted
    if (
        policy.ephemeral_episode_ref is not None
        and args.get("episode_ref") != policy.ephemeral_episode_ref
    ):
        return aborted
    return AttemptProjection(
        ProjectionStatus.ACCEPTED,
        policy.expected_tool,
        confirm,
        True,
    )


def _cap_nonnegative_count(value: int) -> int:
    return min(value, 2)


def _create_evaluation(
    status: ScenarioStatus,
    scenario: ScenarioId,
    attempt_count: int,
    tripwire_count: int | None,
    projection: AttemptProjection | None,
    expected_tool: Tool | None,
    expected_confirm: bool | None,
    attempt_budget: int,
    turn_budget: int,
) -> ScenarioEvaluation:
    evaluation = object.__new__(ScenarioEvaluation)
    object.__setattr__(evaluation, "status", status)
    object.__setattr__(evaluation, "scenario", scenario)
    object.__setattr__(evaluation, "attempt_count", attempt_count)
    object.__setattr__(evaluation, "mcp_tripwire_call_count", tripwire_count)
    object.__setattr__(evaluation, "projection", projection)
    object.__setattr__(evaluation, "expected_tool", expected_tool)
    object.__setattr__(evaluation, "expected_confirm", expected_confirm)
    object.__setattr__(evaluation, "attempt_budget", attempt_budget)
    object.__setattr__(evaluation, "turn_budget", turn_budget)
    object.__setattr__(evaluation, "_factory_token", _EVALUATION_TOKEN)
    _register_evidence(
        _SCENARIO_EVIDENCE,
        evaluation,
        _scenario_evidence_payload(evaluation),
    )
    return evaluation


def _evaluation(
    policy: ScenarioPolicy,
    status: ScenarioStatus,
    attempt_count: int,
    tripwire_count: int | None,
    projection: AttemptProjection | None,
) -> ScenarioEvaluation:
    bounded_attempts = (
        _cap_nonnegative_count(attempt_count)
        if type(attempt_count) is int and attempt_count >= 0
        else 0
    )
    return _create_evaluation(
        status,
        policy.scenario,
        bounded_attempts,
        tripwire_count,
        projection,
        policy.expected_tool,
        policy.expected_confirm,
        policy.attempt_budget,
        policy.turn_budget,
    )


def evaluate_scenario(
    policy: object,
    raw_attempts: object,
    *,
    mcp_tripwire_observation: object,
) -> ScenarioEvaluation:
    if not _policy_is_canonical(policy) or not isinstance(raw_attempts, tuple):
        scenario = (
            policy.scenario
            if isinstance(policy, ScenarioPolicy)
            and isinstance(policy.scenario, ScenarioId)
            else ScenarioId.READ_ONLY_NO_SKILL
        )
        return _create_evaluation(
            ScenarioStatus.FAIL,
            scenario,
            0,
            None,
            None,
            None,
            None,
            0,
            1,
        )
    tripwire_count = verified_tripwire_count(mcp_tripwire_observation)
    if tripwire_count is None:
        return _evaluation(
            policy,
            ScenarioStatus.FAIL,
            len(raw_attempts),
            None,
            None,
        )
    if tripwire_count != 0:
        return _evaluation(
            policy,
            ScenarioStatus.FAIL,
            len(raw_attempts),
            tripwire_count,
            None,
        )
    if len(raw_attempts) > policy.attempt_budget:
        return _evaluation(
            policy,
            ScenarioStatus.ABORTED,
            len(raw_attempts),
            0,
            None,
        )
    if policy.expected_tool is None:
        return _evaluation(
            policy,
            ScenarioStatus.PASS if not raw_attempts else ScenarioStatus.ABORTED,
            len(raw_attempts),
            0,
            None,
        )
    if len(raw_attempts) != 1:
        return _evaluation(
            policy,
            ScenarioStatus.FAIL,
            len(raw_attempts),
            0,
            None,
        )
    projection = project_pre_tool_attempt(policy, raw_attempts[0])
    return _evaluation(
        policy,
        (
            ScenarioStatus.PASS
            if projection.status is ProjectionStatus.ACCEPTED
            else ScenarioStatus.ABORTED
        ),
        1,
        0,
        projection,
    )


def _create_surface_evaluation(
    status: SurfaceStatus,
    toolset_exact: bool,
    terminal_shell_exposed: bool,
) -> SurfaceEvaluation:
    evaluation = object.__new__(SurfaceEvaluation)
    object.__setattr__(evaluation, "status", status)
    object.__setattr__(evaluation, "toolset_exact", toolset_exact)
    object.__setattr__(
        evaluation,
        "terminal_shell_exposed",
        terminal_shell_exposed,
    )
    object.__setattr__(evaluation, "_factory_token", _SURFACE_TOKEN)
    _register_evidence(
        _SURFACE_EVIDENCE,
        evaluation,
        _surface_evidence_payload(evaluation),
    )
    return evaluation


def evaluate_tool_surface(
    observed_tool_names: object,
    canonical_tool_names: object,
) -> SurfaceEvaluation:
    if not (
        isinstance(observed_tool_names, frozenset)
        and isinstance(canonical_tool_names, frozenset)
        and all(type(name) is str for name in observed_tool_names)
        and all(type(name) is str for name in canonical_tool_names)
    ):
        return _create_surface_evaluation(SurfaceStatus.FAIL, False, True)
    exposed = bool(observed_tool_names.intersection(_FORBIDDEN_SURFACE_NAMES))
    exact = observed_tool_names == canonical_tool_names
    return _create_surface_evaluation(
        SurfaceStatus.PASS if exact and not exposed else SurfaceStatus.FAIL,
        exact,
        exposed,
    )


SAFE_SURFACE_EVIDENCE_KEYS: Final = frozenset(
    {
        "schema_version",
        "spec_id",
        "status",
        "toolset_exact",
        "terminal_shell_exposed",
        "fallback_usage_claim",
        "raw_persisted",
    }
)


def _surface_evidence_payload(
    evaluation: SurfaceEvaluation,
) -> dict[str, object]:
    return {
        "schema_version": "hermes-runtime-tool-surface-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "status": evaluation.status.value,
        "toolset_exact": evaluation.toolset_exact is True,
        "terminal_shell_exposed": evaluation.terminal_shell_exposed is True,
        "fallback_usage_claim": False,
        "raw_persisted": False,
    }


def build_surface_evidence(
    evaluation: object,
) -> dict[str, str | bool]:
    issued = _issued_evidence(_SURFACE_EVIDENCE, evaluation)
    if issued is not None:
        return issued
    return {
        "schema_version": "hermes-runtime-tool-surface-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "status": "fail",
        "toolset_exact": False,
        "terminal_shell_exposed": True,
        "fallback_usage_claim": False,
        "raw_persisted": False,
    }


SAFE_SCENARIO_EVIDENCE_KEYS: Final = frozenset(
    {
        "schema_version",
        "spec_id",
        "scenario",
        "status",
        "expected_tool",
        "attempted_tool",
        "expected_confirm",
        "observed_confirm",
        "attempt_count",
        "attempt_budget",
        "turn_budget",
        "policy_blocked",
        "mcp_tripwire_call_count",
        "raw_persisted",
        "internal_skill_selection_claim",
        "fallback_usage_claim",
    }
)


def classify_ephemeral_response(items: object) -> ResponseDisposition:
    """Classify one closed synthetic disposition without retaining response text."""
    if (
        isinstance(items, tuple)
        and len(items) == 1
        and items[0] is ResponseDisposition.CLARIFICATION_ONLY
    ):
        return ResponseDisposition.CLARIFICATION_ONLY
    return ResponseDisposition.UNCLASSIFIED


def _scenario_evidence_payload(
    evaluation: ScenarioEvaluation,
) -> dict[str, object]:
    projection = evaluation.projection
    expected_tool = (
        evaluation.expected_tool.value
        if isinstance(evaluation.expected_tool, Tool)
        else None
    )
    expected_confirm = (
        evaluation.expected_confirm
        if type(evaluation.expected_confirm) is bool
        else None
    )
    tripwire_count = (
        evaluation.mcp_tripwire_call_count
        if type(evaluation.mcp_tripwire_call_count) is int
        and evaluation.mcp_tripwire_call_count in {0, 1, 2}
        else None
    )
    attempt_count = (
        _cap_nonnegative_count(evaluation.attempt_count)
        if type(evaluation.attempt_count) is int
        and evaluation.attempt_count >= 0
        else 0
    )
    return {
        "schema_version": "hermes-blocked-runtime-smoke-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "scenario": evaluation.scenario.value,
        "status": evaluation.status.value,
        "expected_tool": expected_tool,
        "attempted_tool": (
            projection.attempted_tool.value
            if projection and projection.attempted_tool
            else None
        ),
        "expected_confirm": expected_confirm,
        "observed_confirm": projection.confirm if projection else None,
        "attempt_count": attempt_count,
        "attempt_budget": (
            evaluation.attempt_budget
            if type(evaluation.attempt_budget) is int
            and evaluation.attempt_budget in {0, 1}
            else 0
        ),
        "turn_budget": (
            evaluation.turn_budget
            if type(evaluation.turn_budget) is int
            and evaluation.turn_budget == 1
            else 0
        ),
        "policy_blocked": bool(projection and projection.policy_blocked),
        "mcp_tripwire_call_count": tripwire_count,
        "raw_persisted": False,
        "internal_skill_selection_claim": False,
        "fallback_usage_claim": False,
    }


def build_smoke_evidence(
    evaluation: object,
) -> dict[str, str | bool | int | None]:
    """Return only evaluator-issued raw-free evidence."""
    issued = _issued_evidence(_SCENARIO_EVIDENCE, evaluation)
    if issued is not None:
        return issued
    return {
        "schema_version": "hermes-blocked-runtime-smoke-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "scenario": ScenarioId.READ_ONLY_NO_SKILL.value,
        "status": "fail",
        "expected_tool": None,
        "attempted_tool": None,
        "expected_confirm": None,
        "observed_confirm": None,
        "attempt_count": 0,
        "attempt_budget": 0,
        "turn_budget": 1,
        "policy_blocked": False,
        "mcp_tripwire_call_count": None,
        "raw_persisted": False,
        "internal_skill_selection_claim": False,
        "fallback_usage_claim": False,
    }
