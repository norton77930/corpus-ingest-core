# Tasks: Corpus Artifact Index

**Input**: Design documents from `specs/008-corpus-artifact-index/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by repository TDD rules and constitution Principle IX. Write targeted tests before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks
- **[Story]**: Which user story this task belongs to
- All tasks include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared test fixtures and public path/model contracts for all user stories.

- [X] T001 Create corpus artifact fixture helpers in `tests/test_corpus_index.py`
- [X] T002 Add failing storage path contract tests for `data/corpus/{podcast_id}/corpus-index.json` and `.md` in `tests/test_corpus_index.py`
- [X] T003 Add failing public result/model contract tests for corpus index output metadata in `tests/test_corpus_index.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared core contracts that every user story depends on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add corpus index result and row models in `src/podcast_ingest_core/models.py`
- [X] T005 Add corpus index error type in `src/podcast_ingest_core/errors.py`
- [X] T006 Add `corpus_index_asset_paths(podcast_id)` helper in `src/podcast_ingest_core/storage.py`
- [X] T007 Create empty `src/podcast_ingest_core/corpus_index.py` module with public function signature and constant names
- [X] T008 Export corpus index public function and error/model types in `src/podcast_ingest_core/__init__.py`
- [X] T009 Run foundational targeted tests in `tests/test_corpus_index.py`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - View Local Corpus Status (Priority: P1) MVP

**Goal**: Generate JSON and Markdown corpus status artifacts for all locally discovered per-episode artifacts.

**Independent Test**: A fixture corpus with multiple local artifact families produces one JSON and one Markdown index with expected episode rows, artifact statuses, counts, paths, and missing artifact names.

### Tests for User Story 1

- [X] T010 [US1] Add failing empty corpus generation test in `tests/test_corpus_index.py`
- [X] T011 [US1] Add failing multi-episode local artifact discovery test in `tests/test_corpus_index.py`
- [X] T012 [US1] Add failing deterministic regeneration and no timestamp test in `tests/test_corpus_index.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement local per-episode artifact discovery for audio, transcripts, summaries, mentions, reports, mappings, and external boundaries in `src/podcast_ingest_core/corpus_index.py`
- [X] T014 [US1] Implement corpus summary counts and episode row assembly in `src/podcast_ingest_core/corpus_index.py`
- [X] T015 [US1] Implement deterministic JSON and Markdown writers in `src/podcast_ingest_core/corpus_index.py`
- [X] T016 [US1] Implement thin CLI `scripts/generate_corpus_index.py`
- [X] T017 [US1] Add CLI stdout contract test in `tests/test_corpus_index.py`
- [X] T018 [US1] Run User Story 1 targeted tests in `tests/test_corpus_index.py`

**Checkpoint**: User Story 1 is independently testable and delivers MVP value.

---

## Phase 4: User Story 2 - Identify Gaps And Unreadable Artifacts (Priority: P2)

**Goal**: Report missing artifact families and unreadable metadata without failing the whole corpus index.

**Independent Test**: A fixture corpus with missing families, duplicate candidates, and malformed JSON still produces the index and isolates warnings to affected artifacts.

### Tests for User Story 2

- [X] T019 [US2] Add failing missing artifact family test in `tests/test_corpus_index.py`
- [X] T020 [US2] Add failing unreadable JSON containment test in `tests/test_corpus_index.py`
- [X] T021 [US2] Add failing duplicate artifact candidate deterministic selection test in `tests/test_corpus_index.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement stable `missing_artifacts` calculation in `src/podcast_ingest_core/corpus_index.py`
- [X] T023 [US2] Implement unreadable JSON handling and warning aggregation in `src/podcast_ingest_core/corpus_index.py`
- [X] T024 [US2] Implement duplicate candidate counting and deterministic selection in `src/podcast_ingest_core/corpus_index.py`
- [X] T025 [US2] Run User Story 2 targeted tests in `tests/test_corpus_index.py`

**Checkpoint**: User Story 1 and User Story 2 both work independently.

---

## Phase 5: User Story 3 - See Semantic Review Readiness (Priority: P3)

**Goal**: Surface semantic summary existence and latest semantic review status metadata without reading or emitting body content.

**Independent Test**: A fixture corpus with semantic summaries and multiple timestamped semantic review reports reports the latest review status, counts, and paths only.

### Tests for User Story 3

- [X] T026 [US3] Add failing latest semantic review selection test in `tests/test_corpus_index.py`
- [X] T027 [US3] Add failing semantic summary body exclusion test in `tests/test_corpus_index.py`
- [X] T028 [US3] Add failing no review available status test in `tests/test_corpus_index.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement semantic summary path discovery and metadata-only status in `src/podcast_ingest_core/corpus_index.py`
- [X] T030 [US3] Implement latest semantic review report selection and check count extraction in `src/podcast_ingest_core/corpus_index.py`
- [X] T031 [US3] Run User Story 3 targeted tests in `tests/test_corpus_index.py`

**Checkpoint**: All user stories are independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, registry alignment, and full verification.

- [X] T032 [P] Update user-facing usage docs in `README.md`
- [X] T033 [P] Update architecture/data-flow docs in `docs/architecture.md`
- [X] T034 [P] Update feature registry mapping in `specs/README.md`
- [X] T035 [P] Update targeted verification guidance in `docs/verification-matrix.md`
- [X] T036 Verify MCP tool count remains unchanged by running `tests/test_mcp_tool_registry_contract.py`
- [X] T037 Run targeted corpus tests in `tests/test_corpus_index.py`
- [X] T038 Run docs/spec targeted tests in `tests/test_architecture_spec_docs.py` and `tests/test_spec_kit_backfill_docs.py`
- [X] T039 Run full verification: `python -m pytest`
- [X] T040 Run compile verification: `python -m compileall src scripts`
- [X] T041 Run whitespace verification: `git diff --check`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies.
- Foundational (Phase 2): depends on Setup; blocks all user stories.
- User Story 1 (Phase 3): depends on Foundational and is the MVP.
- User Story 2 (Phase 4): depends on Foundational; can be implemented after or alongside US1 once shared scanner contracts exist.
- User Story 3 (Phase 5): depends on Foundational; can be implemented after or alongside US1 once shared scanner contracts exist.
- Polish (Phase 6): depends on all desired user stories.

### User Story Dependencies

- US1: no dependency on US2 or US3.
- US2: no dependency on US3; depends only on shared scanner structure from Foundational.
- US3: no dependency on US2; depends only on shared scanner structure from Foundational.

### Within Each User Story

- Tests must be written before implementation.
- Scanner/status code must be implemented before CLI/docs validation.
- Documentation updates happen after feature behavior is stable.

## Parallel Opportunities

- T032, T033, T034, and T035 touch separate documentation files and can run in parallel after implementation behavior is stable.
- US2 and US3 can proceed in parallel after Phase 2 if coordination avoids concurrent edits to `src/podcast_ingest_core/corpus_index.py`.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases.
2. Complete User Story 1 tests and implementation.
3. Run `tests/test_corpus_index.py` for the MVP.
4. Stop and review JSON/Markdown shape before adding US2/US3.

### Incremental Delivery

1. Deliver US1 to provide the basic corpus status index.
2. Add US2 to make the index resilient for incomplete and malformed corpora.
3. Add US3 to expose semantic review readiness metadata.
4. Finish docs and full verification.
