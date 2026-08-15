"""Unique final Spec033 offline verifier. Main runs this once after reviews."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/033-hermes-v019-pinned-source-loader-audit"
TARGETS = ("tests/test_hermes_v019_source_audit.py", "tests/test_spec_033_hermes_source_audit_docs.py")
SUCCESSOR_MUTABLE_SHARED_PATHS = (
    "README.md",
    "docs/roadmap.md",
    "docs/verification-matrix.md",
    "specs/README.md",
)
PREDECESSOR_AUTHORITY_ROOTS = {
    "spec032_predecessor_verifier": (
        "scripts/verify_spec_032_offline.py",
        "cc90af488f971df5db68eba27876643ba8224a1f07124956d09be2b5047e2890",
    ),
    "spec032_predecessor_manifest": (
        "specs/032-hermes-g2-offline-attempt-executor/contracts/predecessor-digests.json",
        "352b2e63991dfa54f57e8a427f9f8e9dab4ab7b90aab5cd0194df9b54da17f13",
    ),
    "spec032_reviewed_manifest": (
        "specs/032-hermes-g2-offline-attempt-executor/contracts/reviewed-artifact-manifest.json",
        "4a7f8bd25066443dbd05d812775b570ca2e8bab17a8ee7ec13885d690da3e60e",
    ),
}
STATIC_ONLY = (
    "scripts/acquire_spec_033_hermes_source.py", "scripts/validate_spec_033_hermes_source_audit.py",
    "scripts/spec033_offline_runtime_sentinel.py", "scripts/verify_spec_033_offline.py",
    "src/podcast_ingest_core/hermes_v019_source_audit.py",
)
REVIEWED_ARTIFACTS = (
    "README.md", "docs/roadmap.md", "docs/verification-matrix.md", "specs/README.md",
    "src/podcast_ingest_core/hermes_v019_source_audit.py", "scripts/acquire_spec_033_hermes_source.py",
    "scripts/validate_spec_033_hermes_source_audit.py", "scripts/spec033_offline_runtime_sentinel.py",
    "scripts/verify_spec_033_offline.py",
    "tests/test_hermes_v019_source_audit.py", "tests/test_spec_033_hermes_source_audit_docs.py",
    "specs/033-hermes-v019-pinned-source-loader-audit/proposal.md", "specs/033-hermes-v019-pinned-source-loader-audit/spec.md",
    "specs/033-hermes-v019-pinned-source-loader-audit/plan.md", "specs/033-hermes-v019-pinned-source-loader-audit/data-model.md",
    "specs/033-hermes-v019-pinned-source-loader-audit/tasks.md", "specs/033-hermes-v019-pinned-source-loader-audit/checklists/requirements.md",
    "specs/033-hermes-v019-pinned-source-loader-audit/checklists/safety.md", "specs/033-hermes-v019-pinned-source-loader-audit/contracts/source-bundle-manifest.json",
    "specs/033-hermes-v019-pinned-source-loader-audit/contracts/predecessor-digests.json", "specs/033-hermes-v019-pinned-source-loader-audit/contracts/loader-order-verdict.json",
    *tuple(f"specs/033-hermes-v019-pinned-source-loader-audit/upstream/NousResearch-hermes-agent-b7a05b6/{path}" for path in (
        "LICENSE", "pyproject.toml", "run_agent.py", "hermes_cli/main.py", "hermes_cli/oneshot.py", "hermes_cli/plugins.py", "hermes_cli/plugins_cmd.py", "hermes_cli/subcommands/plugins.py", "hermes_cli/runtime_provider.py", "hermes_cli/config.py", "hermes_cli/env_loader.py", "hermes_cli/hooks.py", "agent/agent_init.py", "agent/tool_executor.py", "model_tools.py", "providers/__init__.py", "providers/base.py",
    )),
)


def _result(status: str, failed_step: str | None = None) -> dict[str, object]:
    review_root = SPEC / "contracts/review-root.json"
    try:
        review_root_sha256 = hashlib.sha256(review_root.read_bytes()).hexdigest()
    except OSError:
        review_root_sha256 = "unavailable"
    result: dict[str, object] = {"spec_id": "033-hermes-v019-pinned-source-loader-audit", "status": status, "terminal_status": "BLOCKED_SOURCE_GRAPH", "runtime_status": "not_run", "live_actions_authorized": False, "review_root_sha256": review_root_sha256}
    if failed_step is not None:
        result["failed_step"] = failed_step
    return result


def _verified_reviewed_artifacts() -> bool:
    try:
        review_root = SPEC / "contracts/review-root.json"
        root = json.loads(review_root.read_text(encoding="utf-8"))
        manifest_path = SPEC / "contracts/reviewed-artifact-manifest.json"
        if root != {"schema_version": "spec033-detached-review-root-v2", "reviewed_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}:
            return False
        reviewed = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = reviewed.get("artifacts")
        if reviewed.get("schema_version") != "spec033-reviewed-artifact-manifest-v2" or type(artifacts) is not list or tuple(item.get("path") for item in artifacts if type(item) is dict) != REVIEWED_ARTIFACTS:
            return False
        return all(type(item) is dict and type(item.get("path")) is str and type(item.get("byte_length")) is int and type(item.get("sha256")) is str and (ROOT / item["path"]).is_file() and (ROOT / item["path"]).stat().st_size == item["byte_length"] and hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"] for item in artifacts)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return False


def _literal_assignment(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"missing literal assignment: {name}")


def _predecessor_boundary_valid() -> bool:
    try:
        manifest = json.loads((SPEC / "contracts/predecessor-digests.json").read_text(encoding="utf-8"))
        roots = manifest.get("authority_roots")
        if (
            manifest.get("schema_version") != "spec033-predecessor-boundary-v3"
            or manifest.get("chain_scope") != ["029", "030", "031", "032"]
            or type(roots) is not dict
            or tuple(roots) != tuple(PREDECESSOR_AUTHORITY_ROOTS)
            or manifest.get("successor_mutable_shared_paths") != list(SUCCESSOR_MUTABLE_SHARED_PATHS)
        ):
            return False
        for name, (path, digest) in PREDECESSOR_AUTHORITY_ROOTS.items():
            record = roots.get(name)
            if (
                type(record) is not dict
                or record.get("path") != path
                or record.get("sha256") != digest
                or hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest
            ):
                return False

        verifier_tree = ast.parse((ROOT / PREDECESSOR_AUTHORITY_ROOTS["spec032_predecessor_verifier"][0]).read_text(encoding="utf-8"))
        inventory = _literal_assignment(verifier_tree, "AUTHORITATIVE_PREDECESSOR_PATHS")
        if type(inventory) is not tuple or any(type(path) is not str for path in inventory) or len(inventory) != len(set(inventory)):
            return False
        if roots["spec032_predecessor_verifier"].get("inventory_symbol") != "AUTHORITATIVE_PREDECESSOR_PATHS":
            return False

        predecessor = json.loads((ROOT / PREDECESSOR_AUTHORITY_ROOTS["spec032_predecessor_manifest"][0]).read_text(encoding="utf-8"))
        scope = predecessor.get("scope")
        digests = predecessor.get("immutable_predecessor_files")
        if (
            roots["spec032_predecessor_manifest"].get("schema_version") != "spec032-predecessor-boundary-v2"
            or predecessor.get("schema_version") != "spec032-predecessor-boundary-v2"
            or type(scope) is not dict
            or set(scope) != {"specs", "deploy", "source", "scripts", "tests"}
            or any(type(paths) is not list or any(type(path) is not str for path in paths) for paths in scope.values())
            or type(digests) is not dict
        ):
            return False
        scoped = {path for paths in scope.values() for path in paths}
        if scoped != set(inventory) or set(digests) != set(inventory):
            return False
        if not all(
            type(digest) is str
            and len(digest) == 64
            and (ROOT / path).is_file()
            and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
            for path, digest in digests.items()
        ):
            return False

        reviewed = json.loads((ROOT / PREDECESSOR_AUTHORITY_ROOTS["spec032_reviewed_manifest"][0]).read_text(encoding="utf-8"))
        artifacts = reviewed.get("artifacts")
        if (
            roots["spec032_reviewed_manifest"].get("schema_version") != "spec032-reviewed-artifact-manifest-v2"
            or reviewed.get("schema_version") != "spec032-reviewed-artifact-manifest-v2"
            or reviewed.get("review_evidence_included") is not False
            or reviewed.get("live_authorization") is not False
            or type(artifacts) is not list
            or any(type(item) is not dict for item in artifacts)
            or len(artifacts) != len({item.get("path") for item in artifacts})
        ):
            return False
        reviewed_paths = {item.get("path") for item in artifacts}
        if not set(SUCCESSOR_MUTABLE_SHARED_PATHS) <= reviewed_paths:
            return False
        return all(
            type(item.get("path")) is str
            and type(item.get("byte_length")) is int
            and type(item.get("sha256")) is str
            and (
                item["path"] in SUCCESSOR_MUTABLE_SHARED_PATHS
                or (
                    (ROOT / item["path"]).is_file()
                    and (ROOT / item["path"]).stat().st_size == item["byte_length"]
                    and hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
                )
            )
            for item in artifacts
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError, TypeError, ValueError):
        return False


def _static_guard() -> bool:
    try:
        return _predecessor_boundary_valid() and _verified_reviewed_artifacts() and all(ast.parse((ROOT / path).read_text(encoding="utf-8")) for path in STATIC_ONLY)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError, TypeError):
        return False


def _verdict_matches_audit() -> bool:
    try:
        from podcast_ingest_core.hermes_v019_source_audit import audit_hermes_v019_loader_order, project_hermes_v019_source_audit_receipt, validate_hermes_v019_source_bundle
        bundle = validate_hermes_v019_source_bundle(); loader = audit_hermes_v019_loader_order(bundle)
        receipt = project_hermes_v019_source_audit_receipt(bundle, loader)
        if receipt != {"spec_id": "033-hermes-v019-pinned-source-loader-audit", "status": loader.status, "terminal_status": loader.status, "bundle_valid": bundle.bundle_valid, "project_version": bundle.project_version, "pinned_commit": "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6", "loader_path_verified": loader.loader_path_verified, "import_time_plugin_discovery_present": bool(loader.import_time_callers), "call_time_plugin_discovery_present": bool(loader.call_time_callers), "import_time_status": loader.import_time_status, "call_time_status": loader.call_time_status, "runtime_status": "not_run", "live_actions_authorized": False}:
            return False
        expected = {"spec_id": "033-hermes-v019-pinned-source-loader-audit", "source_bundle_valid": bundle.bundle_valid, "bounded_loader_edges_verified": loader.bounded_loader_edges_verified, "loader_path_verified": loader.loader_path_verified, "required_hook_registration_verified": loader.required_hook_registration_verified, "dynamic_execution_status": loader.dynamic_execution_status, "plugins_list_status": loader.plugins_list_status, "import_time_callers": list(loader.import_time_callers), "import_time_status": loader.import_time_status, "call_time_callers": list(loader.call_time_callers), "call_time_status": loader.call_time_status, "terminal_status": loader.status, "runtime_status": "not_run", "live_actions_authorized": False}
        return json.loads((SPEC / "contracts/loader-order-verdict.json").read_text(encoding="utf-8")) == expected
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return False


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args:
        print(json.dumps(_result("rejected"), sort_keys=True)); return 2
    if not _static_guard() or not _verdict_matches_audit():
        print(json.dumps(_result("failed", "static_guard"), sort_keys=True)); return 1
    pytest_env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    if subprocess.run((sys.executable, "-m", "pytest", "--noconftest", "-p", "scripts.spec033_offline_runtime_sentinel", *TARGETS, "-q"), cwd=ROOT, capture_output=True, text=True, env=pytest_env).returncode != 0:
        print(json.dumps(_result("failed", "focused_tests"), sort_keys=True)); return 1
    if not _verified_reviewed_artifacts() or not _verdict_matches_audit():
        print(json.dumps(_result("failed", "post_test_seal"), sort_keys=True)); return 1
    if subprocess.run((sys.executable, "-m", "compileall", "-q", *(str(ROOT / item) for item in STATIC_ONLY)), cwd=ROOT, capture_output=True, text=True).returncode != 0:
        print(json.dumps(_result("failed", "compile"), sort_keys=True)); return 1
    print(json.dumps(_result("SPEC033_PINNED_SOURCE_AUDIT_IMPLEMENTED"), sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
