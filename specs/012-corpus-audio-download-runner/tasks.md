# Tasks: Corpus Audio Download Runner

**Input**: Design documents from `specs/012-corpus-audio-download-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish audio download runner fixtures and public contract tests before implementation.

- [X] T001 Create audio download runner fixture helpers in `tests/test_corpus_audio_download_runner.py`
- [X] T002 [P] Add failing storage helper path contract test for `data/corpus/{podcast_id}/corpus-audio-download-run.json` and `.md` in `tests/test_corpus_audio_download_runner.py`
- [X] T003 [P] Add failing public result/model contract tests for audio download filters, counts, row outcomes, warnings, and output paths in `tests/test_corpus_audio_download_runner.py`
- [X] T004 [P] Add failing audio download runner error contract test in `tests/test_corpus_audio_download_runner.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T005 Add audio download run filter, counts, row, result, and warning models in `src/corpus_ingest_core/models.py`
- [X] T006 Add audio download runner error type in `src/corpus_ingest_core/errors.py`
- [X] T007 Add `CorpusAudioDownloadRunAssetPaths` and `corpus_audio_download_run_asset_paths(podcast_id)` in `src/corpus_ingest_core/storage.py`
- [X] T008 Create `src/corpus_ingest_core/corpus_audio_download_runner.py` with public function signature, run mode constants, audio selection constants, and no-op-safe module skeleton
- [X] T009 Export audio download runner public function, error, and model types from `src/corpus_ingest_core/__init__.py`
- [X] T010 Run foundational targeted tests `python -m pytest tests/test_corpus_audio_download_runner.py -k "contract or storage or error" --basetemp=.pytest-tmp/run-012-foundation`

**Checkpoint**: Public contracts and module boundaries exist, but runner behavior is not complete.

---

## Phase 3: User Story 1 - Preview Audio Download Backlog (Priority: P1) MVP

**Goal**: Generate dry-run selection metadata from a refreshed 009 remediation plan without reading RSS, calling network, executing download, or writing run report artifacts.

**Independent Test**: A local corpus fixture returns deterministic dry-run rows and counts for eligible missing-audio gaps and skipped unsafe states, while no run report artifact or audio output is written.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing empty corpus dry-run no-write test in `tests/test_corpus_audio_download_runner.py`
- [X] T012 [P] [US1] Add failing refresh-before-selection test proving `generate_corpus_remediation_plan()` runs before audio download selection in `tests/test_corpus_audio_download_runner.py`
- [X] T013 [P] [US1] Add failing missing-audio ready-action selection test in `tests/test_corpus_audio_download_runner.py`
- [X] T014 [P] [US1] Add failing skipped unsafe states test for available audio, blocked audio, non-ready audio, transcript, semantic, downstream, stock-lens, synthesis, and unknown families in `tests/test_corpus_audio_download_runner.py`
- [X] T015 [P] [US1] Add failing dry-run no RSS, no network, no downloader call, and no report write boundary test in `tests/test_corpus_audio_download_runner.py`
- [X] T016 [P] [US1] Add failing deterministic dry-run and no `generated_at` test in `tests/test_corpus_audio_download_runner.py`

### Implementation for User Story 1

- [X] T017 [US1] Implement refreshed remediation plan loading and empty corpus dry-run handling in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T018 [US1] Implement audio selection for ready audio actions with audio status exactly `missing` in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T019 [US1] Implement skipped row reasons for available audio, blocked audio, non-ready source statuses, non-audio families, optional/gated actions, and unknown families in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T020 [US1] Implement dry-run result serialization with null report paths and no artifact writes in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T021 [US1] Implement thin dry-run CLI `scripts/run_corpus_audio_download.py`
- [X] T022 [US1] Add CLI dry-run stdout contract test for output paths and counts in `tests/test_corpus_audio_download_runner.py`
- [X] T023 [US1] Run User Story 1 targeted tests `python -m pytest tests/test_corpus_audio_download_runner.py -k "dry_run or selection or unsafe or no_write or generated_at or cli" --basetemp=.pytest-tmp/run-012-us1`

**Checkpoint**: User can preview eligible audio download work without write, RSS, network, downloader, transcription, or report side effects.

---

