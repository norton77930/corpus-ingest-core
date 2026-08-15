"""Offline-only Spec032 readiness projection; no runner or concrete adapter."""
from __future__ import annotations
import json
import sys

from podcast_ingest_core.hermes_g2_activation_authority import evaluate_spec032_production_gate
from podcast_ingest_core.hermes_g2_activation_executor import build_spec032_safe_receipt, project_blocked_production_gate


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != ("offline-executor-contract",):
        print(json.dumps({"status": "rejected", "live_actions_authorized": False}, sort_keys=True))
        return 2
    result = project_blocked_production_gate(evaluate_spec032_production_gate())
    print(json.dumps(build_spec032_safe_receipt(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
