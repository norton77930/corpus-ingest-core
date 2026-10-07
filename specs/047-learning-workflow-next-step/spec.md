# Feature Specification: Learning Workflow Next Step

**Feature directory**: `specs/047-learning-workflow-next-step`
**Created**: 2026-10-03
**Status**: Implemented; offline-verified on 2026-10-03 after explicit user authorization.
**Input**: Inspect current capabilities after SPEC 046 and propose the next useful bounded phase.

## Context and scope

Users can already ingest, summarize, generate a lecture, and separately derive 05/06. What is missing is a single learning-specific query telling an operator which existing operation to preview next. This proposal inspects one explicitly named local episode. It suggests at most one existing operation, or reports reusable completion or a blocked stage. It does not advance the episode.

Delivered scope: Core query plus one appended read-query MCP tool. Registry transitions from 26 to 27 by appending Tool 27, preserving Tools 1-26. No CLI or new execution Skill is needed in this phase. Existing 045 Skills remain the execution entry points.

## User Scenarios & Testing

### User Story 1 - Find the next lecture action (Priority: P1)

An operator names an episode and learns whether to generate a lecture or complete its cover without remembering file names.

**Why this priority**: Existing Tool 26 already decides both cases but requires the user to choose it first.
**Independent Test**: Offline fixtures return the correct single action, with zero writes and no derivation preview when lecture work remains.

**Acceptance Scenarios**:
1. Given a valid learning-notes source and no lecture, a query suggests lecture generation and states that subsequent confirmed generation requires LLM cost acknowledgement.
2. Given readable 03/04/07 and missing 00, a query suggests cover completion without an LLM cost acknowledgement.
3. Given missing/ineligible source or an incomplete lecture rejected by the existing preview, the query reports a lecture-stage blocker, with no force or upstream execution suggestion.

### User Story 2 - Find derivation work or reusable completion (Priority: P1)

After the lecture is reusable, the operator learns whether 05/06 can be generated or are already reusable.

**Why this priority**: It bridges the separate lecture and derivation operations without combining their approvals.
**Independent Test**: Both runner previews are faked or exercised on isolated local fixtures; suggestions match their existing reuse decisions.

**Acceptance Scenarios**:
1. Given a reusable lecture, valid operator context and missing 05/06, a query suggests derivation generation requiring cost acknowledgement on later confirm.
2. Given both successful reusable previews, the query reports complete, with no suggested call; source_currentness=not_evaluated.
3. Given missing/invalid operator context, partial 05/06, unsafe paths or recovery remnants, the query is blocked. It never proposes automatic repair.

### User Story 3 - Ask safely through MCP (Priority: P2)

An agent asks for the next step and receives only a bounded, structured decision. The user can then invoke the existing execution Skill separately.

**Why this priority**: It makes the Core decision available to current agent clients.
**Independent Test**: Registry/envelope tests exercise the new read-query while all prior tool signatures/order remain identical.

**Acceptance Scenarios**:
1. A valid query returns one decision and optional preview arguments with confirm=False and force=False, without dispatching that tool.
2. Invalid identities fail before local configuration/child access; unknown exceptions produce fixed safe errors without private data.
3. A changed episode between query and execution is re-evaluated by the existing execution preview/confirm; the query is not an approval token or pinned snapshot.

### Edge Cases

Reserved latest/next, blank/traversal identities, case and underscore preservation, missing sources, finance profile, malformed UTF-8, partial lecture, absent cover, partial pair, malformed context, stale title neighbor, symlink/reparse/special file, four recovery remnants, report path refusal, contradictory child results and exceptions containing private sentinels. Existing 05/06 may be empty or stale while still considered reusable by the current derivation contract; never call that quality validation.

### Safety and Data Boundaries

