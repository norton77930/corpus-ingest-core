"""Unique final Spec032 offline verifier. Do not run before required reviews.

The verifier has a deliberate two-part boundary: the five current Spec032 tests
run under a runtime sentinel; 026--031 are immutable predecessor bytes checked
only through the explicit digest manifest and are never executed here.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OFFLINE_PYTEST_TARGETS = (
    "tests/test_hermes_g2_activation_authority.py",
    "tests/test_hermes_g2_attempt_ledger.py",
    "tests/test_hermes_g2_activation_executor.py",
    "tests/test_hermes_g2_docker_commands.py",
    "tests/test_spec_032_hermes_g2_docs.py",
)
PREDECESSOR_STATIC_BOUNDARY = "specs/032-hermes-g2-offline-attempt-executor/contracts/predecessor-digests.json"
AUTHORITATIVE_PREDECESSOR_PATHS = ('deploy/hermes/Dockerfile',
 'deploy/hermes/README.md',
 'deploy/hermes/docker-compose.sidecar.yml',
 'deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json',
 'deploy/hermes/spec029/plugin/spec029_all_block.py',
 'deploy/hermes/spec029/spec029_mcp_deny_adapter.py',
 'deploy/hermes/spec031/Dockerfile',
 'deploy/hermes/spec031/contracts/fixture-contract.md',
 'deploy/hermes/spec031/probe_contract.py',
 'scripts/audit_hermes_g2_loader_source.py',
 'scripts/manage_hermes_integration.py',
 'scripts/manage_hermes_runtime_smoke_deployment.py',
 'scripts/run_hermes_blocked_runtime_smoke.py',
 'scripts/run_mcp_http_server.py',
 'scripts/run_spec_031_g2_once.py',
 'scripts/validate_hermes_blocked_runtime_contract.py',
 'scripts/validate_hermes_g1r_offline_remediation.py',
 'scripts/validate_hermes_g2_activation.py',
 'scripts/validate_hermes_integration.py',
 'scripts/validate_hermes_runtime_capability.py',
 'scripts/validate_hermes_skill_protocol.py',
 'scripts/verify_spec_029.py',
 'scripts/verify_spec_030.py',
 'scripts/verify_spec_031_offline.py',
 'specs/026-hermes-mcp-integration/checklists/requirements.md',
 'specs/026-hermes-mcp-integration/checklists/safety.md',
 'specs/026-hermes-mcp-integration/contracts/hermes-config-merge.md',
 'specs/026-hermes-mcp-integration/contracts/http-transport.md',
 'specs/026-hermes-mcp-integration/contracts/live-smoke-evidence.md',
 'specs/026-hermes-mcp-integration/contracts/skill-sync-manifest.md',
 'specs/026-hermes-mcp-integration/data-model.md',
 'specs/026-hermes-mcp-integration/plan.md',
 'specs/026-hermes-mcp-integration/quickstart.md',
 'specs/026-hermes-mcp-integration/research.md',
 'specs/026-hermes-mcp-integration/spec.md',
 'specs/026-hermes-mcp-integration/tasks.md',
 'specs/027-hermes-skill-routing-contracts/checklists/requirements.md',
 'specs/027-hermes-skill-routing-contracts/checklists/safety.md',
 'specs/027-hermes-skill-routing-contracts/contracts/safe-contract-evidence.md',
 'specs/027-hermes-skill-routing-contracts/contracts/skill-routing-and-protocol.md',
 'specs/027-hermes-skill-routing-contracts/data-model.md',
 'specs/027-hermes-skill-routing-contracts/plan.md',
 'specs/027-hermes-skill-routing-contracts/research.md',
 'specs/027-hermes-skill-routing-contracts/spec.md',
 'specs/027-hermes-skill-routing-contracts/tasks.md',
 'specs/028-hermes-runtime-skill-routing-observation/checklists/requirements.md',
 'specs/028-hermes-runtime-skill-routing-observation/checklists/safety.md',
 'specs/028-hermes-runtime-skill-routing-observation/contracts/capability-gate.md',
 'specs/028-hermes-runtime-skill-routing-observation/contracts/hermes-v2026.8.3-source-manifest.json',
 'specs/028-hermes-runtime-skill-routing-observation/contracts/safe-capability-evidence.md',
 'specs/028-hermes-runtime-skill-routing-observation/data-model.md',
 'specs/028-hermes-runtime-skill-routing-observation/plan.md',
 'specs/028-hermes-runtime-skill-routing-observation/research.md',
 'specs/028-hermes-runtime-skill-routing-observation/spec.md',
 'specs/028-hermes-runtime-skill-routing-observation/tasks.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/checklists/requirements.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/checklists/safety.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/deployment.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/g1-read-only-preflight-receipt.json',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/hermes-v0.19.0-runtime-source-manifest.json',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/contracts/safe-evidence.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/data-model.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/g1-read-only-preflight.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/plan.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/research.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/spec.md',
 'specs/029-hermes-blocked-tool-attempt-runtime-smoke/tasks.md',
 'specs/030-hermes-g1r-offline-remediation/checklists/requirements.md',
 'specs/030-hermes-g1r-offline-remediation/contracts/g1r-offline-remediation-contract.md',
 'specs/030-hermes-g1r-offline-remediation/contracts/g1r-offline-remediation-receipt.json',
 'specs/030-hermes-g1r-offline-remediation/data-model.md',
 'specs/030-hermes-g1r-offline-remediation/plan.md',
 'specs/030-hermes-g1r-offline-remediation/spec.md',
 'specs/030-hermes-g1r-offline-remediation/tasks.md',
 'specs/031-hermes-g2-credentialless-activation-gate/contracts/credentialless-loader-source-manifest.json',
 'specs/031-hermes-g2-credentialless-activation-gate/contracts/fixture-contract.md',
 'specs/031-hermes-g2-credentialless-activation-gate/plan.md',
 'specs/031-hermes-g2-credentialless-activation-gate/proposal.md',
 'specs/031-hermes-g2-credentialless-activation-gate/spec.md',
 'specs/031-hermes-g2-credentialless-activation-gate/tasks.md',
 'src/podcast_ingest_core/hermes_blocked_runtime_smoke.py',
 'src/podcast_ingest_core/hermes_g1r_offline_remediation.py',
 'src/podcast_ingest_core/hermes_g2_activation_observation.py',
 'src/podcast_ingest_core/hermes_g2_activation_runtime.py',
 'src/podcast_ingest_core/hermes_integration.py',
 'src/podcast_ingest_core/hermes_mcp_deny_interposer.py',
 'src/podcast_ingest_core/hermes_runtime_capability.py',
 'src/podcast_ingest_core/hermes_runtime_controller_plan.py',
 'src/podcast_ingest_core/hermes_runtime_deployment.py',
 'src/podcast_ingest_core/hermes_runtime_source_contract.py',
 'src/podcast_ingest_core/hermes_skill_protocol.py',
 'src/podcast_ingest_core/mcp_runtime.py',
 'src/podcast_ingest_core/mcp_server.py',
 'src/podcast_ingest_core/mcp_tools_corpus_workflows.py',
 'src/podcast_ingest_core/mcp_tools_read.py',
 'src/podcast_ingest_core/mcp_tools_side_effect.py',
 'src/podcast_ingest_core/mcp_tools_verified_report_queries.py',
 'tests/test_hermes_deployment_contract.py',
 'tests/test_hermes_g2_activation_observation.py',
 'tests/test_hermes_g2_activation_runtime.py',
 'tests/test_hermes_integration.py',
 'tests/test_hermes_live_smoke.py',
 'tests/test_hermes_runtime_capability.py',
 'tests/test_hermes_skill_protocol.py',
 'tests/test_mcp_http_transport.py',
 'tests/test_spec_027_hermes_skill_protocol_docs.py',
 'tests/test_spec_028_hermes_runtime_capability_docs.py',
 'tests/test_spec_029_offline.py',
 'tests/test_spec_030_g1r_offline_remediation.py',
 'tests/test_spec_031_hermes_g2_docs.py')
STATIC_ONLY = (
    "src/podcast_ingest_core/hermes_g2_docker_driver.py",
    "scripts/run_spec_032_g2_once.py",
    "scripts/spec032_offline_runtime_sentinel.py",
)
_FORBIDDEN_IMPORTS = {
    "subprocess",
    "docker",
    "podcast_ingest_core.hermes_g2_docker_driver",
    "scripts.run_spec_032_g2_once",
}
_FORBIDDEN_CALLS = {"system", "popen", "run", "Popen", "check_call", "check_output"}
_VERIFIER_FORBIDDEN_IMPORTS = {
    "docker",
    "podcast_ingest_core.hermes_g2_docker_driver",
    "scripts.run_spec_032_g2_once",
}


def _module_forbidden(name: object, forbidden: set[str]) -> bool:
    return type(name) is not str or any(
        name == blocked or name.startswith(f"{blocked}.") for blocked in forbidden
    )


def _result(status: str, failed_step: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "spec_id": "032-hermes-g2-offline-attempt-executor",
        "status": status,
        "terminal_status": "BLOCKED_CREDENTIAL_SEAM",
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }
    if failed_step is not None:
        result["failed_step"] = failed_step
    return result


def _forbidden_target_ast(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            _module_forbidden(alias.name, _FORBIDDEN_IMPORTS) for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.level != 0
            or _module_forbidden(node.module, _FORBIDDEN_IMPORTS)
            or any(
                _module_forbidden(f"{node.module}.{alias.name}", _FORBIDDEN_IMPORTS)
                for alias in node.names
            )
        ):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in _FORBIDDEN_CALLS:
                return True
    return False


def _forbidden_verifier_ast(tree: ast.AST) -> bool:
    """Reject verifier self-import/call edges except its isolated test launcher."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            _module_forbidden(alias.name, _VERIFIER_FORBIDDEN_IMPORTS) for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.level != 0
            or _module_forbidden(node.module, _VERIFIER_FORBIDDEN_IMPORTS)
            or any(
                _module_forbidden(f"{node.module}.{alias.name}", _VERIFIER_FORBIDDEN_IMPORTS)
                for alias in node.names
            )
        ):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"Popen", "check_call", "check_output", "system", "popen"}:
                return True
    return False


