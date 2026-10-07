# Tasks: Source preparation jobs

Input:spec.md,plan.md,research.md,data-model.md,contracts/. Root sole writer;tests/review roles read-only. No branch/worktree/commit/deployment. Planning evidence does not implement runtime tasks.

## Phase1 Planning and baseline
- [x] T001 Capture735-file baseline and focused docsRED in specs/054-source-preparation-jobs/workflow-record.md.(FR-014-016;SC-007)
- [x] T002 Specify/clarify/plan/checklist/tasks/analyze package specs/054-source-preparation-jobs/ and update explicit AGENTS.md/specs/README.md/roadmap selection.(FR-001-016;SC-001-007)
- [x] T003 Verify planning docs,protected baseline,registry/full gates and evidence in specs/054-source-preparation-jobs/workflow-record.md.(FR-015-016;SC-007)

## Phase2 US1 Preview and setup diagnosis
- [x] T004 [US1] Write failing safe-ledger/path/readonly/atomic-capacity checks in tests/test_source_preparation_jobs.py.(FR-007,FR-012;SC-003)
- [x] T005 [US1] Implement ledger/admission primitives in src/corpus_ingest_core/source_preparation_jobs.py and managed location in storage.py;rerunGREEN.(FR-007,FR-012;SC-003)
- [x] T006 [US1] Write failing source/config/canonical/partial/reuse/zero-write preview tests in tests/test_source_preparation.py.(FR-001,FR-002,FR-003,FR-004,FR-010,FR-016;SC-001)
- [x] T007 [US1] Implement bounded preview/setup/readiness Core in src/corpus_ingest_core/source_preparation.py;rerunGREEN.(FR-001,FR-002,FR-003,FR-004,FR-010;SC-001)
- [x] T008 [US1] Test absent stores do not get created and malformed source/artifact observations stay blocked in tests/test_source_preparation.py.(FR-003-004,FR-012;SC-001,SC-005)

## Phase3 US2 Approval,admission and worker
- [x] T009 [US2] Write failing approval/drift/duplicate/different-source/quick-ack checks in tests/test_source_preparation.py and test_source_preparation_jobs.py.(FR-005-007;SC-002-003)
- [x] T010 [US2] Implement matching confirmation/coalescing/transactional admission in source_preparation.py and source_preparation_jobs.py;rerunGREEN.(FR-005-007;SC-002-003)
- [x] T011 [US2] Add failing truthful-stage/default-preservation checks to tests/test_youtube_video_ingest.py and test_x_video_ingest.py.(FR-008-009,FR-014;SC-007)
- [x] T012 [US2] Add bounded optional progress hooks in youtube_video_ingest.py and x_video_ingest.py,keeping old default behavior;rerunGREEN.(FR-008-009,FR-014;SC-007)
- [x] T013 [US2] Write failing one-job/owner/force-false/validation/failure worker tests in tests/test_source_preparation_worker.py.(FR-008-012,FR-016;SC-004-005)
- [x] T014 [US2] Implement Core source_preparation_worker.py and thin scripts/run_source_preparation_worker.py;rerunGREEN.(FR-008-012;SC-004-005)
- [x] T015 [US2] Add failing launch/refusal/ambiguous-start/hidden-Windows/context checks in tests/test_source_preparation_worker.py.(FR-006,FR-008,FR-011;SC-002,SC-005)
- [x] T016 [US2] Implement launch ownership/lifecycle in source_preparation.py and source_preparation_jobs.py without auto retry;rerunGREEN.(FR-006,FR-008,FR-011;SC-002,SC-005)

## Phase4 US3 Progress and uncertain outcomes
- [x] T017 [US3] Write failing finite/offline/unknown/stale/readiness status checks in tests/test_source_preparation_jobs.py.(FR-009-012;SC-004-005)
- [x] T018 [US3] Implement read-only bounded status projection in source_preparation.py/source_preparation_jobs.py;rerunGREEN.(FR-009-012;SC-004-005)
- [x] T019 [US3] Add failing partial-write/report/store/process-interruption and no-retry/no-cleanup checks in tests/test_source_preparation_worker.py.(FR-011-012,FR-016;SC-005)
- [x] T020 [US3] Implement fixed failure/attention classification and preserved history in source_preparation_worker.py;rerunGREEN.(FR-011-012;SC-005)
- [x] T021 [US3] Prove a real owned fake worker survives submitting-client disconnect and validates one source in tests/test_source_preparation_worker.py.(FR-006-010,FR-015;SC-002-004)

## Phase5 US4 MCP and portable Skill
- [x] T022 [US4] Write failing Tools33/34 signatures/order/defaults/envelope checks in tests/test_mcp_source_preparation.py and test_mcp_tool_registry_contract.py.(FR-014;SC-007)
- [x] T023 [US4] Append src/corpus_ingest_core/mcp_tools_source_preparation.py and mcp_server.py re-export/group;rerunGREEN with prior32 signatures frozen.(FR-014;SC-007)
- [x] T024 [US4] Exercise owned-fixture SDK transport,one submit,readonly status and fixed errors in tests/test_mcp_source_preparation.py.(FR-004-006,FR-009,FR-012,FR-015;SC-001-005)
- [x] T025 [US4] Add failing consent/setup/progress/hostile-reply dialogue checks in tests/test_source_preparation_skill.py.(FR-013;SC-006)
- [x] T026 [US4] Create .agents/skills/source-preparation/SKILL.md and references/response-contract.md with narrow protected publication;rerunGREEN.(FR-013;SC-006)
- [x] T027 [US4] Read-only pressure-test Skill call limits,approval binding,missing-tool and no downstream-chain behavior;record specs/054-source-preparation-jobs/implementation-log.md.(FR-013,FR-015;SC-006-007)

## Phase6 Verification and closeout
- [x] T028 Update current counts/setup/operator docs in docs/,scripts/validate_mcp_setup.py,Skill catalog,specs/README.md and pyproject.toml only as required by actual appended tools/entry points.(FR-014-016;SC-007)
- [x] T029 Obtain independent read-only requirement/engineering reviews;reproduce findings withfocusedRED/GREEN;record implementation-log.md.(FR-015;SC-007)
- [x] T030 Run relevant regressions,full pytest,compileall,diff and protected-artifact audit;record actual commands/skips/limits in implementation-log.md.(FR-014-016;SC-007)
- [x] T031 Converge spec/plan/tasks;update lifecycle and tests/test_spec_054_source_preparation_docs.py for actual implemented status,then finaldocs checks. Actual Hermes-host evidence stays separate from offline completion.(FR-015-016;SC-007)

## Dependencies and delivery
T001-003 planning precedes runtime. T004/005 -> T006-008 US1;T009/010 admission -> T011-016 worker -> T017-021 status/process proof -> T022-027 MCP/Skill -> T028-031 closeout.
US1 is the first demonstrable slice; do not register tools or claim full readiness early. No parallel writers. Each behavior slice shows focused failure before the smallest implementation and reruns meaningful regressions. Subsequent steps may not reclassify uncertain work as retry-safe.
