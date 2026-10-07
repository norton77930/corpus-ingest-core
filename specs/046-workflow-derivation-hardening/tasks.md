# Tasks: 046 Workflow Derivation Publication Hardening

**Status**: T001-T026 complete; converge found no additional tasks.
**Input**: spec.md, plan.md, contracts/derivation-safety.md and quickstart.md.
**Tests**: TDD required. One active writer.

## Phase 1: Setup

- [x] T001 Record current status and SHA256 of protected existing files; run selected prerequisites and baseline from quickstart.md; write evidence in specs/046-workflow-derivation-hardening/implementation-log.md. [FR-013,SC-005; start]
- [x] T002 Read spec/plan/contracts and check implementation authorization; record intended error/context compatibility changes and no live operations in specs/046-workflow-derivation-hardening/implementation-log.md. [FR-001,FR-003,FR-010,FR-013; depends T001]

## Phase 2: Foundational contracts

- [x] T003 Characterize existing Core/MCP success, force/reuse and report behavior in tests/test_workflow_derivation.py and tests/test_mcp_workflow_derivation.py; do not weaken existing guards. [FR-001,FR-005,FR-009,SC-004; depends T002]
- [x] T004 RED finite state inheritance/message tests in new tests/test_workflow_derivation_safety.py, then add WorkflowDerivationStateError and fixed map in src/corpus_ingest_core/errors.py. [FR-008,FR-012; depends T003]

## Phase 3: US1 - Refuse unsafe state

Independent result: safe-state refusal matrix passes with zero mutations/provider calls.

- [x] T005 [US1] RED invalid-ID and canonical metadata tests with read/provider tripwires in tests/test_workflow_derivation_safety.py (C01-C02). [FR-002,FR-012,SC-001; depends T004]
- [x] T006 [US1] Implement local explicit identity and bounded canonical metadata resolution in src/corpus_ingest_core/workflow_derivation.py; use existing public helpers and rerun T005. [FR-002,FR-003; depends T005]
- [x] T007 [US1] RED all recovery suffix/type/mode/force/generation/reuse combinations and lstat failures in tests/test_workflow_derivation_safety.py, asserting untouched bytes (C03-C04). [FR-004,FR-012,SC-001; depends T006]
- [x] T008 [US1] Implement fail-closed recovery checks before preview/reuse/provider and before staging in src/corpus_ingest_core/workflow_derivation.py; remove automatic recovery of pre-existing entries; rerun T007. [FR-004,FR-007; depends T007]
- [x] T009 [US1] RED managed/context/report path, nested/special/reparse/listing and bounded-read cases (including raw parent traversal, drive-relative and device paths before normalization) in tests/test_workflow_derivation_safety.py; native symlink cases may skip only on OSError (C05-C06). [FR-003,FR-012,SC-001; depends T008]
- [x] T010 [US1] Implement scoped no-follow validation and context policy in src/corpus_ingest_core/workflow_derivation.py without changing shared helpers; rerun all US1 checks and existing prerequisite tests. [FR-002,FR-003,FR-004,FR-005; depends T009]

## Phase 4: US2 - Preserve pair publication and truthful failure states

Independent result: exact byte preservation and every publication fault outcome verified.

- [x] T011 [US2] RED generation/force/reuse byte snapshots for CRLF/LF/BOM/binary/large extras and partial pairs in tests/test_workflow_derivation_safety.py (C07-C09). [FR-005,FR-006,FR-012,SC-002; depends T010]
- [x] T012 [US2] Implement validated full-directory staging with streamed non-pair bytes in src/corpus_ingest_core/workflow_derivation.py; preserve generation/reuse/ack rules; rerun T011. [FR-005,FR-006; depends T011]
- [x] T013 [US2] RED copy/write/backup rename/publish rename/rollback/collision/listed-disappearance failure cases in tests/test_workflow_derivation_safety.py (C10-C12,C15); retain old-tree byte assertions. [FR-006,FR-007,FR-008,FR-012,SC-003; depends T012]
- [x] T014 [US2] Implement explicit created_staging/moved/committed ownership and bounded rollback in src/corpus_ingest_core/workflow_derivation.py; update only the intended generic exception expectation and copy seam in tests/test_workflow_derivation.py; rerun T013. [FR-007,FR-008,FR-013; depends T013]
- [x] T015 [US2] RED postcommit cleanup stat/type/delete and generated/reused report failures through actual write_part_staged_report_pair failure in tests/test_workflow_derivation_safety.py (C13-C14). [FR-008,FR-009,FR-012,SC-003; depends T014]
- [x] T016 [US2] Implement committed cleanup and report failure distinctions at the existing wrapper catch or by handling wrapped WorkflowDerivationError in src/corpus_ingest_core/workflow_derivation.py, leaving shared report protocol unchanged; rerun T015 plus all derivation Core/profile tests. [FR-007,FR-008,FR-009; depends T015]

