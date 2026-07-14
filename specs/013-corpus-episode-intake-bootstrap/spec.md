# Feature Specification: Corpus Episode Intake Bootstrap

**Feature Branch**: `013-corpus-episode-intake-bootstrap`

**Created**: 2026-07-09

**Status**: Implemented

**Input**: User description: "Create a dry-run-first corpus episode intake bootstrap feature that reads the configured podcast RSS feed to resolve `latest` or one explicit episode, writes local seed metadata only after confirmed execution, lets the existing 008/009/012/011/010 corpus chain process the episode, and excludes download, transcription, downstream remediation, LLM, MCP, cache rebuild, source URL output, secret leakage, and investment advice behavior."

## Clarifications

### Session 2026-07-09

- Q: What should 013 confirmed execution do? -> A: Seed Only; confirmed intake writes local episode seed metadata and an intake report, but does not download, transcribe, refresh 008/009, or run downstream remediation.
- Q: Which episode selectors are in v1? -> A: `latest` and one explicit episode reference such as `EP677`; batch latest-N is out of scope.
- Q: May dry-run read RSS/network? -> A: Yes; dry-run may read the configured RSS feed to resolve episode metadata, but it must not write files, download media, read `.env`, call LLM, call MCP, or rebuild cache.
- Q: Which artifacts are written on confirmed run? -> A: Per-episode seed metadata plus latest deterministic JSON/Markdown intake run report.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Episode Intake (Priority: P1)

A local operator wants to check which episode `latest` resolves to, or inspect a specific episode reference from the configured feed, before writing any local corpus metadata.

**Why this priority**: Preview is the safe entry point for a feed-backed intake workflow. It lets the user verify the resolved episode before changing the local corpus.

**Independent Test**: A dry-run can resolve `latest` and an explicit episode from a mocked RSS feed, return metadata-only output, and leave seed and report paths unwritten.

**Acceptance Scenarios**:

1. **Given** the configured feed contains a newest episode, **When** the user previews intake with `episode_ref=latest`, **Then** the result resolves that episode reference and title without writing seed metadata or run reports.
2. **Given** the configured feed contains a requested explicit episode reference, **When** the user previews intake for that reference, **Then** the result reports that exact episode as selected and remains no-write.
3. **Given** the feed cannot resolve the requested episode, **When** the user previews intake, **Then** the result reports a rejected or failed metadata-only outcome without creating corpus artifacts.

---

### User Story 2 - Seed One Episode Into Corpus (Priority: P2)

A local operator wants to confirm intake for exactly one resolved episode so it becomes visible to the offline corpus index and remediation plan.

**Why this priority**: The existing corpus chain only discovers episodes from local artifacts. Seed metadata bridges RSS discovery into the local-only corpus flow without downloading or transcribing.

**Independent Test**: A confirmed run for one resolved episode writes deterministic seed metadata and intake report artifacts, after which 008 discovers the episode and 009 creates a ready audio remediation action.

**Acceptance Scenarios**:

1. **Given** a dry-run selected one episode, **When** confirmed intake runs for the same selector, **Then** seed metadata is written under the podcast corpus directory and the run report records the seeded outcome.
2. **Given** the seed exists and the episode has no local audio, **When** the corpus index and remediation plan are regenerated later, **Then** the episode appears with missing audio and a ready audio action.
3. **Given** a seed already exists for the same episode and unchanged metadata, **When** confirmed intake is repeated, **Then** the run records a reused outcome rather than duplicating seed files.

---

### User Story 3 - Preserve Boundaries and Safe Output (Priority: P3)

A local operator wants feed failures, signed media URLs, and prompt-like or secret-like feed content to be contained without leaking unsafe values or weakening existing corpus safety boundaries.

**Why this priority**: RSS metadata can contain full URLs, tracking query strings, descriptions, and arbitrary text. Intake must keep local artifacts auditable without copying unsafe source content.

**Independent Test**: Feed metadata and failure paths containing full URLs, query strings, token-like values, prompt text, raw LLM-looking text, or traceback-looking text are sanitized from JSON, Markdown, stdout, and stderr.

**Acceptance Scenarios**:

1. **Given** a feed episode has a media URL with a query string, **When** dry-run or confirmed intake returns output, **Then** the output includes only safe metadata such as episode reference, title, published time, duration, GUID hash/status, has-audio flag, local paths, counts, and warnings.
2. **Given** RSS resolution fails, **When** intake is attempted, **Then** the failure is bounded to the run result or expected error message without traceback bodies or source URLs.
3. **Given** confirmed intake writes seed metadata, **When** the run completes, **Then** it does not download audio, transcribe, run downstream remediation, call LLM providers, read `.env`, change MCP tools, or rebuild SQLite cache.

### Edge Cases

