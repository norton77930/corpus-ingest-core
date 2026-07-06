# Feature Specification: Research Workflow Orchestration

**Feature Branch**: `005-research-workflow-orchestration`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for `run_research_workflow`, workflow
CLI, MCP workflow exposure, optional semantic summary, optional stock lens
synthesis, optional fixture verification, and cache stale warnings.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed Phase 7C constitution, no amendment.
- `$speckit-specify`: this file records as-built workflow requirements.
- `$speckit-clarify`: no high-impact ambiguity; existing code/tests are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked consistency across spec, plan, and tasks.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers current workflow orchestration scope.

## User Scenarios & Testing

### User Story 1 - Plan research workflow dry-run (Priority: P1)

Users can request a dry-run plan that lists step order, planned reads/writes,
external API risk, fixture risk, and cache stale warning without writing files.

**Independent Test**: `test_research_workflow.py`.

### User Story 2 - Confirm deterministic workflow (Priority: P2)

Users can confirm workflow execution to produce mentions, episode intelligence,
industry mapping, external boundary, optional fixture verification, and stock
lens report.

**Independent Test**: `test_research_workflow.py`.

### User Story 3 - Expose workflow through MCP (Priority: P3)

MCP clients can invoke the consolidated workflow tool with dry-run first
behavior and exact acknowledgement guard for LLM steps.

**Independent Test**: `test_mcp_server.py`.

## Functional Requirements

- **FR-001**: Workflow MUST default to dry-run and write no artifacts.
- **FR-002**: Confirmed deterministic workflow MUST execute configured local steps in order.
- **FR-003**: Optional semantic summary MUST run only when requested and acknowledged.
- **FR-004**: Optional stock lens synthesis MUST require stock query and exact `api_cost_ack`.
- **FR-005**: Optional external verification MUST use local fixture provider only.
- **FR-006**: Workflow MUST warn about manual cache rebuild after side effects.
- **FR-007**: MCP workflow exposure MUST preserve response envelopes and secret boundary.
- **FR-008**: Phase 6V workflow pass-through MAY enable reviewed semantic context for stock lens synthesis, but default workflow synthesis MUST remain 6F JSON-only and MCP exposure remains unchanged.

## Safety and Data Boundaries

- dry-run is the default.
- LLM steps require exact `api_cost_ack`.
- `.env` and API key values must not be exposed.
- External verification is local fixture only and no live market API.
- Stock lens synthesis input remains `phase-6f-stock-lens-json-only` by default. Phase 6V opt-in may pass reviewed semantic context with `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`, no raw transcript, no live market API, and no MCP tool changes.
- no investment advice.

## Success Criteria

- **SC-001**: Workflow and MCP tests pass.
- **SC-002**: Dry-run calls do not write artifacts or call providers.
- **SC-003**: Confirmed LLM paths fail before writes when acknowledgement is missing.

## Assumptions

- Workflow steps are not transactional; upstream deterministic artifacts may exist if a later optional step fails.
- Cache rebuild remains manual.
