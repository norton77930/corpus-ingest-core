# Feature Specification: Spec Kit Governance

**Feature Branch**: `007-spec-kit-governance`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for architecture stabilization,
official Spec Kit bootstrap, project constitution, templates, AGENTS workflow
alignment, and capability-group backfill docs.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed and established Phase 7C constitution.
- `$speckit-specify`: this file records as-built governance requirements.
- `$speckit-clarify`: no high-impact ambiguity; current docs/tests are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked consistency across spec, plan, and tasks.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers current Spec Kit governance scope.

## User Scenarios & Testing

### User Story 1 - Govern future work through Spec Kit (Priority: P1)

Maintainers can use constitution and templates to keep future work aligned with
project safety rules.

**Independent Test**: `test_spec_kit_constitution.py`.

### User Story 2 - Verify scaffold and docs alignment (Priority: P2)

Maintainers can verify `.specify`, `.agents/skills`, AGENTS, architecture, and
roadmap docs remain aligned.

**Independent Test**: `test_spec_kit_bootstrap.py` and
`test_architecture_spec_docs.py`.

### User Story 3 - Track existing capabilities (Priority: P3)

Maintainers can find implemented capability specs through the registry.

**Independent Test**: `test_spec_kit_backfill_docs.py`.

## Functional Requirements

- **FR-001**: Project MUST include official Spec Kit scaffold and Codex skills.
- **FR-002**: Project MUST include a project-specific constitution.
- **FR-003**: Templates MUST include project gates for dry-run, LLM ack, secret boundary, external status, no live market API, no investment advice, and manual cache rebuild.
- **FR-004**: AGENTS MUST describe the full Spec Kit flow.
- **FR-005**: Existing capabilities MUST be discoverable through `specs/README.md`.

## Safety and Data Boundaries

- Governance docs do not call LLM providers.
- Governance docs do not read `.env`.
- no live market API and no investment advice remain constitution gates.

## Success Criteria

- **SC-001**: Spec Kit bootstrap, constitution, architecture docs, and backfill docs tests pass.
- **SC-002**: Future work can start from full Spec Kit flow instead of ad hoc phase plans.

## Assumptions

- Git metadata remains unreliable in this workspace, so governance does not depend on branch or commit workflows.
