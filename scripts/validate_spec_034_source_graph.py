"""Project Spec034's static-only public receipt; no network or upstream import."""
from __future__ import annotations
import json
import sys
from podcast_ingest_core.hermes_v019_startup_source_graph import (
    audit_spec034_bundled_plugin, audit_spec034_startup_source_graph,
    project_spec034_source_graph_receipt, validate_spec034_source_bundle,
)


def main(argv: object = None) -> int:
    if tuple(sys.argv[1:] if argv is None else argv):
        print(json.dumps({"status": "rejected", "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 2
    bundle = validate_spec034_source_bundle()
    graph = audit_spec034_startup_source_graph(bundle)
    plugin = audit_spec034_bundled_plugin(bundle, graph)
    print(json.dumps(project_spec034_source_graph_receipt(bundle, graph, plugin), sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
