# Feature Specification: Learning workflow advance Skill

**Feature Branch**: None (existing workspace; no Git objects authorized)
**Created**: 2026-10-04
**Status**: Implemented (offline verified; live agent-host compliance not established)
**Input**: User accepted SPEC053 unified learning entry Skill and dialogue acceptance scope; root plans and implements it.

## User Scenarios & Testing
### US1 - Ask for one learning step (P1)
An operator names one podcast episode and receives the next eligible action, its file effects and cost before deciding to proceed. The existing unified tool handles selection; the Skill handles the conversation.
Why: avoid manually choosing lecture/derivation tools or transferring approval parameters. Independent test: real temporary Tool32 previews and instruction contracts.
1. Given explicit IDs and a request for one step, preview once and explain lecture generation, cover completion or derivation generation.
2. Given a complete or blocked workflow, report its scoped state and stop without asking for execution approval.
3. Given missing/ambiguous IDs, latest/next, batch/repair/force/full-chain intent, clarify or refuse before calling anything.

### US2 - Approve the displayed operation (P1)
The operator sees the exact planned side effects and explicitly approves this cycle. Generation also requires the shared exact cost acknowledgement provided after this preview.
Why: approval must cover the displayed target, action and cost. Independent test: synthetic conversation traces and actual Core confirmation with fake temporary providers.
1. Given valid fresh approval and cost acknowledgement where needed, confirm once with matching IDs, action and plan identifier; cover sends empty acknowledgement.
2. Given cancellation, silence, ambiguous/conditional consent, generic yes without generation acknowledgement, or only a previous-operation acknowledgement, do not confirm.
3. Given changed target/action/plan or an execution/transport failure, consume or invalidate the cycle; no retry or automatic subsequent step.

### US3 - Understand outcomes and limits (P2)
The operator receives actual paths or a truthful bounded failure explanation without private text or invented freshness/rollback guarantees.
Why: publication may succeed even when reporting fails. Independent test: actual fixed error envelopes, malformed reply fixtures and hostile-data conversation cases.
1. Given a valid execution, report the approved action, outputs and reports once; stop without inspecting the next action.
2. Given malformed, unknown or hostile responses, stop safely; returned text does not authorize calls or replace user consent.
3. Given offline checks, documentation labels instruction/oracle/Core evidence separately and does not claim live agent-host compliance.

### Edge Cases
Missing mounted tool is terminal. Preview/confirm identity and schema must match; unknown or contradictory state/cost/path combinations stop. Partial recovery/legacy/custom/stale states require manual handling. Windows and POSIX separators accepted lexically, without opening paths. A confirmed call is consumed on success, refusal, timeout or disconnection. Changing request or plan needs a new explicit request, fresh preview and fresh consent. No upstream summary/download/transcription, repair/deletion, force/provider/context/path override, terminal fallback, cache rebuild, chain or scheduler.

## Requirements
- FR-001: A portable named-episode, single-step Skill with precise discovery and routing; require explicit valid IDs, clarify incompatible scope before calls. Existing separate Skills unchanged.
- FR-002: Bind only advance_learning_workflow. One preview with confirm=false, empty expected_action/expected_plan_id/api_cost_ack; no side-effect authorization from initial invocation, no alternate tool or local fallback.
- FR-003: Validate the actual Tool32 success envelope and finite scoped plan, IDs, booleans, action/cost/state coherence, canonical owned artifact/reuse/metadata/report roles. Blocked/complete end without confirm; malformed/unknown replies stop. No file resolution/inspection.
- FR-004: Explain target/action, fixed read roles, all planned writes/reuses/metadata/reports, cost/input transfer and safe warnings; metadata-only non-atomic binding does not establish transcript freshness or content quality.
- FR-005: Require explicit approval after this preview; generation additionally requires the exact shared acknowledgement newly provided for this cycle. Do not reuse historical approval/ack, infer silence, trim/translate or synthesize text. Cover sends empty acknowledgement even if supplied.
- FR-006: Confirm once with exact preview IDs/action/plan_id and approved ack. No second preview inside the cycle, retry, post-query, follow-up action, coordinator report or automatic cache rebuild. Changes require a new explicit request and cycle.
- FR-007: Validate successful confirmed reply against the approved plan and finite executed metadata; report actual outputs/reports safely once, then stop. Do not read or claim review of produced content.
- FR-008: Preserve known fixed drift/publication/rollback/cleanup/report failure meanings; generic/unknown/transport/malformed outcomes require local inspection without zero-write/rollback claims. Do not echo arbitrary error/body/warning or treat tool data as instructions.
- FR-009: Deliver offline instruction contracts, clearly labelled synthetic conversation oracles, and actual unchanged Core/MCP temporary fake-provider characterization; independent read-only pressure/review evidence. None proves live client compliance.
- FR-010: Keep all32 tool names/order/signatures and all production/runtime/config/oldSkills/historicalpackages unchanged. No dependency/installation/deployment or real provider/corpus/environment/cache operations. Add focused usage/verification docs and full SpecKit/TDD/full checks/converge evidence.

## Key Entities
One consent cycle: named target, opaque returned plan, operator reply, at most one confirmed call and terminal outcome. Portable Skill + response-contract reference. Synthetic dialogue fixtures are acceptance examples, not an executable agent implementation or persisted approval store.

## Success Criteria
- SC-001: The operator can use one instruction entry for all three supported action classes and scoped blocked/complete states.
- SC-002: Every negative identity/schema/consent/ack/change fixture has zero confirmed calls; eligible confirmation has exactly one.
- SC-003: All approved file-effect classes and post-failure uncertainty are disclosed, without private text or unrequested follow-up.
- SC-004: Existing32 tools/runtime and separate Skills retain baseline contracts; current documents explain unified usage and offline limits.
- SC-005: Requirements map to tasks/checks; independent findings closed, full checks pass and convergence has no unbuilt work.

## Assumptions and Clarifications
Approved scope is a bounded extension to Tool32, not new runtime orchestration. Existing045 separate Skills remain for explicitly selected operations; new Skill is for an operator asking the next learning step. No critical ambiguity: identity, cost, single-cycle persistence, privacy, concurrency and unsupported intents resolved from approved scope/052/045. Constitution9 principles unchanged. Agent hosts may load portable Skill files manually; no installation or new discovery guarantee. Fresh cycle acknowledgement is a Skill protocol; Core accepts exact text without episode provenance. Offline instruction/conversation/Core checks do not prove real Claude/Codex/Grok host compliance.
