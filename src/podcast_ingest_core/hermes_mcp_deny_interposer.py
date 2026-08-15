"""Offline model of the Spec 029 non-forwarding MCP deny interposer."""
from __future__ import annotations

from typing import Final
import weakref

from podcast_ingest_core.hermes_skill_protocol import (
    canonical_registry_tool_names_from_source,
)


_INTERPOSER_TOKEN: Final = object()
_STATES: dict[int, dict[str, object]] = {}


class TripwireObservation:
    """Opaque, one-use observation issued by one interposer instance."""

    __slots__ = ("_count", "_owner", "_issuance_token")

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use DenyInterposer.observe_tripwire()")


class DenyInterposer:
    __slots__ = (
        "tool_names",
        "_state_key",
        "_factory_token",
        "__weakref__",
    )

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("use from_preflight_snapshot()")

    @classmethod
    def from_preflight_snapshot(cls, snapshot: object) -> "DenyInterposer":
        canonical = canonical_registry_tool_names_from_source()
        if (
            canonical is None
            or not isinstance(snapshot, frozenset)
            or snapshot != canonical
        ):
            raise ValueError("invalid preflight schema snapshot")
        instance = object.__new__(cls)
        key = id(instance)
        object.__setattr__(instance, "tool_names", canonical)
        object.__setattr__(instance, "_state_key", key)
        object.__setattr__(instance, "_factory_token", _INTERPOSER_TOKEN)

        def discard(reference, *, state_key=key) -> None:
            current = _STATES.get(state_key)
            if current is not None and current.get("owner") is reference:
                _STATES.pop(state_key, None)

        owner = weakref.ref(instance, discard)
        _STATES[key] = {"owner": owner, "count": 0, "issuance_token": None}
        return instance

    def _state(self) -> dict[str, object] | None:
        state = _STATES.get(self._state_key)
        if (
            state is None
            or getattr(self, "_factory_token", None) is not _INTERPOSER_TOKEN
            or not isinstance(state.get("owner"), weakref.ReferenceType)
            or state["owner"]() is not self
        ):
            return None
        return state

    @property
    def tripwire_count(self) -> int:
        state = self._state()
        count = state.get("count") if state is not None else None
        return count if type(count) is int and count in {0, 1, 2} else 2

    def handle(self, method: object, params: object) -> dict[str, object]:
        state = self._state()
        if state is None:
            return {"ok": False, "error": "interposer_state_invalid"}
        if method == "initialize":
            return {"ok": True}
        if method == "tools/list":
            return {"tools": sorted(self.tool_names)}
        if method == "tools/call":
            state["count"] = min(self.tripwire_count + 1, 2)
            state["issuance_token"] = None
            return {"ok": False, "error": "policy_denied"}
        return {"ok": False, "error": "method_denied"}

    def observe_tripwire(self) -> TripwireObservation:
        """Issue one observation tied to the current monotonic counter value."""
        state = self._state()
        if state is None:
            raise RuntimeError("interposer state invalid")
        issuance_token = object()
        state["issuance_token"] = issuance_token
        observation = object.__new__(TripwireObservation)
        object.__setattr__(observation, "_count", self.tripwire_count)
        object.__setattr__(observation, "_owner", self)
        object.__setattr__(observation, "_issuance_token", issuance_token)
        return observation


def verified_tripwire_count(observation: object) -> int | None:
    """Consume one issued observation and return its bounded current count."""
    if not isinstance(observation, TripwireObservation):
        return None
    owner = observation._owner
    if not isinstance(owner, DenyInterposer):
        return None
    state = owner._state()
    token = state.get("issuance_token") if state is not None else None
    if (
        state is None
        or token is None
        or observation._issuance_token is not token
        or type(observation._count) is not int
        or observation._count not in {0, 1, 2}
        or observation._count != owner.tripwire_count
    ):
        return None
    state["issuance_token"] = None
    return observation._count
