# Tasks: SPEC048 Workflow Derivation Lineage

User-authorized implementation backlog; checks record completed evidence. One writer; no branch/worktree/commit or real provider. Each behavior slice requires a focused RED before implementation and GREEN afterward.

## Phase 1: Setup
- [x] T001 Record dirty-tree baseline and current27 registry/signatures in specs/048-workflow-derivation-lineage/implementation-log.md; read governance and select package explicitly (FR-012).
- [x] T002 Add failing strict-schema/hash/limit cases in tests/test_workflow_derivation_lineage.py (FR-001, FR-002, FR-007).

## Phase 2: Foundation
- [x] T003 Implement pure canonical hashing/strict bounded receipt codec and finite values in src/corpus_ingest_core/workflow_derivation_lineage.py; run T002 GREEN (FR-001, FR-002, FR-007).
- [x] T004 Add failing additive default-field/preview generation-reuse checks in tests/test_mcp_workflow_derivation.py and tests/test_workflow_derivation_lineage.py (FR-004, FR-005).

## Phase 3: US1 - Generation provenance (P1)
Goal: confirmed generation publishes a matching pair/receipt. Independent acceptance: fake-provider fixture, staged bytes and publication fault matrix.
- [x] T005 Extend src/corpus_ingest_core/models.py and mcp_tools_workflow_derivation.py with metadata_writes; preserve pair fields and zero-side-effect preview, run T004 GREEN (FR-004).
- [x] T006 Add failing actual-consumption, Windows bytes, effective-context and provider-time source-mutation cases in tests/test_workflow_derivation_lineage.py (FR-001, FR-002, FR-008, FR-011; SC-001).
- [x] T007 Capture consumed lecture/tool/message digests before provider and hash staged outputs in src/corpus_ingest_core/workflow_derivation.py; run T006 GREEN (FR-001, FR-002, FR-008, FR-011).
- [x] T008 Add failing reserved-name collision, recognized force replacement, extra-byte/reuse preservation and pair/receipt/hash/rename/rollback/cleanup/report-failure cases in tests/test_workflow_derivation_lineage.py, with existing tests/test_workflow_derivation_safety.py regression retained (FR-003, FR-005, FR-007, FR-011; SC-003).
- [x] T009 Implement receipt ownership preflight and same-directory staging/publication in src/corpus_ingest_core/workflow_derivation.py; retain typed failures and run T008 GREEN (FR-003, FR-005, FR-007, FR-011).

## Phase 4: US2 - Read inspection (P1)
Goal: six finite outcomes without mutation. Independent acceptance: table-driven default/custom/legacy fixtures and side-effect tripwires.
- [x] T010 Add failing six-state/precedence/role matrix in tests/test_workflow_derivation_lineage.py, including all missing/oversized/invalid inputs and receipts, duplicate JSON keys, unsafe paths, recovery siblings and custom-context refusal to reopen paths (FR-006, FR-007, FR-008, FR-009; SC-002).
- [x] T011 Implement public inspect_workflow_derivation_lineage in src/corpus_ingest_core/workflow_derivation.py using pure codec and existing safe helpers; run T010 GREEN (FR-006, FR-007, FR-008, FR-009).
- [x] T012 Add failing explicit-identity/signature/private-sentinel/fixed-error/zero-write-network-provider-cache tests in tests/test_mcp_workflow_derivation_lineage.py (FR-006, FR-009, FR-011; SC-002).
- [x] T013 Implement thin Tool28 wrapper in src/corpus_ingest_core/mcp_tools_workflow_lineage.py; run T012 GREEN without changing Tool27 semantics (FR-006, FR-009, FR-011).

## Phase 5: US3 - Approval and compatibility (P2)
Goal: metadata side effect is explicit and existing27 tools retain contracts. Independent acceptance: offline Skill oracle and registry/Tool27 regressions.
- [x] T014 Add failing metadata validation/display/missing-field/force-ack cases in tests/test_workflow_derivation_bundle_skill.py; explicitly cover the narrow046 owned-file exception (FR-004, FR-010).
- [x] T015 Update .agents/skills/workflow-derivation-bundle/SKILL.md and its oracle; preserve one-preview/one-confirm/stop and run T014 GREEN (FR-004, FR-010).
- [x] T016 Add failing append-only28 registry/facade/setup/docs guards and pin first27 slots/signatures in tests/test_mcp_tool_registry_contract.py and related contract tests (FR-010; SC-004).
- [x] T017 Append Tool28 in src/corpus_ingest_core/mcp_server.py; update scripts/validate_mcp_setup.py and current docs/count guards; run T016 GREEN (FR-010; SC-004).
- [x] T018 Run unchanged lecture Skill/Tool26/Tool27 and legacy/preview/reuse regressions; record exact evidence in specs/048-workflow-derivation-lineage/implementation-log.md (FR-005, FR-010, FR-011; SC-004).

## Phase 6: Closeout
- [x] T019 Run targeted integration and failure-injection matrix in tests/test_workflow_derivation_lineage.py, tests/test_workflow_derivation_safety.py and MCP tests; record RED/GREEN and protected-file byte comparisons (FR-001 through FR-012; SC-001 through SC-004).
- [x] T020 Run full pytest, compileall src scripts and git diff --check; record actual commands/results/skip reasons in specs/048-workflow-derivation-lineage/implementation-log.md (FR-012).
- [x] T021 Conduct read-only behavior and engineering reviews separately, resolve concrete issues via failing checks and rerun impacted verification; record review provenance in specs/048-workflow-derivation-lineage/implementation-log.md (FR-012).
- [x] T022 Run Spec Kit converge, append any concrete unmet tasks to this tasks.md, complete and verify them before marking specs/README.md implemented; record limitations/no-deployment status (FR-012).

## Dependencies and delivery
T001 -> T002-T004 -> US1 -> US2 -> US3 -> closeout. Within each phase retain listed order. US1/US2 may be reviewed independently; backend/Skill ship together. Parallel examples: read-only US1 publication review and US2 state-matrix review while the single writer handles US3; no concurrent code writers. MVP is a fixture-proven generation record plus read inspection; no partial production release without approval disclosure. All FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012 are mapped above.
