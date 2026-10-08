# Feature Specification: Source learning reliability and note quality

**Feature Directory**: `specs/059-source-learning-reliability`
**Created**: 2026-10-08
**Status**: Implemented; actual Hermes acceptance remains separate
**Input**: Harden prepared-source learning after host testing: narrowly recover parameter mistakes, prefer local source learning, preserve source examples, and keep bounded/version-pinned evidence.

## User Scenarios & Testing

### User Story 1 - Recover one parameter mistake (Priority: P1)

A user requesting notes should keep successfully read evidence when the host mistypes a continuation parameter, without accepting changed sources or repeating side effects.

**Why this priority**: A long source needs many successful pages; a single correctable mistake currently stops learning.
**Independent Test**: Inject a malformed cursor or version after successful pages, check one recovery and exact remaining evidence; inject a second mistake and check partial scope.

**Acceptance Scenarios**:

1. Given a pinned version and a successful page, when the next query fails because of a parameter mistake, then inspect using only the same two IDs, require the original version, and retry the unread page once using the saved parameters.
2. Given the recovery has been used, when another parameter mistake occurs, then stop without another inspection and report partial notes with examined scope.
3. Given a changed version, unsafe/missing source, malformed reply or preparation failure, when it occurs, then stop without automatic retry or repair.

### User Story 2 - Use the intended source and explain failures (Priority: P1)

A user gives a supported audiovisual URL and asks for understanding, summary, QA or learning notes. The host selects the source learning entry and local MCP before third-party transcript searches.

**Why this priority**: Correct notes depend on selecting the intended local source.
**Independent Test**: Inspect discovery descriptions and routing instructions, validate safe diagnostics for inspect/version/cursor mistakes, and provide a host discovery acceptance scenario.

**Acceptance Scenarios**:

1. Given a supported URL and learning intent, when the entry is discoverable, then use its existing preview/QA path before web extraction or third-party transcripts.
2. Given preparation is unavailable or blocked, then explain the blocker and ask the user to decide; never silently switch sources.
3. Given non-inspect parameters in inspect, malformed version, invalid cursor or version mismatch, then distinguish these conditions without echoing transcript or caller-supplied values.

### User Story 3 - Preserve meaning and source attribution (Priority: P2)

Learning notes explain the source's issues and concrete examples, without guessed gender, unsolicited audience/application sections or unlabeled AI content.

**Independent Test**: Validate the editable template and run synthetic examples with unknown speakers and a concrete metaphor.

**Acceptance Scenarios**:

1. Given no source-confirmed gender, then use 講者 or a confirmed name, not a guessed gendered pronoun.
2. Given a key example/metaphor, then preserve the concrete situation and explain how it supports the argument rather than only giving an abstract takeaway.
3. Given no request for project application or audience-specific summary, then omit those sections; AI additions appear in explicitly labeled separate sections.

### User Story 4 - Verify long sources portably (Priority: P2)

A bounded long-source verification accommodates a source longer than 60,000 characters, and a lecture preview test works across Windows and Linux.

**Independent Test**: Deliver over 60,000 synthetic characters under default verifier settings; validate CLI defaults and native/POSIX lecture path projections.

### Edge Cases

- A well-formed but different version is source_changed, even if the host thinks it is a typo.
- A first inspect failure has no pinned baseline: stop; do not claim the version is unchanged.
- Recovery before the first successful read uses the validated initial read request with an empty cursor.
- Recovery inspection fails, changes identity/version, or produces malformed data: stop, no further call.
- Successful recovery does not replenish its one-per-task allowance or call/character budget.
- Search, selected ranges and interrupted chunks remain partial for a whole-source request.
- Explicit inspect defaults are indistinguishable from omitted defaults at the current bound function; this feature does not change the public signature to track presence.
- A host with no discoverable Skill cannot route using that Skill's description; installation/discovery is a separate operator prerequisite.

### Safety and Data Boundaries

