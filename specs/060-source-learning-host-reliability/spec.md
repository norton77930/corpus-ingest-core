# Feature Specification: Source learning host reliability

**Feature directory**: `specs/060-source-learning-host-reliability`
**Branch**: Existing `main`; no feature branch created.
**Created**: 2026-10-08
**Status**: Implemented; local verification complete; actual operator-source and Hermes acceptance pending.
**Input**: User requests a repair plan for Grok's Hermes findings on SPEC059 / commit `8f6579a`: fragile continuation copying, truncated discovery descriptions, background delegation, web-first routing and insufficiently grounded notes. The user approved this plan and authorized implementation.

## User Scenarios & Testing

### User Story 1 - Continue reading reliably (Priority: P1)

A learner requests whole-source notes. Reading must continue without omissions or duplicate text, using a shorter continuation value and one fixed source version. A model parameter mistake may recover once from the last successful response.

**Why this priority**: Interrupted delivery prevents meaningful whole-source notes regardless of writing quality.
**Independent Test**: Reconstruct bounded synthetic multi-page sources, including a segment split across pages; inject a copying mistake, then verify exact continuation and second-error stopping.

**Acceptance Scenarios**:

1. **Given** a prepared source with multiple pages, **when** all consecutive pages are read, **then** every requested text chunk is delivered exactly once and new continuation values have at most 60 characters.
2. **Given** a pinned version and a failed parameter copy, **when** the permitted recovery runs, **then** fresh inspection must match the original version and the unread page uses the continuation freshly copied from the last successful response, never the failed request.
3. **Given** a changed source, a failed recovery inspection, or a second parameter error, **when** reading would continue, **then** it stops and reports partial coverage without repinning or automatic repair.
4. **Given** an existing continuation value, **when** an updated reader receives it with the same original scope/version, **then** it remains usable; newly emitted values use the shorter format.

### User Story 2 - Discover the local source route (Priority: P1)

A learner supplies a YouTube/X URL and a source-learning question without preloading Skill bodies. The visible short description must identify the local entry, and the first source-processing call must preview that source locally.

**Why this priority**: An unread Skill cannot influence model behavior; third-party text may answer a different source.
**Independent Test**: Apply Hermes's actual description truncation to all repository Skills and inspect entry routing requirements; separately observe a fresh Hermes conversation.

**Acceptance Scenarios**:

1. **Given** only a short discovery description, **when** the learner asks a URL learning question, **then** source-learning-entry visibly identifies YouTube/X learning and local MCP priority.
2. **Given** installed resources and mounted tools, **when** the entry starts, **then** its first source-processing MCP call is a non-confirming preparation preview before web or third-party transcript lookup.
3. **Given** missing resources, unavailable tools or blocked local acquisition, **when** the route cannot proceed, **then** it explains the cause and awaits user choice; failure alone does not authorize web fallback.

### User Story 3 - Keep reading and progress in the conversation (Priority: P1)

A learner can observe the ordered calls and receives an honest answer about what has actually been read. Content reading cannot disappear into a background AI task whose result may not return.

**Why this priority**: A reported background handle is not delivered evidence or a promise that notes will arrive.
**Independent Test**: Check foreground/delegation/progress requirements and, in Hermes, verify no delegation and truthful partial/completed status.

**Acceptance Scenarios**:

1. **Given** a source-learning request, **when** preparation preview/status, inspection, search or reading is invoked, **then** calls occur directly and sequentially in the main conversation, never through background AI delegation.
2. **Given** no active reading operation, **when** the turn ends with partial evidence, **then** it states the examined scope instead of claiming notes are still being processed.
3. **Given** a properly approved background download/transcription job, **when** it is accepted, **then** submission and recorded progress may be reported accurately, without automatic AI learning or claiming completed notes.

### User Story 4 - Learn from the speaker's actual explanation (Priority: P2)

A learner asking what a source means receives the source's argument and key examples, with general explanation visibly separated and no invented speaker identity or unsolicited sections.

**Why this priority**: Fluent general knowledge can obscure what was actually said in the source.
**Independent Test**: Check the written response rules and synthetic evidence scenarios; review real Hermes notes against the relevant source passages separately.

**Acceptance Scenarios**:

