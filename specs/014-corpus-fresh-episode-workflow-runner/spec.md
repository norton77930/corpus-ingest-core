# Feature Specification: Corpus Fresh Episode Workflow Runner

**Feature Branch**: `014-corpus-fresh-episode-workflow-runner`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "Create a dry-run-first corpus fresh episode workflow runner that safely guides testing the newest or explicitly selected episode through the existing 013 intake, 012 audio download, 011 local transcription, and 010 deterministic remediation chain. Confirmed execution must run only the next safe stage for one episode and must not execute semantic/LLM, MCP, cache rebuild, stock-lens, or batch behavior."

## Clarifications

### Session 2026-07-10

- Q: What confirmed execution model should v1 use? -> A: Single next-stage confirmation; each confirmed run executes only the currently selected next safe stage, not the full chain.
- Q: Which selectors are in scope? -> A: `latest` and one explicit episode reference such as `EP677`.
- Q: When may workflow evaluation persist local state? -> A: Confirmed runs only; dry-run creates, modifies, or deletes zero files.
- Q: Which stage interface should v1 expose? -> A: `stage=next` only.
- Q: How should transcription options behave? -> A: Reuse 011 defaults and allow model/device/compute/VAD options to pass through when local transcription is selected.
- Q: How should stage probes and confirmed dispatch differ? -> A: Seeded selection uses package-private previews over one shared in-memory index/plan snapshot, while confirmed dispatch may call at most one selected existing public runner with `confirm=True`.
- Q: What happens when a probe fails or reports a non-safe status? -> A: Probe exceptions and `failed`, `rejected`, or `blocked` outcomes stop selection fail closed with `selected_stage=blocked`; the row keeps its actual status, while a safely skipped satisfied prerequisite may continue to the next probe.
- Q: How should safe confirmed stops be reported? -> A: A confirmed terminal probe outcome writes deterministic workflow reports and returns structured CLI JSON with exit code 0; invalid input and system-level command errors remain non-zero.
- Q: How is fresh corpus state computed without violating dry-run? -> A: Corpus index and remediation state are recomputed in memory during dry-run; seed, audio, transcript, index, plan, 010-014 reports, downstream artifacts, and `.part` files are never created, modified, or deleted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview the Next Safe Stage (Priority: P1)

A local operator wants one command that resolves the latest or explicit episode and reports the next safe corpus action without executing a stage or changing any local file.

**Why this priority**: Preview is the safe entry point for testing latest episodes. It reduces manual command sequencing while preserving dry-run visibility.

**Independent Test**: Real 008/009 builders and 010-012 previews cover six corpus states while writer call count stays zero and the before/after tree manifest remains identical, including stale sentinels and `.part` absence.

**Acceptance Scenarios**:

1. **Given** the latest episode is not yet seeded, **When** the operator dry-runs the workflow with `episode_ref=latest`, **Then** the result reports intake as the next stage and creates, modifies, or deletes zero files.
2. **Given** an explicit episode already has seed metadata but is missing local audio, **When** the operator dry-runs the workflow, **Then** the result reports audio download as the next stage.
3. **Given** no safe next stage exists, **When** the operator dry-runs the workflow, **Then** the result reports completed or blocked metadata with manual follow-up warnings only.

---

### User Story 2 - Execute One Confirmed Next Stage (Priority: P2)

A local operator wants to confirm exactly one next stage for one episode so they can step through intake, download, transcription, and deterministic remediation without accidentally running the whole corpus chain.

**Why this priority**: The operator needs a safer shortcut for real latest-episode testing, but each side effect must remain bounded and auditable.

**Independent Test**: A confirmed `stage=next` run dispatches to only the appropriate existing core runner for the selected state and writes one deterministic workflow run report.

**Acceptance Scenarios**:

1. **Given** the episode is unseeded, **When** confirmed workflow runs with `stage=next`, **Then** it calls episode intake only and does not call audio download, transcription, remediation, cache rebuild, MCP, or LLM paths.
2. **Given** seed metadata exists and audio is missing with a ready audio action, **When** confirmed workflow runs with `stage=next`, **Then** it calls audio download only.
3. **Given** local audio exists and transcript is missing, **When** confirmed workflow runs with `stage=next`, **Then** it calls local transcription only and passes through the selected transcription options.
4. **Given** transcript-ready deterministic actions exist, **When** confirmed workflow runs with `stage=next`, **Then** it calls deterministic remediation only for that episode and passes through force, allow-partial, and max-actions options.

