# Tasks: Corpus Episode Completion Workflow Runner

**Input**: Design documents from
`specs/016-corpus-episode-completion-workflow-runner/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`,
`data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required. Every behavior phase follows RED -> GREEN and preserves the
repository safety guards.

**Organization**: Tasks are grouped by user story. Existing dirty 014/015 work,
`.env`, and `data/` are protected baseline and must not be overwritten,
read, cleaned, staged, or committed by these tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because files and incomplete dependencies do not overlap.
- **[Story]**: Maps to a user story from `spec.md`.
- No task authorizes commit, push, PR, external provider use, real corpus
  mutation, cache rebuild, or client-specific Hermes Agent/OpenClaw setup.

## Phase 1: Setup and Contract Baseline

**Purpose**: Lock scope and additive contracts before behavior work.

- [x] T001 Record the protected dirty-worktree baseline and verify `.specify/feature.json` remains ignored for 016 without reading `.env` or `data/`
- [x] T002 [P] Add RED public API/model/error/export signature assertions for 016 to `tests/test_contracts.py` (FR-017)
- [x] T003 [P] Add RED storage path and no-directory-allocation assertions to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-015)
- [x] T004 Add additive 016 immutable dataclasses with exact field order to `src/podcast_ingest_core/models.py`
- [x] T005 Add `CorpusEpisodeCompletionWorkflowRunAssetPaths` and `corpus_episode_completion_workflow_run_asset_paths()` to `src/podcast_ingest_core/storage.py`
- [x] T006 Add `CorpusEpisodeCompletionWorkflowRunnerFailedError` and additive public exports to `src/podcast_ingest_core/errors.py` and `src/podcast_ingest_core/__init__.py`
- [x] T007 Run focused `tests/test_contracts.py` and `tests/test_corpus_episode_completion_workflow_runner.py` contract/storage tests and make the Phase 1 RED tests GREEN

**Checkpoint**: Additive 016 types and paths exist without changing runtime behavior.

---

## Phase 2: Foundational Snapshot Preview Seams

**Purpose**: Reuse one fresh 008/009 snapshot across 014 and 015 without changing
their public behavior.

- [x] T008 [P] Add RED 014 compatibility and strict semantic-handoff tests to `tests/test_corpus_episode_workflow_runner.py` for invalid transcript, semantic-only blockers, non-semantic blockers, and `max_actions=1` (FR-003, FR-010)
- [x] T009 [P] Add RED 015 shared-snapshot seam and public compatibility tests to `tests/test_corpus_semantic_remediation_runner.py` (FR-004, FR-017)
- [x] T010 Extract `_preview_corpus_episode_workflow_from_snapshot()` in `src/podcast_ingest_core/corpus_episode_workflow_runner.py` with public 014 default behavior unchanged
- [x] T011 Implement private 016 semantic-handoff mode in `src/podcast_ingest_core/corpus_episode_workflow_runner.py` that requires exact valid transcript, selects one deterministic row, and ignores only semantic-family blockers
- [x] T012 Extract `_preview_corpus_semantic_remediation_from_snapshot()` in `src/podcast_ingest_core/corpus_semantic_remediation_runner.py` while preserving 015 builder/catch/public behavior
- [x] T013 Run `tests/test_corpus_episode_workflow_runner.py` and `tests/test_corpus_semantic_remediation_runner.py` and make all seam/compatibility tests GREEN

**Checkpoint**: 014 and 015 standalone contracts are unchanged; 016 has pure
post-snapshot preview seams.

---

## Phase 3: User Story 1 - Preview the Safe Next Action (Priority: P1)

**Goal**: Select one safe next action or terminal state from fresh state with
strict zero-file behavior.

**Independent Test**: Every ladder state returns the specified action from real
008/009 builders while the complete tree manifest is unchanged and no side
effect surface is called.

### Tests for User Story 1

- [x] T014 [US1] Add RED full ladder state-table tests with real 008/009 builders to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-001 to FR-004, SC-001)
- [x] T015 [US1] Add RED unseeded/latest-to-canonical intake preview tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-001 to FR-003)
- [x] T016 [US1] Add RED strict zero-file tree-manifest, stale-sentinel, writer/provider/env/executor/progress-call, and no-`.part` tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-005 to FR-006, SC-002)
- [x] T017 [US1] Add RED one-index/one-plan/shared-object reuse assertions across deterministic and semantic seams to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-004)
- [x] T018 [US1] Add RED partial/empty/incomplete transcript and semantic-handoff precedence tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-003, FR-014)
- [x] T019 [US1] Add RED selector/snapshot/probe failure stop-order and adversarial category-only no-leak tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-014, FR-023)
- [x] T020 [US1] Add RED request normalization, unsafe identifier, non-positive numeric, terminal completed, and blocked/manual-only tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-011, FR-014)

### Implementation for User Story 1

- [x] T021 [US1] Create `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py` with constants, bounded validators, safe labels, and fixed reason/category allowlists
- [x] T022 [US1] Implement 013 dry-run selector resolution and safe canonical episode handling in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T023 [US1] Implement unseeded intake selection and one 008/009 snapshot build for seeded episodes in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T024 [US1] Implement deterministic-to-semantic selection using the shared 014/015 seams in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T025 [US1] Implement one bounded row, risk flags, counts, warnings, filters, and terminal/manual-only mapping in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T026 [US1] Implement recursive safe serialization and `result_to_dict()` in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py` (FR-023 to FR-024)
- [x] T027 [US1] Export `run_corpus_episode_completion_workflow()` and its result serializer from `src/podcast_ingest_core/__init__.py`
- [x] T028 [US1] Run `tests/test_corpus_episode_completion_workflow_runner.py` and make all User Story 1 tests GREEN

