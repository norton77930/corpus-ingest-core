# Feature Specification: Corpus Local Transcription Runner

**Feature Branch**: `011-corpus-local-transcription-runner`

**Created**: 2026-07-09

**Status**: Implemented

**Input**: User description: "Create a dry-run-first local corpus transcription runner that builds on 008 corpus index and 009 corpus remediation plan. The runner refreshes the remediation plan, selects only episodes where local audio is available and transcript is fully missing, supports confirmed execution only for one explicit episode, calls the existing transcription capability with an explicit local audio path, writes latest deterministic run reports only after confirmed runs, and excludes download, corrupt/partial transcript repair, LLM, MCP, network, `.env`, cache rebuild, and investment advice behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Local Transcription Backlog (Priority: P1)

A local operator wants to see which episodes can safely be transcribed from already-downloaded local audio without downloading anything, loading transcription models, or writing new transcript outputs.

**Why this priority**: Preview is the minimum safe step before a long-running transcription side effect. It lets users inspect exactly which episodes are eligible, skipped, and blocked.

**Independent Test**: A local corpus with refreshed remediation metadata can produce a dry-run result listing eligible local-audio transcript gaps, skipped unsafe transcript states, and zero run report artifacts.

**Acceptance Scenarios**:

1. **Given** a podcast has at least one episode with local audio and no transcript outputs, **When** the user previews local transcription, **Then** the result marks that episode as selected and includes planned reads and planned writes.
2. **Given** a podcast has episodes with missing audio, existing transcript outputs, unreadable transcript metadata, or partial transcript outputs, **When** the user previews local transcription, **Then** those episodes are skipped with factual reasons and are not selected.
3. **Given** the user previews local transcription repeatedly over unchanged local artifacts, **When** the results are compared, **Then** the result content is deterministic and contains no generation timestamp.

---

### User Story 2 - Execute One Local Transcription (Priority: P2)

A local operator wants to confirm transcription for exactly one selected episode, using the already-downloaded local audio file, and receive an auditable run report.

**Why this priority**: Transcription is potentially long-running and resource-intensive. A one-episode confirmation guard keeps blast radius and runtime risk bounded.

**Independent Test**: A confirmed run with one selected episode transcribes only that episode through the local audio path, records transcript output paths, and writes deterministic JSON and Markdown run reports.

**Acceptance Scenarios**:

1. **Given** a user requests confirmed local transcription without an episode reference, **When** the runner is invoked, **Then** the run is rejected before any transcription work starts.
2. **Given** a user confirms local transcription for one selected episode, **When** the local audio path exists and transcript outputs are missing, **Then** only that episode is transcribed and the run report records executed or reused outcome metadata.
3. **Given** a user confirms local transcription for an episode that is not selected, **When** the runner is invoked, **Then** no transcription occurs and the run records a clear skipped or rejected outcome.

---

### User Story 3 - Contain Transcription Failures and Preserve Boundaries (Priority: P3)

A local operator wants a transcription failure to be recorded without leaking transcript text, secrets, stack traces, or weakening the no-download and no-LLM boundaries.

**Why this priority**: Transcription depends on local audio, runtime dependencies, and model loading. Failures must be auditable without hiding unsafe side effects.

**Independent Test**: A confirmed run with a transcription failure records the failure, writes only metadata and paths, does not download audio, does not call LLM or MCP surfaces, and does not expose raw transcript text or secret values.

**Acceptance Scenarios**:

1. **Given** the underlying transcription dependency fails, **When** confirmed local transcription runs, **Then** the failure is recorded with a bounded error category and no traceback body.
2. **Given** local source metadata contains transcript text, secret-like values, or unsafe prompt-like strings, **When** the run result is produced, **Then** JSON, Markdown, stdout, and stderr include only metadata, paths, counts, statuses, and warnings.
3. **Given** a selected episode has stale cache metadata after successful transcription, **When** the run report is produced, **Then** the report may warn that cache rebuild remains manual but must not rebuild the cache automatically.

### Edge Cases