def _predecessor_boundary_valid() -> bool:
    """Check manifest bytes against this verifier's fixed predecessor inventory."""
    try:
        manifest = json.loads((ROOT / PREDECESSOR_STATIC_BOUNDARY).read_text(encoding="utf-8"))
        if manifest.get("schema_version") != "spec032-predecessor-boundary-v2":
            return False
        scope = manifest.get("scope")
        digests = manifest.get("immutable_predecessor_files")
        if type(scope) is not dict or type(digests) is not dict or set(scope) != {"specs", "deploy", "source", "scripts", "tests"}:
            return False
        if any(type(paths) is not list or any(type(path) is not str for path in paths) for paths in scope.values()):
            return False
        scoped = {path for paths in scope.values() for path in paths}
        expected = set(AUTHORITATIVE_PREDECESSOR_PATHS)
        if len(AUTHORITATIVE_PREDECESSOR_PATHS) != len(expected) or scoped != expected or set(digests) != expected:
            return False
        return all(
            type(digest) is str and len(digest) == 64 and (ROOT / path).is_file()
            and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
            for path, digest in digests.items()
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return False


def _static_guard() -> bool:
    try:
        if not _predecessor_boundary_valid():
            return False
        verifier_tree = ast.parse((ROOT / "scripts/verify_spec_032_offline.py").read_text(encoding="utf-8"))
        if _forbidden_verifier_ast(verifier_tree):
            return False
        verifier_imports = {
            alias.name for node in ast.walk(verifier_tree) if isinstance(node, ast.Import) for alias in node.names
        } | {
            node.module for node in ast.walk(verifier_tree) if isinstance(node, ast.ImportFrom) and node.module
        }
        if verifier_imports & {"docker", "podcast_ingest_core.hermes_g2_docker_driver", "scripts.run_spec_032_g2_once"}:
            return False
        for path in STATIC_ONLY:
            if not (ROOT / path).is_file():
                return False
            ast.parse((ROOT / path).read_text(encoding="utf-8"))
        for path in OFFLINE_PYTEST_TARGETS:
            target = ROOT / path
            if not target.is_file() or _forbidden_target_ast(ast.parse(target.read_text(encoding="utf-8"))):
                return False
    except (OSError, UnicodeDecodeError, SyntaxError):
        return False
    return True


def _run(command: tuple[str, ...]) -> bool:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True).returncode == 0


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args:
        print(json.dumps(_result("rejected"), sort_keys=True))
        return 2
    if not _static_guard():
        print(json.dumps(_result("failed", "static_guard"), sort_keys=True))
        return 1
    if not _run((sys.executable, "-m", "pytest", "-p", "scripts.spec032_offline_runtime_sentinel", *OFFLINE_PYTEST_TARGETS, "-q")):
        print(json.dumps(_result("failed", "focused_tests"), sort_keys=True))
        return 1
    compile_targets = tuple(str(ROOT / path) for path in STATIC_ONLY) + tuple(
        str(ROOT / path) for path in (
            "src/podcast_ingest_core/hermes_g2_activation_authority.py",
            "src/podcast_ingest_core/hermes_g2_attempt_ledger.py",
            "src/podcast_ingest_core/hermes_g2_activation_executor.py",
            "src/podcast_ingest_core/hermes_g2_docker_commands.py",
            "scripts/validate_hermes_g2_executor_offline.py",
        )
    )
    if not _run((sys.executable, "-m", "compileall", "-q", *compile_targets)):
        print(json.dumps(_result("failed", "compile"), sort_keys=True))
        return 1
    print(json.dumps(_result("SPEC032_OFFLINE_EXECUTOR_IMPLEMENTED"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