**Checkpoint**: User Story 1 is independently usable as a strict zero-file preview.

---

## Phase 4: User Story 2 - Execute One Approved Action (Priority: P2)

**Goal**: Recompute fresh state, execute at most one exact approved action, write
one bounded latest report pair, and stop.

**Independent Test**: Preview a canonical episode, confirm the exact returned
action, and observe one matching public runner call, one bounded outcome, no
other stage calls, and no fallback after drift/failure.

### Tests for User Story 2

- [x] T029 [US2] Add RED confirmed-`next` and confirmed-`latest` rejection-before-any-read/write tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-007 to FR-008, SC-004)
- [x] T030 [US2] Add RED exact semantic acknowledgement ordering tests covering RSS, snapshot, profile, env, credential, provider, progress, executor, and writer seams to `tests/test_llm_ack_guard_contracts.py` and `tests/test_corpus_episode_completion_workflow_runner.py` (FR-012, SC-005)
- [x] T031 [US2] Add RED confirmed dispatch matrix tests proving exactly one matching 013/012/011/010/015 runner call, `max_actions=1`, and zero other runner calls to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-010, SC-003)
- [x] T032 [US2] Add RED action-drift, target-disappearance, completed/blocked, and no-fallback tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-009 to FR-011)
- [x] T033 [US2] Add RED stage executed/reused/completed/blocked/rejected/failed/exception outcome mapping and stop-after-one tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-010, FR-014)
- [x] T034 [US2] Add RED confirmed report JSON/Markdown schema, no-`generated_at`, atomic `.part` replacement, cleanup, writer-failure, and no-compensation tests to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-015 to FR-016)
- [x] T035 [US2] Add RED adversarial report/stdout/stderr no-leak and no-investment-advice tests to `tests/test_llm_cli_no_leak.py` and `tests/test_corpus_episode_completion_workflow_runner.py` (FR-023 to FR-024, SC-007)
- [x] T036 [US2] Add RED semantic-review ignores-all-LLM-options assertions to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-013)

### Core Implementation for User Story 2

