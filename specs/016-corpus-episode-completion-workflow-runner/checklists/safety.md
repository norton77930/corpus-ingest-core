# Safety Requirements Checklist: Corpus Episode Completion Workflow Runner

**Purpose**: Review whether the written 016 requirements completely and
unambiguously define human control, side-effect, LLM, secret, MCP, and
compatibility boundaries before implementation
**Created**: 2026-07-13
**Feature**: [spec.md](../spec.md)

## Human-Control Requirement Completeness

- [x] CHK001 Are preview, explanation, explicit approval, exact confirmation, report, and stop requirements all defined in order? [Completeness, Spec FR-020]
- [x] CHK002 Is the treatment of missing, ambiguous, conditional, and negative approval explicitly defined? [Clarity, Spec FR-021]
- [x] CHK003 Are confirmed `next` and confirmed `latest` rejection requirements explicit and measurable? [Clarity, Spec FR-007 to FR-008]
- [x] CHK004 Does the spec define action-drift rejection without fallback to the newly selected action? [Exception Flow, Spec FR-009]
- [x] CHK005 Is "one action" bounded as one matching runner invocation, with deterministic remediation limited to one row? [Clarity, Spec FR-010]
- [x] CHK006 Are terminal completed/blocked states and MCP-unavailable behavior defined to stop without alternate execution? [Coverage, Spec FR-011 and FR-021]

## Zero-File and Artifact Boundary

- [x] CHK007 Is strict zero-file defined to include creation, modification, and deletion across all artifacts and `.part` files? [Completeness, Spec FR-005 and SC-002]
- [x] CHK008 Are all forbidden dry-run calls - stage executor, provider, environment loader, writer, and progress callback - enumerated? [Coverage, Spec FR-005]
- [x] CHK009 Is fresh in-memory snapshot reuse defined without treating persisted index/plan/report sentinels as stage truth? [Consistency, Spec FR-004 to FR-006]
- [x] CHK010 Is confirmed 010-012 pre-execution 008/009 refresh distinguished from prohibited extra/post-stage refresh and cache rebuild? [Clarity, Spec FR-022]
- [x] CHK011 Are confirmed report ownership, atomic per-file replacement, pair non-transactionality, and no compensation after failure documented? [Recovery, Spec FR-015 to FR-016]

## LLM Consent and Secret Boundary

- [x] CHK012 Does the spec require exact semantic-summary acknowledgement before every feed, snapshot, profile, environment, credential, provider, executor, progress, and writer surface? [Completeness, Spec FR-012 and SC-005]
- [x] CHK013 Is semantic summary the only action permitted to transfer transcript text or incur provider cost? [Consistency, Spec Safety and Data Boundaries]
- [x] CHK014 Is deterministic semantic review explicitly isolated from all LLM profile, environment, credential, endpoint, provider, and acknowledgement options? [Coverage, Spec FR-013]
- [x] CHK015 Are provider/model identifiers distinguished from excluded endpoint/base-URL and credential data in outputs? [Clarity, Spec FR-019 and FR-023]
- [x] CHK016 Are `.env`, API key, token, provider secret, URL, raw body, raw exception, and traceback disclosure requirements explicit for every report/interface surface? [Completeness, Spec FR-023]
- [x] CHK017 Is category-only fail-closed behavior defined for selector, snapshot, stage, and report failures without raw dependency text? [Exception Flow, Spec FR-014 to FR-016]

## MCP and Skill Contract Quality

- [x] CHK018 Is the exact thirteenth MCP tool name and exact 13-tool registry requirement stated while preserving the first twelve contracts? [Traceability, Spec FR-018]
- [x] CHK019 Are dry-run, successful structured outcome, and safe error envelope requirements distinguished? [Completeness, Spec FR-019]
- [x] CHK020 Is the MCP request surface bounded to non-secret options and explicitly free of callback, profile path, env-file path, force, partial, retry, or loop controls? [Coverage, Spec FR-019 and FR-022]
- [x] CHK021 Is the Skill defined as conversational guidance while Core remains the hard enforcement boundary? [Consistency, Spec US3 and FR-020 to FR-021]
- [x] CHK022 Are terminal/CLI/other-tool/scheduler/retry/autonomous fallback prohibitions unambiguous? [Clarity, Spec FR-021]
- [x] CHK023 Is Codex validation required without claiming client-specific Hermes Agent or OpenClaw live compatibility? [Scope, Spec FR-025]

## Cross-Boundary Consistency

- [x] CHK024 Are no live market data, no investment advice, and `not_investment_advice=true` requirements explicit? [Consistency, Spec FR-022 to FR-024]
- [x] CHK025 Are existing 013-015 public APIs, CLIs, reports, and standalone behaviors protected from change? [Dependency, Spec FR-017 to FR-018]
- [x] CHK026 Are invalid transcript and semantic-only handoff precedence defined without weakening public 014 behavior? [Edge Case, Spec FR-003]
- [x] CHK027 Can every success criterion be objectively verified through bounded counts, tree manifests, call ordering, registry membership, no-leak scans, or protocol checks? [Measurability, Spec SC-001 to SC-009]

## Notes

- Standard-depth reviewer checklist focused on the approved safety boundaries.
- Requirements review completed on 2026-07-13: 27/27 items pass.
- This checklist validates requirement quality; implementation verification is
  defined separately in tasks and tests.
