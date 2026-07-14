# Feature Specification: Corpus Semantic Remediation Runner

**Feature Branch**: `015-corpus-semantic-remediation-runner`

**Created**: 2026-07-12

**Status**: Implemented

**Input**: User description: "Create a standalone, single-episode corpus semantic remediation runner. Dry-run must be strict zero-file. Confirmed execution must explicitly select one semantic summary or semantic review action, preserve exact LLM acknowledgement and secret boundaries, and must not integrate with 010, 014, MCP, automatic cache rebuild, batch, scheduler, retry, or full-chain automation."

## Clarifications

### Session 2026-07-12

- Q: How must confirmed execution identify work? → A: Dry-run may select `next`, but confirmed execution must explicitly name `semantic_summary` or `semantic_review`.
- Q: Which episode selectors are allowed? → A: Both dry-run and confirmed execution require one explicit canonical episode reference; `latest` is rejected.
- Q: May dry-run refresh persisted index or plan artifacts? → A: No. Dry-run creates, modifies, or deletes zero files and evaluates one fresh in-memory corpus snapshot.
- Q: What happens when an existing semantic review is failed, blocked, or unreadable? → A: The runner fails closed with blocked/manual-only guidance and does not regenerate or rerun it.
- Q: How broad is v1 integration? → A: The runner is standalone Core+CLI only, exposes a safe subset of existing semantic configuration, and does not change 010, 014, or MCP.
- Q: May dry-run resolve LLM profiles or local environment configuration? → A: No. Every dry-run bypasses profile, `.env`, credential, and provider resolution because semantic state selection requires none of them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview the Next Semantic Action (Priority: P1)

A local operator wants to inspect one explicit episode and learn whether semantic summary generation, deterministic semantic review, no further work, or manual intervention is appropriate without changing any file or contacting an LLM provider.

**Why this priority**: Safe preview is the minimum useful capability and is required before any transcript transfer, provider construction, or cost-bearing execution.

**Independent Test**: A fixture corpus covering valid and invalid transcript, summary, and review states returns one bounded decision while a complete before/after file-tree manifest remains identical and all provider, environment-loader, writer, and executor call counts remain zero.

**Acceptance Scenarios**:

1. **Given** a valid transcript and no semantic summary, **When** the operator previews the explicit episode, **Then** the selected action is `semantic_summary`, the result states that exact cost acknowledgement is required, and no file or provider state changes.
2. **Given** a semantic summary and no semantic review, **When** the operator previews the episode, **Then** the selected action is `semantic_review` and the result states that the action is deterministic and does not require LLM acknowledgement.
3. **Given** a passed semantic review, **When** the operator previews the episode, **Then** the result is completed with no executable action.
4. **Given** an unusable transcript, unreadable summary, or failed, blocked, or unreadable review, **When** the operator previews the episode, **Then** the result is blocked/manual-only and no alternative action is selected.
5. **Given** an explicit dry-run action that differs from the freshly selected executable action, **When** the operator previews the episode, **Then** the row is `rejected`, the actual `selected_action` remains visible, and no executor or writer is called.

---

### User Story 2 - Generate One Confirmed Semantic Summary (Priority: P2)

A local operator wants to explicitly confirm semantic summary generation for one canonical episode after inspecting the planned transcript transfer and cost risk.

**Why this priority**: Semantic summary fills the first gated semantic artifact gap but sends transcript content outside the machine and may incur cost, so it requires the strongest confirmation boundary.

**Independent Test**: With a valid transcript, a missing semantic summary, an exact acknowledgement, and a controlled provider double, one semantic summary is produced, one latest runner report is written, no review is executed, and no unsafe body or secret content appears in output.

**Acceptance Scenarios**:

