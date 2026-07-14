# Feature Specification: Corpus Remediation Runner

**Feature Branch**: `010-corpus-remediation-runner`

**Created**: 2026-07-09

**Status**: Implemented

**Input**: User description: "Create a deterministic-only, dry-run-first corpus remediation runner that builds on 008 corpus index and 009 corpus remediation plan. The runner refreshes the remediation plan, selects ready deterministic actions, supports confirmed execution only with filters, writes latest deterministic run reports only after confirmed runs, and excludes download, transcription, LLM, MCP, network, `.env`, cache rebuild, and investment advice behavior."

## Clarifications

### Session 2026-07-09

- Q: Should dry-run write `corpus-remediation-run.json/.md` artifacts? -> A: No. Dry-run returns the planned run report in stdout only; confirmed execution writes the latest deterministic run report artifacts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Safe Corpus Remediation (Priority: P1)

A local operator wants to preview which deterministic corpus remediation actions are ready to run for a podcast without writing downstream artifacts or changing local corpus state.

**Why this priority**: This is the minimum safe step after 009. It lets users inspect the execution set, exclusions, blockers, and risks before any side effects occur.

**Independent Test**: A local corpus with a refreshed remediation plan can produce a dry-run result containing selected, skipped, blocked, and excluded actions, while no downstream artifact or run report artifact is written.

**Acceptance Scenarios**:

1. **Given** a podcast with a remediation plan containing ready deterministic actions, **When** the user previews corpus remediation without confirmation, **Then** the system refreshes the plan, returns selected and skipped action counts, and writes no run report artifact.
2. **Given** a remediation plan containing audio, transcript, semantic summary, or semantic review actions, **When** the user previews corpus remediation, **Then** those actions are excluded with factual reasons and are not selected for execution.
3. **Given** a remediation plan containing blocked actions, **When** the user previews corpus remediation, **Then** blocked actions remain visible as skipped or blocked with their blocking artifact reasons.

---

### User Story 2 - Execute Filtered Deterministic Remediation (Priority: P2)

A local operator wants to confirm a bounded execution run that performs only deterministic actions for one episode or one action family, then receives an auditable run report.

**Why this priority**: Confirmed execution is useful only when blast radius is bounded. Requiring filters prevents accidentally running the entire corpus.

**Independent Test**: A confirmed run with either an episode filter or an action-family filter executes only ready deterministic actions matching the filter, records outputs and counts, and writes deterministic JSON and Markdown run reports.

**Acceptance Scenarios**:

1. **Given** a user requests confirmed remediation without an episode or action-family filter, **When** the runner is invoked, **Then** the run is rejected before executing any action.
2. **Given** a user confirms remediation for one action family, **When** ready deterministic actions exist for that family, **Then** only matching selected actions are executed and the run report records executed, reused, skipped, and failed counts.
3. **Given** a user confirms remediation for one episode, **When** ready deterministic actions exist for that episode, **Then** only that episode's selected deterministic actions are executed in dependency order.

---

### User Story 3 - Contain Failures and Preserve Safety Boundaries (Priority: P3)

A local operator wants one failed action to be recorded without hiding unrelated ready work, leaking sensitive content, or weakening project safety boundaries.

**Why this priority**: Corpus remediation may operate over incomplete or inconsistent local artifacts. Failures need to be auditable and isolated.

**Independent Test**: A confirmed run with one action failure records the failure, skips same-run downstream actions that depend on that failed artifact, continues unrelated ready actions, and emits no raw transcript, evidence snippet, semantic body, prompt, raw LLM output, secret, or investment advice.

**Acceptance Scenarios**:

1. **Given** one selected deterministic action fails, **When** the confirmed run continues, **Then** the failure is recorded for that action and unrelated selected actions still receive deterministic outcomes.
2. **Given** a selected action fails and a later selected action in the same episode depends on it, **When** the later action is reached, **Then** the later action is skipped with a failed-dependency reason.
3. **Given** source artifacts contain transcript text, evidence text, semantic content, prompt text, or secret-like values, **When** the run result is produced, **Then** JSON, Markdown, and stdout include only metadata, paths, counts, statuses, and warnings.

### Edge Cases

- Empty local corpus produces a valid dry-run result with zero selected actions and no run report artifact.
- A remediation plan with only excluded families produces zero selected actions and factual exclusion reasons.
- Confirmed execution without `episode_ref` or `action_family` is rejected before any action execution.
- `max_actions=0` is rejected as invalid input; positive `max_actions` limits selected actions deterministically after filtering.
- Repeated dry-runs over unchanged local artifacts produce identical stdout payload content except transport formatting.
- Repeated confirmed runs over unchanged already-satisfied local artifacts produce deterministic report shape and mark reused outcomes rather than fabricating new work.
- One failed action records failure and skips same-run downstream selected actions that require the failed family; unrelated selected actions continue.

### Safety and Data Boundaries *(mandatory for research, LLM, MCP, or external-data work)*

