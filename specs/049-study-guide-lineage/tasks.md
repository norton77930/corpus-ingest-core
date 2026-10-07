# Tasks: SPEC049 Study-guide lineage

One writer, read-only reviewers. Behavior changes require RED then GREEN.

## Phase1: Setup
- [x] T001 Record baseline and28 contracts in implementation-log.md (FR-012).

## Phase2: Foundation
- [x] T002 Add focused failing codec checks in tests/test_study_guide_lineage.py (FR-001, FR-007).
- [x] T003 Implement src/corpus_ingest_core/study_guide_lineage.py; run codec GREEN (FR-001, FR-007).

## Phase3: US1 - generation
- [x] T004 [US1] Add failing preview/actual-consumption/preservation/collision checks in tests/test_study_guide_lineage.py (FR-001, FR-002, FR-003, FR-004, FR-005).
- [x] T005 [US1] Extend models.py, study_guide_bundle.py and mcp_tools_study_guide.py; run GREEN (FR-001, FR-002, FR-003, FR-004, FR-005).
- [x] T006 [US1] Add failure-injection and cross-stage preservation checks in tests/test_study_guide_lineage.py; fix only evidenced failures (FR-002, FR-003, FR-005; SC-001, SC-003).

## Phase4: US2 - inspection
- [x] T007 [US2] Add failing state/role/safety/limits matrix in tests/test_study_guide_lineage.py (FR-006, FR-007, FR-008, FR-009; SC-002).
- [x] T008 [US2] Implement Core inspect_study_guide_lineage in study_guide_bundle.py; run GREEN (FR-006, FR-007, FR-008, FR-009).
- [x] T009 [US2] Add failing delegation/signature/sanitization checks in tests/test_mcp_study_guide_lineage.py (FR-006, FR-009).
- [x] T010 [US2] Implement mcp_tools_study_guide_lineage.py thin wrapper; run GREEN (FR-006, FR-009).

## Phase5: US3 - compatibility
- [x] T011 [US3] Add failing Skill metadata/ownership oracle checks in tests/test_study_guide_bundle_skill.py (FR-004, FR-010).
- [x] T012 [US3] Update .agents/skills/study-guide-bundle/SKILL.md and tests/fixtures/study_guide_lineage_skill_cases.json; run GREEN (FR-004, FR-010).
- [x] T013 [US3] Add failing29 registry/facade/setup/docs checks; append group/re-export in mcp_server.py and update current docs and scripts/validate_mcp_setup.py (FR-006, FR-011; SC-004).
- [x] T014 [US3] Run unchanged Tool25/27/28 and lecture reuse/cover regressions; compare protected baseline paths in implementation-log.md (FR-005, FR-010, FR-011).

## Phase6: Closeout
- [x] T015 Run separate read-only behavior and engineering reviews; resolve findings via TDD, record in implementation-log.md (FR-012).
- [x] T016 Run full pytest, compileall src scripts, git diff --check; record exact evidence in implementation-log.md (FR-012; SC-001, SC-002, SC-003, SC-004).
- [x] T017 Run converge against all FR/SC/stories, append and complete concrete gaps; update specs/README.md and workflow-record.md only after verified (FR-012).

## Dependencies and independent delivery
Foundation -> US1 -> US2 -> US3 -> closeout. US1 fake generation validates metadata separately; US2 state fixtures are independently inspectable; US3 guards validate compatibility and consent. MVP: tracked lecture plus read-only query. Parallel examples: read-only generation reviewer and read-only query reviewer; never concurrent writers. All scope ships together with Skill disclosure.