- Empty feed returns a rejected result for `latest` and writes no seed in dry-run.
- Missing or blank `episode_ref` defaults to `latest`.
- Explicit episode lookup is case-insensitive and normalizes to the feed-derived canonical episode reference.
- Feed entries without audio enclosure may still be seeded with `has_audio_url=false`, but 012 must not later select them as ready for download until remediation metadata can distinguish no-audio-url from missing local audio.
- Confirmed execution for an unresolved episode is rejected and writes only a report when a confirmed attempt was made.
- Repeated confirmed intake over unchanged seed metadata records `reused` and keeps deterministic report content.
- Seed metadata must not include raw description, full source URL, full audio URL, query string, or feed HTML body.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature may read configured podcast RSS metadata in dry-run and confirmed modes to resolve one episode selector.
- Dry-run must not write seed metadata, run reports, audio files, transcript outputs, downstream artifacts, cache files, or provider artifacts.
- Confirmed execution may write one local episode seed metadata artifact and latest intake run JSON/Markdown reports under `data/corpus/{podcast_id}/`.
- This feature must not download audio, transcribe audio, generate summaries, extract mentions, generate reports, run deterministic remediation, run semantic summary/review, run stock-lens, call LLM providers, read `.env`, call MCP, change MCP registry, or rebuild SQLite cache.
- Outputs and written artifacts must not include full audio source URLs, URL query strings, raw episode description, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated output must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run episode intake bootstrap for exactly one requested podcast identifier.
- **FR-002**: System MUST accept an episode selector of `latest` or one explicit episode reference; missing or blank selector MUST default to `latest`.
- **FR-003**: System MUST resolve the selector from the configured podcast feed in dry-run and confirmed modes.
- **FR-004**: System MUST default to dry-run mode and MUST NOT write seed metadata, run reports, audio, transcripts, downstream artifacts, cache files, or provider artifacts in dry-run mode.
- **FR-005**: System MUST return metadata-only dry-run output containing resolved selector, canonical episode reference, title, published time when available, duration when available, GUID status or bounded identifier metadata, has-audio flag, planned writes, outcome counts, and warnings.
- **FR-006**: System MUST reject unresolved selectors with bounded metadata and no seed writes.
- **FR-007**: System MUST write one deterministic per-episode seed metadata artifact only after confirmed execution resolves one episode.
- **FR-008**: System MUST write latest deterministic intake run JSON and Markdown reports only after confirmed execution is attempted.
- **FR-009**: System MUST record selected, seeded, reused, failed, rejected, skipped, and warning counts in result metadata and confirmed run reports.
- **FR-010**: System MUST let the offline corpus index discover episodes from confirmed seed metadata in addition to existing local per-episode artifact families.
- **FR-011**: System MUST let the remediation plan classify a seeded episode with no local audio as missing audio and produce an audio remediation action when safe metadata indicates audio is available from the feed.
- **FR-012**: System MUST keep confirmed seed and report content deterministic for unchanged inputs and outcomes, including no generation timestamp.
- **FR-013**: System MUST NOT include full source URLs, audio URLs, URL query strings, raw descriptions, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies in JSON, Markdown, stdout, or stderr.
- **FR-014**: System MUST NOT download audio, transcribe audio, run downstream remediation, call LLM providers, read `.env`, call or change MCP tools, generate stock-lens artifacts, or rebuild SQLite cache.
- **FR-015**: System MUST provide a thin local command surface that previews by podcast and selector and confirmed-runs by podcast plus selector.
- **FR-016**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-017**: System MUST preserve no-investment-advice boundaries in all intake outputs.
- **FR-018**: System MUST leave audio download, transcription, downstream remediation, and SQLite cache rebuild as explicit manual follow-up operations after confirmed intake.

### Key Entities *(include if feature involves data)*

- **Corpus Episode Intake Run**: One dry-run or confirmed selector resolution for one podcast. Key attributes include podcast identifier, run mode, selector, resolved episode metadata, report paths when written, counts, rows, warnings, and no-investment-advice marker.
- **Episode Seed**: Local metadata that makes a feed-resolved episode discoverable by offline corpus indexing. Key attributes include podcast identifier, episode reference, title, published time, duration, safe GUID/status metadata, has-audio flag, seed source, and warning count.
- **Episode Intake Row**: One selected, seeded, reused, failed, rejected, or skipped episode result. Key attributes include selector, canonical episode reference when resolved, safe metadata, planned reads, planned writes, outcome status, reason, and warnings.
- **Episode Intake Warning**: A non-fatal warning associated with a run or row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dry-run for `latest` resolves exactly one newest feed episode and creates zero files.
- **SC-002**: Dry-run for one explicit episode resolves that canonical episode or returns one bounded rejection, with zero seed or report writes.
- **SC-003**: Confirmed intake for a resolvable episode writes exactly one seed metadata artifact and one pair of latest JSON/Markdown run reports.
- **SC-004**: After confirmed intake and later corpus index/regeneration, the seeded episode appears in 008 and receives a missing-audio status when no local audio exists.
- **SC-005**: After later remediation planning, a seeded missing-audio episode with feed audio availability produces an audio action that 012 can select for confirmed download.
- **SC-006**: Generated output contains zero full source URLs, audio URLs, URL query strings, raw descriptions, prompt text, raw LLM output, secret values, provider configuration values, or traceback bodies.
- **SC-007**: Existing MCP reviewed tool count and response envelope remain unchanged.
- **SC-008**: Dry-run results, seed metadata, and confirmed run reports over unchanged inputs contain no `generated_at` or equivalent generation timestamp field.

## Assumptions

- Package 008 remains the offline corpus status source and may be extended to discover local seed metadata.
- Package 009 remains the source for remediation actions and may use seed-derived metadata to distinguish audio available from feed from unknown local-only audio gaps.
- Existing `get_episode(podcast_id, episode_ref)` remains the feed resolution mechanism for `latest` and explicit episode references.
- Seed metadata intentionally omits full source URLs, audio URLs, raw descriptions, and feed HTML body in v1.
- Batch latest-N intake, automatic download, automatic transcription, automatic remediation, MCP exposure, retry/rate-limit policy, and automatic cache rebuild are future features outside v1.
