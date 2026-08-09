# Feature Specification: Core Consolidation (Behavior-Frozen Refactor)

**Feature Branch**: `025-core-consolidation`
**Created**: 2026-08-08
**Status**: Implemented

**Input**: Consolidate five verified internal-debt families (divergent path-safety predicates, duplicated weak report-write protocol, `mcp_server.py` monolith, drifting doc tool-count claims, missing shared test fixtures) behind a **hard behavior freeze**: no MCP tool, CLI, or runner may change its externally observable behavior.

## Clarifications

### Session 2026-08-08

- Q: Refactor before or after the next feature epics (Hermes mount, deterministic batch backfill, market-data layer)? → A: **Consolidation first** — every upcoming epic would otherwise copy the divergent patterns again.
- Q: Path-safety reconciliation — strictest-union or per-context strictness? → A: **Per-context strictness parameter.** The 017 runner variant (rejects all `:` and absolute paths) is a deliberately tighter no-leak boundary, not an accident; union-merging would change accepted sets and violate the freeze.
- Q: Upgrade the five weak `.part` report writers to `write_atomic_audit_report_pair`? → A: **No — dedupe only.** The strong protocol changes artifact bytes (injects an `audit_report_pair` JSON key and a Markdown marker line); upgrading is an observable behavior change requiring its own spec. Recorded as the top post-025 candidate.
- Q: Does making `storage.DATA_DIR` environment-overridable violate the freeze? → A: Accepted as the **only runtime-visible change** in the epic; with `PODCAST_INGEST_DATA_DIR` unset the value is byte-identical to today (`Path("data")`).
- Q: Constitution amendment needed? → A: **No.** All nine principles are preserved; Principle II (stable core contracts) is the point of the freeze.

## User Scenarios & Testing

### User Story 1 — Future feature work stops inheriting debt (Priority: P1)

A maintainer adding Tool 22 or a new runner after this epic gets: one path-safety structural source, one weak-protocol writer, a modular MCP registration facade with an explicit playbook, machine-checked doc counts, and a shared test fixture — instead of copy-paste seeds that diverge.

**Independent Test**: grep-style boundary guard tests fail if a new module re-defines the safety regexes, re-implements the weak writer, constructs a second `FastMCP`, or adds an unmarked tool-count claim to governed docs.

### User Story 2 — Nothing observable changed (Priority: P1)

An operator or agent using any of the 21 MCP tools, 41 CLI scripts, or 8 corpus runners sees identical responses, identical report bytes, identical error messages (stdout and stderr), and an identical registry.

**Independent Test**: `tests/test_mcp_tool_registry_contract.py` passes **without a single edit**; all pre-existing runner no-leak and failure-injection suites pass unmodified; the pre-refactor path-safety characterization truth table still holds post-refactor.

## Safety and Data Boundaries

- No new side effects, no new writes, no LLM paths touched, no cache behavior change.
- Every spec 008–024 no-leak boundary (forbidden output fragments incl. stderr) must keep holding; the freeze is enforced by leaving those suites untouched.
- No investment advice / no live market API surfaces are modified.

## Requirements

