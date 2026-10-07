# Tasks: Safe Study-guide MCP Access

**Input**: `specs/044-study-guide-mcp/` design artifacts
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/study-guide-mcp.md, quickstart.md; completed pre-implementation analysis.
**Status**: T001–T028 are implemented in this session. Checkboxes record that implementation evidence.

One active writer. No branches/worktrees/commits/deployment. All runtime fixtures are synthetic and isolated. Before each behavior change, record an assertion-level focused RED, implement the smallest coherent fix, then GREEN and relevant regression. Never weaken baseline guards or run real LLM/download/transcription. IDs below are ordered; every GREEN depends on its preceding RED.

## Phase 1: Setup

- [x] T001 Reconcile HEAD and supplied planning-only changes with `specs/044-study-guide-mcp/workflow-record.md`; select 044 explicitly, preserve unrelated changes, and create `specs/044-study-guide-mcp/implementation-log.md` for actual commands/results. No demand to commit/clean the planning files before starting. [SC-005]
- [x] T002 Run the existing targeted Core/MCP/spec baselines from `specs/044-study-guide-mcp/quickstart.md` (omit the not-yet-created new test file); record environment and result in `specs/044-study-guide-mcp/implementation-log.md`. [FR-010, SC-005; depends T001]

## Phase 2: Foundational Contract

The existing fixtures, storage paths, provider factory, report pair writer and single FastMCP are the foundation. No setup implementation or new dependencies are required. Use the state table and fixed error contract; do not build another framework. The first safe deployable slice is US3 below.

## Phase 3: US3 — Preserve Shared-directory Data (P1)

**Goal**: protect bytes and classify failures at the public Core seam before exposing the tool.
**Independent test**: `tests/test_study_guide_bundle.py`, fake provider, isolated directories, exact before/after bytes and failing operation injection.

- [x] T003 [US3] RED: add `test_cover_only_preserves_lecture_derivation_and_extra_bytes` and allowed-force-without-derivation preservation cases in `tests/test_study_guide_bundle.py`; include CRLF, UTF-8 BOM, binary extra files and missing/invalid-UTF8 cover. Demonstrate current public runner loses or rewrites bytes. [FR-007, SC-004; depends T002]
- [x] T004 [US3] GREEN: in `src/corpus_ingest_core/study_guide_bundle.py`, preserve existing safe regular files with byte copies, overlay only 00 for cover-only and only four lecture roles for generation; keep output-role/result schemas unchanged. Rerun T003. [FR-007/008, SC-004; depends T003]
- [x] T005 [US3] RED: in `tests/test_study_guide_bundle.py`, add explicit/invalid/reserved/underscore identity, canonical identity mismatch/ambiguity, unsafe source/bundle/ancestor, child directory/special file, link/dangling-link and Windows reparse cases; include fake source-body sentinels and no-provider/no-writer checks for preview, reuse and confirm. [FR-013, SC-002/003; depends T004]
- [x] T006 [US3] GREEN: add local entry/source/no-follow preflight in `src/corpus_ingest_core/study_guide_bundle.py` using existing storage/canonical/snapshot helpers; source JSON retains identity validation, source summary retains caps, optional cover dependencies are safe. Add finite `StudyGuideBundleStateError` in `src/corpus_ingest_core/errors.py`; do not alter shared helpers/models. Rerun T005. [FR-013/014; depends T005]
- [x] T007 [US3] RED: in `tests/test_study_guide_bundle.py`, cover 05-only/06-only/both × preview/confirm × force and non-force generating branches; test all four recovery suffixes, old-only-with-derivation and safe reuse/cover exceptions; snapshots must show zero mutation on refusal. [FR-005/006/013, SC-003/004; depends T006]
- [x] T008 [US3] GREEN: add Core derivation-generation conflict and all-mode recovery-remnant refusal before provider/publication in `src/corpus_ingest_core/study_guide_bundle.py`; no cleanup, automatic recovery or force bypass. Rerun T007. [FR-006/013; depends T007]
- [x] T009 [US3] RED: inject staging copy/write, destination rename, publication rename, rollback, cleanup and report-pair failures in `tests/test_study_guide_bundle.py`; assert pre-commit restoration, retained old on rollback failure, complete new bundle after commit and distinct reused-report failure. [FR-007/014, SC-004; depends T008]
- [x] T010 [US3] GREEN: track publication commit state and raise finite typed reasons from `src/corpus_ingest_core/study_guide_bundle.py` / `src/corpus_ingest_core/errors.py`; preserve existing report protocol, no automatic retry or false rollback claim. Rerun T009. [FR-014; depends T009]
- [x] T011 [US3] Run Core/derivation/index/contracts regression plus path/snapshot/report guard coverage from `specs/044-study-guide-mcp/quickstart.md`; record Windows native-link skips separately from portable mandatory checks in `specs/044-study-guide-mcp/implementation-log.md`. [FR-007/008/013/014, SC-004/005; depends T010]

## Phase 4: US1 — Preview in MCP (P1)

**Goal**: metadata-only preview of exactly one lecture action.
**Independent test**: new wrapper tests with a fake Core plus real-Core zero-write integration; isolate module registration until integration updates all registry pins.

