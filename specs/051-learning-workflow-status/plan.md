# Implementation Plan: Learning workflow status
Date2026-10-04 | Branch:none | Spec:spec.md
## Summary
New thick Core composes public queries from047-050; thin MCP appends Tool31. Compact closed projections, recovery-first short circuit, deterministic diagnostic attention. User authorized immediate plan+implementation; one writer.
## Technical Context
Python3.11+, existing FastMCP/PyYAML/pytest, local files only via existing queries. No dependencies/storage/schema migration. At most four sequential query calls, each once; underlying safe reads retain existing caps. Public output contains no child suggested_call/path/body/hash/arbitrary warnings. No global scan, retry or atomic snapshot claim.
## Constitution Check
I scoped local metadata; II thickCore/thinMCP; III no new side effects; IV no provider/env/secrets; V non_atomic and explicit freshness limits; VI no advice; VII no APIs; VIII no cache writes; IX TDD/current gates/reviews. PASS before/after design, constitution unchanged. User instructions override optional design/commit/branch approval ceremony; no Git objects.
## Phase0 Research
Existing public query contracts and finite states read from code; choices in research.md, no unknown technology questions.
## Phase1 Design
learning_workflow_status.py imports public storage/learning_workflow_next_step/study_guide_bundle/workflow_derivation/learning_bundle_recovery and pure lineage CHANGED_ROLES. Validates two lexical IDs locally without profile/FS. Recovery query first; unsafe/unknown/gated states never invoke other queries. Clear state calls next-step, lecture lineage, derivation lineage once each. Shape/identity/enum/flags/reason-role coherence checked; exceptions/malformed return fixed blocked section. Only compact fields are projected. Summary status is diagnostic observation, not readiness; no executable suggested_call. See data-model.md/contracts/status.md.
## Planned paths
Create src/corpus_ingest_core/learning_workflow_status.py,mcp_tools_learning_status.py; tests/test_learning_workflow_status.py,test_mcp_learning_workflow_status.py,test_spec_051_learning_status_docs.py; package051. Modify only mcp_server.py last group/re-export, scripts/validate_mcp_setup.py, existing count/facade guards, current docs/README/AGENTS/spec registry. Protect all priorCore/Skills/044-050 packages, secure helpers/codecs/generators, config/pyproject/data/cache/history. Snapshot against pre051 dirty baseline.
## Delivery phases
Setup ->US2 gate/identity ->US1 compact composition ->US3 MCP/registry/docs ->targeted/fresh read-only reviews/full/converge. No parallel writers. Runtime implementation staged by focused RED then GREEN.
## Complexity Tracking
No shared safety refactor or duplicate filesystem inspection. No new action planner. Recovery summary excludes locations; detail remains Tool30. Inherited bounds apply to existing queries; non_atomic warning covers inter-query drift. Ordinary lineage not_generated is pending, not an attention signal unless inconsistent with preview mode.