- **FR-001 (Freeze)**: The MCP registry MUST keep exactly 21 tools with unchanged registration order, names, signatures, and parameter defaults; `tests/test_mcp_tool_registry_contract.py` MUST pass with zero modifications.
- **FR-002 (Freeze)**: Runner/CLI observable outputs MUST be unchanged: run-report JSON/Markdown bytes, error types, error message strings (stdout/stderr), and dry-run/confirm semantics.
- **FR-003 (D1)**: A single structural path-safety source `src/podcast_ingest_core/path_safety.py` MUST provide the shared skeleton `is_safe_local_path_structure(value, *, allow_absolute)` plus the shared regex constants; the four runner `_is_safe_local_path` functions MUST become thin wrappers that keep their names, their per-module round-trip conjuncts, and their exact accepted/rejected sets. A characterization truth-table test MUST be committed green **before** the refactor and MUST NOT change after it.
- **FR-004 (D2)**: A single weak-protocol writer `src/podcast_ingest_core/run_report_io.py::write_part_staged_report_pair` MUST replace the four byte-identical `.part` staging bodies (audio download / local transcription / remediation / episode workflow) byte-equivalently (same serialization kwargs, `.part` naming, unlink/write/replace order, raw `OSError` re-raise), and `write_part_staged_markdown` MUST absorb the episode-intake markdown-only variant; per-runner exception mapping and message formats (which differ: `{exc}` vs `{type(exc).__name__}`) MUST stay in their modules. Weak→strong protocol upgrade is OUT OF SCOPE.
- **FR-005 (D3)**: `mcp_server.py` MUST become a pure facade: exactly one `FastMCP(` construction in `src` (in `mcp_runtime.py`); all 21 `@mcp.tool()` decorations MUST live in four group modules (`mcp_tools_read`, `mcp_tools_side_effect`, `mcp_tools_corpus_workflows`, `mcp_tools_verified_report_queries`) whose import order inside the facade defines registration order; the facade MUST re-export every tool function and every dependency-module alias that existing tests monkeypatch through `mcp_server.<attr>`; group modules MUST NOT import `mcp_server`.
- **FR-006 (D3)**: The completion-workflow confirmed-request rejection rules MUST be single-sourced in core as `confirmed_request_rejection_reason(...)`; the MCP early gate keeps its normalization wrapper and delegates; the CLI imports the canonical message constants; all emitted bytes unchanged.
- **FR-007 (D4)**: A registry-derived docs checker MUST compute N from the live registry and validate every tool-count claim in governed docs (`README.md`, `docs/*.md`, `specs/README.md`): current-marked claims MUST equal N, historical-marked claims are exempt, unmarked claims FAIL. Stale lines (`docs/architecture.md` "exact 20", `docs/agent-handoff.md` "18", `specs/README.md` "20" + missing 023/024 rows) MUST be synced once. Superseded literal pins are removed only after the checker is green alongside them.
- **FR-008 (D5)**: `tests/conftest.py` MUST provide an opt-in `tmp_data_dirs` fixture that patches every `storage` `*_DIR` constant (discovered by reflection) plus the known evals-path bypass constants; `storage.DATA_DIR` MUST honor `PODCAST_INGEST_DATA_DIR` at import, defaulting byte-identically to `Path("data")`. Existing `_use_tmp_data_dirs` helper copies stay valid; new test files MUST use the fixture (allowlist freeze).
- **FR-009 (Satellite)**: `verified_research_report_source_revalidation.py` MUST import `REPORT_SCHEMA_VERSION` instead of re-typing the literal; each evals reports-dir path MUST have one defining module with module-level re-exports elsewhere (monkeypatch targets preserved).
- **FR-010 (Guards)**: Each consolidated boundary MUST gain a grep/inspect-style guard test (pattern: `tests/test_llm_provider_factory_boundary.py`) so re-divergence is a test failure, and MUST be registered in `docs/verification-matrix.md` and the `docs/agent-handoff.md` boundary map.
- **FR-011 (Known debt)**: Deferred items MUST be recorded in this package: function-local constant imports masking dependency cycles (`verified_research_lineage.py:859-986` family), weak→strong writer upgrade, tightening the 015 predicate's missing round-trip check.

## Success Criteria

- Full suite green with `test_mcp_tool_registry_contract.py` unmodified.
- Path-safety characterization table identical before and after the refactor.
- Boundary guard tests turn each debt pattern's reappearance into a red test.
- Governed docs can no longer carry an unmarked or wrong tool count silently.

## Assumptions

1. The four predicate variants' current accepted/rejected sets are each runner's spec'd contract (including the 015 variant's missing round-trip conjunct — preserved, not fixed).
2. `scripts/run_mcp_server.py` continues to import `podcast_ingest_core.mcp_server.run`.

## Out of Scope (v1)

- Weak→strong report-protocol upgrade (post-025 candidate #1)
- Sub-packaging the flat 63-module namespace; runner-family engine extraction
- Renaming `podcast_id` / `episode_ref` (source-neutral naming deferred to multi-source work)
- Hoisting lineage function-local imports
- Any MCP surface, tool, or parameter change
