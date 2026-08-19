# Requirements Checklist: Multi-Document Study Guide

One box per FR in `spec.md`. Unchecked until the matching test is green.

## Taxonomy

- [x] FR-001 Exactly four documents: `00`, `03`, `04`, `07`
- [x] FR-002 `01`/`02`/`05`/`06` are not produced or indexed
- [x] FR-003 `05`/`06` workflow content does not appear as lecture evidence

## Source and profile

- [x] FR-004 `summary_profile == learning-notes` required
- [x] FR-005 Missing/unreadable/finance-shaped semantic summary refuses; no 015 chain
- [x] FR-006 Transcript is not sent to a provider (identity helper still reads transcript JSON)
- [x] FR-007 Semantic review `passed` is not required

## Cover

- [x] FR-008 `00` is deterministic from seed + audio metadata
- [x] FR-009 `00` does not network, remux, or invent stream fields

## Generated lecture files

- [x] FR-010 `03` section set
- [x] FR-011 `04` per-concept set
- [x] FR-012 `07` section set + uncertainty-preserving prompt section
- [x] FR-013 Timestamps already in the source; no external corrections

## Family, paths, index

- [x] FR-014 Paths from `storage`; canonical transcript title
- [x] FR-015 One family `study_guide`; available only when all four are readable
- [x] FR-016 Atomic four-file replace

## Workflow contract

- [x] FR-017 Truthful dry-run, zero writes, zero provider
- [x] FR-018 Exact ack first on confirmed generation; protocol unchanged
- [x] FR-019 Metadata-only CLI
- [x] FR-020 No cache rebuild
- [x] FR-021 No MCP tool, no new dependency, envelope frozen
- [x] FR-022 Other podcasts unchanged (per-podcast paths; no byte-stash of gooaye)

---

# Specification Quality Checklist: Multi-Document Study Guide

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Taxonomy, transcript-to-LLM refusal, one-family bundle, and no review-passed gate were locked with the operator before specify. Remaining plan-level seams (module names, exact path helper names) belong in `plan.md`, not here.
- "No implementation details" is satisfied at the user-story layer. Clarifications name existing repo contracts (`learning-notes`, exact `api_cost_ack`, registry size 22) because those are safety boundaries, matching Specs 036 and 037.
