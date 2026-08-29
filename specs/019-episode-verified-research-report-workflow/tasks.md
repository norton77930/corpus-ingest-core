# Tasks: Episode Verified Research Report Workflow

**Feature**: 019-episode-verified-research-report-workflow  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**TDD**: Project constitution requires RED before GREEN for new runtime behavior.

## Phase 1: Setup

- [x] T001 Create package docs already present under `specs/019-episode-verified-research-report-workflow/` (verify completeness vs plan structure)
- [x] T002 [P] Wire `SPECIFY_FEATURE_DIRECTORY` / local `.specify/feature.json` to `specs/019-episode-verified-research-report-workflow` for agent context

## Phase 2: Foundational (blocking)

- [x] T003 [P] Add focused RED tests in `tests/test_episode_verified_research_report_workflow_runner.py` for: public signature `run_episode_verified_research_report_workflow`, `confirm=False` default, required `episode_ref`
- [x] T004 [P] Add RED tests for strict zero-write preview and reserved selector rejection (`latest`/`next` casefold) in `tests/test_episode_verified_research_report_workflow_runner.py`
- [x] T005 [P] Add RED tests for blocked inventory (missing/stale roles) and no provider/RSS/015–017 dispatch on confirm in `tests/test_episode_verified_research_report_workflow_runner.py`
- [x] T006 [P] Add RED tests for ready-path assemble publish + reuse + fail-closed conflict in `tests/test_episode_verified_research_report_workflow_runner.py`
- [x] T007 Add models/errors/exports stubs as needed in `src/corpus_ingest_core/models.py`, `errors.py`, `__init__.py` so RED imports resolve without full behavior

## Phase 3: User Story 1 — Preview (P1) [US1]

**Goal**: Explicit-episode readiness preview, zero writes.  
**Independent test**: Preview ready and missing fixtures; assert inventories and zero files.

- [x] T008 [US1] Implement readiness inspection helper in `src/corpus_ingest_core/episode_verified_research_report_workflow_runner.py` reusing lineage/transcript/review validators
- [x] T009 [US1] Implement `confirm=False` path returning metadata-only readiness plan in `episode_verified_research_report_workflow_runner.py`
- [x] T010 [US1] Implement early reserved-selector and empty-ref rejection shared by preview/confirm in `episode_verified_research_report_workflow_runner.py`
- [x] T011 [US1] GREEN: pass T003–T004 preview/selector tests

## Phase 4: User Story 2 — Confirm assemble/publish (P1) [US2]

**Goal**: Confirm only assembles/publishes when ready; else blocked inventory.  
**Independent test**: Ready fixtures → completed bundle; missing review → blocked, no publish; provider factory not called.

- [x] T012 [US2] Implement confirm path: readiness gate → `assemble_verified_research_report` → `publish_verified_research_report_bundle` in `episode_verified_research_report_workflow_runner.py`
- [x] T013 [US2] Implement blocked terminal result with `missing_roles` / `stale_roles` / `failed_gates` metadata in runner + models
- [x] T014 [US2] Ensure confirm does not call LLM provider factory, RSS, download, 015/016/017, or `run_research_workflow` (guard via tests/monkeypatch)
- [x] T015 [US2] Optional metadata-only checkpoint finalization consistent with artifact-subordinate rules in runner (if plan checkpoint path used)
- [x] T016 [US2] GREEN: pass T005–T006 blocked/publish tests

## Phase 5: User Story 3 — Reuse / conflict (P2) [US3]

**Goal**: Second confirm reuses identical bundle; conflicts fail closed.  
**Independent test**: Double confirm identical sources; mutate source between runs.

- [x] T017 [US3] Align confirm success path with existing publish reuse/conflict semantics (no parallel publisher) in runner
- [x] T018 [US3] GREEN: reuse and fail-closed cases in `tests/test_episode_verified_research_report_workflow_runner.py`

## Phase 6: Interfaces & governance

- [x] T019 [P] Thin CLI `scripts/run_episode_verified_research_report_workflow.py`
- [x] T020 [P] Append MCP tool 16 `run_episode_verified_research_report_workflow` in `src/corpus_ingest_core/mcp_server.py` with early selector rejection
- [x] T021 [P] Portable Skill `.agents/skills/episode-verified-research-report/SKILL.md`
- [x] T022 Update `scripts/validate_mcp_setup.py` and `tests/test_mcp_setup_validation.py` for exact 16 tools + Skill metadata
- [x] T023 Update `tests/test_mcp_tool_registry_contract.py` and `tests/test_mcp_server.py` for tool 16 order/contract
- [x] T024 [P] Skill contract tests `tests/test_episode_verified_research_report_skill.py`
- [x] T025 Update docs: `specs/README.md`, `docs/agent-handoff.md`, `docs/mcp-usage.md`, `docs/roadmap.md`, `docs/verification-matrix.md`, `AGENTS.md` SPECKIT pointer, README as needed for 16 tools / 019

## Phase 7: Polish & verification

- [x] T026 Run 015–018 regression targeted tests (semantic remediation, completion, latest deterministic, verified report 018, registry)
- [x] T027 Full `python -m pytest`, `python -m compileall src scripts`, `git diff --check`
- [x] T028 Mark completion conditions only after green evidence

## Dependencies

```text
Phase1 → Phase2 (RED) → Phase3 US1 → Phase4 US2 → Phase5 US3
                ↘ Phase6 interfaces (after T012 minimum for MCP wiring)
Phase7 after US2+interfaces
```

## Parallel examples

- T003–T006 can be authored together as RED suite
- T019–T021 parallel after Core GREEN
- T024 parallel with T022–T023

## MVP scope

US1 + US2 (preview + confirm publish/blocked) + MCP/CLI/Skill enough to demo historical episode report without ack.

## Completion Conditions

- [x] Preview zero-write; reserved selectors rejected
- [x] Confirm assemble/publish or blocked inventory; no LLM/RSS/child runners; no api_cost_ack
- [x] Reuse/conflict semantics hold
- [x] Registry exactly 16 tools; 1–15 preserved
- [x] Full pytest/compileall/diff-check green (1007 passed, 2026-07-22)

## Phase 8: Post-converge optional regressions

- [x] T029 [US3] Source mutation after publish blocks stale reuse (no silent `reused`) in `tests/test_episode_verified_research_report_workflow_runner.py`
- [x] T030 Blank `episode_ref` rejection + `result_to_dict` metadata-only serialization in `tests/test_episode_verified_research_report_workflow_runner.py`
- [x] T031 Note: optional checkpoint persistence remains out of v1 (FR-011 is if-written); no Convergence CRITICAL gap
