# Tasks: Corpus Episode Intake Bootstrap

**Input**: Design documents from `specs/013-corpus-episode-intake-bootstrap/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish episode intake fixtures and public contract tests before implementation.

- [X] T001 Create episode intake fixture helpers in `tests/test_corpus_episode_intake.py`
- [X] T002 [P] Add failing storage helper path contract tests for episode seed path and intake run JSON/Markdown paths in `tests/test_corpus_episode_intake.py`
- [X] T003 [P] Add failing public result/model contract tests for intake filters, counts, rows, warnings, seed metadata, and output paths in `tests/test_corpus_episode_intake.py`
- [X] T004 [P] Add failing episode intake error contract test in `tests/test_corpus_episode_intake.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T005 Add episode intake filter, counts, row, seed, result, and warning models in `src/corpus_ingest_core/models.py`
- [X] T006 Add episode intake error type in `src/corpus_ingest_core/errors.py`
- [X] T007 Add `CorpusEpisodeIntakeRunAssetPaths`, `corpus_episode_seed_asset_path(podcast_id, episode_ref)`, and `corpus_episode_intake_run_asset_paths(podcast_id)` in `src/corpus_ingest_core/storage.py`
- [X] T008 Create `src/corpus_ingest_core/corpus_episode_intake.py` with public function signature, run mode constants, selector constants, and no-op-safe module skeleton
- [X] T009 Export episode intake public function, error, storage helper, and model types from `src/corpus_ingest_core/__init__.py`
- [X] T010 Run foundational targeted tests `python -m pytest tests/test_corpus_episode_intake.py -k "contract or storage or error" --basetemp=.pytest-tmp/run-013-foundation`

**Checkpoint**: Public contracts and module boundaries exist, but intake behavior is not complete.

---

## Phase 3: User Story 1 - Preview Episode Intake (Priority: P1) MVP

**Goal**: Resolve `latest` or one explicit episode selector from configured RSS and return metadata-only dry-run output without writes.

