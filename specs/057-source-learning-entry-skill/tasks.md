# Tasks: Source learning entry Skill

Input: [plan](plan.md), [spec](spec.md), [research](research.md), [conversation model](data-model.md), [contract](contracts/skill.md). User authorized planning followed directly by implementation. One active writer; independent reviewers stay read-only. Tests precede the Skill.

## Phase 1: Setup

- [x] T001 Record approved scope, constitution review and explicit feature selection in specs/057-source-learning-entry-skill/spec.md.
- [x] T002 Research real Tool33/34/35 seams and available Hermes capabilities in specs/057-source-learning-entry-skill/research.md.
- [x] T003 Generate plan/design/quality artifacts in specs/057-source-learning-entry-skill/ and analyze before implementation.

## Phase 2: Foundational

- [x] T004 Establish failing resource/docs guards and standalone baseline in tests/test_source_learning_entry_skill.py, tests/test_spec_057_source_learning_docs.py and specs/057-source-learning-entry-skill/implementation-log.md.

## Phase 3: US1 Ready source (P1, MVP)

Independent test: a ready URL or known prepared identity reaches fresh inspected timed evidence without confirmation/submission.

- [x] T005 [US1] Add ready/readability/context-digest backend characterizations in tests/test_source_learning_entry_skill.py.
- [x] T006 [US1] Implement known-ID/ready-URL entry and installed QA/template handoff in .agents/skills/source-learning-entry/SKILL.md.

## Phase 4: US2 Missing source (P1)

Independent test: only fresh disclosed-plan approval permits one confirmation; accepted always stops, and busy-other-source never binds its job.

- [x] T007 [US2] Define approval/denial/drift/busy/uncertain outcome oracles and backend binding checks in tests/fixtures/source_learning_entry_cases.json and tests/test_source_learning_entry_skill.py.
- [x] T008 [US2] Implement preparation disclosure, exact binding and submission stopping in .agents/skills/source-learning-entry/references/entry-protocol.md.

## Phase 5: US3 Continue later (P2)

Independent test: status-only stops; explicit retained learning request checks matching readiness and fresh source version; lost context and mismatch clarify/stop.

- [x] T009 [US3] Define progress/continuation/mismatch/lost-context/budget/source-change oracles in tests/fixtures/source_learning_entry_cases.json.
- [x] T010 [US3] Implement same-conversation visible handoff and readiness checks in .agents/skills/source-learning-entry/references/entry-protocol.md.

## Phase 6: Cross-cutting validation and handoff

- [x] T011 Validate portability, declared dependencies and frontmatter in tests/test_source_learning_entry_skill.py and .agents/skills/source-learning-entry/SKILL.md.
- [x] T012 Synchronize entry discovery/operator instructions in .agents/skills/README.md, specs/README.md, docs/mcp-usage.md, docs/install-and-porting.md, docs/verification-matrix.md and docs/roadmap.md.
- [x] T013 Run independent synthetic forward/pressure review and record decisions/limits in specs/057-source-learning-entry-skill/implementation-log.md.
- [x] T014 Run a read-only owned existing-source pilot and record versions/pages/hash preservation in specs/057-source-learning-entry-skill/implementation-log.md.
- [x] T015 Run targeted/full pytest, compileall and diff checks; record actual commands/results in specs/057-source-learning-entry-skill/implementation-log.md.
- [x] T016 Compare implemented instructions/tests/docs against intent with Converge and record gaps in specs/057-source-learning-entry-skill/implementation-log.md.
- [ ] T017 Provide an accessible already configured Hermes session and run the actual mounted-host scenarios in specs/057-source-learning-entry-skill/quickstart.md; record real trace/output separately. This operational acceptance gate remains pending while no host entry is accessible; do not check it off using synthetic/SDK evidence.

## Dependencies and execution

T001-T003 -> T004 -> T005/T007/T009 (test/oracle definitions) -> T006/T008/T010 -> T011/T012 -> T013/T014 -> T015 -> T016. T017 additionally depends on an accessible configured host and operator-approved host inference; host availability is not created by this feature. US1 supplies MVP; US2 and US3 add conditional preparation and continuation. Only read-only research, tests in separate owned temp roots and synthetic review may run independently; all repository edits stay with one writer.

## Requirement coverage

| Intent | Tasks |
|---|---|
| FR-001, FR-002, FR-003, SC-001 | T005, T006 |
| FR-004, FR-005, SC-002 | T007, T008 |
| FR-006, FR-007, FR-008, FR-009, SC-003 | T007, T009, T010 |
| FR-010, FR-011, FR-012, SC-004 | T006, T008, T010, T011, T013 |
| FR-013 | T011, T012, T014, T015 |
| FR-014, SC-005 | T002, T012, T016, T017 |

No branch, commit, worktree, deployment, provider invocation or cache rebuild task is authorized.

## Phase 7: Convergence

- [ ] T018 Complete the outstanding T017 operational acceptance using an accessible already configured Hermes host; record actual same-server tool trace/output, source/version/coverage and preserved input hashes in specs/057-source-learning-entry-skill/implementation-log.md per T017 and plan: Verification and host acceptance (partial). This tracks the same pending host gate, not an additional build feature; synthetic probes and SDK receipts cannot close it. No installation, service launch or host configuration is authorized by this task.
