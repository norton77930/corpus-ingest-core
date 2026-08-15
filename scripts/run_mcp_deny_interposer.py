"""Spec029 G0 offline deny-adapter controller; it never binds a listener."""
from __future__ import annotations

import json
import sys


_OFFLINE_MODE = ("offline-contract",)
_REJECTED = {"status": "rejected", "live_actions_authorized": False, "raw_persisted": False}
_SUCCESS = {
    "status": "offline_contract",
    "network_bound": False,
    "live_actions_authorized": False,
    "raw_persisted": False,
}


def main(argv=None):
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != _OFFLINE_MODE:
        print(json.dumps(_REJECTED, sort_keys=True))
        return 2
    print(json.dumps(_SUCCESS, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
