# Feature Specification: Corpus Artifact Index

**Feature Branch**: `008-corpus-artifact-index`

**Created**: 2026-07-08

**Status**: Implemented

**Input**: User description: "Create a deterministic, offline corpus status index that scans local per-episode podcast artifacts and writes `data/corpus/{podcast_id}/corpus-index.json` plus `.md`. Source is local artifacts only; no RSS, no network, no SQLite cache dependency. Scope is per-episode artifacts only, excluding stock-lens and synthesis query-level inventory in v1. Include status, counts, paths, missing artifacts, and latest semantic summary review status without raw transcript text or evidence snippets. Core and CLI only; no MCP tool in v1."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Local Corpus Status (Priority: P1)

Maintainers and AI agents need a single local corpus status report that lists every episode with at least one supported local per-episode artifact and shows which artifact families are present or missing.

**Why this priority**: This is the core value of the feature. Without a corpus-level status report, users must manually inspect multiple `data/` subtrees before deciding what can be processed next.

**Independent Test**: Can be tested by preparing local episode artifacts across supported artifact families, generating the index, and confirming the JSON and Markdown list the discovered episodes with artifact statuses, counts, paths, and missing artifact names.

**Acceptance Scenarios**:

1. **Given** local transcript and mentions artifacts exist for multiple episodes, **When** the corpus index is generated for the podcast, **Then** the output includes one row per discovered episode with transcript and mentions status information.
2. **Given** the local corpus has no supported per-episode artifacts, **When** the corpus index is generated for the podcast, **Then** the output still exists and reports `episode_count=0`.

---

### User Story 2 - Identify Gaps And Unreadable Artifacts (Priority: P2)

Maintainers and AI agents need the corpus report to identify missing artifact families and unreadable artifact metadata without failing the entire report.

**Why this priority**: The index is useful only if it can support remediation planning across an incomplete local corpus while preserving local artifact safety boundaries.

**Independent Test**: Can be tested by preparing an episode with missing summaries plus an unreadable JSON artifact and confirming the index marks only the affected artifact as missing or unreadable while still reporting the rest of the corpus.

**Acceptance Scenarios**:

1. **Given** an episode has transcript output but no summary, mentions, report, mapping, or external boundary artifacts, **When** the corpus index is generated, **Then** `missing_artifacts` lists each absent supported artifact family.
2. **Given** one supported artifact JSON file cannot be parsed, **When** the corpus index is generated, **Then** the episode remains in the index and the affected artifact is marked `unreadable` with a warning count greater than zero.

---

### User Story 3 - See Semantic Review Readiness (Priority: P3)

Maintainers and AI agents need each episode row to show whether a semantic summary exists and whether the latest semantic summary review passed, failed, or is blocked.

**Why this priority**: Reviewed semantic summaries are optional LLM intermediate artifacts that may be reused by later synthesis only when review status is safe and explicit.

**Independent Test**: Can be tested by preparing multiple semantic review reports for one episode and confirming the index selects the latest review deterministically and exposes only status, counts, and paths.

**Acceptance Scenarios**:

1. **Given** an episode has a semantic summary and multiple semantic review reports, **When** the corpus index is generated, **Then** the episode row reports the latest semantic review status and review report path.
2. **Given** an episode has a semantic summary but no review report, **When** the corpus index is generated, **Then** the episode row reports the semantic summary path and a review status that clearly indicates no review is available.

### Edge Cases

