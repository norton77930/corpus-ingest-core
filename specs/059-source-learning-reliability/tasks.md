# Tasks: Source learning reliability and note quality

## Phase 1: Setup and requirement review

- [x] T001 Review constitution v1.0.1 and create requirements/clarifications in specs/059-source-learning-reliability/spec.md (FR-001–012).
- [x] T002 Produce plan, research, data model and contracts in specs/059-source-learning-reliability/plan.md; verify both requirements checklists.
- [x] T003 Analyze spec/plan/tasks coverage with explicit SPECIFY_FEATURE_DIRECTORY and update AGENTS.md current feature; no branch/commit.

## Phase 2: Foundation and focused RED

- [x] T004 Add failing safe diagnostic and contract/mutation checks in tests/test_source_learning_reliability.py (FR-001–009, FR-012).
- [x] T005 Add long-source default and POSIX fixture failing checks in tests/test_source_learning_reliability.py (FR-010–011).
- [x] T006 Add package/discovery requirement coverage tests in tests/test_spec_059_source_learning_docs.py (FR-012).

## Phase 3: US1 bounded recovery

- [x] T007 [US1] Specify sequential verbatim copying and one-recovery contract in .agents/skills/source-content-qa/SKILL.md and references/response-contract.md (FR-001–005).
- [x] T008 [US1] Permit only the QA exception in .agents/skills/source-learning-entry/SKILL.md/references/entry-protocol.md; preserve preparation no-retry (FR-003–005).
- [x] T009 [US1] Replace source_changed restart oracle/guard in tests/fixtures/source_content_qa_dialogues.json and tests/test_source_content_qa_skill.py (FR-003).
- [x] T010 [US1] Exercise synthetic real-tool recovery/second-error/drift/budget/no-side-effect sequences and read-only Skill pressure checks in tests/test_source_learning_reliability.py (FR-001–005, FR-012).

## Phase 4: US2 source routing and diagnostics

- [x] T011 [US2] Add finite Core validation diagnoses in src/corpus_ingest_core/source_content_query.py (FR-006).
- [x] T012 [US2] Map known reason/diagnosis pairs to safe fixed messages in src/corpus_ingest_core/mcp_tools_source_content.py (FR-006).
- [x] T013 [US2] Strengthen entry description/body and current routing/install guides in .agents/skills/source-learning-entry/SKILL.md, docs/mcp-usage.md and docs/install-and-porting.md (FR-007).

## Phase 5: US3 source-grounded notes

- [x] T014 [US3] Add neutral speaker, concrete example and conditional section/AI isolation rules in .agents/skills/source-content-qa/references/learning-notes-template.md and response-contract.md (FR-008–009).
- [x] T015 [US3] Verify quality contract guards/pressure scenarios in tests/test_source_learning_reliability.py; distinguish offline from real Hermes (FR-012).

## Phase 6: US4 long-source portable verification

- [x] T016 [US4] Share default120000 across src/corpus_ingest_core/learning_mcp_acceptance.py and scripts/verify_learning_mcp.py; preserve lower budgets/no-retry (FR-010).
- [x] T017 [US4] Use tmp_path in tests/test_mcp_study_guide_bundle.py and validate POSIX path interpretation (FR-011).
- [x] T018 [US4] Document current default/long-source bounds in specs/058-learning-mcp-acceptance/contracts/verification.md and specs/059-source-learning-reliability/quickstart.md (FR-010).

## Phase 7: Cross-cutting verification

- [x] T019 Update specs/README.md, .agents/skills/README.md and docs/verification-matrix.md discovery/verification references (FR-012).
- [x] T020 Run focused and relevant regression checks from specs/059-source-learning-reliability/quickstart.md.
- [x] T021 Run full pytest, compileall src scripts and git diff --check; inspect changed paths for prohibited artifacts.
- [x] T022 Converge against specs/059-source-learning-reliability/spec.md/plan.md/tasks.md; report separate pending actual Hermes acceptance.

## Dependencies and execution

T001–003 -> T004–006 -> US1/US2 -> US3/US4 -> T019–022. Tests precede behavior edits. US3/US4 are independent review opportunities after shared requirements, but all writes execute sequentially in this workspace. No parallel writers or new production retry runtime. MVP is US1+safe diagnostics; authorized scope completes all four stories. Real-host replay/discovery is an operator acceptance scenario, not a falsely completed build task.

## Requirement coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T004, T007, T010 |
| FR-002 | T004, T007, T010 |
| FR-003 | T007, T008, T009, T010 |
| FR-004 | T008, T010 |
| FR-005 | T007, T008, T010 |
| FR-006 | T004, T011, T012 |
| FR-007 | T004, T013 |
| FR-008 | T014, T015 |
| FR-009 | T014, T015 |
| FR-010 | T005, T016, T018 |
| FR-011 | T005, T017 |
| FR-012 | T006, T010, T015, T019–T022 |