## Phase 5: US3 - Safe public errors and operator guidance

Independent result: finite public errors without leaked markers; approval/stop contracts preserved.

- [x] T017 [US3] RED both MCP branches for all fixed categories, mutated exception args, unknown reason/class and synthetic sensitive text in tests/test_mcp_workflow_derivation.py (C16). [FR-010,FR-012,SC-004; depends T016]
- [x] T018 [US3] Implement one fixed-error mapper and one Core delegation per mode in src/corpus_ingest_core/mcp_tools_workflow_derivation.py; preserve success/warnings/fields and correct conditional LLM risk text; rerun T017 and existing MCP tests. [FR-001,FR-009,FR-010; depends T017]
- [x] T019 [US3] RED derivation instruction/fixed-outcome oracle updates in tests/test_workflow_derivation_bundle_skill.py and tests/test_learning_workflow_skill_contracts.py (C18); keep lecture cases and consent rules unchanged. [FR-011,FR-012; depends T018]
- [x] T020 [US3] Update .agents/skills/workflow-derivation-bundle/SKILL.md and affected tests/fixtures/learning_workflow_skill_cases.json cases for fixed states/pre-existing recovery refusal; rerun T019 and new MCP checks. [FR-008,FR-010,FR-011,SC-004; depends T019]

## Phase 6: Integration and closeout

- [x] T021 Update current .agents/skills/README.md, docs/mcp-usage.md, docs/agent-handoff.md, docs/verification-matrix.md and specs/README.md; replace superseded legacy claims but preserve 044/045 historical evidence. [FR-011,FR-013; depends T020]
- [x] T022 Run all quickstart targeted sets including Tool26/registry/facade/setup/report/path/ack/cache/secret/docs guards; record exact results/skips in specs/046-workflow-derivation-hardening/implementation-log.md (C17). [FR-001,FR-012,FR-013,SC-005; depends T021]
- [x] T023 Run full pytest, compileall and diff check with a fresh short basetemp; record commands/results and compare protected file hashes in specs/046-workflow-derivation-hardening/implementation-log.md. [FR-012,FR-013,SC-005; depends T022]
- [x] T024 Review US1-US3/FR/SC acceptance separately from constitution and scope; record evidence/limits and any read-only reviewer findings in specs/046-workflow-derivation-hardening/implementation-log.md. [FR-001,FR-012,FR-013,SC-001,SC-002,SC-003,SC-004,SC-005; depends T023]
- [x] T025 Run speckit-converge; append only real missing work to specs/046-workflow-derivation-hardening/tasks.md, complete it through RED/GREEN and rerun affected checks. [FR-012,FR-013,SC-005; depends T024]
- [x] T026 Update specs/046-workflow-derivation-hardening/spec.md, tasks.md, implementation-log.md and specs/README.md with actual completion; report no unauthorized live calls/branch/commit/deployment. [FR-013,SC-005; depends T025]

## Dependencies and Parallel Opportunities

T001-T004 -> US1 T005-T010 -> US2 T011-T016 -> US3 T017-T020 -> T021-T026. One writer; no [P] write tasks. A read-only reviewer can inspect the completed US1 contract while the writer prepares US2, but must not edit files or run competing filesystem tests. Each RED precedes its paired GREEN.

## Implementation Strategy

US1 is the first independently useful refusal layer; it is not complete046. Complete US2 publication and US3 public-error handling before release. Do not remove assertions merely because the new implementation uses a different private seam. Source freshness, all-in-one workflows and stronger report atomicity remain excluded.

## Requirement Traceability

| Requirement | Tasks |
| --- | --- |
| FR-001 | T002, T003, T018, T022, T024 |
| FR-002 | T005, T006, T010 |
| FR-003 | T002, T006, T009, T010 |
| FR-004 | T007, T008, T010 |
| FR-005 | T003, T010, T011, T012 |
| FR-006 | T011, T012, T013 |
| FR-007 | T008, T013, T014, T016 |
| FR-008 | T004, T013, T014, T015, T016, T020 |
| FR-009 | T003, T015, T016, T018 |
| FR-010 | T002, T017, T018, T020 |
| FR-011 | T019, T020, T021 |
| FR-012 | T004, T005, T007, T009, T011, T013, T015, T017, T019, T022, T023, T024, T025 |
| FR-013 | T001, T002, T014, T021, T022, T023, T024, T025, T026 |
| SC-001 | T005, T007, T009, T024 |
| SC-002 | T011, T024 |
| SC-003 | T013, T015, T024 |
| SC-004 | T003, T017, T020, T024 |
| SC-005 | T001, T022, T023, T024, T025, T026 |
