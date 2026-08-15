"""Focused H4 repair contracts for Spec034; static/offline only."""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/034-hermes-v019-pinned-startup-source-graph"


def test_r1_final_verifier_requires_detached_h4_root_and_exact_ordered_authority(monkeypatch):
    from scripts import verify_spec_034_offline as verifier

    manifest = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    root = SPEC / "contracts/review-root.json"
    assert tuple(item["path"] for item in manifest["artifacts"]) == verifier.REVIEWED_ARTIFACT_PATHS
    # The external bootstrap, not the final verifier itself, is the trust
    # anchor.  This check is static only and does not invoke either entrypoint.
    assert verifier._seal_valid(hashlib.sha256(root.read_bytes()).hexdigest()) is True
    assert verifier._seal_valid("0" * 64) is False
    monkeypatch.setattr(verifier, "REVIEWED_ARTIFACT_PATHS", verifier.REVIEWED_ARTIFACT_PATHS[:-1])
    assert verifier._seal_valid(hashlib.sha256(root.read_bytes()).hexdigest()) is False


def test_r1_final_verifier_rejects_duplicate_extra_empty_and_reordered_authority(monkeypatch):
    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    exact = verifier.REVIEWED_ARTIFACT_PATHS
    for malformed in ((), exact + (exact[-1],), exact + ("README.md",), tuple(reversed(exact))):
        monkeypatch.setattr(verifier, "REVIEWED_ARTIFACT_PATHS", malformed)
        assert verifier._seal_valid(root_digest) is False
    monkeypatch.setattr(verifier, "REVIEWED_ARTIFACT_PATHS", exact)


def test_r2_recovery_only_removes_protocol_owned_partial_publication(monkeypatch, tmp_path):
    from scripts import acquire_spec_034_hermes_source as acquisition

    bundle = tmp_path / "bundle"
    manifest = tmp_path / "manifest.json"
    lock = tmp_path / ".lock"
    bundle.mkdir()
    (bundle / "known").write_text("partial", encoding="utf-8")
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", bundle)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", lock)
    lock.write_text(json.dumps(acquisition._publication_lock_payload("bundle_renamed")), encoding="utf-8")
    monkeypatch.setattr(acquisition, "_partial_bundle_is_authoritative", lambda: True)
    assert acquisition.recover_interrupted_publication() is True
    assert not bundle.exists() and not lock.exists()

    bundle.mkdir()
    (bundle / "unknown").write_text("keep", encoding="utf-8")
    lock.write_text(json.dumps(acquisition._publication_lock_payload("bundle_renamed")), encoding="utf-8")
    monkeypatch.setattr(acquisition, "_partial_bundle_is_authoritative", lambda: False)
    assert acquisition.recover_interrupted_publication() is False
    assert (bundle / "unknown").read_text(encoding="utf-8") == "keep"

    (bundle / "unknown").unlink()
    bundle.rmdir()
    lock.write_text("not-json", encoding="utf-8")
    assert acquisition.recover_interrupted_publication() is False
    lock.unlink()
    bundle.mkdir()
    (bundle / "known").write_text("partial", encoding="utf-8")
    lock.write_text(json.dumps(acquisition._publication_lock_payload("bundle_renamed")), encoding="utf-8")
    monkeypatch.setattr(acquisition.shutil, "rmtree", lambda _path: (_ for _ in ()).throw(OSError("cannot cleanup")))
    assert acquisition.recover_interrupted_publication() is False


def test_r3_claim_evidence_is_independent_and_owner_scoped():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    decision = graph.audit_spec034_startup_source_graph(graph.validate_spec034_source_bundle())
    details = {name: {"complete": complete, "verdict": verdict, "blocked_reasons": reasons} for name, complete, verdict, reasons in decision.claim_details}
    assert tuple(details) == (
        "startup_source_ordering", "credential_provider_boundary", "security_guidance_plugin",
    )
    assert all(set(item) == {"complete", "verdict", "blocked_reasons"} for item in details.values())
    source = b"def target():\n    required()\n    def nested():\n        forbidden()\n"
    assert graph._owned_calls(source, "target") == {"required"}
    assert graph._required_edge_reasons(b"from hermes_cli.config import *\n", "module", "hermes_cli/config.py")
    assert graph._required_edge_reasons(b"import importlib\nimportlib.import_module('hermes_cli.config')\n", "module", "hermes_cli/config.py")
    assert graph._required_edge_reasons(b"import sys\nsys.path.append('x')\n", "module", "hermes_cli/config.py")


def test_r4_canonical_filesystem_seams_reject_reparse_and_second_read_drift(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    path = tmp_path / "regular.txt"
    path.write_bytes(b"stable")
    assert graph._entry_is_regular_no_link(path)
    monkeypatch.setattr(graph, "_is_reparse_point", lambda _stat: True)
    assert not graph._entry_is_regular_no_link(path)
    monkeypatch.setattr(graph, "_is_reparse_point", lambda _stat: False)
    calls = {"count": 0}
    original = path.read_bytes
    def mutate_on_second_read():
        calls["count"] += 1
        if calls["count"] == 1:
            path.write_bytes(b"drifted")
        return original()
    monkeypatch.setattr(Path, "read_bytes", lambda candidate: mutate_on_second_read() if candidate == path else original())
    assert graph._read_regular_bytes(path) is None
    inventory = SPEC / "contracts/h1-source-inventory-proposal.json"
    manifest = SPEC / "contracts/source-bundle-manifest.json"
    review_root = SPEC / "contracts/review-root.json"
    monkeypatch.setattr(graph, "_is_reparse_point", lambda _stat: True)
    assert graph._read_regular_bytes(inventory) is None
    assert graph._read_regular_bytes(manifest) is None
    from scripts import verify_spec_034_offline as verifier
    monkeypatch.setattr(verifier, "_is_regular_no_link", lambda _path: False)
    assert verifier._read(review_root) is None


def test_r5_product_test_has_no_unsealed_test_helper_dependency():
    source = (ROOT / "tests/test_spec_034_verified_report_public_seam_regression.py").read_text(encoding="utf-8")
    helper = (ROOT / "tests/spec034_final_c6_support.py").read_text(encoding="utf-8")
    assert "test_latest_episode_verified_research_report_workflow_runner" not in source + helper
    assert "from test_" not in source + helper
    assert "from tests.spec034_final_c6_support import run_c6_public_workflow" in source
    assert "source_digest" in helper and "reused is True" in helper
    assert "external_data_verification.verify_external_data_boundary" in helper


def test_r6_predecessor_boundary_is_current_and_exact():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    assert graph._predecessor_boundary_matches() is True
    boundary = json.loads((SPEC / "contracts/predecessor-boundary.json").read_text(encoding="utf-8"))
    assert "spec033_review_root_sha256" in boundary
    assert "spec033_reviewed_artifact_manifest_sha256" in boundary
    assert "spec033_source_manifest_sha256" in boundary


def test_b1_bootstrap_preflight_validates_before_any_final_verifier_launch(monkeypatch):
    from scripts import run_spec_034_final_once as bootstrap

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    final_bytes = (ROOT / "scripts/verify_spec_034_offline.py").read_bytes()
    assert bootstrap.EXPECTED_FINAL_VERIFIER_SHA256 == hashlib.sha256(final_bytes).hexdigest()
    assert bootstrap.EXPECTED_FINAL_VERIFIER_LENGTH == len(final_bytes)
    assert "subprocess.run" not in inspect.getsource(bootstrap._preflight)
    assert bootstrap._preflight(root_digest) is True
    monkeypatch.setattr(bootstrap, "EXPECTED_FINAL_VERIFIER_SHA256", "0" * 64)
    assert bootstrap._preflight(root_digest) is False


def test_b1_bootstrap_preflight_rejects_bad_final_bytes_without_entrypoint_execution(monkeypatch, tmp_path):
    from scripts import run_spec_034_final_once as bootstrap

    final = tmp_path / "verify.py"
    final.write_text("raise AssertionError('must not execute')", encoding="utf-8")
    root = tmp_path / "review-root.json"
    root.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "FINAL_VERIFIER_PATH", final)
    monkeypatch.setattr(bootstrap, "REVIEW_ROOT_PATH", root)
    assert bootstrap._preflight(hashlib.sha256(root.read_bytes()).hexdigest()) is False


