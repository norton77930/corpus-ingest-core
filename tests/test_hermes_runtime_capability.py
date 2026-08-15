"""Focused offline capability-gate tests for Spec 028."""

from __future__ import annotations

import ast
import inspect
import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_hermes_runtime_capability.py"
MODULE = ROOT / "src" / "podcast_ingest_core" / "hermes_runtime_capability.py"
MANIFEST = (
    ROOT
    / "specs"
    / "028-hermes-runtime-skill-routing-observation"
    / "contracts"
    / "hermes-v2026.8.3-source-manifest.json"
)

SAFE_KEYS = {
    "schema_version",
    "spec_id",
    "terminal_status",
    "runtime_target",
    "release_tag",
    "missing_requirement_count",
    "ok",
    "mode",
    "verdict",
    "failure_code",
    "source_identity_verified",
    "coverage_complete",
    "canonical_skill_identity",
    "skill_to_tool_linkage",
    "fallback_used",
    "fallback_not_used",
    "guaranteed_skill_tool_correlation",
    "official_no_side_effect_positive_control",
    "live_actions_authorized",
    "hermes_runtime_observation",
    "c6_status",
    "synthetic_all_present_passes",
    "synthetic_missing_fail_closed",
    "synthetic_ambiguous_fail_closed",
    "synthetic_invalid_fail_closed",
    "synthetic_non_boolean_fail_closed",
    "synthetic_source_identity_malformed_fail_closed",
}


def _all_present(module):
    return tuple(
        module.RequirementObservation(
            requirement,
            module.ObservationState.PRESENT,
            True,
        )
        for requirement in module.CapabilityRequirement
    )


def test_pinned_manifest_has_exact_official_source_identity_and_terminal_block():
    import podcast_ingest_core.hermes_runtime_capability as capability

    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(raw) == {
        "schema_version",
        "repository",
        "release",
        "annotated_tag",
        "annotated_tag_object_sha",
        "tag_target_commit_sha",
        "hooks_path",
        "hooks_blob_sha",
        "terminal_verdict",
        "requirements",
    }
    assert raw["schema_version"] == "hermes-v2026.8.3-source-manifest-v1"
    assert raw["repository"] == "NousResearch/hermes-agent"
    assert raw["release"] == "Hermes Agent v0.20.0"
    assert raw["annotated_tag"] == "v2026.8.3"
    assert raw["annotated_tag_object_sha"] == "7de39e700d2c329e15d32eb0b96e2f7cdd9fbdb2"
    assert raw["tag_target_commit_sha"] == "3c27eb6234bf91b8ceee9e9071591b31e9b148cb"
    assert raw["hooks_path"] == "website/docs/user-guide/features/hooks.md"
    assert raw["hooks_blob_sha"] == "be8b9c0caa2792a24bb34dba9400400acdf91eaa"
    assert raw["terminal_verdict"] == "blocked_capability"

    manifest = capability.load_pinned_hermes_source_manifest()
    result = capability.evaluate_hermes_capability(
        manifest.observations,
        manifest.source_identity,
    )
    assert result.verdict is capability.CapabilityVerdict.BLOCKED_CAPABILITY
    assert result.failure is capability.FailureCode.BLOCKED_CAPABILITY


def test_evaluator_is_total_and_fails_closed_for_missing_ambiguous_invalid_and_non_boolean_inputs():
    import podcast_ingest_core.hermes_runtime_capability as capability

    identity = capability.canonical_source_identity()
    passed = capability.evaluate_hermes_capability(_all_present(capability), identity)
    assert passed.verdict is capability.CapabilityVerdict.PASS_CANONICAL_COVERAGE

    missing = capability.evaluate_hermes_capability(
        _all_present(capability)[1:], identity
    )
    ambiguous = capability.evaluate_hermes_capability(
        (
            capability.RequirementObservation(
                capability.CapabilityRequirement.CANONICAL_SKILL_IDENTITY,
                capability.ObservationState.AMBIGUOUS,
                True,
            ),
        )
        + _all_present(capability)[1:],
        identity,
    )
    invalid = capability.evaluate_hermes_capability((object(),), identity)
    non_boolean = capability.evaluate_hermes_capability(
        (
            capability.RequirementObservation(
                capability.CapabilityRequirement.CANONICAL_SKILL_IDENTITY,
                capability.ObservationState.PRESENT,
                "yes",
            ),
        )
        + _all_present(capability)[1:],
        identity,
    )
    malformed_identity = capability.evaluate_hermes_capability(
        _all_present(capability), replace(identity, hooks_blob_sha="not-a-sha")
    )

    for blocked in (missing, ambiguous):
        assert blocked.verdict is capability.CapabilityVerdict.BLOCKED_CAPABILITY
        assert blocked.failure is capability.FailureCode.BLOCKED_CAPABILITY
    for malformed in (invalid, non_boolean, malformed_identity):
        assert malformed.verdict is capability.CapabilityVerdict.INVALID_EVIDENCE
        assert malformed.failure in {
            capability.FailureCode.INVALID_EVIDENCE,
            capability.FailureCode.INVALID_SOURCE_IDENTITY,
        }