## Phase 4: User Story 2 - Execute One Audio Download (Priority: P2)

**Goal**: Execute confirmed audio download for exactly one eligible episode using the existing downloader and write latest run report artifacts.

**Independent Test**: Confirmed execution rejects missing or blank episode references, applies single-episode selection, calls `download_audio()` exactly once for eligible rows, never shells out, and writes deterministic JSON/Markdown run reports.

### Tests for User Story 2

- [X] T024 [P] [US2] Add failing confirmed execution rejects missing, empty, and whitespace episode reference before downloader call test in `tests/test_corpus_audio_download_runner.py`
- [X] T025 [P] [US2] Add failing confirmed execution records absent requested episode as rejected without downloader call test in `tests/test_corpus_audio_download_runner.py`
- [X] T026 [P] [US2] Add failing confirmed execution records present but non-selected episode as rejected without downloader call test in `tests/test_corpus_audio_download_runner.py`
- [X] T027 [P] [US2] Add failing confirmed execution calls `download_audio(podcast_id, episode_ref)` exactly once for selected episode test in `tests/test_corpus_audio_download_runner.py`
- [X] T028 [P] [US2] Add failing confirmed execution never shells out to scripts test in `tests/test_corpus_audio_download_runner.py`
- [X] T029 [P] [US2] Add failing downloaded versus reused outcome mapping test from downloader `AudioAsset` metadata in `tests/test_corpus_audio_download_runner.py`
- [X] T030 [P] [US2] Add failing confirmed run report JSON/Markdown writer test with no `generated_at` in `tests/test_corpus_audio_download_runner.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement confirmed execution episode normalization, validation, and pre-download rejection in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T032 [US2] Implement synthetic rejected row for requested episode absent from refreshed remediation plan in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T033 [US2] Implement download dispatch using existing `download_audio(podcast_id, episode_ref)` in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T034 [US2] Implement downloaded versus reused outcome mapping and local output metadata extraction in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T035 [US2] Implement deterministic confirmed JSON and Markdown run report writers in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T036 [US2] Extend CLI parsing for `--confirm` and `--episode` in `scripts/run_corpus_audio_download.py`
- [X] T037 [US2] Add CLI confirmed stdout and stderr contract tests in `tests/test_corpus_audio_download_runner.py`
- [X] T038 [US2] Run User Story 2 targeted tests `python -m pytest tests/test_corpus_audio_download_runner.py -k "confirm or episode or download_audio or shell or reused or report or cli" --basetemp=.pytest-tmp/run-012-us2`

**Checkpoint**: User can execute one bounded audio download and receive an auditable run report.

---

## Phase 5: User Story 3 - Contain Download Failures and Preserve Boundaries (Priority: P3)

**Goal**: Record download failures without leaking full source URLs, query strings, secrets, traceback bodies, or weakening no-transcription/no-LLM/no-MCP/no-cache boundaries.

**Independent Test**: A failing downloader dependency records failure metadata only, writes safe run outputs when appropriate, and emits no source URL, prompt, raw LLM output, secret values, or traceback bodies.

### Tests for User Story 3

- [X] T039 [P] [US3] Add failing downloader dependency failure containment test in `tests/test_corpus_audio_download_runner.py`
- [X] T040 [P] [US3] Add failing no full source URL/query string/prompt/raw LLM output/secret/traceback leakage test for JSON, Markdown, stdout, and stderr in `tests/test_corpus_audio_download_runner.py`
- [X] T041 [P] [US3] Add failing boundary guard test for transcription, deterministic downstream remediation, RSS/network during dry-run, SQLite cache rebuild, `.env`, LLM provider, MCP, semantic execution, stock-lens, and synthesis in `tests/test_corpus_audio_download_runner.py`
- [X] T042 [P] [US3] Add failing no investment advice and external-status-as-market-fact output test in `tests/test_corpus_audio_download_runner.py`
- [X] T043 [P] [US3] Add failing manual follow-up warning metadata test after confirmed audio download or reuse without calling transcription, remediation, or cache rebuild in `tests/test_corpus_audio_download_runner.py`

### Implementation for User Story 3

- [X] T044 [US3] Implement per-episode downloader exception capture and failure row serialization without raw exception text or traceback leakage in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T045 [US3] Harden JSON, Markdown, stdout, and stderr serialization against full source URLs, query strings, prompts, raw LLM output, secrets, traceback bodies, market facts, and investment advice in `src/corpus_ingest_core/corpus_audio_download_runner.py` and `scripts/run_corpus_audio_download.py`
- [X] T046 [US3] Add manual follow-up warning metadata for confirmed audio writes or reuse without calling `transcribe_episode`, `run_corpus_remediation`, or `rebuild_cache` in `src/corpus_ingest_core/corpus_audio_download_runner.py`
- [X] T047 [US3] Run User Story 3 targeted tests `python -m pytest tests/test_corpus_audio_download_runner.py -k "failure or leak or boundary or investment or follow_up or cache" --basetemp=.pytest-tmp/run-012-us3`

**Checkpoint**: Failed audio download is isolated and safety boundaries remain explicit.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T048 [P] Update audio download runner documentation in `README.md`
- [X] T049 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T050 [P] Update verification mapping for audio download runner tests in `docs/verification-matrix.md`
- [X] T051 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-012-mcp`
- [X] T052 Run corpus regression tests `python -m pytest tests/test_corpus_audio_download_runner.py tests/test_corpus_remediation_plan.py tests/test_corpus_index.py tests/test_corpus_local_transcription_runner.py --basetemp=.pytest-tmp/run-012-corpus`
- [X] T053 Run downloader regression tests `python -m pytest tests/test_downloader.py --basetemp=.pytest-tmp/run-012-downloader`
- [X] T054 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-012-docs`
- [X] T055 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-012-full`
- [X] T056 Run compile check `python -m compileall src scripts`
- [X] T057 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

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

