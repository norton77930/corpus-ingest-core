# Feature Specification: Workflow Derivation Bundle

**Feature Branch**: `042-workflow-derivation-bundle`
**Created**: 2026-08-20
**Status**: Implemented

**Input**: Spec 038 shipped the evidence-bound lecture (`00` / `03` / `04` / `07`) and left prototype `05_prompt_examples.md` and `06_apply_to_my_workflow.md` out, because they are workflow derivations, not transcript summaries. Mixing them into the lecture family produces fabricated operator-tool advice. This spec adds a **separate** derivation family that applies an existing lecture to an operator-supplied workflow context.

## Clarifications

### Session 2026-08-20

Recommended defaults from HANDOFF Task A and Spec 038 Assumption 1, adopted so this package can proceed without blocking:

- Q: Do `05` / `06` belong in this repository? → A: **Yes, as a new family, not as Spec 038 files.** The lecture family stays `study_guide` (`00`/`03`/`04`/`07` only). Derivation is `workflow_derivation` (`05` + `06`). A complete lecture must not look unfinished just because derivations are absent, and a pair of prompt templates must not look like a finished lecture.
- Q: What operator context is required? → A: **A named local workflow-context document the operator supplies.** It lists the tools and surfaces 06 may discuss (for this operator: Claude Code, Codex, GitHub Copilot, CLAUDE.md, Skills, spec / plan / tasks). 05/06 MUST NOT advise a tool that is absent from that document. Missing context fails closed. The runner does not invent a personal workflow from the lecture alone.
- Q: May this send transcript text to an LLM? → A: **No.** Input is the existing lecture (`03`/`04`/`07`) plus the operator context. Principle IV is unamended: semantic summary remains the only transcript-to-LLM path.
- Q: MCP tool? → A: **No.** Core plus a thin CLI. Registry stays at exactly 24.

## User Scenarios & Testing

### User Story 1 — Apply the lecture to my tools (Priority: P1)

The operator has a finished Spec 038 lecture and a workflow-context document. They ask for the derivation pair and receive two documents that match the prototype reading order: reusable prompt examples (`05`) and how to apply the lecture to the named tools (`06`).

**Why this priority**: This is the held-out half of the eight-file sequence. The lecture is already shippable; this is the personal application layer.

**Independent Test**: For a learning-notes episode whose `study_guide` family is available, with a fixture workflow context that names Claude Code and Codex only, one confirmed run writes `05` and `06` whose `06` may discuss those two tools and must not introduce GitHub Copilot as advice.

**Acceptance Scenarios**:

1. **Given** an available lecture bundle and a readable workflow context, **When** the operator confirms the run, **Then** `05_prompt_examples.md` and `06_apply_to_my_workflow.md` exist beside the lecture files and the `workflow_derivation` family is `available`.
2. **Given** that run, **When** `05` is read, **Then** it contains a bad-vs-good prompt comparison grounded in the lecture, plus at least one reusable prompt template, and any catalogue not supported by the lecture is labelled reconstructed or 不確定事項.
3. **Given** that run, **When** `06` is read, **Then** it maps lecture ideas onto only the tools named in the workflow context, and does not tell the operator to buy, sell, or hold anything.
4. **Given** a workflow context that omits Copilot, **When** `06` is read, **Then** it does not advise GitHub Copilot.

---

### User Story 2 — Dry-run tells the truth and writes nothing (Priority: P1)

The default call plans the two writes, names the lecture files and the workflow context it would read, and writes nothing. It does not call an LLM.

**Why this priority**: Principle III. Same class of plan-honesty Spec 036 and 038 already enforce.

**Independent Test**: `confirm=false` against a fixture episode returns planned reads/writes and performs zero filesystem writes and zero provider calls.

**Acceptance Scenarios**:

1. **Given** a ready episode, **When** dry-run runs, **Then** the plan lists the lecture paths, the workflow-context path, the two planned write paths, and that cache will not be rebuilt.
2. **Given** existing `05`/`06` that would be reused, **When** dry-run runs, **Then** the plan says reuse, not write.
3. **Given** any dry-run, **When** the tree is compared before and after, **Then** it is identical, including no `.part` files.
4. **Given** dry-run, **When** stdout is inspected, **Then** it is metadata-only JSON: no lecture body, no prompt, no secret, no transcript.

---

### User Story 3 — Missing lecture, wrong profile, or missing context fail closed (Priority: P1)

A finance episode, a lecture that is only `partial`, a missing workflow context, or a missing lecture is refused before any LLM work and before any write. The Spec 038 files are left untouched.

**Why this priority**: Derivations must not invent a lecture, and must not leak finance/gooaye into a coding-workflow document.

**Independent Test**: Fixture cases — finance profile, missing lecture, partial lecture, missing context — each raise a named error, write zero files, and make zero provider calls.

**Acceptance Scenarios**:

1. **Given** `summary_profile=finance` (including gooaye), **When** the runner is invoked, **Then** it refuses and writes nothing.
2. **Given** a learning-notes episode whose `study_guide` family is missing or `partial`, **When** the runner is invoked, **Then** it refuses and does not generate a lecture.
3. **Given** a missing or unreadable workflow-context document, **When** the runner is invoked, **Then** it refuses, naming that the operator must supply context.
4. **Given** any of those refusals, **When** the lecture directory is inspected, **Then** `00`/`03`/`04`/`07` are unchanged.

---

### User Story 4 — Honesty about reconstruction (Priority: P2)

Prompt examples that are not quoted from the lecture are labelled as reconstructed. Workflow advice never claims the speaker named a tool they did not name.

**Why this priority**: Spec 037's real run already admitted reusable prompts were reconstructed. Completing `05`/`06` without that label would undo the evidence rule.

