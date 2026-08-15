"""Offline-only Spec031 credentialless feasibility CLI."""
from __future__ import annotations

import json
import sys

from podcast_ingest_core.hermes_g2_activation_observation import (
    G2RuntimeSignal,
    build_g2_safe_receipt,
    evaluate_credentialless_feasibility,
    evaluate_g2_activation,
    evaluate_g2_eligibility,
    not_required_g2_owned_rollback,
    observe_g2_runtime,
)


def _rejected() -> dict[str, object]:
    return {
        "spec_id": "031-hermes-g2-credentialless-activation-gate",
        "status": "rejected",
        "runtime_status": "not_run",
        "live_actions_authorized": False,
        "raw_persisted": False,
    }


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != ("offline-feasibility",):
        print(json.dumps(_rejected(), sort_keys=True))
        return 2
    feasibility = evaluate_credentialless_feasibility()
    receipt = build_g2_safe_receipt(
        evaluate_g2_activation(
            feasibility,
            evaluate_g2_eligibility(feasibility),
            observe_g2_runtime(G2RuntimeSignal.NOT_RUN, live_start_observed=False),
            not_required_g2_owned_rollback(),
        )
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