- [x] T037 [US2] Implement confirmed `next`/`latest` and exact semantic acknowledgement early guards in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T038 [US2] Implement fresh action-equality rejection and zero-dispatch terminal handling in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T039 [US2] Implement exact one-runner dispatch for 013/012/011/010/015 with deterministic `max_actions=1` and review LLM-option isolation in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T040 [US2] Implement bounded stage-result/exception mapping and confirmed stale-metadata/cache warnings in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T041 [US2] Implement confirmed-only JSON/Markdown rendering and atomic report writing in `src/podcast_ingest_core/corpus_episode_completion_workflow_runner.py`
- [x] T042 [US2] Run `tests/test_corpus_episode_completion_workflow_runner.py`, `tests/test_llm_ack_guard_contracts.py`, and `tests/test_llm_cli_no_leak.py` and make the confirmed Core suite GREEN

### Thin CLI for User Story 2

- [x] T043 [P] [US2] Add RED parser/default/argument-forwarding/exit-code tests for `scripts/run_corpus_episode_completion_workflow.py` to `tests/test_corpus_episode_completion_workflow_runner.py` (FR-017)
- [x] T044 [P] [US2] Add RED CLI acknowledgement-before-profile/env and category-only stderr tests to `tests/test_llm_cli_no_leak.py` (FR-012, FR-023)
- [x] T045 [US2] Create thin `scripts/run_corpus_episode_completion_workflow.py` with early confirmed guards, confirmed-summary-only config loading, Core call, bounded JSON stdout, and category-only errors
- [x] T046 [US2] Run `tests/test_corpus_episode_completion_workflow_runner.py`, `tests/test_llm_ack_guard_contracts.py`, and `tests/test_llm_cli_no_leak.py` for the 016 CLI and make them GREEN

**Checkpoint**: User Story 2 safely advances one episode by one approved action
through Core or CLI and then stops.

---

## Phase 5: User Story 3 - Use the Workflow from an Agent (Priority: P3)

**Goal**: Expose one reviewed stdio MCP tool and one portable human-control Skill.

**Independent Test**: Registry/Skill/setup validation passes, and a fresh
ephemeral Codex session discovers the Skill/tool and attempts only a safe
early-rejected dry-run path without corpus/provider writes.

### MCP Tests and Implementation

- [x] T047 [P] [US3] Add RED exact 13-tool registry, preserved-first-12, side-effect default, and bounded 016 schema assertions to `tests/test_mcp_tool_registry_contract.py` (FR-018)
- [x] T048 [P] [US3] Add RED 016 MCP dry-run/confirmed/blocked/rejected/error envelope, forwarding, early-ack, and no-leak tests to `tests/test_mcp_server.py` (FR-019, SC-006 to SC-007)
- [x] T049 [US3] Add a dedicated category-only completion workflow MCP call wrapper and `run_corpus_episode_completion_workflow` tool to `src/podcast_ingest_core/mcp_server.py`
- [x] T050 [US3] Preserve every existing MCP tool signature/envelope while updating only the reviewed registry to exact 13 in `src/podcast_ingest_core/mcp_server.py`
- [x] T051 [US3] Run `tests/test_mcp_server.py` and `tests/test_mcp_tool_registry_contract.py` and make the MCP suite GREEN

### Setup Validator Tests and Implementation

- [x] T052 [P] [US3] Add RED completion registry, Skill metadata, and confirmed-`next` early-guard checks to `tests/test_mcp_setup_validation.py` (FR-018 to FR-021)
- [x] T053 [US3] Extend `scripts/validate_mcp_setup.py` with registry-only discovery, portable Skill metadata validation, and safe early guard without real RSS/corpus/provider/cache work
- [x] T054 [US3] Run `tests/test_mcp_setup_validation.py` and make setup validation GREEN

### Portable Skill Tests and Implementation