- Empty local corpus: the feature still writes valid JSON and Markdown with zero episodes and zero artifact counts.
- Episode discovered from only one artifact family: the episode appears with available status for that family and missing status for all other supported per-episode families.
- Duplicate artifact candidates for the same episode and family: the feature chooses one deterministically and records the candidate count.
- Unreadable or malformed JSON artifact: the feature marks only that artifact as `unreadable`, records a warning, and continues indexing the rest of the corpus.
- Partial or invalid transcript outputs: transcript status comes from the existing transcript validation classification and is represented without raw transcript text.
- Multiple semantic review reports: the latest report is selected deterministically using the existing timestamped review artifact naming.
- Query-level artifacts such as stock-lens and stock-lens synthesis are intentionally excluded from v1 and must not affect episode discovery or counts.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature reads local per-episode artifact metadata from `data/audio`, `data/transcripts`, `data/summaries`, `data/mentions`, `data/reports`, `data/mappings`, `data/external`, and semantic summary review reports under `evals`.
- This feature writes only corpus index artifacts under `data/corpus/{podcast_id}/`.
- The feature does not require dry-run behavior because it only writes a deterministic status artifact and performs no provider call, download, transcription, workflow execution, cache rebuild, or market-data verification.
- The feature must not call an LLM and must not require `api_cost_ack`.
- The feature must not read `.env`, provider settings, API keys, tokens, or secret values.
- The feature must not call RSS, network services, live market APIs, or SQLite cache reads.
- The feature must preserve external-data status as status metadata only; `not_requested`, `not_fetched`, and `data_date=null` are not market facts.
- The feature must not include raw transcript text, evidence snippets, LLM prompt text, raw LLM output, or semantic summary body text in the corpus index.
- The feature must not expose an MCP tool in v1 and must not change the reviewed MCP tool count or response envelope.
- The feature must not provide buy/sell/hold, target price, guaranteed return, personalized recommendation, or any investment advice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a corpus index for exactly one requested podcast identifier.
- **FR-002**: System MUST discover episodes only from supported local per-episode artifact families and MUST NOT use RSS, network calls, SQLite cache content, stock-lens artifacts, or stock-lens synthesis artifacts for discovery.
- **FR-003**: System MUST write both JSON and Markdown corpus index artifacts under `data/corpus/{podcast_id}/`.
- **FR-004**: System MUST always regenerate the corpus index when requested and MUST NOT reuse a stale corpus index artifact.
- **FR-005**: System MUST keep corpus index content deterministic for unchanged local artifacts, including no generation timestamp in the JSON or Markdown payload.
- **FR-006**: System MUST include a top-level summary with episode count and counts for each supported artifact family.
- **FR-007**: System MUST include one episode row per discovered episode with artifact status, counts, paths, and missing artifact names.
- **FR-008**: System MUST include transcript validation status and transcript segment count when transcript artifacts are present or partially present.
- **FR-009**: System MUST include extractive summary and semantic summary existence and paths without reading or embedding summary body text.
- **FR-010**: System MUST include latest semantic summary review status, review report path, check count, failed count, warning count, and blocked count when review reports exist.
- **FR-011**: System MUST include mentions existence, mention count, and artifact paths when mentions metadata is readable.
- **FR-012**: System MUST include episode intelligence report status, transcript status, segment count, and artifact paths when report metadata is readable.
- **FR-013**: System MUST include industry mapping status, node count, candidate count, warning count, and artifact paths when mapping metadata is readable.
- **FR-014**: System MUST include external boundary status, candidate count, warning count, and artifact paths when boundary metadata is readable.
- **FR-015**: System MUST mark a malformed or unreadable artifact as `unreadable`, record a warning, and continue producing the rest of the index.
- **FR-016**: System MUST include `missing_artifacts` for every episode, using stable artifact family names.
- **FR-017**: System MUST produce a human-readable Markdown table that summarizes episode readiness without raw transcript text, evidence text, or semantic summary content.
- **FR-018**: System MUST provide a CLI-facing result that reports output paths, episode count, warning count, and artifact-family counts.
- **FR-019**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-020**: System MUST include no investment advice notice in Markdown output.

### Key Entities *(include if feature involves data)*

- **Corpus Index**: Podcast-level status artifact for one podcast. Key attributes include podcast identifier, index mode, episode count, artifact family counts, warning count, and episode rows.
- **Episode Corpus Row**: Status record for one discovered episode. Key attributes include podcast identifier, episode reference, title if available, artifact family statuses, missing artifact names, and warnings.
- **Artifact Family Status**: Status for a supported per-episode artifact family. Key attributes include status, paths, counts, and warning details.
- **Semantic Review Status**: Status summary for the latest semantic summary review report associated with an episode. Key attributes include review status, report path, check count, failed count, warning count, and blocked count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a prepared corpus containing at least five episodes across three or more artifact families, users can generate one JSON and one Markdown corpus index in a single command and identify each episode's available and missing artifact families from the output.
- **SC-002**: For unchanged local artifacts, two consecutive corpus index generations produce the same JSON content and Markdown content.
- **SC-003**: For an empty local corpus, users receive valid JSON and Markdown outputs with `episode_count=0` and no episode rows.
- **SC-004**: For a corpus with one malformed supported artifact JSON, the index still includes all readable episodes and records at least one warning for the malformed artifact.
- **SC-005**: Generated corpus index artifacts contain zero raw transcript text snippets, zero evidence text snippets, zero LLM prompt text, and zero raw LLM response text.
- **SC-006**: The existing MCP reviewed tool count and response envelope remain unchanged after the feature is delivered.
- **SC-007**: Users can determine semantic summary review readiness for an episode with a semantic summary and review report without opening the semantic summary file.

## Assumptions

- v1 indexes only local per-episode artifacts and intentionally excludes RSS-only episodes that have no local artifacts.
- v1 excludes stock-lens and stock-lens synthesis because those artifacts are query-level rather than per-episode.
- The supported per-episode artifact families are audio, transcript, extractive summary, semantic summary, semantic summary review, mentions, episode intelligence report, industry mapping, and external boundary.
- The existing transcript validation status names remain authoritative for transcript readiness.
- Semantic summary review reports use the existing timestamped review artifact naming and contain review status plus check counts.
- The corpus index is a derived artifact that may be overwritten by later runs.