- [x] T012 [US1] RED: add tests in `tests/test_study_guide_bundle.py` for the pure plan projector on generation, force, reuse and cover-only, including full-path discrimination and no filesystem/profile/provider access. Assert two planned report paths but unchanged Core preview actual report-path fields. [FR-002/003/011; depends T011]
- [x] T013 [US1] GREEN: add `describe_study_guide_plan(result)` to `src/corpus_ingest_core/study_guide_bundle.py`; project existing write sets and storage report paths only; add identity JSON dependency to planned reads, without a dataclass/schema change. Rerun T012. [FR-002/011; depends T012]
- [x] T014 [US1] RED: create `tests/test_mcp_study_guide_bundle.py` for exact five-parameter defaults, single preview delegation, projector use, preview envelope/read/write/reuse/report/LLM fields and safe fixed errors; inject body/credential marker text into known/unknown exceptions. [FR-001/002/003/009/011/014; depends T013]
- [x] T015 [US1] GREEN: add `src/corpus_ingest_core/mcp_tools_study_guide.py` using the existing FastMCP and action-plan/error helpers; format Core data and finite messages, no filesystem/readiness logic, raw error strings or shared-runtime changes. Rerun T014. [FR-001/002/003/009/011/014; depends T014]
- [x] T016 [US1] Add/run real-Core preview cases in `tests/test_mcp_study_guide_bundle.py`: source missing/finance, reuse, cover-only, force/refusal, no env/network/provider/writer, unchanged full tree manifests; update `specs/044-study-guide-mcp/implementation-log.md`. [FR-003/006/013, SC-002/003; depends T015]

## Phase 5: US2 — Confirm One Lecture (P1)

**Goal**: one confirmed Core operation; ack only when it generates; no chained work.
**Independent test**: fake Core delegation tests plus real Core/fake provider artifact/report tests through the tool.

- [x] T017 [US2] RED: in `tests/test_mcp_study_guide_bundle.py`, test one confirmed call, unchanged ack/force forwarding, no internal preview, no wrapper ack synthesis, absent/wrong ack before provider and metadata-only known/unknown failures including post-commit reason messages. [FR-004/005/009/011/014; depends T016]
- [x] T018 [US2] GREEN: implement confirmed delegation and success/error presentation in `src/corpus_ingest_core/mcp_tools_study_guide.py`, using `tool_success` serialization and top-level warnings copied from Core; keep other tool handlers untouched. Rerun T017. [FR-004/005/011/014; depends T017]
- [x] T019 [US2] Add/run real-Core fake-provider end-to-end cases in `tests/test_mcp_study_guide_bundle.py`: four-file generation, no-ack reuse, no-ack cover-only, force/derivation refusal, report and cleanup failure, fresh confirm reevaluation after fixture drift. Record whole-response no-leak and exact provider/writer counts. [FR-004/005/006/007/014, SC-001/003/004; depends T018]
- [x] T020 [US2] Add/run compatibility/safety assertions in `tests/test_mcp_study_guide_bundle.py` and `tests/test_study_guide_bundle.py`: Core/CLI/result/report keys unchanged, identity metadata stays local, no transcript transfer, no auto Tool25/download/transcribe/summary/cache, finance prompts and artifact ladder unchanged. [FR-008/011, SC-001/005; depends T019]

## Phase 6: Integration, Documentation and Closeout

- [x] T021 RED: update expected new-tool prefix/count/default contracts in `tests/test_mcp_tool_registry_contract.py`, `tests/test_console_entry_points.py`, `tests/test_mcp_setup_validation.py` and Tool25 fixed-slot assertions in `tests/test_mcp_workflow_derivation.py`; show missing facade registration fails before adding it. [FR-010, SC-005; depends T020]
- [x] T022 GREEN: append the new group/re-export within the order fence in `src/corpus_ingest_core/mcp_server.py`; update `scripts/validate_mcp_setup.py` to require 26 and the new name; synchronize live explanatory count comments in `pyproject.toml` only. Rerun T021 and facade/single-FastMCP/HTTP checks. [FR-010, SC-005; depends T021]
- [x] T023 RED: update future live-count/doc expectations in `tests/test_ai_governance_docs.py`, `tests/test_architecture_spec_docs.py`, `tests/test_spec_020_verified_research_report_catalog_docs.py`; run the unchanged dynamic docs-count checker to expose stale documentation. [FR-010/012; depends T022]
- [x] T024 GREEN: update the complete live-doc inventory in `specs/044-study-guide-mcp/plan.md`, including `docs/api.md`, `docs/mcp-usage.md`, `docs/usage.md`, `docs/verification-matrix.md` and `specs/README.md`; show separate lecture/derivation requests, partial/recovery/refusal and report-write semantics. Preserve historical counts/specs and rerun T023. [FR-002/010/012; depends T023]
- [x] T025 Run all relevant targeted sets in `specs/044-study-guide-mcp/quickstart.md`, including ack/no-leak/cache/path/report/registry/docs guards; record outputs and limitations in `specs/044-study-guide-mcp/implementation-log.md`. [FR-001–014, SC-001–005; depends T024]
- [x] T026 Run full `python -m pytest`, `python -m compileall src scripts`, `git diff --check` with the correct interpreter and isolated basetemp; record current counts, return codes and skips in `specs/044-study-guide-mcp/implementation-log.md`. Do not use planning-session results as implementation evidence. [SC-005; depends T025]
- [x] T027 Review behavior against `specs/044-study-guide-mcp/spec.md` separately from standards in `AGENTS.md` / `docs/ai-development-framework.md`; record both code-correctness and architecture-boundary findings in `specs/044-study-guide-mcp/implementation-log.md`. Keep reviewers read-only and fix findings through the sole writer with focused checks. [FR-001–014, SC-001–005; depends T026]
- [x] T028 Run Spec Kit converge for 044 against code/spec/plan/tasks; append any actual remaining work in `specs/044-study-guide-mcp/tasks.md`, complete it within scope, rerun checks when fixes justify it, and only then update package status/checkboxes plus final evidence in `specs/044-study-guide-mcp/implementation-log.md`. No commit or real-provider smoke. [SC-001–005; depends T027]

