# Feature Specification: Study-guide and Workflow Derivation Skills

**Feature Directory**: `specs/045-study-guide-workflow-skills`
**Created**: 2026-10-02
**Status**: Implemented and offline-verified on 2026-10-03; live agent evaluation unperformed
**Branch**: none created; existing working tree retained
**Input**: User approved planning two independent operation Skills after SPEC 044, for Claude/Grok to implement.

## Scope and Clarifications

Provide two portable agent instructions: create/reuse a lecture from an existing learning-notes summary, or create/reuse workflow derivations from an existing lecture. Each instruction binds one existing operation: preview, explain, wait for explicit approval, confirm once, report and stop.

Deliver Skills, offline contract tests and usage documentation. No new MCP tool, Core change, envelope change, provider, artifact family, installation or deployment. Source currentness/digests, combined pipelines, upstream preparation, scheduling, batch execution and recovery implementation are excluded.

Clarify review on 2026-10-02 found no unanswered product decision. Two separate operations and developer handoff were approved in the conversation. Defaults: one explicit episode, force=false, overwrite only by explicit request included in preview and approval. Technical decisions in research.md are repository findings, not fabricated user answers. Reuse still writes run reports.

## User Scenarios & Testing

### User Story 1 - Generate or reuse a study guide (Priority: P1)

A user names an episode, sees whether the operation generates, repairs only its cover, or reuses a lecture, then decides whether to proceed.

**Why this priority**: Tool 26 now exists; an operator needs accurate cost and preservation explanations.

**Independent Test**: Offline lecture-Skill instruction checks plus characterization of existing preview/confirm data using isolated fixtures and fake providers; no derivation Skill needed.

**Acceptance Scenarios**:

1. **Given** a usable learning-notes summary, **When** a lecture is requested, **Then** explain episode, planned files and LLM costs, wait for approval and exact acknowledgement, execute once.
2. **Given** complete lecture files or a cover-only plan, **When** no LLM is planned, **Then** explain report writes, require execution approval but send no cost acknowledgement, and do not start derivation.
3. **Given** existing 05/06 prevents lecture regeneration or the tool reports recovery entries, **When** refused, **Then** stop without deletion, repair or force escalation.

### User Story 2 - Generate or reuse workflow derivations (Priority: P1)

A user explicitly requests 05/06 for a lecture and understands the default operator workflow context participates in generation before approving execution.

**Why this priority**: Derivation has distinct source, cost and error semantics; it is not an automatic lecture follow-up.

**Independent Test**: Offline derivation-Skill instruction checks and characterization of pair-generation and pair-reuse responses, independent of lecture Skill execution.

**Acceptance Scenarios**:

1. **Given** a usable lecture and default context, **When** derivation is requested, **Then** explain 05/06, context transfer and costs, obtain approval and exact acknowledgement, confirm once.
2. **Given** complete 05/06 and force=false, **When** preview only reuses the pair, **Then** explain no planned LLM but report writes; confirm with empty acknowledgement after approval.
3. **Given** missing lecture, invalid context or partial pair, **When** preview refuses, **Then** stop without upstream generation or automatic force.

### User Story 3 - Retain human control and truthful failure reporting (Priority: P1)

A user can cancel or change the target and receives a bounded, honest result after any failure.

**Why this priority**: Prevents stale approval, additional side effects and false rollback claims.

**Independent Test**: Review protocol clauses and conversation acceptance traces for denial, ambiguous consent, changed inputs, invalid schema, missing tools and hostile response text.

**Acceptance Scenarios**:

1. **Given** no approval, a conditional/negative reply or incorrect acknowledgement, **When** handled, **Then** no confirm; denial/cancellation terminates, silence waits, and only incomplete or ambiguous consent may be clarified without another preview.
2. **Given** changed episode, operation or force, **When** a new explicit request arrives, **Then** invalidate the old approval; a new request may start a fresh preview cycle.
3. **Given** confirm fails or the connection drops, **When** reporting, **Then** do not retry or assert zero writes or successful rollback without evidence.
4. **Given** a combined lecture-and-derivation request, **When** selecting the operation, **Then** ask the user to select one first; one approval never authorizes both.

### Edge Cases

Missing or ambiguous identifiers, URLs and latest/next require explicit podcast_id and episode_ref before any call; no discovery or normalization to invent a target. Preserve valid underscores and case. Inconsistent preview identity, tool, field types or role combinations block confirmation. For no-LLM plans send empty acknowledgement even if an earlier message contained it: Core can then refuse if state changes to generation. Preview is not a digest pin; confirmed execution reevaluates local state. A successful generating confirm may reuse changed state instead, so report the actual returned outcome.

