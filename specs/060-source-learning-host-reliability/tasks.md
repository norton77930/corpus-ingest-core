# Tasks: Source learning host reliability

Status: Local implementation and verification complete (26/28 tasks). T026/T027 actual operator-source and Hermes acceptance remain pending; local tests do not establish those outcomes. One active writer, no automatic commit/push/branch/deployment.

## Phase 1: Setup

- [x] T001 Record the pre-implementation targeted baseline using tests/test_source_content_query.py, tests/test_source_learning_reliability.py and tests/test_learning_mcp_acceptance.py; confirm existing35-tool registry and prohibited-data boundaries (FR-019–020).
- [x] T002 Recheck scope, contracts, constitution and dependency availability in specs/060-source-learning-host-reliability/plan.md before behavior changes; keep current actual Hermes environment acceptance pending if unavailable (FR-019–020).

## Phase 2: Foundation

- [x] T003 Add focused failing compact-cursor/legacy/mutation/offset tests in tests/test_source_learning_host_reliability.py using real Core and synthetic owned sources; assert the current96-character encoding fails the new length contract (FR-001–004).
- [x] T004 Add failing response-based recovery guards/oracles in tests/test_source_learning_host_reliability.py; mutate outgoing arguments independently of the successful response and prove bad-request reuse fails (FR-005–007).

## Phase 3: US1 reliable continuation

Independent criterion: Exact bounded reconstruction, fixed version/scope, shorter emission, legacy acceptance and one response-based recovery.

- [x] T005 [US1] Implement c1 canonical compact encoding/integrity validation and legacy decode compatibility in src/corpus_ingest_core/source_content_query.py; preserve full existing scope binding and public arguments (FR-001–004, FR-019).
- [x] T006 [US1] Verify altered query/action/window/IDs/version, corrupt valid positions, malformed/new prefixes and empty selections through tests/test_source_learning_host_reliability.py and tests/test_mcp_source_content_query.py; retain fixed content-free diagnoses in src/corpus_ingest_core/mcp_tools_source_content.py (FR-001–004, FR-019).
- [x] T007 [US1] Strengthen fresh copying of the last successful response, discard failed parameters, empty-first-page recovery and non-resetting allowance in .agents/skills/source-content-qa/SKILL.md and references/response-contract.md (FR-005–007).
- [x] T008 [US1] Align .agents/skills/source-learning-entry/SKILL.md and references/entry-protocol.md with the same narrow recovery; keep all preparation/generation stops and approval rules (FR-005–007, FR-019).
- [x] T009 [US1] Update tests/test_source_learning_reliability.py oracle to retain successful responses, then verify once-successful recovery, later second-error stop, unchanged-version reinspection and cumulative budgets in tests/test_source_learning_host_reliability.py (FR-005–007).
- [x] T010 [US1] Run focused GREEN and existing offset/search/unsafe-source/MCP regressions in tests/test_source_content_query.py and tests/test_mcp_source_content_query.py before advancing to the next slice (FR-001–007, FR-019).

## Phase 4: US2 discovery and URL entry

Independent criterion: Host-visible local priority and defined first source-processing call, with user-choice stopping on local blockers.

- [x] T011 [US2] Add failing parsed-frontmatter length/purpose and Hermes57-plus-ellipsis discovery tests for every .agents/skills/*/SKILL.md in tests/test_source_learning_host_reliability.py, including negative overlong descriptions (FR-008).
- [x] T012 [US2] Shorten all current .agents/skills/*/SKILL.md descriptions to at most60 characters; put URL learning/local MCP priority in source-learning-entry description and leave unrelated bodies unchanged (FR-008, FR-019).
- [x] T013 [US2] Make the first source-processing MCP call explicit as non-confirming prepare_learning_source in .agents/skills/source-learning-entry/SKILL.md and references/entry-protocol.md; retain required resource loading and no automatic web fallback (FR-009–010).
- [x] T014 [US2] Run discovery/routing GREEN and update old full-description wording guards in tests/test_source_learning_reliability.py and tests/test_source_learning_entry_skill.py without weakening the visible-purpose/local-first tests (FR-008–010).

## Phase 5: US3 foreground and truthful progress

Independent criterion: No delegated evidence reading; job submission and actual examined scope are distinguished from ongoing/completed notes.

- [x] T015 [US3] Add focused failing foreground/delegate_task/progress and preparation-worker distinction checks in tests/test_source_learning_host_reliability.py (FR-011–012).
- [x] T016 [US3] Add visible direct-main-conversation sequential calls/no background AI rules and truthful accepted/partial status examples in .agents/skills/source-learning-entry/SKILL.md, source-content-qa/SKILL.md and source-preparation/SKILL.md plus existing response/entry contracts (FR-011–012).
- [x] T017 [US3] Run rule GREEN and preparation/continuation approval/no-retry regressions in tests/test_source_learning_host_reliability.py and tests/test_source_learning_entry_skill.py; no host-wide delegation setting change (FR-011–012, FR-019).

