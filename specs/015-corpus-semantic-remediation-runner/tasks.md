# Tasks: Corpus Semantic Remediation Runner

**Input**: Design documents from `specs/015-corpus-semantic-remediation-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is mandatory. Add each failing test and observe the relevant RED result before its implementation task.

**Organization**: Tasks are dependency ordered by shared contracts, strict-zero-file preview, confirmed summary, confirmed review, CLI, safety/governance, and final verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel only when files and dependencies do not overlap
- **[Story]**: Maps the task to US1, US2, or US3
- Every task names its primary file or verification command

## Phase 1: Setup and Failing Shared Contracts

**Purpose**: Establish reusable fixtures and RED tests for additive public boundaries before runtime implementation.

- [X] T001 Create single-episode corpus fixture builders that never access repository `.env` or untracked `data/` in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T002 Add full tree-manifest helpers recording path, hash, size, and mtime in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T003 Add failing public API signature, result-model, error, storage-path, package-export, and explicit absence-of-force/partial/batch/scheduler/retry/automatic-review surfaces contract tests in `tests/test_contracts.py` and `tests/test_corpus_semantic_remediation_runner.py`
- [X] T004 Add failing latest runner JSON/Markdown path and no-directory-creation tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T005 Add failing semantic-summary UTF-8 readability metadata compatibility tests in `tests/test_corpus_index.py`
- [X] T006 Run the new contract/readability tests and record the expected RED result before implementation

---

## Phase 2: Foundational Models, Storage, Index Metadata, and Module Boundary

**Purpose**: Add only the shared additive structures required by every user story.

**CRITICAL**: No preview or confirmed behavior starts until this phase is green.

- [X] T007 Add `CorpusSemanticRemediationRunFilter`, counts, warning, row, and result dataclasses in `src/corpus_ingest_core/models.py`
- [X] T008 Add `CorpusSemanticRemediationRunnerFailedError` in `src/corpus_ingest_core/errors.py`
- [X] T009 Add `CorpusSemanticRemediationRunAssetPaths` and `corpus_semantic_remediation_run_asset_paths()` without filesystem creation in `src/corpus_ingest_core/storage.py`
- [X] T010 Add 2 MiB-bounded full UTF-8 semantic-summary readability metadata without retaining body content or changing legacy semantic status, 009 actions, or extractive-summary behavior in `src/corpus_ingest_core/corpus_index.py`
- [X] T011 Create `src/corpus_ingest_core/corpus_semantic_remediation_runner.py` with constants, exact public signature, additive serializer skeleton, and no side effects
- [X] T012 Export the new Core API, models, error, and storage helper from `src/corpus_ingest_core/__init__.py`
- [X] T013 Run foundational targeted tests in `tests/test_contracts.py`, `tests/test_corpus_index.py`, and `tests/test_corpus_semantic_remediation_runner.py`

**Checkpoint**: Additive contracts and 008 readability metadata are green; no semantic runner execution exists yet.

---

## Phase 3: User Story 1 - Strict Zero-File Semantic Preview (Priority: P1) MVP

**Goal**: Reduce one explicit episode to `semantic_summary`, `semantic_review`, `completed`, or blocked/manual-only from one fresh in-memory snapshot pair without any write or execution.

**Independent Test**: Real 008/009 builders cover the complete state table while before/after tree manifests remain identical and every forbidden call count is zero.

### Tests for User Story 1

- [X] T014 [US1] Add failing invalid blank, `latest`, path-like, URL-like, traversal, UNC, control-character, and unsupported-action validation tests asserting zero 008/009 builder calls in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T015 [US1] Add failing valid-transcript/missing-summary selects `semantic_summary` test using real 008/009 builders in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T016 [US1] Add failing readable-summary/missing-review selects `semantic_review` test using real builders in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T017 [US1] Add failing passed-review produces `completed` with no executable action test in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T018 [US1] Add failing invalid transcript states produce blocked/manual-only tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T019 [US1] Add failing unreadable/oversized summary and default `available`, blank, arbitrary, failed, blocked, unreadable, or duplicate-latest review states produce the exact fail-closed result in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T020 [US1] Add failing absent requested episode and multi-episode isolation tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T021 [US1] Add failing explicit dry-run action match and mismatch outcome tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T022 [US1] Add failing six-state full tree-manifest strict zero-file integration test covering JSON, Markdown, semantic/review, runner report, cache, and `.part` artifacts in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T023 [US1] Add failing exact-one 008/exact-one 009 snapshot identity, stale persisted sentinel, and zero persister/executor/provider/env/progress callback tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T024 [US1] Add failing 008/009 snapshot exception mapping to selected blocked + failed/manual-only row, category-only/no-leak/stop-probe behavior, and dry-run-null/confirmed-report paths in `tests/test_corpus_semantic_remediation_runner.py`

### Implementation for User Story 1

- [X] T025 [US1] Implement safe podcast, explicit episode, action, provider/model identifier, credential-variable-name, and positive chunk-setting normalization in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T026 [US1] Build one private 008 snapshot and one private 009 snapshot from the same result/payload without calling persisters in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T027 [US1] Isolate the canonical episode and implement the dedicated fail-closed semantic state reducer in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T028 [US1] Implement bounded dry-run rows, counts, risk/ack flags, safe planned reads/writes, warnings, and null report paths in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T029 [US1] Implement JSON-compatible allowlisted result serialization and category-only snapshot failure containment in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T030 [US1] Run the full US1 state-table, zero-file manifest, snapshot identity, validation, and no-leak tests

**Checkpoint**: Core dry-run is independently usable and provably creates, modifies, and deletes zero files.

---

## Phase 4: User Story 2 - One Confirmed Semantic Summary (Priority: P2)

**Goal**: Require explicit summary confirmation and exact acknowledgement, call the existing semantic core exactly once, write a confirmed-only latest runner report, and stop.

**Independent Test**: A controlled provider double travels through the real semantic summarizer and produces one executed/reused/failed outcome without review or fallback execution.

### Tests for User Story 2

- [X] T031 [US2] Add failing direct-Core missing/incorrect acknowledgement tests asserting zero snapshot, provider, executor, and writer calls in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T032 [US2] Add failing confirmed `action=next` rejection and explicit summary action-drift tests asserting zero executor/fallback calls in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T033 [US2] Add failing exact-once semantic summary dispatch and supported option forwarding test using the real semantic core with a mock provider in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T034 [US2] Add failing existing-summary reuse mapping and no-review chaining test in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T035 [US2] Add failing provider, transcript, and summary-write exception category-only containment tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T036 [US2] Add failing confirmed latest JSON/Markdown report schema, no `generated_at`, metadata-only body, per-file atomic `.part` replacement, and JSON/Markdown report-writer failure/no-cleanup tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T037 [US2] Add failing confirmed summary stale-index/plan/cache warning and no automatic refresh/rebuild tests in `tests/test_corpus_semantic_remediation_runner.py`

### Implementation for User Story 2

- [X] T038 [US2] Validate exact summary acknowledgement before snapshot/provider work and reject confirmed `next` in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T039 [US2] Implement explicit-action equality gating and exact-once `semantic_summarize_episode()` dispatch with supported option forwarding in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T040 [US2] Map semantic executor executed, reused, and category-only failed outcomes without rescan, review, retry, or fallback in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T041 [US2] Implement confirmed-only latest JSON/Markdown rendering and atomic runner-report writes in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T042 [US2] Add bounded stale index/plan/cache warnings after confirmed attempts in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T043 [US2] Run the confirmed summary, acknowledgement order, real semantic core, report, no-chain, and cache-boundary tests

**Checkpoint**: One explicit summary action can execute or reuse exactly once and always stops before semantic review.

---

## Phase 5: User Story 3 - One Confirmed Deterministic Semantic Review (Priority: P3)

**Goal**: Run the existing local review exactly once without LLM configuration, preserve its timestamped artifact contract, record the bounded outcome, and stop.

**Independent Test**: A local semantic fixture travels through the real review core while profile/env/provider/summary call counts remain zero.

### Tests for User Story 3

- [X] T044 [US3] Add failing exact-once real deterministic review dispatch with local fixture and zero LLM/profile/env/provider activity test in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T045 [US3] Add failing review action-drift, missing summary, terminal review, and no-summary-fallback tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T046 [US3] Add failing passed, failed, and blocked review outcome mapping tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T047 [US3] Add failing duplicate timestamped latest-review selection and returned review source/output path preservation test in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T048 [US3] Add failing review exception and partial pair-write category-only containment without cleanup or retry test in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T049 [US3] Add failing confirmed review latest report/no-`generated_at`/manual stale warning test in `tests/test_corpus_semantic_remediation_runner.py`

### Implementation for User Story 3

- [X] T050 [US3] Implement exact-once `review_semantic_summary_smoke()` dispatch that ignores LLM options and never calls summary/provider/env surfaces in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T051 [US3] Map review passed, failed, blocked, and category-only failed outcomes while preserving executor-owned timestamped paths in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T052 [US3] Preserve existing review pair-write/partial-failure ownership without cleanup, rescan, retry, or fallback in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py`
- [X] T053 [US3] Run the confirmed deterministic review, no-LLM, timestamped-contract, terminal-state, and failure tests