---

### User Story 3 - Preserve Safety Boundaries and Manual Follow-up (Priority: P3)

A local operator wants workflow output to remain safe and factual even when upstream feeds, stage runners, or local artifact metadata contain unsafe values or non-executable actions.

**Why this priority**: The workflow runner coordinates multiple side-effect-capable runners, so it must not weaken any existing RSS, download, transcript, LLM, MCP, cache, or investment-advice boundary.

**Independent Test**: Unsafe feed/stage metadata and runner failures are bounded in JSON, Markdown, stdout, and stderr without leaking full URLs, raw transcript text, prompt text, raw LLM output, secrets, traceback bodies, or investment advice.

**Acceptance Scenarios**:

1. **Given** semantic, LLM, stock-lens, MCP, or cache rebuild work appears as a possible follow-up, **When** the workflow evaluates next stage, **Then** those items are listed as manual-only or skipped and are never executed.
2. **Given** a selected stage fails, **When** the workflow reports the failure, **Then** the result contains bounded error category metadata without traceback bodies or unsafe source content.
3. **Given** confirmed execution writes a workflow run report, **When** report content is inspected, **Then** it contains metadata, stage status, counts, paths, and warnings only.

### Edge Cases

- Missing or blank `episode_ref` defaults to `latest`.
- Explicit episode lookup remains single-episode only; batch latest-N is out of scope.
- Confirmed execution with any stage value other than `next` is rejected.
- CLI confirmed execution without an explicit `--stage next` flag is rejected.
- Confirmed execution without an executable safe next stage writes a rejected or blocked workflow report but does not run downstream work.
- If intake resolves `latest` to a canonical episode reference, subsequent stage decisions use the canonical reference.
- If an existing runner reports rejected, failed, blocked, or skipped outcomes, the workflow records that outcome and stops after that stage.
- Repeated confirmed workflow runs over unchanged state overwrite the latest workflow report deterministically.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- 013 dry-run may read the configured podcast RSS feed. Seeded selection builds one in-memory corpus snapshot and uses package-private 012/011/010 previews with `source_persisted=False`; it does not call their public standalone dry-run entry points.
- `confirm=False` is a strict zero-file operation: it must not create, modify, or delete seed, audio, transcript, index, plan, 010-014 report, downstream, cache, provider, MCP, or `.part` artifacts.
- Confirmed execution dispatches exactly one existing public runner. That runner may perform its existing refreshed index/plan and selected-stage writes, after which 014 writes one latest workflow JSON/Markdown report; no alternative stage is attempted.
- This feature must not execute semantic summary/review, LLM calls, stock-lens, synthesis, MCP tools, SQLite cache rebuild, batch latest-N processing, or any stage other than `next`.
- Outputs and written artifacts must not include full source URLs, URL query strings, raw transcript text, evidence snippets, semantic body text, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated output must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run the fresh episode workflow for exactly one podcast identifier and one episode selector.
- **FR-002**: System MUST accept `latest` and one explicit episode reference; missing or blank selector MUST default to `latest`.
- **FR-003**: System MUST support only `stage=next` in v1 and MUST reject other stage values.
- **FR-004**: System MUST default to dry-run mode, MUST NOT execute stages, and MUST create, modify, or delete zero files in dry-run mode.
- **FR-005**: System MUST determine the next safe stage in this order: intake, audio download, local transcription, deterministic remediation, then completed or manual-only follow-up.
- **FR-006**: System MUST call only the existing 013 intake core runner when the selected next stage is intake.
- **FR-007**: System MUST call only the existing 012 audio download core runner when the selected next stage is audio download.
- **FR-008**: System MUST call only the existing 011 local transcription core runner when the selected next stage is local transcription.
- **FR-009**: System MUST call only the existing 010 deterministic remediation core runner when the selected next stage is deterministic remediation.
- **FR-010**: System MUST pass model, device, compute type, and VAD options through to local transcription only when local transcription is the selected stage.
- **FR-011**: System MUST pass force, allow-partial, and max-actions options through to deterministic remediation only when deterministic remediation is the selected stage.
- **FR-012**: System MUST write latest deterministic workflow run JSON and Markdown reports only after confirmed execution is attempted.
- **FR-013**: System MUST record selected stage, executed stage, skipped/manual-only stages, blocked or rejected state, output paths, source stage report paths, counts, and warnings.
- **FR-014**: System MUST stop after one confirmed stage attempt, regardless of success, reuse, failure, rejection, or skipped outcome.
- **FR-015**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-016**: System MUST NOT execute semantic summary/review, LLM providers, stock-lens, synthesis, MCP tools, `.env` reads, SQLite cache rebuild, batch latest-N, or full-chain automation.
- **FR-017**: System MUST NOT include unsafe source content, raw transcript/evidence/semantic/prompt/LLM body text, secret values, traceback bodies, market claims, or investment advice in JSON, Markdown, stdout, or stderr.
- **FR-018**: System MUST provide a thin local command surface that previews by podcast and selector and confirmed-runs one `next` stage by podcast plus selector only when `--stage next --confirm` is explicit.
- **FR-019**: Seeded dry-run selection MUST build exactly one fresh in-memory index/plan snapshot and reuse that same snapshot for audio, transcription, and remediation previews.
- **FR-020**: Public standalone 010-012 dry-runs MUST retain their existing behavior of refreshing and persisting 008/009 while executing no external side effect and writing no own stage report.
- **FR-021**: The only permitted non-path planned-read values MUST be the exact labels `configured podcast RSS feed` and `in-memory corpus snapshot`; safe local dependency paths remain permitted, while snapshot provenance `source_persisted=False` remains package-private and MUST NOT change public models, CLI JSON, or exports.

