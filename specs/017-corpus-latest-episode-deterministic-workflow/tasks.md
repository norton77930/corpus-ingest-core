# Tasks: Latest Episode Deterministic Workflow

**Input**: Design documents from
`/specs/017-corpus-latest-episode-deterministic-workflow/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. Each runtime behavior is introduced RED→GREEN with pytest.

## Phase 1: Spec Kit Setup

- [x] T001 Create 017 spec and requirements checklist in `specs/017-corpus-latest-episode-deterministic-workflow/spec.md` and `checklists/requirements.md`
- [x] T002 Create plan, research, data model, contract, quickstart, and safety checklist in `specs/017-corpus-latest-episode-deterministic-workflow/`
- [x] T003 Point the active Spec Kit handoff marker to `specs/017-corpus-latest-episode-deterministic-workflow/plan.md` in `AGENTS.md`

## Phase 2: Foundational Core Contract

**Purpose**: Add the immutable, safe public contract before user-story behavior.

- [x] T004 Add failing public-contract and zero-write dry-run tests in `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T005 Add workflow models, dedicated error, storage report paths, package exports, and safe result serialization in `src/corpus_ingest_core/models.py`, `errors.py`, `storage.py`, and `__init__.py`
- [x] T006 Add the minimal importable `run_corpus_latest_episode_deterministic_workflow` runner in `src/corpus_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py` and make T004 green

**Checkpoint**: The new public entry point has a dry-run-first immutable contract.

## Phase 3: User Story 1 - Process One Latest Episode (Priority: P1) 🎯 MVP

**Goal**: One confirmed request pins a latest episode and advances its complete
local deterministic ladder before semantic work.

**Independent Test**: A fixture episode with no artifacts executes intake,
download, transcription, and one-at-a-time deterministic remediation in order,
then returns `ready_for_semantic_summary` without LLM or secret access.

- [x] T007 [US1] Add failing pinned-selector, ordered-stage, remediation-loop, and semantic-boundary tests in `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T008 [US1] Implement canonical latest snapshot, stage probe/dispatch loop, one-action remediation loop, confirmed report writing, and semantic boundary result in `src/corpus_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T009 [US1] Add RED MCP wrapper and 14-tool registry contract cases in `tests/test_mcp_server.py` and `tests/test_mcp_tool_registry_contract.py`
- [x] T010 [US1] Add `run_corpus_latest_episode_deterministic_workflow` to `src/corpus_ingest_core/mcp_server.py` and update registry/docs-count guards in `tests/test_mcp_tool_registry_contract.py` and `tests/test_ai_governance_docs.py`
- [x] T011 [US1] Add the thin CLI and its red/green contract coverage in `scripts/run_corpus_latest_episode_deterministic_workflow.py` and `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T012 [US1] Add the `corpus-latest-episode-processing` portable Skill and its metadata/no-fallback coverage in `.agents/skills/corpus-latest-episode-processing/SKILL.md` and `tests/test_corpus_latest_episode_processing_skill.py`

**Checkpoint status**: P1 is met. The 2026-07-17 `seeded`/`downloaded`
child-outcome mapping defect remains recorded below as historical, and is
resolved: successful child outcomes now advance the pinned workflow correctly.

## Phase 4: User Story 2 - Safely Resume or Avoid Rework (Priority: P2)

**Goal**: A new confirmed request uses valid local artifacts and never reruns an
already-ready deterministic episode.

**Independent Test**: Partial and ready fixtures show only the first missing
step executes, or that no executor is called.

- [x] T013 [US2] Add failing partial-artifact resume and already-ready no-op tests in `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T014 [US2] Extend the core runner's state classification and aggregate result rows in `src/corpus_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py` to make T013 green

**Checkpoint**: Repeat requests preserve valid work and surface the semantic
handoff boundary without duplicate deterministic writes.

## Phase 5: User Story 3 - Stop Clearly on a Problem (Priority: P3)

**Goal**: Any stage or remediation failure/block stops the active workflow
without fallback or later work.

**Independent Test**: Inject every high-level stage and remediation action
failure and assert no later stage executor is called.

- [x] T015 [US3] Add failing failed/blocked selector, stage, remediation-action, safe-output, `.env`/provider, and cache-rebuild guard tests in `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`
- [x] T016 [US3] Implement fail-closed aggregation, repeated-action bound, sanitization, manual-cache warning, and no-LLM/no-secret enforcement in `src/corpus_ingest_core/corpus_latest_episode_deterministic_workflow_runner.py`

**Checkpoint**: All unsafe or failed paths produce bounded metadata and stop.

## Phase 6: Cross-Cutting Documentation and Setup