**Checkpoint**: One explicit deterministic review can execute exactly once without any LLM configuration or fallback action.

---

## Phase 6: Thin CLI and Cross-Cutting Safety Guards

**Purpose**: Expose the Core safely while locking acknowledgement ordering, structured exits, no-leak output, and excluded-system contracts.

### Tests

- [X] T054 Add failing CLI dry-run JSON, explicit selector/action, zero profile/`.env`/provider/executor/write, and exit-zero tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T055 Add failing CLI confirmed-summary acknowledgement-before-profile/env-loader/provider construction tests in `tests/test_llm_ack_guard_contracts.py` and `tests/test_corpus_semantic_remediation_runner.py`
- [X] T056 Add failing CLI confirmed-summary profile/env resolution and safe option forwarding tests using controlled loaders in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T057 Add failing CLI confirmed-review bypasses all LLM profile/env/provider resolution tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T058 Add failing structured outcome exit-zero and invalid input/ack/report-writer/system-error safe non-zero tests in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T059 Add adversarial JSON/Markdown/stdout/stderr no-leak tests for transcript, semantic body, prompt, raw response, endpoint/query, secret, traceback, investment-advice strings, exact planned-write labels, and supported safe CJK local paths in `tests/test_llm_cli_no_leak.py` and `tests/test_corpus_semantic_remediation_runner.py`
- [X] T060 Add exact 12-tool MCP, no 010/014 integration, manual cache rebuild, provider-factory, repository-secret, unchanged 014 contract, and no force/partial/batch/scheduler/retry/full-chain/automatic-review/stock-lens/live-market surface guards in the relevant existing safety tests

