"""Future-only Spec032 composition root; this closure must not execute it."""
from __future__ import annotations
import json
import sys

from podcast_ingest_core.hermes_g2_activation_authority import evaluate_spec032_production_gate
from podcast_ingest_core.hermes_g2_activation_executor import build_spec032_safe_receipt, project_blocked_production_gate

EXACT_SPEC032_H4_ACK = "SPEC032_G2_H4_ONE_RUN_ACK"


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    # The acknowledgement is syntax only, never durable/live authorization.
    gate = evaluate_spec032_production_gate()
    result = project_blocked_production_gate(gate)
    if args != ("--ack", EXACT_SPEC032_H4_ACK):
        print(json.dumps(build_spec032_safe_receipt(result), sort_keys=True))
        return 2
    print(json.dumps(build_spec032_safe_receipt(result), sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
