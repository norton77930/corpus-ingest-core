# Tasks: Historical Episode Verified Report Path

**Feature**: 023-historical-episode-verified-report-path  
**TDD**: RED before GREEN.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec package | docs tests |
| C2 Core suggest zero-write | focused tests |
| C3 Skill one-confirm-stop | skill contract tests |
| C4 CLI + Tool 20 | CLI/MCP registry tests |
| C5 Docs + full verify | pytest/compileall |

## Tasks

- [x] T001 Create package docs under `specs/023-...`
- [x] T002 Docs contract test
- [x] T003 Models/errors/exports + Core RED tests
- [x] T004 Implement Core suggest
- [x] T005 Skill + skill tests
- [x] T006 CLI + MCP Tool 20 + registry
- [x] T007 Docs alignment + full verification; Status Implemented

## Phase: Formal Spec Kit gates (retroactive 2026-08-05)

- [x] T008 Clarify: record Session 2026-08-05 decisions in `spec.md` (one-confirm-per-request; report_present no 021; invalid via exception; no mega-runner)
- [x] T009 Analyze: FR-001–010 covered; no CRITICAL constitution conflicts (see package research/session notes)
- [x] T010 Converge: FR-006 zero-write tree test; FR-003 exception wording; drop private storage pattern import for episode_ref

## Analyze snapshot (T009)

| FR | Covered by | Status |
| --- | --- | --- |
| FR-001 | Core + tests | PASS |
| FR-002 | Core reject latest/next | PASS |
| FR-003 | codes + InputError | PASS (wording aligned) |
| FR-004 | publish_ready path | PASS |
| FR-005 | completion_action path | PASS |
| FR-006 | zero-write test | PASS (T010) |
| FR-007 | CLI + CLI tests | PASS |
| FR-008 | Tool 20 registry | PASS |
| FR-009 | Skill + skill tests | PASS |
| FR-010 | no new deps | PASS |

**Constitution**: no CRITICAL issues (read-only suggest, thin CLI/MCP, no advice, no auto cache rebuild).

## Converge snapshot (T010)

| Finding | Severity | Resolution |
| --- | --- | --- |
| FR-006 missing tree snapshot | HIGH | T010 zero-write test added |
| FR-003 invalid_input code wording | MEDIUM | Spec clarified → raise error |
| private storage._SAFE_EPISODE_REF | LOW | inline same regex public rule |

**Outcome**: converged after T010; no further open findings.