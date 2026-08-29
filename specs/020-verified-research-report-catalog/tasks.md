# Tasks: Verified Research Report Catalog

**Feature**: 020-verified-research-report-catalog
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contract**: [contracts/verified-research-report-catalog.md](contracts/verified-research-report-catalog.md)
**TDD**: Constitution Principle IX requires focused RED before GREEN for each new runtime behavior.

## Completion Contract

- **C1 — 019 closure/hygiene prerequisite**: The approved Stage 0 focused 47-test evidence closes the SPEC 019 CLI hygiene prerequisite; its fixed category-only error boundary is preserved before catalog closure work.
- **C2 — Core list**: Deterministic bounded canonical bundle discovery, optional exact filters, and missing-root empty/zero-write behavior are covered by focused tests.
- **C3 — Core search**: Search uses only safe manifest-derived metadata; tests prove report/transcript/source body content is never read.
- **C4 — Core inspect**: Exact-locator inspection fail-closes on containment, canonical identity, exact-file-set, manifest schema/hash/size, or report-identity failure; success says only self-consistency with `source_currentness_status=not_evaluated`.
- **C5 — Thin CLI**: `query_verified_research_report_catalog.py` exposes `list/search/inspect`, delegates once to Core, and serializes sanitized JSON only.
- **C6 — MCP append**: `query_verified_research_report_catalog` is Tool 17; Tools 1–16 remain ordered and contract-compatible.
- **C7 — Verification/closure**: Focused Core/CLI/MCP/docs tests, full pytest, `compileall`, and `git diff --check` are green; docs and implementation tasks have evidence before checking completion.

## Phase 1: Specification Setup

- [x] T001 Create the complete Spec Kit package under `specs/020-verified-research-report-catalog/`.
- [x] T002 Add and run focused RED documentation contract `tests/test_spec_020_verified_research_report_catalog_docs.py` before package documents exist.
- [x] T003 Encode Core, CLI, MCP, data, safety, and quickstart contracts; keep runtime/CLI/MCP untouched.

## Phase 2: Foundational RED Tests (blocking)

- [x] T004 [P] Add Core signature/result-model RED tests for `list_verified_research_reports`, `search_verified_research_reports`, and `inspect_verified_research_report` in `tests/test_verified_research_report_catalog.py`.
- [x] T005 [P] Add RED filesystem fixture tests for missing root zero-write, exact filters, sort, limits, per-level caps, canonical `v1-[a-f0-9]{64}`, symlink/junction rejection, and out-of-root containment in `tests/test_verified_research_report_catalog.py`.
- [x] T006 [P] Add RED body-read guard tests proving list/search never read `report.json`, `report.md`, transcript, or source artifact bodies in `tests/test_verified_research_report_catalog.py`.
- [x] T007 [P] Add RED inspect tests for exact three files, manifest schema, directory/manifest/report identity, SHA-256/size mismatches, malformed manifests, and mandatory `source_currentness_status=not_evaluated` in `tests/test_verified_research_report_catalog.py`.
- [x] T008 Add result models, errors, exports, and bounded input validation stubs in `src/corpus_ingest_core/models.py`, `errors.py`, and `__init__.py` only as required to make RED imports resolve.

## Phase 3: User Story 1 — List Canonical Bundles (P1) [US1] — C2

**Goal**: Discover eligible local canonical bundle summaries without write or path disclosure.
**Independent test**: Fixture tree with matching/nonmatching/malicious candidates returns sorted bounded safe summaries and no writes.

- [x] T009 [US1] Implement non-reparse, contained, bounded level-by-level catalog traversal in `src/corpus_ingest_core/verified_research_report_catalog.py`.
- [x] T010 [US1] Implement safe manifest projection and eligibility validation without report/transcript/source-body reads in `src/corpus_ingest_core/verified_research_report_catalog.py`.
- [x] T011 [US1] Implement `list_verified_research_reports` exact filters, 50 default/100 maximum limit, deterministic ordering, and missing-root empty result.
- [x] T012 [US1] GREEN: run and pass T004–T006 list-related tests.

