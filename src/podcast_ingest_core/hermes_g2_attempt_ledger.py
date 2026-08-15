"""Pure in-memory, single-process Spec032 offline attempt ledger.

There is deliberately no filesystem or production-ledger capability in this
closure.  Factory-issued state is valid only in this Python process.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import threading
import weakref
from podcast_ingest_core.hermes_g2_activation_authority import Spec032Scope

_LOCK = threading.RLock()


class AttemptLedgerStatus(str, Enum):
    CLAIMED = "CLAIMED"
    PASS_OFFLINE_EXECUTOR_CONTRACT = "PASS_OFFLINE_EXECUTOR_CONTRACT"
    FAILED_ACTIVATION_QUARANTINED = "FAILED_ACTIVATION_QUARANTINED"
    FAILED_ROLLBACK_QUARANTINED = "FAILED_ROLLBACK_QUARANTINED"
    FAILED_LEDGER_TERMINALIZATION_QUARANTINED = "FAILED_LEDGER_TERMINALIZATION_QUARANTINED"
    BLOCKED_REPLAY = "BLOCKED_REPLAY"
    QUARANTINED_INDETERMINATE_ATTEMPT = "QUARANTINED_INDETERMINATE_ATTEMPT"
    QUARANTINED_MALFORMED_LEDGER = "QUARANTINED_MALFORMED_LEDGER"
    QUARANTINED_INACCESSIBLE_LEDGER = "QUARANTINED_INACCESSIBLE_LEDGER"
    BLOCKED_PRODUCTION_LEDGER_NOT_AUTHORIZED = "BLOCKED_PRODUCTION_LEDGER_NOT_AUTHORIZED"


@dataclass(frozen=True, init=False)
class AttemptLedger:
    _factory_token: object

    def __init__(self, *_a: object, **_k: object) -> None:
        raise TypeError("use create_offline_temporary_ledger()")


@dataclass(frozen=True, init=False)
class AttemptLedgerDecision:
    status: AttemptLedgerStatus
    _factory_token: object

    def __init__(self, *_a: object, **_k: object) -> None:
        raise TypeError("ledger decisions are factory-issued")


_LEDGERS: dict[int, tuple[weakref.ReferenceType[object], object, bool, bool]] = {}
_DECISIONS: dict[int, tuple[weakref.ReferenceType[object], object, AttemptLedgerStatus]] = {}


def _factory_state(value: object, fields: tuple[str, ...]) -> tuple[bool, object | None]:
    """Return a factory token without hostile key equality or hash lookups."""
    try:
        state = vars(value)
    except BaseException:
        return False, None
    if type(state) is not dict or len(state) != len(fields):
        return False, None
    token: object | None = None
    for index, (key, item) in enumerate(state.items()):
        if type(key) is not str or key != fields[index]:
            return False, None
        if key == "_factory_token":
            token = item
    return token is not None, token


def _register(registry: dict, value: object, token: object, *facts: object) -> None:
    key = id(value)

    def discard(ref: weakref.ReferenceType[object], *, key: int = key) -> None:
        with _LOCK:
            current = registry.get(key)
            if current is not None and current[0] is ref:
                registry.pop(key, None)

    registry[key] = (weakref.ref(value, discard), token, *facts)


def _issued(value: object, cls: type, registry: dict) -> bool:
    if type(value) is not cls:
        return False
    valid, token = _factory_state(value, tuple(cls.__annotations__))
    with _LOCK:
        entry = registry.get(id(value))
    return bool(valid and entry is not None and entry[0]() is value and token is entry[1])


def _new(cls: type, **fields: object) -> object:
    value = object.__new__(cls)
    for name, item in fields.items():
        object.__setattr__(value, name, item)
    object.__setattr__(value, "_factory_token", object())
    return value


def create_offline_temporary_ledger(scope: object) -> AttemptLedger | None:
    """Issue one ephemeral offline ledger for the only approved Spec032 scope."""
    if scope is not Spec032Scope.OFFLINE_EXECUTOR_VALIDATION:
        return None
    with _LOCK:
        value = _new(AttemptLedger)
        _register(_LEDGERS, value, vars(value)["_factory_token"], False, False)
        return value


def is_factory_issued_attempt_ledger(value: object) -> bool:
    return _issued(value, AttemptLedger, _LEDGERS)


def _decision(status: AttemptLedgerStatus) -> AttemptLedgerDecision:
    with _LOCK:
        value = _new(AttemptLedgerDecision, status=status)
        _register(_DECISIONS, value, vars(value)["_factory_token"], status)
        return value


def claim_attempt(value: object) -> AttemptLedgerDecision:
    if not is_factory_issued_attempt_ledger(value):
        return _decision(AttemptLedgerStatus.QUARANTINED_MALFORMED_LEDGER)
    with _LOCK:
        entry = _LEDGERS.get(id(value))
        if entry is None or entry[0]() is not value:
            return _decision(AttemptLedgerStatus.QUARANTINED_MALFORMED_LEDGER)
        if entry[2]:
            return _decision(
                AttemptLedgerStatus.BLOCKED_REPLAY
                if entry[3]
                else AttemptLedgerStatus.QUARANTINED_INDETERMINATE_ATTEMPT
            )
        _LEDGERS[id(value)] = (entry[0], entry[1], True, False)
        return _decision(AttemptLedgerStatus.CLAIMED)


def terminalize_attempt(value: object, status: object) -> AttemptLedgerDecision:
    if (
        not is_factory_issued_attempt_ledger(value)
        or type(status) is not AttemptLedgerStatus
        or status is AttemptLedgerStatus.CLAIMED
    ):
        return _decision(AttemptLedgerStatus.FAILED_LEDGER_TERMINALIZATION_QUARANTINED)
    with _LOCK:
        entry = _LEDGERS.get(id(value))
        if entry is None or entry[0]() is not value or not entry[2] or entry[3]:
            return _decision(AttemptLedgerStatus.FAILED_LEDGER_TERMINALIZATION_QUARANTINED)
        _LEDGERS[id(value)] = (entry[0], entry[1], True, True)
        return _decision(status)
