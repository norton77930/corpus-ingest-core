# Tasks: Corpus Remediation Plan

**Input**: Design documents from `specs/009-corpus-remediation-plan/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: TDD is required for new runtime behavior. Write failing tests before implementation tasks in each phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Test Fixtures and Contracts)

**Purpose**: Establish remediation-plan test fixtures and public contract tests before implementation.

- [X] T001 Create corpus remediation fixture helpers in `tests/test_corpus_remediation_plan.py`
- [X] T002 [P] Add failing storage helper path contract test for `data/corpus/{podcast_id}/corpus-remediation-plan.json` and `.md` in `tests/test_corpus_remediation_plan.py`
- [X] T003 [P] Add failing public result/model contract tests for remediation summary counts and output paths in `tests/test_corpus_remediation_plan.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared models, errors, storage contracts, module skeleton, and exports required by all user stories.

**CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T004 Add corpus remediation plan result, episode row, action, blocker, and count models in `src/corpus_ingest_core/models.py`
- [X] T005 Add corpus remediation plan error type in `src/corpus_ingest_core/errors.py`
- [X] T006 Add `CorpusRemediationPlanAssetPaths` and `corpus_remediation_plan_asset_paths(podcast_id)` in `src/corpus_ingest_core/storage.py`
- [X] T007 Create `src/corpus_ingest_core/corpus_remediation_plan.py` with public function signature, artifact family constants, and no-op-safe module skeleton
- [X] T008 Export corpus remediation public function, error, and model types from `src/corpus_ingest_core/__init__.py`
- [X] T009 Run foundational targeted tests in `tests/test_corpus_remediation_plan.py`

**Checkpoint**: Public contracts and module boundaries exist, but remediation behavior is not complete.

---

## Phase 3: User Story 1 - View Corpus Remediation Backlog (Priority: P1) MVP

**Goal**: Generate deterministic JSON and Markdown remediation plan artifacts from a refreshed local corpus index.

**Independent Test**: A local corpus with empty and multi-episode fixture states writes deterministic plan artifacts with summary counts, ordered actions, source index paths, and no timestamp.

### Tests for User Story 1

- [X] T010 [P] [US1] Add failing empty corpus remediation plan test in `tests/test_corpus_remediation_plan.py`
- [X] T011 [P] [US1] Add failing refresh-before-planning test proving `generate_corpus_index()` runs before remediation derivation in `tests/test_corpus_remediation_plan.py`
- [X] T012 [P] [US1] Add failing at-least-five-episode, three-artifact-family ordered action and summary count test in `tests/test_corpus_remediation_plan.py`
- [X] T013 [P] [US1] Add failing deterministic regeneration and no `generated_at` test in `tests/test_corpus_remediation_plan.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement refreshed corpus index loading and empty corpus handling in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T015 [US1] Implement full-ladder action ordering, per-episode rows, and summary counts in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T016 [US1] Implement deterministic JSON and Markdown writers in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T017 [US1] Implement thin CLI `scripts/generate_corpus_remediation_plan.py`
- [X] T018 [US1] Add CLI stdout contract test for output paths and summary counts in `tests/test_corpus_remediation_plan.py`
- [X] T019 [US1] Run User Story 1 targeted tests in `tests/test_corpus_remediation_plan.py`

**Checkpoint**: User can generate a basic remediation backlog for one podcast without executing any remediation action.

---

## Phase 4: User Story 2 - Understand Blockers and Unsafe Inputs (Priority: P2)

**Goal**: Represent missing upstream dependencies, unreadable metadata, and non-fatal warnings without failing the whole plan.

**Independent Test**: A fixture corpus with audio available, transcript missing, downstream gaps, and one malformed metadata artifact produces isolated warnings and blocked downstream actions.

### Tests for User Story 2

- [X] T020 [P] [US2] Add failing audio-present transcript-missing blocker test in `tests/test_corpus_remediation_plan.py`
- [X] T021 [P] [US2] Add failing unreadable JSON warning containment test in `tests/test_corpus_remediation_plan.py`
- [X] T022 [P] [US2] Add failing missing-upstream blocks downstream actions test in `tests/test_corpus_remediation_plan.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement transcript and upstream blocker generation in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T024 [US2] Implement warning propagation from corpus index rows into remediation row and summary warnings in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T025 [US2] Implement advisory command text for download, transcribe, and deterministic downstream actions without executing commands in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T026 [US2] Run User Story 2 targeted tests in `tests/test_corpus_remediation_plan.py`

**Checkpoint**: Broken or incomplete episodes remain visible, with blockers and warnings isolated to affected rows.

---

## Phase 5: User Story 3 - Review Optional Semantic Remediation (Priority: P3)

**Goal**: Show semantic summary and semantic review gaps as optional/gated actions without LLM execution or LLM body leakage.

