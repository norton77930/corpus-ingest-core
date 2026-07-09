# Safety Checklist: Corpus Local Transcription Runner

**Purpose**: Validate requirements quality for local transcription side-effect boundaries before implementation
**Created**: 2026-07-09
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests whether requirements are complete, clear, and consistent. It does not verify implementation behavior.

## Requirement Completeness

- [x] CHK001 Are dry-run no-write requirements defined for transcript outputs, run report artifacts, and downstream corpus artifacts? [Completeness, Spec §Safety and Data Boundaries]
- [x] CHK002 Are confirmed execution requirements limited to exactly one requested episode? [Completeness, Spec §FR-007]
- [x] CHK003 Are eligible local transcription selection criteria fully specified as audio available, audio path exists, transcript action ready, and transcript status missing? [Completeness, Spec §FR-005]
- [x] CHK004 Are skipped unsafe transcript states explicitly listed, including unreadable, corrupt, partial, incomplete, valid existing, and empty existing transcript outputs? [Completeness, Spec §FR-006]
- [x] CHK005 Are output artifact paths specified only for confirmed run reports and not dry-run reports? [Completeness, Spec §FR-011]

## Requirement Clarity

- [x] CHK006 Is "local audio" defined through metadata and an existing local path rather than remote feed availability? [Clarity, Spec §FR-005]
- [x] CHK007 Is "transcript fully missing" defined separately from corrupt, partial, incomplete, valid, or empty transcript states? [Clarity, Spec §FR-005, Spec §FR-006]
- [x] CHK008 Is the behavior for confirmed execution without an episode reference unambiguous and pre-transcription? [Clarity, Spec §FR-007]
- [x] CHK009 Is the behavior for a confirmed but non-eligible episode defined as no transcription with a rejected or skipped outcome? [Clarity, Spec §US2]
- [x] CHK010 Are planned reads, planned writes, output paths, and outcome counts defined as metadata-only fields? [Clarity, Spec §FR-014]

## Requirement Consistency

- [x] CHK011 Do the spec and plan consistently exclude download, RSS, network, LLM, `.env`, MCP, stock-lens, downstream remediation, and cache rebuild behavior? [Consistency, Spec §Safety and Data Boundaries, Plan §Technical Context]
- [x] CHK012 Do the dry-run requirements align with the constitution's dry-run first side-effect rule? [Consistency, Constitution III]
- [x] CHK013 Do the confirmed-run report requirements align with the latest-state artifact path contract? [Consistency, Spec §FR-011, Contract §Storage Helper]
- [x] CHK014 Do CLI and core contracts expose the same selection controls and runtime options? [Consistency, Contract §Core Function, Contract §CLI]

## Scenario Coverage

- [x] CHK015 Are primary preview, confirmed execution, and failure containment scenarios all covered by user stories? [Coverage, Spec §User Scenarios]
- [x] CHK016 Are empty corpus, missing audio, unsafe transcript state, missing episode reference, non-eligible episode, missing local audio path, repeated dry-run, and repeated confirmed run edge cases addressed? [Coverage, Spec §Edge Cases]
- [x] CHK017 Are failure scenarios defined without requiring traceback or secret exposure? [Coverage, Spec §US3]
- [x] CHK018 Are cache staleness and manual rebuild requirements represented without allowing automatic cache rebuild? [Coverage, Spec §US3, Spec §FR-020]

## Acceptance Criteria Quality

- [x] CHK019 Are measurable outcomes defined for empty corpus, mixed eligible/ineligible states, missing episode rejection, eligible execution, failure recording, no-leak output, MCP stability, and no timestamp? [Measurability, Spec §Success Criteria]
- [x] CHK020 Can each success criterion be objectively evaluated without implementation-specific hidden assumptions? [Measurability, Spec §Success Criteria]

## Boundary and Assumption Coverage

- [x] CHK021 Are dependencies on 009 remediation plan and existing local audio artifacts documented? [Assumption, Spec §Assumptions]
- [x] CHK022 Are future exclusions for download automation, transcript repair, semantic/LLM automation, MCP exposure, and batch transcription documented as out of scope? [Gap, Spec §Assumptions]
- [x] CHK023 Are no-investment-advice and external-status-not-market-fact requirements explicitly retained even though the feature is transcription-focused? [Completeness, Spec §Safety and Data Boundaries]
