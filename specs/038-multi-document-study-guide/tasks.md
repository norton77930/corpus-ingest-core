# Tasks: Multi-Document Study Guide

**Feature**: 038-multi-document-study-guide
**TDD**: RED before GREEN.
**Status**: Implemented. Real confirm landed. CLI default `API_KEY`. x-raytar index reports `study_guide: available`. Not committed.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec + locked taxonomy | `spec.md` Clarifications; `05`/`06` out |
| C2 Principle IV unamended | runner never reads/sends transcript; captured messages |
| C3 One family, four files | `test_corpus_index` + bundle tests |
| C4 Dry-run zero write / zero LLM | tree manifest + provider-not-called |
| C5 Confirm ack-first | wrong ack raises before `create_provider` |
| C6 Finance / gooaye isolation | refuse + gooaye artifacts unchanged |
| C7 No 05/06 fabrication | fixture without tool names stays clean |
| C8 Registry exact 22 | `test_mcp_tool_registry_contract` unmodified |
| C9 Full verify | pytest / compileall / diff-check vs 24/1628 baseline |

Non-goals: `01`/`02`/`05`/`06`, MCP, 015 chain, review-passed gate, Hermes, YouTube, `gb10`.

## Analyze findings (pre-implementation)

1. `CorpusArtifactFamilyCounts` has no `partial` bucket; unknown statuses count as available. Plan maps `partial` → `unreadable`.
2. `ARTIFACT_LADDER` is independent of `SUPPORTED_ARTIFACT_FAMILIES`. Do not add `study_guide` to the ladder.
3. `test_generate_corpus_index_reports_missing_artifact_families` pins the missing list. Adding the family is a deliberate contract update.
4. `test_data_dir_fixture_contract.KNOWN_STORAGE_DIR_CONSTANTS` must gain `STUDY_GUIDES_DIR`.
5. `SemanticSummaryProvider.complete` already exists; do not add a protocol method.
6. `corpus_index` must not import `config`.
7. Semantic CLI is `scripts/summarize_episode.py --mode semantic`. New family gets its own script.

## Phase 1: Setup

- [ ] T001 Record 038 in `specs/README.md` and add a verification-matrix row in `docs/verification-matrix.md`
- [ ] T002 [P] Add `STUDY_GUIDES_DIR` to `tests/test_data_dir_fixture_contract.py` known set

## Phase 2: Foundational

- [ ] T003 RED `tests/test_study_guide_profiles.py`: heading lists for `03`/`04`/`07` match FR-010–012; prompt forbids 05/06 workflow advice and transcript invention
- [ ] T004 GREEN `src/podcast_ingest_core/study_guide_profiles.py` as pure data (stdlib + `.errors` only)
- [ ] T005 RED/GREEN `src/podcast_ingest_core/errors.py` + `models.py`: `StudyGuideBundleError`, `StudyGuideBundleResult`
- [ ] T006 RED/GREEN `src/podcast_ingest_core/storage.py`: `STUDY_GUIDES_DIR` and `study_guide_bundle_paths(podcast_id, episode_ref, title)`
- [ ] T007 Export error + runner placeholder from `src/podcast_ingest_core/__init__.py` only when the function exists (T010)

## Phase 3: US2 Dry-run (P1)

- [ ] T008 [US2] RED `tests/test_study_guide_bundle.py`: dry-run on a fixture learning-notes episode lists planned reads/writes, writes zero files, constructs no provider
- [ ] T009 [US2] RED reuse dry-run says reuse when all four files exist
- [ ] T010 [US2] GREEN `src/podcast_ingest_core/study_guide_bundle.py` dry-run path

## Phase 4: US3 Refuse (P1)

- [ ] T011 [US3] RED finance/gooaye profile refuses with named required profile, zero writes
- [ ] T012 [US3] RED missing semantic summary refuses, does not import/call 015
- [ ] T013 [US3] RED finance-shaped summary (市場觀點) refuses even if profile is learning-notes
- [ ] T014 [US3] GREEN the refuse branches in `study_guide_bundle.py`

## Phase 5: US1 Confirmed bundle (P1)

- [ ] T015 [US1] RED confirmed without exact ack raises before provider construction
- [ ] T016 [US1] RED fake `complete()` returns structured JSON; four files appear atomically; `00` has only seed/audio facts
- [ ] T017 [US1] RED `03`/`04`/`07` headings match FR-010–012; no 市場觀點
- [ ] T018 [US1] GREEN confirmed path: ack → `create_provider` → `complete` → validate → atomic write + run report + cache warning
- [ ] T019 [US1] Force/reuse: `force=false` reuses complete bundle without LLM; `force=true` rewrites

## Phase 6: US4 Evidence (P2)

- [ ] T020 [US4] RED source 不確定事項 about reconstructed prompts is preserved
- [ ] T021 [US4] RED fixture without Claude Code / Codex / Copilot / CLAUDE.md / Skill does not grow that advice
- [ ] T022 [US4] RED captured messages exclude transcript text and the Chunk Summaries body
- [ ] T023 [US4] RED `prohibited_advice` pass on generated files; advice-shaped body fails
- [ ] T024 [US4] GREEN validation helpers in `study_guide_bundle.py`

## Phase 7: Index + CLI + contracts

- [ ] T025 RED/GREEN `src/podcast_ingest_core/corpus_index.py`: append `study_guide`; `partial` counts as unreadable; update `tests/test_corpus_index.py` missing-list contract
- [ ] T026 Assert `ARTIFACT_LADDER` unchanged in `tests/test_corpus_remediation_plan.py` or the new test file
- [ ] T027 Thin CLI `scripts/run_study_guide_bundle.py` + no-leak stdout test
- [ ] T028 `tests/test_contracts.py`: pin `run_study_guide_bundle` signature; export the error
- [ ] T029 T007 exports

## Phase 8: Polish

- [ ] T030 Docs: `docs/verification-matrix.md` (if not done in T001); no MCP docs change
- [ ] T031 Mark FR/safety checklist boxes that tests cover
- [ ] T032 Full `python -m pytest` + `python -m compileall src scripts` + `git diff --check`

## Dependency order

T001–T006 → T008–T014 → T015–T019 → T020–T024 → T025–T029 → T030–T032

US2 is the first runnable increment. US1 is the MVP the operator can see.
