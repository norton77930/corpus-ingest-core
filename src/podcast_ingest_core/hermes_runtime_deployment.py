"""Offline Spec029 v0.19 baseline-overlay and rollback models.

This module models a disposable overlay only.  It does not inspect containers,
read deployment configuration, execute Docker, or expose a live transition.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final
import threading
import time as _time
import weakref

from podcast_ingest_core.hermes_runtime_source_contract import (
    ContractVerdict,
    RuntimeContractEvaluation,
    evaluate_pinned_runtime_contract,
)


class PreflightStatus(str, Enum):
    BLOCKED_SOURCE_DRIFT = "BLOCKED_SOURCE_DRIFT"
    BLOCKED_RUNTIME_SEAM = "BLOCKED_RUNTIME_SEAM"
    BLOCKED_CONTROL_PLANE = "BLOCKED_CONTROL_PLANE"
    BLOCKED_INVALID_EVIDENCE = "BLOCKED_INVALID_EVIDENCE"


class RollbackStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FAILED_QUARANTINED = "FAILED_QUARANTINED"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


_PREFLIGHT_TOKEN: Final = object()
_PREFLIGHT_EVIDENCE: dict[int, tuple[weakref.ReferenceType, dict[str, object]]] = {}
_LEASE_LOCK = threading.Lock()
_OFFLINE_CONTROLLER_LEASES: dict[
    int, tuple[weakref.ReferenceType, object, str, float, bool]
] = {}
_LEDGER_LOCK = threading.Lock()
_ISSUED_LEDGERS: dict[int, tuple[weakref.ReferenceType, object]] = {}


class OfflineControllerLease:
    """Opaque G0 controller lease; it cannot authorize a live action."""

    __slots__ = ("_state_key", "_token", "__weakref__")

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use issue_offline_controller_lease()")


def issue_offline_controller_lease(
    owner: object, *, ttl_seconds: object
) -> OfflineControllerLease:
    """Issue a bounded offline-model lease from the trusted monotonic clock."""
    if (
        type(owner) is not str
        or not owner
        or type(ttl_seconds) is not int
        or not 0 < ttl_seconds <= 300
    ):
        raise ValueError("invalid offline controller lease request")
    with _LEASE_LOCK:
        lease = object.__new__(OfflineControllerLease)
        state_key, token = id(lease), object()
        object.__setattr__(lease, "_state_key", state_key)
        object.__setattr__(lease, "_token", token)

        def discard(reference, *, key=state_key) -> None:
            with _LEASE_LOCK:
                current = _OFFLINE_CONTROLLER_LEASES.get(key)
                if current is not None and current[0] is reference:
                    _OFFLINE_CONTROLLER_LEASES.pop(key, None)

        _OFFLINE_CONTROLLER_LEASES[state_key] = (
            weakref.ref(lease, discard),
            token,
            owner,
            _time.monotonic() + ttl_seconds,
            False,
        )
        return lease


def consume_offline_controller_lease(lease: object, owner: object) -> bool:
    """Atomically consume one trusted-clock lease; never authorize live action."""
    if not isinstance(lease, OfflineControllerLease) or type(owner) is not str:
        return False
    with _LEASE_LOCK:
        state = _OFFLINE_CONTROLLER_LEASES.get(getattr(lease, "_state_key", None))
        if (
            state is None
            or state[0]() is not lease
            or state[1] is not getattr(lease, "_token", None)
            or state[2] != owner
            or state[4] is True
        ):
            return False
        if _time.monotonic() >= state[3]:
            # Expiry is irrevocable even if a faulty clock later moves backward.
            _OFFLINE_CONTROLLER_LEASES[id(lease)] = (
                state[0], state[1], state[2], state[3], True
            )
            return False
        _OFFLINE_CONTROLLER_LEASES[id(lease)] = (
            state[0], state[1], state[2], state[3], True
        )
        return True


@dataclass(frozen=True)
class BaselineOverlayFacts:
    """Safe controller-projected facts for a v0.19 disposable overlay."""

    baseline_v019_image: str
    disposable_overlay_prepared: bool
    overlay_isolated_from_production: bool
    controller_controls_resolved: bool
    interposer_placement_verified: bool
    interposer_non_forwarding_verified: bool
    terminal_shell_absent: bool
    rollback_recipe_complete: bool


@dataclass(frozen=True, init=False)
class PreflightEvaluation:
    status: PreflightStatus
    baseline_image_pinned: bool
    disposable_overlay_prepared: bool
    overlay_isolated_from_production: bool
    controls_resolved: bool
    interposer_boundary_verified: bool
    terminal_shell_absent: bool
    rollback_recipe_complete: bool
    activation_authorized: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_offline_overlay_preflight()")


@dataclass(frozen=True)
class RollbackFacts:
    overlay_deactivated: bool
    overlay_removed: bool
    baseline_v019_preserved: bool
    controller_controls_restored: bool
    offline_controller_lease_revoked: bool


@dataclass(frozen=True)
class RollbackEvaluation:
    status: RollbackStatus
    prior_controls_restored: bool
    writers_may_resume: bool


@dataclass(frozen=True, init=False)
class PrivateDeploymentLedger:
    """Factory-only owner ledger; identities never enter safe evidence."""

    _owner: str
    owner_only: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use PrivateDeploymentLedger.create()")

    @classmethod
    def create(cls, owner: object) -> "PrivateDeploymentLedger":
        if type(owner) is not str or not owner:
            raise ValueError("owner required")
        ledger = object.__new__(cls)
        key, token = id(ledger), object()
        object.__setattr__(ledger, "_owner", owner)
        object.__setattr__(ledger, "owner_only", True)
        object.__setattr__(ledger, "_factory_token", token)

        def discard(reference, *, ledger_key=key) -> None:
            with _LEDGER_LOCK:
                current = _ISSUED_LEDGERS.get(ledger_key)
                if current is not None and current[0] is reference:
                    _ISSUED_LEDGERS.pop(ledger_key, None)

        with _LEDGER_LOCK:
            _ISSUED_LEDGERS[key] = (weakref.ref(ledger, discard), token)
        return ledger


def _is_factory_issued_ledger(ledger: object) -> bool:
    if not isinstance(ledger, PrivateDeploymentLedger):
        return False
    with _LEDGER_LOCK:
        current = _ISSUED_LEDGERS.get(id(ledger))
        return (
            current is not None
            and current[0]() is ledger
            and current[1] is getattr(ledger, "_factory_token", None)
            and getattr(ledger, "owner_only", None) is True
        )


def _register_preflight_evidence(evaluation: object, payload: dict[str, object]) -> None:
    key = id(evaluation)

    def discard(reference, *, evidence_key=key) -> None:
        current = _PREFLIGHT_EVIDENCE.get(evidence_key)
        if current is not None and current[0] is reference:
            _PREFLIGHT_EVIDENCE.pop(evidence_key, None)

    _PREFLIGHT_EVIDENCE[key] = (weakref.ref(evaluation, discard), dict(payload))


def _issued_preflight_evidence(evaluation: object) -> dict[str, object] | None:
    current = _PREFLIGHT_EVIDENCE.get(id(evaluation))
    if current is None or current[0]() is not evaluation:
        return None
    return dict(current[1])


def _is_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _strict_bool_fields(value: object) -> bool:
    return hasattr(value, "__dict__") and all(
        type(item) is bool for item in value.__dict__.values()
    )


def _create_preflight(
    status: PreflightStatus,
    *,
    baseline_image_pinned: bool,
    disposable_overlay_prepared: bool,
    overlay_isolated_from_production: bool,
    controls_resolved: bool,
    interposer_boundary_verified: bool,
    terminal_shell_absent: bool,
    rollback_recipe_complete: bool,
) -> PreflightEvaluation:
    evaluation = object.__new__(PreflightEvaluation)
    values = {
        "status": status,
        "baseline_image_pinned": baseline_image_pinned,
        "disposable_overlay_prepared": disposable_overlay_prepared,
        "overlay_isolated_from_production": overlay_isolated_from_production,
        "controls_resolved": controls_resolved,
        "interposer_boundary_verified": interposer_boundary_verified,
        "terminal_shell_absent": terminal_shell_absent,
        "rollback_recipe_complete": rollback_recipe_complete,
        "activation_authorized": False,
        "_factory_token": _PREFLIGHT_TOKEN,
    }
    for name, value in values.items():
        object.__setattr__(evaluation, name, value)
    _register_preflight_evidence(evaluation, _preflight_evidence_payload(evaluation))
    return evaluation


def _invalid_preflight() -> PreflightEvaluation:
    return _create_preflight(
        PreflightStatus.BLOCKED_INVALID_EVIDENCE,
        baseline_image_pinned=False,
        disposable_overlay_prepared=False,
        overlay_isolated_from_production=False,
        controls_resolved=False,
        interposer_boundary_verified=False,
        terminal_shell_absent=False,
        rollback_recipe_complete=False,
    )


def evaluate_offline_overlay_preflight(
    facts: object, source_evaluation: object
) -> PreflightEvaluation:
    """Evaluate an offline baseline-overlay plan; G0 never authorizes activation."""
    current_source = evaluate_pinned_runtime_contract()
    if (
        not isinstance(source_evaluation, RuntimeContractEvaluation)
        or source_evaluation != current_source
    ):
        return _create_preflight(
            PreflightStatus.BLOCKED_SOURCE_DRIFT,
            baseline_image_pinned=False,
            disposable_overlay_prepared=False,
            overlay_isolated_from_production=False,
            controls_resolved=False,
            interposer_boundary_verified=False,
            terminal_shell_absent=False,
            rollback_recipe_complete=False,
        )
    if (
        not isinstance(facts, BaselineOverlayFacts)
        or not all(
            type(value) is bool
            for name, value in facts.__dict__.items()
            if name != "baseline_v019_image"
        )
    ):
        return _invalid_preflight()
    pinned = _is_digest(facts.baseline_v019_image)
    interposer = all((facts.interposer_placement_verified, facts.interposer_non_forwarding_verified))
    controls = facts.controller_controls_resolved
    complete = all(
        (
            pinned,
            facts.disposable_overlay_prepared,
            facts.overlay_isolated_from_production,
            controls,
            interposer,
            facts.terminal_shell_absent,
            facts.rollback_recipe_complete,
        )
    )
    if not complete:
        return _create_preflight(
            PreflightStatus.BLOCKED_CONTROL_PLANE,
            baseline_image_pinned=pinned,
            disposable_overlay_prepared=facts.disposable_overlay_prepared,
            overlay_isolated_from_production=facts.overlay_isolated_from_production,
            controls_resolved=controls,
            interposer_boundary_verified=interposer,
            terminal_shell_absent=facts.terminal_shell_absent,
            rollback_recipe_complete=facts.rollback_recipe_complete,
        )
    # No safe input/provider/overlay runtime seam has been verified in G0.
    return _create_preflight(
        PreflightStatus.BLOCKED_RUNTIME_SEAM,
        baseline_image_pinned=True,
        disposable_overlay_prepared=True,
        overlay_isolated_from_production=True,
        controls_resolved=True,
        interposer_boundary_verified=True,
        terminal_shell_absent=True,
        rollback_recipe_complete=True,
    )


SAFE_PREFLIGHT_EVIDENCE_KEYS: Final = frozenset(
    {
        "schema_version",
        "spec_id",
        "status",
        "baseline_image_pinned",
        "disposable_overlay_prepared",
        "overlay_isolated_from_production",
        "controls_resolved",
        "interposer_boundary_verified",
        "terminal_shell_absent",
        "rollback_recipe_complete",
        "activation_authorized",
        "live_preflight_run",
        "raw_persisted",
    }
)


def _preflight_evidence_payload(evaluation: PreflightEvaluation) -> dict[str, object]:
    return {
        "schema_version": "hermes-runtime-preflight-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "status": evaluation.status.value,
        "baseline_image_pinned": evaluation.baseline_image_pinned is True,
        "disposable_overlay_prepared": evaluation.disposable_overlay_prepared is True,
        "overlay_isolated_from_production": evaluation.overlay_isolated_from_production is True,
        "controls_resolved": evaluation.controls_resolved is True,
        "interposer_boundary_verified": evaluation.interposer_boundary_verified is True,
        "terminal_shell_absent": evaluation.terminal_shell_absent is True,
        "rollback_recipe_complete": evaluation.rollback_recipe_complete is True,
        "activation_authorized": False,
        "live_preflight_run": False,
        "raw_persisted": False,
    }


def build_preflight_evidence(evaluation: object) -> dict[str, str | bool]:
    issued = _issued_preflight_evidence(evaluation)
    if issued is not None:
        return issued
    return {
        "schema_version": "hermes-runtime-preflight-evidence-v1",
        "spec_id": "029-hermes-blocked-tool-attempt-runtime-smoke",
        "status": PreflightStatus.BLOCKED_INVALID_EVIDENCE.value,
        "baseline_image_pinned": False,
        "disposable_overlay_prepared": False,
        "overlay_isolated_from_production": False,
        "controls_resolved": False,
        "interposer_boundary_verified": False,
        "terminal_shell_absent": False,
        "rollback_recipe_complete": False,
        "activation_authorized": False,
        "live_preflight_run": False,
        "raw_persisted": False,
    }


def evaluate_rollback(facts: object) -> RollbackEvaluation:
    """Incomplete exact restoration facts remain quarantined."""
    if not isinstance(facts, RollbackFacts) or not _strict_bool_fields(facts):
        return RollbackEvaluation(RollbackStatus.INVALID_EVIDENCE, False, False)
    if all(facts.__dict__.values()):
        return RollbackEvaluation(RollbackStatus.COMPLETE, True, True)
    return RollbackEvaluation(RollbackStatus.FAILED_QUARANTINED, False, False)


def build_deployment_evidence(ledger: object) -> dict[str, str | bool]:
    return {
        "schema_version": "hermes-runtime-deployment-evidence-v1",
        "owner_ledger_present": _is_factory_issued_ledger(ledger),
        "live_preflight_run": False,
        "raw_persisted": False,
    }
