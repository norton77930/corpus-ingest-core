# Artifact Index Checklist: Corpus Artifact Index

**Purpose**: Validate corpus artifact index requirements quality before implementation planning handoff
**Created**: 2026-07-08
**Feature**: [spec.md](../spec.md)

**Note**: This checklist validates the requirements writing, not runtime behavior.

## Requirement Completeness

- [x] CHK001 Are supported per-episode artifact families explicitly listed? [Completeness, Spec FR-002]
- [x] CHK002 Are query-level stock-lens and synthesis artifacts explicitly excluded from v1? [Completeness, Spec Edge Cases]
- [x] CHK003 Are JSON and Markdown output requirements both specified? [Completeness, Spec FR-003]
- [x] CHK004 Are empty corpus, missing artifact, unreadable JSON, duplicate candidate, and partial transcript scenarios covered? [Coverage, Spec Edge Cases]

## Requirement Clarity

- [x] CHK005 Is "local artifacts only" defined clearly enough to exclude RSS, network, SQLite cache, and MCP tool inputs? [Clarity, Spec FR-002]
- [x] CHK006 Is deterministic regeneration clarified with no timestamp and no stale reuse? [Clarity, Spec FR-004/FR-005]
- [x] CHK007 Are stable artifact family names required for `missing_artifacts`? [Clarity, Spec FR-016]
- [x] CHK008 Is latest semantic review selection described with a deterministic rule? [Clarity, Spec User Story 3]

## Requirement Consistency

- [x] CHK009 Are the spec, plan, data model, and contract consistent that v1 has no MCP tool change? [Consistency, Spec FR-019]
- [x] CHK010 Are data-model entities aligned with Functional Requirements and Success Criteria? [Consistency, Spec Key Entities]
- [x] CHK011 Are Markdown and JSON safety boundaries consistent across spec and contract artifacts? [Consistency, Spec Safety and Data Boundaries]

## Acceptance Criteria Quality

- [x] CHK012 Are success criteria measurable without depending on implementation internals? [Measurability, Spec SC-001..SC-007]
- [x] CHK013 Are acceptance scenarios independently testable by user story? [Acceptance Criteria, Spec User Scenarios]
- [x] CHK014 Does the spec define how malformed artifacts affect only their own artifact family? [Exception Flow, Spec FR-015]

## Safety Boundaries

- [x] CHK015 Are raw transcript, evidence snippet, semantic summary body, prompt text, raw LLM output, and secret output exclusions explicit? [Safety, Spec Safety and Data Boundaries]
- [x] CHK016 Are no LLM call, no `.env` read, no live market API, no SQLite cache dependency, and no investment advice boundaries documented? [Safety, Spec Safety and Data Boundaries]
- [x] CHK017 Are external boundary status values kept as metadata instead of market facts? [Safety, Spec Safety and Data Boundaries]

## Notes

- Checklist generation corresponds to `$speckit-checklist` for this feature.
