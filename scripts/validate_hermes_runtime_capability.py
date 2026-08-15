"""Emit fixed, offline evidence for the Spec 028 Hermes capability gate."""

from __future__ import annotations

import json
import sys
from typing import Sequence

from podcast_ingest_core.hermes_runtime_capability import (
    FailureCode,
    build_capability_evidence,
    evaluate_pinned_hermes_capability,
    evaluate_synthetic_hermes_capability,
    rejected_capability_evidence,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Accept only the fixed offline ``capability`` and ``synthetic`` modes."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1 or arguments[0] not in {"capability", "synthetic"}:
        print(json.dumps(rejected_capability_evidence(FailureCode.INVALID_MODE), sort_keys=True))
        return 2
    try:
        evaluation = (
            evaluate_pinned_hermes_capability()
            if arguments[0] == "capability"
            else evaluate_synthetic_hermes_capability()
        )
        print(json.dumps(build_capability_evidence(evaluation), sort_keys=True))
    except Exception:
        print(json.dumps(rejected_capability_evidence(FailureCode.INTERNAL_FAILURE), sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
