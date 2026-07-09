# Tasks: Corpus Remediation Runner

**Input**: Design documents from `specs/010-corpus-remediation-runner/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish runner test fixtures and public contract tests before implementation.

- [X] T001 Create corpus remediation runner fixture helpers in `tests/test_corpus_remediation_runner.py`
- [X] T002 [P] Add failing storage helper path contract test for `data/corpus/{podcast_id}/corpus-remediation-run.json` and `.md` in `tests/test_corpus_remediation_runner.py`
- [X] T003 [P] Add failing public result/model contract tests for runner filters, counts, row outcomes, and output paths in `tests/test_corpus_remediation_runner.py`
- [X] T004 [P] Add failing runner error contract test in `tests/test_corpus_remediation_runner.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T005 Add corpus remediation run filter, counts, row, result, and warning models in `src/podcast_ingest_core/models.py`
- [X] T006 Add corpus remediation runner error type in `src/podcast_ingest_core/errors.py`
- [X] T007 Add `CorpusRemediationRunAssetPaths` and `corpus_remediation_run_asset_paths(podcast_id)` in `src/podcast_ingest_core/storage.py`
- [X] T008 Create `src/podcast_ingest_core/corpus_remediation_runner.py` with public function signature, deterministic allowlist constants, excluded family constants, and no-op-safe module skeleton
- [X] T009 Export runner public function, error, and model types from `src/podcast_ingest_core/__init__.py`
- [X] T010 Run foundational targeted tests `python -m pytest tests/test_corpus_remediation_runner.py -k "contract or storage or error" --basetemp=.pytest-tmp/run-010-foundation`

**Checkpoint**: Public contracts and module boundaries exist, but runner behavior is not complete.

---

## Phase 3: User Story 1 - Preview Safe Corpus Remediation (Priority: P1) MVP

**Goal**: Generate dry-run selection metadata from a refreshed 009 remediation plan without executing actions or writing run report artifacts.

**Independent Test**: A local corpus with empty and multi-action fixture states returns deterministic dry-run rows and counts, excludes non-deterministic families, and writes no run report artifact.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing empty corpus dry-run no-write test in `tests/test_corpus_remediation_runner.py`
- [X] T012 [P] [US1] Add failing refresh-before-selection test proving `generate_corpus_remediation_plan()` runs before selection in `tests/test_corpus_remediation_runner.py`
- [X] T013 [P] [US1] Add failing dry-run selected deterministic families and excluded non-deterministic families test in `tests/test_corpus_remediation_runner.py`
- [X] T014 [P] [US1] Add failing blocked and skipped source action visibility test in `tests/test_corpus_remediation_runner.py`
- [X] T015 [P] [US1] Add failing deterministic dry-run and no `generated_at` test in `tests/test_corpus_remediation_runner.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement refreshed remediation plan loading and empty corpus dry-run handling in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T017 [US1] Implement deterministic action selection, exclusion reasons, blocked rows, skipped rows, and dry-run counts in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T018 [US1] Implement dry-run serialization result with null report paths and no artifact writes in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T019 [US1] Implement thin dry-run CLI `scripts/run_corpus_remediation.py`
- [X] T020 [US1] Add CLI dry-run stdout contract test for output paths and counts in `tests/test_corpus_remediation_runner.py`
- [X] T021 [US1] Run User Story 1 targeted tests `python -m pytest tests/test_corpus_remediation_runner.py -k "dry_run or excluded or blocked or generated_at or cli" --basetemp=.pytest-tmp/run-010-us1`

**Checkpoint**: User can preview selected deterministic corpus remediation actions without any write side effects.

---

## Phase 4: User Story 2 - Execute Filtered Deterministic Remediation (Priority: P2)

**Goal**: Execute only ready deterministic actions during confirmed, filter-bounded runs and write latest run report artifacts.

**Independent Test**: Confirmed execution rejects unfiltered runs, applies family/episode filters, executes only ready deterministic actions, and writes deterministic JSON/Markdown run reports.

### Tests for User Story 2

- [X] T022 [P] [US2] Add failing confirmed execution rejects missing episode/action-family filter test in `tests/test_corpus_remediation_runner.py`
- [X] T023 [P] [US2] Add failing action-family filter and positive `max_actions` ordering test in `tests/test_corpus_remediation_runner.py`
- [X] T024 [P] [US2] Add failing episode filter executes only matching ready deterministic actions test in `tests/test_corpus_remediation_runner.py`
- [X] T025 [P] [US2] Add failing confirmed run report JSON/Markdown writer test in `tests/test_corpus_remediation_runner.py`
- [X] T026 [P] [US2] Add failing direct-core-call and no-shell-out execution boundary test in `tests/test_corpus_remediation_runner.py`
- [X] T027 [P] [US2] Add failing `force` and `allow_partial` propagation test for confirmed deterministic core dispatch in `tests/test_corpus_remediation_runner.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement confirmed execution filter validation and `max_actions` validation in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T029 [US2] Implement execution dispatch for `extractive_summary`, `mentions`, `episode_intelligence`, `industry_mapping`, and `external_boundary` using existing core functions in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T030 [US2] Implement output path extraction and `executed` versus `reused` outcome mapping in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T031 [US2] Implement deterministic confirmed JSON and Markdown run report writers in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T032 [US2] Extend CLI parsing for `--confirm`, `--episode`, `--action-family`, `--max-actions`, `--force`, and `--allow-partial` in `scripts/run_corpus_remediation.py`
- [X] T033 [US2] Add CLI confirmed stdout and stderr contract tests in `tests/test_corpus_remediation_runner.py`
- [X] T034 [US2] Run User Story 2 targeted tests `python -m pytest tests/test_corpus_remediation_runner.py -k "confirm or filter or max_actions or report or shell or force or allow_partial" --basetemp=.pytest-tmp/run-010-us2`