No new tool, provider, dependency, durable session state or source artifact. Read-only query output stays bounded; exact version and cursor binding remain. Preparation/ingest/transcription/lecture workflows retain fresh consent, one dispatch and no retry. No .env access, credentials, host settings, real transcript fixtures, operation records or personal handoff documents. No investment advice/live market API; cache rebuild stays manual. Chat notes remain host output, not repository-provider calls or published artifacts.

## Requirements

### Functional Requirements

- **FR-001**: Allow at most one recovery per explicit learning task, only for a valid query_source_content failure envelope with invalid_request or invalid_cursor caused by the host's parameters after a version is pinned.
- **FR-002**: Recovery MUST inspect with only the same podcast_id and episode_ref, verify the pinned version and identity, and retry only the failed unread request using the last successful next_cursor (or initial empty cursor).
- **FR-003**: Stop on a second eligible error, failed recovery inspection, changed/unsafe/missing source, malformed reply or transport ambiguity; label unfinished notes partial and state valid examined scope without mixing versions.
- **FR-004**: Preparation, downloading, transcription, study-guide and other side-effect tools MUST retain no-retry rules and consent boundaries.
- **FR-005**: Reads MUST be sequential, one page at a time; copy next_cursor and source_version verbatim from the previous valid response, preserve query/window/action and count recovery against cumulative budgets in conversation only.
- **FR-006**: Inspect misuse MUST explain 'inspect 只接受 podcast_id、episode_ref'; read diagnostics MUST distinguish malformed version, invalid cursor encoding/continuation binding, and source-version mismatch using finite content-free messages.
- **FR-007**: Entry discovery and routing MUST cover supported audiovisual URL understanding, summary, QA and learning notes; use local MCP first, and request user choice when preparation is unavailable/blocked instead of automatically fetching third-party transcripts.
- **FR-008**: Unknown gender MUST use 講者 or a source-confirmed name; important source examples/metaphors MUST preserve concrete detail and argumentative purpose.
- **FR-009**: Notes MUST omit unsolicited audience/project sections, honor requested format, and isolate AI additions in clearly labeled sections of the existing editable template.
- **FR-010**: Verifier default total-character budget MUST be 120,000 in Core and CLI, with explicit long-source guidance; per-page/call/timeout bounds and verifier's own no-retry behavior remain.
- **FR-011**: The study-guide preview test MUST use portable native paths and correctly identify planned LLM writes on Windows/Linux without changing production path interpretation.
- **FR-012**: Tests MUST cover recovery success and stopping, safe diagnostics, unchanged side-effect stopping, routing and quality contracts; offline checks MUST not claim actual Hermes/model compliance.

### Key Entities

- Conversation checkpoint: source identity, fixed version, original scope/action/query, successful cursor/chunks and cumulative budgets; never persisted by this feature.
- Query diagnosis: finite public reason plus safe parameter-category explanation; no raw request values or evidence.
- Notes: source-grounded explanations/examples/replay ranges, optional separately labeled AI additions, explicit completeness.

## Success Criteria

- **SC-001**: Both malformed cursor and version scenarios recover once without losing or duplicating previously successful evidence.
- **SC-002**: Every tested second-error/changed-source/unsafe/preparation scenario stops at the specified boundary with no additional side-effect attempt.
- **SC-003**: Reader guidance routes audiovisual learning to the original local source and explicitly exposes blocked choices.
- **SC-004**: Synthetic note cases retain concrete examples and do not require unsupported gender, unsolicited applications or unmarked additions.
- **SC-005**: A synthetic source exceeding 60,000 characters fits default verification, and portable preview checks preserve LLM detection.

## Assumptions and Clarifications

- User authorized planning and implementation together; no branch/commit/push/deployment.
- One recovery is total per explicit request, not per page. Initial inspect failure stops; this conservative choice needs no new source/version baseline semantics.
- Hosts can discover the Skill description and load its references; otherwise operator setup is required outside this feature.
- Offline tests and read-only agent scenarios assess contracts, not actual Hermes. Real-host discovery and note quality remain separate acceptance checks.
- Existing constitution v1.0.1 applies without amendment. No new provider or safety-boundary relaxation is required.