1. **Given** the current selected action is `semantic_summary`, **When** the operator confirms that exact action with the required acknowledgement, **Then** the existing semantic summary capability is invoked exactly once and the runner stops.
2. **Given** a missing or incorrect acknowledgement, **When** semantic summary confirmation is requested, **Then** execution is rejected before profile, local environment, credential, or provider resolution and no file is written.
3. **Given** the corpus state changed after preview, **When** the operator confirms `semantic_summary` but it is no longer the selected action, **Then** the attempt is rejected and the runner does not execute a different action.
4. **Given** a provider or summary-write failure after a valid confirmation, **When** execution stops, **Then** the latest runner report records a category-only failed outcome without raw diagnostic content.

---

### User Story 3 - Run One Confirmed Semantic Review (Priority: P3)

A local operator wants to explicitly run the existing deterministic semantic review for one episode whose semantic summary exists but has no review.

**Why this priority**: Review completes the semantic safety gate without another LLM call, but it must remain separate from summary generation so one confirmation never chains multiple writes.

**Independent Test**: With an existing local semantic summary and no review, one deterministic review invocation writes its existing timestamped review pair plus one latest runner report, while provider and local-environment access remain unused.

**Acceptance Scenarios**:

1. **Given** the selected action is `semantic_review`, **When** the operator confirms that exact action, **Then** the existing deterministic review capability is invoked exactly once and the runner stops.
2. **Given** review confirmation, **When** the request includes no LLM acknowledgement, **Then** the review may proceed because it does not construct a provider or transfer transcript content.
3. **Given** the summary is no longer available or a terminal review now exists, **When** the operator confirms review, **Then** the attempt is rejected or blocked without summary generation or another fallback action.
4. **Given** the review result is failed or blocked, **When** the runner reports the outcome, **Then** it preserves the terminal status and does not automatically retry, regenerate the summary, or invoke an LLM.

### Edge Cases