**Independent Test**: A feed fixture returns deterministic dry-run rows and counts for latest, explicit, unresolved, and blank selector cases while no seed or report artifacts are written.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing dry-run latest resolution no-write test in `tests/test_corpus_episode_intake.py`
- [X] T012 [P] [US1] Add failing dry-run explicit episode resolution test for `EP677` in `tests/test_corpus_episode_intake.py`
- [X] T013 [P] [US1] Add failing blank or missing selector defaults to `latest` test in `tests/test_corpus_episode_intake.py`
- [X] T014 [P] [US1] Add failing unresolved selector rejected without seed/report write test in `tests/test_corpus_episode_intake.py`
- [X] T015 [P] [US1] Add failing dry-run does not call downloader, transcriber, remediation runner, cache rebuild, LLM, `.env`, or MCP boundary test in `tests/test_corpus_episode_intake.py`
- [X] T016 [P] [US1] Add failing dry-run deterministic output and no `generated_at` test in `tests/test_corpus_episode_intake.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement selector normalization for missing, blank, `latest`, and explicit episode refs in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T018 [US1] Implement feed resolution through existing `get_episode(podcast_id, episode_ref)` in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T019 [US1] Implement safe metadata extraction that omits source URLs, audio URLs, query strings, raw descriptions, and feed HTML body in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T020 [US1] Implement dry-run result serialization with null report paths, planned seed/report writes only, and no artifact writes in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T021 [US1] Implement thin dry-run CLI `scripts/run_corpus_episode_intake.py`
- [X] T022 [US1] Add CLI dry-run stdout contract test for selector, resolved episode, output paths, and counts in `tests/test_corpus_episode_intake.py`
- [X] T023 [US1] Run User Story 1 targeted tests `python -m pytest tests/test_corpus_episode_intake.py -k "dry_run or latest or explicit or selector or no_write or generated_at or cli" --basetemp=.pytest-tmp/run-013-us1`

**Checkpoint**: User can preview latest or explicit episode intake without writes or downstream side effects.

---

## Phase 4: User Story 2 - Seed One Episode Into Corpus (Priority: P2)

**Goal**: Confirm intake for one resolved episode, write deterministic seed metadata and latest report artifacts, and make the episode visible to 008/009/012.

**Independent Test**: Confirmed execution writes one seed and one report pair; 008 discovers the seeded episode; 009 emits a ready audio action; 012 dry-run selects that action.

### Tests for User Story 2

- [X] T024 [P] [US2] Add failing confirmed run writes deterministic seed metadata and run report test in `tests/test_corpus_episode_intake.py`
- [X] T025 [P] [US2] Add failing repeated confirmed run records reused outcome without duplicate seed files test in `tests/test_corpus_episode_intake.py`
- [X] T026 [P] [US2] Add failing confirmed unresolved selector writes rejected report without seed test in `tests/test_corpus_episode_intake.py`
- [X] T027 [P] [US2] Add failing 008 discovers seeded episode metadata test in `tests/test_corpus_index.py`
- [X] T028 [P] [US2] Add failing 009 creates ready audio remediation action for seeded missing-audio episode with feed audio availability and non-ready action for seeded no-audio episode test in `tests/test_corpus_remediation_plan.py`
- [X] T029 [P] [US2] Add failing 012 dry-run selects seeded missing-audio episode with feed audio availability and skips seeded no-audio episode test in `tests/test_corpus_audio_download_runner.py`
- [X] T030 [P] [US2] Add failing confirmed intake does not call `download_audio()`, `transcribe_episode()`, `run_corpus_remediation()`, or `rebuild_cache()` test in `tests/test_corpus_episode_intake.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement deterministic seed JSON writer with atomic `.part` replace in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T032 [US2] Implement seed reuse detection and reused outcome mapping in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T033 [US2] Implement confirmed rejected report behavior for unresolved selectors without seed writes in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T034 [US2] Implement deterministic intake run JSON and Markdown report writers in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T035 [US2] Extend 008 episode discovery and title metadata to include seed metadata in `src/corpus_ingest_core/corpus_index.py`
- [X] T036 [US2] Extend 009 audio action readiness logic for seeded missing-audio episodes with feed audio availability and no-audio feed metadata in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T037 [US2] Ensure 012 audio runner selection accepts seeded ready audio actions without requiring local audio in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T038 [US2] Extend CLI parsing for `--confirm` and `--episode` in `scripts/run_corpus_episode_intake.py`
- [X] T039 [US2] Add CLI confirmed stdout and stderr contract tests in `tests/test_corpus_episode_intake.py`
- [X] T040 [US2] Run User Story 2 targeted tests `python -m pytest tests/test_corpus_episode_intake.py tests/test_corpus_index.py tests/test_corpus_remediation_plan.py tests/test_corpus_audio_download_runner.py -k "seed or seeded or reuse or rejected or corpus_episode_intake or (ready and audio)" --basetemp=.pytest-tmp/run-013-us2`

**Checkpoint**: User can seed one episode and the existing corpus chain can plan and select follow-up audio download work.

---

## Phase 5: User Story 3 - Preserve Boundaries and Safe Output (Priority: P3)

**Goal**: Bound feed failures and unsafe feed content without leaking full URLs, query strings, raw descriptions, prompt-like text, raw LLM-looking text, secrets, or traceback bodies.

**Independent Test**: Feed resolution and output fixtures containing unsafe values produce only safe metadata in JSON, Markdown, stdout, stderr, seed metadata, and errors.

### Tests for User Story 3

