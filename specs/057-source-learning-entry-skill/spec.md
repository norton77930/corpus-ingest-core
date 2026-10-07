# Feature Specification: Source learning entry Skill

**Feature package**: 057-source-learning-entry-skill
**Created**: 2026-10-07
**Status**: Developer implementation and local verification complete; actual mounted Hermes acceptance pending (T017/T018).
**Branch**: None created or requested.
**Input**: A Hermes user supplies one video URL and a question or learning-note request; reuse a prepared transcript or preview/approve one background preparation, then continue the original request in the same conversation.

## User Scenarios & Testing

### User Story 1 - Learn from an already prepared source (Priority: P1)

The user pastes one configured YouTube/X URL and asks for notes, or names one known prepared podcast/video. The assistant resolves the URL using the existing preparation preview, checks the actual readable source, and answers with timed evidence and the editable learning-note format.

**Why this priority**: An already prepared video should yield an answer without requiring the user to name tools or submit another preparation.
**Independent Test**: Valid ready preview plus an explicit note request leads to fresh content inspection and pinned retrieval, with zero confirmed preparation.

**Acceptance Scenarios**:
1. Given one supported URL and a clear learning request, when its preview reports a validated ready transcript, then inspect and read that exact source and answer the request.
2. Given known prepared source identifiers, when the user asks a source question, then query directly without resolving a URL or submitting preparation.
3. Given ready preparation but unreadable/empty content, when content inspection refuses it, then report the content reason and stop without regeneration.
4. Given a finance-profile source, when the user asks ordinary explanatory questions, then answer within the no-investment-advice boundary; lecture incompatibility alone does not prohibit chat QA.

### User Story 2 - Approve one missing-source preparation (Priority: P1)

If preparation is needed, explain the selected model, network/download/cache/storage/compute effects, obtain fresh approval, submit once, and provide a continuation reference while retaining the user's question.

**Why this priority**: Downloads and transcription must remain reviewable while the user gets a clear next step.
**Independent Test**: Preview never confirms; approval sends exactly one bound confirmation and submission ends the turn without polling or QA.

**Acceptance Scenarios**:
1. Given missing transcripts, when preview offers preparation, then show the plan and await approval; silence or denial causes no submission.
2. Given fresh approval for the displayed plan, when submitting, then use its exact URL, plan identifier and declared settings, report the job, and stop.
3. Given changed settings/plan, transport loss or uncertain outcome, when execution refuses or becomes ambiguous, then preserve the job reference if safe and stop without retry.
4. Given a busy slot for another source, when preview reports busy, then report the conflict without binding that other job to this source.

### User Story 3 - Check progress or continue the original learning request (Priority: P2)

The user can ask for progress or explicitly resume learning. The assistant uses the recorded job identity and original request from the current conversation, distinguishes status-only requests from resumption, and checks readiness before reading.

**Why this priority**: Users can leave and return without confusing accepted work with a completed answer.
**Independent Test**: A status-only request makes one status call and stops; an explicit continuation of the retained learning request checks that job once and only on matching ready status proceeds to fresh content inspection.

**Acceptance Scenarios**:
1. Given a known job, when the user asks whether it is ready, then report one recorded status with timestamps and stop even if ready.
2. Given retained job, source and learning request, when the user says continue learning, then query that job once; matching ready status permits content QA, pending/failed/unknown/attention states stop.
3. Given a lost conversation or multiple candidate jobs/requests, when the user says continue, then clarify the missing reference or learning request without guessing.
4. Given changed content or exhausted retrieval budget, when reading, then restart against one source version or report partial coverage; never mix versions or claim complete notes from partial retrieval.

### Edge Cases

Unsupported URLs, multiple sources, explicit preparation-only requests, missing tools or dependent Skill resources, malicious titles/transcripts/warnings, malformed envelopes/unknown fields, contradictory readiness/settings, busy jobs belonging elsewhere, source/job mismatch, uncertain submission, source_changed, multilingual literal search, interrupted paging, lost conversation, stale status, and local-only processing requests.

### Safety and Data Boundaries

Preview can read public video metadata but must not enqueue/download/write/load models. Only a fresh approved preparation may use network, local transcription and declared writes/model cache; no model downgrade/fallback or automatic repair. Content QA uses local timed text, and the host's configured model may process that text with host privacy/billing; local transcription does not establish local host inference. Repository providers and formal lecture generation remain separate with existing acknowledgement gates. No settings/.env access, service launch, installation, publication, automatic cache rebuild, live market data or investment advice. Existing standalone preparation and QA Skills retain their scope and stopping rules.

