# Tasks: SPEC050 Learning bundle recovery

One active writer; test/review roles read-only. New behavior requires focused RED then GREEN.

## Phase1: Setup
- [x] T001 Record dirty baseline,29 tool signatures and approved scope in implementation-log.md (FR-001, FR-009, FR-010).

## Phase2: US1 - directories
- [x] T002 [US1] Add failing explicit-identity/five-location/state/safety/limits cases in tests/test_learning_bundle_recovery.py (FR-001, FR-002, FR-003, FR-004, FR-006, FR-007; SC-001).
- [x] T003 [US1] Implement bounded identity/directory observation in src/corpus_ingest_core/learning_bundle_recovery.py; run GREEN (FR-001, FR-002, FR-003, FR-004, FR-006, FR-007).

## Phase3: US2 - receipts
- [x] T004 [US2] Add failing both-codec/original-stem/missing-invalid-mismatch-cap cases in tests/test_learning_bundle_recovery.py (FR-004, FR-005, FR-007; SC-002).
- [x] T005 [US2] Implement capped strict receipt/output observations in learning_bundle_recovery.py; run GREEN (FR-004, FR-005, FR-007).
- [x] T006 [US2] Add focused privacy/zero-write/provider/cache/network/extras tripwires in tests/test_learning_bundle_recovery.py and confirm protected049 generation/query code unchanged (FR-007, FR-008, FR-009).

## Phase4: US3 - MCP/compatibility
- [x] T007 [US3] Add failing thin-wrapper/signature/no-leak cases in tests/test_mcp_learning_bundle_recovery.py (FR-001, FR-007, FR-008; SC-003).
- [x] T008 [US3] Implement src/corpus_ingest_core/mcp_tools_learning_recovery.py; run GREEN (FR-001, FR-007, FR-008).
- [x] T009 [US3] Add failing30-tool registry/facade/setup/docs guards in tests/test_mcp_tool_registry_contract.py and related guard files (FR-001, FR-009, FR-010; SC-003).
- [x] T010 [US3] Append group/re-export in mcp_server.py, update scripts/validate_mcp_setup.py and current docs/counts; run GREEN (FR-001, FR-009, FR-010).
- [x] T011 [US3] Run unchanged Tools25-29 and Skills regressions; record metadata-only/protected baseline evidence in implementation-log.md (FR-008, FR-009, FR-010).

## Phase5: Closeout
- [x] T012 Conduct separate read-only behavior/engineering reviews; reproduce and fix concrete findings via focused RED/GREEN, record implementation-log.md (FR-010).
- [x] T013 Run full pytest, compileall src scripts, git diff --check; record commands/results/skips in implementation-log.md (FR-010; SC-001, SC-002, SC-003, SC-004).
- [x] T014 Run converge on050 spec/plan/tasks, append/finish concrete gaps and mark specs/README.md implemented only after verification (FR-010; SC-004).

## Dependencies and strategy
US1 directory observation ->US2 receipt consistency ->US3 MCP/compatibility ->closeout. US1 independently accepts five-location fixtures; US2 independently accepts strict metadata/output observations; US3 verifies safe public envelope. MVP is offline diagnosis, no repair executor. Parallel examples: independent read-only behavior and engineering review; no parallel writers. All runtime and public docs ship together.
