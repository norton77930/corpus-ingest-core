"""Hermes v0.19.0 all-block plugin for the offline Spec029 seam.

Hermes creates its own plugin context and calls ``register(ctx)`` directly. G0
therefore accepts only the explicitly injected, test-only non-sensitive
``SPEC029_EXPECTED_TOOL`` control. It is neither a prompt nor credential and
is never projected or persisted. Production activation remains unauthorized.
"""
from __future__ import annotations

import os
import threading


_BLOCK_ACTION = "block"
_BLOCK_MESSAGE = "SPEC029_POLICY_BLOCK"
_CONTROL_ENV = "SPEC029_EXPECTED_TOOL"
_CONTROL_PREFIX = "spec029-s016-next:"
_lock = threading.Lock()
_registered = False
_registered_context = None
_expected_tool = None
_projection_sink = None
_count = 0


def _expected_tool_from_test_control() -> str | None:
    """Read only the explicit G0 test control, never general process config."""
    raw = os.environ.get(_CONTROL_ENV)
    if type(raw) is not str or not raw.startswith(_CONTROL_PREFIX):
        return None
    expected_tool = raw.removeprefix(_CONTROL_PREFIX)
    if (
        not expected_tool
        or len(expected_tool) > 128
        or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789_-"
            for character in expected_tool
        )
    ):
        return None
    return expected_tool


def _block_directive() -> dict[str, str]:
    """Return a fresh exact v0.19 pre-execution block directive."""
    return {"action": _BLOCK_ACTION, "message": _BLOCK_MESSAGE}


def _abort_projection(count: int) -> dict[str, str | bool | int | None]:
    return {
        "projection_status": "aborted",
        "tool_matched": None,
        "confirm": None,
        "action_next": None,
        "attempt_count": count,
        "policy_blocked": True,
        "raw_persisted": False,
    }


def _closed_projection(
    kwargs: dict[str, object], count: int, expected_tool: str | None
) -> dict[str, str | bool | int | None]:
    if count != 1 or expected_tool is None:
        return _abort_projection(count)
    tool_name = kwargs.get("tool_name")
    args = kwargs.get("args")
    if type(tool_name) is not str or type(args) is not dict:
        return _abort_projection(count)
    confirm = args.get("confirm")
    action = args.get("action")
    if confirm is not False or action != "next" or tool_name != expected_tool:
        return _abort_projection(count)
    return {
        "projection_status": "accepted",
        "tool_matched": True,
        "confirm": confirm,
        "action_next": True,
        "attempt_count": count,
        "policy_blocked": True,
        "raw_persisted": False,
    }


def _pre_tool_call(*_args, **kwargs):
    """Safely project S016 only, then block before any tool execution."""
    global _count
    with _lock:
        _count = min(_count + 1, 2)
        count, expected_tool, sink = _count, _expected_tool, _projection_sink
    if sink is not None:
        try:
            sink(_closed_projection(kwargs, count, expected_tool))
        except Exception:
            # Observation callback failure cannot weaken the fixed block.
            pass
    return _block_directive()


def register(ctx) -> None:
    """Register exactly the v0.19 pre-tool block hook; errors stay observable."""
    global _registered, _registered_context, _expected_tool
    expected_tool = _expected_tool_from_test_control()
    if expected_tool is None:
        raise RuntimeError("valid Spec029 ephemeral control required")
    with _lock:
        if _registered:
            if ctx is _registered_context:
                return
            raise RuntimeError("plugin already registered")
        # This is the only registration: no partial pre/post sequence exists.
        ctx.register_hook("pre_tool_call", _pre_tool_call)
        _expected_tool = expected_tool
        _registered_context = ctx
        _registered = True


def registration_receipt() -> dict[str, bool]:
    """Return fixed safe evidence only after the pre-hook registration succeeds."""
    with _lock:
        registered = _registered is True
    return {
        "registered": registered,
        "pre_hook_registered": registered,
        "raw_persisted": False,
    }
