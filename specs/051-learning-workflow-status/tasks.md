# Tasks: Learning workflow status
Input:spec.md/plan.md/research.md/data-model.md/contracts/status.md. One writer; all behavior uses RED/GREEN. User requested direct implementation after planning.

## Phase1 Setup
- [x] T001 Record baseline697 files,30 contracts and approved scope in specs/051-learning-workflow-status/implementation-log.md (FR-001,FR-007,FR-009).

## Phase2 US2 - recovery gate
- [x] T002 [US2] Add failing explicit identity/recovery-first/skip/error cases in tests/test_learning_workflow_status.py (FR-001,FR-002,FR-004;SC-002).
- [x] T003 [US2] Implement identity validation and recovery gate in src/corpus_ingest_core/learning_workflow_status.py;run GREEN (FR-001,FR-002,FR-004).

## Phase3 US1 - compact overview
- [x] T004 [US1] Add failing projection/lineage/legacy/custom/stale/conflict/no-leak cases in tests/test_learning_workflow_status.py (FR-003,FR-004,FR-005,FR-006;SC-001).
- [x] T005 [US1] Implement closed metadata projection and deterministic attention summary in learning_workflow_status.py;run GREEN (FR-003,FR-004,FR-005,FR-006).
- [x] T006 [US1] Verify real temporary integrations and zero writes/provider/environment/network/report/cache calls in tests/test_learning_workflow_status.py (FR-002,FR-006,FR-007;SC-002).

## Phase4 US3 - MCP and compatibility
- [x] T007 [US3] Add failing thin-wrapper/signature/fixed-error cases in tests/test_mcp_learning_workflow_status.py (FR-001,FR-008;SC-003).
- [x] T008 [US3] Implement src/corpus_ingest_core/mcp_tools_learning_status.py;run GREEN (FR-008).
- [x] T009 [US3] Add failing31-tool/count/facade/docs guards in tests/test_mcp_tool_registry_contract.py and related count/facade files (FR-007,FR-008;SC-003).
- [x] T010 [US3] Append group/re-export to mcp_server.py;update scripts/validate_mcp_setup.py/current docs/count guards;run GREEN (FR-007,FR-008).
- [x] T011 [US3] Run unchanged25-30/Skills regressions and baseline30 signature/order/protected-file audit;record implementation-log.md (FR-006,FR-007,FR-008).

## Phase5 closeout
- [x] T012 Conduct separate fresh read-only behavior/engineering reviews, reproduce/fix concrete findings with RED/GREEN and record implementation-log.md (FR-009).
- [x] T013 Run full pytest,compileall src scripts,git diff --check;record results/skips in implementation-log.md (FR-009;SC-001,SC-002,SC-003,SC-004).
- [x] T014 Run converge051;append/finish gaps and update spec/registry/AGENTS after verification;record workflow-record.md and implementation-log.md (FR-009;SC-004).

## Dependencies and strategy
Setup ->US2 gate ->US1 composition ->US3 MCP ->closeout. US2 independently verifies short-circuit/no queries;US1 uses clear-recovery fixtures;US3 validates public envelope/compatibility. MVP single offline overview. Parallel examples: independent read-only behavior and engineering reviews; no parallel writer tasks. No Git objects.