def test_safe_evidence_has_exact_keys_no_raw_values_and_actual_gate_terminates_without_live_authorization():
    import podcast_ingest_core.hermes_runtime_capability as capability

    raw_sentinel = "raw hook payload prompt args results must never escape"
    manifest = capability.load_pinned_hermes_source_manifest()
    actual = capability.evaluate_hermes_capability(
        manifest.observations,
        manifest.source_identity,
    )
    safe = capability.build_capability_evidence(actual)

    assert set(safe) == SAFE_KEYS
    assert safe == {
        "schema_version": "hermes-runtime-capability-evidence-v1",
        "spec_id": "028-hermes-runtime-skill-routing-observation",
        "terminal_status": "blocked_capability",
        "runtime_target": "hermes-agent",
        "release_tag": "v2026.8.3",
        "missing_requirement_count": 6,
        "ok": True,
        "mode": "capability",
        "verdict": "BLOCKED_CAPABILITY",
        "failure_code": "blocked_capability",
        "source_identity_verified": True,
        "coverage_complete": False,
        "canonical_skill_identity": "missing",
        "skill_to_tool_linkage": "missing",
        "fallback_used": "missing",
        "fallback_not_used": "missing",
        "guaranteed_skill_tool_correlation": "missing",
        "official_no_side_effect_positive_control": "missing",
        "live_actions_authorized": False,
        "hermes_runtime_observation": "not_run",
        "c6_status": "pass_current_not_rerun",
        "synthetic_all_present_passes": False,
        "synthetic_missing_fail_closed": False,
        "synthetic_ambiguous_fail_closed": False,
        "synthetic_invalid_fail_closed": False,
        "synthetic_non_boolean_fail_closed": False,
        "synthetic_source_identity_malformed_fail_closed": False,
    }
    assert raw_sentinel not in json.dumps(safe, sort_keys=True)


def test_cli_accepts_only_fixed_offline_modes_and_never_echoes_argv():
    capability = subprocess.run(
        [sys.executable, str(SCRIPT), "capability"],
        check=False,
        capture_output=True,
        text=True,
    )
    synthetic = subprocess.run(
        [sys.executable, str(SCRIPT), "synthetic"],
        check=False,
        capture_output=True,
        text=True,
    )
    sentinel = "raw-prompt-args-results-sentinel"
    rejected = subprocess.run(
        [sys.executable, str(SCRIPT), sentinel],
        check=False,
        capture_output=True,
        text=True,
    )

    assert capability.returncode == 0
    capability_payload = json.loads(capability.stdout)
    assert set(capability_payload) == SAFE_KEYS
    assert capability_payload["ok"] is True
    assert capability_payload["verdict"] == "BLOCKED_CAPABILITY"
    assert capability_payload["live_actions_authorized"] is False
    assert capability_payload["hermes_runtime_observation"] == "not_run"
    assert capability_payload["c6_status"] == "pass_current_not_rerun"

    assert synthetic.returncode == 0
    synthetic_payload = json.loads(synthetic.stdout)
    assert set(synthetic_payload) == SAFE_KEYS
    assert synthetic_payload["ok"] is True
    assert synthetic_payload["verdict"] == "PASS_CANONICAL_COVERAGE"
    assert all(
        synthetic_payload[key] is True
        for key in (
            "synthetic_all_present_passes",
            "synthetic_missing_fail_closed",
            "synthetic_ambiguous_fail_closed",
            "synthetic_invalid_fail_closed",
            "synthetic_non_boolean_fail_closed",
            "synthetic_source_identity_malformed_fail_closed",
        )
    )

    assert rejected.returncode == 2
    rejected_payload = json.loads(rejected.stdout)
    assert set(rejected_payload) == SAFE_KEYS
    assert rejected_payload["mode"] == "rejected"
    assert rejected_payload["verdict"] == "INVALID_EVIDENCE"
    assert rejected_payload["failure_code"] == "invalid_mode"
    assert sentinel not in rejected.stdout
    assert rejected.stderr == ""


def test_module_and_cli_remain_offline_read_only_without_a_second_skill_router_or_live_boundary():
    for path in (MODULE, SCRIPT):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert not {
            "docker",
            "mcp",
            "requests",
            "urllib",
            "http",
            "socket",
            "subprocess",
            "podcast_ingest_core.hermes_integration",
        }.intersection(imported_modules)
        assert ".write_text(" not in source
        assert ".write_bytes(" not in source
        assert "hermes_integration" not in source
        assert "mcp_server" not in source
        assert "mcp_runtime" not in source
        assert "validate_hermes_integration" not in source

    module_source = MODULE.read_text(encoding="utf-8")
    for prohibited in (
        "corpus-episode-completion",
        "run_corpus_episode_completion_workflow",
        "corpus-latest-episode-processing",
        "run_corpus_latest_episode_deterministic_workflow",
        "latest-episode-verified-research-report",
        "run_latest_episode_verified_research_report_workflow",
        "episode-verified-research-report",
        "run_episode_verified_research_report_workflow",
    ):
        assert prohibited not in module_source


