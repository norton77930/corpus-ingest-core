# Tasks: 045 Study-guide and Workflow Derivation Skills

**Input**: [spec.md](spec.md), [plan.md](plan.md), [protocol](contracts/skill-protocol.md), [quickstart](quickstart.md)
**Status**: T001-T024 complete; converge found no additional tasks
**Tests**: TDD required by constitution and FR-013. One active writer; no parallel writer tasks.

## Phase 1: Setup

- [x] T001 Record current HEAD/status and preserve all 044 work in `specs/045-study-guide-workflow-skills/implementation-log.md`; run official prerequisites with this package selected. [FR-014, SC-005]
- [x] T002 Run existing Skills/MCP/registry/docs baselines from `specs/045-study-guide-workflow-skills/quickstart.md` (exclude new test files until created), recording exact commands/results in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-013, SC-005; depends T001]

## Phase 2: Foundational contract characterization

- [x] T003 Add existing-wrapper characterization in `tests/test_learning_workflow_skill_contracts.py`: actual five parameters, Tool 26 dry-run/LLM/report fields and Tool 25 preview/pair semantics; fake Core or existing isolated fixtures only. Keep registry at 26 and avoid new production helpers. These tests characterize existing behavior and need not be RED. [FR-003/004/009/014, SC-004/005; depends T002]
- [x] T004 Document backend limits and test tiers in `specs/045-study-guide-workflow-skills/implementation-log.md`: Tool 25 legacy recovery/raw errors, both tools' lack of digest pinning, static tests versus live agent execution. Record any real contract mismatch before changing the design; do not fix runtime under this task. [FR-010/012/013, SC-003/005; depends T003]

## Phase 3: US1 - Lecture Skill (P1)

Goal: preview/generate/reuse/cover-only with accurate consent/cost. Independent check: new lecture Skill tests plus existing Tool 26 characterization.

- [x] T005 [US1] RED: create `tests/test_study_guide_bundle_skill.py` for portable frontmatter, own-tool-only binding, P01-P07 order, exact ack pinned to Core constant, explicit IDs/force, matching confirm and generation/reuse/cover-only role rules. Demonstrate failure before creating the Skill. [FR-001/002/003/004/005/006/008/009/013, SC-001/002/004; depends T004]
- [x] T006 [US1] GREEN: create `.agents/skills/study-guide-bundle/SKILL.md` with the complete self-contained P01-P10 protocol, five-parameter boundary, Tool 26 roles/report fields and safe failure outcomes. No executable code fences or runtime reads. Rerun T005. [FR-001/002/003/004/005/006/008/009; depends T005]
- [x] T007 [US1] Add focused instruction regressions to `tests/test_study_guide_bundle_skill.py` for empty ack despite history, 05/06 conflict, recovery refusal, state drift and no automatic derivation; show any missing clause failing before fixing `.agents/skills/study-guide-bundle/SKILL.md`. [FR-005/007/008/010/011/012, SC-002/003/004; depends T006]
- [x] T008 [US1] Run lecture instruction checks plus `tests/test_mcp_study_guide_bundle.py`; record independent US1 results in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-013, SC-001/004/005; depends T007]

## Phase 4: US2 - Derivation Skill (P1)

Goal: independently request 05/06 with correct reuse costs and context explanation. Independent check: new derivation Skill tests plus existing Tool 25 characterization.

- [x] T009 [US2] RED: create `tests/test_workflow_derivation_bundle_skill.py` for portable frontmatter, own-tool binding, P01-P07 order, exact ack, exact pair writes/reuses classification, generic-risk mismatch and report-write explanation without invented report paths. [FR-001/002/003/004/005/006/009/013, SC-001/002/004; depends T008]
- [x] T010 [US2] GREEN: create `.agents/skills/workflow-derivation-bundle/SKILL.md` with self-contained P01-P10 and Tool 25 role table, default context transfer disclosure, empty ack on reuse, no raw errors and explicit legacy recovery limits. Rerun T009. [FR-001/002/003/004/005/006/009/010/012; depends T009]
- [x] T011 [US2] Add focused instruction regressions in `tests/test_workflow_derivation_bundle_skill.py` for partial/missing lecture or context, no force escalation, known recovery stop, no upstream fallback, no-cost drift and uncertain confirm; make any missing instruction RED before repairing the Skill. [FR-007/008/010/011/012, SC-002/003/004; depends T010]
- [x] T012 [US2] Run derivation instruction checks plus `tests/test_mcp_workflow_derivation.py`; record independent US2 results in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-013, SC-001/004/005; depends T011]

## Phase 5: US3 - Consent and failure boundary (P1)

Goal: explicit authority and honest terminal outcomes. Independent check: cross-Skill rules and C01-C20 acceptance matrix.

