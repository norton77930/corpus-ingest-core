"""Offline source-audit projection for the unavailable Spec032 loader proof."""
from __future__ import annotations
import json
import sys


def audit_pinned_loader_source() -> dict[str, object]:
    # No live source/config/provider is read. The repository has no auditable
    # pinned first-party loader bytes/call path, so this is a fixed fail-closed fact.
    return {
        "pinned_commit": "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6",
        "terminal_status": "BLOCKED_CREDENTIAL_SEAM",
        "activation_ready": False,
        "build_authorized": False,
        "official_loader_verified": False,
        "provider_materialization_status": "blocked_unknown",
        "live_actions_authorized": False,
    }


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != ("offline-source-audit",):
        print(json.dumps({"status": "rejected", "live_actions_authorized": False}, sort_keys=True))
        return 2
    print(json.dumps(audit_pinned_loader_source(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
