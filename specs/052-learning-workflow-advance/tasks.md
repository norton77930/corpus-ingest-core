# Tasks: Single-episode learning workflow advance
Input:spec/plan/model/contract/research. Root sole writer;user authorizes direct execution;reviewers read-only.

## Phase1 Baseline and authorized documentation
- [x] T001 Record701file/31contract baseline and docsRED in implementation-log.md (FR-010,FR-012).
- [x] T002 Recheck038/044 behavior;update038 tasks/checklists/completion-record and044 status/evidence;docsGREEN (FR-010;SC-004).

## Phase2 US1 Preview
- [x] T003 Add focused failing identity/controls/zero-effects/selection/noop/attention/shape/canonical-path tests in tests/test_learning_workflow_advance.py (FR-001,FR-002,FR-003,FR-011;SC-001,SC-002).
- [x] T004 Implement preview-only Core learning_workflow_advance.py and runGREEN (FR-001,FR-002,FR-003,FR-011).

## Phase3 US2 Confirmation
- [x] T005 Add failing bindings/action/path/cost-drift/ack-before-inspection/single-dispatch/post-failure projection cases (FR-004,FR-005,FR-006,FR-007,FR-008;SC-002,SC-003).
- [x] T006 Implement confirmed path and safe post-dispatch projection in learning_workflow_advance.py;runGREEN (FR-004,FR-005,FR-006,FR-007,FR-008).

## Phase4 US3 MCP and compatibility
- [x] T007 Add failing wrapper/signature/envelope/fixed-phase-error tests in tests/test_mcp_learning_workflow_advance.py (FR-008,FR-009;SC-003,SC-004).
- [x] T008 Implement thin mcp_tools_learning_advance.py;runGREEN (FR-008,FR-009).
- [x] T009 Add failing32-count/finalslot/facade/docs guards (FR-009;SC-004).
- [x] T010 Append facade group/export,update validator/currentdocs/count guards;runGREEN (FR-009).

## Phase5 Integration and closeout
- [x] T011 Run real temporary fake-provider generation/cover/derivation/complete/legacy/stale/recovery/race cases,unchanged25-31/Skills and protected-file/31-contract audit (FR-001,FR-002,FR-003,FR-004,FR-005,FR-006,FR-007,FR-008,FR-009,FR-011;SC-001,SC-002,SC-003,SC-004).
- [x] T012 Fresh read-only behavior/engineering reviews;reproduce concrete findingsRED/fixGREEN;record implementation-log.md (FR-012;SC-005).
- [x] T013 Full pytest,compileall src scripts,diff check;record results/skips (FR-012;SC-005).
- [x] T014 Converge052,append/complete genuine gaps,update lifecycle/registry/AGENTS/roadmap and final checks (FR-010,FR-012;SC-005).

## Dependencies and implementation strategy
T001->T002->T003/004->T005/006->T007/008->T009/010->T011->T012->T013->T014. Single-preview increment is independently testable before confirm;confirmed one-action increment next;MCP adapter last. Review focus in plan mapped to failure/drift/integration tests. Independent read-only reviewers may run concurrently; no parallel writers. No commits/branches/worktrees/real providers.