1. **Given** a source-related conceptual question, **when** answering, **then** retrieve relevant evidence first; general knowledge is explicitly labeled as AI supplementary explanation.
2. **Given** no explicit speaker gender, **when** referring to a speaker in assistant-authored prose, **then** use a source-confirmed name or 講者, not 他/她.
3. **Given** a key example in the relevant read passage, **when** explaining that issue, **then** retain the example's concrete situation/actions and its argumentative role.
4. **Given** a request without project applications or audience-specific deliverables, **when** writing notes, **then** omit those extra sections.

### Edge Cases

- A cursor copied with missing, reordered, duplicated or changed characters; an unknown format prefix; a corrupted position that is still numerically in range.
- Changing podcast, episode, action, literal query or time window mid-continuation; valid-looking but different version still stops as source_changed.
- A long segment spanning pages; search selection positions differing from source ordinals; an empty search selection.
- An error before the first successful read but after a successful inspect: recover with the original empty cursor; initial inspect failure never recovers.
- A literal search without hits, mixed-language keywords or unclear conceptual phrasing: lack of keyword hits is not absence of a concept.
- A host lacking the entry description, dependencies or tools; reading Skill resources precedes the first source-processing MCP call.
- Pending preparation is a recorded job observation, not active background AI writing; progress-only requests remain status-only.
- A user changes formatting, asks a general question unrelated to the source, or requests no AI supplements: apply the current request without unnecessary retrieval/sections.
- A full-source verifier must cover the final zero-duration segment as well as all ordinary segments; selected-range exhaustion alone is not proof of whole-source delivery.

### Safety and Data Boundaries

Only local prepared evidence and synthetic tests are used by the reader. No new provider, source downloading, transcription, artifact publication or repository query/session store is added. Preparation still previews first, requires fresh approval before confirmation, and retains no retry. Existing provider acknowledgement, hostile-evidence handling, no investment advice and manual cache rebuild boundaries remain. Never commit source media/transcripts, host settings, credentials, session traces, operation logs or personal handoff documents. This phase does not run live preparation or alter a Hermes host.

## Requirements

### Functional Requirements

- **FR-001**: Newly emitted continuation values MUST be at most 60 characters and stateless, with accidental corruption detected rather than silently skipping content.
- **FR-002**: Read/search MUST retain the complete 64-lowercase-hex expected_source_version and bind continuation to source identity, version, action, literal query and time window; a changed source stops without repinning.
- **FR-003**: Continuation MUST preserve partial-segment character offsets, ordered exact delivery and existing output bounds without using original segment IDs for pagination.
- **FR-004**: Existing valid continuation values MUST remain accepted under their existing scope and position checks; new responses emit the shorter format.
- **FR-005**: The one eligible recovery MUST freshly copy continuation from the last successful validated response, never from the failed request; use empty continuation if no read/search page succeeded in that sequence.
- **FR-006**: Recovery MUST remain limited to one structured query_source_content host-parameter invalid_request/invalid_cursor per explicit learning task after a successful pin; second error, inspect failure, source_changed, unsafe/missing source, malformed reply or transport ambiguity stops partial. Preparation/generation never inherit the exception.
- **FR-007**: Reading and recovery MUST remain sequential and retain cumulative call/character budgets and conversational checkpoints only; successful recovery does not replenish the allowance.
- **FR-008**: Every repository Skill description MUST fit within 60 normalized Unicode characters and state its purpose; entry discovery MUST visibly convey YouTube/X learning and local MCP priority. Tests MUST use Hermes's 57-character-plus-ellipsis truncation behavior for overlong descriptions.
- **FR-009**: A supported URL learning request MUST start source-processing MCP calls with prepare_learning_source confirm=false; loading required Skills/resources is allowed first. It MUST not call x_search, web_search, web_extract or obtain third-party transcripts before the local route.
- **FR-010**: Local acquisition being blocked/unavailable MUST produce a clear explanation and user choice, never automatic web substitution, repair or host configuration changes.
- **FR-011**: Preparation preview/confirm/status and content inspect/search/read calls MUST run directly in the main conversation, one at a time, without delegate_task or background AI workers. Existing server-managed media preparation jobs remain permitted under their original approval contract.
- **FR-012**: Status statements MUST reflect actual tool calls/results and observed coverage. Without active AI work, the assistant MUST not claim notes remain 整理中/已在處理; an accepted preparation job can be reported as 已提交 with returned job/status and any returned timestamp (omit absent fields), not as completed notes.
- **FR-013**: Questions about a selected source MUST retrieve relevant search/read evidence before answering, even when phrased as a general concept; unrelated general-knowledge questions do not trigger source retrieval.
- **FR-014**: Evidence retrieval MUST preserve literal-search limitations, surrounding-context reading, timestamps and ASR uncertainty; no keyword hits do not prove conceptual absence.
- **FR-015**: Unknown gender MUST be represented by 講者 or a source-confirmed name in assistant-authored prose; main Skill instructions MUST include positive and negative examples and prohibit inference from voice/context.
- **FR-016**: Before answering, the assistant MUST check relevant already-read passages for key concrete examples/metaphors and preserve their situation/actions and relation to the speaker's reasoning; never invent examples where none were supplied.
- **FR-017**: General knowledge, self-created examples and inferences MUST be clearly separated under an AI 補充 label and never attributed to the source; omit supplements if the user requests source-only content.
- **FR-018**: Responses MUST omit unrequested extra deliverables, audience summaries and project applications; truthful source/coverage limitations remain necessary disclosure.
- **FR-019**: Changes MUST preserve the reviewed 35-tool registry, public signatures/envelopes/reasons, bounded output, no stored session state, no-retry/approval boundaries and prohibited-data exclusions.
- **FR-020**: Verification MUST include cursor/recovery/discovery/Skill-rule regressions, updated verification-matrix and Hermes quickstart, full pytest/compileall/diff checks at implementation closeout, and default-budget whole-source MCP delivery with scope_complete=true plus whole-source segment-count checks. Actual model behavior MUST be reported separately from deterministic delivery.

