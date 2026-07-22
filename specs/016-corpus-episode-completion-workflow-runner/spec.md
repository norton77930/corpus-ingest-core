# Feature Specification: Corpus Episode Completion Workflow Runner

**Feature Branch**: `016-corpus-episode-completion-workflow-runner`

**Created**: 2026-07-13

**Status**: Implemented

**Input**: User-approved design for a human-controlled, single-episode
completion workflow exposed through Core, CLI, MCP, and a portable Agent Skill.

## User Scenarios & Testing

### User Story 1 - Preview the Safe Next Action (Priority: P1)

As an operator, I want an agent to inspect one podcast episode and explain the
single safe next action without changing any files, so I can decide whether to
approve that action.

**Why this priority**: Human control and a trustworthy zero-file preview are
the minimum safe value of the feature.

**Independent Test**: For each episode state, request a dry-run and verify that
the expected next action, planned reads and writes, risks, blockers, and
canonical episode reference are returned while the entire local tree remains
byte-for-byte and metadata-for-metadata unchanged.

**Acceptance Scenarios**:

1. **Given** an episode at any supported point in the completion ladder,
   **When** the operator requests a dry-run, **Then** exactly one next action or
   a terminal `completed`/`blocked` result is selected deterministically.
2. **Given** `latest` is requested in dry-run mode, **When** the feed resolves
   successfully, **Then** the result identifies one canonical episode reference
   that can be used for later confirmation.
3. **Given** persisted index, plan, or workflow reports are stale, **When** the
   preview runs, **Then** fresh in-memory state determines the result and no
   persisted planning artifact is read as stage truth or refreshed.
4. **Given** snapshot or selector inspection fails, **When** the preview runs,
   **Then** it fails closed with bounded category-only metadata and performs no
   later probe or side effect.

---

### User Story 2 - Execute One Approved Action (Priority: P2)

As an operator, I want the agent to execute only the exact episode action I
approved and then stop, so no hidden loop or fallback can advance the episode
without another decision from me.

**Why this priority**: It turns the safe preview into useful progress while
keeping every side effect human-controlled.

**Independent Test**: Preview a state, confirm the returned canonical episode
reference and explicit action, and verify exactly one matching existing stage
executor is attempted, one bounded completion report is written, and no other
action is attempted.

**Acceptance Scenarios**:

1. **Given** a dry-run selected an explicit action, **When** the operator
   confirms the same action for the canonical episode reference, **Then** the
   matching existing runner is invoked at most once and the workflow stops.
2. **Given** the episode state changed after preview, **When** the previously
   approved action is confirmed, **Then** the request is rejected without
   executing the newly selected alternative.
3. **Given** a confirmed request still uses `next` or `latest`, **When** it is
   validated, **Then** it is rejected before any feed, snapshot, profile,
   environment, provider, executor, or writer work.
4. **Given** semantic summary is selected, **When** acknowledgement is missing
   or not exact, **Then** the request is rejected before any potentially costly
   or secret-bearing work.
5. **Given** the selected stage returns blocked, rejected, failed, or raises a
   contained exception, **When** the workflow records that outcome, **Then** it
   stops without retry, fallback, cleanup, or cache rebuild.

---

### User Story 3 - Use the Workflow from an Agent (Priority: P3)

As an operator using Codex or another standards-compatible agent, I want a
portable skill and one reviewed MCP tool to guide the preview, explanation,
approval, execution, report, and stop protocol.

**Why this priority**: This is the intended conversational surface, but it
depends on the Core safety contract from the first two stories.

**Independent Test**: In a fresh Codex session, discover the repository skill
and MCP tool, select the tool with `confirm=false` and a bounded input that is
rejected by early validation before RSS/corpus work, and verify that no
confirmed action, local fallback command, or additional loop is started.

**Acceptance Scenarios**:

1. **Given** the completion skill and MCP server are mounted, **When** an
   operator asks to advance an episode, **Then** the agent previews first,
   explains the selected action and risks, asks one explicit approval question,
   and waits.
2. **Given** approval is missing, ambiguous, or negative, **When** the agent
   interprets the reply, **Then** it does not call a confirmed action.
3. **Given** explicit approval is received, **When** the agent proceeds,
   **Then** it calls the same MCP tool with the exact canonical episode
   reference and selected action, reports the bounded result, and stops.
4. **Given** the completion MCP tool is unavailable, **When** the skill is used,
   **Then** it reports a setup problem and does not fall back to a CLI, terminal,
   another side-effect tool, scheduler, or autonomous loop.

### Edge Cases

- An unseeded episode selects `intake`; missing audio selects
  `audio_download`; local audio without transcript selects
  `local_transcription`; a valid transcript missing deterministic artifacts
  selects `deterministic_remediation`; missing semantic summary selects
  `semantic_summary`; missing semantic review selects `semantic_review`; a
  passed review selects `completed`.
- A missing episode, invalid transcript, unavailable audio source, unreadable
  semantic summary, failed/blocked/unknown review, unsafe path, or indeterminate
  dependency is `blocked` and manual-only.
