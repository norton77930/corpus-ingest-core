"""Spec029 G0 offline baseline-overlay planner; activation is unauthorized."""
from __future__ import annotations

import json
import sys


_OFFLINE_MODES = frozenset({("offline-baseline-overlay-plan",), ("offline-validate",)})
_REJECTED = {"status": "rejected", "live_actions_authorized": False, "raw_persisted": False}
_BLOCKED = {
    "status": "BLOCKED_RUNTIME_SEAM",
    "activation_authorized": False,
    "live_actions_authorized": False,
    "live_preflight_run": False,
    "raw_persisted": False,
}


def main(argv=None):
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args not in _OFFLINE_MODES:
        print(json.dumps(_REJECTED, sort_keys=True))
        return 2
    print(json.dumps(_BLOCKED, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