### Key Entities

- **Continuation**: Bound source selection, next selected position and character offset; not a durable session or approval credential.
- **Reading checkpoint**: Last validated successful response, original version/scope and remaining allowance, held only in conversation.
- **Discovery description**: Short purpose/routing text the host exposes before a Skill is loaded.
- **Evidence and response**: Relevant timed source passages, concrete speaker examples and separately identified AI explanation.
- **Acceptance observation**: Local human review of host call order, coverage and notes; no committed source/session artifacts.

## Success Criteria

### Measurable Outcomes

- **SC-001**: New continuation values are no longer than 60 characters; synthetic multi-page and split-segment delivery reconstructs 100% of requested text with no omissions or duplicates.
- **SC-002**: Controlled copying mistakes recover exactly once from valid evidence; a second mistake or source change always stops without mixing versions.
- **SC-003**: All repository Skills retain an intelligible purpose in the host's short discovery view; the URL entry's local-first direction remains visible.
- **SC-004**: In the operator's fresh URL learning acceptance conversation, local preview precedes any third-party lookup and all evidence reading remains visible in the main conversation.
- **SC-005**: Source-related concept answers cite retrieved passages; reviewed notes retain the relevant key examples, use neutral speaker references and separate every AI supplement, with no unsolicited deliverables.
- **SC-006**: The owned whole-source delivery check reaches all inspected segments with default budgets; this result is never represented as proof that the host model understood or accurately summarized them.

## Assumptions and Clarifications

- The user approved implementation; actual operator-source and Hermes acceptance remain separate from local verification.
- Choose shorter stateless tokens rather than a new ordinal-only API; preserve offsets and scope binding. Encoding details belong to plan/contracts.
- Retain legacy cursor reading for compatibility; it does not acquire new integrity properties retroactively.
- The repository can publish clear Skills and deterministic checks but cannot enforce Hermes's arbitrary tool choices without a separate host policy, which is out of scope.
- Discovery assumes complete synchronized Skill folders and mounted MCP tools; no host installation/settings changes are included.
- The known Hermes source is an operator-owned acceptance target, not a repository fixture. Current inspect metadata, not historical segment counts/times, determines acceptance bounds.
- Unrelated Skills change description text only; their approval, acknowledgement and execution workflows remain unchanged.