- A completed or blocked preview has no executable action and cannot be
  confirmed into a fallback stage.
- A confirmed report-write failure does not remove or compensate for artifacts
  already produced by the one attempted stage.
- Semantic review remains deterministic and ignores all semantic provider,
  endpoint, credential, model, and acknowledgement options.
- Bounded validation rejects unsafe common inputs and options relevant to the
  selected action before work begins. LLM-only options are ignored without
  validation for deterministic semantic review.

### Safety and Data Boundaries

- The workflow may inspect an approved podcast feed, local episode seed/audio,
  transcript metadata, deterministic artifacts, semantic summary metadata, and
  semantic review metadata. Output keeps these categories distinct and never
  treats external availability status as a market fact.
- Dry-run is strict zero-file: it may read the configured feed and safe local
  artifacts and compute fresh state in memory, but it creates, modifies, or
  deletes no file and calls no provider or stage executor.
- Confirmed execution is explicit, canonical-episode-specific, and limited to
  one approved action. Semantic summary is the only action that may send
  transcript text to an LLM and requires the exact API-cost acknowledgement
  before any provider-related work.
- `.env`, API keys, tokens, provider secrets, feed/source URLs,
  transcript or semantic bodies, prompts, raw responses, raw exceptions,
  endpoints, and tracebacks must not appear in reports, stdout, stderr, or MCP
  responses.
- The workflow never calls live market data, rebuilds the cache automatically,
  or emits buy/sell/hold guidance, target prices, guaranteed returns, or
  personalized investment advice.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST accept one podcast identifier and either `latest`
  or one explicit episode selector for dry-run preview.
- **FR-002**: The system MUST resolve the selector to at most one canonical
  episode reference and return that reference in a successful preview.
- **FR-003**: The system MUST select from the ordered states `intake`,
  `audio_download`, `local_transcription`, `deterministic_remediation`,
  `semantic_summary`, `semantic_review`, `completed`, and `blocked`
  without skipping forward.
- **FR-004**: A seeded preview MUST compute one fresh in-memory corpus index and
  one fresh remediation plan and reuse that same snapshot across deterministic
  and semantic classification.
- **FR-005**: Dry-run MUST create, modify, and delete zero files; MUST call zero
  stage executors, providers, environment loaders, and progress callbacks; and
  MUST expose bounded planned reads, planned writes, risks, blockers, and
  confirmation requirements.
- **FR-006**: Persisted index, plan, stage report, and workflow report files MUST
  NOT be treated as the authoritative next-action state during preview.
- **FR-007**: Confirmed execution MUST reject `action=next` and MUST require one
  explicit executable action.
- **FR-008**: Confirmed execution MUST reject `episode_ref=latest` and MUST
  require the canonical episode reference returned by preview.
- **FR-009**: Before dispatch, the system MUST recompute fresh state and reject
  the request if the selected action differs from the explicit approved action.
- **FR-010**: A valid confirmed request MUST attempt exactly one matching
  existing stage runner and stop, regardless of the stage outcome. The
  deterministic remediation stage MUST be bounded to one selected remediation
  row in that runner invocation.
- **FR-011**: Completed, blocked, invalid, drifted, or otherwise non-executable
  states MUST invoke no stage runner.
- **FR-012**: Confirmed semantic summary MUST validate the exact API-cost
  acknowledgement before feed, snapshot, profile, environment, credential,
  provider, executor, progress, or report-writer work.
- **FR-013**: Semantic review MUST remain local and deterministic. LLM-only
  provider, model, endpoint, credential, chunk, and acknowledgement options
  MUST be ignored without resolution or validation; only common
  podcast/episode/action inputs are validated for this action.
- **FR-014**: Snapshot, selector, stage, and report failures MUST fail closed;
  contained outputs MUST expose only safe fixed reasons or exception categories.
- **FR-015**: A confirmed request that passes early validation and fresh
  action-equality checks and then attempts one stage runner MUST write a latest
  JSON and Markdown workflow report for that bounded stage outcome using safe
  atomic replacement. Early-invalid, terminal, or drift-rejected requests MUST
  write zero files. Reports MUST NOT include a generated timestamp or unsafe
  content.
- **FR-016**: A report-write failure MUST remain an uncontained safe command
  error and MUST NOT trigger cleanup, retry, fallback, or compensating actions.
- **FR-017**: The system MUST provide an additive public Core entry point and a
  thin command-line entry point without changing existing 013–015 public
  contracts or standalone behavior.
- **FR-018**: The stdio MCP server MUST expose exactly one new reviewed tool
  named `run_corpus_episode_completion_workflow`, resulting in an exact registry
  of 13 tools while preserving the prior 12 tools and their contracts.
- **FR-019**: The new MCP tool MUST preserve the established success, dry-run,
  and safe error envelope forms and expose only bounded non-secret request and
  result fields.