def test_b2_all_h2_startup_and_plugin_edges_are_exact_and_mutation_sensitive():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    assert tuple(edge.claim for edge in graph.REQUIRED_H2_EDGES).count("startup_source_ordering") == 8
    assert tuple(edge.claim for edge in graph.REQUIRED_H2_EDGES).count("security_guidance_plugin") == 6
    source = graph._validated_bytes()
    assert source is not None
    baseline = {name: (complete, reasons) for name, complete, _verdict, reasons in graph._claim_details(source)}
    assert baseline["startup_source_ordering"][0] is True
    assert baseline["security_guidance_plugin"][0] is True
    for edge in graph.REQUIRED_H2_EDGES:
        changed = dict(source)
        changed[edge.source] = changed[edge.source].replace(edge.required_bytes, edge.replacement_bytes, 1)
        assert changed[edge.source] != source[edge.source], edge.edge_id
        result = {name: (complete, reasons) for name, complete, _verdict, reasons in graph._claim_details(changed)}
        assert result[edge.claim][0] is False, edge.edge_id
        assert any(edge.edge_id in reason for reason in result[edge.claim][1]), edge.edge_id


def test_b3_canonical_ancestor_guard_rejects_reparse_component(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    trusted = tmp_path / "trusted"
    child = trusted / "nested"
    child.mkdir(parents=True)
    leaf = child / "evidence.json"
    leaf.write_text("{}", encoding="utf-8")
    child_inode = child.lstat().st_ino
    monkeypatch.setattr(graph, "_is_reparse_point", lambda info: info.st_ino == child_inode)
    assert graph._canonical_path_under(leaf, trusted) is False


def test_b4_lock_payload_is_nonabsolute_nonce_bound_and_recovers_each_phase(monkeypatch, tmp_path):
    from scripts import acquire_spec_034_hermes_source as acquisition

    bundle = tmp_path / "bundle"
    manifest = tmp_path / "manifest.json"
    lock = tmp_path / ".lock"
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", bundle)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", lock)
    nonce = "a" * 32
    payload = acquisition._publication_lock_payload("staging_created", f".bundle.stage-{nonce}", nonce)
    assert set(payload) == {"schema_version", "phase", "staging_basename", "protocol_nonce"}
    assert not any(Path(value).is_absolute() for value in payload.values())
    staging = tmp_path / payload["staging_basename"]
    staging.mkdir()
    lock.write_text(json.dumps(payload), encoding="utf-8")
    assert acquisition.recover_interrupted_publication() is True
    assert not staging.exists() and not lock.exists()

    nonce = "a" * 32
    for phase in ("bundle_renamed", "manifest_written"):
        bundle.mkdir()
        for path in acquisition.ALLOWLIST:
            target = bundle / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"known")
        payload = acquisition._publication_lock_payload(phase, f".bundle.stage-{nonce}", nonce)
        lock.write_text(json.dumps(payload), encoding="utf-8")
        if phase == "bundle_renamed":
            monkeypatch.setattr(acquisition, "_partial_bundle_is_authoritative", lambda: True)
        else:
            manifest.write_text("{}", encoding="utf-8")
            monkeypatch.setattr(acquisition, "_manifest_is_complete", lambda *_args: True)
        assert acquisition.recover_interrupted_publication() is True
        if phase == "bundle_renamed":
            assert not bundle.exists() and not lock.exists()
        else:
            assert bundle.exists() and not lock.exists()
        manifest.unlink(missing_ok=True)
        if bundle.exists():
            import shutil
            shutil.rmtree(bundle)


