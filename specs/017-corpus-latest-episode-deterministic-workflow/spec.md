# Feature Specification: Latest Episode Deterministic Workflow

**Feature Branch**: `017-corpus-latest-episode-deterministic-workflow`

**Created**: 2026-07-16

**Status**: Implemented

**Input**: User description: "Allow an AI Agent to understand a natural request such as \"幫我處理 Gooaye 最新一集\" and advance exactly one latest episode through local deterministic processing, stopping before LLM semantic summary."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process One Latest Episode (Priority: P1)

An AI Agent receives an unambiguous natural-language request to process one
configured podcast's latest episode. It acknowledges the request once, advances
that one episode through intake, audio download, local transcription, and all
required deterministic remediation work, then reports the result once.

**Why this priority**: This is the requested end-to-end local workflow and the
minimum independently useful outcome.

**Independent Test**: A configured latest episode with no corpus artifacts can
be processed through the deterministic boundary, producing only the expected
local artifacts and a final metadata-only result.

**Acceptance Scenarios**:

1. **Given** an unseeded latest episode, **When** confirmed processing starts,
   **Then** intake, download, local transcription, and required deterministic
   remediation run in order and the result says it is ready for semantic summary.
2. **Given** a newer RSS entry appears after processing starts, **When** the
   workflow continues, **Then** it completes the episode resolved at the start
   and never switches to the newer entry.

---

### User Story 2 - Safely Resume or Avoid Rework (Priority: P2)

An operator can issue the same request again after an interrupted or completed
attempt. Existing valid work is preserved; incomplete work resumes at its first
missing deterministic step, while a semantic-summary-ready episode is not run
again.

**Why this priority**: Local download and transcription can be expensive, so a
new explicit request must not discard valid local work or create unnecessary
duplicates.

**Independent Test**: Fixtures covering a partial episode and an already-ready
episode prove that only the required remaining work runs, or that no work runs.

**Acceptance Scenarios**:

1. **Given** the latest episode already has audio but lacks a transcript,
   **When** confirmed processing runs, **Then** intake and download are not
   repeated and processing begins with local transcription.
2. **Given** deterministic remediation is already complete, **When** confirmed
   processing runs, **Then** no stage executor runs and the result identifies
   the episode as ready for semantic summary.

---

### User Story 3 - Stop Clearly on a Problem (Priority: P3)

An operator receives a bounded result when selector resolution, a deterministic
stage, or one remediation action fails or is blocked. The workflow stops at that
point and does not retry or run a later action.

**Why this priority**: Autonomous local processing must be predictable and
auditable rather than silently compensating for failures.

**Independent Test**: Inject a failure or blocked result at each stage and
assert that all later stage executors have zero calls.

**Acceptance Scenarios**:

1. **Given** audio download fails, **When** confirmed processing runs,
   **Then** local transcription and remediation do not run and the result
   contains only the safe failure category and completed work.
2. **Given** a remediation action fails, **When** confirmed processing runs,
   **Then** later remediation actions and all excluded semantic work do not run.

### Edge Cases

- An unavailable or unresolvable latest episode is blocked without writes.
- A new request after a prior failure is a new explicit authorization; it may
  resume the same latest episode from valid local artifacts but never retries
  within the same run.
- An invalid transcript, unavailable audio source, unsafe local path, or
  indeterminate dependency blocks processing and requires manual follow-up.
- A latest episode that changes only after a finished run is considered only by
  the next request.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- The feature reads configured RSS metadata and local corpus artifacts and may
  write local intake, audio, transcript, deterministic-remediation, and run
  report artifacts.
- It is dry-run first. A dry-run creates, changes, and deletes zero files and
  performs no stage execution; confirmed processing requires explicit
  `confirm=true`.
- No LLM call, semantic summary, semantic review, provider construction,
  profile credential resolution, or `.env` read is possible in this feature.
- The feature uses no external market data and never treats boundary status as a
  market fact.
- Responses and reports are metadata-only and must not reveal raw transcript,
  evidence bodies, credential-style assignments, URI query/fragment data from
  any scheme, secrets, or traceback bodies.
- The feature provides no buy/sell/hold recommendation, target price,
  guaranteed return, or personalized investment advice.
- SQLite cache rebuild remains manual; successful writes may only warn that
  derived cache metadata can be stale.
- Confirmed processing is target-scoped to the canonical episode reference
  resolved once at run start. The workflow must fail closed on any invalid,
  blocked, failed, rejected, or target-drift state. Its terminal semantic handoff is metadata-only: it may report `ready_for_semantic_summary` but
  never executes semantic summary or review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept one configured podcast identifier and
  process only its latest episode; it MUST reject arbitrary URLs and unsafe
  identifiers.