- **FR-020**: A portable `corpus-episode-completion` Agent Skill MUST require
  the ordered protocol preview → explain → ask → wait → confirm exact action →
  report → stop. For semantic summary, the human MUST provide the exact
  acknowledgement text; the agent MUST NOT synthesize or substitute it.
- **FR-021**: The skill MUST treat missing, ambiguous, or negative approval as
  no approval and MUST NOT fall back to terminal, CLI, another side-effect tool,
  scheduler, retry, or autonomous loop when the MCP tool is unavailable.
- **FR-022**: The workflow MUST NOT provide batch, latest-N, scheduler, retry,
  force, partial semantic work, transcript repair, full-chain automation,
  remote MCP hosting, or live market data. It MUST perform no extra or
  post-stage index/plan refresh and no automatic cache rebuild; unchanged
  confirmed 010-012 runners MUST retain their established pre-execution 008/009
  refresh.
- **FR-023**: Reports and interface output MUST NOT disclose feed/source URLs,
  endpoint/base URLs, query strings, transcript/evidence/semantic/prompt/provider
  bodies, secret values, raw exception messages, or traceback bodies.
- **FR-024**: All outputs MUST retain `not_investment_advice=true` and MUST NOT
  contain investment recommendations, target prices, guaranteed returns, or
  personalized advice.
- **FR-025**: Codex MUST be validated for safe skill/tool discovery and dry-run
  selection; Hermes Agent and OpenClaw client-specific setup and live validation
  MUST remain outside 016.
- **FR-026**: Preview and confirmed execution MUST validate semantic provider, model, base URL, credential-variable name, chunk duration, and segment cap whenever fresh selection actually chooses `semantic_summary`, including `action=next` preview after fresh selection. Invalid selected-action settings are rejected before report writes, provider construction, or child dispatch; preview metadata reflects the same effective selected action and validated options.
- **FR-027**: A confirmed outcome MUST retain the selected child row's safe report paths, safe warnings, and category-only failure classification, plus safe top-level child JSON/Markdown report paths and warnings. It MUST deduplicate safe local report paths and MUST omit raw child exception messages, unsafe paths, URI data, and credentials.

### Key Entities

- **Completion Workflow Request**: Podcast id, requested episode selector,
  canonical episode reference, requested action, confirmation state, bounded
  transcription and semantic options, and acknowledgement presence.
- **Completion Snapshot**: One fresh in-memory index and plan view used to
  classify a seeded episode without persisting planning artifacts.
- **Completion Selection**: The selected action or terminal state, fixed reason,
  manual-only flag, planned reads/writes, risks, warnings, and confirmation
  requirement.
- **Completion Outcome**: One bounded record of the attempted action or terminal
  state, including safe status and counts but no raw content.
- **Completion Workflow Report**: Confirmed-only latest JSON/Markdown metadata
  describing the selection and one attempted outcome.
- **Agent Approval Protocol**: The portable conversation sequence that connects
  a dry-run result to one human-approved confirmed MCP call.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All seven executable/terminal ladder positions and blocked states
  produce the specified deterministic next action or terminal outcome in
  repeatable acceptance tests.
- **SC-002**: In 100% of dry-run acceptance cases, before/after tree manifests
  including path, hash, size, and modification time are identical and no stage,
  provider, environment loader, writer, or progress callback is invoked.
- **SC-003**: In 100% of confirmed acceptance cases, no more than one matching
  stage runner is attempted, deterministic remediation selects at most one
  remediation row, and no fallback or second workflow action occurs.
- **SC-004**: Every stale-action or non-canonical confirmed request is rejected
  before a stage executor or report writer is called.
- **SC-005**: Every missing or incorrect semantic acknowledgement is rejected
  before any feed, snapshot, profile, environment, credential, provider,
  executor, progress, or writer activity.
- **SC-006**: The MCP registry contains exactly 13 reviewed tools and all prior
  12 tool contract regression checks remain passing.
- **SC-007**: Adversarial no-leak checks find zero instances of secrets, URLs,
  transcript/semantic/prompt/provider bodies, raw exceptions, or tracebacks in
  reports and interface output.
- **SC-008**: The portable skill passes structural and protocol validation, and
  a fresh Codex smoke selects only the `confirm=false` tool path with a bounded
  early-validation rejection, without RSS/corpus/provider/writer work,
  confirmed action, or fallback command.
- **SC-009**: All targeted 013–016, MCP, skill, acknowledgement, secret, cache,
  and governance checks pass, followed by the repository's full test and source
  compilation gates.

## Assumptions

- Existing 008/009 in-memory builders and 013–015 public stage runners remain
  the authoritative implementation dependencies and retain their contracts.
- The local MCP transport remains stdio and credentials, when needed for a
  confirmed semantic summary, are supplied to the server process environment.
- The operator can copy the canonical episode reference and explicit action
  from preview into the confirmation request.
- Standards-compatible clients may mount the MCP server and skill, but 016 only
  validates Codex and does not claim Hermes Agent or OpenClaw installation
  compatibility beyond the portable formats.
- A future autonomous mode requires a separate approved feature and cannot
  weaken this feature's single-action contract.