**Checkpoint**: User can execute bounded deterministic remediation and receive auditable run reports.

---

## Phase 5: User Story 3 - Contain Failures and Preserve Safety Boundaries (Priority: P3)

**Goal**: Record failed actions, skip same-run downstream dependents, continue unrelated actions, and preserve all no-leak/no-investment/no-MCP boundaries.

**Independent Test**: A fixture run with one failing action records the failure, skips dependent rows, continues unrelated rows, and emits no raw transcript, evidence, semantic body, prompt, raw LLM output, secret, or investment advice.

### Tests for User Story 3

- [X] T035 [P] [US3] Add failing single-action failure containment test in `tests/test_corpus_remediation_runner.py`
- [X] T036 [P] [US3] Add failing same-run downstream failed-dependency skip test in `tests/test_corpus_remediation_runner.py`
- [X] T037 [P] [US3] Add failing no raw transcript/evidence/semantic body/prompt/raw LLM output/secret leakage test in `tests/test_corpus_remediation_runner.py`
- [X] T038 [P] [US3] Add failing boundary guard test for RSS, network, SQLite cache rebuild, `.env`, LLM provider, MCP, download, transcription, and semantic execution in `tests/test_corpus_remediation_runner.py`
- [X] T039 [P] [US3] Add failing no investment advice and external-status-as-market-fact output test in `tests/test_corpus_remediation_runner.py`

### Implementation for User Story 3

- [X] T040 [US3] Implement per-action exception capture and failure row serialization without traceback leakage in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T041 [US3] Implement same-run failed-dependency skip handling in `src/podcast_ingest_core/corpus_remediation_runner.py`
- [X] T042 [US3] Harden JSON, Markdown, stdout, and stderr serialization against raw transcript, evidence, semantic body, prompt, raw LLM output, secrets, market facts, and investment advice in `src/podcast_ingest_core/corpus_remediation_runner.py` and `scripts/run_corpus_remediation.py`
- [X] T043 [US3] Run User Story 3 targeted tests `python -m pytest tests/test_corpus_remediation_runner.py -k "failure or dependency or leak or boundary or investment" --basetemp=.pytest-tmp/run-010-us3`

**Checkpoint**: Failed deterministic remediation is isolated and safety boundaries remain explicit.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T044 [P] Update corpus remediation runner documentation in `README.md`
- [X] T045 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T046 [P] Update verification mapping for corpus remediation runner tests in `docs/verification-matrix.md`
- [X] T047 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-010-mcp`
- [X] T048 Run corpus regression tests `python -m pytest tests/test_corpus_remediation_runner.py tests/test_corpus_remediation_plan.py tests/test_corpus_index.py --basetemp=.pytest-tmp/run-010-corpus`
- [X] T049 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-010-docs`
- [X] T050 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-010-full`
- [X] T051 Run compile check `python -m compileall src scripts`
- [X] T052 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

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

- **US1**: Required MVP. Establishes refreshed plan loading, dry-run selection, exclusion logic, counts, no-write behavior, and CLI preview.
- **US2**: Extends US1 with confirmed filter validation, deterministic execution dispatch, and run report artifacts.
- **US3**: Extends US2 with failure containment and safety boundary hardening.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T011 through T015 can be written in parallel after Phase 2.
- T022 through T027 can be written in parallel after US1 test fixtures exist.
- T035 through T039 can be written in parallel after US2 execution fixtures exist.
- T044 through T046 can run in parallel after runtime behavior is stable.

---

## Parallel Example: User Story 1

```text
Task: "Add failing empty corpus dry-run no-write test in tests/test_corpus_remediation_runner.py"
Task: "Add failing refresh-before-selection test proving generate_corpus_remediation_plan() runs before selection in tests/test_corpus_remediation_runner.py"
Task: "Add failing dry-run selected deterministic families and excluded non-deterministic families test in tests/test_corpus_remediation_runner.py"
Task: "Add failing deterministic dry-run and no generated_at test in tests/test_corpus_remediation_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup tests.
2. Complete Phase 2 public contracts and module skeleton.
3. Complete Phase 3 User Story 1.
4. Run `tests/test_corpus_remediation_runner.py` for the MVP.
5. Stop and validate dry-run no-write behavior before adding confirmed execution.

### Incremental Delivery

1. Deliver US1 to preview safe deterministic corpus remediation.
2. Add US2 to execute bounded deterministic actions and write run reports.
3. Add US3 to contain failures and prove safety boundaries.
4. Run full verification before claiming implementation complete.

### Boundary Rules

- Do not write artifacts during dry-run.
- Do not execute unfiltered confirmed runs.
- Do not execute audio download, transcription, semantic summary, semantic review, stock-lens, synthesis, unknown, blocked, optional, or gated actions.
- Do not add MCP tools or change MCP envelopes.
- Do not read RSS, network, SQLite cache, `.env`, API keys, live market data, stock-lens query artifacts, or stock-lens synthesis artifacts.
- Do not include raw transcript, evidence snippets, semantic body text, prompt text, raw LLM output, or secret values in JSON, Markdown, stdout, stderr, or tests.
- Do not automatically rebuild cache.
- Do not provide investment advice.