- Blank episode references, `latest`, path-like references, URL-like references, and unsupported action names are rejected before corpus evaluation.
- Confirmed execution with `action=next` is rejected before any file or external state change.
- Another episode's missing, failed, or blocked semantic artifacts cannot affect the requested episode's decision.
- A valid canonical episode reference absent from the fresh snapshot produces `blocked`/manual-only. Dry-run has null report paths; a validated confirmed request writes the bounded blocked latest report and uses structured exit code 0.
- Any present semantic review status other than exact `passed` is fail-closed unless its artifact status is exactly `missing`; missing selects review, while `available`, blank/defaulted, warning, arbitrary, failed, blocked, or unreadable states are blocked/manual-only.
- A missing, empty, partial, corrupt, or unreadable transcript is blocked even if the underlying semantic capability could otherwise create or reuse an artifact.
- An unreadable semantic summary is blocked rather than treated as a safe regeneration request because v1 does not support force overwrite.
- Existing failed, blocked, or unreadable review artifacts are terminal/manual-only; duplicate timestamped review candidates use the existing latest-review discovery contract.
- If a semantic summary appears between snapshot selection and execution, the underlying executor may report reuse; the runner records reuse and still stops after that one call.
- If review report writing partially fails, the runner records a bounded failed outcome and does not attempt cleanup beyond the existing review capability's contract.
- Snapshot exceptions map deterministically to `selected_action=blocked`, row `action=blocked`, row `status=failed`, and `manual_only=true`, with only the exception category. Dry-run report paths remain null; a validated confirmed attempt writes the bounded latest report.
- Snapshot, provider, summary, and review exceptions expose only safe exception categories in runner-owned results, reports, stdout, and stderr.
- If runner-report writing fails after a semantic artifact was created, the CLI returns a safe non-zero system error; no fallback, cleanup, retry, or claim of transactional JSON/Markdown pair success is made.
- Safe local paths may contain supported CJK components; URLs, query strings, fragments, traversal, UNC paths, control characters, and unsafe path components are omitted.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- The feature reads local corpus artifact metadata; during snapshot evaluation it may perform a bounded UTF-8 readability check of an existing semantic summary without returning its body. It reads a local transcript only during confirmed semantic summary execution, reads the existing semantic summary body only during confirmed review, and reads non-secret provider/profile configuration only when required.
- Dry-run is strict zero-file: it must not create, modify, delete, allocate, or persist index, plan, summary, review, runner-report, cache, or `.part` artifacts.
- Semantic summary is the only LLM action. It may transfer transcript content and incur cost only after explicit action confirmation and exact `api_cost_ack`, validated before local environment or provider resolution.
- Semantic review is deterministic and must not read `.env`, resolve credentials, construct a provider, or require LLM acknowledgement.
- Runtime may load local environment configuration only for confirmed semantic summary after exact acknowledgement. Secret values must never appear in artifacts, stdout, stderr, warnings, or exceptions.
- Outputs contain metadata, safe paths, counts, statuses, risk flags, provider/model identifiers, and category-only failures. They exclude raw transcript, evidence snippets, semantic body text, prompts, raw provider responses, base URLs, URL queries, secret values, and traceback bodies.
- The feature adds no live market data and must not reinterpret external-data boundary/status values as market facts.
- The feature adds no MCP tool and preserves the reviewed exact 12-tool registry and response envelopes.
- The feature does not call 010 or 014, rebuild SQLite cache, persist refreshed 008/009 artifacts, execute stock-lens work, or chain semantic summary into review.
- The generated output must not contain buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or language implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a standalone single-episode semantic remediation entry point for one podcast and one explicit canonical episode reference.
- **FR-002**: The system MUST reject blank, `latest`, path-like, URL-like, or otherwise unsafe episode references.
- **FR-003**: Dry-run MUST accept only `next`, `semantic_summary`, or `semantic_review` as action values; an explicit dry-run action mismatch MUST return a `rejected` row while retaining the fresh `selected_action`; confirmed execution MUST reject `next` and require one explicit semantic action.
- **FR-004**: Every valid request that passes input validation and, for confirmed summary, exact acknowledgement validation MUST derive the requested episode's state from exactly one fresh in-memory corpus index and remediation-plan snapshot and MUST isolate the requested episode before classifying any state.
- **FR-005**: Dry-run MUST create, modify, or delete zero files and MUST call zero persisters, provider constructors, environment loaders, semantic executors, review executors, and execution progress callbacks.
- **FR-006**: A valid transcript with a missing semantic summary MUST select `semantic_summary`.
- **FR-007**: An available semantic summary with a missing semantic review MUST select `semantic_review`.
- **FR-008**: A passed semantic review MUST produce a completed outcome with no executable action.
- **FR-009**: A requested episode absent from the fresh snapshot; missing, empty, partial, corrupt, or unreadable transcript state; unreadable semantic summary state; and every present semantic review state other than exact `passed` MUST produce blocked/manual-only outcomes. Exact missing review state remains actionable as `semantic_review`.
- **FR-010**: Confirmed execution MUST recompute fresh state and reject an explicit action that is no longer selected without executing a fallback action.
- **FR-011**: Confirmed execution MUST dispatch at most one existing semantic summary or semantic review capability and MUST stop after that attempt regardless of executed, reused, failed, rejected, or blocked outcome.
- **FR-012**: Confirmed semantic summary MUST require the exact acknowledgement before profile, local environment, credential, or provider resolution and MUST pass only the supported provider, model, endpoint, credential-variable-name, and chunking options.
- **FR-013**: V1 MUST NOT expose force overwrite or partial-transcript execution.
- **FR-014**: Confirmed semantic review MUST NOT require LLM acknowledgement and MUST NOT access profile, local environment, credentials, provider construction, or provider calls.
- **FR-015**: The system MUST write the latest semantic remediation runner JSON and Markdown reports only after a validated confirmed attempt; dry-run and invalid acknowledgement/input MUST write no runner report.
- **FR-016**: The runner report MUST record requested and selected action, outcome, safe planned reads and writes, safe output and source-report paths, counts, warnings, acknowledgement requirement, risk flags, and provider/model metadata when applicable.
- **FR-017**: Runner-owned JSON, Markdown, stdout, and stderr MUST omit unsafe source bodies, raw transcript/evidence/semantic/prompt/provider content, raw base URLs, query strings, fragments, secret values, and traceback bodies.
- **FR-018**: Runner-owned exceptions and failed outcomes MUST expose safe exception categories only; snapshot failure MUST map to blocked/failed/manual-only with dry-run report paths null and validated confirmed report paths populated.
- **FR-019**: The system MUST preserve the existing timestamped semantic review artifact contract and MUST NOT add a generation timestamp to the latest runner report schema.
- **FR-020**: The system MUST warn that derived corpus index/plan and SQLite cache metadata may be stale after confirmed writes and MUST NOT refresh or rebuild them automatically.
- **FR-021**: The system MUST preserve existing 010 and 014 behavior and MUST NOT add, remove, or change MCP tools or response envelopes.
- **FR-022**: The system MUST provide a thin local command surface with explicit podcast, episode, action, confirmation, acknowledgement, safe provider/profile, and chunking inputs.
- **FR-023**: Structured dry-run, selected, executed, reused, completed, blocked, rejected, and runner-contained failed outcomes MUST use exit code 0; invalid input, invalid acknowledgement, runner-report write failure, or other uncontained system command errors MUST use a non-zero exit code.
- **FR-024**: The feature MUST NOT add batch, scheduling, retry, full-chain automation, automatic review, stock-lens continuation, live market data, or investment-advice behavior.

