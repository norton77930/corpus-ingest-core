# Tasks: Hermes MCP and Portable Skills Integration

**Feature**: 026-hermes-mcp-integration  
**TDD**: one public seam RED → minimal GREEN per slice.

## Completion Contract

| Claim | Status | Evidence |
| --- | --- | --- |
| C0 R2 scope authorized | PASS-current | approved plan names both repos/runtime paths and prohibitions; runtime/build/inference approvals were obtained before each gated action |
| C1 Spec gate complete | PASS-current | package/contracts/checklists/tasks remain the governing record; feature status is Blocked rather than falsely Implemented |
| C2 stdio/registry frozen | PASS-current | transport/facade/registry targeted tests; original registry test unchanged; exact remote order digest `e71b93866a86503155967cc1648cbc83ce1407815fb6d1724c32712fc305076d` |
| C3 sidecar safe/persistent | PASS-current | image `sha256:c8ca1182966a3dc710df96a72017d5760cf5c068f1f52d3bbe9f56bdab263b6e`; `mcp==1.28.1`; non-root user; both Compose configs valid; healthy container; 21 tools discovered |
| C4 config merge recoverable | PASS-current | pre-mutation `applying` manifest, mutation flags, required-field/type validation, backup digest checks, post-restore verification, idempotent rollback drift detection, and bounded manifest-update failures; `test_hermes_integration.py` green |
| C5 four Skills portable | PASS-current | exact four-Skill digest/allowlist/shadow checks plus previous-target recovery rename and crash-recoverable staged replacement; uninterrupted atomic directory exchange is explicitly not claimed |
| C6 direct smoke endpoint equality | PASS-current | exactly one authorized `hermes-direct-smoke-v2` live run exited 0 with exact 21 tools, one read-only call, one `confirm=false` preview, protocol＋application success, exact safety booleans, and all three metadata/content endpoint-equality pairs true; no protected digest/path/content was emitted |
| C7 Hermes request bounded | BLOCKED/FAIL | v0.19.0 runtime evidence is insufficient; official v0.20.0 tag `v2026.8.3` hooks are promising but lack canonical fallback evidence and an approved safe projection collector. Candidate runtime validation is not evaluated; no upgrade/inference/session-dump workaround permitted |
| C8 migration operable | PASS-current | portable rollback requires exact manifest-bound targets; current-machine runbook separates the template/Skill helper transaction from the exact Compose/template/live-config byte-backup route |

Assurance: code reviewer for compatibility/error/redaction/rollback; architecture reviewer for single-instance/network/lifecycle/data-flow. Exactly one final verification invocation after both reviews pass.

## Phase 1: Spec Gate

- [x] T001 Constitution review: no amendment
- [x] T002 Specify/clarify decisions and R2 scope
- [x] T003 Plan/research/data model/contracts/checklists/tasks
- [x] T004 Analyze package consistency and resolve preflight facts (SDK 1.28.1 public settings, port 8767 free, `skills.external_dirs`, Streamable HTTP URL default, non-interactive MCP test; C7 metadata remains runtime-gated)

## Phase 2: Implement

- [x] T005 RED/GREEN single-instance Streamable HTTP seam and thin runner (27 targeted registry/facade/transport tests passed)
- [x] T006 Sidecar Dockerfile/Compose and static deployment contracts (4 targeted deployment tests passed)
- [x] T007 RED/GREEN structured Hermes config plan/apply/rollback (synthetic preservation/no-op/failure/redaction/rollback green)
- [x] T008 RED/GREEN four-Skill manifest sync/rollback (actual source-root preflight repaired to select exactly four and ignore unrelated Skills; allowlist/digest/shadow/rollback green; 9 combined targeted tests passed)
- [x] T009 Targeted tests/preflight, exact backup, incremental OpenAB Compose/template/live-leaf update, and four-Skill synchronization
- [x] T010 Historical pinned image build/start, health, direct exact-21 readiness, read-only call, and `confirm=false` preview with metadata-only manifests; current v2 content-equality capability is implemented/tested but has not run live
- [x] T011 One bounded fresh-session Hermes preview attempted exactly once; protected-surface metadata stayed unchanged, but C7 remains BLOCKED/FAIL. v0.20.0 `v2026.8.3` hooks are docs-only candidate capability with runtime validation not evaluated
- [x] T012 Portable build/restore/readiness/upgrade/rollback runbook and governance docs; 79 targeted/governance tests passed

## Phase 3: Converge and Seal

- [x] T013 Converged FR-001–013 against code/evidence: FR-001–010/012–013 are PASS-current; FR-011/C7 remains BLOCKED/FAIL, so feature status remains Blocked
- [x] T014 Required reviewer re-check PASS: code review confirmed descriptor-only traversal, bounded CLI/no-leak, framing, conjunction, and direct-call contract; architecture/security review confirmed opaque-input data flow, endpoint-equality claim precision, POSIX-only execution boundary, C6/C7 separation, and Blocked governance
- [x] T014a Single C6 live validator executed exactly once after explicit named-source/container authorization: process exit 0, `ok=true`, exact 21 order/digest, one read-only and one `confirm=false` preview, `dry_run=true`, `requires_confirmation=true`, and all three endpoint metadata/content equality pairs true. Invocation count is 1; do not rerun
- [ ] T015 Final verification intentionally not run: C7 remains BLOCKED/FAIL; Status must not become Implemented

## Analyze Matrix

| FR | Tasks | Primary risk |
| --- | --- | --- |
| FR-001–004 | T005 | second instance or registry/stdio drift |
| FR-005–006 | T006/T009/T010 | secret inclusion, network exposure, port collision |
| FR-007 | T007/T009 | YAML clobber or secret-bearing output |
| FR-008 | T008/T009 | shadowing, partial copy, rollback mismatch |
| FR-009–011 | T009–T011 | unsafe runtime action or unverifiable Hermes behavior |
| FR-012–013 | T012–T015 | non-portable recovery or evidence leakage |

**CRITICAL constitution issues**: none after approved R2 scope; implementation must stop if a preflight fact contradicts the approved topology or safe evidence path.
