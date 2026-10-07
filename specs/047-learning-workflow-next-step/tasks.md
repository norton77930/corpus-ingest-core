# Tasks: Learning Workflow Next Step

Status: implemented and offline-verified on 2026-10-03; T001-T018 complete, converge adds no tasks. One active writer. Do not commit, branch, create worktrees, deploy, read .env or call real providers. Approved implementation must preserve the starting dirty tree.

## Phase 1 - Setup

- [x] T001 Record current scoped hashes and relevant baseline tests in `specs/047-learning-workflow-next-step/implementation-log.md`; confirm the live registry still has 26 and protect 044-046 files. FR-008, FR-010.
- [x] T002 Add focused identity/invalid-input and zero-child-access failing cases in `tests/test_learning_workflow_next_step.py`, following `tests/conftest.py` tmp_data_dirs. FR-001, FR-006.

## Phase 2 - Foundation

- [x] T003 Implement only validated identity, local result/error types and finite result construction in `src/corpus_ingest_core/learning_workflow_next_step.py`; rerun T002. FR-001, FR-007.
- [x] T004 Add failing malformed preview/mode/identity/list/reuse and private-sentinel tests in `tests/test_learning_workflow_next_step.py`; define call spies for all forbidden side effects. FR-006, FR-007, FR-009.
- [x] T005 Implement preview shape validation and fixed exception mapping in `src/corpus_ingest_core/learning_workflow_next_step.py`; no private runner helpers or filesystem reads from returned paths. FR-004, FR-007, FR-009.

## Phase 3 - US1: Lecture decision (P1)

Goal: one correct lecture-generation/cover action or lecture blocker. Independent test: only the lecture preview runs and nothing is written.

- [x] T006 [US1] Add RED generation, cover-only, partial lecture/source/profile refusal and exact false-flag/short-circuit checks in `tests/test_learning_workflow_next_step.py`. FR-002, FR-004, FR-005.
- [x] T007 [US1] Implement lecture-first composition using public runner/projection in `src/corpus_ingest_core/learning_workflow_next_step.py`, with suggested_call as data only; rerun US1 checks. FR-002, FR-005, FR-006.
- [x] T008 [US1] Add isolated real-preview fixtures for recovery/unsafe/conflict and generic lecture blockers in `tests/test_learning_workflow_next_step.py`; verify byte snapshots and unchanged existing runner diagnostics. FR-004, FR-006, FR-010.

## Phase 4 - US2: Derivation or completion (P1)

Goal: only lecture reuse permits derivation evaluation. Independent test: pair generation/reuse/context refusal, no false completion or implicit repair.

- [x] T009 [US2] Add RED derivation-generation/reuse, partial pair/context rejection, mismatched bundle directory and unexpected result/exception cases in `tests/test_learning_workflow_next_step.py`. FR-003, FR-004, FR-009.
- [x] T010 [US2] Implement derivation preview composition and bounded complete semantics in `src/corpus_ingest_core/learning_workflow_next_step.py`; rerun US2 cases. FR-003, FR-005, FR-007, FR-009.
- [x] T011 [US2] Add real-preview cases including empty/stale pair reuse, no-currentness claim, context failure despite existing pair, sequential-state drift and forbidden-call/byte preservation checks in `tests/test_learning_workflow_next_step.py`. FR-003, FR-006, FR-007, FR-010.

## Phase 5 - US3: MCP query (P2)

Goal: one new read-query surface with frozen existing tool contracts. Independent test: Tool27 delegates once and accepts only two required identifiers.

- [x] T012 [US3] Add RED schema, success/blocked/error envelope, exact delegation and private-sentinel cases in `tests/test_mcp_learning_workflow_next_step.py`. FR-001, FR-007, FR-008, FR-009.
- [x] T013 [US3] Add thin `src/corpus_ingest_core/mcp_tools_learning_workflow.py` and append its import/re-export to `src/corpus_ingest_core/mcp_server.py`; no execution logic in MCP. FR-008.
- [x] T014 [US3] Update append-only/read-query/count assertions in `tests/test_mcp_tool_registry_contract.py`, `tests/test_mcp_server_facade_boundary.py`, `tests/test_mcp_setup_validation.py`, `tests/test_console_entry_points.py` and `scripts/validate_mcp_setup.py`; preserve exact first26 definitions. FR-008, FR-010.

## Phase 6 - Documentation and closeout

- [x] T015 Update current tool listings/counts in `docs/api.md`, `docs/mcp-usage.md`, client setup/readiness/install docs, `docs/agent-handoff.md`, `docs/ai-development-framework.md`, `docs/architecture.md` and `docs/verification-matrix.md`; document separate preview/approval and generic blockers. Preserve historical counts and 045 Skill protocols. FR-005, FR-007, FR-008, FR-010.
- [x] T016 Run targeted new Core/MCP plus 044-046/045/registry/facade/setup/console/secret/ack/cache/docs suites and standard full pytest, compileall and diff checks from `specs/047-learning-workflow-next-step/quickstart.md`; record actual failures/skips/results. FR-006, FR-008, FR-010.
- [x] T017 Review requested behavior and engineering standards separately against `specs/047-learning-workflow-next-step/contracts/next-step.md`; resolve concrete findings with RED/GREEN. Record review limitations in `specs/047-learning-workflow-next-step/implementation-log.md`. FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010.
- [x] T018 Run Spec Kit converge; append only demonstrated gaps in `specs/047-learning-workflow-next-step/tasks.md`. Then update package status, `specs/README.md`, AGENTS marker and `tests/test_spec_047_learning_next_step_docs.py` lifecycle assertions with actual completion evidence. FR-010.

## Dependencies and execution strategy

T001 -> T002 -> T003 -> T004 -> T005 -> US1(T006-T008) -> US2(T009-T011) -> US3(T012-T014) -> T015-T018. Within each behavior slice, capture RED before production changes and GREEN after; T008/T011 may characterize existing safe behavior already green and must be labeled honestly.

MVP is US1 at Core level, but the approved full feature is not complete until US2/US3 and closeout pass. US2 depends on US1 reuse projection; US3 depends on complete Core contract. No parallel writers or artificial parallel labels. Optional independent read-only review may inspect each completed story while the writer proceeds; reviewers do not change fixtures or run shared-state mutations. T016 full verification is repeated only after material fixes justify it.
