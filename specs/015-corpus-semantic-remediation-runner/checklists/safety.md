# Safety Checklist: Corpus Semantic Remediation Runner

**Purpose**: Validate requirement-level LLM, zero-write, no-leak, and integration boundaries before implementation
**Created**: 2026-07-12
**Feature**: [spec.md](../spec.md)

## Selector and Confirmation Boundaries

- [x] CHK001 Is one explicit canonical episode reference required and is `latest` expressly rejected? [Clarity, Spec FR-001/FR-002]
- [x] CHK002 Are dry-run action values and the stricter confirmed-action rule stated separately? [Clarity, Spec FR-003]
- [x] CHK003 Is action drift defined as rejection without fallback execution? [Edge Case, Spec FR-010/FR-011]
- [x] CHK004 Are force overwrite, partial transcript, chaining, retry, batch, and scheduling exclusions explicit? [Boundary, Spec FR-013/FR-024]

## Strict Zero-File Preview

- [x] CHK005 Does dry-run require zero created, modified, or deleted files across index, plan, semantic, review, report, cache, and `.part` artifacts? [Completeness, Spec FR-005/SC-001]
- [x] CHK006 Does preview require exactly one fresh in-memory 008 snapshot and one 009 snapshot derived from it? [Measurability, Spec FR-004]
- [x] CHK007 Must the requested episode be isolated before state classification so other episodes cannot contaminate the decision? [Edge Case, Spec FR-004/SC-002]
- [x] CHK008 Are dry-run provider, environment-loader, persister, executor, writer, and progress-callback prohibitions explicit? [Coverage, Spec FR-005/SC-001]
- [x] CHK009 Is bounded semantic-summary readability inspection distinguished from reading or returning the summary body? [Clarity, Spec Safety and Data Boundaries]

## Semantic Summary LLM Boundary

- [x] CHK010 Is the exact acknowledgement required only for confirmed `semantic_summary`? [Clarity, Spec FR-012/FR-014]
- [x] CHK011 Must acknowledgement validation precede profile, `.env`, credential, provider construction, and any file write? [Ordering, Spec FR-012/SC-004]
- [x] CHK012 Is the allowed semantic configuration subset limited to provider, model, endpoint, credential-variable name, and chunking options? [Boundary, Spec FR-012/FR-022]
- [x] CHK013 Is transcript transfer and possible API cost described before confirmation? [Completeness, Spec US2/Safety]
- [x] CHK014 Are missing or invalid acknowledgement outcomes specified as zero-write and non-zero CLI exits? [Measurability, Spec FR-023/SC-004]

## Deterministic Review Boundary

- [x] CHK015 Is semantic review explicitly deterministic and prohibited from profile, `.env`, credential, provider, and LLM access? [Boundary, Spec FR-014/SC-005]
- [x] CHK016 Is exact missing review the only actionable review state, exact passed the only completed state, and every other present/default/unknown state terminal manual-only? [Edge Case, Spec FR-009]
- [x] CHK017 Is the existing timestamped review artifact contract retained, including bounded handling of partial pair-write failure? [Compatibility, Spec FR-019/Edge Cases]

## Fail-Closed and No-Leak Requirements

- [x] CHK018 Is the complete transcript/summary/review state table specified, including unreadable and corrupt states? [Completeness, Spec FR-006-FR-009]
- [x] CHK019 Are runner-owned failures restricted to safe exception categories without traceback or raw exception bodies? [Clarity, Spec FR-018]
- [x] CHK020 Are transcript, evidence, summary, prompt, provider response, endpoint, query, fragment, secret, and traceback bodies excluded from JSON, Markdown, stdout, and stderr? [Coverage, Spec FR-017/SC-006]
- [x] CHK021 Are safe path handling and CJK-compatible local path requirements defined without permitting URLs, traversal, UNC, or control characters? [Edge Case, Spec Edge Cases]
- [x] CHK022 Is prohibited investment-advice language excluded from all runner-owned outputs? [Boundary, Spec FR-024/SC-006]

## Integration, Reports, and Governance

- [x] CHK023 Are confirmed-only latest report fields and the absence of `generated_at` specified? [Completeness, Spec FR-015/FR-016/FR-019]
- [x] CHK024 Is automatic 008/009 refresh and SQLite cache rebuild excluded, with a manual stale-metadata warning required? [Boundary, Spec FR-020]
- [x] CHK025 Are 010, 014, MCP registration/envelopes, live market data, stock-lens continuation, and automatic review explicitly out of scope? [Compatibility, Spec FR-021/FR-024]
- [x] CHK026 Do success criteria require exact-one executor behavior, exact 12 MCP tools, provider-factory guards, cache guards, and adversarial no-leak coverage? [Measurability, Spec SC-003/SC-007]