**Independent Test**: A lecture fixture with no reusable-prompt section still produces `05`, and every invented template sits under a reconstructed / 不確定事項 label. `06` does not claim the speaker said "Claude Code" unless that string is already in the lecture or the operator context is describing the operator, not the speaker.

**Acceptance Scenarios**:

1. **Given** a lecture without a prompt-template section, **When** `05` is produced, **Then** daily-engineering prompt catalogues are labelled reconstructed or 不確定事項, not as quotes from the film.
2. **Given** a lecture that never mentions Claude Code, **When** `06` maps an idea onto Claude Code because the operator context named that tool, **Then** the mapping is labelled as operator application, not as something the speaker instructed.

---

### Edge Cases

- `force=true` replaces both derivation files atomically; it does not rewrite the lecture four.
- One of `05`/`06` present and the other missing is `partial`, not available.
- Workflow context that names a tool the lecture never discussed is still allowed for `06` as operator application, and must stay labelled as such.
- Workflow context that is empty of tool names fails closed.
- Confirmed execution without exact acknowledgement does not construct a provider and does not write.
- Investment-shaped wording in the lecture cannot become buy/sell/hold advice in `05`/`06`.

### Safety and Data Boundaries

- Reads: existing lecture Markdown (`03`/`04`/`07`), operator workflow-context document, podcast profile. Does not read transcript, `.env` values, or live market data.
- Writes: `05` and `06` plus a metadata-only run report. Dry-run first. Lecture files are never rewritten.
- LLM: optional, confirmed only, exact `api_cost_ack` before provider construction. Input is lecture text + operator context, never transcript.
- Secrets: `.env` / API keys / tokens must not appear in stdout, artifacts, or reports.
- External data: unused. Status values are not market facts.
- Investment: no buy/sell/hold, target price, guaranteed return, or personalized investment advice.
- Cache: warn only; no automatic rebuild.
- MCP: none. Registry remains 24.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose a dry-run-first Core operation that writes `05_prompt_examples.md` and `06_apply_to_my_workflow.md` for one named episode.
- **FR-002**: The derivation family MUST be distinct from `study_guide`. Lecture availability MUST NOT depend on `05`/`06`. Derivation availability MUST require both files readable.
- **FR-003**: Confirmed runs MUST require an available Spec 038 lecture (`00`/`03`/`04`/`07` all readable) on a `learning-notes` profile.
- **FR-004**: Confirmed runs MUST require a readable operator workflow-context document that names at least one allowed tool or surface.
- **FR-005**: `06` MUST NOT advise a tool or surface absent from that context.
- **FR-006**: Dry-run MUST list actual lecture paths, the context path, planned writes or reuses, cache-stale warning, and LLM/ack risk, and MUST write nothing and call no provider.
- **FR-007**: Confirmed LLM work MUST require exact `api_cost_ack` before provider construction.
- **FR-008**: The runner MUST NOT send transcript text to a provider.
- **FR-009**: Reconstructed prompt catalogues and operator-application mappings MUST be labelled as such, not as speaker quotes.
- **FR-010**: Finance / gooaye profiles MUST be refused. Existing lecture and finance artifacts MUST remain unchanged.
- **FR-011**: `05`/`06` writes MUST be atomic as a pair: success leaves both new files; failure leaves the previous pair (or neither), never one new file and one old file.
- **FR-012**: Thin CLI only. No MCP tool. Registry stays at exactly 24.
- **FR-013**: No automatic cache rebuild. No live market API. No investment advice.
- **FR-014**: `05` MUST include a bad-vs-good prompt contrast grounded in the lecture and at least one reusable template; `06` MUST map lecture ideas onto the named tools (how to use the idea in each named surface, plus what to watch for when prompting later).

### Key Entities

- **Lecture bundle**: the existing four-file `study_guide` for one episode; read-only input.
- **Operator workflow context**: a local document listing tools/surfaces the operator actually uses; required input.
- **Derivation pair**: `05_prompt_examples.md` and `06_apply_to_my_workflow.md`; written together.
- **Derivation run report**: metadata-only JSON + Markdown describing reads, writes, reuse, and warnings.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An operator with a finished lecture and a workflow-context document can obtain both derivation files in one confirmed action without opening a second summarisation pass on the audio.
- **SC-002**: A fixture whose context omits a tool never receives advice for that tool in `06`.
- **SC-003**: Dry-run against a ready fixture writes zero files and calls no provider.
- **SC-004**: Finance / gooaye episodes remain byte-identical after a refused run.
- **SC-005**: A lecture without native prompt examples still yields `05`, with reconstructed material labelled, and no invented speaker-attributed tool instruction.
- **SC-006**: The reviewed MCP registry remains exactly 24 tools.
- **SC-007**: Full repository regression adds no non-Hermes failures.

## Assumptions

1. The prototype `05` / `06` headings and intent are the design, not something to reinvent. v1 realises them as a derivation family that requires operator context.
2. Default operator context for this machine names Claude Code, Codex, GitHub Copilot, CLAUDE.md, Skills, and spec / plan / tasks — because that is this operator's actual workflow — but the runner still reads it from a file rather than hard-coding those names in Core.
3. One confirmed LLM call may emit both documents. Two independent calls are not required.
4. Derivations are not lineage inputs for verified research reports in v1.
5. Existing 038 bundles are not migrated. `force=true` replaces only the derivation pair.
6. Translation (`02`) and grouped-transcript persistence (`01`) stay out of scope.
7. Principle IV is not amended.

## Out of Scope (v1)

- Rewriting Spec 038 lecture files.
- Sending transcript text to an LLM.
- Regenerating or reviewing the semantic summary.
- MCP exposure.
- A third summary profile.
- Making verified-research lineage consume `05`/`06`.
- Automatic cache rebuild, live market API, investment advice, Hermes work.
