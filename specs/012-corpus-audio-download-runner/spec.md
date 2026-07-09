# Feature Specification: Corpus Audio Download Runner

**Feature Branch**: `012-corpus-audio-download-runner`

**Created**: 2026-07-09

**Status**: Draft

**Input**: User description: "Create a dry-run-first corpus audio download runner that builds on 008 corpus index and 009 corpus remediation plan. The runner previews episodes where audio is missing, supports confirmed execution only for one explicit episode, calls the existing audio download capability, writes latest deterministic run reports only after confirmed runs, and excludes transcription, LLM, MCP, cache rebuild, downstream remediation, source URL output, secret leakage, and investment advice behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Audio Download Backlog (Priority: P1)

A local operator wants to see which episodes are missing local audio and could be downloaded, without reading RSS feeds, calling network providers, downloading media, or writing run report artifacts.

**Why this priority**: Preview is the minimum safe step before a network side effect. It lets users inspect exactly which episodes are eligible, skipped, and blocked.

**Independent Test**: A local corpus with refreshed remediation metadata can produce a dry-run result listing eligible audio gaps, skipped unsafe states, and zero run report artifacts.

**Acceptance Scenarios**:

1. **Given** a podcast has at least one episode with missing local audio and a ready audio remediation action, **When** the user previews audio download work, **Then** the result marks that episode as selected and includes planned outcome metadata without source URLs.
2. **Given** a podcast has episodes with available audio, blocked audio actions, non-ready audio actions, transcript actions, semantic actions, or downstream remediation actions, **When** the user previews audio download work, **Then** those episodes or actions are skipped with factual reasons and are not selected.
3. **Given** the user previews audio download work repeatedly over unchanged local artifacts, **When** the results are compared, **Then** the result content is deterministic and contains no generation timestamp.

---

### User Story 2 - Execute One Audio Download (Priority: P2)

A local operator wants to confirm audio download for exactly one selected episode and receive an auditable run report that records whether the audio was downloaded or reused.

**Why this priority**: Downloading audio reads RSS metadata and uses network. A one-episode confirmation guard keeps blast radius, bandwidth, and remote side effects bounded.

**Independent Test**: A confirmed run with one selected episode downloads or reuses only that episode through the existing audio download capability and writes deterministic JSON and Markdown run reports.

**Acceptance Scenarios**:

1. **Given** a user requests confirmed audio download without an episode reference, **When** the runner is invoked, **Then** the run is rejected before RSS or network work starts.
2. **Given** a user confirms audio download for one selected episode, **When** the existing download capability succeeds, **Then** only that episode is attempted and the run report records downloaded or reused outcome metadata.
3. **Given** a user confirms audio download for an episode that is not selected, **When** the runner is invoked, **Then** no download occurs and the run records a clear rejected outcome.

---

### User Story 3 - Contain Download Failures and Preserve Boundaries (Priority: P3)

A local operator wants download failures to be recorded without leaking full source URLs, secrets, traceback bodies, or weakening the no-transcribe, no-LLM, no-MCP, and no-cache boundaries.

**Why this priority**: Audio download depends on feed metadata and network. Failures must be auditable without exposing signed URLs, tokens, stack traces, or unrelated side effects.

**Independent Test**: A confirmed run with a download failure records the failure, writes only metadata and local paths, does not transcribe, does not call LLM or MCP surfaces, and does not expose full source URLs or secret values.

**Acceptance Scenarios**:

1. **Given** the underlying download dependency fails, **When** confirmed audio download runs, **Then** the failure is recorded with a bounded error category and no traceback body.
2. **Given** source metadata or dependency errors contain a signed URL, token-like query string, API key, or unsafe prompt-like string, **When** the run result is produced, **Then** JSON, Markdown, stdout, and stderr include only metadata, paths, counts, statuses, and bounded warnings.
3. **Given** audio download writes or reuses a local audio artifact, **When** the run report is produced, **Then** the report may warn that downstream corpus work remains manual but must not run transcription, downstream remediation, or cache rebuild automatically.

### Edge Cases