## Dependencies and Parallel Opportunities

```text
T001 → T002 → US3 (T003–T011) → US1 (T012–T016)
     → US2 (T017–T020) → integration (T021–T024)
     → verification/review/converge (T025–T028)
```

No `[P]` writer tasks: one writer and shared Core/registry state require ordered edits. Optional read-only work can inspect preservation cases during US3, compare envelopes during US1 and examine no-leak cases during US2, but cannot edit files or run suites against a changing tree. No parallel pytest processes sharing artifacts/basetemp.

## MVP / Completion Rule

US3 alone is an independently testable Core safety improvement, but 044's deliverable requires US3+US1+US2 and registry/docs integration. No preview-only or CLI-only closeout. 28 tasks total: setup 2, US3 9, US1 5, US2 4, integration/closeout 8. Expected initial state is all unchecked.

## Requirement Traceability

| Requirement | Primary task IDs |
| --- | --- |
| FR-001 | T014, T015 |
| FR-002 | T012, T013, T014, T015, T024 |
| FR-003 | T005, T014, T015, T016 |
| FR-004 | T017, T018, T019 |
| FR-005 | T007, T017, T018, T019 |
| FR-006 | T007, T008, T016, T019 |
| FR-007 | T003, T004, T009, T011, T019 |
| FR-008 | T004, T011, T020 |
| FR-009 | T014, T015, T017 |
| FR-010 | T002, T021, T022, T023, T024 |
| FR-011 | T012, T013, T014, T015, T017, T018, T020 |
| FR-012 | T023, T024 |
| FR-013 | T005, T006, T007, T008, T011, T016 |
| FR-014 | T006, T009, T010, T011, T014, T015, T017, T018, T019 |
| SC-001 | T019, T020, T025, T027, T028 |
| SC-002 | T005, T016, T025 |
| SC-003 | T005, T007, T016, T019, T025 |
| SC-004 | T003, T004, T007, T009, T011, T019, T025 |
| SC-005 | T001, T002, T011, T020, T021, T022, T025, T026, T027, T028 |

## Phase 7: Convergence

Acceptance reopened two P1 preservation gaps. These tasks are the remaining work; they do not renumber T001–T028.

- [x] T029 CRITICAL: at publication copy time, refuse instead of skipping a preserved entry whose metadata or safety check fails; keep the original directory bytes and do not publish. Public Core test injects the failure on `extra.bin`. per FR-007 (contradicts)
- [x] T030 CRITICAL: treat PermissionError and other I/O errors while reading an existing cover as refusal in both preview and confirm, not as cover-only unreadability. per spec clarification / FR-013 (contradicts)
- [x] T031 Map both refusals through Tool 26 to the fixed `unsafe_path` message, with no injected exception text, and keep the directory bytes unchanged. per FR-014 (partial)

## Phase 8: Convergence

Acceptance reopened a directory-metadata P1. `_lstat` still reports every `OSError` as absence, so an unreadable destination is published as an empty directory and its `.old` backup is removed. These tasks do not renumber T001–T031.

- [x] T032 CRITICAL: before creating staging, distinguish a missing destination from an unreadable one; refuse when the destination, a required ancestor, or an already listed preserved entry cannot be confirmed safe, and keep the original directory bytes. per FR-007 / US3 (contradicts)
- [x] T033 CRITICAL: fail closed on preview and confirm when recovery-sibling, ancestor, or 05/06 derivation metadata hits PermissionError or another OSError; do not treat that failure as absence. per FR-013 (contradicts)
- [x] T034: drive pre-commit rollback and post-commit cleanup from the phase this operation already confirmed; do not claim the original bundle was restored or that cleanup succeeded when that state cannot be confirmed. per FR-014 (partial)
- [x] T035: map the publisher destination-metadata refusal through Tool 26 to the fixed `unsafe_path` message, with no injected exception text, and keep the directory bytes unchanged. per FR-014 (partial)