def test_b5_reviewed_configs_and_independent_manifest_digest_sensitivity(monkeypatch):
    manifest_path = SPEC / "contracts/reviewed-artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = tuple(item["path"] for item in manifest["artifacts"])
    configs = (
        "config/industry_chain_mappings.yaml",
        "config/external_data_boundary.yaml",
        "config/gooaye_lens.yaml",
    )
    assert all(path in paths for path in configs)
    records = [{"path": item["path"], "sha256": item["sha256"], "byte_length": item["byte_length"]} for item in manifest["artifacts"]]
    canonical = json.dumps(records, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    changed = [dict(item) for item in records]
    index = paths.index(configs[0])
    changed[index]["sha256"] = hashlib.sha256(b"independent config mutation").hexdigest()
    assert hashlib.sha256(canonical).hexdigest() != hashlib.sha256(json.dumps(changed, ensure_ascii=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    original_read = verifier._read
    config_path = ROOT / configs[0]
    def changed_config_bytes(path):
        data = original_read(path)
        return data + b"\n# drift" if path == config_path else data
    monkeypatch.setattr(verifier, "_read", changed_config_bytes)
    assert verifier._seal_valid(root_digest) is False


def test_b6_current_docs_state_startup_plugin_closed_and_credential_overall_blocked():
    current = (
        ROOT / "README.md", SPEC / "proposal.md", SPEC / "spec.md", SPEC / "plan.md", SPEC / "tasks.md",
        SPEC / "checklists/requirements.md", SPEC / "checklists/safety.md", ROOT / "docs/roadmap.md",
        ROOT / "docs/verification-matrix.md", ROOT / "specs/README.md",
    )
    for path in current:
        text = path.read_text(encoding="utf-8")
        assert "startup/plugin closed; credential_provider BLOCKED; overall BLOCKED" in text, path
        assert "three explicitly claim-scoped graphs only" not in text, path


def test_b7_final_authority_is_exact_manifest_tuple_and_static_launcher_contract():
    from scripts import verify_spec_034_offline as verifier

    manifest = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    paths = tuple(item["path"] for item in manifest["artifacts"])
    assert paths == verifier.REVIEWED_ARTIFACT_PATHS
    assert "scripts/run_spec_034_final_once.py" in paths
    assert "config/industry_chain_mappings.yaml" in paths
    assert "config/external_data_boundary.yaml" in paths
    assert "config/gooaye_lens.yaml" in paths
    command_contract = SPEC / "contracts/final-invocation.md"
    text = command_contract.read_text(encoding="utf-8")
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in Path(verifier.__file__).read_text(encoding="utf-8")
    assert "--noconftest" in Path(verifier.__file__).read_text(encoding="utf-8")
    assert "--approved-bootstrap-sha256" in text and "--review-root-sha256" in text
    assert 'sys.argv[1] != "--approved-bootstrap-sha256"' in text
    assert 'sys.argv[3] != "--bootstrap-length"' in text and 'sys.argv[5] != "--review-root-sha256"' in text
    assert "root = Path.cwd().absolute()" in text and "root_info = current.lstat()" in text
    assert "st_file_attributes" in text and "regular_under(bootstrap, root)" in text


def test_b3_bootstrap_and_final_verifier_lstat_the_trusted_root_component():
    from scripts import run_spec_034_final_once as bootstrap
    from scripts import verify_spec_034_offline as verifier

    assert "root_info = current.lstat()" in Path(bootstrap.__file__).read_text(encoding="utf-8")
    assert "root_info = root.lstat()" in Path(verifier.__file__).read_text(encoding="utf-8")


def test_b4_consumer_blocks_while_publication_lock_exists(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    lock = tmp_path / ".spec034-source-publication.lock"
    lock.write_text("pending", encoding="utf-8")
    monkeypatch.setattr(graph, "PUBLICATION_LOCK_PATH", lock)
    decision = graph.validate_spec034_source_bundle()
    assert decision.status == "BLOCKED_SOURCE_GRAPH"
    assert decision.reason == "publication_recovery_pending"


# Task #77: focused F1--F7 contracts.  These exercise only byte/preflight
# harnesses and static source predicates, never any Spec034 entrypoint.
def test_task77_f1_isolated_launcher_executes_verified_inert_bytes_only(tmp_path):
    from scripts import spec034_trust_launcher as launcher

    payload = b"result = 40 + 2\n"
    namespace = launcher.execute_verified_bytes(payload, "approved/inert.py")
    assert namespace["result"] == 42
    assert "__builtins__" in namespace
    target = tmp_path / "trusted.py"
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    verified = launcher.read_verified_regular_bytes(target, tmp_path, digest, len(payload))
    target.write_bytes(b"raise RuntimeError('pathname was reread')\n")
    assert verified == payload
    assert launcher.execute_verified_bytes(verified, "approved/trusted.py")["result"] == 42
    assert launcher.read_verified_regular_bytes(target, tmp_path, digest, len(payload)) is None

    contract = (SPEC / "contracts/final-invocation.md").read_text(encoding="utf-8")
    assert "python -I -S -c" in contract
    assert "compile(bootstrap_bytes" in contract
    assert "runpy.run_path" not in contract and "assert " not in contract
    for relative in ("scripts/run_spec_034_final_once.py", "scripts/verify_spec_034_offline.py"):
        assert "assert " not in (ROOT / relative).read_text(encoding="utf-8")
    bootstrap_source = (ROOT / "scripts/run_spec_034_final_once.py").read_text(encoding="utf-8")
    assert "str(FINAL_VERIFIER_PATH)" not in bootstrap_source
    assert "input=final_bytes" in bootstrap_source


def test_task77_f1_isolated_python_ignores_sitecustomize_and_pythonpath(tmp_path):
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text("raise RuntimeError('ambient sitecustomize loaded')", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "PYTHONOPTIMIZE": "1"}
    completed = subprocess.run(
        (sys.executable, "-I", "-S", "-c", "import sys; print('isolated')"),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == "isolated"
    assert "sitecustomize" not in completed.stderr


def test_task77_f2_journal_atomicity_and_adjacent_recovery_windows(monkeypatch, tmp_path):
    from scripts import acquire_spec_034_hermes_source as acquisition

    bundle = tmp_path / "bundle"
    manifest = tmp_path / "manifest.json"
    journal = tmp_path / ".lock"
    monkeypatch.setattr(acquisition, "BUNDLE_ROOT", bundle)
    monkeypatch.setattr(acquisition, "MANIFEST_PATH", manifest)
    monkeypatch.setattr(acquisition, "PUBLICATION_LOCK_PATH", journal)
    nonce = "a" * 32
    acquisition._write_journal("staging_created", f".bundle.stage-{nonce}", nonce, exclusive=True)
    previous = journal.read_bytes()
    monkeypatch.setattr(acquisition.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("replace failed")))
    try:
        acquisition._write_journal("bundle_renamed", f".bundle.stage-{nonce}", nonce)
    except OSError:
        pass
    else:
        raise AssertionError("atomic journal replacement must surface failure")
    assert journal.read_bytes() == previous

    # A crash after exclusive journal creation but before staging mkdir is an
    # owned adjacent state, not a permanent consumer block.
    assert acquisition.recover_interrupted_publication() is True
    assert not journal.exists()

    # Partial staging, rename-before-marker, malformed manifest after rename,
    # and completed publication with an old marker are adjacent owned states.
    staging = tmp_path / f".bundle.stage-{nonce}"
    staging.mkdir()
    (staging / "agent").mkdir()
    (staging / "agent" / "agent_init.py").write_bytes(b"partial")
    acquisition._write_journal("staging_created", staging.name, nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not staging.exists() and not journal.exists()

    bundle.mkdir()
    for relative in acquisition.ALLOWLIST:
        target = bundle / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"known")
    monkeypatch.setattr(acquisition, "_partial_bundle_is_authoritative", lambda: True)
    acquisition._write_journal("staging_created", staging.name, nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not bundle.exists() and not journal.exists()

    bundle.mkdir()
    for relative in acquisition.ALLOWLIST:
        target = bundle / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"known")
    manifest.write_text("{", encoding="utf-8")
    monkeypatch.setattr(acquisition, "_manifest_is_complete", lambda *_args: False)
    acquisition._write_journal("bundle_renamed", staging.name, nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not bundle.exists() and not manifest.exists() and not journal.exists()

    bundle.mkdir()
    for relative in acquisition.ALLOWLIST:
        target = bundle / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"known")
    manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(acquisition, "_manifest_is_complete", lambda *_args: True)
    acquisition._write_journal("staging_created", staging.name, nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert bundle.exists() and manifest.exists() and not journal.exists()


def test_task77_f3_run_agent_owner_order_is_ast_bound_and_mutation_sensitive():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = (SPEC / "upstream/NousResearch-hermes-agent-b7a05b6/run_agent.py").read_bytes()
    assert graph._run_agent_dotenv_before_model_tools(source) is True
    moved = source.replace(
        b"from hermes_cli.env_loader import load_hermes_dotenv",
        b"from model_tools import (\n    get_tool_definitions,\n)\nfrom hermes_cli.env_loader import load_hermes_dotenv",
        1,
    )
    assert graph._run_agent_dotenv_before_model_tools(moved) is False


def test_task77_f4_bundled_plugin_identity_chain_is_complete_and_mutation_sensitive():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = graph._validated_bytes()
    assert source is not None
    assert graph._bundled_security_guidance_identity_proven(source) is True
    changed = dict(source)
    changed["hermes_cli/plugins.py"] = changed["hermes_cli/plugins.py"].replace(
        b'init_file = plugin_dir / "__init__.py"', b'init_file = plugin_dir / "main.py"'
    )
    assert graph._bundled_security_guidance_identity_proven(changed) is False


def test_task77_f5_all_current_authorities_have_only_exact_blocked_terminal():
    current = (
        ROOT / "README.md", ROOT / "docs/roadmap.md", ROOT / "docs/verification-matrix.md", ROOT / "specs/README.md",
        SPEC / "proposal.md", SPEC / "spec.md", SPEC / "plan.md", SPEC / "tasks.md",
        SPEC / "checklists/requirements.md", SPEC / "checklists/safety.md", SPEC / "contracts/final-invocation.md",
    )
    terminal = "startup/plugin closed; credential_provider BLOCKED; overall BLOCKED"
    for path in current:
        text = path.read_text(encoding="utf-8")
        assert terminal in text, path
        assert "Terminal is `SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED`" not in text, path


def test_task77_f6_product_regression_contains_independent_canonical_digest_contract():
    source = (ROOT / "tests/spec034_final_c6_support.py").read_text(encoding="utf-8")
    assert "_spec034_independent_source_digest" in source
    assert "from podcast_ingest_core.verified_research_report import _source_digest" not in source


def test_task77_f7_detached_root_externally_records_all_trust_identities():
    root = json.loads((SPEC / "contracts/review-root.json").read_text(encoding="utf-8"))
    assert root["schema_version"] == "spec034-detached-review-root-v8"
    assert set(root) == {
        "schema_version", "reviewed_manifest_sha256", "launcher_contract_sha256", "capability_manifest_sha256", "capability_distributions", "bootstrap", "final_verifier", "isolated_pytest_runner",
    }
    assert tuple(root["capability_distributions"]) == ("pytest", "pluggy", "iniconfig", "packaging", "pygments", "colorama", "requests", "urllib3", "certifi", "charset-normalizer", "idna", "pyyaml")
    assert set(root["bootstrap"]) == {"sha256", "byte_length"}
    assert set(root["final_verifier"]) == {"sha256", "byte_length"}
    assert set(root["isolated_pytest_runner"]) == {"sha256", "byte_length"}


# Task #78 G1: exercise the actual local publisher/consumer boundary using
# canonical fixture bytes.  No completion helper is monkeypatched.
def _task78_local_publication_workspace(monkeypatch, tmp_path):
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph
    from scripts import acquire_spec_034_hermes_source as acquisition

    spec = tmp_path
    contracts = spec / "c"
    contracts.mkdir()
    actual_spec = SPEC
    for name in ("h1-source-inventory-proposal.json", "predecessor-boundary.json"):
        (contracts / name).write_bytes((actual_spec / "contracts" / name).read_bytes())
    for name in ("review-root.json", "reviewed-artifact-manifest.json", "source-bundle-manifest.json"):
        destination = tmp_path.parent / "033-hermes-v019-pinned-source-loader-audit/contracts" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((actual_spec.parent / "033-hermes-v019-pinned-source-loader-audit/contracts" / name).read_bytes())

    bundle_root = spec / "b"
    manifest_path = contracts / "source-bundle-manifest.json"
    lock_path = contracts / ".spec034-source-publication.lock"
    for module in (graph, acquisition):
        monkeypatch.setattr(module, "BUNDLE_ROOT", bundle_root)
        monkeypatch.setattr(module, "MANIFEST_PATH" if module is acquisition else "SOURCE_MANIFEST_PATH", manifest_path)
        monkeypatch.setattr(module, "PUBLICATION_LOCK_PATH", lock_path)
    monkeypatch.setattr(graph, "SPEC_ROOT", spec)
    monkeypatch.setattr(graph, "H1_INVENTORY_PATH", contracts / "h1-source-inventory-proposal.json")
    monkeypatch.setattr(graph, "PREDECESSOR_BOUNDARY_PATH", contracts / "predecessor-boundary.json")
    source_root = actual_spec / "upstream/NousResearch-hermes-agent-b7a05b6"
    staged = [(path, (source_root / path).read_bytes()) for path in acquisition.ALLOWLIST]
    records = [
        {"path": path, "git_blob_sha": blob, "sha256": digest, "byte_length": length}
        for path, blob, digest, length in acquisition.AUTHORITATIVE_PATH_BLOBS
    ]
    return acquisition, graph, {
        "schema_version": "spec034-pinned-source-bundle-v1",
        "repository": acquisition.REPOSITORY,
        "pinned_commit": acquisition.COMMIT,
        "tree_sha": acquisition.TREE_SHA,
        "h1_inventory_sha256": acquisition.H1_INVENTORY_SHA256,
        "files": records,
        "_staged": staged,
    }


def test_task78_g1_local_publication_and_owned_recovery_complete_manifest(monkeypatch, tmp_path):
    acquisition, graph, bundle = _task78_local_publication_workspace(monkeypatch, tmp_path)

    acquisition._write(bundle)
    assert graph.validate_spec034_source_bundle().bundle_valid is True

    nonce = "a" * 32
    acquisition._write_journal("validated", f".{acquisition.BUNDLE_ROOT.name}.stage-{nonce}", nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not acquisition.PUBLICATION_LOCK_PATH.exists()
    assert graph.validate_spec034_source_bundle().bundle_valid is True


def test_task78_g1_partial_owned_publication_rolls_back_but_unknown_lock_stays_blocked(monkeypatch, tmp_path):
    acquisition, graph, bundle = _task78_local_publication_workspace(monkeypatch, tmp_path)

    acquisition._write(bundle)
    acquisition.MANIFEST_PATH.write_text("{", encoding="utf-8")
    nonce = "b" * 32
    acquisition._write_journal("manifest_written", f".{acquisition.BUNDLE_ROOT.name}.stage-{nonce}", nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not acquisition.BUNDLE_ROOT.exists()
    assert not acquisition.MANIFEST_PATH.exists()
    assert not acquisition.PUBLICATION_LOCK_PATH.exists()

    acquisition.PUBLICATION_LOCK_PATH.write_text("unknown", encoding="utf-8")
    blocked = graph.validate_spec034_source_bundle()
    assert blocked.status == "BLOCKED_SOURCE_GRAPH"
    assert blocked.reason == "publication_recovery_pending"


def test_task78_g2_nested_call_never_counts_as_module_startup():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    statement = ast.parse("def nested():\n    load_hermes_dotenv()\n").body[0]
    assert graph._static_statement_calls_name(statement, "load_hermes_dotenv") is False
    source = (SPEC / "upstream/NousResearch-hermes-agent-b7a05b6/run_agent.py").read_bytes()
    top_level_call = b"_loaded_env_paths = load_hermes_dotenv(hermes_home=_hermes_home, project_env=_project_env)"
    assert top_level_call in source
    changed = source.replace(top_level_call, b"def retained_nested_call():\n    load_hermes_dotenv(hermes_home=_hermes_home, project_env=_project_env)", 1)
    assert graph._run_agent_dotenv_before_model_tools(changed) is False


def test_task78_g3_bundled_plugin_flow_requires_same_manifest_identity():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = graph._validated_bytes()
    assert source is not None
    assert graph._bundled_security_guidance_identity_proven(source) is True
    loader = source["hermes_cli/plugins.py"]
    for old, new in (
        (b"self._load_directory_module(manifest)", b"self._load_directory_module(other_manifest)"),
        (b"plugin_dir = Path(manifest.path)", b"plugin_dir = Path(global_plugin_dir)"),
        (b'        init_file = plugin_dir / "__init__.py"\n        if not init_file.exists():', b'        init_file = plugin_dir / "main.py"\n        if not init_file.exists():'),
        (b"ctx = PluginContext(manifest, self)", b"ctx = PluginContext(other_manifest, self)"),
    ):
        changed = dict(source)
        changed["hermes_cli/plugins.py"] = loader.replace(old, new, 1)
        assert changed["hermes_cli/plugins.py"] != loader
        assert graph._bundled_security_guidance_identity_proven(changed) is False


def _task78_pytest_capability_receipt():
    names = ("pytest", "pluggy", "iniconfig", "packaging", "pygments", "colorama")
    distributions = []
    roots = set()
    for name in names:
        distribution = importlib.metadata.distribution(name)
        record_relative = next(str(item) for item in distribution.files or () if str(item).endswith("/RECORD"))
        record = distribution.locate_file(record_relative)
        root = record.parent.parent
        roots.add(str(root))
        data = record.read_bytes()
        files = []
        for relative in distribution.files or ():
            candidate = distribution.locate_file(relative)
            if candidate.is_file():
                contents = candidate.read_bytes()
                files.append({"path": str(relative).replace("\\", "/"), "sha256": hashlib.sha256(contents).hexdigest(), "byte_length": len(contents)})
        distributions.append({"name": name, "version": distribution.version, "record_path": record_relative, "record_sha256": hashlib.sha256(data).hexdigest(), "record_length": len(data), "files": files})
    assert len(roots) == 1
    return {"site_root": roots.pop(), "distributions": distributions}


def test_task78_g4_isolated_child_installs_verified_sentinel_before_pytest(monkeypatch, tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner

    inert = tmp_path / "inert_target.py"
    inert.write_text("def test_inert():\n    assert 2 + 2 == 4\n", encoding="utf-8")
    # Task #79 accepts only protocol-owned exact snapshots. Build an inert
    # project snapshot and a separately verified capability snapshot.
    from scripts import verify_spec_034_offline as verifier

    project = tmp_path / "project"
    (project / "src" / "podcast_ingest_core").mkdir(parents=True)
    (project / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
    (project / "inert_target.py").write_bytes(inert.read_bytes())
    target = "inert_target.py"
    sentinel = (ROOT / "scripts/spec034_offline_runtime_sentinel.py").read_bytes()
    entries = []
    for path in ("pyproject.toml", target):
        data = (project / path).read_bytes()
        entries.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "byte_length": len(data)})
    init = project / "src" / "podcast_ingest_core" / "__init__.py"
    init.write_bytes(b"")
    entries.append({"path": "src/podcast_ingest_core/__init__.py", "sha256": hashlib.sha256(b"").hexdigest(), "byte_length": 0})
    capability_manifest = json.loads((SPEC / "contracts/python-test-capability-manifest.json").read_text(encoding="utf-8"))
    capability, capability_records = verifier._create_capability_snapshot(capability_manifest)
    try:
        payload = {
            "project_snapshot": str(project), "project_records": entries, "targets": [target], "expected_node_ids": ["inert_target.py::test_inert"], "cwd": str(project),
            "capability_snapshot": str(capability), "capability_records": list(capability_records),
            "approved_top_levels": sorted({top for values in verifier.CAPABILITY_TOP_LEVELS.values() for top in values}),
            "sentinel": {"module": "spec034_sealed_sentinel", "bytes_b64": __import__("base64").b64encode(sentinel).decode("ascii"), "sha256": hashlib.sha256(sentinel).hexdigest(), "byte_length": len(sentinel)},
        }
        source = (ROOT / "scripts/spec034_isolated_pytest_runner.py").read_text(encoding="utf-8")
        final = (ROOT / "scripts/verify_spec_034_offline.py").read_text(encoding="utf-8")
        assert '"-I", "-S", "-c", _CHILD_EXEC_RUNNER' in source
        assert "install(root)" in source and "import pytest" in source
        assert source.index("install(root)") < source.index("import pytest")
        assert "-p", "scripts.spec034_offline_runtime_sentinel" not in source
        assert '"-I", "-S", "-c", _ISOLATED_CHILD_EXEC_RUNNER' in final
        assert final.index("_sealed_pytest_command") > final.index("_isolated_pytest_payload")
        marker = tmp_path / "sitecustomize.py"
        marker.write_text("raise RuntimeError('sitecustomize must not run')", encoding="utf-8")
        monkeypatch.setenv("PYTHONPATH", str(tmp_path))
        monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only --ignore=inert_target.py -k none")
        monkeypatch.setenv("PYTEST_PLUGINS", "unapproved")
        monkeypatch.setenv("PYTEST_DEBUG", "1")
        monkeypatch.setenv("PYTEST_THEME", "dark")
        assert runner.run_isolated(payload) == 0
    finally:
        assert verifier._remove_snapshot(capability) is True


def test_task78_g5_fresh_manifest_seals_isolated_runner_and_current_authorities():
    from scripts import verify_spec_034_offline as verifier

    manifest = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    paths = tuple(item["path"] for item in manifest["artifacts"])
    assert "scripts/spec034_isolated_pytest_runner.py" in paths
    assert "specs/034-hermes-v019-pinned-startup-source-graph/contracts/python-test-capability-manifest.json" in paths
    assert paths == verifier.REVIEWED_ARTIFACT_PATHS


# Task #79 v5 review repairs: all seams below are non-final and use inert bytes.
def test_task79_h1_project_snapshot_preserves_preseal_verified_bytes_after_workspace_restore(monkeypatch, tmp_path):
    from scripts import verify_spec_034_offline as verifier

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    artifact = workspace / "tests" / "inert.py"
    artifact.parent.mkdir()
    original = b"VALUE = 'reviewed'\n"
    artifact.write_bytes(original)
    records = ({"path": "tests/inert.py", "sha256": hashlib.sha256(original).hexdigest(), "byte_length": len(original)},)
    monkeypatch.setattr(verifier, "ROOT", workspace)

    snapshot = verifier._create_project_snapshot(records)
    try:
        artifact.write_bytes(b"VALUE = 'mutated after seal'\n")
        artifact.write_bytes(original)  # replace -> execute snapshot -> restore
        verified = (snapshot / "tests/inert.py").read_bytes()
        namespace: dict[str, object] = {}
        exec(compile(verified, "snapshot/tests/inert.py", "exec"), namespace, namespace)
        assert namespace["VALUE"] == "reviewed"
        assert verifier._snapshot_exact(snapshot, records) is True
    finally:
        verifier._remove_snapshot(snapshot)


def test_task79_h2_h4_capability_manifest_is_literal_complete_and_snapshot_bound(monkeypatch):
    from scripts import verify_spec_034_offline as verifier

    manifest = json.loads((SPEC / "contracts/python-test-capability-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == verifier.CAPABILITY_SCHEMA
    assert tuple(item["canonical_name"] for item in manifest["distributions"]) == verifier.CAPABILITY_DISTRIBUTIONS
    assert all(item["files"] and item["record"]["path"] in {file["path"] for file in item["files"]} for item in manifest["distributions"])
    assert verifier._capability_manifest_valid(manifest) is True
    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    assert verifier._manifest_authority(root_digest) is not None
    monkeypatch.setattr(verifier, "EXPECTED_CAPABILITY_MANIFEST_SHA256", "0" * 64)
    assert verifier._manifest_authority(root_digest) is None


def test_task79_h3_runner_requires_capability_snapshot_and_rejects_project_shadow(monkeypatch, tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner

    project = tmp_path / "project"
    capability = tmp_path / "capability"
    project.mkdir()
    capability.mkdir()
    (project / "pyproject.toml").write_bytes(b"[tool.pytest.ini_options]\n")
    (project / "pytest.py").write_bytes(b"raise RuntimeError('shadow')\n")
    records = ({"path": "pyproject.toml", "sha256": hashlib.sha256((project / "pyproject.toml").read_bytes()).hexdigest(), "byte_length": (project / "pyproject.toml").stat().st_size}, {"path": "pytest.py", "sha256": hashlib.sha256((project / "pytest.py").read_bytes()).hexdigest(), "byte_length": (project / "pytest.py").stat().st_size})
    monkeypatch.setattr(runner, "APPROVED_TOP_LEVEL_CAPABILITY_NAMES", frozenset({"pytest"}))
    assert runner._project_snapshot_valid(project, records) is False


def test_task79_h5_plugin_identity_requires_loaded_same_module_and_exec_module():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = graph._validated_bytes()
    assert source is not None
    loader = source["hermes_cli/plugins.py"]
    for old, new in (
        (b"spec.loader.exec_module(module)", b"pass  # execution removed"),
        (b"module = self._load_directory_module(manifest)", b"module = alternate_module"),
        (b"return module", b"return other_module"),
    ):
        changed = dict(source)
        changed["hermes_cli/plugins.py"] = loader.replace(old, new, 1)
        assert changed["hermes_cli/plugins.py"] != loader
        assert graph._bundled_security_guidance_identity_proven(changed) is False


# Task #80 J1 RED: the final child must receive every canonical authority
# class, rather than just mutable reviewed artifacts.
def test_task80_j1_execution_records_are_typed_complete_and_snapshot_exact(tmp_path):
    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    authority = verifier._manifest_authority(root_digest)
    assert authority is not None
    records, capability = authority.records, authority.capability
    execution_records = verifier._execution_records(authority)

    categories = tuple(record.category for record in execution_records)
    assert categories.count("reviewed") == len(records)
    assert categories.count("detached") == 2
    assert categories.count("upstream") == 20
    assert categories.count("predecessor") == 3
    paths = tuple(record.path for record in execution_records)
    assert len(paths) == len(set(paths))
    verifier_source = Path(verifier.__file__).read_text(encoding="utf-8")
    assert "from podcast_ingest_core import hermes_v019_startup_source_graph" not in verifier_source
    assert len(verifier.H2_PATH_BLOB_SHA_LENGTH) == 20
    assert all(len(record) == 4 for record in verifier.H2_PATH_BLOB_SHA_LENGTH)
    snapshot = verifier._create_execution_snapshot(execution_records)
    try:
        assert verifier._execution_snapshot_exact(snapshot, execution_records) is True
        (snapshot / "unexpected.txt").write_bytes(b"extra")
        assert verifier._execution_snapshot_exact(snapshot, execution_records) is False
    finally:
        assert verifier._remove_snapshot(snapshot) is True


# Task #80 J2 RED: the final child gets only a sentinel-safe acceptance suite.
def test_task80_j2_final_targets_are_dedicated_and_ast_safe():
    from scripts import verify_spec_034_offline as verifier

    assert verifier.TARGETS == ("tests/test_spec_034_final_acceptance.py",)
    target = ROOT / verifier.TARGETS[0]
    tree = ast.parse(target.read_text(encoding="utf-8"))
    banned = {"subprocess", "socket", "urllib", "requests", "http", "network"}
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name.split(".", 1)[0] in banned for alias in node.names)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in {"subprocess", "socket"}
        for node in ast.walk(tree)
    )


# Task #80 J3 RED: permanent current authority drift after child completion
# must fail even when both temporary snapshots remain byte-exact.
def test_task80_j3_post_child_revalidates_current_authority(monkeypatch, tmp_path):
    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    authority = verifier._manifest_authority(root_digest)
    assert authority is not None
    records, capability = authority.records, authority.capability
    assert verifier._post_child_current_authority_valid(authority) is True
    original_read = verifier._read
    drift_path = ROOT / records[0]["path"]
    monkeypatch.setattr(
        verifier,
        "_read",
        lambda path: original_read(path) + b"permanent drift" if path == drift_path else original_read(path),
    )
    assert verifier._post_child_current_authority_valid(authority) is False
    monkeypatch.undo()
    # Replacement/restoration is distinguishable: restored current authority
    # passes while a permanent current-byte difference cannot.
    assert verifier._post_child_current_authority_valid(authority) is True


def test_task80_j4_actual_final_safe_target_runs_in_sentinel_snapshot():
    """Non-final smoke: execute only the final-safe target via runner helper."""
    from scripts import spec034_isolated_pytest_runner as runner
    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    authority = verifier._manifest_authority(root_digest)
    assert authority is not None
    records, capability_manifest = authority.records, authority.capability
    execution_records = verifier._execution_records(authority)
    assert execution_records is not None
    project = verifier._create_execution_snapshot(execution_records)
    capability, capability_records = verifier._create_capability_snapshot(capability_manifest)
    try:
        runner_record = next(record for record in execution_records if record.path == "scripts/spec034_isolated_pytest_runner.py")
        sentinel_record = next(record for record in execution_records if record.path == "scripts/spec034_offline_runtime_sentinel.py")
        runner_bytes = (project / runner_record.path).read_bytes()
        sentinel = (project / sentinel_record.path).read_bytes()
        payload = verifier._isolated_pytest_payload(project, execution_records, capability, capability_records, runner_bytes, sentinel)
        packet = json.loads(payload.decode("utf-8"))["payload"]
        assert packet["targets"] == ["tests/test_spec_034_final_acceptance.py"]
        assert packet["expected_node_ids"] == list(verifier.EXPECTED_FINAL_NODE_IDS)
        assert runner.run_isolated(packet) == 0
    finally:
        assert verifier._remove_snapshot(capability) is True
        assert verifier._remove_snapshot(project) is True


# Task #81 K2 RED: ambient pytest controls cannot select/collect no tests, and
# success requires the literal final target node set to execute as passed calls.
def test_task81_k2_runner_clears_ambient_pytest_controls_and_requires_exact_passes(monkeypatch, tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner

    project = tmp_path / "project"
    project.mkdir()
    target = project / "inert_target.py"
    target.write_text("def test_inert():\n    assert 2 + 2 == 4\n", encoding="utf-8")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "unapproved")
    monkeypatch.setenv("PYTEST_THEME", "dark")
    runner._clear_pytest_ambient()
    assert os.environ == {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_") or key == "PYTEST_DISABLE_PLUGIN_AUTOLOAD"}
    assert os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"

    from scripts import verify_spec_034_offline as verifier

    parent_env = verifier._minimal_child_env()
    assert parent_env == {key: value for key, value in parent_env.items() if not key.startswith("PYTEST_") or key == "PYTEST_DISABLE_PLUGIN_AUTOLOAD"}
    assert not any(key.startswith("PYTHON") for key in parent_env)
    assert parent_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    expected = ("inert_target.py::test_inert",)
    counter = runner._ExactPassedCalls(expected)
    counter.collected = expected
    counter.passed_calls = expected
    assert counter.complete is True
    counter.passed_calls = ()
    assert counter.complete is False


# Task #81 K3 RED: after detached authority is obtained, execution records and
# the snapshot retain those approved detached bytes without another pathname read.
def test_task81_k3_execution_snapshot_retains_authority_detached_bytes_after_replacement(monkeypatch):
    from scripts import verify_spec_034_offline as verifier

    root_digest = hashlib.sha256((SPEC / "contracts/review-root.json").read_bytes()).hexdigest()
    authority = verifier._manifest_authority(root_digest)
    assert authority is not None
    expected_root, expected_manifest = authority.root_bytes, authority.manifest_bytes
    original_read = verifier._read
    detached = {
        SPEC / "contracts/review-root.json": b"replacement root must not be reread",
        SPEC / "contracts/reviewed-artifact-manifest.json": b"replacement manifest must not be reread",
    }
    monkeypatch.setattr(verifier, "_read", lambda path: detached[path] if path in detached else original_read(path))
    records = verifier._execution_records(authority)
    assert records is not None
    detached_records = tuple(record for record in records if record.category == "detached")
    snapshot = verifier._create_execution_snapshot(detached_records)
    try:
        assert (snapshot / "specs/034-hermes-v019-pinned-startup-source-graph/contracts/review-root.json").read_bytes() == expected_root
        assert (snapshot / "specs/034-hermes-v019-pinned-startup-source-graph/contracts/reviewed-artifact-manifest.json").read_bytes() == expected_manifest
    finally:
        assert verifier._remove_snapshot(snapshot) is True


# Task #82 L1 RED: a child may start with the parent workspace as its process
# cwd, but it must bind its payload cwd and run tests from its verified project
# snapshot before any target import can resolve relative configuration.
def test_task82_l1_child_cwd_is_exact_snapshot_and_payload_cwd_is_bound(tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner
    from scripts import verify_spec_034_offline as verifier

    project = tmp_path / "project"
    package = project / "src" / "podcast_ingest_core"
    package.mkdir(parents=True)
    (project / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
    (package / "__init__.py").write_bytes(b"")
    target = project / "inert_target.py"
    target.write_text(
        "from pathlib import Path\n\ndef test_inert():\n    assert Path.cwd().absolute() == Path(__file__).parent.absolute()\n",
        encoding="utf-8",
    )
    records = [
        {"path": path, "sha256": hashlib.sha256((project / path).read_bytes()).hexdigest(), "byte_length": len((project / path).read_bytes())}
        for path in ("pyproject.toml", "src/podcast_ingest_core/__init__.py", "inert_target.py")
    ]
    capability_manifest = json.loads((SPEC / "contracts/python-test-capability-manifest.json").read_text(encoding="utf-8"))
    capability, capability_records = verifier._create_capability_snapshot(capability_manifest)
    sentinel = (ROOT / "scripts/spec034_offline_runtime_sentinel.py").read_bytes()
    try:
        payload = {
            "project_snapshot": str(project), "project_records": records,
            "capability_snapshot": str(capability), "capability_records": list(capability_records),
            "targets": ["inert_target.py"], "expected_node_ids": ["inert_target.py::test_inert"],
            "cwd": str(project),
            "approved_top_levels": sorted({top for values in verifier.CAPABILITY_TOP_LEVELS.values() for top in values}),
            "sentinel": {"module": "spec034_sealed_sentinel", "bytes_b64": __import__("base64").b64encode(sentinel).decode("ascii"), "sha256": hashlib.sha256(sentinel).hexdigest(), "byte_length": len(sentinel)},
        }
        assert runner.run_isolated(payload) == 0
        payload["cwd"] = str(tmp_path)
        assert runner.run_isolated(payload) == 21
    finally:
        assert verifier._remove_snapshot(capability) is True


# Task #82 L1 RED: after snapshot creation, replacement of all three original
# workspace configs cannot change the C6 helper's relative config observations.
def test_task82_l1_c6_reads_approved_relative_configs_from_snapshot(monkeypatch, tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner
    from scripts import verify_spec_034_offline as verifier

    workspace = tmp_path / "workspace"
    for relative in (
        "pyproject.toml", "src/podcast_ingest_core/__init__.py", "tests/__init__.py", "tests/spec034_final_c6_support.py",
        "config/industry_chain_mappings.yaml", "config/external_data_boundary.yaml", "config/gooaye_lens.yaml",
    ):
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    target = workspace / "snapshot_target.py"
    target.write_text(
        "from tests.spec034_final_c6_support import _spec034_snapshot_config_bytes\n\ndef test_snapshot_config():\n    _spec034_snapshot_config_bytes()\n",
        encoding="utf-8",
    )
    records = tuple(
        {"path": relative, "sha256": hashlib.sha256((workspace / relative).read_bytes()).hexdigest(), "byte_length": len((workspace / relative).read_bytes())}
        for relative in (
            "pyproject.toml", "src/podcast_ingest_core/__init__.py", "tests/__init__.py", "tests/spec034_final_c6_support.py", "snapshot_target.py",
            "config/industry_chain_mappings.yaml", "config/external_data_boundary.yaml", "config/gooaye_lens.yaml",
        )
    )
    monkeypatch.setattr(verifier, "ROOT", workspace)
    project = verifier._create_project_snapshot(records)
    capability_manifest = json.loads((SPEC / "contracts/python-test-capability-manifest.json").read_text(encoding="utf-8"))
    capability, capability_records = verifier._create_capability_snapshot(capability_manifest)
    sentinel = (ROOT / "scripts/spec034_offline_runtime_sentinel.py").read_bytes()
    try:
        for relative in ("industry_chain_mappings.yaml", "external_data_boundary.yaml", "gooaye_lens.yaml"):
            (workspace / "config" / relative).write_bytes(b"original-workspace-replaced")
        payload = {
            "project_snapshot": str(project), "project_records": list(records),
            "capability_snapshot": str(capability), "capability_records": list(capability_records),
            "targets": ["snapshot_target.py"], "expected_node_ids": ["snapshot_target.py::test_snapshot_config"], "cwd": str(project),
            "approved_top_levels": sorted({top for values in verifier.CAPABILITY_TOP_LEVELS.values() for top in values}),
            "sentinel": {"module": "spec034_sealed_sentinel", "bytes_b64": __import__("base64").b64encode(sentinel).decode("ascii"), "sha256": hashlib.sha256(sentinel).hexdigest(), "byte_length": len(sentinel)},
        }
        assert runner.run_isolated(payload) == 0
    finally:
        assert verifier._remove_snapshot(capability) is True
        assert verifier._remove_snapshot(project) is True


# Task #82 L2 RED: public receipt construction has no caller-replaceable
# provenance verifier. Only current canonical audit projections may issue it.
def test_task82_l2_receipt_rejects_injected_or_discovered_issuer():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    bundle = graph.validate_spec034_source_bundle()
    audit = graph.audit_spec034_startup_source_graph(bundle)
    plugin = graph.audit_spec034_bundled_plugin(bundle, audit)
    with __import__("pytest").raises(TypeError):
        graph.project_spec034_source_graph_receipt(bundle, audit, plugin, _require=lambda *_args: None)
    issuer_names = ("_ISSUE_CATALOG", "_ISSUE_GRAPH", "_ISSUE_PLUGIN", "_REQUIRE_PAIR")
    assert not any(callable(getattr(graph, name, None)) for name in issuer_names)
    with __import__("pytest").raises(TypeError):
        graph._DECISION_AUTHORITY.graph_issue(bundle, "forged")
    receipt = graph.project_spec034_source_graph_receipt(bundle, audit, plugin)
    assert receipt["claim_statuses"]["credential_provider_boundary"] == "BLOCKED_SOURCE_GRAPH"
    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(graph, "_validated_bytes", lambda: None)
        with __import__("pytest").raises(TypeError):
            graph.project_spec034_source_graph_receipt(bundle, audit, plugin)
    finally:
        monkeypatch.undo()


# Task #82 L3 RED: the directory loader's spec/module/loader/return flow must
# retain one named value at every ownership-scoped transition.
def test_task82_l3_plugin_loader_ast_dataflow_rejects_alias_and_substitution():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = graph._validated_bytes()
    assert source is not None
    loader = source["hermes_cli/plugins.py"]
    mutations = (
        (b"        module = importlib.util.module_from_spec(spec)", b"        spec_alias = spec\n        module = importlib.util.module_from_spec(spec)"),
        (b"module_from_spec(spec)", b"module_from_spec(other_spec)"),
        (b"spec.loader.exec_module(module)", b"alternate_loader.exec_module(module)"),
        (b"spec.loader.exec_module(module)", b"spec.loader.exec_module(other_module)"),
        (b"return module", b"return other_module"),
    )
    for old, new in mutations:
        changed = dict(source)
        changed["hermes_cli/plugins.py"] = loader.replace(old, new, 1)
        assert changed["hermes_cli/plugins.py"] != loader
        assert graph._bundled_security_guidance_identity_proven(changed) is False


# Task #83 M1 RED: child code loading must retain the approved in-memory bytes
# after a snapshot pathname is swapped and restored.  This is an inert mini
# package seam, not an attempt to execute any final entrypoint.
def test_task83_m1_snapshot_importer_executes_cached_approved_bytes_after_path_swap(tmp_path):
    from scripts import spec034_isolated_pytest_runner as runner

    root = tmp_path / "snapshot"
    package = root / "mini"
    package.mkdir(parents=True)
    original = b"VALUE = 'approved'\n"
    malicious = b"raise RuntimeError('malicious pathname code executed')\n"
    init = package / "__init__.py"
    init.write_bytes(original)
    records = {
        "mini/__init__.py": original,
    }

    importer = runner._VerifiedBytesImporter(root, records)
    init.write_bytes(malicious)
    import importlib
    import sys
    sys.meta_path.insert(0, importer)
    sys.modules.pop("mini", None)
    try:
        module = importlib.import_module("mini")
        assert module.VALUE == "approved"
        assert module.__file__ == str(init.absolute())
    finally:
        sys.modules.pop("mini", None)
        sys.meta_path.remove(importer)
        init.write_bytes(original)


# Task #83 M2 RED: dead decoys and split branches cannot satisfy a same-spec
# reachable flow proof merely by providing every desired call somewhere.
def test_task83_m2_plugin_dataflow_rejects_dead_decoy_and_split_branch_flow():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    source = graph._validated_bytes()
    assert source is not None
    loader = source["hermes_cli/plugins.py"]
    dead_decoy = loader.replace(
        b"        module = importlib.util.module_from_spec(spec)\n        module.__package__ = module_name",
        b"        if False:\n            module = importlib.util.module_from_spec(spec)\n            spec.loader.exec_module(module)\n            return module\n        module.__package__ = module_name",
        1,
    )
    split_branch = loader.replace(
        b"        module = importlib.util.module_from_spec(spec)\n        module.__package__ = module_name",
        b"        if manifest.name:\n            module = importlib.util.module_from_spec(spec)\n        else:\n            module = alternate_module\n        module.__package__ = module_name",
        1,
    )
    caller_split_branch = loader.replace(
        b"                module = self._load_directory_module(manifest)\n            else:\n                module = self._load_entrypoint_module(manifest)",
        b"                if manifest.name:\n                    module = self._load_directory_module(manifest)\n                else:\n                    module = alternate_module\n            else:\n                module = self._load_entrypoint_module(manifest)",
        1,
    )
    for mutated in (dead_decoy, split_branch, caller_split_branch):
        changed = dict(source)
        changed["hermes_cli/plugins.py"] = mutated
        assert graph._bundled_security_guidance_identity_proven(changed) is False


# Task #82 L4 RED: persist the rename directory entry before writing its journal
# phase, and treat exact bundle_renamed/both-missing state as retry-safe rollback.
def test_task82_l4_bundle_rename_fsync_precedes_journal_and_recovers_both_missing(monkeypatch, tmp_path):
    acquisition, _graph, bundle = _task78_local_publication_workspace(monkeypatch, tmp_path)
    events: list[str] = []
    original_rename = acquisition.os.rename
    original_journal = acquisition._write_lock

    def renamed(source, destination):
        events.append("rename")
        return original_rename(source, destination)

    def journal(phase, *args, **kwargs):
        events.append(f"journal:{phase}")
        return original_journal(phase, *args, **kwargs)

    monkeypatch.setattr(acquisition.os, "rename", renamed)
    monkeypatch.setattr(acquisition, "_fsync_parent_best_effort", lambda path: events.append(f"fsync:{path}"))
    monkeypatch.setattr(acquisition, "_write_lock", journal)
    acquisition._write(bundle)
    assert events.index("rename") < events.index(f"fsync:{acquisition.BUNDLE_ROOT}") < events.index("journal:bundle_renamed")

    __import__("shutil").rmtree(acquisition.BUNDLE_ROOT)
    acquisition.MANIFEST_PATH.unlink()
    nonce = "c" * 32
    acquisition._write_journal("bundle_renamed", f".{acquisition.BUNDLE_ROOT.name}.stage-{nonce}", nonce, exclusive=True)
    assert acquisition.recover_interrupted_publication() is True
    assert not acquisition.PUBLICATION_LOCK_PATH.exists()