- **FR-002**: The system MUST provide a zero-write dry-run that resolves at
  most one canonical latest episode and returns its deterministic plan, risks,
  planned reads, planned writes, and confirmation requirement.
- **FR-003**: Confirmed processing MUST resolve `latest` exactly once at the
  start of that run and use the resulting canonical episode reference for every
  subsequent operation.
- **FR-004**: Confirmed processing MUST advance only the ordered deterministic
  ladder: intake, audio download, local transcription, then required
  deterministic remediation actions.
- **FR-005**: The system MUST preserve valid local artifacts and begin a new
  confirmed request at the first incomplete deterministic operation for the
  resolved episode.
- **FR-006**: The system MUST return a terminal ready-for-semantic-summary
  result without executing an LLM, semantic review, or any other follow-on work.
- **FR-007**: On a failed, blocked, rejected, or unsafe deterministic action,
  the system MUST stop the current run immediately, record bounded metadata,
  and execute no later action or retry.
- **FR-008**: Confirmed processing MUST write metadata-only JSON and Markdown
  run reports after a validated attempt; dry-run and invalid input MUST write no
  workflow-owned report.
- **FR-009**: The system MUST provide one reviewed MCP entry point and one thin
  local command surface. Both MUST delegate to the same core behavior and
  default to dry-run.
- **FR-010**: The portable Agent Skill MUST treat an explicit natural-language
  request to process a configured latest episode as a one-time execution
  authorization, acknowledge once, invoke only the dedicated MCP workflow once
  with `confirm=true`, report once, and stop. The MCP tool itself remains
  dry-run by default outside that Skill protocol.
- **FR-011**: The Skill and workflow MUST NOT use a terminal fallback, retry,
  force overwrite, partial processing, batch processing, scheduling, automatic
  cache rebuild, semantic summary, semantic review, or live market data.
- **FR-012**: The MCP registry MUST expose exactly fourteen reviewed tools and
  preserve the existing response envelopes and prior thirteen tool contracts.
- **FR-013**: Existing 016 human-controlled preview and one-action confirmation
  behavior MUST remain unchanged.
- **FR-014**: Confirmed result composition MUST preserve action identity coherence:
  the selected remediation action identifier and the priority-winning target
  execution row identifier MUST agree when both are present. A mismatch or an
  identifier that is present but malformed MUST fail closed without copying the
  source row's reason, paths, warnings, failure category, or status metadata.
  Only a genuinely absent or `null` source identifier may retain a valid
  selected identifier.
- **FR-015**: Internal semantic-handoff classification MUST contain valid
  remediation evidence for the canonical target episode. Empty results and
  results containing only non-target `skipped` rows MUST fail closed; target
  semantic residual rows may only be `blocked` or `excluded`.
- **FR-016**: Metadata sanitization MUST replace credential-style assignments
  and URI query/fragment data from every URI scheme with the standard safety
  boundary placeholder while preserving ordinary safe text and safe local paths.

### Key Entities

- **Latest Episode Snapshot**: The one canonical podcast episode selected at
  the start of a run, including safe identification metadata used by later
  deterministic actions.
- **Deterministic Workflow Result**: The metadata-only record of the selected
  episode, run mode, ordered actions, outcome, safe output references, warnings,
  and whether semantic summary is now the next boundary.
- **Workflow Run Report**: The confirmed-only JSON and Markdown audit record for
  the latest deterministic workflow attempt for one configured podcast.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single confirmed request completes every necessary local
  deterministic step for one latest episode and stops at the semantic-summary
  boundary without human intervention between those steps.
- **SC-002**: In automated tests, 100% of injected failures or blocked states
  result in zero invocations of all later workflow actions.
- **SC-003**: In automated tests, a feed update during processing results in
  100% of later actions using the canonical episode selected at run start.
- **SC-004**: In automated tests, an already semantic-summary-ready episode
  executes zero deterministic stage actions.
- **SC-005**: The Agent-facing surface contains exactly one dedicated MCP tool
  and one dedicated Skill for this workflow, with no LLM or secret access.

## Assumptions

- `gooaye` remains a configured podcast profile; core behavior stays profile
  driven and does not hard-code a podcast name.
- The first phase ends at `ready_for_semantic_summary`; changes to LLM summary
  wording or semantic review are future approved work.
- A subsequent explicit natural-language request is a new authorization, but a
  single workflow invocation never retries after a failure.
- The existing local artifact and report conventions remain the source of truth
  for determining completed or resumable deterministic work.
