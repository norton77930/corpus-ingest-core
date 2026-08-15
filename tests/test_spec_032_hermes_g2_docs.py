"""Static successor, fixture, CLI, and future-boundary guards for Spec032."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/032-hermes-g2-offline-attempt-executor"


def test_successor_docs_and_predecessor_digests_are_truthful_and_immutable():
    marker = "BLOCKED_CREDENTIAL_SEAM"
    for name in ("proposal.md", "spec.md", "plan.md", "data-model.md", "tasks.md", "contracts/executor-contract.md"):
        assert marker in (SPEC / name).read_text(encoding="utf-8") or name in {"data-model.md", "tasks.md"}
    manifest = json.loads((SPEC / "contracts/predecessor-digests.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "spec032-predecessor-boundary-v2"
    assert set(manifest["scope"]) == {"specs", "deploy", "source", "scripts", "tests"}
    scoped = {path for group in manifest["scope"].values() for path in group}
    assert set(manifest["immutable_predecessor_files"]) == scoped
    verifier_tree = ast.parse((ROOT / "scripts/verify_spec_032_offline.py").read_text(encoding="utf-8"))
    inventory = next(
        ast.literal_eval(node.value)
        for node in verifier_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AUTHORITATIVE_PREDECESSOR_PATHS" for target in node.targets)
    )
    assert type(inventory) is tuple and set(inventory) == scoped == set(manifest["immutable_predecessor_files"])
    assert {
        "scripts/run_mcp_http_server.py",
        "tests/test_mcp_http_transport.py",
        "src/podcast_ingest_core/mcp_tools_corpus_workflows.py",
        "src/podcast_ingest_core/mcp_tools_read.py",
        "src/podcast_ingest_core/mcp_tools_side_effect.py",
        "src/podcast_ingest_core/mcp_tools_verified_report_queries.py",
    } <= scoped
    for number in range(26, 32):
        assert any(path.startswith(f"specs/{number:03d}-") for path in scoped)
    for relative, digest in manifest["immutable_predecessor_files"].items():
        assert type(relative) is str and type(digest) is str and len(digest) == 64
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    source = json.loads((SPEC / "contracts/source-audit-manifest.json").read_text(encoding="utf-8"))
    assert source["pinned_commit"] == "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
    assert source["official_loader_call_path_verified"] is False and source["terminal_status"] == marker
    reviewed = json.loads((SPEC / "contracts/reviewed-artifact-manifest.json").read_text(encoding="utf-8"))
    assert reviewed["schema_version"] == "spec032-reviewed-artifact-manifest-v2"
    assert reviewed["review_evidence_included"] is False
    assert "excluded" in reviewed["self_hash_policy"]
    assert "contracts/reviewed-artifact-manifest.json" not in {item["path"] for item in reviewed["artifacts"]}
    assert all((ROOT / item["path"]).is_file() and (ROOT / item["path"]).stat().st_size == item["byte_length"] and hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"] for item in reviewed["artifacts"])


def test_spec032_ledger_docs_are_in_memory_single_process_and_future_only_for_filesystem():
    owned = (
        "proposal.md", "spec.md", "plan.md", "data-model.md", "tasks.md",
        "contracts/executor-contract.md",
    )
    text = "\n".join((SPEC / name).read_text(encoding="utf-8") for name in owned).lower()
    assert "in-memory" in text and "single-process" in text and "future-only" in text
    assert "test-storage" not in text and "fixed ledger filename" not in text and "exclusive claim/staging" not in text
    for relative in ("README.md", "docs/roadmap.md", "docs/verification-matrix.md", "specs/README.md"):
        pointer = (ROOT / relative).read_text(encoding="utf-8").lower()
        assert "in-memory" in pointer and "single-process" in pointer


def test_fixture_and_cli_remain_definition_only_and_blocked_without_echoing_bad_argv():
    fixture = json.loads((ROOT / "deploy/hermes/spec032/fixture-definition.json").read_text(encoding="utf-8"))
    assert fixture == {**fixture, "activation_ready": False, "build_authorized": False, "official_loader_verified": False, "provider_materialization_status": "blocked_unknown", "live_actions_authorized": False}
    probe = (ROOT / "deploy/hermes/spec032/credentialless_probe.py").read_text(encoding="utf-8")
    assert "plugin.register(" not in probe and "credential" in probe and "provider" in probe
    cli = (ROOT / "scripts/validate_hermes_g2_executor_offline.py").read_text(encoding="utf-8")
    assert "run_spec_032_g2_once" not in cli and "hermes_g2_docker_driver" not in cli


def test_offline_targets_have_no_subprocess_or_future_runtime_imports():
    verifier = ROOT / "scripts/verify_spec_032_offline.py"
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    targets = next(node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "OFFLINE_PYTEST_TARGETS" for target in node.targets))
    assert {item.value for item in targets.elts} == {
        "tests/test_hermes_g2_activation_authority.py",
        "tests/test_hermes_g2_attempt_ledger.py",
        "tests/test_hermes_g2_activation_executor.py",
        "tests/test_hermes_g2_docker_commands.py",
        "tests/test_spec_032_hermes_g2_docs.py",
    }
    assert any(isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "PREDECESSOR_STATIC_BOUNDARY" for target in node.targets) for node in tree.body)
    sentinel_tree = ast.parse((ROOT / "scripts/spec032_offline_runtime_sentinel.py").read_text(encoding="utf-8"))
    session_hook = next(
        node
        for node in sentinel_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "pytest_sessionstart"
    )
    assert [argument.arg for argument in session_hook.args.args] == ["session"]
    for item in targets.elts:
        source = (ROOT / item.value).read_text(encoding="utf-8")
        target_tree = ast.parse(source)
        forbidden_modules = {"subprocess", "podcast_ingest_core.hermes_g2_docker_driver", "scripts.run_spec_032_g2_once"}
        imported = {
            alias.name for node in ast.walk(target_tree) if isinstance(node, ast.Import) for alias in node.names
        } | {
            node.module for node in ast.walk(target_tree) if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not imported & forbidden_modules
        assert not any(
            isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
            for node in ast.walk(target_tree)
        )


def test_runtime_and_static_sentinels_block_package_level_future_imports():
    import builtins
    import pytest
    from scripts import verify_spec_032_offline as verifier

    cases = (
        ("podcast_ingest_core", "hermes_g2_docker_driver"),
        ("scripts", "run_spec_032_g2_once"),
    )
    for package, child in cases:
        with pytest.raises(AssertionError, match="Spec032 offline sentinel"):
            builtins.__import__(package, fromlist=(child,))
        tree = ast.parse(f"from {package} import {child}")
        assert verifier._forbidden_target_ast(tree) is True


def test_runtime_and_static_sentinels_block_relative_future_imports():
    import builtins
    import pytest
    from scripts import verify_spec_032_offline as verifier

    package_globals = {"__package__": "podcast_ingest_core"}
    with pytest.raises(AssertionError, match="Spec032 offline sentinel"):
        builtins.__import__("", package_globals, None, ("hermes_g2_docker_driver",), 1)
    with pytest.raises(AssertionError, match="Spec032 offline sentinel"):
        builtins.__import__("hermes_g2_docker_driver", package_globals, None, ("FutureSpec032DockerDriver",), 1)
    for source in (
        "from . import hermes_g2_docker_driver",
        "from .hermes_g2_docker_driver import FutureSpec032DockerDriver",
    ):
        tree = ast.parse(source)
        assert verifier._forbidden_target_ast(tree) is True
        assert verifier._forbidden_verifier_ast(tree) is True


def test_runtime_and_static_sentinels_block_forbidden_module_descendants():
    import ast
    import builtins
    import pytest
    from scripts import verify_spec_032_offline as verifier

    cases = (
        ("podcast_ingest_core.hermes_g2_docker_driver.nonexistent", {}),
        ("scripts.run_spec_032_g2_once.nonexistent", {}),
        ("hermes_g2_docker_driver.nonexistent", {"__package__": "podcast_ingest_core"}),
    )
    for name, package_globals in cases:
        with pytest.raises(AssertionError, match="Spec032 offline sentinel"):
            builtins.__import__(name, package_globals, None, (), 1 if package_globals else 0)
    for source in (
        "import podcast_ingest_core.hermes_g2_docker_driver.nonexistent",
        "import scripts.run_spec_032_g2_once.nonexistent",
        "from podcast_ingest_core.hermes_g2_docker_driver.nonexistent import value",
    ):
        tree = ast.parse(source)
        assert verifier._forbidden_target_ast(tree) is True
        assert verifier._forbidden_verifier_ast(tree) is True


def test_verifier_never_imports_future_runner_or_concrete_driver_and_their_static_sources_parse():
    verifier = ROOT / "scripts/verify_spec_032_offline.py"
    tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all("hermes_g2_docker_driver" not in item and "run_spec_032_g2_once" not in item for item in imports)
    verifier_source = verifier.read_text(encoding="utf-8")
    assert "OFFLINE_PYTEST_TARGETS" in verifier_source
    assert "_forbidden_verifier_ast" in verifier_source
    assert '"import_module"' in verifier_source
    for relative in ("src/podcast_ingest_core/hermes_g2_docker_driver.py", "scripts/run_spec_032_g2_once.py"):
        compile((ROOT / relative).read_text(encoding="utf-8"), relative, "exec")


def test_top_level_pointers_and_matrix_do_not_claim_live_or_final_pass():
    for relative in ("README.md", "specs/README.md", "docs/roadmap.md", "docs/verification-matrix.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "Spec 032" in text and "BLOCKED_CREDENTIAL_SEAM" in text
        assert "PASS_OFFLINE_EXECUTOR_CONTRACT" in text and "not live" in text
        assert "future" in text.lower() and "production ledger" in text.lower()
    assert "next unused feature package number is **032**" in (ROOT / "docs/roadmap.md").read_text(encoding="utf-8")