- [x] T017 Update MCP usage, README, agent handoff, framework, specs registry, and setup validation for the fourteenth reviewed tool and new Skill in `README.md`, `docs/mcp-usage.md`, `docs/agent-handoff.md`, `docs/ai-development-framework.md`, `specs/README.md`, and `scripts/validate_mcp_setup.py`
- [x] T018 Update repository secret-boundary allowlists and setup/Skill tests in `tests/test_repository_secret_boundary.py`, `tests/test_mcp_setup_validation.py`, and `tests/test_corpus_latest_episode_processing_skill.py`
- [x] T019 Run the quickstart and targeted core/MCP/CLI/Skill/docs safety suites listed in `specs/017-corpus-latest-episode-deterministic-workflow/quickstart.md`
- [x] T020 Run `python -m pytest`, `python -m compileall src scripts`, and `git diff --check`; record any Git ownership limitation without changing global Git configuration
- [x] T021 Verify `seeded` and `downloaded` child-outcome mapping advances one canonical episode without switching targets.
- [x] T022 Verify metadata coherence for confirmed JSON/Markdown reports and the terminal semantic handoff row.
- [x] T023 Verify canonical latest identity across an RSS update and multi-episode corpus state; no second episode enters one request.
- [x] T024 Verify the semantic boundary: terminal `ready_for_semantic_summary` is metadata-only and dispatches no semantic executor.
- [x] T025 Verify the confirmed EP679 end-to-end outcome and the single-call Skill/MCP authorization protocol.
- [x] T026 Add an action-identity mismatch regression and fail closed before
  priority-winning execution metadata can be combined with a different selected
  remediation action.
- [x] T027 Add malformed action identity regressions for both selected and
  priority-winning source identifiers; preserve a valid selected identifier only
  when the source identifier is genuinely absent or `null`.
- [x] T028 Add missing target remediation evidence regressions for empty results
  and results containing only non-target `skipped` rows, while preserving
  non-target skip isolation and target deterministic classification.
- [x] T029 Add sanitizer regressions for credential assignments and
  non-HTTP URI query/fragment data in reasons and warnings, using the standard
  safety-boundary
  replacement without weakening safe text or local path handling.
- [x] T030 Correct the data model's top-level outcome list: successful
  `executed`/`reused` rows continue to `ready_for_semantic_summary`; they are not
  terminal public outcomes.
- [x] T031 Add the 016 compatibility regression for completed semantic review
  artifacts: accept well-formed canonical target evidence without requiring a
  semantic residual or deterministic terminal action, while preserving empty,
  non-target-only, malformed, and invalid-semantic-status fail-closed cases.
- [x] T032 Harden malformed probe action identity handling, RFC-style `scheme:`
  query/fragment sanitization, and repository-level `.venv/` ignore policy.

  **Historical initial blocker (2026-07-17, resolved):** the focused
  SPEC 017/MCP/Skill/docs/security group passed with 105 passed; the full suite
  passed with 776 passed and no skipped tests; `python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電` returned `ok=true` with 14 tools and no warnings; `python -m compileall src scripts` and `git diff --check` passed. Pytest emitted a non-failing cache warning because `.pytest_cache` was not writable. The initial user-confirmed CUDA `float16` EP679 run created the episode seed and metadata-only latest-workflow reports, then returned `blocked` before audio download because the successful intake outcome `seeded` was not accepted as workflow progress; `downloaded` had the same mapping gap. No transcription, deterministic remediation, LLM/provider/`.env` access, retry, automatic cache rebuild, commit, or push occurred.

  **historical blocker resolved:** child-outcome mapping, confirmed report metadata
  coherence, canonical single-target selection, semantic boundary, and
  multi-episode regression coverage are complete. Prior authorized verification
  recorded a full suite result of 801 passed. The final metadata-only confirmed
  EP679 report is `episode_ref=EP679`,
  `outcome=ready_for_semantic_summary`, `ready_count=1`, `blocked_count=0`, and
  `failed_count=0`. The report records no semantic/LLM/provider work, retry,
  cache rebuild, commit, or push. SPEC 017 is Implemented; the portable Skill
  now treats the explicit natural-language request as a one-time execution
  authorization for exactly one dedicated MCP `confirm=true` call, then reports
  once and stops.

## Dependencies & Execution Order

- Phase 1 is complete.
- Phase 2 blocks all runtime stories.
- US1 depends on Phase 2; US2 and US3 extend the same runner and follow US1.
- Cross-cutting docs/setup follows the public MCP and Skill surfaces from US1.
- TDD order is mandatory: T004/T007/T009/T013/T015 must fail before their
  associated production changes.

## Implementation Strategy

1. Establish the contract and a strict zero-write dry-run.
2. Deliver the complete deterministic success path and dedicated Agent surface.
3. Add resumability/no-op behavior, then failure-stop and safety guards.
4. Update the reviewed registry and all required documentation in the same
   release, then run quickstart, targeted suites, full regression, compileall,
   and diff validation.
