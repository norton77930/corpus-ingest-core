# Tasks: Corpus Fresh Episode Workflow Runner

**Input**: Design documents from `specs/014-corpus-fresh-episode-workflow-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish workflow runner fixtures and public contract tests before implementation.

- [X] T001 Create workflow runner fixture helpers in `tests/test_corpus_episode_workflow_runner.py`
- [X] T002 [P] Add failing storage helper path contract tests for workflow run JSON/Markdown paths in `tests/test_corpus_episode_workflow_runner.py`
- [X] T003 [P] Add failing public result/model contract tests for workflow filters, counts, rows, warnings, and result paths in `tests/test_corpus_episode_workflow_runner.py`
- [X] T004 [P] Add failing workflow runner error contract test in `tests/test_corpus_episode_workflow_runner.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T005 Add workflow filter, counts, row, result, and warning models in `src/podcast_ingest_core/models.py`
- [X] T006 Add workflow runner error type in `src/podcast_ingest_core/errors.py`
- [X] T007 Add `CorpusEpisodeWorkflowRunAssetPaths` and `corpus_episode_workflow_run_asset_paths(podcast_id)` in `src/podcast_ingest_core/storage.py`
- [X] T008 Create `src/podcast_ingest_core/corpus_episode_workflow_runner.py` with public function signature, stage constants, run mode constants, and no-op-safe module skeleton
- [X] T009 Export workflow public function, error, storage helper, and model types from `src/podcast_ingest_core/__init__.py`
- [X] T010 Run foundational targeted tests `python -m pytest tests/test_corpus_episode_workflow_runner.py -k "contract or storage or error" --basetemp=.pytest-tmp/run-014-foundation`

**Checkpoint**: Public contracts and module boundaries exist, but workflow behavior is not complete.

---

## Phase 3: User Story 1 - Preview the Next Safe Stage (Priority: P1) MVP

**Goal**: Resolve latest or explicit episode state and return metadata-only dry-run output for exactly one next safe stage without writes.

