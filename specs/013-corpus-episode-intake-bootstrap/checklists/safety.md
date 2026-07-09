# Safety Checklist: Corpus Episode Intake Bootstrap

**Purpose**: Validate that the requirements define safety boundaries clearly before implementation
**Created**: 2026-07-09
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [x] CHK001 Are dry-run no-write requirements defined for seed metadata, run reports, audio, transcripts, downstream artifacts, cache files, and provider artifacts? [Completeness, Spec FR-004]
- [x] CHK002 Are confirmed write boundaries limited to one seed artifact and latest intake reports? [Completeness, Spec FR-007, FR-008]
- [x] CHK003 Are selector rules for `latest`, explicit episode refs, blank selectors, and batch exclusion documented? [Completeness, Spec FR-002]
- [x] CHK004 Are follow-up operations explicitly left manual after confirmed intake? [Completeness, Spec FR-018]

## Requirement Clarity

- [x] CHK005 Is RSS/network access in dry-run explicitly allowed only for selector resolution? [Clarity, Spec FR-003, Safety Boundaries]
- [x] CHK006 Are seed metadata contents bounded to safe metadata and no raw feed body? [Clarity, Spec FR-005, FR-013]
- [x] CHK007 Are run report count fields defined for selected, seeded, reused, failed, skipped, rejected, and warnings? [Clarity, Spec FR-009]
- [x] CHK008 Is deterministic output defined with no generation timestamp? [Clarity, Spec FR-012]

## Requirement Consistency

- [x] CHK009 Do dry-run RSS allowances avoid contradicting 012 dry-run no-network boundaries by assigning RSS discovery only to 013? [Consistency, Spec Safety Boundaries]
- [x] CHK010 Do 008 local-only requirements remain consistent by making seed metadata the local source after intake? [Consistency, Spec FR-010]
- [x] CHK011 Do 009 and 012 handoff requirements align with seed-derived audio availability without storing full URLs? [Consistency, Spec FR-011]

## Scenario Coverage

- [x] CHK012 Are primary preview scenarios defined for latest and explicit episode refs? [Coverage, User Story 1]
- [x] CHK013 Are confirmed seed and repeated reuse scenarios defined? [Coverage, User Story 2]
- [x] CHK014 Are feed failure and unsafe feed content scenarios defined? [Coverage, User Story 3]
- [x] CHK015 Are edge cases for empty feed, unresolved selector, entries without audio, and repeated confirmed intake addressed? [Coverage, Edge Cases]

## Safety Boundaries

- [x] CHK016 Are full source URLs, audio URLs, query strings, descriptions, prompts, raw LLM output, secrets, and tracebacks excluded from outputs and artifacts? [Safety, Spec FR-013]
- [x] CHK017 Are download, transcription, downstream remediation, semantic work, stock-lens, LLM, `.env`, MCP, and cache rebuild exclusions explicit? [Safety, Spec FR-014]
- [x] CHK018 Is MCP registry preservation required and testable? [Safety, Spec FR-016]
- [x] CHK019 Is no-investment-advice preservation required? [Safety, Spec FR-017]

## Acceptance Criteria Quality

- [x] CHK020 Are success criteria measurable for dry-run no-write, confirmed seed writes, 008 discovery, 009 action planning, 012 selection, no leaks, MCP unchanged, and no timestamp? [Acceptance Criteria, Success Criteria]
- [x] CHK021 Can each user story be tested independently without requiring full downstream automation? [Acceptance Criteria, User Stories]
- [x] CHK022 Are implementation-phase verification expectations represented in quickstart and tasks? [Traceability, quickstart.md, tasks.md]