### Implementation

- [X] T061 Implement thin `scripts/run_corpus_semantic_remediation.py` argument parsing, Core call, sanitized JSON output, and bounded error exits
- [X] T062 Implement CLI ordering so invalid summary acknowledgement precedes profile/`.env` loading, dry-run bypasses both profile and `.env` resolution, and confirmed review bypasses all LLM resolution in `scripts/run_corpus_semantic_remediation.py`
- [X] T063 Harden safe path, warning, provider/model, progress, failure-category, Markdown, stdout, and stderr allowlists in `src/corpus_ingest_core/corpus_semantic_remediation_runner.py` and `scripts/run_corpus_semantic_remediation.py`
- [X] T064 Run CLI, acknowledgement, no-leak, MCP, cache, provider-factory, secret-boundary, 010, and 014 targeted safety suites

---

## Phase 7: Documentation, Governance, and Final Verification

**Purpose**: Align runtime documentation and complete every gate before lifecycle finalization.

- [X] T065 Add failing governance/docs guard tests for 015 artifacts, active AGENTS pointer, lifecycle status, roadmap, MCP/cache, and `.env` boundaries in `tests/test_architecture_spec_docs.py`, `tests/test_ai_governance_docs.py`, and related guard suites
- [X] T066 Document 015 Core/CLI, strict zero-file preview, exact acknowledgement, deterministic review, and manual cache boundary in `README.md`
- [X] T067 Map 015 runtime/data flow and exclusions in `docs/architecture.md`
- [X] T068 Register 015 source, CLI, tests, and status in `specs/README.md`
- [X] T069 Add 015 targeted suites and full-gate commands to `docs/verification-matrix.md`
- [X] T070 Update `docs/agent-handoff.md` and `docs/roadmap.md` with 015 scope and next unused feature number
- [X] T071 Run the governance/docs guards GREEN and validate `specs/015-corpus-semantic-remediation-runner/quickstart.md` using only controlled fixtures and no real `.env`, provider, or untracked `data/`
- [X] T072 Run targeted 010-015 corpus, semantic core/review, LLM acknowledgement/no-leak, MCP, cache, provider-factory, secret, and governance suites
- [X] T073 Run `python -m pytest`
- [X] T074 Run `python -m compileall src scripts`
- [X] T075 Run `git -c safe.directory=<repo-path> diff --check`

