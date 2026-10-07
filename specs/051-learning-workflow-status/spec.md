# Feature Specification: Learning workflow status overview

**Feature Branch**: None (user prohibits branch creation)
**Created**: 2026-10-04
**Status**: Implemented
**Input**: User requested planning and immediate implementation of the next phase after SPEC050. Scope is a single-episode read-only overview over existing learning queries.

## User Scenarios & Testing
### US1 - View progress and provenance together (P1)
As a learning operator I want one compact view of the next learning step, lecture provenance, derivation provenance and recovery state.
Why: the current four separate queries are useful but require manual reconciliation. Independent test: owned temporary fixtures or closed child-query fixtures.
1. Given clear recovery and four successful observations, then one overview preserves each scoped status without calling a generator in confirm mode.
2. Given legacy/untracked or custom-context provenance, then attention is explicit; file presence is not promoted to verified source freshness.
3. Given stale lecture/derivation observations, then changed roles and deterministic attention reasons are reported without automatic regeneration.

### US2 - Respect recovery and unknown observations (P1)
As an operator I want unsafe recovery or failed observations to remain visible and stop unsafe follow-up work.
Independent test: call-order tripwires, injected malformed/exception child responses and fixture snapshots.
1. Given recovery is not clear, then recovery is queried once and the other three sections are not_evaluated/recovery_gate, with no further reads through their queries.
2. Given a child exception/foreign identity/malformed metadata, then a finite blocked section inspection_unavailable appears without private text.
3. Given progress and lineage disagree about output presence, then observations_conflict requires attention; no claim of atomic consistency.

### US3 - Query through existing MCP (P2)
As a client I want an appended Tool31 with the same safe envelope and explicit identity requirements.
Independent test: thin delegation, signature/schema, first30 order/signature snapshot and current docs/setup guards.
1. Given explicit IDs, then Core is called once and only closed metadata is returned.
2. Given invalid IDs, then fixed ValueError before child queries; unexpected MCP failure has fixed InternalError.

### Edge Cases
Missing/ambiguous/malformed canonical identity follows Tool30 blocked state. Four observations are sequential, not atomic. Recovery gate skips next-step/lineages entirely. Remaining queries are each attempted once even if one fails; no retries. Untracked/custom-context observations demand attention but remain distinct from blocked inspection. not_generated is ordinary pending work unless it conflicts with an observed reuse mode. Unknown child fields/warnings/paths/suggested_call are never forwarded.

### Safety and Data Boundaries
Read-only, offline, zero provider/environment/reports/cache writes. No execution authorization, confirm/force/ack/provider/context/path input, raw bodies, hashes, arbitrary filenames, suggested_call, repair commands or winner selection. Tools1-30, generators, codecs, secure readers and Skills unchanged. No advice/live market API, new dependency, CLI/UI/batch/scheduler or recovery executor. No Git branch/worktree/commit/staging/deployment. Existing dirty044-050 changes retained.

## Requirements
- FR-001: Add Core inspect_learning_workflow_status(podcast_id,episode_ref), append Tool31 with exactly two required explicit IDs; reject invalid/padded/path/latest/next IDs before any child query.
- FR-002: Query recovery first, at most once; only clear/no_recovery_entries continues to existing next-step, lecture lineage and derivation lineage, each once and sequentially. Other recovery outcomes skip all three using explicit not_evaluated/recovery_gate shapes.
- FR-003: Return a closed compact overview with recovery, next_step, study_guide_lineage, workflow_derivation_lineage sections. Whitelist known states/reasons/output/input role labels and validate returned identity/read-only/scope/network metadata. Never forward child suggested_call, unknown fields, warnings, paths, content or fingerprints.
- FR-004: Child exceptions or malformed/inconsistent/foreign metadata produce finite blocked/inspection_unavailable section outcomes. Remaining clear-gated children are still attempted once. Top blocked outranks attention_required, which outranks observed; attention_required boolean is true for blocked or advisory conditions.
- FR-005: Ordered attention reasons reflect recovery gate, next-step blocker, each lineage blocked/stale/untracked/custom-context and observations_conflict. Pending not_generated alone is not an anomaly; reuse mode versus not_generated or generation mode versus existing lineage is a non-atomic conflict. Overview never claims end-to-end readiness or freshness.
- FR-006: Always return scope learning_workflow_status, read_only=true, network_access=false; fixed warnings non_atomic_observation, summary_transcript_freshness_not_evaluated, no_execution_authorization, publication_outcome_not_proven. Existing child queries retain their own bounds. At most four child query calls, no recursion/retry or global listing.
- FR-007: Zero writes/network/provider/environment/report/cache actions; no execution authorization or automatic repair/deletion/regeneration. No new side-effect or caller path surface. Preserve existing thirty tool contracts and all044-050 generation/query/codec/Skill/secure-reader files byte-for-byte.
- FR-008: Thin MCP wrapper delegates once and maps errors to fixed existing envelopes; registry/facade/setup/docs/count guards updated to31, first30 order/signatures preserved.
- FR-009: Follow full Spec Kit/TDD, targeted/full pytest, compileall/diff, separate fresh-context read-only behavior/engineering reviews and converge. Root sole writer; no Git objects or actual provider/corpus/cache actions.

## Key Entities
Overview = explicit episode identity + four scoped observations + deterministic attention summary. Each observation is in-memory metadata, never persisted. Exact shapes/state tables in data-model.md/contracts/status.md.

## Success Criteria
- SC-001: One query shows four independent scopes and preserves legacy/custom/stale/pending distinctions for a single episode.
- SC-002: Recovery refusal and malformed observations never cause follow-up execution, private-data leakage or a successful-readiness claim; calls are bounded to four.
- SC-003: Appended Tool31 and current client docs agree while all first30 signatures/order remain unchanged.
- SC-004: Requirements have task/test evidence, independent reviews closed, full checks current and converge adds no remaining unbuilt work.

## Assumptions and Clarifications
2026-10-04: user authorized next-phase plan+implementation; choose operational overview of existing read-only learning tools. Alternatives: destructive recovery executor needs separate explicit scope; learning search/index would add a new subsystem; a CLI-only overview would not serve existing MCP clients. No material safety expansion. Zero clarification questions: reuse local contracts for identity/unknowns/privacy. The overview supplies diagnostic metadata, not a suggested executable call; detailed recovery still uses Tool30. Constitution unchanged.