- Empty local corpus produces a valid dry-run result with zero selected episodes and no run report artifact.
- An episode with local audio but unreadable, corrupt, partial, or incomplete transcript outputs is skipped rather than overwritten.
- An episode with local audio and a valid or empty existing transcript is skipped rather than re-transcribed.
- Confirmed execution without an episode reference is rejected before model loading or transcription starts.
- Confirmed execution for an episode not present in the refreshed remediation plan records no transcription work.
- A local audio path listed in metadata but missing on disk is skipped or failed for that episode only.
- Repeated dry-runs over unchanged local artifacts produce identical result content except transport formatting.
- Repeated confirmed runs over unchanged already-satisfied local artifacts produce deterministic report shape and mark reused or skipped outcomes rather than fabricating new work.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature reads local corpus remediation plan metadata, local corpus index metadata, and local audio path metadata only. It refreshes the 009 remediation plan before selecting transcript work.
- This feature's dry-run mode must not write transcript outputs, run report artifacts, or any downstream corpus artifacts; it returns planned reads, planned writes, selected/skipped counts, and warnings through local command output only.
- Confirmed execution may write transcript `.json`, `.txt`, and `.srt` outputs for exactly one selected episode and may write latest run report artifacts under `data/corpus/{podcast_id}/`.
- This feature must not download audio, read RSS, call network providers, call LLM providers, read `.env`, add MCP tools, invoke MCP tools, repair corrupt or partial transcript outputs, execute semantic summary or review, execute downstream remediation families, generate stock-lens artifacts, or rebuild SQLite cache.
- This feature must not add, remove, or change MCP tools or MCP response envelopes.
- This feature must not output raw transcript text, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated run output must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run local corpus transcription planning or execution for exactly one requested podcast identifier.
- **FR-002**: System MUST refresh the 009 corpus remediation plan before selecting transcription work for every run.
- **FR-003**: System MUST default to dry-run mode and MUST NOT write transcript outputs or run report artifacts in dry-run mode.
- **FR-004**: System MUST return dry-run selected, skipped, failed, and warning counts through local command output.
- **FR-005**: System MUST only select transcript remediation actions whose source status is `ready`, whose audio artifact is locally available, whose audio path exists, and whose transcript status is exactly `missing`.
- **FR-006**: System MUST skip missing-audio, unreadable transcript, corrupt transcript, partial transcript, incomplete transcript, existing valid transcript, existing empty transcript, semantic, deterministic downstream, stock-lens, synthesis, and unknown families with factual reasons.
- **FR-007**: System MUST reject confirmed execution unless exactly one episode reference is provided.
- **FR-008**: System MUST reject confirmed execution for an episode that is not selected by the refreshed local transcription criteria.
- **FR-009**: System MUST execute confirmed transcription by using the existing local transcription capability with the selected local audio path and without shelling out to local scripts.
- **FR-010**: System MUST NOT trigger audio download during local transcription selection or confirmed execution.
- **FR-011**: System MUST write `data/corpus/{podcast_id}/corpus-local-transcription-run.json` and `.md` only after confirmed execution is attempted.
- **FR-012**: System MUST keep run report content deterministic for unchanged local inputs and confirmed outcomes, including no generation timestamp.
- **FR-013**: System MUST record selected, executed, reused, failed, skipped, rejected, and warning counts in JSON, Markdown, and command output.
- **FR-014**: System MUST record per-episode outcome rows with podcast identifier, episode reference, source remediation action id when available, transcript status, audio path, planned reads, planned writes, output paths when available, outcome status, reason, and warnings.
- **FR-015**: System MUST contain single-episode transcription failures by recording the failed outcome and preserving all other dry-run row metadata.
- **FR-016**: System MUST provide a thin local command surface that can preview by podcast and confirmed-run by podcast plus one episode reference.
- **FR-017**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-018**: System MUST preserve no-leak boundaries for transcript text, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, and traceback bodies.
- **FR-019**: System MUST preserve no-investment-advice boundaries in all runner outputs.
- **FR-020**: System MUST leave SQLite cache rebuild as an explicit manual operation after confirmed transcription writes artifacts.

### Key Entities *(include if feature involves data)*

- **Corpus Local Transcription Run**: One dry-run or confirmed local transcription selection for one podcast. Key attributes include podcast identifier, mode, source remediation plan paths, filters, selected count, outcome counts, warnings, and run rows.
- **Local Transcription Row**: One selected, skipped, executed, reused, or failed transcript action derived from local corpus metadata. Key attributes include episode reference, source action id, transcript status, audio status, audio path, planned reads, planned writes, output paths, outcome status, reason, and warning messages.
- **Local Transcription Filter**: The bounded criteria applied before confirmed execution. Key attributes include optional episode reference and confirmation mode.
- **Local Transcription Warning**: A non-fatal warning associated with the run or a specific row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For an empty local corpus, users receive a dry-run result with zero selected episodes, zero executed episodes, and no run report artifact written.
- **SC-002**: For a remediation plan containing at least one eligible local-audio transcript gap and at least three ineligible transcript states, dry-run output identifies the eligible row and all ineligible rows with factual skipped reasons.
- **SC-003**: For confirmed execution without an episode reference, zero transcription work starts and the user receives a clear rejection.
- **SC-004**: For a confirmed run targeting one eligible episode, 100% of executed rows belong to that episode and use a local audio path from refreshed corpus metadata.
- **SC-005**: For a confirmed run where transcription fails, the failed outcome is recorded and no raw traceback body is exposed.
- **SC-006**: Generated run outputs contain zero raw transcript snippets, zero prompt text, zero raw LLM response text, zero secret values, and zero provider configuration values.
- **SC-007**: The existing MCP reviewed tool count and response envelope remain unchanged after the feature is delivered.
- **SC-008**: Dry-run and confirmed run reports over unchanged inputs contain no `generated_at` or equivalent generation timestamp field.

## Assumptions

- Package `009-corpus-remediation-plan` is available and remains the source of transcript action status, blocker status, and corpus metadata.
- Existing local audio artifacts were produced or placed outside this feature; this feature does not fetch or validate remote media.
- Existing corrupt, unreadable, partial, or incomplete transcript outputs may require future repair policy and are intentionally not overwritten in v1.
- Transcription may be long-running and resource-intensive, so v1 confirmed execution is limited to one episode per run.
- Cache rebuild remains manual after confirmed transcription writes artifacts.
