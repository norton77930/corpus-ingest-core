# Feature Specification: Metadata Search MCP Core

**Feature Branch**: `003-metadata-search-mcp-core`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for deterministic mention extraction,
SQLite cache, transcript and mention search, MCP stdio tools, MCP setup docs,
and MCP tool-use eval artifacts.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed Phase 7C constitution, no amendment.
- `$speckit-specify`: this file records as-built metadata/search/MCP requirements.
- `$speckit-clarify`: no high-impact ambiguity; current code/tests/docs are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked consistency across spec, plan, and tasks.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers the current metadata/search/MCP scope.

## User Scenarios & Testing

### User Story 1 - Extract deterministic metadata (Priority: P1)

Users can extract mentions from transcript segments without LLM calls.

**Independent Test**: `test_entity_extractor.py`.

### User Story 2 - Search indexed podcast artifacts (Priority: P2)

Users can rebuild SQLite metadata cache and search transcripts or mentions.

**Independent Test**: `test_cache.py` and `test_search.py`.

### User Story 3 - Use MCP tools safely (Priority: P3)

MCP clients can call read/search tools and dry-run first side-effect tools with
standard response envelopes.

**Independent Test**: `test_mcp_server.py`, `test_mcp_setup_validation.py`,
`test_docs_mcp_eval.py`, and `test_mcp_eval_report_script.py`.

## Functional Requirements

- **FR-001**: System MUST extract deterministic mention artifacts from transcript segments.
- **FR-002**: System MUST rebuild SQLite cache from existing local artifacts on explicit request.
- **FR-003**: System MUST support transcript search and mention search from local cache/artifacts.
- **FR-004**: System MUST expose MCP tools through stdio without changing core behavior.
- **FR-005**: MCP side-effect tools MUST remain dry-run first and use established envelopes.
- **FR-006**: MCP completion MUST warn about manual cache rebuild when artifacts may be stale.
- **FR-007**: MCP eval prompts and reports MUST preserve audit records.

## Safety and Data Boundaries

- Mention extraction and search are deterministic.
- MCP exposed side effects are dry-run first.
- MCP responses must not leak `.env`, API key values, raw transcript dumps in dry-run, or tracebacks.
- Search and mentions are podcast evidence helpers, not investment advice.

## Success Criteria

- **SC-001**: Existing metadata, cache, search, MCP, and eval tests pass.
- **SC-002**: MCP error/success/dry-run envelopes remain stable.
- **SC-003**: Search evidence remains traceable to local artifacts.

## Assumptions

- Cache is derived data and can be rebuilt manually.
- MCP clients are external callers over stdio.
- Historical eval reports remain audit records.
