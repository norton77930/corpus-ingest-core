"""Spec031 future runner boundary; current gates are deliberately not ready.

The public runner evaluates closed offline gates before any lease, marker, or
driver edge. Current source proof cannot reach ready eligibility, so every path
performs zero runtime side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final
import weakref

from podcast_ingest_core.hermes_g2_activation_observation import (
    G2ActivationStatus,
    G2RuntimeSignal,
    build_g2_safe_receipt,
    evaluate_credentialless_feasibility,
    evaluate_g2_activation,
    evaluate_g2_approval_gates,
    evaluate_g2_eligibility,
    not_required_g2_owned_rollback,
    observe_g2_runtime,
)
from podcast_ingest_core.hermes_runtime_controller_plan import (
    ControllerOperation,
    InputMode,
    LogSink,
    REQUIRED_OPERATION_ORDER,
    REQUIRED_TMPFS_ROLES,
    TmpfsRole,
)


EXACT_G2_ACTIVATION_ACK: Final = "SPEC031_G2_CREDENTIALLESS_ACTIVATION_ACK"
ATTEMPT_MARKER_PATH: Final = (
    Path(__file__).resolve().parents[2]
    / ".tmp"
    / "spec031-g2"
    / "attempt.json"
)


class G2DriverOperation(str, Enum):
    INSPECT_METADATA = "inspect_metadata"
    ACTIVATE_DISPOSABLE = "activate_disposable"
    ROLLBACK_G2_OWNED = "rollback_g2_owned"


class G2AttemptStatus(str, Enum):
    BLOCKED_INVALID_PROVENANCE = "BLOCKED_INVALID_PROVENANCE"
    BLOCKED_REVIEW_GATE = "BLOCKED_REVIEW_GATE"
    BLOCKED_HUMAN_APPROVAL = "BLOCKED_HUMAN_APPROVAL"
    BLOCKED_CREDENTIAL_SEAM = "BLOCKED_CREDENTIAL_SEAM"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True, init=False)
class G2ActivationPlan:
    operation_order: tuple
    tmpfs_roles: frozenset
    input_mode: InputMode
    log_sink: LogSink
    credential_channel_absent: bool
    read_only_rootfs: bool
    auto_remove: bool
    no_durable_persistence: bool
    fresh_session_only: bool
    live_actions_authorized: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use build_g2_activation_plan()")

    def __repr__(self) -> str:
        return "G2ActivationPlan()"


@dataclass(frozen=True, init=False)
class G2AttemptResult:
    status: G2AttemptStatus
    attempt_count: int
    retry_count: int
    runtime_status: str
    driver_call_count: int
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use run_g2_activation_once()")

    def __repr__(self) -> str:
        return "G2AttemptResult()"


_REGISTRY: dict[
    int, tuple[weakref.ReferenceType, object, tuple[object, ...], type]
] = {}
_UNSUPPORTED = object()
_ENUM_TYPES = (G2AttemptStatus, ControllerOperation, InputMode, LogSink, TmpfsRole)


def _fields(cls: type) -> tuple[str, ...]:
    return tuple(cls.__annotations__)


def _state(value: object, fields: tuple[str, ...]) -> dict[str, object] | None:
    try:
        state = vars(value)
    except TypeError:
        return None
    if type(state) is not dict or len(state) != len(fields):
        return None
    keys = tuple(state)
    if any(type(key) is not str for key in keys):
        return None
    if any(not any(key == field for field in fields) for key in keys):
        return None
    return state


def _freeze(value: object, field: str = "") -> object:
    if field == "_factory_token":
        return ("identity", value)
    if type(value) is bool:
        return ("bool", value)
    if type(value) is int:
        return ("int", value)
    if type(value) is str:
        return ("str", value)
    if type(value) in _ENUM_TYPES:
        return ("identity", value)
    if type(value) is tuple:
        values = tuple(_freeze(item) for item in value)
        return _UNSUPPORTED if _UNSUPPORTED in values else ("tuple", values)
    if type(value) is frozenset:
        values = tuple(_freeze(item) for item in value)
        return _UNSUPPORTED if _UNSUPPORTED in values else ("frozenset", values)
    return _UNSUPPORTED


def _matches(value: object, sealed: object) -> bool:
    kind, expected = sealed
    if kind == "identity":
        return value is expected
    if kind == "bool":
        return type(value) is bool and value is expected
    if kind == "int":
        return type(value) is int and value == expected
    if kind == "str":
        return type(value) is str and value == expected
    if kind == "tuple":
        return bool(
            type(value) is tuple
            and len(value) == len(expected)
            and all(_matches(item, item_seal) for item, item_seal in zip(value, expected))
        )
    if kind == "frozenset":
        if type(value) is not frozenset or len(value) != len(expected):
            return False
        matched = [False] * len(expected)
        for item in value:
            for index, item_seal in enumerate(expected):
                if not matched[index] and _matches(item, item_seal):
                    matched[index] = True
                    break
            else:
                return False
        return True
    return False


def _issue(value: object, fields: tuple[str, ...]) -> object:
    token = object()
    object.__setattr__(value, "_factory_token", token)
    state = _state(value, fields)
    assert state is not None
    seal = tuple(_freeze(state[name], name) for name in fields)
    assert _UNSUPPORTED not in seal
    key = id(value)

    def discard(reference: weakref.ReferenceType, *, value_key: int = key) -> None:
        current = _REGISTRY.get(value_key)
        if current is not None and current[0] is reference:
            _REGISTRY.pop(value_key, None)

    _REGISTRY[key] = (weakref.ref(value, discard), token, seal, type(value))
    return value


def _make(cls: type, **values: object) -> object:
    item = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(item, name, value)
    return _issue(item, _fields(cls))


def _issued(value: object, cls: type) -> bool:
    if type(value) is not cls:
        return False
    fields = _fields(cls)
    state = _state(value, fields)
    entry = _REGISTRY.get(id(value))
    return bool(
        entry
        and state is not None
        and entry[0]() is value
        and entry[3] is cls
        and state["_factory_token"] is entry[1]
        and len(entry[2]) == len(fields)
        and all(
            _matches(state[name], sealed)
            for name, sealed in zip(fields, entry[2])
        )
    )


def build_g2_activation_plan() -> G2ActivationPlan:
    return _make(
        G2ActivationPlan,
        operation_order=REQUIRED_OPERATION_ORDER,
        tmpfs_roles=REQUIRED_TMPFS_ROLES,
        input_mode=InputMode.ONE_SHOT_STDIN,
        log_sink=LogSink.NONE,
        credential_channel_absent=True,
        read_only_rootfs=True,
        auto_remove=True,
        no_durable_persistence=True,
        fresh_session_only=True,
        live_actions_authorized=False,
    )


def is_factory_issued_g2_activation_plan(value: object) -> bool:
    return _issued(value, G2ActivationPlan)


def _result(status: G2AttemptStatus) -> G2AttemptResult:
    return _make(
        G2AttemptResult,
        status=status,
        attempt_count=0,
        retry_count=0,
        runtime_status="not_run",
        driver_call_count=0,
    )


def _blocked_evaluation(acknowledgement: object):
    feasibility = evaluate_credentialless_feasibility()
    approval = evaluate_g2_approval_gates(acknowledgement)
    return evaluate_g2_activation(
        feasibility,
        evaluate_g2_eligibility(feasibility),
        observe_g2_runtime(G2RuntimeSignal.NOT_RUN, live_start_observed=False),
        not_required_g2_owned_rollback(),
        approval,
    )


def _claim_persistent_attempt_marker() -> bool:
    """Later-only fixed-path atomic claim; unreachable until ready gates exist."""
    try:
        ATTEMPT_MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ATTEMPT_MARKER_PATH.open("x", encoding="utf-8") as handle:
            handle.write(
                '{"spec_id":"031-hermes-g2-credentialless-activation-gate",'
                '"status":"claimed"}\n'
            )
    except OSError:
        return False
    return True


def run_g2_activation_once(
    acknowledgement: object, driver: object
) -> G2AttemptResult:
    """Return before lease, marker, or driver while any offline gate blocks."""
    evaluation = _blocked_evaluation(acknowledgement)
    status_map = {
        G2ActivationStatus.BLOCKED_INVALID_PROVENANCE: G2AttemptStatus.BLOCKED_INVALID_PROVENANCE,
        G2ActivationStatus.BLOCKED_REVIEW_GATE: G2AttemptStatus.BLOCKED_REVIEW_GATE,
        G2ActivationStatus.BLOCKED_HUMAN_APPROVAL: G2AttemptStatus.BLOCKED_HUMAN_APPROVAL,
        G2ActivationStatus.BLOCKED_CREDENTIAL_SEAM: G2AttemptStatus.BLOCKED_CREDENTIAL_SEAM,
    }
    return _result(status_map.get(evaluation.status, G2AttemptStatus.NOT_READY))


def build_g2_attempt_safe_receipt(
    acknowledgement: object,
) -> dict[str, str | bool | int]:
    return build_g2_safe_receipt(_blocked_evaluation(acknowledgement))