### Key Entities

- **Semantic Remediation Request**: One requested podcast, canonical episode, action, confirmation mode, acknowledgement state, and non-secret semantic configuration.
- **Semantic Remediation Decision**: The selected action or terminal state derived from one in-memory corpus snapshot for the requested episode.
- **Semantic Remediation Outcome**: One selected, executed, reused, completed, blocked, rejected, or failed action result with metadata-only audit fields.
- **Semantic Remediation Run Report**: Confirmed-only latest JSON and Markdown audit artifacts for the attempted action.
- **Semantic Summary Artifact**: Existing per-episode semantic Markdown output created by the established semantic summary capability.
- **Semantic Review Artifact**: Existing timestamped JSON and Markdown review output created by the established deterministic semantic review capability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across every defined dry-run corpus state, before/after manifests are identical and all file-writer, environment-loader, provider, executor, and progress-callback counts are zero.
- **SC-002**: The requested episode receives the correct next action or terminal state in 100% of the specified transcript, summary, and review state-table scenarios, including multi-episode fixtures.
- **SC-003**: Every confirmed test case invokes no more than one semantic executor and invokes zero non-selected or fallback executors.
- **SC-004**: Missing or incorrect acknowledgement produces zero profile, local-environment, credential, provider, executor, report-writer, and artifact-writer calls.
- **SC-005**: Confirmed review test cases produce zero LLM profile, local-environment, credential, provider-construction, and provider-call activity.
- **SC-006**: Adversarial JSON, Markdown, stdout, and stderr tests contain zero raw transcript, semantic body, prompt, raw provider response, raw endpoint, secret, traceback, or prohibited investment-advice content.
- **SC-007**: Existing 010 and 014 contract suites, exact 12-tool MCP registry guards, manual-cache-rebuild guards, provider-factory guards, and repository secret-boundary guards continue to pass unchanged.
- **SC-008**: The complete targeted and repository-wide verification commands pass before all tasks are marked complete and the feature status changes from Draft to Implemented.

## Assumptions

- A local operator already has one explicit canonical episode reference and uses 014 or other existing commands separately for intake, download, transcription, and deterministic remediation.
- Existing corpus index and remediation planning metadata remain the authoritative semantic-state inputs, but 015 evaluates fresh in-memory snapshots rather than persisted copies.
- Existing semantic summary and semantic review capabilities remain the owners of their output artifact formats and execution behavior.
- Dry-run and confirmed review bypass LLM profile and local environment resolution entirely. Only confirmed semantic summary may resolve non-secret profile configuration or local environment values, and only after exact acknowledgement.
- Review freshness relative to a later summary modification is outside v1; the latest existing review artifact remains authoritative.
- No dependency, migration, live provider, MCP exposure, or existing artifact migration is required.
