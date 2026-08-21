"""Spec 028 documentation and offline-boundary guards."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "028-hermes-runtime-skill-routing-observation"
STATUS = (
    "Spec 028 capability gate is complete and correctly terminates at "
    "BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill "
    "sync, hooks, collector, inference, or runtime observation was performed. "
    "C6 remains PASS-current and was not rerun; actual Hermes Skill routing "
    "remains BLOCKED/not_run."
)
R2_SUCCESSOR_POLICY = (
    "Any future work involving Hermes upgrade, Skill sync, hooks/plugin/collector, "
    "Docker/MCP/network, live config/session access, inference, or runtime "
    "observation must establish and receive separate approval for a new R2 "
    "successor spec; Spec 028 does not automatically authorize it."
)


def test_spec_028_package_records_the_pinned_capability_gate_without_raw_runtime_material():
    package_paths = (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "tasks.md",
        "contracts/capability-gate.md",
        "contracts/safe-capability-evidence.md",
        "contracts/hermes-v2026.8.3-source-manifest.json",
        "checklists/requirements.md",
        "checklists/safety.md",
    )
    for relative_path in package_paths:
        assert (FEATURE / relative_path).is_file()

    content = "\n".join(
        (FEATURE / relative_path).read_text(encoding="utf-8")
        for relative_path in package_paths
    )
    for phrase in (
        STATUS,
        R2_SUCCESSOR_POLICY,
        "NousResearch/hermes-agent",
        "7de39e700d2c329e15d32eb0b96e2f7cdd9fbdb2",
        "3c27eb6234bf91b8ceee9e9071591b31e9b148cb",
        "website/docs/user-guide/features/hooks.md",
        "be8b9c0caa2792a24bb34dba9400400acdf91eaa",
        "canonical Skill identity",
        "Skill-to-tool linkage",
        "fallback used",
        "fallback not-used",
        "guaranteed Skill/tool correlation",
        "official no-side-effect positive control",
        "PASS_CANONICAL_COVERAGE",
        "BLOCKED_CAPABILITY",
        "live_actions_authorized",
        "hermes_runtime_observation",
        "c6_status",
        "fixed safe schema",
        "spec_id",
        "terminal_status",
        "runtime_target",
        "release_tag",
        "missing_requirement_count",
        "exact top-level key set",
        "hermes-v2026.8.3-source-manifest-v1",
        "unknown, missing, or schema drift",
        "forged well-typed",
        "only present, missing, or ambiguous states",
        "no raw official page",
        "no hook payload",
        "no example prompt",
        "no arguments or results",
        "C6 remains PASS-current and was not rerun",
    ):
        assert phrase in content


def test_governed_docs_and_predecessors_point_to_spec_028_without_reopening_c6():
    for relative_path in (
        "specs/README.md",
        "docs/architecture.md",
        "docs/mcp-readiness.md",
        "docs/roadmap.md",
        "docs/verification-matrix.md",
        "docs/agent-handoff.md",
        "specs/026-hermes-mcp-integration/spec.md",
        "specs/027-hermes-skill-routing-contracts/spec.md",
    ):
        assert STATUS in (ROOT / relative_path).read_text(encoding="utf-8")

    spec_026 = (ROOT / "specs/026-hermes-mcp-integration/spec.md").read_text(encoding="utf-8")
    spec_027 = (ROOT / "specs/027-hermes-skill-routing-contracts/spec.md").read_text(encoding="utf-8")
    for relative_path in (
        "specs/028-hermes-runtime-skill-routing-observation/spec.md",
        "specs/028-hermes-runtime-skill-routing-observation/plan.md",
        "specs/README.md",
    ):
        assert R2_SUCCESSOR_POLICY in (ROOT / relative_path).read_text(encoding="utf-8")
    assert "Spec 028 successor pointer" in spec_026
    assert "Spec 028 successor pointer" in spec_027
    assert "C6 is PASS-current" in spec_026

    c6_validator = (ROOT / "scripts/validate_hermes_integration.py").read_text(encoding="utf-8")
    assert "hermes_runtime_capability" not in c6_validator
