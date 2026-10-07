# Tasks: Learning MCP acceptance

## Phase 1: Setup and design

- [x] T001 Record scope/constitution/clarification in specs/058-learning-mcp-acceptance/spec.md.
- [x] T002 Resolve official templates and design seams in specs/058-learning-mcp-acceptance/plan.md and research.md.
- [x] T003 Write entities/contracts/quality checklists in specs/058-learning-mcp-acceptance/ and analyze requirement coverage before code.

## Phase 2: Foundation

- [x] T004 Establish focused RED for absent verification Core/CLI in tests/test_learning_mcp_acceptance.py.

## Phase 3: US1 selected-source connection

- [x] T005 [US1] Cover registry/identity/version/chunk/selection/budget/failure metadata in tests/test_learning_mcp_acceptance.py.
- [x] T006 [US1] Implement bounded session verification in src/corpus_ingest_core/learning_mcp_acceptance.py.
- [x] T007 [US1] Cover owned stdio/loopback validation/timeout/no-secret diagnostics in tests/test_learning_mcp_acceptance.py.
- [x] T008 [US1] Implement Core transport adapters and thin scripts/verify_learning_mcp.py.

Independent acceptance: specified source/range succeeds only with consistent complete delivery; missing/wrong/broken/budget replies cannot pass.

## Phase 4: US2 content acceptance

- [x] T009 [US2] Guard source questions/replay/AI distinctions in tests/test_spec_058_learning_acceptance_docs.py.
- [x] T010 [US2] Supply three human checks and pending operational records in specs/058-learning-mcp-acceptance/content-acceptance.md.

Independent acceptance: each question has source reasoning/examples/replay criteria and a separate pending human outcome.

## Phase 5: US3 handoff

- [x] T011 [US3] Cover missing/unsafe/transitive Skill references and notes template in tests/test_learning_mcp_acceptance.py.
- [x] T012 [US3] Implement metadata-only resource inventory in src/corpus_ingest_core/learning_mcp_acceptance.py.
- [x] T013 [US3] Document data/transport/model/resource/approval/continuation in specs/058-learning-mcp-acceptance/quickstart.md.
- [x] T014 [US3] Update discovery in specs/README.md, AGENTS.md, docs/install-and-porting.md, docs/verification-matrix.md and docs/roadmap.md.

Independent acceptance: inventory detects missing resources and handoff covers same-server prerequisites without implicit installation/preparation.

## Phase 6: Verification

- [x] T015 Run actual owned SDK pilot and record source hash preservation in specs/058-learning-mcp-acceptance/implementation-log.md.
- [x] T016 Run targeted/full pytest, compileall/diff and fresh read-only review; record in specs/058-learning-mcp-acceptance/implementation-log.md.
- [x] T017 Converge against artifacts and preserve genuine live gates in specs/058-learning-mcp-acceptance/tasks.md.

## Dependencies and requirement coverage

T001-T003 -> T004/T005/T007/T011 -> T006/T008/T012 -> T009/T014 -> T015/T016 -> T017. Root is sole writer; read-only research/review may run independently. No commits/branches/worktrees/deployment.

| Requirement | Tasks |
|---|---|
| FR-001, FR-002 | T004,T007,T008 |
| FR-003, FR-004, SC-001 | T005,T006,T015 |
| FR-005, FR-006, FR-007 | T005,T006,T007,T008,T016 |
| FR-008, SC-002 | T011,T012 |
| FR-009, SC-003 | T009,T010 |
| FR-010, SC-004 | T009,T013,T014 |
| FR-011 | T009,T010,T013,T017 |
| FR-012 | T007,T014,T015,T016 |

## Operational gates (outside automatic build execution)

- [ ] OP001 Human replay checks in content-acceptance.md; requires operator playback.
- [ ] OP002 Real new-source preparation; requires compatible already managed host and fresh exact preview/plan approval.
- [ ] OP003 Actual Hermes VM/mounted-host cases; requires accessible configured host. Close SPEC057 T017/T018 only with real traces, not this utility.

These remain pending until their prerequisites/evidence are supplied. Developer implementation can complete independently and must report that distinction.