- [x] T055 [P] [US3] Add RED portable frontmatter, ordered protocol, canonical-not-latest confirmation, ambiguous/negative no-approval, user-supplied acknowledgement, no-fallback, and stop-after-one tests to `tests/test_corpus_episode_completion_skill.py` (FR-020 to FR-021, SC-008)
- [x] T056 [US3] Use the repository Skill-authoring workflow to create `.agents/skills/corpus-episode-completion/SKILL.md` with minimal client-neutral frontmatter and the approved MCP-only human-control protocol
- [x] T057 [US3] Validate the Skill contains no Codex-only metadata, CLI/terminal fallback, retry, loop, cron, scheduler, or automatic second-action path in `tests/test_corpus_episode_completion_skill.py`
- [x] T058 [US3] Run `tests/test_corpus_episode_completion_skill.py`, `tests/test_mcp_tool_registry_contract.py`, and `tests/test_mcp_setup_validation.py` and make the automated agent surface GREEN

### Codex Smoke

- [x] T059 [US3] Document and execute one fresh ephemeral read-only Codex smoke using only the repository Skill and stdio MCP with an early-rejected unsafe podcast id, then record only sanitized pass/fail metadata in `specs/016-corpus-episode-completion-workflow-runner/quickstart.md` (FR-025, SC-008)

**Checkpoint**: Codex can select the portable Skill and thirteenth MCP tool
without a confirmed action, fallback command, real provider, or corpus write.

---

## Phase 6: Polish, Governance, and Full Verification

**Purpose**: Lock compatibility/safety boundaries, synchronize repository
documentation, converge, and run final gates.

### Safety and Compatibility Guards

- [x] T060 [P] Add 016 public contract/model-field-order and explicit no-force/partial/batch/latest-N/retry/scheduler/loop Core signature, CLI parser, and MCP schema assertions to `tests/test_contracts.py`, `tests/test_corpus_episode_completion_workflow_runner.py`, and `tests/test_mcp_tool_registry_contract.py` (FR-017, FR-022)
- [x] T061 [P] Strengthen 013-015 compatibility tests in `tests/test_corpus_episode_intake.py`, `tests/test_corpus_episode_workflow_runner.py`, and `tests/test_corpus_semantic_remediation_runner.py`
- [x] T062 [P] Add no automatic post-stage cache/index/plan rebuild guards to `tests/test_cache_rebuild_guard.py`
- [x] T063 [P] Extend provider-factory and acknowledgement-order guards in `tests/test_llm_provider_factory_boundary.py` and `tests/test_llm_ack_guard_contracts.py`
- [x] T064 [P] Extend repository secret/no-leak coverage for new Core/CLI/MCP/Skill files in `tests/test_repository_secret_boundary.py` and `tests/test_llm_cli_no_leak.py`

### Documentation and Governance

- [x] T065 [P] Add RED 016 lifecycle, exact-13, artifact inventory, active-plan, and next-unused-017 assertions to `tests/test_architecture_spec_docs.py` and `tests/test_ai_governance_docs.py`
- [x] T066 Update `README.md` with 016 Core/CLI, one-action human-control flow, report paths, MCP tool, and portable Skill
- [x] T067 Update `docs/architecture.md`, `docs/agent-handoff.md`, and `docs/roadmap.md` with 016 state machine, hard-Core/Skill boundary, exact 13 tools, and next unused 017
- [x] T068 Update `docs/verification-matrix.md`, `docs/mcp-usage.md`, and `docs/codex-mcp-setup.md` with 016 targeted gates, MCP schema, Skill use, and safe smoke
- [x] T069 Update `specs/README.md` with the 016 package, mappings, lifecycle, MCP exposure, and scope boundary
- [x] T070 Update `docs/mcp-readiness.md`, `docs/mcp-tool-use-eval.md`, and `docs/mcp-eval-prompts.md` only where needed to document the reviewed local stdio Skill/MCP evaluation
- [x] T071 Run `tests/test_architecture_spec_docs.py`, `tests/test_ai_governance_docs.py`, and `tests/test_mcp_tool_registry_contract.py` and make the documentation suite GREEN

