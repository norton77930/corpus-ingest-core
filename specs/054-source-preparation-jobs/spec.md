# Feature Specification: Source preparation jobs

**Feature Branch**: None; existing workspace, no Git objects authorized.
**Created**: 2026-10-06
**Status**: Implemented; offline-verified.
**Input**: User approved the proposed single-source preparation entry and progress management for Hermes users. People should be able to supply a source before manually downloading or transcribing it. Question answering and LLM-generated learning documents remain a later phase.

## User Scenarios & Testing

### US1 - Understand what one source needs (P1)

An operator supplies one YouTube or X video URL. The system identifies the source, checks configuration and existing artifacts, then explains the work needed without starting it.

**Why this priority**: Prevents the operator needing to understand download/transcription tools and avoids misleading recovery errors for missing configuration.
**Independent Test**: Synthetic source metadata and owned local artifacts demonstrate each preparation decision without writes or downloads.

**Acceptance Scenarios**:
1. With a registered compatible source and no transcript, preview identifies the target, planned download/transcription/validation, file effects and local-compute/network risks.
2. With a validated complete canonical transcript, preview reports transcript readiness without starting a job or claiming learning notes exist.
3. With missing registration, incompatible source type, unsafe paths or partial artifacts, preview returns a specific actionable blocker and performs no repair.

### US2 - Start once and return to the conversation (P1)

After seeing and approving a preparation plan, the operator starts one background job and receives a durable reference instead of waiting for the full transcription inside a tool call.

**Why this priority**: Transcription may take substantial time; the conversation should not be the owner of the work.
**Independent Test**: Owned fake acquisition/transcription plus a real temporary worker process, admission races and injected startup failure.

**Acceptance Scenarios**:
1. Approval matching the displayed source and plan submits one job; the acknowledgment does not wait for media processing.
2. Repeated submission of the same active source returns its existing job; another source is refused while the one-source capacity is occupied.
3. Changed identity, configuration or file plan invalidates approval before admission and worker launch.

### US3 - See progress and distinguish outcomes (P1)

The operator asks for progress using a job reference, including in a later conversation. The answer distinguishes actual processing, validated readiness, ordinary failure and uncertain partial work.

**Why this priority**: Missing responses and failed reports must not cause a duplicate download or transcription.
**Independent Test**: Persisted fixture records and process lifecycle tests, with no external network or production corpus changes.

**Acceptance Scenarios**:
1. Status reports the last observed stage and timestamps; it does not invent percentages, completion times or content answers.
2. Readiness requires validating the expected transcript artifacts and identity; a successful download alone is insufficient.
3. Interrupted, unresponsive or ambiguous work requires attention; status polling never repairs, launches or retries it.

### US4 - Use the preparation entry from Hermes (P2)

An operator can say “prepare this video so I can ask questions about it.” Hermes explains the plan, obtains approval, starts once and reports progress through the supported tools.

**Why this priority**: Portable instruction routing must match the backend's actual contract, not promise a complete learning or Q&A pipeline.
**Independent Test**: Offline dialogue contracts, actual owned SDK HTTP submit/disconnect/status and the Windows stdio admission blocker; an actual Hermes-host check is separately labelled and requires the operator's environment.

**Acceptance Scenarios**:
1. The initial natural-language request triggers preview only; denial, silence or ambiguous approval starts nothing.
2. A missing mounted tool is a setup problem; the Skill does not use terminal or another executor as a fallback.
3. When preparation finishes, the response says the transcript is ready and stops; question answering, semantic summary and lecture generation are not automatically invoked.

### Edge Cases

Unsupported URLs, non-video posts, source metadata unavailable, missing profile, incorrect source type, identity drift, incomplete transcript sets, blocked managed paths, concurrent submissions, existing failed jobs with possible partial files, capacity exhaustion, worker launch failure, worker disappearance, status store failure, artifact/report failure after partial writes, malformed replies and unknown job references. A previously ready job is an observation with a verification time, not a guarantee that files or remote source content never changed.

### Safety and Data Boundaries

Preview may resolve public source metadata over the network; zero-write does not mean zero-network. Confirmed work downloads public source media, transcribes locally and writes only declared artifacts plus job metadata. No LLM, semantic summary, learning-note/lecture generation, raw content answers or automatic cache rebuild. No `.env` or provider configuration access. No secrets, raw transcript bodies, arbitrary exception text or full configuration in responses or job records. No live market API or investment advice. No automatic retry, cleanup, rollback, profile mutation or forced overwrite. Existing workflows and Skills retain their independent consent protocols.

## Requirements

### Functional Requirements