---

## Phase 8: Convergence and Lifecycle Finalization

**Purpose**: Compare code against every 015 artifact and finalize lifecycle state only after convergence has no blocking gap.

- [X] T076 Run `$speckit-converge`; append any missing work after T076, return to `$speckit-implement`, and repeat targeted/full gates whenever convergence finds a gap
- [X] T077 After a clean convergence result and successful T072-T075 gates, mark all 015 tasks/checklists complete and change `spec.md` status from `Draft` to `Implemented`

### Convergence stabilization tasks (appended; historical tasks preserved)

- [X] T078 Add failing regressions for full bounded Markdown report metadata parity and normalized CLI action gating in `tests/test_corpus_semantic_remediation_runner.py`
- [X] T079 Run the new convergence regressions and record the expected RED result
- [X] T080 Render every contract-required bounded result field in the Markdown report and use one normalized CLI action for acknowledgement, LLM-option resolution, progress, and Core dispatch
- [X] T081 Run the convergence regressions GREEN and rerun the 015 report, CLI, acknowledgement, and no-leak targeted suites
- [X] T082 Repeat `$speckit-converge` plus the full pytest, compileall, and diff gates before lifecycle finalization

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** has no dependencies and establishes the RED contract tests.
- **Phase 2** depends on Phase 1 and blocks all user stories.
- **US1 / Phase 3** depends on Phase 2 and establishes the pure state/snapshot boundary.
- **US2 / Phase 4** depends on US1 because confirmed summary reuses its fresh state reducer.
- **US3 / Phase 5** depends on US1 and the shared confirmed report boundary from US2.
- **Phase 6** depends on all three Core stories.
- **Phase 7** depends on stable runtime and safety behavior.
- **Phase 8** depends on successful runtime, docs, and verification gates; any discovered work is appended after T076 without rewriting history and returns to implementation.

### User Story Dependencies

- **US1** is the independently testable MVP and has no dependency on confirmed executors.
- **US2** uses US1 selection but is independently testable with a controlled provider and the real semantic core.
- **US3** uses US1 selection but is independently testable with a local fixture and the real deterministic review core.

### Parallel Opportunities

- Setup tests are executed sequentially because their shared fixtures and contract files overlap.
- State-table tests T014-T024 are kept sequential in the shared runner test file; the implementation remains one reducer.
- Summary and review phases use independent fixtures but remain dependency ordered because they share the runner module and test file.
- Documentation implementation follows the failing T065 governance tests and may be reviewed independently after runtime contracts stabilize.

## Implementation Strategy

1. Complete and observe RED for each phase's tests.
2. Add the minimum implementation required for GREEN.
3. Run the phase checkpoint before starting the next side-effect boundary.
4. Preserve the user's existing 014 worktree, `.env`, and untracked `data/`; create no commit, push, or PR without separate authorization.
5. Do not mark 015 `Implemented` until T076 reports no blocking gap and T072-T075 all pass.

## Stop Conditions

Stop and obtain explicit approval if implementation would require a constitution amendment, new dependency, artifact migration, MCP change, automatic cache/index/plan refresh, 010/014 behavior change, force/partial execution, batch/retry/scheduler/full-chain behavior, live market access, or more than one semantic executor per confirmed call.