## Phase 6: US4 source-grounded responses

Independent criterion: Evidence precedes source concept answers; neutral naming, relevant concrete examples and explicit supplements survive the response contract.

- [x] T018 [US4] Add failing concept-evidence, no-hit semantics, neutral-name positive/negative examples and pre-answer example/AI-label/requested-scope checks in tests/test_source_learning_host_reliability.py (FR-013–018).
- [x] T019 [US4] Add evidence-before-concept-answer, context/ASR rules and neutral-name examples to .agents/skills/source-content-qa/SKILL.md and references/response-contract.md (FR-013–015).
- [x] T020 [US4] Add a pre-answer relevant-example check and consistent AI 補充 labeling to .agents/skills/source-content-qa/SKILL.md, references/response-contract.md and the single learning-notes-template.md; preserve conditional headings and no unrequested applications (FR-016–018).
- [x] T021 [US4] Run writing-contract GREEN and existing source-content-qa Skill regressions in tests/test_source_content_qa_skill.py and tests/test_source_learning_reliability.py; explicitly distinguish instruction guards from real model quality (FR-013–018, FR-020).

## Phase 7: Cross-cutting verification and acceptance

- [x] T022 Add a real-SDK default-budget whole-source synthetic1448-segment/over60000-character regression in tests/test_learning_mcp_acceptance.py or tests/test_source_learning_host_reliability.py, including split chunks and final-instant range coverage; require scope_complete and inspected/selected/delivered count equality without raising defaults (FR-003, FR-020).
- [x] T023 Update docs/verification-matrix.md, docs/api.md, docs/mcp-usage.md, docs/install-and-porting.md and .agents/skills/README.md for compact compatibility, visible discovery and operator acceptance; preserve historical SPEC059 as-built claims (FR-001–020).
- [x] T024 Run all relevant cursor/MCP/Skill/verifier/registry/preparation/docs/prohibited-data tests from specs/060-source-learning-host-reliability/quickstart.md; examine skip reasons and scoped diffs (FR-019–020).
- [x] T025 Run pytest -q, compileall src scripts, git diff --check and verify_learning_mcp inventory at implementation closeout using specs/060-source-learning-host-reliability/quickstart.md; record safe summary results, no operation-log file (FR-019–020).
- [ ] T026 Run default-budget whole-source verify_learning_mcp against the explicitly selected operator-owned prepared source as described in specs/060-source-learning-host-reliability/quickstart.md; otherwise leave this actual-source acceptance pending with the missing-environment reason (FR-020).
- [ ] T027 Perform the six real Hermes scenarios in specs/060-source-learning-host-reliability/quickstart.md, reviewing call order/coverage/concept answers/pronouns/examples/AI labels/output scope; do not mark synthetic or string-test success as actual host success (FR-008–018, FR-020).
- [x] T028 Converge code against specs/060-source-learning-host-reliability/spec.md, plan.md and tasks.md; report build completion separately from any pending T026/T027 operator acceptance and preserve prohibited artifacts (FR-019–020).

## Dependencies and execution strategy

T001–002 -> T003–004 -> T005–010 -> T011–014 -> T015–017 -> T018–021 -> T022–028. Each slice starts with its focused RED and ends with GREEN/regressions. No parallel writers. Independent read-only checks of descriptions and contracts may run while another review reads cursor behavior; no parallel host read calls or background learning delegation. The minimum useful slice is US1, but approved implementation completes all four stories. T026/T027 require the operator environment and remain explicitly pending if inaccessible; T028 must not erase that distinction.

## Requirement coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T003, T005, T006, T010, T023 |
| FR-002 | T003, T005, T006, T010 |
| FR-003 | T003, T005, T010, T022 |
| FR-004 | T003, T005, T006, T010 |
| FR-005 | T004, T007, T008, T009 |
| FR-006 | T004, T007, T008, T009 |
| FR-007 | T004, T007, T008, T009 |
| FR-008 | T011, T012, T014, T027 |
| FR-009 | T013, T014, T027 |
| FR-010 | T013, T014, T027 |
| FR-011 | T015, T016, T017, T027 |
| FR-012 | T015, T016, T017, T027 |
| FR-013 | T018, T019, T021, T027 |
| FR-014 | T018, T019, T021, T027 |
| FR-015 | T018, T019, T021, T027 |
| FR-016 | T018, T020, T021, T027 |
| FR-017 | T018, T020, T021, T027 |
| FR-018 | T018, T020, T021, T027 |
| FR-019 | T001, T002, T005, T006, T008, T017, T023, T024, T025, T028 |
| FR-020 | T001, T002, T021, T022, T023, T024, T025, T026, T027, T028 |