- **US1**: Required MVP. Establishes refreshed plan loading, dry-run audio selection, skipped reasons, counts, no-write/no-network behavior, and CLI preview.
- **US2**: Extends US1 with confirmed single-episode validation, audio download dispatch, and run report artifacts.
- **US3**: Extends US2 with failure containment and safety boundary hardening.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T011 through T016 can be written in parallel after Phase 2.
- T024 through T030 can be written in parallel after US1 test fixtures exist.
- T039 through T043 can be written in parallel after US2 execution fixtures exist.
- T048 through T050 can run in parallel after runtime behavior is stable.

---

## Parallel Example: User Story 1

```text
Task: "Add failing empty corpus dry-run no-write test in tests/test_corpus_audio_download_runner.py"
Task: "Add failing refresh-before-selection test proving generate_corpus_remediation_plan() runs before audio download selection in tests/test_corpus_audio_download_runner.py"
Task: "Add failing missing-audio ready-action selection test in tests/test_corpus_audio_download_runner.py"
Task: "Add failing dry-run no RSS, no network, no downloader call, and no report write boundary test in tests/test_corpus_audio_download_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup tests.
2. Complete Phase 2 public contracts and module skeleton.
3. Complete Phase 3 User Story 1.
4. Run `tests/test_corpus_audio_download_runner.py` for the MVP.
5. Stop and validate dry-run no-write, no-RSS, no-network, and no-downloader behavior before adding confirmed execution.

### Incremental Delivery

1. Deliver US1 to preview safe audio download work.
2. Add US2 to execute one bounded audio download and write run reports.
3. Add US3 to contain failures and prove safety boundaries.
4. Run full verification before claiming implementation complete.

### Boundary Rules

- Do not write artifacts during dry-run.
- Do not read RSS, call network, or call `download_audio()` during dry-run.
- Do not execute confirmed runs without one non-empty episode reference.
- Do not execute transcription, deterministic downstream remediation, semantic summary, semantic review, stock-lens, synthesis, unknown, blocked, optional, or gated actions.
- Do not add MCP tools or change MCP envelopes.
- Do not read SQLite cache, `.env`, API keys, live market data, stock-lens query artifacts, or stock-lens synthesis artifacts.
- Do not include full source URLs, URL query strings, raw transcript, prompt text, raw LLM output, traceback bodies, or secret values in JSON, Markdown, stdout, stderr, or tests.
- Do not automatically transcribe, run downstream remediation, or rebuild cache after confirmed audio writes or reuse.
- Do not provide investment advice.
