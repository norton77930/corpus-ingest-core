"""Sentinel-safe final acceptance for Spec034's sealed child only.

This suite deliberately uses canonical bytes, AST, and public static seams.  It
contains no process, socket, or network operation; runner/journal/trust tests
remain non-final verification.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/034-hermes-v019-pinned-startup-source-graph"
TERMINAL = "startup/plugin closed; credential_provider BLOCKED; overall BLOCKED"


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_c0_reviewed_artifacts_and_detached_authority_are_current():
    manifest_path = SPEC / "contracts/reviewed-artifact-manifest.json"
    root_path = SPEC / "contracts/review-root.json"
    manifest = _json(manifest_path)
    root = _json(root_path)
    records = manifest["artifacts"]
    assert isinstance(records, list)
    assert "reviewed-artifact-manifest.json" not in {item["path"] for item in records}
    assert "review-root.json" not in {item["path"] for item in records}
    for record in records:
        path = ROOT / record["path"]
        assert path.read_bytes()
        assert len(path.read_bytes()) == record["byte_length"]
        assert _sha(path) == record["sha256"]
    assert root["reviewed_manifest_sha256"] == _sha(manifest_path)
    assert root["launcher_contract_sha256"] == _sha(SPEC / "contracts/final-invocation.md")


def test_c1_h2_bundle_is_exactly_twenty_current_literal_records():
    manifest = _json(SPEC / "contracts/source-bundle-manifest.json")
    files = manifest["files"]
    assert len(files) == 20
    bundle = SPEC / "upstream/NousResearch-hermes-agent-b7a05b6"
    actual = sorted(path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file())
    assert actual == [record["path"] for record in files]
    for record in files:
        data = (bundle / record["path"]).read_bytes()
        assert len(data) == record["byte_length"]
        assert hashlib.sha256(data).hexdigest() == record["sha256"]
        assert hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest() == record["git_blob_sha"]


def test_c2_predecessor_boundary_pins_all_three_current_records():
    boundary = _json(SPEC / "contracts/predecessor-boundary.json")
    predecessor = ROOT / "specs/033-hermes-v019-pinned-source-loader-audit/contracts"
    expected = {
        "spec033_review_root_sha256": predecessor / "review-root.json",
        "spec033_reviewed_artifact_manifest_sha256": predecessor / "reviewed-artifact-manifest.json",
        "spec033_source_manifest_sha256": predecessor / "source-bundle-manifest.json",
    }
    assert all(boundary[name] == _sha(path) for name, path in expected.items())


def test_c3_static_receipt_is_closed_only_for_startup_and_plugin():
    from podcast_ingest_core import hermes_v019_startup_source_graph as graph

    bundle = graph.validate_spec034_source_bundle()
    audit = graph.audit_spec034_startup_source_graph(bundle)
    plugin = graph.audit_spec034_bundled_plugin(bundle, audit)
    receipt = graph.project_spec034_source_graph_receipt(bundle, audit, plugin)
    assert receipt["claim_statuses"]["startup_source_ordering"] == "STATIC_SOURCE_GRAPH_CLOSED"
    assert receipt["claim_statuses"]["security_guidance_plugin"] == "STATIC_SOURCE_GRAPH_CLOSED"
    assert receipt["claim_statuses"]["credential_provider_boundary"] == "BLOCKED_SOURCE_GRAPH"
    assert receipt["runtime_status"] == "not_run"
    assert receipt["live_actions_authorized"] is False


def test_c4_sentinel_and_final_target_are_static_and_closed():
    sentinel = ROOT / "scripts/spec034_offline_runtime_sentinel.py"
    source = sentinel.read_text(encoding="utf-8")
    assert "socket.socket = _blocked" in source
    assert "subprocess.run = _blocked" in source
    assert "urllib.request.urlopen = _blocked" in source
    target = Path(__file__)
    tree = ast.parse(target.read_text(encoding="utf-8"))
    banned = {"subprocess", "socket", "urllib", "requests", "http", "network"}
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name.split(".", 1)[0] in banned for alias in node.names)
        for node in ast.walk(tree)
    )


def test_c5_public_product_seams_remain_available_without_external_execution():
    from podcast_ingest_core import verified_research_report as report

    assert callable(report.assemble_verified_research_report)
    assert callable(report.publish_verified_research_report_bundle)
    assert "OpenAICompatibleProvider" not in Path(report.__file__).read_text(encoding="utf-8")


def test_c6_current_docs_preserve_blocked_terminal_and_no_live_claim(monkeypatch, tmp_path):
    from tests.spec034_final_c6_support import run_c6_public_workflow

    run_c6_public_workflow(monkeypatch, tmp_path)
    current = (
        ROOT / "README.md", ROOT / "docs/roadmap.md", ROOT / "docs/verification-matrix.md",
        ROOT / "specs/README.md", SPEC / "proposal.md", SPEC / "spec.md", SPEC / "plan.md",
        SPEC / "tasks.md", SPEC / "checklists/requirements.md", SPEC / "checklists/safety.md",
        SPEC / "contracts/final-invocation.md",
    )
    for path in current:
        assert TERMINAL in path.read_text(encoding="utf-8")


def test_c7_final_acceptance_is_the_only_final_child_target():
    verifier = ROOT / "scripts/verify_spec_034_offline.py"
    source = verifier.read_text(encoding="utf-8")
    assert 'TARGETS = ("tests/test_spec_034_final_acceptance.py",)' in source
    assert "tests/test_spec_034_h4_repair.py" not in source.split("TARGETS =", 1)[1].split("PYTEST_ARGUMENTS", 1)[0]