**Independent Test**: A dry-run over mocked corpus state selects intake, audio download, local transcription, deterministic remediation, completed, or blocked without writing reports or executing stage runners.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing dry-run unseeded latest selects intake and writes no workflow report test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T012 [P] [US1] Add failing dry-run seeded missing-audio selects audio download test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T013 [P] [US1] Add failing dry-run local-audio transcript-missing selects local transcription test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T014 [P] [US1] Add failing dry-run transcript-ready deterministic actions select deterministic remediation test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T015 [P] [US1] Add failing dry-run completed or blocked state produces no executable stage test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T016 [P] [US1] Add failing missing or blank selector defaults to `latest` test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T017 [P] [US1] Add failing unsupported stage value rejected test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T018 [P] [US1] Add failing dry-run does not call confirmed intake, downloader, transcriber, deterministic remediation execution, LLM, `.env`, MCP, or cache rebuild boundary test in `tests/test_corpus_episode_workflow_runner.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement selector and stage normalization in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T020 [US1] Implement dry-run stage probes using existing 013, 012, 011, and 010 dry-run/core metadata in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T021 [US1] Implement next-stage precedence selection and completed/blocked fallback in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T022 [US1] Implement metadata-only result serialization with null report paths for dry-run in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T023 [US1] Implement thin dry-run CLI `scripts/run_corpus_episode_workflow.py`
- [X] T024 [US1] Add CLI dry-run stdout contract test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T025 [US1] Run User Story 1 targeted tests `python -m pytest tests/test_corpus_episode_workflow_runner.py -k "dry_run or next_stage or selector or unsupported_stage or no_write or cli" --basetemp=.pytest-tmp/run-014-us1`

**Checkpoint**: User can preview the next safe stage for latest or explicit episode without writes or side effects.

---

## Phase 4: User Story 2 - Execute One Confirmed Next Stage (Priority: P2)

**Goal**: Confirm exactly one next stage for one episode, dispatch to only the matching existing core runner, and write deterministic workflow reports.

**Independent Test**: Confirmed execution calls only the selected existing runner for intake, audio download, local transcription, or deterministic remediation, passes relevant options, writes one workflow report pair, and stops.

### Tests for User Story 2

- [X] T026 [P] [US2] Add failing confirmed unseeded episode calls 013 intake only test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T027 [P] [US2] Add failing confirmed seeded missing-audio calls 012 audio download only test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T028 [P] [US2] Add failing confirmed local-audio transcript-missing calls 011 local transcription only test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T029 [P] [US2] Add failing confirmed transcription passes model, device, compute type, and VAD options test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T030 [P] [US2] Add failing confirmed transcript-ready deterministic actions call 010 remediation only with episode filter test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T031 [P] [US2] Add failing confirmed deterministic remediation passes force, allow_partial, and max_actions test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T032 [P] [US2] Add failing confirmed blocked/no-executable-state writes rejected or blocked workflow report without stage execution test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T033 [P] [US2] Add failing confirmed workflow report deterministic JSON/Markdown and no `generated_at` test in `tests/test_corpus_episode_workflow_runner.py`

### Implementation for User Story 2

- [X] T034 [US2] Implement confirmed intake dispatch to `run_corpus_episode_intake(..., confirm=True)` only in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T035 [US2] Implement confirmed audio dispatch to `run_corpus_audio_download(..., confirm=True)` only in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T036 [US2] Implement confirmed transcription dispatch to `run_corpus_local_transcription(..., confirm=True)` with transcription option pass-through in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T037 [US2] Implement confirmed deterministic dispatch to `run_corpus_remediation(..., confirm=True, episode_ref=..., force=..., allow_partial=..., max_actions=...)` in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T038 [US2] Implement one-stage-stop outcome mapping for executed, reused, failed, rejected, skipped, blocked, and completed states in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T039 [US2] Implement deterministic workflow run JSON and Markdown report writers in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T040 [US2] Extend CLI parsing for `--confirm`, `--stage`, transcription options, and remediation options in `scripts/run_corpus_episode_workflow.py`
- [X] T041 [US2] Add CLI confirmed stdout, stderr, and explicit `--stage next` required contract tests in `tests/test_corpus_episode_workflow_runner.py`
- [X] T042 [US2] Run User Story 2 targeted tests `python -m pytest tests/test_corpus_episode_workflow_runner.py -k "confirmed or dispatch or pass_through or report or generated_at" --basetemp=.pytest-tmp/run-014-us2`

**Checkpoint**: User can confirm exactly one next stage and inspect the workflow report before continuing.

---

## Phase 5: User Story 3 - Preserve Safety Boundaries and Manual Follow-up (Priority: P3)

**Goal**: Bound unsafe values, skipped manual-only work, and selected-stage failures without weakening existing corpus safety boundaries.

**Independent Test**: Unsafe values and failures from probes or stage runners produce sanitized metadata only; semantic/LLM/stock-lens/MCP/cache/batch actions are never executed.

### Tests for User Story 3

- [X] T043 [P] [US3] Add failing semantic, LLM, stock-lens, MCP, cache rebuild, and batch actions are manual-only and never executed test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T044 [P] [US3] Add failing selected stage failure containment without traceback/source URL/secret leakage test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T045 [P] [US3] Add failing JSON, Markdown, stdout, and stderr leak-safety test for raw transcript, evidence, semantic body, prompt, raw LLM output, secret, URL, query string, and traceback bodies in `tests/test_corpus_episode_workflow_runner.py`
- [X] T046 [P] [US3] Add failing no investment advice or market claim output test in `tests/test_corpus_episode_workflow_runner.py`
- [X] T047 [P] [US3] Add failing no MCP registry change guard coverage for 014 in `tests/test_corpus_episode_workflow_runner.py`
- [X] T048 [P] [US3] Add failing manual follow-up warnings for cache rebuild and excluded stages test in `tests/test_corpus_episode_workflow_runner.py`

### Implementation for User Story 3

- [X] T049 [US3] Harden workflow serialization and CLI errors against unsafe source content and traceback leakage in `src/podcast_ingest_core/corpus_episode_workflow_runner.py` and `scripts/run_corpus_episode_workflow.py`
- [X] T050 [US3] Implement manual-only warning rows for semantic, LLM, stock-lens, MCP, cache rebuild, and batch exclusions in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T051 [US3] Ensure selected runner failure handling records bounded category metadata and stops in `src/podcast_ingest_core/corpus_episode_workflow_runner.py`
- [X] T052 [US3] Run User Story 3 targeted tests `python -m pytest tests/test_corpus_episode_workflow_runner.py -k "manual_only or leak or boundary or investment or failure or cache or mcp" --basetemp=.pytest-tmp/run-014-us3`

**Checkpoint**: Workflow coordination preserves all existing safety boundaries and reports unsafe or excluded work as metadata only.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T053 [P] Update workflow runner documentation in `README.md`
- [X] T054 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T055 [P] Update verification mapping for workflow runner tests in `docs/verification-matrix.md`
- [X] T056 Run workflow targeted tests `python -m pytest tests/test_corpus_episode_workflow_runner.py --basetemp=.pytest-tmp/run-014-workflow`
- [X] T057 Run corpus runner regression tests `python -m pytest tests/test_corpus_episode_intake.py tests/test_corpus_audio_download_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_remediation_runner.py --basetemp=.pytest-tmp/run-014-runner-regression`
- [X] T058 Run corpus base regression tests `python -m pytest tests/test_corpus_index.py tests/test_corpus_remediation_plan.py --basetemp=.pytest-tmp/run-014-corpus-base`
- [X] T059 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-014-mcp`
- [X] T060 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-014-docs`
- [X] T061 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-014-full`
- [X] T062 Run compile check `python -m compileall src scripts`
- [X] T063 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational.
- **User Story 2 (Phase 4)**: Depends on US1 because confirmed execution uses next-stage selection.
- **User Story 3 (Phase 5)**: Depends on US1/US2 serialization and dispatch behavior.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Preview the Next Safe Stage**: MVP. Establishes dry-run stage selection and no-write behavior.
- **US2 Execute One Confirmed Next Stage**: Builds on US1 and adds one-stage confirmed dispatch/reporting.
- **US3 Preserve Safety Boundaries and Manual Follow-up**: Hardens all outputs, failures, and excluded-stage handling.

