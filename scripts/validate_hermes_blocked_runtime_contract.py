"""Offline-only validator for Spec 029 pinned source contract."""
from __future__ import annotations
import json, sys
from podcast_ingest_core.hermes_runtime_source_contract import build_contract_evidence, evaluate_pinned_runtime_contract

def main(argv=None):
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != ("offline",):
        print(json.dumps({"verdict":"BLOCKED_SOURCE_DRIFT","live_actions_authorized":False}, sort_keys=True)); return 2
    print(json.dumps(build_contract_evidence(evaluate_pinned_runtime_contract()), sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