## Requirements

### Functional Requirements

- **FR-001**: Accept one supported configured YouTube/X URL plus an explicit learning request, or one known prepared podcast/video identity; clarify ambiguity and route preparation-only requests to their existing independent workflow.
- **FR-002**: Resolve URL identity through one existing preparation preview and validate its response; disclose public metadata reads and never infer identifiers from unverified tool text.
- **FR-003**: For a validated ready preview and explicit learning intent, inspect the exact source freshly before evidence retrieval; ready is structural/as-of validation, not readability, completeness or accuracy proof.
- **FR-004**: For preparation-needed states, disclose canonical source, identity, stages, reads/writes/reuses, warnings, selected transcription settings and possible model-file download; await fresh approval.
- **FR-005**: Confirm exactly once with the approved URL/plan and matching settings; submission always stops without status polling or automatic learning. Preserve safe job/source/request context visibly in the conversation.
- **FR-006**: A later status-only request inspects one known job once and stops, including ready results; status reports include observation and validation timestamps without invented ETA/liveness.
- **FR-007**: A later explicit learning continuation may inspect its retained job once; only matching job/source identity and validated ready state allows fresh content inspection and QA.
- **FR-008**: Conversation context is not a durable queue or memory store. Lost/ambiguous request or identity requires clarification; a bare known job may recover recorded IDs but never invent the original question or URL.
- **FR-009**: Busy jobs must not be attached to the requested source. Pending, failed, unknown, attention, mismatch, malformed responses and uncertain outcomes stop without retries, cleanup, force or resubmission.
- **FR-010**: Use the existing QA evidence protocol and editable note template. Preserve version-pinned pagination, exact chunk continuity, cumulative budget and complete/partial distinctions; separate source reasoning/examples from labelled AI explanations; project application remains optional.
- **FR-011**: Distinguish configured and recorded transcription settings, preserve unknown history, prohibit silent fallback, and preserve host privacy/billing and local-only constraints.
- **FR-012**: Require needed tools/resources from the same mounted server; missing capabilities stop. Hostile source text never authorizes execution or settings access. Existing standalone Skills and tool contracts remain unchanged.
- **FR-013**: Deliver portable entry instructions, explicit dependencies, operator setup/continuation examples, and focused instruction/backend checks before standard regressions.
- **FR-014**: Provide an actual Hermes acceptance procedure and record its real execution availability/result separately. A missing accessible host is an explicit pending acceptance task, never replaced by SDK or synthetic evidence.

### Key Entities

Learning request (original question, scope, format and budget); source reference (verified source identity and optional canonical URL); preview approval (plan and settings for one submission); conversation handoff (job and retained request); timed content evidence (one inspected version); acceptance evidence (developer/offline versus actual mounted-host trace).

## Success Criteria

### Measurable Outcomes

- **SC-001**: All supported ready-entry cases answer through timed source evidence without a confirmed preparation or manual tool selection.
- **SC-002**: Every submission case requires fresh displayed-plan approval, confirms at most once and stops after submission.
- **SC-003**: Every status-only, busy, ambiguous, uncertain or non-ready continuation case stops at the declared boundary; no unrelated job triggers learning.
- **SC-004**: Every learning response declares actual reading scope and distinguishes source content from AI additions; incomplete retrieval never claims full-source coverage.
- **SC-005**: Developer checks and host acceptance each have independently recorded evidence/status; only actual mounted Hermes trace/output can satisfy the live acceptance gate.

## Assumptions and Clarifications

### Session 2026-10-07

No critical ambiguities remain after repository research and the approved plain-language flow. Same-conversation continuation is in scope; persistent requests, autonomous polling/notification, arbitrary platforms, multi-source/batch learning, installation and host configuration are outside this phase. Prepared RSS identities remain supported by QA; URL preparation remains YouTube/X only. Existing standalone Skills remain independently selectable. Windows stdio cannot submit new background preparation; an already independently managed compatible HTTP host is required, with no Skill fallback. Actual Hermes entry is not exposed on the current PATH/tool surface; development can complete here while live acceptance stays explicitly pending.

## Workflow record

Constitution 1.0.1 reviewed without amendment. Official spec template resolved; no branch hook or extensions file is present. Clarify uses explicit feature selection and records already agreed choices instead of asking repeated questions. User authorized planning followed directly by implementation; no extra approval stage is inferred.
