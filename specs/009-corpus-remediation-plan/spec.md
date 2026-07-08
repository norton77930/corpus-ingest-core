# Feature Specification: Corpus Remediation Plan

**Feature Branch**: `009-corpus-remediation-plan`

**Created**: 2026-07-08

**Status**: Implemented

**Input**: User description: "Generate a deterministic offline corpus remediation/action plan from local corpus artifact status. The plan refreshes the corpus index first, writes JSON and Markdown under data/corpus/{podcast_id}/, includes full-ladder missing artifact actions, and never executes remediation, downloads, transcription, LLM calls, MCP tools, cache rebuilds, RSS, network, SQLite cache, or stock-lens query inventory."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Corpus Remediation Backlog (Priority: P1)

A local operator wants to generate one corpus-level remediation plan for a podcast and see which episodes need which artifact families restored, regenerated, or reviewed.

**Why this priority**: This is the minimum useful outcome after the corpus artifact index: it turns status metadata into an ordered backlog without performing any remediation work.

**Independent Test**: A local corpus with multiple episodes and missing artifact families produces one JSON remediation plan and one Markdown remediation plan with summary counts, episode rows, ordered actions, blockers, warnings, and no generation timestamp.

**Acceptance Scenarios**:

1. **Given** a corpus with no local episode artifacts, **When** the user generates a remediation plan for one podcast, **Then** the system writes valid JSON and Markdown outputs with zero episodes and zero actions.
2. **Given** a corpus with episodes missing different artifact families, **When** the user generates a remediation plan, **Then** each episode shows ordered next actions derived from the artifact dependency ladder.
3. **Given** unchanged local artifacts, **When** the user generates the remediation plan twice, **Then** the JSON and Markdown contents are identical.

---

### User Story 2 - Understand Blockers and Unsafe Inputs (Priority: P2)

A local operator wants missing, corrupt, or unreadable artifact state to be visible without causing the entire corpus planning run to fail.

**Why this priority**: Remediation is useful only when incomplete corpora can still be inspected. One broken artifact should not hide other episodes or unrelated artifact families.

**Independent Test**: A fixture corpus with a missing transcript, an available audio artifact, missing downstream research artifacts, and one malformed metadata artifact produces a remediation plan that isolates blockers and warnings to the affected episode and family.

**Acceptance Scenarios**:

1. **Given** an episode has audio available but transcript missing, **When** the remediation plan is generated, **Then** the plan lists transcription as the next manual action and marks transcript-dependent downstream actions as blocked until a readable transcript exists.
2. **Given** one supported artifact metadata file is unreadable, **When** the remediation plan is generated, **Then** the plan records a warning for that artifact and still includes readable episodes and unrelated actions.
3. **Given** an episode has a missing upstream artifact, **When** the plan lists downstream gaps, **Then** the downstream actions identify the upstream blocker instead of implying they are immediately runnable.

---

### User Story 3 - Review Optional Semantic Remediation (Priority: P3)

A local operator wants semantic summary and semantic review gaps to appear in the plan as optional, gated work without triggering any LLM provider call or exposing LLM content.

**Why this priority**: Semantic artifacts have special cost, privacy, and review boundaries. They must be visible for completeness while remaining opt-in and safely separated from deterministic work.

**Independent Test**: A fixture corpus with semantic summary gaps, missing semantic review artifacts, and reviewed semantic summaries produces gated semantic actions, review status, and check-count metadata without semantic body text, prompt text, or raw model output.

**Acceptance Scenarios**:

1. **Given** a transcript exists but semantic summary is missing, **When** the remediation plan is generated, **Then** the semantic summary action is marked optional and gated by explicit LLM acknowledgement.
2. **Given** a semantic summary exists but no review report exists, **When** the remediation plan is generated, **Then** the semantic review action is listed after the semantic summary dependency and no semantic summary body text is included.
3. **Given** semantic artifacts contain body text or raw model output, **When** the remediation plan is generated, **Then** the output includes only status, paths, counts, and warnings.

---

### Edge Cases