- Empty local corpus produces a valid dry-run result with zero selected episodes and no run report artifact.
- An episode with local audio already available is skipped rather than downloaded in dry-run selection.
- An audio remediation action with blocked, optional, gated, or non-ready status is skipped.
- Confirmed execution without an episode reference, with an empty episode reference, or with a whitespace-only episode reference is rejected before RSS or network work starts.
- Confirmed execution for an episode not present in the refreshed remediation plan records no download work.
- Confirmed execution for an episode present but not selected records a rejected outcome.
- A successful download result with `already_exists=true` records a reused outcome rather than a downloaded outcome.
- Download dependency failures affect only the requested episode and do not produce traceback bodies or full source URLs in outputs.
- Repeated dry-runs over unchanged local artifacts produce identical result content except transport formatting.
- Repeated confirmed runs over unchanged already-satisfied local audio produce deterministic report shape and mark reused or rejected outcomes rather than fabricating new work.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature reads local corpus remediation plan metadata, local corpus index metadata, and local audio status metadata during dry-run. It refreshes the 009 remediation plan before selecting audio work.
- This feature's dry-run mode must not write audio files, run report artifacts, transcript outputs, or downstream corpus artifacts; it returns planned reads, planned writes, selected/skipped counts, and warnings through local command output only.
- Confirmed execution may read RSS/feed metadata and call the network only through the existing audio download capability for exactly one selected episode.
- Confirmed execution may write or reuse one local audio artifact and may write latest run report artifacts under `data/corpus/{podcast_id}/`.
- This feature must not transcribe audio, repair transcript artifacts, execute deterministic downstream remediation, call LLM providers, read `.env`, add MCP tools, invoke MCP tools, generate stock-lens artifacts, or rebuild SQLite cache.
- This feature must not add, remove, or change MCP tools or MCP response envelopes.
- This feature must not output full audio source URLs, query strings, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated run output must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run corpus audio download planning or execution for exactly one requested podcast identifier.
- **FR-002**: System MUST refresh the 009 corpus remediation plan before selecting audio download work for every run.
- **FR-003**: System MUST default to dry-run mode and MUST NOT write audio files, run report artifacts, transcript outputs, or downstream artifacts in dry-run mode.
- **FR-004**: System MUST NOT read RSS feeds, call network providers, or call the audio downloader in dry-run mode.
- **FR-005**: System MUST only select audio remediation actions whose source status is `ready` and whose audio artifact status is `missing`.
- **FR-006**: System MUST skip available audio, blocked audio actions, non-ready audio actions, transcript actions, semantic actions, deterministic downstream actions, stock-lens actions, synthesis actions, and unknown families with factual reasons.
- **FR-007**: System MUST reject confirmed execution unless exactly one non-empty episode reference is provided.
- **FR-008**: System MUST reject confirmed execution for an episode that is not selected by the refreshed audio download criteria.
- **FR-009**: System MUST execute confirmed download by using the existing audio download capability for the selected episode and without shelling out to local scripts.
- **FR-010**: System MUST NOT execute transcription, deterministic downstream remediation, semantic summary, semantic review, stock-lens generation, LLM synthesis, MCP calls, or cache rebuild during selection or confirmed execution.
- **FR-011**: System MUST write `data/corpus/{podcast_id}/corpus-audio-download-run.json` and `.md` only after confirmed execution is attempted or explicitly rejected.
- **FR-012**: System MUST keep run report content deterministic for unchanged local inputs and confirmed outcomes, including no generation timestamp.
- **FR-013**: System MUST record selected, downloaded, reused, failed, skipped, rejected, and warning counts in JSON, Markdown, and command output.
- **FR-014**: System MUST record per-episode outcome rows with podcast identifier, episode reference, source remediation action id when available, audio status, planned reads, planned writes, local output path when available, content type when available, size bytes when available, outcome status, reason, and warnings.
- **FR-015**: System MUST NOT include full audio source URLs, URL query strings, API keys, tokens, `.env` values, provider secret values, prompt text, raw LLM output, or traceback bodies in JSON, Markdown, stdout, or stderr.
- **FR-016**: System MUST contain single-episode download failures by recording the failed outcome and preserving all other dry-run row metadata.
- **FR-017**: System MUST provide a thin local command surface that can preview by podcast and confirmed-run by podcast plus one episode reference.
- **FR-018**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-019**: System MUST preserve no-investment-advice boundaries in all runner outputs.
- **FR-020**: System MUST leave transcription, downstream remediation, and SQLite cache rebuild as explicit manual follow-up operations after confirmed audio writes or reuse.

### Key Entities *(include if feature involves data)*

- **Corpus Audio Download Run**: One dry-run or confirmed audio download selection for one podcast. Key attributes include podcast identifier, mode, source remediation plan paths, filters, selected count, outcome counts, warnings, and run rows.
- **Audio Download Row**: One selected, skipped, downloaded, reused, failed, or rejected audio action derived from corpus remediation metadata. Key attributes include episode reference, source action id, audio status, planned reads, planned writes, local output path, content type, size bytes, outcome status, reason, and warning messages.
- **Audio Download Filter**: The bounded criteria applied before confirmed execution. Key attributes include optional episode reference and confirmation mode.
- **Audio Download Warning**: A non-fatal warning associated with the run or a specific row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For an empty local corpus, users receive a dry-run result with zero selected episodes, zero downloaded episodes, and no run report artifact written.
- **SC-002**: For a remediation plan containing at least one eligible missing-audio action and at least three ineligible states, dry-run output identifies the eligible row and all ineligible rows with factual skipped reasons.
- **SC-003**: For confirmed execution without a non-empty episode reference, zero RSS, network, or download work starts and the user receives a clear rejection.
- **SC-004**: For a confirmed run targeting one eligible episode, 100% of attempted download rows belong to that episode.
- **SC-005**: For a confirmed run where the existing downloader reports an existing local file, the run records a reused outcome rather than a downloaded outcome.
- **SC-006**: For a confirmed run where download fails, the failed outcome is recorded and no raw traceback body or full source URL is exposed.
- **SC-007**: Generated run outputs contain zero full source URLs, URL query strings, prompt text, raw LLM response text, secret values, provider configuration values, or traceback bodies.
- **SC-008**: The existing MCP reviewed tool count and response envelope remain unchanged after the feature is delivered.
- **SC-009**: Dry-run results and confirmed run reports over unchanged inputs contain no `generated_at` or equivalent generation timestamp field.

## Assumptions

- Package `009-corpus-remediation-plan` is available and remains the source of audio action status, blocker status, and corpus metadata.
- Existing `download_audio(podcast_id, episode_ref)` remains the only confirmed download mechanism in v1.
- Confirmed download may read RSS metadata and call the network through existing downloader behavior; dry-run may not.
- Full source URLs may contain signed URLs, query tokens, or tracking parameters, so runner outputs omit source URLs entirely in v1.
- Batch download, retry policy tuning, rate limiting, transcript generation, downstream remediation, MCP exposure, and automatic cache rebuild are future features outside v1.
