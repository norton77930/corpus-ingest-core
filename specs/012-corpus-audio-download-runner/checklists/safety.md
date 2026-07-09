# Safety Checklist: Corpus Audio Download Runner

**Purpose**: Validate requirements quality for audio download side-effect boundaries before implementation
**Created**: 2026-07-09
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests whether requirements are complete, clear, and consistent. It does not verify implementation behavior.

## Requirement Completeness

- [x] CHK001 Are dry-run no-write requirements defined for audio files, run report artifacts, transcript outputs, and downstream corpus artifacts? [Completeness, Spec §Safety and Data Boundaries]
- [x] CHK002 Are dry-run no-RSS, no-network, and no-downloader-call requirements explicitly defined? [Completeness, Spec §FR-004]
- [x] CHK003 Are confirmed execution requirements limited to exactly one non-empty requested episode? [Completeness, Spec §FR-007]
- [x] CHK004 Are eligible audio download selection criteria fully specified as audio action ready and audio status missing? [Completeness, Spec §FR-005]
- [x] CHK005 Are skipped non-audio and unsafe action states explicitly listed, including available audio, blocked audio, non-ready audio, transcript, semantic, downstream, stock-lens, synthesis, and unknown families? [Completeness, Spec §FR-006]
- [x] CHK006 Are output artifact paths specified only for confirmed run reports and not dry-run reports? [Completeness, Spec §FR-011]

## Requirement Clarity

- [x] CHK007 Is "audio missing" defined through refreshed remediation metadata rather than remote feed availability? [Clarity, Spec §FR-005]
- [x] CHK008 Is the behavior for confirmed execution without a non-empty episode reference unambiguous and pre-network? [Clarity, Spec §FR-007]
- [x] CHK009 Is the behavior for a confirmed but non-selected episode defined as no download with a rejected outcome? [Clarity, Spec §FR-008]
- [x] CHK010 Are planned reads, planned writes, output paths, and outcome counts defined as metadata-only fields without source URLs? [Clarity, Spec §FR-014, Spec §FR-015]
- [x] CHK011 Is `downloaded` versus `reused` outcome behavior defined for downloader results? [Clarity, Spec §SC-005]

## Requirement Consistency

- [x] CHK012 Do the spec and plan consistently allow RSS/network only for confirmed single-episode execution through the existing downloader? [Consistency, Spec §Safety and Data Boundaries, Plan §Technical Context]
- [x] CHK013 Do the spec and plan consistently exclude transcription, deterministic downstream remediation, LLM, `.env`, MCP, stock-lens, synthesis, and cache rebuild behavior? [Consistency, Spec §Safety and Data Boundaries, Plan §Technical Context]
- [x] CHK014 Do the dry-run requirements align with the constitution's dry-run first side-effect rule? [Consistency, Constitution III]
- [x] CHK015 Do the source URL omission requirements align across spec, plan, data model, contract, and quickstart? [Consistency, Spec §FR-015, Contract §JSON Report Shape]
- [x] CHK016 Do CLI and core contracts expose the same selection controls? [Consistency, Contract §Core Function, Contract §CLI]

## Scenario Coverage

- [x] CHK017 Are primary preview, confirmed execution, and failure containment scenarios all covered by user stories? [Coverage, Spec §User Scenarios]
- [x] CHK018 Are empty corpus, existing audio, blocked action, missing episode reference, absent episode, non-selected episode, existing file reuse, download failure, repeated dry-run, and repeated confirmed run edge cases addressed? [Coverage, Spec §Edge Cases]
- [x] CHK019 Are failure scenarios defined without requiring traceback, source URL, or secret exposure? [Coverage, Spec §US3]
- [x] CHK020 Are manual follow-up boundaries represented without allowing automatic transcription, downstream remediation, or cache rebuild? [Coverage, Spec §FR-020]

## Acceptance Criteria Quality

- [x] CHK021 Are measurable outcomes defined for empty corpus, mixed eligible/ineligible states, missing episode rejection, eligible execution, reuse, failure recording, no-leak output, MCP stability, and no timestamp? [Measurability, Spec §Success Criteria]
- [x] CHK022 Can each success criterion be objectively evaluated without implementation-specific hidden assumptions? [Measurability, Spec §Success Criteria]

## Boundary and Assumption Coverage

- [x] CHK023 Are dependencies on 009 remediation plan and existing downloader behavior documented? [Assumption, Spec §Assumptions]
- [x] CHK024 Are future exclusions for batch download, retry/rate-limit policy, transcription, downstream remediation, MCP exposure, and automatic cache rebuild documented as out of scope? [Gap, Spec §Assumptions]
- [x] CHK025 Are no-investment-advice and external-status-not-market-fact requirements explicitly retained even though the feature is audio-focused? [Completeness, Spec §Safety and Data Boundaries]
