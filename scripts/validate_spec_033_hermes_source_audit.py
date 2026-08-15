"""Static Spec033 receipt projection; no network and no upstream execution."""
from __future__ import annotations
import json
import sys
from podcast_ingest_core.hermes_v019_source_audit import (
    audit_hermes_v019_loader_order,
    project_hermes_v019_source_audit_receipt,
    validate_hermes_v019_source_bundle,
)


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args:
        print(json.dumps({"status": "rejected", "live_actions_authorized": False}, sort_keys=True))
        return 2
    bundle = validate_hermes_v019_source_bundle()
    receipt = project_hermes_v019_source_audit_receipt(bundle, audit_hermes_v019_loader_order(bundle))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
