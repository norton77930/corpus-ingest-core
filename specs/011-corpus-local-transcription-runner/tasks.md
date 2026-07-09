# Tasks: Corpus Local Transcription Runner

**Input**: Design documents from `specs/011-corpus-local-transcription-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish local transcription runner fixtures and public contract tests before implementation.

- [X] T001 Create local transcription runner fixture helpers in `tests/test_corpus_local_transcription_runner.py`
- [X] T002 [P] Add failing storage helper path contract test for `data/corpus/{podcast_id}/corpus-local-transcription-run.json` and `.md` in `tests/test_corpus_local_transcription_runner.py`
- [X] T003 [P] Add failing public result/model contract tests for local transcription filters, counts, row outcomes, warnings, and output paths in `tests/test_corpus_local_transcription_runner.py`
- [X] T004 [P] Add failing local transcription runner error contract test in `tests/test_corpus_local_transcription_runner.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T005 Add local transcription run filter, counts, row, result, and warning models in `src/podcast_ingest_core/models.py`
- [X] T006 Add local transcription runner error type in `src/podcast_ingest_core/errors.py`
- [X] T007 Add `CorpusLocalTranscriptionRunAssetPaths` and `corpus_local_transcription_run_asset_paths(podcast_id)` in `src/podcast_ingest_core/storage.py`
- [X] T008 Create `src/podcast_ingest_core/corpus_local_transcription_runner.py` with public function signature, run mode constants, transcript selection constants, and no-op-safe module skeleton
- [X] T009 Export local transcription runner public function, error, and model types from `src/podcast_ingest_core/__init__.py`
- [X] T010 Run foundational targeted tests `python -m pytest tests/test_corpus_local_transcription_runner.py -k "contract or storage or error" --basetemp=.pytest-tmp/run-011-foundation`

**Checkpoint**: Public contracts and module boundaries exist, but runner behavior is not complete.

---

## Phase 3: User Story 1 - Preview Local Transcription Backlog (Priority: P1) MVP

**Goal**: Generate dry-run selection metadata from a refreshed 009 remediation plan without loading transcription models, executing transcription, or writing run report artifacts.