### Parallel Opportunities

- T002, T003, T004 can run in parallel after T001 fixture conventions are clear.
- US1 test tasks T011-T018 can run in parallel.
- US2 tests T026-T033 can run in parallel because they cover separate mocked stage states.
- US3 tests T043-T048 can run in parallel.
- Polish docs T053-T055 can run in parallel after implementation behavior is stable.

## Implementation Strategy

### MVP First

1. Complete Phases 1-2 to establish public contracts.
2. Complete US1 so operators can preview the next safe stage with no writes.
3. Verify US1 targeted tests before implementing confirmed dispatch.

### Incremental Delivery

1. Add US2 one-stage confirmed dispatch and workflow report writing.
2. Add US3 leak and boundary hardening.
3. Finish docs and full verification gates.

### Stop Conditions

- Stop before implementation until the user explicitly approves `$speckit-implement`.
- Stop if `$speckit-analyze` finds critical or high consistency issues.
- Stop if a task requires changing MCP registry, adding LLM execution, adding automatic cache rebuild, executing more than one stage per confirmed run, or broadening from one selector per run.

## Phase 7: Convergence

- [X] T064 Add confirmed no-executable completed-state coverage and report it as rejected or blocked per Edge Case: confirmed execution without an executable safe next stage (partial)

## Phase 8: Convergence

- [X] T065 CRITICAL add regression coverage and fail closed on every stage-probe exception without confirmed dispatch per FR-004, FR-014, and Constitution III (contradicts)
- [X] T066 CRITICAL add regression coverage and stop selection on returned `failed`, `rejected`, or `blocked` prerequisite outcomes while preserving the actual outcome per FR-005, FR-014, and the probe-failure clarification (contradicts)
- [X] T067 CRITICAL replace dependency-provided free-text propagation with bounded allowlisted workflow metadata and adversarial leak-safety coverage per FR-017, SC-007, Constitution IV, and Constitution VI (contradicts)
- [X] T068 contain unexpected intake/core exceptions at the workflow and CLI boundaries with bounded category-only output and no traceback body per US3/AC2 and FR-017 (partial)

## Phase 9: Convergence

- [ ] T069 CRITICAL add real 014 dry-run integration regressions for unseeded, audio-download, local-transcription, deterministic-remediation, completed, and blocked states that assert a full before/after tree manifest is identical, all 008-014 writer call counts are zero, stale index/plan/report sentinels are neither trusted nor overwritten, and no `.part` file appears per FR-004 and SC-001 (contradicts)
- [ ] T070 split 008 and 009 into package-private side-effect-free build snapshots and atomic persist seams while preserving the public signatures, result types, write order, payload schemas, and standalone behavior in `src/podcast_ingest_core/corpus_index.py`, `src/podcast_ingest_core/corpus_remediation_plan.py`, `tests/test_corpus_index.py`, and `tests/test_corpus_remediation_plan.py` (partial)
- [ ] T071 extract package-private plan preview seams for 012, 011, and 010, use `source_persisted=True` in their unchanged public standalone runners, and add compatibility tests proving standalone dry-run still persists fresh 008/009 but executes no side effect and writes no stage report in `src/podcast_ingest_core/corpus_audio_download_runner.py`, `src/podcast_ingest_core/corpus_local_transcription_runner.py`, `src/podcast_ingest_core/corpus_remediation_runner.py`, and their tests (partial)
- [ ] T072 CRITICAL change 014 selection to build one in-memory 008/009 snapshot for a seeded episode, pass that same snapshot through 012/011/010 previews with `source_persisted=False`, allow only the exact non-path planned-read labels `configured podcast RSS feed` and `in-memory corpus snapshot`, and preserve one-stage confirmed dispatch without public API, CLI, model, schema, or MCP changes in `src/podcast_ingest_core/corpus_episode_workflow_runner.py` (contradicts)
- [ ] T073 add deep 008/009 snapshot failure and metadata no-leak regressions plus confirmed one-stage, no cache rebuild, exact 12 MCP tools, secret/LLM/no-advice, and terminal-outcome regression gates in the relevant corpus and safety test files (partial)
- [ ] T074 align the 014 spec, plan, research, data model, contract, quickstart, safety checklist, root README, architecture, Spec registry, and verification matrix on strict zero-file dry-run semantics while preserving the historical T001-T068 task record (partial)
- [ ] T075 make `.specify/feature.json` an ignored untracked local selector, preserve `SPECIFY_FEATURE_DIRECTORY` selection, and update ADR-0006 plus gitignore/governance guard tests without changing the constitution (contradicts)
- [ ] T076 run the 014 zero-write integration tests, 010-012 standalone compatibility tests, targeted corpus/safety/docs suites, `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`; only after every gate passes mark T069-T076 complete and change 014 status from `Draft` to `Implemented` (partial)
