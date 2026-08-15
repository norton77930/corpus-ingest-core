"""Factory-sealed, offline-only Spec031 G2 gate observations.

No function reads a runtime, configuration, credential, session, endpoint, or
log. The pinned source cannot prove the official loader seam, so this module
cannot issue ready eligibility or authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final
import weakref

from podcast_ingest_core.hermes_runtime_controller_plan import (
    REQUIRED_TMPFS_ROLES,
    TmpfsRole,
)
from podcast_ingest_core.hermes_runtime_source_contract import (
    ContractVerdict,
    RuntimeContractEvaluation,
    evaluate_pinned_runtime_contract,
)


class CredentialFeasibilityStatus(str, Enum):
    BLOCKED_INVALID_PROVENANCE = "BLOCKED_INVALID_PROVENANCE"
    BLOCKED_CREDENTIAL_SEAM = "BLOCKED_CREDENTIAL_SEAM"


class G2EligibilityStatus(str, Enum):
    BLOCKED_INVALID_PROVENANCE = "BLOCKED_INVALID_PROVENANCE"
    BLOCKED_CREDENTIAL_SEAM = "BLOCKED_CREDENTIAL_SEAM"
    READY = "READY"


class G2ApprovalStatus(str, Enum):
    BLOCKED_INVALID_PROVENANCE = "BLOCKED_INVALID_PROVENANCE"
    BLOCKED_REVIEW_GATE = "BLOCKED_REVIEW_GATE"
    BLOCKED_HUMAN_APPROVAL = "BLOCKED_HUMAN_APPROVAL"
    READY = "READY"


class RuntimeObservationStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    UNKNOWN = "UNKNOWN"
    QUARANTINED = "QUARANTINED"


class G2RuntimeSignal(str, Enum):
    NOT_RUN = "NOT_RUN"
    UNKNOWN = "UNKNOWN"


class G2RuntimeControlStatus(str, Enum):
    NOT_RUN = "not_run"
    PASS = "PASS"
    QUARANTINED = "QUARANTINED"


class G2RollbackStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    COMPLETE = "COMPLETE"
    QUARANTINED = "QUARANTINED"


class G2RollbackSignal(str, Enum):
    COMPLETE = "COMPLETE"
    UNKNOWN = "UNKNOWN"


class G2ActivationStatus(str, Enum):
    BLOCKED_INVALID_PROVENANCE = "BLOCKED_INVALID_PROVENANCE"
    BLOCKED_REVIEW_GATE = "BLOCKED_REVIEW_GATE"
    BLOCKED_HUMAN_APPROVAL = "BLOCKED_HUMAN_APPROVAL"
    BLOCKED_CREDENTIAL_SEAM = "BLOCKED_CREDENTIAL_SEAM"
    FAILED_ACTIVATION_QUARANTINED = "FAILED_ACTIVATION_QUARANTINED"
    FAILED_ROLLBACK_QUARANTINED = "FAILED_ROLLBACK_QUARANTINED"


@dataclass(frozen=True, init=False)
class CredentialFeasibilityEvaluation:
    status: CredentialFeasibilityStatus
    source_contract_verified: bool
    official_loader_verified: bool
    provider_construction_absent: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_credentialless_feasibility()")

    def __repr__(self) -> str:
        return "CredentialFeasibilityEvaluation()"


@dataclass(frozen=True, init=False)
class G2EligibilityEvaluation:
    status: G2EligibilityStatus
    credential_feasibility_blocked: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_g2_eligibility()")

    def __repr__(self) -> str:
        return "G2EligibilityEvaluation()"


@dataclass(frozen=True, init=False)
class G2ApprovalEvaluation:
    status: G2ApprovalStatus
    exact_acknowledgement: bool
    reviews_passed: bool
    human_approval_verified: bool
    reviewed_revision_verified: bool
    fixture_identity_verified: bool
    baseline_selector_verified: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_g2_approval_gates()")

    def __repr__(self) -> str:
        return "G2ApprovalEvaluation()"


@dataclass(frozen=True, init=False)
class RuntimeObservation:
    status: RuntimeObservationStatus
    live_start_observed: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use observe_g2_runtime()")

    def __repr__(self) -> str:
        return "RuntimeObservation()"


@dataclass(frozen=True, init=False)
class G2RuntimeControlFacts:
    read_only_rootfs: bool
    tmpfs_roles: frozenset[TmpfsRole]
    durable_mount_count: int
    persistent_volume_count: int
    host_port_count: int
    internal_non_host_network: bool
    stdin_byte_count: int
    log_sink_absent: bool
    tty_absent: bool
    shell_absent: bool
    fresh_session_only: bool
    credential_channel_absent: bool
    provider_materialization_not_reached: bool
    mcp_transport_count: int
    tools_call_count: int
    core_dispatch_count: int
    prompt_count: int
    inference_count: int
    baseline_bounded_unchanged: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use issue_g2_runtime_control_facts()")

    def __repr__(self) -> str:
        return "G2RuntimeControlFacts()"


@dataclass(frozen=True, init=False)
class G2RuntimeControlEvaluation:
    status: G2RuntimeControlStatus
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use assess_g2_runtime_controls()")

    def __repr__(self) -> str:
        return "G2RuntimeControlEvaluation()"


@dataclass(frozen=True, init=False)
class G2OwnedRollbackFacts:
    sibling_absent: bool
    tmpfs_destroyed: bool
    network_absent: bool
    credential_channel_absent: bool
    live_lease_revoked: bool
    attempt_consumed: bool
    baseline_controls_unchanged: bool
    unknown_cleanup: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use issue_g2_owned_rollback_facts()")

    def __repr__(self) -> str:
        return "G2OwnedRollbackFacts()"


@dataclass(frozen=True, init=False)
class G2OwnedRollbackEvaluation:
    status: G2RollbackStatus
    g2_owned_rollback_completed: bool
    writers_may_resume: bool
    quarantine_required: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_g2_owned_rollback()")

    def __repr__(self) -> str:
        return "G2OwnedRollbackEvaluation()"


@dataclass(frozen=True, init=False)
class G2ActivationEvaluation:
    status: G2ActivationStatus
    credential_feasibility: CredentialFeasibilityStatus
    eligibility: G2EligibilityStatus
    approval: G2ApprovalStatus
    runtime_observation_status: RuntimeObservationStatus
    runtime_control_status: G2RuntimeControlStatus
    g2_rollback_status: G2RollbackStatus
    live_start_observed: bool
    writers_may_resume: bool
    rollback_quarantine_required: bool
    _factory_token: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use evaluate_g2_activation()")

    def __repr__(self) -> str:
        return "G2ActivationEvaluation()"


_REGISTRY: dict[
    int, tuple[weakref.ReferenceType, object, tuple[object, ...], type]
] = {}
_UNSUPPORTED = object()
_ENUM_TYPES = (
    CredentialFeasibilityStatus,
    G2EligibilityStatus,
    G2ApprovalStatus,
    RuntimeObservationStatus,
    G2RuntimeControlStatus,
    G2RollbackStatus,
    G2ActivationStatus,
    TmpfsRole,
)


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
    if type(value) in _ENUM_TYPES:
        return ("identity", value)
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


def _make(cls: type, **values: object) -> object:
    item = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(item, name, value)
    return _issue(item, _fields(cls))


def _valid_pinned_source(value: object) -> bool:
    if type(value) is not RuntimeContractEvaluation:
        return False
    state = _state(value, tuple(RuntimeContractEvaluation.__annotations__))
    return bool(
        state is not None
        and state["verdict"] is ContractVerdict.BLOCKED_RUNTIME_SEAM
        and state["pinned_manifest_identity_verified"] is True
        and state["safe_one_shot_input_seam_verified"] is False
        and state["plugin_live_activation_authorized"] is False
    )


def evaluate_credentialless_feasibility(
    source_evaluation: object = None,
) -> CredentialFeasibilityEvaluation:
    """Block until pinned source proves a provider-free official loader path."""
    internal_source = source_evaluation is None
    source = (
        evaluate_pinned_runtime_contract()
        if internal_source
        else source_evaluation
    )
    return _make(
        CredentialFeasibilityEvaluation,
        status=CredentialFeasibilityStatus.BLOCKED_CREDENTIAL_SEAM,
        source_contract_verified=bool(internal_source and _valid_pinned_source(source)),
        official_loader_verified=False,
        provider_construction_absent=False,
    )


def is_factory_issued_credential_feasibility(value: object) -> bool:
    return _issued(value, CredentialFeasibilityEvaluation)


def evaluate_g2_eligibility(feasibility: object) -> G2EligibilityEvaluation:
    valid = is_factory_issued_credential_feasibility(feasibility)
    blocked = bool(
        valid
        and feasibility.status is CredentialFeasibilityStatus.BLOCKED_CREDENTIAL_SEAM
    )
    return _make(
        G2EligibilityEvaluation,
        status=(
            G2EligibilityStatus.BLOCKED_CREDENTIAL_SEAM
            if blocked
            else G2EligibilityStatus.BLOCKED_INVALID_PROVENANCE
        ),
        credential_feasibility_blocked=blocked,
    )


def is_factory_issued_g2_eligibility(value: object) -> bool:
    return _issued(value, G2EligibilityEvaluation)


def evaluate_g2_approval_gates(acknowledgement: object) -> G2ApprovalEvaluation:
    exact = (
        type(acknowledgement) is str
        and acknowledgement == "SPEC031_G2_CREDENTIALLESS_ACTIVATION_ACK"
    )
    return _make(
        G2ApprovalEvaluation,
        status=(
            G2ApprovalStatus.BLOCKED_REVIEW_GATE
            if exact
            else G2ApprovalStatus.BLOCKED_HUMAN_APPROVAL
        ),
        exact_acknowledgement=exact,
        reviews_passed=False,
        human_approval_verified=False,
        reviewed_revision_verified=False,
        fixture_identity_verified=False,
        baseline_selector_verified=False,
    )


def is_factory_issued_g2_approval(value: object) -> bool:
    return _issued(value, G2ApprovalEvaluation)


def observe_g2_runtime(
    signal: object, *, live_start_observed: object
) -> RuntimeObservation:
    if type(live_start_observed) is not bool:
        status, started = RuntimeObservationStatus.QUARANTINED, False
    elif type(signal) is not G2RuntimeSignal:
        status, started = RuntimeObservationStatus.QUARANTINED, live_start_observed
    elif signal is G2RuntimeSignal.NOT_RUN and live_start_observed is False:
        status, started = RuntimeObservationStatus.NOT_RUN, False
    elif signal is G2RuntimeSignal.UNKNOWN and live_start_observed is False:
        status, started = RuntimeObservationStatus.UNKNOWN, False
    else:
        status, started = RuntimeObservationStatus.QUARANTINED, live_start_observed
    return _make(RuntimeObservation, status=status, live_start_observed=started)


def is_factory_issued_runtime_observation(value: object) -> bool:
    return _issued(value, RuntimeObservation)


def issue_g2_runtime_control_facts(*values: object) -> G2RuntimeControlFacts | None:
    fields = _fields(G2RuntimeControlFacts)[:-1]
    if len(values) != len(fields):
        return None
    if type(values[1]) is not frozenset:
        return None
    bool_indexes = (0, 5, 7, 8, 9, 10, 11, 12, 18)
    int_indexes = (2, 3, 4, 6, 13, 14, 15, 16, 17)
    if any(type(values[index]) is not bool for index in bool_indexes):
        return None
    if any(type(values[index]) is not int for index in int_indexes):
        return None
    if any(type(item) is not TmpfsRole for item in values[1]):
        return None
    return _make(G2RuntimeControlFacts, **dict(zip(fields, values)))


def assess_g2_runtime_controls(facts: object) -> G2RuntimeControlEvaluation:
    if not _issued(facts, G2RuntimeControlFacts):
        return _make(
            G2RuntimeControlEvaluation,
            status=G2RuntimeControlStatus.QUARANTINED,
        )
    state = vars(facts)
    true_fields = (
        "read_only_rootfs",
        "internal_non_host_network",
        "log_sink_absent",
        "tty_absent",
        "shell_absent",
        "fresh_session_only",
        "credential_channel_absent",
        "provider_materialization_not_reached",
        "baseline_bounded_unchanged",
    )
    count_fields = (
        "durable_mount_count",
        "persistent_volume_count",
        "host_port_count",
        "stdin_byte_count",
        "mcp_transport_count",
        "tools_call_count",
        "core_dispatch_count",
        "prompt_count",
        "inference_count",
    )
    complete = bool(
        all(state[name] is True for name in true_fields)
        and state["tmpfs_roles"] == REQUIRED_TMPFS_ROLES
        and all(state[name] == 0 for name in count_fields)
    )
    return _make(
        G2RuntimeControlEvaluation,
        status=(
            G2RuntimeControlStatus.PASS
            if complete
            else G2RuntimeControlStatus.QUARANTINED
        ),
    )


def issue_g2_owned_rollback_facts(*values: object) -> G2OwnedRollbackFacts | None:
    fields = _fields(G2OwnedRollbackFacts)[:-1]
    if len(values) != len(fields) or any(type(value) is not bool for value in values):
        return None
    return _make(G2OwnedRollbackFacts, **dict(zip(fields, values)))


def not_required_g2_owned_rollback() -> G2OwnedRollbackEvaluation:
    return _make(
        G2OwnedRollbackEvaluation,
        status=G2RollbackStatus.NOT_REQUIRED,
        g2_owned_rollback_completed=False,
        writers_may_resume=False,
        quarantine_required=False,
    )


def evaluate_g2_owned_rollback(facts: object) -> G2OwnedRollbackEvaluation:
    if _issued(facts, G2OwnedRollbackFacts):
        state = vars(facts)
        complete = bool(
            all(
                state[name] is True
                for name in _fields(G2OwnedRollbackFacts)[:-2]
            )
            and state["unknown_cleanup"] is False
        )
    else:
        complete = False
    return _make(
        G2OwnedRollbackEvaluation,
        status=(G2RollbackStatus.COMPLETE if complete else G2RollbackStatus.QUARANTINED),
        g2_owned_rollback_completed=complete,
        writers_may_resume=complete,
        quarantine_required=not complete,
    )


def is_factory_issued_g2_owned_rollback(value: object) -> bool:
    return _issued(value, G2OwnedRollbackEvaluation)


def _invalid_activation() -> G2ActivationEvaluation:
    return _make(
        G2ActivationEvaluation,
        status=G2ActivationStatus.BLOCKED_INVALID_PROVENANCE,
        credential_feasibility=CredentialFeasibilityStatus.BLOCKED_INVALID_PROVENANCE,
        eligibility=G2EligibilityStatus.BLOCKED_INVALID_PROVENANCE,
        approval=G2ApprovalStatus.BLOCKED_INVALID_PROVENANCE,
        runtime_observation_status=RuntimeObservationStatus.QUARANTINED,
        runtime_control_status=G2RuntimeControlStatus.NOT_RUN,
        g2_rollback_status=G2RollbackStatus.QUARANTINED,
        live_start_observed=False,
        writers_may_resume=False,
        rollback_quarantine_required=True,
    )


def evaluate_g2_activation(
    feasibility: object,
    eligibility: object,
    runtime_observation: object,
    rollback: object,
    approval: object = None,
    controls: object = None,
) -> G2ActivationEvaluation:
    if not all(
        (
            is_factory_issued_credential_feasibility(feasibility),
            is_factory_issued_g2_eligibility(eligibility),
            is_factory_issued_runtime_observation(runtime_observation),
            is_factory_issued_g2_owned_rollback(rollback),
        )
    ):
        return _invalid_activation()
    if approval is not None and not is_factory_issued_g2_approval(approval):
        return _invalid_activation()

    live_or_quarantined = bool(
        runtime_observation.live_start_observed
        or runtime_observation.status is RuntimeObservationStatus.QUARANTINED
    )
    rollback_incompatible = bool(
        rollback.status is G2RollbackStatus.NOT_REQUIRED and live_or_quarantined
    )
    effective_rollback_status = (
        G2RollbackStatus.QUARANTINED if rollback_incompatible else rollback.status
    )
    effective_writers_may_resume = bool(
        rollback.writers_may_resume and not rollback_incompatible
    )
    effective_rollback_quarantine = bool(
        rollback.quarantine_required or rollback_incompatible
    )
    control_status = (
        G2RuntimeControlStatus.QUARANTINED
        if live_or_quarantined
        else G2RuntimeControlStatus.NOT_RUN
    )
    approval_status = (
        approval.status if approval is not None else G2ApprovalStatus.BLOCKED_REVIEW_GATE
    )

    if effective_rollback_status is G2RollbackStatus.QUARANTINED:
        status = G2ActivationStatus.FAILED_ROLLBACK_QUARANTINED
    elif runtime_observation.status is RuntimeObservationStatus.QUARANTINED:
        status = G2ActivationStatus.FAILED_ACTIVATION_QUARANTINED
    elif approval is not None and approval.status is G2ApprovalStatus.BLOCKED_HUMAN_APPROVAL:
        status = G2ActivationStatus.BLOCKED_HUMAN_APPROVAL
    elif approval is not None:
        status = G2ActivationStatus.BLOCKED_REVIEW_GATE
    else:
        status = G2ActivationStatus.BLOCKED_CREDENTIAL_SEAM

    return _make(
        G2ActivationEvaluation,
        status=status,
        credential_feasibility=feasibility.status,
        eligibility=eligibility.status,
        approval=approval_status,
        runtime_observation_status=runtime_observation.status,
        runtime_control_status=control_status,
        g2_rollback_status=effective_rollback_status,
        live_start_observed=runtime_observation.live_start_observed,
        writers_may_resume=effective_writers_may_resume,
        rollback_quarantine_required=effective_rollback_quarantine,
    )


def is_factory_issued_g2_activation(value: object) -> bool:
    return _issued(value, G2ActivationEvaluation)


SAFE_G2_RECEIPT_KEYS: Final = frozenset(
    {
        "schema_version",
        "spec_id",
        "status",
        "terminal_status",
        "attempt_count",
        "retry_count",
        "driver_call_count",
        "credential_feasibility",
        "eligibility",
        "approval",
        "offline_reviews_passed",
        "human_approval_verified",
        "reviewed_revision_verified",
        "fixture_identity_verified",
        "baseline_selector_verified",
        "fixture_build_authorized",
        "official_loader_verified",
        "provider_materialization_status",
        "runtime_status",
        "runtime_observation_status",
        "runtime_control_status",
        "runtime_counts_observed",
        "read_only_rootfs_observed",
        "tmpfs_role_count",
        "durable_mount_count",
        "persistent_volume_count",
        "host_port_count",
        "internal_non_host_network_observed",
        "stdin_byte_count",
        "log_sink_observed",
        "tty_observed",
        "shell_observed",
        "fresh_session_observed",
        "credential_channel_runtime_observed",
        "credential_value_read",
        "credential_value_copied",
        "credential_value_projected",
        "credential_value_logged",
        "mcp_transport_count",
        "tools_call_count",
        "core_dispatch_count",
        "prompt_count",
        "inference_count",
        "baseline_bounded_unchanged_observed",
        "g2_rollback_status",
        "rollback_required",
        "rollback_quarantined",
        "writers_may_resume",
        "runtime_status_not_run",
        "c6_status",
        "c6_rerun",
        "c6_authorized",
        "g3a_authorized",
        "further_live_authorized",
        "live_actions_authorized",
        "raw_persisted",
        "raw_persisted_scope",
    }
)


def build_g2_safe_receipt(evaluation: object) -> dict[str, str | bool | int]:
    """Project only bounded facts; zero counts are marked as unobserved."""
    if not is_factory_issued_g2_activation(evaluation):
        evaluation = _invalid_activation()

    runtime_status = {
        RuntimeObservationStatus.NOT_RUN: "not_run",
        RuntimeObservationStatus.UNKNOWN: "unknown",
        RuntimeObservationStatus.QUARANTINED: "quarantined",
    }[evaluation.runtime_observation_status]
    counts_observed = evaluation.runtime_control_status is G2RuntimeControlStatus.PASS
    rollback_quarantined = evaluation.g2_rollback_status is G2RollbackStatus.QUARANTINED
    rollback_required = bool(evaluation.live_start_observed or rollback_quarantined)

    return {
        "schema_version": "hermes-g2-activation-receipt-v2",
        "spec_id": "031-hermes-g2-credentialless-activation-gate",
        "status": evaluation.status.value,
        "terminal_status": evaluation.status.value,
        "attempt_count": 0,
        "retry_count": 0,
        "driver_call_count": 0,
        "credential_feasibility": evaluation.credential_feasibility.value,
        "eligibility": evaluation.eligibility.value,
        "approval": evaluation.approval.value,
        "offline_reviews_passed": False,
        "human_approval_verified": False,
        "reviewed_revision_verified": False,
        "fixture_identity_verified": False,
        "baseline_selector_verified": False,
        "fixture_build_authorized": False,
        "official_loader_verified": False,
        "provider_materialization_status": "blocked_unknown",
        "runtime_status": runtime_status,
        "runtime_observation_status": evaluation.runtime_observation_status.value,
        "runtime_control_status": evaluation.runtime_control_status.value,
        "runtime_counts_observed": counts_observed,
        "read_only_rootfs_observed": False,
        "tmpfs_role_count": 0,
        "durable_mount_count": 0,
        "persistent_volume_count": 0,
        "host_port_count": 0,
        "internal_non_host_network_observed": False,
        "stdin_byte_count": 0,
        "log_sink_observed": False,
        "tty_observed": False,
        "shell_observed": False,
        "fresh_session_observed": False,
        "credential_channel_runtime_observed": False,
        "credential_value_read": False,
        "credential_value_copied": False,
        "credential_value_projected": False,
        "credential_value_logged": False,
        "mcp_transport_count": 0,
        "tools_call_count": 0,
        "core_dispatch_count": 0,
        "prompt_count": 0,
        "inference_count": 0,
        "baseline_bounded_unchanged_observed": False,
        "g2_rollback_status": evaluation.g2_rollback_status.value,
        "rollback_required": rollback_required,
        "rollback_quarantined": rollback_quarantined,
        "writers_may_resume": evaluation.writers_may_resume,
        "runtime_status_not_run": runtime_status == "not_run",
        "c6_status": "pass_current_not_rerun",
        "c6_rerun": False,
        "c6_authorized": False,
        "g3a_authorized": False,
        "further_live_authorized": False,
        "live_actions_authorized": False,
        "raw_persisted": False,
        "raw_persisted_scope": "safe_receipt_only",
    }