- **FR-001**: Accept one supported YouTube or X video URL and resolve an explicit canonical source/episode identity; reject unsupported, ambiguous or unsafe requests before artifact access.
- **FR-002**: Identify the selected local source registry and data context internally, check required registration and source-type compatibility, and return specific setup blockers without exposing settings or changing profiles.
- **FR-003**: Inspect existing canonical artifacts; distinguish missing audio, reusable audio, complete validated transcript, partial/unsafe/unavailable artifacts and incompatible configuration. Unknown inspection is never absence.
- **FR-004**: Preview lists reads, artifact/job/report writes, reused files, planned stages and network/local-compute risks; preview writes nothing and launches no worker.
- **FR-005**: Require approval after preview, bound to the same canonical source and displayed plan. Detected identity, configuration or plan drift stops before job admission; this binding is not a content snapshot or lock.
- **FR-006**: After valid confirmation, durably record one job and return its reference without waiting for acquisition/transcription. Submission failures distinguish rejected work from an uncertain recorded/started job.
- **FR-007**: Coalesce submissions for the same active source and enforce one active source per selected data root; refuse a different source while busy. This is not a batch scheduler.
- **FR-008**: Worker lifetime is independent of a chat/tool connection. Execute only the admitted source with existing acquisition/transcription behavior and force disabled; never process another job automatically.
- **FR-009**: Persist finite truthful stages and verification timestamps. Status is bounded, read-only and offline, including for unknown or interrupted jobs; no invented percentages or ETA.
- **FR-010**: Mark transcript readiness only after the expected complete canonical transcript passes identity and validation checks. Always distinguish transcript readiness from study-guide readiness; finance sources are not silently converted to learning sources.
- **FR-011**: Preserve partial artifacts, history and uncertainty on failure, interruption or report failure. Never retry, repair, delete or declare rollback automatically; a later attempt requires inspection and fresh approval.
- **FR-012**: Keep request/record/status content bounded and metadata-only, reject hostile job references and unsafe stores, and return fixed safe reasons rather than raw exceptions, credentials, transcript content or settings.
- **FR-013**: Add one portable Hermes-compatible source-preparation Skill that routes preview, approval, one submission and explicit later status requests. It performs no polling loop, execution fallback or downstream learning/Q&A chain.
- **FR-014**: Preserve existing MCP tool names/order/signatures and default behavior. Expose preparation and status as additive Tools33/34 after runtime implementation. Existing Core ingestion gains only the approved optional keyword-only progress_callback=None; old callers retain their default behavior. The earlier design-only delivery registered no tools.
- **FR-015**: Use TDD, process/transport tests with owned temporary data and fake media executors, documentation guards, independent read-only review, full checks and converge before runtime completion claims. Distinguish local/offline evidence from actual Hermes-host evidence.
- **FR-016**: Retain all current secret, no-advice, no-market-API, preview-first and manual-cache boundaries. Do not call real external sources/providers or deploy a worker during planning/offline verification.

### Key Entities

- Preparation intent: one source URL and a transcript-preparation goal, not a chat transcript or question-answering request.
- Preparation plan: resolved identity, observed local readiness, bounded file effects, stages, risks, blockers and an opaque approval binding.
- Preparation job: durable source/plan binding, status, owner and timing metadata, safe outcome, artifact-role references and verification time.
- Status observation: a bounded view of the job, reported stage and scoped readiness; it is not a live source or content-quality guarantee.

## Success Criteria

- **SC-001**: Every supported readiness/setup/partial-artifact fixture produces the intended decision, with zero preview writes or worker launches.
- **SC-002**: In controlled offline acceptance, submission acknowledgment finishes within 2 seconds after preflight/admission begins even when the fake executor is held; source-metadata resolution time is measured separately.
- **SC-003**: Concurrent duplicate submissions admit at most one active worker for that source; a different source cannot acquire the occupied execution slot.
- **SC-004**: A submitted owned-fixture job remains inspectable after the submitting client disconnects; successful completion reports a validated transcript, never generated learning notes.
- **SC-005**: Every injected interruption/partial-publication/store failure returns a bounded failure or attention outcome without retry, repair, cleanup or false readiness.
- **SC-006**: All recorded consent/setup/progress dialogue cases respect the declared call limits and expose no protected content.
- **SC-007**: Existing tool contracts and historical artifacts remain intact; all requirements have tasks and targeted/full verification evidence at runtime closeout.

## Assumptions and Clarifications

V1 is one configured YouTube/X source, one active job per data root, local acquisition/transcription and transcript readiness only. RSS/latest/batch/imported subtitles/automatic registration/cancellation/retry/scheduling/content questions/LLM-generated learning documents are out of scope. Operators configure missing source profiles through existing local-only setup; this entry diagnoses that prerequisite rather than editing it. Same-host MCP/worker is the planning default; the operator was asked whether Hermes and the worker share a host. Remote Hermes may connect through an already managed secure MCP connection, but exposing a remote listener or deployment is not authorized here. Existing study-guide files can exist even when the selected profile registry lacks their source; registry absence does not prove artifact absence. Constitution reviewed without amendment. Readiness denotes validation of local artifacts at a recorded time, not semantic accuracy or remote-source freshness.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
