# Safety Checklist: Corpus Fresh Episode Workflow Runner

**Purpose**: Validate requirement-level safety boundaries before implementation
**Created**: 2026-07-10
**Feature**: [spec.md](../spec.md)

## Dry-run and Confirmation

- [x] CHK001 Are dry-run no-write requirements explicit for workflow reports and stage artifacts? [Completeness, Spec FR-004]
- [x] CHK002 Is confirmed execution limited to one `next` stage per run? [Clarity, Spec FR-003/FR-014]
- [x] CHK003 Are unsupported stage values explicitly rejected? [Edge Case, Spec FR-003]

## Stage Boundaries

- [x] CHK004 Is the next-stage ordering documented and testable? [Completeness, Spec FR-005]
- [x] CHK005 Are selected-stage-only dispatch requirements defined for intake, audio download, transcription, and deterministic remediation? [Coverage, Spec FR-006-FR-009]
- [x] CHK006 Are pass-through options constrained to the relevant stage only? [Clarity, Spec FR-010/FR-011]
- [x] CHK007 Is full-chain automation explicitly out of scope? [Boundary, Spec FR-016]

## Data and Leakage

- [x] CHK008 Are unsafe output exclusions specified for JSON, Markdown, stdout, and stderr? [Completeness, Spec FR-017]
- [x] CHK009 Are raw transcript, evidence, semantic body, prompt, and raw LLM output excluded? [Coverage, Spec Safety]
- [x] CHK010 Are URL, query string, secret, and traceback leakage boundaries explicit? [Coverage, Spec SC-007]
- [x] CHK011 Is no-investment-advice language preserved? [Consistency, Spec Safety]

## Excluded Systems

- [x] CHK012 Are semantic/LLM actions manual-only and non-executable in this runner? [Boundary, Spec FR-016]
- [x] CHK013 Is MCP registry immutability explicit? [Boundary, Spec FR-015]
- [x] CHK014 Is automatic SQLite cache rebuild excluded? [Boundary, Spec FR-016]
- [x] CHK015 Is stock-lens and synthesis execution excluded? [Boundary, Spec FR-016]
- [x] CHK016 Is batch latest-N processing excluded? [Boundary, Spec FR-016]

## Auditability

- [x] CHK017 Are confirmed workflow report write rules deterministic and timestamp-free? [Measurability, Spec FR-012/SC-009]
- [x] CHK018 Are report contents specified as metadata, counts, paths, outcomes, and warnings only? [Completeness, Spec FR-013]
- [x] CHK019 Are failure outcomes bounded without continuing to additional stages? [Edge Case, Spec Edge Cases]
- [x] CHK020 Are manual follow-up warnings required for non-executable actions? [Coverage, Spec US3]