# Tasks: Verified Research Report Coverage Index

**Feature**: 022-verified-research-report-coverage-index  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**TDD**: RED before GREEN for each runtime slice.

## Completion Contract

| Claim | Status | Required evidence |
| --- | --- | --- |
| C1 Package docs complete | PASS | docs contract test green |
| C2 Core join/filter/limit | PASS | focused coverage tests green |
| C3 Zero-write / no body read | PASS | tree snapshot + guards green |
| C4 Thin CLI | PASS | CLI tests green |
| C5 MCP Tool 19 append-only | PASS | registry exact 19; Tools 1–18 unchanged |
| C6 Docs/registry alignment | PASS | handoff/roadmap/README/mcp docs |
| C7 Full verification | PASS | pytest + compileall + git diff --check |

## Phase 1: Spec Kit package

- [x] T001 Create package under `specs/022-verified-research-report-coverage-index/`
- [x] T002 Set `SPECIFY_FEATURE_DIRECTORY` / `.specify/feature.json`
- [x] T003 Docs contract RED→GREEN `tests/test_spec_022_verified_research_report_coverage_docs.py`

## Phase 2: Core RED→GREEN

- [x] T004 Models/errors/exports stubs
- [x] T005 RED Core join/filter/limit/orphan/zero-write tests
- [x] T006 Implement `verified_research_report_coverage.py`
- [x] T007 GREEN Core tests

## Phase 3: Interfaces

- [x] T008 RED CLI + MCP registry tests
- [x] T009 Thin CLI script
- [x] T010 MCP adapter + Tool 19 append
- [x] T011 GREEN CLI/MCP tests

## Phase 4: Docs + verify

- [x] T012 Update specs/README, agent-handoff, roadmap, verification-matrix, mcp-usage, README, validate_mcp_setup as needed
- [x] T013 Focused + full verification; mark Implemented

## Dependencies

```text
T001–T003 → T004–T007 → T008–T011 → T012–T013
```

## Final verification notes

```text
Pre-converge baseline: 1157 passed, 7 skipped
Post-converge full:    1164 passed, 7 skipped
python -m compileall src scripts → OK (earlier + scripts compile)
```

## Phase 5: Convergence (post formal analyze/converge)

- [x] T014 Add MCP Tool 19 adapter tests in `tests/test_mcp_server.py` matching catalog/revalidation pattern: one Core delegation, invalid envelope before Core, generic error without path/traceback (FR-010, plan: MCP, missing)
- [x] T015 Complete README surfaces for 022: directory listing `query_verified_research_report_coverage.py`, Core Functions entry, and CLI example (FR-009 / plan T012, partial)
- [x] T016 Re-run focused MCP/docs tests and full verification; only then keep **Status: Implemented** (C7 revalidate)

Convergence outcome: **converged** after T014–T016 (no further open findings).
