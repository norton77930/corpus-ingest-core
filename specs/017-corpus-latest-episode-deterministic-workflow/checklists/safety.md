# Safety Requirements Checklist: Latest Episode Deterministic Workflow

**Purpose**: Review requirement quality for deterministic automation, safety
boundaries, and Agent-facing contracts before implementation.

**Created**: 2026-07-16

**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [x] CHK001 Are input requirements explicit that only configured podcast IDs,
  rather than arbitrary URLs or selectors, are accepted? [Completeness, Spec §FR-001]
- [x] CHK002 Are dry-run and confirmed-write boundaries defined for every
  externally visible surface? [Completeness, Spec §FR-002, §FR-008, §FR-009]
- [x] CHK003 Are the four deterministic stages and the semantic-summary stop
  boundary both explicitly specified? [Completeness, Spec §FR-004, §FR-006]
- [x] CHK004 Are resume and already-ready no-op requirements defined without
  implying an automatic retry? [Completeness, Spec §FR-005, Assumptions]

## Requirement Clarity and Consistency

- [x] CHK005 Is "latest" unambiguously defined as one canonical snapshot per
  invocation, including the RSS-update case? [Clarity, Spec §FR-003]
- [x] CHK006 Are the failure, blocked, rejected, and later-action prohibition
  requirements mutually consistent? [Consistency, Spec §FR-007]
- [x] CHK007 Is the Agent Skill's one acknowledgement, one tool call, and one
  final report requirement consistent with the MCP dry-run default? [Consistency, Spec §FR-009, §FR-010]
- [x] CHK008 Is the requirement to preserve 016's one-action contract explicit
  enough to prevent implementation by widening 016? [Clarity, Spec §FR-013]

## Safety and Exception Coverage

- [x] CHK009 Are unresolvable selector, unsafe artifact, unavailable audio,
  invalid transcript, and remediation-action failure outcomes all addressed?
  [Coverage, Spec Edge Cases, §FR-007]
- [x] CHK010 Are no-retry, no-force, no-partial, no-batch, no-scheduler, and
  no-terminal-fallback exclusions all documented? [Coverage, Spec §FR-011]
- [x] CHK011 Are secret, raw transcript, provider, LLM, semantic-review, market,
  cache-rebuild, and investment-advice exclusions complete? [Coverage, Safety and Data Boundaries]

## Measurability and Traceability

- [x] CHK012 Can each success criterion be verified from an independent test or
  an Agent-facing contract outcome? [Measurability, Spec §SC-001–§SC-005]
- [x] CHK013 Does the fourteen-tool registry requirement identify compatibility
  expectations for all pre-existing tools? [Traceability, Spec §FR-012]
- [x] CHK014 Are report contents constrained to safe metadata, safe references,
  and failure categories rather than diagnostic/source bodies? [Clarity, Spec §FR-008]

## Notes

- Intended depth: formal reviewer gate for a local side-effect workflow.
- Audience: feature author and reviewer before implementation and release.
