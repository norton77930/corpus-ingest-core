"""Governance and documentation guards for Spec033."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/033-hermes-v019-pinned-source-loader-audit"


def test_spec033_gate_contracts_and_top_level_pointers_are_present_and_honest():
    for relative in (
        "proposal.md", "spec.md", "plan.md", "data-model.md", "tasks.md",
        "checklists/requirements.md", "checklists/safety.md", "contracts/source-bundle-manifest.json", "contracts/predecessor-digests.json",
        "contracts/reviewed-artifact-manifest.json", "contracts/review-root.json", "contracts/loader-order-verdict.json",
    ):
        assert (SPEC / relative).is_file()
    verdict = json.loads((SPEC / "contracts/loader-order-verdict.json").read_text(encoding="utf-8"))
    assert verdict == {
        "spec_id": "033-hermes-v019-pinned-source-loader-audit",
        "source_bundle_valid": True,
        "bounded_loader_edges_verified": True,
        "loader_path_verified": False,
        "required_hook_registration_verified": False,
        "dynamic_execution_status": "unresolved",
        "plugins_list_status": "manifest_only_not_loader_proof",
        "import_time_callers": ["model_tools.py"],
        "import_time_status": "BLOCKED_SOURCE_GRAPH",
        "call_time_callers": ["hermes_cli/main.py", "hermes_cli/oneshot.py"],
        "call_time_status": "BLOCKED_SOURCE_GRAPH",
        "terminal_status": "BLOCKED_SOURCE_GRAPH",
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }
    reviewed = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    assert reviewed["schema_version"] == "spec033-reviewed-artifact-manifest-v2"
    assert reviewed["review_evidence_included"] is False and reviewed["live_actions_authorized"] is False
    reviewed_paths = {artifact["path"] for artifact in reviewed["artifacts"]}
    source_manifest = json.loads((SPEC / "contracts/source-bundle-manifest.json").read_text(encoding="utf-8"))
    assert {
        f"specs/033-hermes-v019-pinned-source-loader-audit/upstream/NousResearch-hermes-agent-b7a05b6/{record['path']}"
        for record in source_manifest["files"]
    } <= reviewed_paths
    for artifact in reviewed["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.is_file() and path.stat().st_size == artifact["byte_length"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
    for relative in ("README.md", "specs/README.md", "docs/roadmap.md", "docs/verification-matrix.md"):
        pointer = (ROOT / relative).read_text(encoding="utf-8")
        assert "Spec 033" in pointer and "BLOCKED_SOURCE_GRAPH" in pointer and "not_run" in pointer


def test_predecessor_boundary_covers_spec029_through_spec032_without_executing_predecessors():
    from scripts import verify_spec_033_offline as verifier_module

    predecessor = json.loads((SPEC / "contracts/predecessor-digests.json").read_text(encoding="utf-8"))
    assert predecessor["schema_version"] == "spec033-predecessor-boundary-v3"
    assert predecessor["chain_scope"] == ["029", "030", "031", "032"]
    roots = predecessor["authority_roots"]
    assert tuple(roots) == (
        "spec032_predecessor_verifier",
        "spec032_predecessor_manifest",
        "spec032_reviewed_manifest",
    )
    assert roots["spec032_predecessor_verifier"]["inventory_symbol"] == "AUTHORITATIVE_PREDECESSOR_PATHS"
    assert roots["spec032_predecessor_manifest"]["schema_version"] == "spec032-predecessor-boundary-v2"
    assert roots["spec032_reviewed_manifest"]["schema_version"] == "spec032-reviewed-artifact-manifest-v2"
    assert predecessor["successor_mutable_shared_paths"] == [
        "README.md",
        "docs/roadmap.md",
        "docs/verification-matrix.md",
        "specs/README.md",
    ]
    assert verifier_module._predecessor_boundary_valid() is True
    verifier = (ROOT / "scripts/verify_spec_033_offline.py").read_text(encoding="utf-8")
    assert "subprocess.run" in verifier
    assert "verify_spec_032_offline.py\")" not in verifier


def test_detached_review_root_seals_reviewed_manifest_without_self_hash_cycle():
    root = json.loads((SPEC / "contracts/review-root.json").read_text(encoding="utf-8"))
    reviewed_path = SPEC / "contracts/reviewed-artifact-manifest.json"
    assert root["schema_version"] == "spec033-detached-review-root-v2"
    assert root["reviewed_manifest_sha256"] == hashlib.sha256(reviewed_path.read_bytes()).hexdigest()
    reviewed = json.loads(reviewed_path.read_text(encoding="utf-8"))
    paths = {item["path"] for item in reviewed["artifacts"]}
    assert "scripts/verify_spec_033_offline.py" in paths
    assert "specs/033-hermes-v019-pinned-source-loader-audit/contracts/review-root.json" not in paths
    verifier = (ROOT / "scripts/verify_spec_033_offline.py").read_text(encoding="utf-8")
    assert '"review_root_sha256"' in verifier
    assert "REVIEW_ROOT_SHA256" not in verifier


def test_final_verifier_statically_regenerates_and_exact_compares_audit_verdict():
    verifier = ast.parse((ROOT / "scripts/verify_spec_033_offline.py").read_text(encoding="utf-8"))
    function = next(node for node in verifier.body if isinstance(node, ast.FunctionDef) and node.name == "_verdict_matches_audit")
    calls = {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"validate_hermes_v019_source_bundle", "audit_hermes_v019_loader_order", "project_hermes_v019_source_audit_receipt"} <= calls
    comparisons = [node for node in ast.walk(function) if isinstance(node, ast.Compare) and any(isinstance(operator, ast.Eq) for operator in node.ops)]
    assert any(any(isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == "loads" for item in (comparison.left, *comparison.comparators)) for comparison in comparisons)


def test_final_verifier_disables_ambient_pytest_plugins_before_sentinel_startup():
    verifier = (ROOT / "scripts/verify_spec_033_offline.py").read_text(encoding="utf-8")
    assert '"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"' in verifier
    assert "env=pytest_env" in verifier
    assert '"--noconftest"' in verifier


def test_spec033_offline_sentinel_blocks_network_and_upstream_imports():
    sentinel = ast.parse((ROOT / "scripts/spec033_offline_runtime_sentinel.py").read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(sentinel) if isinstance(node, ast.Import) for alias in node.names}
    assert "socket" in imported
    assignment = next(
        node for node in sentinel.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_BLOCKED_ROOTS" for target in node.targets)
    )
    assert isinstance(assignment.value, ast.Call)
    roots = ast.literal_eval(assignment.value.args[0])
    assert {"agent", "hermes_cli", "run_agent", "providers", "model_tools"} <= roots