**Independent Test**: A fixture corpus with semantic gaps and semantic review status produces gated semantic actions, review metadata, and no semantic body, prompt, raw output, or secret leakage.

### Tests for User Story 3

- [X] T027 [P] [US3] Add failing semantic summary optional/gated action test in `tests/test_corpus_remediation_plan.py`
- [X] T028 [P] [US3] Add failing semantic review dependency and status metadata test in `tests/test_corpus_remediation_plan.py`
- [X] T029 [P] [US3] Add failing no raw transcript/evidence/semantic body/prompt/raw LLM output test in `tests/test_corpus_remediation_plan.py`

### Implementation for User Story 3

- [X] T030 [US3] Implement semantic summary and semantic review gated action metadata in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T031 [US3] Include semantic review status, path, check counts, failed counts, and warning counts from the refreshed corpus index in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T032 [US3] Harden JSON and Markdown serialization against raw transcript, evidence, semantic body, prompt, raw LLM output, and secret leakage in `src/corpus_ingest_core/corpus_remediation_plan.py`
- [X] T033 [US3] Run User Story 3 targeted tests in `tests/test_corpus_remediation_plan.py`

**Checkpoint**: Semantic remediation is visible but clearly optional/gated and leak-safe.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, governance mapping, and verification gates.

- [X] T034 [P] Update corpus remediation documentation in `README.md`
- [X] T035 [P] Update architecture and Spec Kit registry mappings in `docs/architecture.md` and `specs/README.md`
- [X] T036 [P] Update verification mapping for corpus remediation tests in `docs/verification-matrix.md`
- [X] T037 Add local-only and no-execution boundary coverage for RSS, network, SQLite cache, `.env`, LLM provider, MCP, remediation command execution, and cache rebuild calls in `tests/test_corpus_remediation_plan.py`
- [X] T038 Run MCP registry guard `python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-009-mcp`
- [X] T039 Run targeted remediation tests `python -m pytest tests/test_corpus_remediation_plan.py --basetemp=.pytest-tmp/run-009-remediation`
- [X] T040 Run docs/spec guard tests `python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py --basetemp=.pytest-tmp/run-009-docs`
- [X] T041 Run full test suite `python -m pytest --basetemp=.pytest-tmp/run-009-full`
- [X] T042 Run compile check `python -m compileall src scripts`
- [X] T043 Run whitespace check `git -c safe.directory=<repo-path> diff --check`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and should be implemented after US1 to reuse action row assembly.
- **User Story 3 (Phase 5)**: Depends on Phase 2 and can proceed after US1 action row assembly exists.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1**: Required MVP. Establishes refreshed index loading, output writers, summary counts, and CLI.
- **US2**: Extends US1 rows with blockers, warning containment, and advisory command text.
- **US3**: Extends US1 rows with semantic optional/gated actions and leak safety.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T010 through T013 can be written in parallel after Phase 2.
- T020 through T022 can be written in parallel after US1 test fixtures exist.
- T027 through T029 can be written in parallel after US1 test fixtures exist.
- T034 through T036 can run in parallel after runtime behavior is stable.

---

## Parallel Example: User Story 1

```text
Task: "Add failing empty corpus remediation plan test in tests/test_corpus_remediation_plan.py"
Task: "Add failing refresh-before-planning test proving generate_corpus_index() runs before remediation derivation in tests/test_corpus_remediation_plan.py"
Task: "Add failing at-least-five-episode, three-artifact-family ordered action and summary count test in tests/test_corpus_remediation_plan.py"
Task: "Add failing deterministic regeneration and no generated_at test in tests/test_corpus_remediation_plan.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup tests.
2. Complete Phase 2 public contracts and module skeleton.
3. Complete Phase 3 User Story 1.
4. Run `tests/test_corpus_remediation_plan.py` for the MVP.
5. Stop and validate JSON/Markdown determinism before adding blocker and semantic behavior.

### Incremental Delivery

1. Deliver US1 to provide the basic remediation backlog.
2. Add US2 to make incomplete and corrupt corpora actionable without whole-plan failure.
3. Add US3 to make semantic remediation visible, gated, and leak-safe.
4. Run full verification before claiming implementation complete.

### Boundary Rules

- Do not execute remediation actions while generating the plan.
- Do not add MCP tools or change MCP envelopes.
- Do not read RSS, network, SQLite cache, `.env`, API keys, live market data, stock-lens query artifacts, or stock-lens synthesis artifacts.
- Do not include raw transcript, evidence snippets, semantic body text, prompt text, raw LLM output, or secret values in JSON, Markdown, stdout, stderr, or tests.
- Do not automatically rebuild cache.
- Do not provide investment advice.

## Phase 7: Convergence

- [X] T044 Add external boundary transitive transcript blocker coverage and implementation in `tests/test_corpus_remediation_plan.py` and `src/corpus_ingest_core/corpus_remediation_plan.py` per FR-010 / Edge Cases / data-model ladder (partial)