- Empty local corpus still writes valid JSON and Markdown remediation plan artifacts.
- Episodes discovered from downstream artifacts with missing audio or transcript remain visible and show upstream blockers.
- Audio available with missing transcript produces a transcription action, not downstream research actions as immediately runnable.
- Transcript missing or unreadable blocks extractive summary, mentions, semantic summary, semantic review, episode intelligence, industry mapping, and external boundary actions.
- A semantic review action is not listed as immediately runnable until a semantic summary artifact exists.
- Corrupt or unreadable JSON metadata marks only the affected artifact family as unsafe and records a warning.
- Duplicate artifact candidates inherited from the corpus index remain deterministic and do not create duplicate remediation rows.
- Repeated runs over unchanged local artifacts produce identical JSON and Markdown content.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature reads only local corpus status and local per-episode artifact metadata. It must not use RSS, network calls, SQLite cache content, live market data, stock-lens query artifacts, or stock-lens synthesis artifacts as inputs.
- This feature writes only derived remediation plan artifacts under `data/corpus/{podcast_id}/`.
- This feature must refresh the corpus artifact index before deriving the remediation plan so users do not act on stale corpus status.
- The remediation plan may list manual or dry-run-style action suggestions, but the feature must not execute downloads, transcription, summaries, workflow steps, LLM calls, MCP tools, or cache rebuilds.
- LLM-related semantic actions must be marked optional and gated. The plan may mention that exact API-cost acknowledgement is required for future execution, but must not construct providers, read secret values, or call an LLM.
- The generated plan must not include raw transcript text, evidence snippets, semantic summary body text, prompt text, raw LLM output, `.env` values, API keys, tokens, or provider secret values.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated plan must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.
- This feature must not expose a new MCP tool and must not change the reviewed MCP tool count or response envelope.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a corpus remediation plan for exactly one requested podcast identifier.
- **FR-002**: System MUST refresh the corpus artifact index before deriving the remediation plan and MUST NOT reuse a stale corpus index artifact as the planning source.
- **FR-003**: System MUST derive remediation state only from local corpus status and supported local per-episode artifact metadata.
- **FR-004**: System MUST write both JSON and Markdown remediation plan artifacts under `data/corpus/{podcast_id}/`.
- **FR-005**: System MUST keep remediation plan content deterministic for unchanged local artifacts, including no generation timestamp in the JSON or Markdown payload.
- **FR-006**: System MUST include top-level summary counts for episodes, actions, blocked actions, optional actions, gated actions, and warnings.
- **FR-007**: System MUST include per-episode rows with artifact status, missing artifact families, blockers, warnings, and ordered remediation actions.
- **FR-008**: System MUST order actions using the full artifact ladder: audio, transcript, extractive summary, mentions, semantic summary, semantic review, episode intelligence, industry mapping, and external boundary.
- **FR-009**: System MUST list download and transcription remediation only as manual or dry-run-style suggested actions and MUST NOT execute them.
- **FR-010**: System MUST mark transcript-dependent downstream actions as blocked when the transcript artifact is missing or unreadable.
- **FR-011**: System MUST isolate corrupt or unreadable artifact metadata warnings to the affected episode and artifact family without failing the whole remediation plan.
- **FR-012**: System MUST mark semantic summary and semantic review actions as optional or gated according to their LLM and review boundaries.
- **FR-013**: System MUST exclude raw transcript text, evidence snippets, semantic body text, prompt text, raw LLM output, and secret values from JSON and Markdown outputs.
- **FR-014**: System MUST keep Markdown output factual and command-oriented: missing artifacts, blockers, warnings, paths, counts, and next actions only.
- **FR-015**: System MUST provide a thin local command surface that prints output paths and summary counts after generating the remediation plan.
- **FR-016**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.

### Key Entities *(include if feature involves data)*

- **Corpus Remediation Plan**: Podcast-level derived artifact for one podcast. Key attributes include podcast identifier, source corpus index paths, episode count, action counts, warning count, and plan rows.
- **Episode Remediation Row**: Status and remediation record for one discovered episode. Key attributes include episode reference, title if available, missing artifact families, blockers, warnings, and ordered actions.
- **Remediation Action**: One suggested next step. Key attributes include action identifier, artifact family, action type, priority/order, dependency status, optional/gated flags, and safe command text if available.
- **Remediation Blocker**: A reason an action cannot be immediately performed. Key attributes include blocked artifact family, blocking artifact family, status, and path or warning context when available.
- **Remediation Warning**: Non-fatal warning associated with an episode, artifact family, or corpus-level input.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For an empty local corpus, users receive valid JSON and Markdown outputs with `episode_count=0`, `action_count=0`, and no episode rows.
- **SC-002**: For a prepared corpus containing at least five episodes across three or more artifact families, users can identify all missing artifact families and the next ordered action for each affected episode from the generated Markdown.
- **SC-003**: For unchanged local artifacts, two consecutive remediation plan generations produce identical JSON content and identical Markdown content.
- **SC-004**: For an episode with audio available and transcript missing, the plan lists transcription as the next manual action and marks at least three transcript-dependent downstream action families as blocked.
- **SC-005**: For a corpus with one malformed supported artifact JSON, the plan still includes all readable episodes and records at least one warning for the malformed artifact.
- **SC-006**: Generated remediation plan artifacts contain zero raw transcript text snippets, zero evidence text snippets, zero semantic body text snippets, zero LLM prompt text, zero raw LLM response text, and zero secret values.
- **SC-007**: The existing MCP reviewed tool count and response envelope remain unchanged after the feature is delivered.

## Assumptions

- The corpus artifact index from package `008` is available and remains the authoritative local status input for v1 planning.
- A remediation plan is a derived artifact that may be overwritten by later runs.
- The user wants full-ladder planning, including upstream audio and transcript gaps, but still wants no remediation execution in this feature.
- Safe command text is advisory and factual; commands that would trigger side effects or external LLM work must be marked manual, dry-run, optional, or gated as appropriate.
- Stock-lens and stock-lens synthesis inventory remain out of scope because they are query-level rather than per-episode remediation targets.