- [X] T041 [P] [US3] Add failing no full source URL/audio URL/query string/raw description/prompt/raw LLM output/secret/traceback leakage test for dry-run JSON, confirmed report, seed JSON, stdout, and stderr in `tests/test_corpus_episode_intake.py`
- [X] T042 [P] [US3] Add failing feed reader dependency failure containment test in `tests/test_corpus_episode_intake.py`
- [X] T043 [P] [US3] Add failing boundary guard test for no download, transcription, deterministic downstream remediation, `.env`, LLM provider, MCP, semantic execution, stock-lens, synthesis, and cache rebuild in `tests/test_corpus_episode_intake.py`
- [X] T044 [P] [US3] Add failing no investment advice and external-status-as-market-fact output test in `tests/test_corpus_episode_intake.py`
- [X] T045 [P] [US3] Add failing manual follow-up warning metadata test after confirmed seed without running 008/009/012/011/010 or cache rebuild in `tests/test_corpus_episode_intake.py`

### Implementation for User Story 3

- [X] T046 [US3] Implement bounded feed resolution exception capture without raw exception text or traceback leakage in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T047 [US3] Harden JSON, Markdown, stdout, stderr, and seed serialization against full URLs, query strings, raw descriptions, prompts, raw LLM output, secrets, traceback bodies, market facts, and investment advice in `src/corpus_ingest_core/corpus_episode_intake.py` and `scripts/run_corpus_episode_intake.py`
- [X] T048 [US3] Add manual follow-up warning metadata for confirmed seed writes or reuse without calling index, remediation plan, audio download, transcription, downstream remediation, or cache rebuild in `src/corpus_ingest_core/corpus_episode_intake.py`
- [X] T049 [US3] Run User Story 3 targeted tests `python -m pytest tests/test_corpus_episode_intake.py -k "failure or leak or boundary or investment or follow_up or cache" --basetemp=.pytest-tmp/run-013-us3`

**Checkpoint**: Feed intake failure and unsafe metadata are isolated and safety boundaries remain explicit.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T050 [P] Update episode intake documentation in `README.md`
- [X] T051 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T052 [P] Update verification mapping for episode intake tests in `docs/verification-matrix.md`
- [X] T053 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-013-mcp`
- [X] T054 Run corpus regression tests `python -m pytest tests/test_corpus_episode_intake.py tests/test_corpus_index.py tests/test_corpus_remediation_plan.py tests/test_corpus_audio_download_runner.py --basetemp=.pytest-tmp/run-013-corpus`
- [X] T055 Run feed reader regression tests `python -m pytest tests/test_feed_reader.py --basetemp=.pytest-tmp/run-013-feed`
- [X] T056 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-013-docs`
- [X] T057 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-013-full`
- [X] T058 Run compile check `python -m compileall src scripts`
- [X] T059 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational.
- **User Story 2 (Phase 4)**: Depends on US1 because confirmed seeding uses selector resolution.
- **User Story 3 (Phase 5)**: Depends on US1/US2 serialization and report paths.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Preview Episode Intake**: MVP. Establishes selector resolution and dry-run no-write behavior.
- **US2 Seed One Episode Into Corpus**: Builds on US1 and integrates seed metadata with 008/009/012.
- **US3 Preserve Boundaries and Safe Output**: Hardens all outputs and failure paths.

### Parallel Opportunities

- T002, T003, T004 can run in parallel after T001 fixture conventions are clear.
- US1 test tasks T011-T016 can run in parallel.
- US2 tests T024-T030 can run in parallel because they cover separate files or fixtures.
- US3 tests T041-T045 can run in parallel.
- Polish docs T050-T052 can run in parallel after implementation behavior is stable.

## Implementation Strategy

### MVP First

1. Complete Phases 1-2 to establish public contracts.
2. Complete US1 to preview `latest` and explicit episode selectors with no writes.
3. Verify US1 targeted tests before implementing seed writes.

### Incremental Delivery

1. Add US2 confirmed seed writes and 008/009/012 integration.
2. Add US3 leak and boundary hardening.
3. Finish docs and full verification gates.

### Stop Conditions

- Stop before implementation until the user explicitly approves `$speckit-implement`.
- Stop if `$speckit-analyze` finds critical or high consistency issues.
- Stop if a task requires changing MCP registry, adding LLM execution, adding cache rebuild automation, or broadening from one selector per run.