## Phase 4: User Story 2 — Search Safe Metadata (P1) [US2] — C3

**Goal**: Search only the safe projection without widening the read boundary.
**Independent test**: Body-read guards remain untouched while known safe metadata terms match in deterministic bounded order.

- [x] T013 [US2] Implement query normalization and safe scalar matching for `search_verified_research_reports` in `src/corpus_ingest_core/verified_research_report_catalog.py`.
- [x] T014 [US2] Reject blank/unsafe/oversize query and preserve exact optional filters, bounds, and deterministic sort.
- [x] T015 [US2] GREEN: run focused search/body-read safety tests from `tests/test_verified_research_report_catalog.py`.

## Phase 5: User Story 3 — Inspect Exact Bundle (P1) [US3] — C4

**Goal**: Verify only local bundle self-consistency for an exact locator.
**Independent test**: Valid fixture succeeds; each structural or integrity mutation returns a bounded invalid verdict with currentness not evaluated.

- [x] T016 [US3] Implement exact canonical locator resolution and pre-read containment/reparse checks in `src/corpus_ingest_core/verified_research_report_catalog.py`.
- [x] T017 [US3] Implement exact-three-file, manifest schema/identity, report JSON identity, and manifest SHA-256/size validation.
- [x] T018 [US3] Implement sanitized inspection result with category-only failures and mandatory `source_currentness_status=not_evaluated`.
- [x] T019 [US3] GREEN: run and pass T007 inspect tests, including tampering and no raw-manifest/absolute-path assertions.

## Phase 6: Interfaces (after Core GREEN) — C5/C6

- [x] T020 [P] Add CLI RED tests in `tests/test_verified_research_report_catalog_cli.py` for `list/search/inspect`, input parsing, one-Core-call delegation, and JSON-safe output.
- [x] T021 [P] Add MCP registry/adapter RED tests in `tests/test_mcp_tool_registry_contract.py` and `tests/test_mcp_server.py` for append-only Tool 17, existing envelope, and unchanged Tools 1–16.
- [x] T022 [C5] Implement thin `scripts/query_verified_research_report_catalog.py`; no output/export/path/network/provider options.
- [x] T023 [C6] Append thin `query_verified_research_report_catalog` MCP adapter as Tool 17 in `src/corpus_ingest_core/mcp_server.py`; do not alter Tool 1–16.
- [x] T024 [C5] GREEN: run CLI focused tests.
- [x] T025 [C6] GREEN: run MCP adapter and registry focused tests.

## Phase 7: Cross-cutting Verification — C7

- [x] T026 [P] Update user-facing docs/registry/setup validation only if implementation changes require Tool 17 documentation; retain the no-body-read/no-export boundaries.
- [x] T027 [C7] Run focused SPEC 020 Core/CLI/MCP/docs verification; final targeted result: **114 passed, 3 skipped** (platform symlink/junction capability skips).
- [x] T028 [C7] Run full verification: `python -m pytest` (**1084 passed, 3 skipped, 1 known pytest-cache ACL warning**), `python -m compileall src scripts` (passed), and `git diff --check` (passed).

## Dependencies and Delivery Order

```text
T001–T003 complete → T004–T008 RED foundation
T004–T008 → US1/C2 → US2/C3 → US3/C4 → CLI/C5 + MCP/C6 → C7
```

US2 shares the safe projection established by US1. US3 shares only containment and locator validation, not body-reading behavior. CLI and MCP begin only after Core slices are green.

## Completion Conditions

- [x] C1 SPEC 019 closure/hygiene prerequisite has Stage 0 focused 47-test evidence.
- [x] C2 list behavior has focused green evidence.
- [x] C3 search body-read boundary has focused green evidence.
- [x] C4 inspect self-consistency/currentness boundary has focused green evidence.
- [x] C5 CLI is thin and green.
- [x] C6 Tool 17 is append-only and green.
- [x] C7 required verification commands are green and recorded with actual output.