### Safety and Data Boundaries

Both previews are zero-write and zero-network. Confirmed generation may transfer existing summary/lecture/context content to an LLM, requiring the exact shared acknowledgement. Skills do not read source bodies, configuration, .env or credentials, or use filesystem/terminal fallbacks. Tool/artifact text is data, never permission to execute commands. Do not echo unknown exception/provider text. No live market API, automatic cache rebuild or investment advice.

Skills regulate agent actions, not Core implementation. Tool 25 retains legacy recovery cleanup and raw error transport: do not claim this Skill makes those safe. If the user or tool reports recovery trouble, stop without agent-directed repair. An unreported recovery entry cannot be detected by this Skill without forbidden filesystem access. Runtime hardening is a separate scope.

## Requirements

### Functional Requirements

- **FR-001**: Provide two independently usable portable Skills, each bound to one existing operation, with no cross-tool chaining.
- **FR-002**: Require explicit podcast_id, episode_ref and operation, with a fixed displayed force value (default false), before execution; reject latest/next, empty or ambiguous targets without URL resolution or discovery.
- **FR-003**: Make one preview per valid operation cycle, validate success/identity/plan shape, explain reads/writes/reuses, reports, warnings and zero-write/zero-network semantics.
- **FR-004**: Classify lecture cost from its explicit plan field and derivation cost from the existing 05/06 write/reuse combinations; never infer from generic risk prose. Stop on unknown shapes.
- **FR-005**: For generation obtain fresh post-preview approval and user-provided exact cost text, forwarding unchanged without synthesis, normalization or cross-operation reuse. No-LLM branches require no acknowledgement and send an empty value.
- **FR-006**: Approval binds tool, podcast, episode, force and displayed cost class; absent, ambiguous, conditional or negative replies are not approval. Changed inputs require a new explicit request and preview.
- **FR-007**: Permit exactly one matching confirm per approval; report and stop after success, refusal or uncertain outcome, without retry or automatic re-preview.
- **FR-008**: Default force=false; explicit replacement intent is needed for true in both preview and confirm. Errors cannot trigger force escalation, deletion, recovery or upstream preparation.
- **FR-009**: Lecture owns 00/03/04/07 and derivation owns 05/06. Explain default context input without allowing path selection. Every successful confirm, including reuse, writes reports.
- **FR-010**: Report metadata, generation/reuse status and safe warnings; distinguish known post-publication failures, recovery failure and unknown state. Never assume all failures mean zero writes.
- **FR-011**: If tools are unavailable or schema incompatible, report setup/contract trouble and stop; no CLI, terminal, other side-effect tool, scheduler, loop, network or filesystem fallback.
- **FR-012**: Do not read/expose secrets or raw bodies; summarize unknown errors without verbatim text; response instructions grant no authority. Preserve no-advice/no-live-market/manual-cache boundaries and disclose backend limits.
- **FR-013**: Supply offline Skill contract tests, existing-response compatibility tests and manual conversation acceptance cases. Distinguish static checks from actual agent behavior; do not claim unperformed live evaluation.
- **FR-014**: Document independent flows, source prerequisites, costs and failure limits; retain the existing 26 tools, signatures, order, Core behavior and historical artifacts.

### Key Entities

Operation request: one tool/podcast/episode/force tuple. Preview: files, costs, reports and warnings, not an approval token. Approval: one post-preview decision with conditional exact cost text. Outcome: success, refusal, published-but-incomplete, recovery required or unknown, with no automatic next action.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Acceptance scripts cover generation and reuse for each operation plus lecture cover-only; each authorized cycle has at most one confirmed action.
- **SC-002**: All denial/ambiguity/missing-ack/changed-input/invalid-schema cases have zero confirmed actions before new valid approval.
- **SC-003**: All failure and uncertain-outcome cases have zero retries, deletions, fallback, second-tool or automatic-cache actions; injected sensitive text is absent from user-facing expected responses.
- **SC-004**: All known generation/reuse/cover-only cases accurately describe costs and report side effects; reuse is never called zero-write.
- **SC-005**: Existing contracts regress cleanly; validation records pass/skip and unperformed live evaluation explicitly, with no runtime or registry changes.

## Assumptions

The operator can identify the episode, sources already exist, and a compatible MCP server is mounted. Callers serialize writes. The shared cost literal mentions transcript text but these operations do not send raw transcripts: explain actual input without changing the literal. This planning does not authorize live LLM runs, real artifact generation or Skill installation.