### Targeted and Full Gates

- [x] T072 Run targeted `tests/test_corpus_episode_intake.py`, `tests/test_corpus_audio_download_runner.py`, `tests/test_corpus_local_transcription_runner.py`, `tests/test_corpus_remediation_runner.py`, `tests/test_corpus_episode_workflow_runner.py`, `tests/test_corpus_semantic_remediation_runner.py`, and `tests/test_corpus_episode_completion_workflow_runner.py` and record the passing result
- [x] T073 Run targeted `tests/test_mcp_server.py`, `tests/test_mcp_tool_registry_contract.py`, `tests/test_mcp_setup_validation.py`, `tests/test_corpus_episode_completion_skill.py`, `tests/test_llm_ack_guard_contracts.py`, `tests/test_llm_cli_no_leak.py`, `tests/test_llm_provider_factory_boundary.py`, `tests/test_cache_rebuild_guard.py`, `tests/test_repository_secret_boundary.py`, and governance suites and record the passing result
- [x] T074 Run `python -m pytest` and record the full pass/skip counts
- [x] T075 Run `python -m compileall src scripts` and record success
- [x] T076 Run `git diff --check` and inspect `git status --short` without staging or committing
- [x] T077 Run `speckit-converge`; if findings exist, append-only convergence tasks and return to implementation until clean
- [x] T078 Revalidate `specs/016-corpus-episode-completion-workflow-runner/checklists/requirements.md` and `safety.md`, confirm implementation tasks were marked progressively in `tasks.md`, and keep lifecycle finalization gated on T072-T077
- [x] T079 Change 016 `spec.md` status from `Draft` to `Implemented` only after T072-T078 pass

## Phase 7: Convergence

- [x] T080 Correct the `semantic_summary` selection risk metadata and add a regression assertion so external-provider work is marked `network_risk=true` per FR-005 and data-model risk rules

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1**: Starts after the approved Spec Kit artifacts and protected
  worktree baseline.
- **Phase 2**: Depends on Phase 1 additive contracts and blocks all user stories.
- **Phase 3 / US1**: Depends on Phase 2 seams; provides the MVP preview.
- **Phase 4 / US2**: Depends on US1 selection and serialization.
- **Phase 5 / US3**: Depends on US1/US2 Core contracts; MCP and Skill tests may
  be prepared in parallel after Core result types stabilize.
- **Phase 6**: Depends on all three stories.

### User Story Dependencies

- **US1 (P1)**: Independently delivers safe zero-file preview.
- **US2 (P2)**: Uses US1 fresh selection to authorize one action.
- **US3 (P3)**: Wraps US1/US2 through MCP and the portable Skill without moving
  safety enforcement out of Core.

### Parallel Opportunities

- Phase 1 contract and storage RED tests can run in parallel.
- Phase 2 014 and 015 seam tests touch separate files.
- Within each story, test tasks marked [P] can run in parallel before sequential
  implementation.
- Phase 5 MCP, setup-validator, and Skill RED tests touch separate files.
- Phase 6 safety guards can run in parallel before docs and final gates.

## Implementation Strategy

### MVP First

1. Complete additive contracts and snapshot seams.
2. Implement the strict zero-file state machine.
3. Validate US1 independently before any confirmed/MCP/Skill work.

### Incremental Delivery

1. US1: preview only.
2. US2: one exact confirmed Core/CLI action.
3. US3: thirteenth MCP tool plus portable Skill.
4. Governance, Codex smoke, converge, and full gates.

## Notes

- Completed tasks must be changed from `[ ]` to `[x]` without renumbering.
- Tests are written and observed RED before their corresponding implementation.
- Convergence may only append new task IDs after T079; it must not rewrite
  existing task history.
- No task authorizes a commit, push, PR, real LLM/provider call, real corpus
  write, automatic cache rebuild, or Hermes Agent/OpenClaw client setup.