**Independent Test**: A local corpus fixture returns deterministic dry-run rows and counts for eligible local-audio transcript gaps and skipped unsafe states, while no run report artifact or transcript output is written.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing empty corpus dry-run no-write test in `tests/test_corpus_local_transcription_runner.py`
- [X] T012 [P] [US1] Add failing refresh-before-selection test proving `generate_corpus_remediation_plan()` runs before local transcription selection in `tests/test_corpus_local_transcription_runner.py`
- [X] T013 [P] [US1] Add failing local-audio transcript-missing selection test in `tests/test_corpus_local_transcription_runner.py`
- [X] T014 [P] [US1] Add failing skipped unsafe transcript states test for missing audio, unreadable, corrupt, partial, incomplete, valid existing, and empty existing transcripts in `tests/test_corpus_local_transcription_runner.py`
- [X] T015 [P] [US1] Add failing dry-run no transcription, no download, no whisper/model load, and no report write boundary test in `tests/test_corpus_local_transcription_runner.py`
- [X] T016 [P] [US1] Add failing deterministic dry-run and no `generated_at` test in `tests/test_corpus_local_transcription_runner.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement refreshed remediation plan loading and empty corpus dry-run handling in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T018 [US1] Implement local transcription selection for transcript ready actions with existing local audio path and transcript status `missing` in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T019 [US1] Implement skipped row reasons for missing audio, unsafe transcript states, non-transcript families, blocked actions, and non-ready source statuses in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T020 [US1] Implement dry-run result serialization with null report paths and no artifact writes in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T021 [US1] Implement thin dry-run CLI `scripts/run_corpus_local_transcription.py`
- [X] T022 [US1] Add CLI dry-run stdout contract test for output paths and counts in `tests/test_corpus_local_transcription_runner.py`
- [X] T023 [US1] Run User Story 1 targeted tests `python -m pytest tests/test_corpus_local_transcription_runner.py -k "dry_run or selection or unsafe or no_write or generated_at or cli" --basetemp=.pytest-tmp/run-011-us1`

**Checkpoint**: User can preview eligible local transcription work without any write, download, model-load, or transcription side effects.

---

## Phase 4: User Story 2 - Execute One Local Transcription (Priority: P2)

**Goal**: Execute confirmed local transcription for exactly one eligible episode using an explicit local audio path and write latest run report artifacts.

**Independent Test**: Confirmed execution rejects missing episode references, applies single-episode selection, passes explicit local audio path to transcription, never downloads audio, and writes deterministic JSON/Markdown run reports.

### Tests for User Story 2

- [X] T024 [P] [US2] Add failing confirmed execution rejects missing episode reference before transcription test in `tests/test_corpus_local_transcription_runner.py`
- [X] T025 [P] [US2] Add failing confirmed execution rejects or records non-eligible episode without transcription test in `tests/test_corpus_local_transcription_runner.py`
- [X] T026 [P] [US2] Add failing confirmed execution passes explicit local `audio_path` and `force=False` to transcription core test in `tests/test_corpus_local_transcription_runner.py`
- [X] T027 [P] [US2] Add failing confirmed execution never calls `download_audio` or shell subprocess test in `tests/test_corpus_local_transcription_runner.py`
- [X] T028 [P] [US2] Add failing runtime option propagation test for `model`, `device`, `compute_type`, and `vad_filter` in `tests/test_corpus_local_transcription_runner.py`
- [X] T029 [P] [US2] Add failing confirmed run report JSON/Markdown writer test in `tests/test_corpus_local_transcription_runner.py`

### Implementation for User Story 2

- [X] T030 [US2] Implement confirmed execution episode validation and pre-transcription rejection in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T031 [US2] Implement transcription dispatch using existing core function with explicit local `audio_path`, `force=False`, and runtime options in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T032 [US2] Implement transcript output path extraction and `executed` versus `reused` outcome mapping in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T033 [US2] Implement deterministic confirmed JSON and Markdown run report writers in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T034 [US2] Extend CLI parsing for `--confirm`, `--episode`, `--model`, `--device`, `--compute-type`, and `--vad-filter` in `scripts/run_corpus_local_transcription.py`
- [X] T035 [US2] Add CLI confirmed stdout and stderr contract tests in `tests/test_corpus_local_transcription_runner.py`
- [X] T036 [US2] Run User Story 2 targeted tests `python -m pytest tests/test_corpus_local_transcription_runner.py -k "confirm or episode or audio_path or download or runtime or report or cli" --basetemp=.pytest-tmp/run-011-us2`

**Checkpoint**: User can execute one bounded local transcription and receive an auditable run report.

---

## Phase 5: User Story 3 - Contain Transcription Failures and Preserve Boundaries (Priority: P3)

**Goal**: Record transcription failures without leaking raw transcript text, secrets, traceback bodies, or weakening no-download/no-LLM/no-MCP/no-cache boundaries.

**Independent Test**: A failing transcription dependency records failure metadata only, writes safe run outputs when appropriate, and emits no raw transcript, prompt, raw LLM output, secret values, or traceback bodies.

### Tests for User Story 3

- [X] T037 [P] [US3] Add failing transcription dependency failure containment test in `tests/test_corpus_local_transcription_runner.py`
- [X] T038 [P] [US3] Add failing no raw transcript/prompt/raw LLM output/secret/traceback leakage test for JSON, Markdown, stdout, and stderr in `tests/test_corpus_local_transcription_runner.py`
- [X] T039 [P] [US3] Add failing boundary guard test for RSS, network, SQLite cache rebuild, `.env`, LLM provider, MCP, download, semantic execution, downstream remediation, stock-lens, and synthesis in `tests/test_corpus_local_transcription_runner.py`
- [X] T040 [P] [US3] Add failing no investment advice and external-status-as-market-fact output test in `tests/test_corpus_local_transcription_runner.py`
- [X] T041 [P] [US3] Add failing manual cache stale warning metadata test after confirmed transcript writes in `tests/test_corpus_local_transcription_runner.py`

### Implementation for User Story 3

- [X] T042 [US3] Implement per-episode transcription exception capture and failure row serialization without traceback leakage in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T043 [US3] Harden JSON, Markdown, stdout, and stderr serialization against raw transcript, prompt, raw LLM output, secrets, traceback bodies, market facts, and investment advice in `src/podcast_ingest_core/corpus_local_transcription_runner.py` and `scripts/run_corpus_local_transcription.py`
- [X] T044 [US3] Add manual cache stale warning metadata for confirmed writes without calling `rebuild_cache` in `src/podcast_ingest_core/corpus_local_transcription_runner.py`
- [X] T045 [US3] Run User Story 3 targeted tests `python -m pytest tests/test_corpus_local_transcription_runner.py -k "failure or leak or boundary or investment or cache" --basetemp=.pytest-tmp/run-011-us3`

**Checkpoint**: Failed local transcription is isolated and safety boundaries remain explicit.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T046 [P] Update local transcription runner documentation in `README.md`
- [X] T047 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T048 [P] Update verification mapping for local transcription runner tests in `docs/verification-matrix.md`
- [X] T049 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-011-mcp`
- [X] T050 Run corpus regression tests `python -m pytest tests/test_corpus_local_transcription_runner.py tests/test_corpus_remediation_plan.py tests/test_corpus_index.py --basetemp=.pytest-tmp/run-011-corpus`
- [X] T051 Run transcription regression tests `python -m pytest tests/test_transcriber.py --basetemp=.pytest-tmp/run-011-transcriber`
- [X] T052 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-011-docs`
- [X] T053 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-011-full`
- [X] T054 Run compile check `python -m compileall src scripts`
- [X] T055 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and should be implemented after US1 selection exists.
- **User Story 3 (Phase 5)**: Depends on Phase 2 and can proceed after US2 execution dispatch exists.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1**: Required MVP. Establishes refreshed plan loading, dry-run local selection, skipped reasons, counts, no-write behavior, and CLI preview.
- **US2**: Extends US1 with confirmed single-episode validation, local transcription dispatch, and run report artifacts.
- **US3**: Extends US2 with failure containment and safety boundary hardening.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T011 through T016 can be written in parallel after Phase 2.
- T024 through T029 can be written in parallel after US1 test fixtures exist.
- T037 through T041 can be written in parallel after US2 execution fixtures exist.
- T046 through T048 can run in parallel after runtime behavior is stable.