Read-only means zero file creation/modification, including reports/cache; not metadata-only internal reading. Existing previews read bounded source/lecture/context content locally. No body text, paths, context tool names or raw child objects are returned. No provider, .env, network, LLM, download, transcription, cache rebuild, repair, scheduling, automatic force, or confirmed child call. No automatic chaining of execution; at most two sequential read-only previews. No live market API, investment recommendation, target price, guaranteed return or personalized advice. Query results are not source-freshness, semantic quality or atomic-snapshot attestations.

## Requirements

### Functional Requirements

- **FR-001**: Accept exactly one explicit podcast/episode identity; reject invalid/reserved identities before configuration or child access, preserve valid case/underscores, and accept no caller file/provider/force/confirm/cost-ack parameters.
- **FR-002**: Evaluate lecture preview first with confirm=False and force=False, at most once. If it plans generation or cover completion, return that single action without evaluating derivation.
- **FR-003**: Only after a successful reusable lecture preview, evaluate derivation preview once with confirm=False and force=False. Suggest generation on a valid generation plan; report complete only when both previews explicitly report reuse and no artifact writes.
- **FR-004**: Represent expected child prerequisite failures as a blocked stage with a fixed reason; retain safe structured unsafe_path/recovery_required/derivation_conflict distinctions where provided. Do not infer missing prerequisites by parsing exception text, and do not recommend force or automatic cleanup.
- **FR-005**: For an available action, provide exactly one existing tool's preview arguments and the future confirm's LLM/cost-ack requirement. All suggested arguments use confirm=False and force=False; no generated acknowledgement text. For complete/blocked results, action and cost fields are null.
- **FR-006**: Guarantee no writes, provider creation, network, cache activity or execution dispatch on every query path. Do not add an artifact family or an ARTIFACT_LADDER stage.
- **FR-007**: Return a finite allowlisted decision only, with source_currentness=not_evaluated and fixed completion semantics. Do not expose source text, absolute/relative paths, context content, arbitrary child warnings or exception text.
- **FR-008**: Append one read-query MCP tool after the existing 26 only during approved implementation. Keep all previous names/order/signatures/defaults/envelopes and both 045 execution Skill protocols unchanged.
- **FR-009**: Validate child identity, preview mode, booleans and coherent reuse/write states; inconsistent results must never be actionable or complete. Unknown failures receive a fixed generic public error.
- **FR-010**: Cover decisions, fail-closed boundaries and registry compatibility with offline RED/GREEN checks, documentation, full regression and Spec Kit converge before implementation closeout.

### Key Entities

- Episode identity: unchanged explicit podcast ID and episode reference.
- Next-step decision: status, evaluated stage modes, fixed reason, optional action/preview call and future LLM requirement.
- Preview observation: transient existing Core result; not persisted, not returned verbatim, not an authorization or source digest.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four normal cases (lecture generation, cover completion, derivation generation, both reusable) yield exactly the expected single decision in offline acceptance fixtures.
- **SC-002**: All refusal/error fixtures preserve the file tree byte-for-byte and record zero provider/network/executor/cache calls.
- **SC-003**: No fixture response contains injected private content or paths; every complete result explicitly disclaims source freshness and content quality verification.
- **SC-004**: All 26 existing tool contracts remain unchanged; the approved new query occupies only the next slot, and all required regression checks pass.

## Assumptions

The user authorized this scoped implementation after planning. One named local learning-notes episode per query; no latest/bulk scan or upstream remediation planner. Missing source/context/partial artifacts can receive a generic stage-specific blocker because existing errors lack stable detailed codes. Trusted managed roots and externally serialized writers follow 044/046; sequential observations are not atomic. Existing publication/report contracts remain unchanged. Source lineage/digests, strong report transactions, recovery tooling, scheduling, UI and cross-episode search are deferred.

## Clarifications resolved by bounded defaults

Goal is one next-step query, not a learning catalog or combined generator. Generic prerequisite blockers are intentional; finer diagnostics would require separately scoped runner changes. Completion means existing preview reuse only. Output surfaces only future confirm cost metadata; execution still starts with its own preview and approval. No high-impact unanswered question is needed to review this proposal; these defaults remain proposed product choices.