- [x] T013 [US3] RED: extend `tests/test_learning_workflow_skill_contracts.py` to require C01-C20 case coverage, defined rule references, matching request/confirm arguments, confirm response versus transport-outcome exclusivity, one-confirm bound and safe report expectations in `tests/fixtures/learning_workflow_skill_cases.json`; show missing fixture fails. Test fixture consistency, not a fake independent agent. [FR-006/007/010/011/012/013, SC-001/002/003/004; depends T012]
- [x] T014 [US3] GREEN: create synthetic `tests/fixtures/learning_workflow_skill_cases.json` with all contract cases, confirmed response/error or bounded transport outcome, and required cross-Skill variants; no real identifiers/secrets/bodies. Tie each case to P01-P10 clauses present in both Skill documents, then rerun T013. [FR-006/007/010/011/012/013, SC-001/002/003/004; depends T013]
- [x] T015 [US3] Add contract-negative cases in `tests/test_learning_workflow_skill_contracts.py` for missing fields, wrong types, duplicate roles, mixed directories, identity mismatch, invalid cost combinations and both slash styles; pin how instructions reject them without executing a synthetic agent. Add focused RED clauses if the Skill text lacks a case. [FR-002/003/004/011/013, SC-002/004; depends T014]
- [x] T016 [US3] Review every dialogue case against `.agents/skills/study-guide-bundle/SKILL.md` and `.agents/skills/workflow-derivation-bundle/SKILL.md`; record expected traces, denial-versus-clarification behavior, failure-status distinctions and prompt-injection/no-echo checks against the supplied confirm/transport evidence and unperformed live evaluation in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-005/006/007/008/010/011/012/013, SC-001/002/003/004; depends T015]

## Phase 6: Integration and closeout

- [x] T017 RED: add assertions in `tests/test_learning_workflow_skill_contracts.py` for both Skill entries, prerequisites, separate requests, report side effects and backend limitations in `.agents/skills/README.md`, `docs/mcp-usage.md`, `docs/agent-handoff.md` and `docs/verification-matrix.md`. Show missing guidance fails. [FR-009/012/014, SC-004/005; depends T016]
- [x] T018 GREEN: update those four documents and `specs/README.md` without rewriting unrelated/historical content; keep live count 26 and run T017 plus unchanged docs-count guards. [FR-009/012/014, SC-004/005; depends T017]
- [x] T019 Run all targeted sets in `specs/045-study-guide-workflow-skills/quickstart.md`, record exact results and skips in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-013/014, SC-005; depends T018]
- [x] T020 Run full pytest, compileall and diff check per `specs/045-study-guide-workflow-skills/quickstart.md`, using the repo interpreter and fresh short basetemp; record current results in `specs/045-study-guide-workflow-skills/implementation-log.md`. [SC-005; depends T019]
- [x] T021 Review requirements/acceptance separately from engineering/constitution boundaries in `specs/045-study-guide-workflow-skills/implementation-log.md`; inspect full diff for production/helper/registry scope creep. Label self-review honestly; reviewers stay read-only. [FR-001/014, SC-001/002/003/004/005; depends T020]
- [x] T022 Run speckit-converge against code/spec/plan/tasks, append only real remaining in-scope work in `specs/045-study-guide-workflow-skills/tasks.md`; record hooks and findings in `specs/045-study-guide-workflow-skills/implementation-log.md`. [FR-013/014, SC-005; depends T021]
- [x] T023 Complete any appended tasks through the sole writer with RED/GREEN, rerun affected checks if changed, and update `specs/045-study-guide-workflow-skills/implementation-log.md`; if none, record no added work instead of fabricating tasks. [SC-005; depends T022]
- [x] T024 Update completion status in `specs/045-study-guide-workflow-skills/spec.md`, `specs/README.md` and the implementation evidence, reporting files/commands/results/skips/limitations and no branch/commit/deployment. [FR-014, SC-005; depends T023]

## Dependencies and Parallel Opportunities

T001-T004 -> US1 T005-T008 -> US2 T009-T012 -> US3 T013-T016 -> T017-T024. One writer, sequential changes and tests. US1 and US2 have independent acceptance criteria; separate read-only reviewers may compare their instructions, but no parallel writers or test runs sharing scratch.

## Implementation Strategy

US1 is a usable intermediate MVP; complete both Skills and US3 for 045 acceptance. Do not mark all tasks complete after static checks alone: backend characterization, case review, documentation, full regression and converge are required. Actual model obedience remains unverified unless a separately authorized live evaluation is recorded.

## Requirement Traceability

| Requirement | Primary tasks |
| --- | --- |
| FR-001 | T005,T006,T009,T010,T021 |
| FR-002 | T005,T006,T009,T010,T015 |
| FR-003 | T003,T005,T006,T009,T010,T015 |
| FR-004 | T003,T005,T006,T009,T010,T015 |
| FR-005 | T005,T007,T009,T010,T016 |
| FR-006 | T005,T009,T013,T014,T016 |
| FR-007 | T007,T011,T013,T014,T016 |
| FR-008 | T005,T007,T011,T016 |
| FR-009 | T003,T006,T009,T010,T017,T018 |
| FR-010 | T004,T007,T010,T011,T013,T014,T016 |
| FR-011 | T007,T011,T013,T014,T015,T016 |
| FR-012 | T004,T007,T010,T011,T013,T014,T016,T017,T018 |
| FR-013 | T002,T003,T005,T008,T009,T012,T013,T014,T015,T016,T019,T022 |
| FR-014 | T001,T003,T017,T018,T019,T021,T022,T024 |
| SC-001 | T005,T008,T009,T012,T013,T014,T016,T021 |
| SC-002 | T005,T007,T009,T011,T013,T014,T015,T016,T021 |
| SC-003 | T004,T007,T011,T013,T014,T016,T021 |
| SC-004 | T003,T005,T007,T009,T011,T013,T014,T015,T016,T017,T018,T021 |
| SC-005 | T001,T002,T003,T004,T008,T012,T017,T018,T019,T020,T021,T022,T023,T024 |
