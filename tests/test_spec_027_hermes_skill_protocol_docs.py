"""SPEC 027 offline Hermes Skill routing contract documentation guards."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "027-hermes-skill-routing-contracts"
STATUS = (
    "Spec 027 contract layer is complete (offline assurance only); actual Hermes "
    "runtime routing is BLOCKED/not_evaluated and is not a runtime PASS."
)


def test_spec_027_package_and_governed_docs_distinguish_contracts_from_runtime_evidence():
    for relative_path in (
        "spec.md",
        "plan.md",
        "research.md",
        "data-model.md",
        "tasks.md",
        "contracts/skill-routing-and-protocol.md",
        "contracts/safe-contract-evidence.md",
        "checklists/requirements.md",
        "checklists/safety.md",
    ):
        assert (FEATURE / relative_path).is_file()

    package_docs = "\n".join(
        (FEATURE / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            "spec.md",
            "data-model.md",
            "tasks.md",
            "contracts/skill-routing-and-protocol.md",
            "contracts/safe-contract-evidence.md",
            "checklists/requirements.md",
            "checklists/safety.md",
        )
    )
    for phrase in (
        "clarification_required",
        "run_corpus_episode_completion_workflow",
        "run_corpus_latest_episode_deterministic_workflow",
        "run_latest_episode_verified_research_report_workflow",
        "run_episode_verified_research_report_workflow",
        "no raw natural language",
        "exact 21-tool registry of its time",
        "outside this routed",
        "MANAGED_SKILLS",
        "managed_allowlist_ok",
        "hermes_runtime_observation",
        "synthetic_protocols_pass",
        "unknown_event_fail_closed",
        "non_boolean_fail_closed",
        "PreviewOutcome",
        "not_evaluated",
        "exact verified `Skill`",
        "Approval.EXACT_REFERENCE",
        "route Skill, verified sequence Skill, and call budget",
        "closed shape for every 016 event slot",
        "malformed `SkillArtifact.skill`",
        "registry_tool_names",
        "static source extraction",
        "per-Skill prohibition clauses",
        "one canonical high-level workflow tool",
        "0 <= observed_call_count <= call_budget",
        "016=2, 017=1, 018=2, and 019=1 or 2",
        "_registry_tool_names_from_source()",
        "exactly equal to the safe extracted set",
        "Python `ast`",
        "`FunctionDef` and `AsyncFunctionDef`",
        "ambiguous decorator shape",
        "SyntaxError/OSError",
        "module-body top-level",
        "alias assignment",
        "single `name=`",
        "duplicate registry names",
        "dynamic/non-string `name`",
        "cross-source duplicate",
        "definition count",
        "indirect `.tool` decorator",
        "`mcp`-referencing decorator",
    ):
        assert phrase in package_docs

    for relative_path in (
        "specs/README.md",
        "docs/architecture.md",
        "docs/mcp-readiness.md",
        "docs/roadmap.md",
        "docs/verification-matrix.md",
        "docs/agent-handoff.md",
        "deploy/hermes/README.md",
        "specs/026-hermes-mcp-integration/quickstart.md",
    ):
        assert STATUS in (ROOT / relative_path).read_text(encoding="utf-8")

    spec_026 = (ROOT / "specs/026-hermes-mcp-integration/spec.md").read_text(encoding="utf-8")
    assert "Spec 027 amendment pointer" in spec_026
    assert "C6 is PASS-current" in spec_026
