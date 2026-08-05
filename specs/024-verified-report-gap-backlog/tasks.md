# Tasks: Verified Report Gap Backlog

**Feature**: 024-verified-report-gap-backlog  
**TDD**: RED before GREEN.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec package + clarify | package + Session 2026-08-05 |
| C2 Core reuses 022 gaps | tests |
| C3 Zero-write | tree snapshot |
| C4 CLI + Tool 21 | CLI + registry |
| C5 Analyze/converge | this file |
| C6 Full verify | pytest/compileall |

## Spec Kit sequence

`constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge`

## Phase 1: Spec Kit

- [x] T001 Constitution: no amendment
- [x] T002 Specify package docs
- [x] T003 Clarify B-lite decisions in spec
- [x] T004 Plan / research / data-model / contracts / checklists
- [x] T005 Tasks + analyze table (below)

## Phase 2: Implement

- [x] T006 Docs contract test RED
- [x] T007 Core models/errors + RED tests
- [x] T008 Implement Core wrapper
- [x] T009 CLI + MCP Tool 21 + registry 21
- [x] T010 Docs alignment (handoff/roadmap/mcp/README)

## Phase 3: Converge + verify

- [x] T011 Converge FR-001–009 vs code (wrapper reuses 022; Tool 21 append-only)
- [x] T012 Full pytest + compileall; Status Implemented

## Analyze (pre-implement)

| FR | Task | Risk |
| --- | --- | --- |
| FR-001–006 | T007–T008 | low if wrap 022 |
| FR-007–008 | T009 | registry exact 21 |
| FR-009 | T010 | docs drift |

**CRITICAL constitution issues**: none expected (read-only).
