"""Spec034 offline governance contract guards."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/034-hermes-v019-pinned-startup-source-graph"


def test_spec034_governance_has_frozen_h2_and_static_only_boundaries():
    for relative in (
        "proposal.md", "spec.md", "plan.md", "tasks.md", "checklists/requirements.md",
        "checklists/safety.md", "contracts/h1-source-inventory-proposal.json",
        "contracts/h1-discovery-receipt.json", "contracts/source-bundle-manifest.json",
        "contracts/predecessor-boundary.json", "contracts/python-test-capability-manifest.json",
        "contracts/reviewed-artifact-manifest.json", "contracts/review-root.json",
    ):
        assert (SPEC / relative).is_file()
    manifest = json.loads((SPEC / "contracts/source-bundle-manifest.json").read_text(encoding="utf-8"))
    inventory = SPEC / "contracts/h1-source-inventory-proposal.json"
    assert manifest["h1_inventory_sha256"] == hashlib.sha256(inventory.read_bytes()).hexdigest()
    assert len(manifest["files"]) == 20
    assert manifest["runtime_status"] == "not_run"
    assert manifest["live_actions_authorized"] is False
    reviewed = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    root = json.loads((SPEC / "contracts/review-root.json").read_text(encoding="utf-8"))
    assert reviewed["schema_version"] == "spec034-reviewed-artifact-manifest-v8"
    assert reviewed["review_evidence_included"] is False
    capability = json.loads((SPEC / "contracts/python-test-capability-manifest.json").read_text(encoding="utf-8"))
    assert capability["schema_version"] == "spec034-python-test-capability-manifest-v1"
    assert root["schema_version"] == "spec034-detached-review-root-v8"
    assert root["capability_manifest_sha256"] == hashlib.sha256((SPEC / "contracts/python-test-capability-manifest.json").read_bytes()).hexdigest()
    assert "spec033_review_root_sha256" in json.loads((SPEC / "contracts/predecessor-boundary.json").read_text(encoding="utf-8"))


def test_spec034_sentinel_blocks_upstream_imports_and_network_execution():
    sentinel = ast.parse((ROOT / "scripts/spec034_offline_runtime_sentinel.py").read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(sentinel) if isinstance(node, ast.Import) for alias in node.names}
    assert {"socket", "subprocess"} <= imported
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in (ROOT / "scripts/verify_spec_034_offline.py").read_text(encoding="utf-8")
    assert "--noconftest" in (ROOT / "scripts/verify_spec_034_offline.py").read_text(encoding="utf-8")
    values = [node.value for node in sentinel.body if isinstance(node, ast.Assign)]
    roots = next(ast.literal_eval(value.args[0]) for value in values if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "frozenset")
    assert {"agent", "hermes_cli", "run_agent", "providers", "model_tools", "plugins"} <= set(roots)