- This feature reads only local corpus remediation plan metadata and local per-episode deterministic artifact metadata. It refreshes the 009 remediation plan before selecting actions.
- This feature's dry-run mode must not write downstream artifacts or run report artifacts; it returns a planned report in stdout only.
- Confirmed execution may write deterministic local artifacts produced by existing deterministic generators and may write latest run report artifacts under `data/corpus/{podcast_id}/`.
- This feature must not execute audio download, transcription, semantic summary, semantic review, stock-lens query inventory, stock-lens synthesis, LLM calls, MCP tools, RSS reads, network calls, live market data calls, `.env` reads, or SQLite cache rebuilds.
- This feature must not add, remove, or change MCP tools or MCP response envelopes.
- This feature must not output raw transcript text, evidence snippets, semantic summary body text, prompt text, raw LLM output, `.env` values, API keys, tokens, or provider secret values.
- External-data boundary/status entries remain availability markers and must not be presented as market facts.
- The generated run output must not include buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or statements implying an investment action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run corpus remediation for exactly one requested podcast identifier.
- **FR-002**: System MUST refresh the 009 corpus remediation plan before selecting actions for every run.
- **FR-003**: System MUST default to dry-run mode and MUST NOT write downstream artifacts or run report artifacts in dry-run mode.
- **FR-004**: System MUST return dry-run selected, skipped, blocked, excluded, and warning counts through the local command output.
- **FR-005**: System MUST only select ready actions whose artifact family is one of `extractive_summary`, `mentions`, `episode_intelligence`, `industry_mapping`, or `external_boundary`.
- **FR-006**: System MUST exclude audio, transcript, semantic summary, semantic review, stock-lens, synthesis, and any unknown action family from execution selection with factual skip reasons.
- **FR-007**: System MUST reject confirmed execution unless at least one selection filter is provided: one episode reference or one action family.
- **FR-008**: System MUST apply episode and action-family filters before applying a positive maximum-action limit.
- **FR-009**: System MUST execute selected confirmed actions in deterministic dependency order and MUST NOT shell out to local scripts to perform action work.
- **FR-010**: System MUST write `data/corpus/{podcast_id}/corpus-remediation-run.json` and `.md` only after confirmed execution is attempted.
- **FR-011**: System MUST keep run report content deterministic for unchanged local inputs and confirmed outcomes, including no generation timestamp.
- **FR-012**: System MUST record selected, executed, reused, failed, skipped, blocked, excluded, and warning counts in JSON, Markdown, and command output.
- **FR-013**: System MUST record per-action outcome rows with podcast identifier, episode reference, artifact family, action status, source remediation action id, output paths when available, and warnings when present.
- **FR-014**: System MUST contain single-action failures by recording the failed action, skipping same-run downstream selected actions that depend on the failed family, and continuing unrelated selected actions.
- **FR-015**: System MUST provide a thin local command surface that can preview by podcast and confirmed-run by podcast plus episode or action-family filter.
- **FR-016**: System MUST preserve existing MCP behavior by not adding, removing, or changing MCP tools in v1.
- **FR-017**: System MUST preserve no-leak boundaries for transcript text, evidence text, semantic body text, prompt text, raw LLM output, `.env` values, API keys, tokens, and provider secret values.
- **FR-018**: System MUST preserve no-investment-advice boundaries in all runner outputs.

### Key Entities *(include if feature involves data)*

- **Corpus Remediation Run**: One dry-run or confirmed remediation selection for one podcast. Key attributes include podcast identifier, mode, source remediation plan paths, filters, selected count, outcome counts, warnings, and run rows.
- **Run Action Row**: One selected, skipped, excluded, executed, reused, or failed action derived from a remediation action. Key attributes include episode reference, artifact family, action id, status, reason, output paths, and warning messages.
- **Run Selection Filter**: The bounded criteria applied to a remediation plan before execution. Key attributes include optional episode reference, optional action family, and optional maximum action count.
- **Run Warning**: A non-fatal warning associated with the run or a specific action row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For an empty local corpus, users receive a dry-run result with zero selected actions, zero executed actions, and no run report artifact written.
- **SC-002**: For a remediation plan containing at least five actions across deterministic and excluded families, dry-run output identifies all selected deterministic actions and all excluded non-deterministic families with counts.
- **SC-003**: For confirmed execution without an episode or action-family filter, zero actions execute and the user receives a clear rejection.
- **SC-004**: For a confirmed run filtered to one ready deterministic action family, 100% of executed action rows belong to that family.
- **SC-005**: For a confirmed run where one selected action fails, the failed action is recorded and unrelated selected actions still receive an outcome.
- **SC-006**: Generated run outputs contain zero raw transcript snippets, zero evidence text snippets, zero semantic body text snippets, zero prompt text, zero raw LLM response text, and zero secret values.
- **SC-007**: The existing MCP reviewed tool count and response envelope remain unchanged after the feature is delivered.

## Assumptions

- Package `009-corpus-remediation-plan` is available and remains the source of action status and ordering.
- A run report is a latest-state derived artifact that may be overwritten by later confirmed runs.
- Dry-run report content is returned in command output only to preserve the constitution dry-run no-write boundary.
- Deterministic execution uses existing local artifact generators and does not add new research semantics.
- Cache rebuild remains manual after confirmed remediation writes artifacts.