### Key Entities *(include if feature involves data)*

- **Corpus Episode Workflow Run**: One dry-run or confirmed next-stage evaluation for one podcast and selector. Key attributes include podcast identifier, selector, canonical episode reference when resolved, run mode, selected stage, stage outcome, report paths when written, counts, rows, warnings, and no-investment-advice marker.
- **Workflow Stage Row**: One stage candidate or executed stage outcome. Key attributes include stage name, status, reason, planned reads, planned writes, output paths, source runner report paths, outcome counts, and warnings.
- **Workflow Stage Counts**: Summary counts for selected, executed, reused, failed, skipped, blocked, rejected, manual-only, and warning outcomes.
- **Workflow Warning**: A non-fatal warning associated with stage selection, manual follow-up, or bounded failure metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dry-run for `latest` returns exactly one selected next stage or one completed/blocked result and creates, modifies, or deletes zero files across the full local tree.
- **SC-002**: Confirmed workflow execution attempts exactly one stage and writes exactly one pair of latest JSON/Markdown workflow reports.
- **SC-003**: Confirmed workflow execution for each stage state calls only the matching existing core runner and calls zero non-selected stage runners.
- **SC-004**: Local transcription confirmed through the workflow passes through model, device, compute type, and VAD options unchanged.
- **SC-005**: Deterministic remediation confirmed through the workflow passes through force, allow-partial, and max-actions options unchanged with an episode filter.
- **SC-006**: Semantic, LLM, stock-lens, MCP, cache rebuild, and batch actions are never executed by the workflow and appear only as skipped/manual follow-up metadata.
- **SC-007**: Generated output contains zero full source URLs, query strings, raw transcript/evidence/semantic/prompt/LLM body text, secret values, provider configuration values, traceback bodies, market claims, or investment advice.
- **SC-008**: Existing MCP reviewed tool count and response envelope remain unchanged.
- **SC-009**: Dry-run results and confirmed run reports over unchanged inputs contain no `generated_at` or equivalent generation timestamp field.

## Assumptions

- Existing 013, 012, 011, and 010 core runners remain the source of stage execution behavior and safety boundaries.
- The workflow runner derives next-stage state from one fresh in-memory corpus snapshot and package-private preview seams, while confirmed execution delegates to exactly one existing public runner.
- `latest` resolution may depend on 013 intake behavior; explicit episode references avoid selector drift after the first run.
- v1 does not expose MCP tooling, scheduling, batch processing, semantic/LLM automation, or automatic cache rebuild.
- `SPECIFY_FEATURE_DIRECTORY` takes precedence for explicit local selection; ignored `.specify/feature.json` may preserve local state but is local-only, gitignored, and untracked.
