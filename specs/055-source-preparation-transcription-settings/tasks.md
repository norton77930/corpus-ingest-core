# Tasks: Source preparation transcription settings

Date: 2026-10-07. Planning followed by implementation authorized. Root sole writer; research/reviews read-only. No branch/commit/worktree/deployment.

## Phase 1: Planning

- [x] T001 Constitution review, explicit selection and scoped baseline (FR-012, SC-005).
- [x] T002 Research config/digest/worker/payload compatibility (FR-001, FR-004, FR-009).
- [x] T003 Spec, clarification scan, plan, checklists and consistency analysis (FR-001–FR-012, SC-001–SC-005).

## Phase 2: Configuration and preview

- [x] T004 RED: omitted/valid/invalid/language/precision settings tests (FR-001, FR-002, SC-001).
- [x] T005 Add frozen settings and optional profile parsing in preparation_transcription.py/models.py/config.py (FR-001, FR-002).
- [x] T006 GREEN: config/profile regressions (FR-001, FR-002, SC-001).
- [x] T007 RED: preview disclosure, GPU refusal, actual/unknown/title metadata and zero-write checks (FR-003, FR-006, FR-008, SC-001, SC-004).
- [x] T008 Lazy capability observation and configured/actual projections (FR-003, FR-006).
- [x] T009 Retain selected validated JSON snapshot for actual metadata/warnings (FR-008, SC-004).
- [x] T010 GREEN: preview/refusal/legacy artifact regressions (FR-003, FR-006, FR-008).
- [x] T011 RED: model/device/precision drift before confirm and duplicate reuse (FR-004, SC-002).
- [x] T012 Bind new settings and retain legacy context/hash checks (FR-004, FR-009, SC-002).

## Phase 3: Ledger and worker

- [x] T013 RED: v2 roundtrip/corruption and v1 read-only byte preservation (FR-009, SC-004).
- [x] T014 Exact dual payload validation without SQLite migration (FR-004, FR-009).
- [x] T015 Legacy defaults only under unchanged absent new configuration (FR-009).
- [x] T016 RED: both source executors, post-admission drift, hardware loss and metadata mismatch (FR-005–FR-007, SC-002, SC-003).
- [x] T017 Persisted execution and matching metadata before v2 readiness (FR-005, FR-007).
- [x] T018 Safe failure/slot/no-retry/fallback behavior (FR-005, FR-006, FR-012, SC-003).
- [x] T019 Approved/actual accepted/status projection without current files/config reads (FR-007, FR-009, FR-010).
- [x] T020 GREEN: lifecycle/process/partial/default executor regressions (FR-005–FR-010, SC-002–SC-004).

## Phase 4: MCP and Skill

- [x] T021 Existing difference/unknown and preserved bytes end-to-end (FR-008, SC-004).
- [x] T022 Registry/signature/fixed error/additive schema checks (FR-010, SC-005).
- [x] T023 Source-preparation Skill/reference update (FR-011).
- [x] T024 Owned dialogue fixtures and malformed/mismatched/unknown settings cases (FR-011, SC-005).
- [x] T025 Usage/porting/agent guidance, registry/roadmap and plan marker (FR-003, FR-010–FR-012).
- [x] T026 Owned SDK worker settings fixture; label separately from Hermes (FR-005, FR-011, SC-003, SC-005).

## Phase 5: Closeout

- [x] T027 Scoped regressions and secret/path/cache/docs/registry guards (FR-012, SC-005).
- [x] T028 Fresh read-only behavior/engineering review and focused fixes (FR-012).
- [x] T029 Full pytest/compileall/diff, actual results/skips (FR-012, SC-005).
- [x] T030 Converge, append genuine gaps only, final evidence/limits (FR-012, SC-005).

Dependencies: planning → config/preview → binding/ledger → worker → MCP/Skill → closeout. Serialize writers; preserve production and uncertain history. No unlabelled real media/provider/deployment.
