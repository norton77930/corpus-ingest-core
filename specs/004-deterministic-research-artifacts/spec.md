# Feature Specification: Deterministic Research Artifacts

**Feature Branch**: `004-deterministic-research-artifacts`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for episode intelligence, industry
chain mapping, external data boundary, local fixture verification, Gooaye Lens,
and deterministic stock lens reports.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed Phase 7C constitution, no amendment.
- `$speckit-specify`: this file records as-built deterministic research requirements.
- `$speckit-clarify`: no high-impact ambiguity; code, tests, and docs are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked consistency across spec, plan, and tasks.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers the current deterministic research scope.

## User Scenarios & Testing

### User Story 1 - Generate episode intelligence (Priority: P1)

Users can create one-episode research reports from validated transcripts and
mention artifacts.

**Independent Test**: `test_episode_intelligence.py`.

### User Story 2 - Map industry chains and external boundaries (Priority: P2)

Users can create industry mapping and external boundary artifacts that preserve
podcast evidence, inference, and external status separation.

**Independent Test**: `test_industry_mapping.py`,
`test_external_data_boundary.py`, and `test_external_data_verification.py`.

### User Story 3 - Build Gooaye Lens and stock lens reports (Priority: P3)

Users can load the Gooaye Lens model and generate deterministic stock lens
reports from local artifacts.

**Independent Test**: `test_gooaye_lens.py` and `test_stock_lens_report.py`.

## Functional Requirements

- **FR-001**: System MUST generate episode intelligence JSON and Markdown from existing local transcript and mention artifacts.
- **FR-002**: System MUST generate industry mapping artifacts from episode intelligence and local mapping config.
- **FR-003**: System MUST distinguish `podcast_explicit`, `inferred_from_industry`, and `needs_verification`.
- **FR-004**: System MUST generate external boundary artifacts with `not_requested`, `not_fetched`, and `data_date=null` until verification exists.
- **FR-005**: System MUST support local fixture verification without live provider calls.
- **FR-006**: System MUST load the Gooaye Lens model from local config.
- **FR-007**: System MUST generate deterministic stock lens reports from local mapping and external artifacts.
- **FR-008**: System MUST reject invalid or partial inputs unless the relevant allow-partial option is used.

## Safety and Data Boundaries

- This package is deterministic and does not call LLM providers.
- Fixture verification is local fixture only and no live market API.
- External status remains status, not market fact.
- Stock lens reports preserve evidence separation and no investment advice.
- `.env` and API keys are not required.

## Success Criteria

- **SC-001**: Existing deterministic research artifact tests pass.
- **SC-002**: All generated artifacts preserve warnings and source status.
- **SC-003**: Inferred candidates never become podcast evidence without explicit local evidence.

## Assumptions

- Historical artifacts are not rewritten unless force flags are used.
- Local config files define deterministic mappings and lens dimensions.
- Missing fixture data creates warnings, not fabricated facts.