---

## Parallel Example: User Story 1

```text
Task: "Add failing empty corpus dry-run no-write test in tests/test_corpus_local_transcription_runner.py"
Task: "Add failing refresh-before-selection test proving generate_corpus_remediation_plan() runs before local transcription selection in tests/test_corpus_local_transcription_runner.py"
Task: "Add failing local-audio transcript-missing selection test in tests/test_corpus_local_transcription_runner.py"
Task: "Add failing skipped unsafe transcript states test for missing audio, unreadable, corrupt, partial, incomplete, valid existing, and empty existing transcripts in tests/test_corpus_local_transcription_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup tests.
2. Complete Phase 2 public contracts and module skeleton.
3. Complete Phase 3 User Story 1.
4. Run `tests/test_corpus_local_transcription_runner.py` for the MVP.
5. Stop and validate dry-run no-write, no-download, and no-model-load behavior before adding confirmed execution.

### Incremental Delivery

1. Deliver US1 to preview safe local transcription work.
2. Add US2 to execute one bounded local transcription and write run reports.
3. Add US3 to contain failures and prove safety boundaries.
4. Run full verification before claiming implementation complete.

### Boundary Rules

- Do not write artifacts during dry-run.
- Do not execute confirmed runs without one episode reference.
- Do not execute audio download, RSS reads, network calls, semantic summary, semantic review, deterministic downstream remediation, stock-lens, synthesis, unknown, blocked, optional, or gated actions.
- Do not repair or overwrite corrupt, unreadable, partial, incomplete, valid, or empty transcript outputs in v1.
- Do not add MCP tools or change MCP envelopes.
- Do not read SQLite cache, `.env`, API keys, live market data, stock-lens query artifacts, or stock-lens synthesis artifacts.
- Do not include raw transcript, prompt text, raw LLM output, traceback bodies, or secret values in JSON, Markdown, stdout, stderr, or tests.
- Do not automatically rebuild cache.
- Do not provide investment advice.