def test_pinned_loader_rejects_manifest_schema_keyset_and_requirement_shape_drift(tmp_path, monkeypatch):
    import podcast_ingest_core.hermes_runtime_capability as capability

    assert tuple(inspect.signature(capability.load_pinned_hermes_source_manifest).parameters) == ()
    canonical = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hostile_manifests = []

    additional = dict(canonical)
    additional["unreviewed_field"] = "sentinel"
    hostile_manifests.append(additional)

    missing_top_level = dict(canonical)
    del missing_top_level["hooks_blob_sha"]
    hostile_manifests.append(missing_top_level)

    schema_drift = dict(canonical)
    schema_drift["schema_version"] = "unexpected-schema"
    hostile_manifests.append(schema_drift)

    additional_requirement = dict(canonical)
    additional_requirement["requirements"] = {
        **canonical["requirements"],
        "unreviewed_requirement": "missing",
    }
    hostile_manifests.append(additional_requirement)

    missing_requirement = dict(canonical)
    missing_requirement["requirements"] = dict(canonical["requirements"])
    del missing_requirement["requirements"]["fallback_used"]
    hostile_manifests.append(missing_requirement)

    for index, hostile in enumerate(hostile_manifests):
        path = tmp_path / f"hostile-{index}.json"
        path.write_text(json.dumps(hostile), encoding="utf-8")
        with monkeypatch.context() as patch:
            patch.setattr(capability, "_MANIFEST_PATH", path)
            loaded = capability.load_pinned_hermes_source_manifest()
        assert loaded.source_identity is None
        assert loaded.observations is None
        assert capability.evaluate_hermes_capability(
            loaded.observations,
            loaded.source_identity,
        ).verdict is capability.CapabilityVerdict.INVALID_EVIDENCE


def test_safe_evidence_rejects_forged_well_typed_cross_field_evaluations():
    import podcast_ingest_core.hermes_runtime_capability as capability

    actual_manifest = capability.load_pinned_hermes_source_manifest()
    blocked = capability.evaluate_hermes_capability(
        actual_manifest.observations,
        actual_manifest.source_identity,
    )
    synthetic = capability.evaluate_synthetic_hermes_capability()
    invalid = capability.evaluate_hermes_capability(
        (object(),),
        capability.canonical_source_identity(),
    )
    all_present_states = tuple(
        capability.ObservationState.PRESENT
        for _ in capability.CapabilityRequirement
    )
    forged = (
        replace(blocked, source_identity_verified=False),
        replace(blocked, coverage_complete=True),
        replace(blocked, states=all_present_states),
        replace(
            blocked,
            states=(
                capability.ObservationState.INVALID,
                capability.ObservationState.MISSING,
            )
            + all_present_states[2:],
        ),
        replace(blocked, failure=capability.FailureCode.NONE),
        replace(synthetic, synthetic_checks=capability.SyntheticChecks()),
        replace(invalid, failure=capability.FailureCode.NONE),
        capability.CapabilityEvaluation(
            capability.CapabilityMode.REJECTED,
            capability.CapabilityVerdict.INVALID_EVIDENCE,
            capability.FailureCode.NONE,
            False,
            False,
            tuple(
                capability.ObservationState.INVALID
                for _ in capability.CapabilityRequirement
            ),
        ),
    )

    for evaluation in forged:
        safe = capability.build_capability_evidence(evaluation)
        assert safe["ok"] is False
        assert safe["verdict"] == "INVALID_EVIDENCE"
        assert safe["terminal_status"] == "invalid_evidence"
        assert safe["failure_code"] == "invalid_evidence"
        assert 0 <= safe["missing_requirement_count"] <= len(
            capability.CapabilityRequirement
        )


def test_pinned_evaluation_rejects_a_blocked_terminal_with_forged_pass_observations(monkeypatch):
    import podcast_ingest_core.hermes_runtime_capability as capability

    forged_manifest = capability.PinnedSourceManifest(
        capability.canonical_source_identity(),
        _all_present(capability),
        capability.FailureCode.BLOCKED_CAPABILITY.value,
    )
    monkeypatch.setattr(
        capability,
        "load_pinned_hermes_source_manifest",
        lambda: forged_manifest,
    )

    evaluation = capability.evaluate_pinned_hermes_capability()
    safe = capability.build_capability_evidence(evaluation)

    assert evaluation.verdict is capability.CapabilityVerdict.INVALID_EVIDENCE
    assert safe["ok"] is False
    assert safe["verdict"] == "INVALID_EVIDENCE"
    assert safe["terminal_status"] == "invalid_evidence"
