# Tasks: Core Consolidation

**Feature**: 025-core-consolidation
**TDD**: characterization/guard RED before refactor GREEN; behavior freeze throughout.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec package + clarify | package + Session 2026-08-08 |
| C2 Freeze held | registry contract test unmodified; runner suites unmodified |
| C3 Predicates single-sourced | characterization table pre/post identical + boundary guard |
| C4 Weak writer deduped | boundary guard + failure-injection suites green |
| C5 Facade split | single `FastMCP`; facade guard; registry test green untouched |
| C6 Docs counts machine-checked | consistency checker + one-time sync |
| C7 Full verify | pytest / compileall / git diff --check |

## Spec Kit sequence

`constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge`

## Phase 1: Spec Kit

- [x] T001 Constitution: no amendment
- [x] T002 Specify package docs
- [x] T003 Clarify consolidation decisions in spec
- [x] T004 Plan / research / data-model / contracts / checklists
- [x] T005 Tasks + analyze table (below)

## Phase 2: Implement (batches)

- [x] T006 B1 conftest + `PODCAST_INGEST_DATA_DIR` + fixture contract guard (gated: full suite 1200 passed)
- [x] T007 B2 characterization truth table RED-lock, then `path_safety.py` + wrappers + boundary guard (gated: full suite 1252 passed; truth table identical pre/post)
- [x] T008 B3 `run_report_io.py` extraction + boundary guard (same gate as T007)
- [x] T009 B4 `mcp_runtime` + 4 group modules + facade + rejection-reason single-source + facade guard (registry contract test unmodified and green; 187 targeted passed)
- [x] T010 B5 docs count checker + one-time doc sync incl. 023/024/025 rows (superseded stale pins in `test_spec_020_*` flipped to negative; other literal pins retained alongside the checker — see research deviations)
- [x] T011 B6 satellite: schema-version import, evals-dir single source in `storage.py` + module-level re-exports, verification-matrix + agent-handoff boundary rows

## Phase 3: Converge + verify

- [x] T012 Converge FR-001–011 vs code; known-debt register final (research.md deviations log)
- [x] T013 Full pytest + compileall + `git diff --check`; Status → Implemented (final gate: 1260 passed, 7 skipped; compileall clean; git diff --check clean — CRLF warnings are the repo's normal Windows line-ending notices, not check failures)

## Analyze (pre-implement)

| FR | Task | Risk |
| --- | --- | --- |
| FR-001/002 | all | freeze broken by accident → registry/no-leak suites are the tripwire |
| FR-003 | T007 | accepted-set drift → characterization-first |
| FR-004 | T008 | failure-semantics drift → raw OSError re-raise, kwargs identical |
| FR-005/006 | T009 | import order / alias misses → grep inventory, facade guard |
| FR-007 | T010 | codifying stale count → two-step landing, N from live registry |
| FR-008 | T006 | fixture blind spots → reflection coverage test |
| FR-009–011 | T011 | monkeypatch target breakage → module-level re-exports |

**CRITICAL constitution issues**: none (behavior-frozen internal refactor).
