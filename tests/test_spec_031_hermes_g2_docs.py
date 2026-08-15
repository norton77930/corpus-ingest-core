"""Static documentation, fixture, CLI, and runner boundary tests for Spec031."""
from __future__ import annotations
import ast,json
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]; SPEC=ROOT/"specs/031-hermes-g2-credentialless-activation-gate"; FIXTURE=ROOT/"deploy/hermes/spec031"
def test_blocked_fixture_manifest_never_claims_ready_loader_or_build():
    manifest=json.loads((SPEC/"contracts/credentialless-loader-source-manifest.json").read_text(encoding="utf-8")); docker=(FIXTURE/"Dockerfile").read_text(encoding="utf-8"); probe=(FIXTURE/"probe_contract.py").read_text(encoding="utf-8")
    assert docker.strip().splitlines()[1]=="FROM scratch" and "plugin.register(" not in probe
    assert manifest["fixture_build_authorized"] is False and manifest["official_loader_verified"] is False
    assert manifest["provider_materialization_status"]=="blocked_unknown" and manifest["terminal_status"]=="BLOCKED_CREDENTIAL_SEAM"
def test_offline_cli_receipt_is_exact_blocked_and_invalid_argv_is_not_echoed():
    script=ROOT/"scripts/validate_hermes_g2_activation.py"; bad=subprocess.run([sys.executable,str(script),"private-sentinel"],capture_output=True,text=True); good=subprocess.run([sys.executable,str(script),"offline-feasibility"],capture_output=True,text=True)
    assert bad.returncode==2 and "private-sentinel" not in bad.stdout+bad.stderr
    receipt=json.loads(good.stdout); assert good.returncode==0 and receipt["status"]=="BLOCKED_CREDENTIAL_SEAM" and receipt["attempt_count"]==0 and receipt["runtime_status"]=="not_run"
def test_runner_only_projects_complete_safe_receipt_and_verifier_never_imports_executor():
    runner=(ROOT/"scripts/run_spec_031_g2_once.py").read_text(encoding="utf-8"); verifier=(ROOT/"scripts/verify_spec_031_offline.py").read_text(encoding="utf-8")
    assert "build_g2_attempt_safe_receipt" in runner and "result.status" not in runner and "return 1" in runner
    tree=ast.parse(verifier); imports=[node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
    assert all("hermes_g2_activation_runtime" not in item for item in imports) and "run_g2_activation_once" not in verifier
    targets=next(node.value for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=="OFFLINE_PYTEST_TARGETS" for target in node.targets))
    assert "tests/test_hermes_g2_activation_runtime.py" not in ast.literal_eval(targets)
    assert "ast.parse" in verifier and "compileall" in verifier

def test_offline_package_does_not_claim_unimplemented_live_executor_seams():
    marker="Future live lease, driver, metadata inspection, and rollback execution are not implemented by this offline closure."
    for name in ("proposal.md","spec.md","plan.md","tasks.md"):
        assert marker in (SPEC/name).read_text(encoding="utf-8")


def test_spec031_top_level_pointers_are_consistent_and_next_package_is_032():
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    registry=(ROOT/"specs/README.md").read_text(encoding="utf-8")
    roadmap=(ROOT/"docs/roadmap.md").read_text(encoding="utf-8")
    marker="Spec 031 is **Offline Implemented**"
    for text in (readme,registry,roadmap):
        assert marker in text
        assert "BLOCKED_CREDENTIAL_SEAM" in text
        assert "runtime_status=not_run" in text
    assert "next unused feature package number is **032**" in roadmap
