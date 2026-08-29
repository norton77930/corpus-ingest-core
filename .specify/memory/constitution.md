<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template principle placeholders -> Local Artifacts and Evidence Traceability
- Template principle placeholders -> Thin Interfaces over Thick Core
- Template principle placeholders -> Dry-Run First Side Effects
- Template principle placeholders -> LLM Opt-In and Secret Boundary
- Template principle placeholders -> Evidence, Inference, and External Status Separation
- Template principle placeholders -> No Investment Advice
- Template principle placeholders -> Manual Cache Rebuild
- Template principle placeholders -> TDD and Verification Gates
Added sections:
- Research and Data Boundaries
- Spec Kit Development Workflow
Removed sections:
- Placeholder principle and section tokens from the official template
Templates requiring updates:
- updated: .specify/templates/plan-template.md
- updated: .specify/templates/spec-template.md
- updated: .specify/templates/tasks-template.md
- updated: .specify/templates/checklist-template.md
- N/A: .specify/templates/commands/*.md is not present in this scaffold
Follow-up TODOs: none
-->
# Podcast Ingestion Core / Gooaye Research System Constitution

## Core Principles

### I. Local Artifacts and Evidence Traceability

All research outputs MUST be derived from local artifacts or explicitly approved
provider responses. Podcast-derived claims MUST preserve timestamp evidence when
the source contains transcript segments or mention evidence. Generated artifacts
MUST keep source paths, source status, warnings, and reuse/regeneration status
auditable in JSON and Markdown outputs.

Rationale: the research system is useful only when users can trace conclusions
back to podcast evidence, deterministic config, external verification status, or
LLM synthesis boundaries.

### II. Thin Interfaces over Thick Core

Runtime behavior MUST live in `src/corpus_ingest_core`. CLI scripts and MCP
tools MUST remain thin wrappers that parse inputs, call core functions, and
format responses. Public core functions MUST keep stable contracts unless a
future approved phase explicitly changes them with tests and documentation.

Rationale: core-first design keeps CLI, MCP, tests, and future automation
consistent while avoiding duplicated research logic.

### III. Dry-Run First Side Effects

Side-effect workflows that write artifacts, call providers, download data, or
perform potentially expensive work MUST provide dry-run behavior where practical.
Dry-run responses MUST list planned reads, planned writes, step order, required
confirmation, and known risks without writing artifacts or calling providers.
Confirmed execution MUST be explicit through the relevant `confirm=True` or CLI
flag.

Rationale: the project is used for local research automation, so planned writes
and external risks must be visible before execution.

### IV. LLM Opt-In and Secret Boundary

LLM execution MUST be opt-in. Confirmed LLM calls MUST require exact `api_cost_ack`
text before provider construction. Stock lens synthesis MUST use
only `phase-6f-stock-lens-json-only` input; semantic summary is the only current
path that may send transcript text to an LLM, and only after explicit
acknowledgement. `.env` values, API keys, tokens, and provider secret values MUST
not be printed, written to committed files, returned in MCP responses, or stored
in review reports.

Rationale: LLM calls may send data outside the machine and incur costs; secret
handling must remain local and explicit.

### V. Evidence, Inference, and External Status Separation

Research artifacts MUST distinguish podcast evidence, deterministic inference,
external verification status, and LLM-generated synthesis. `podcast_explicit`
means the podcast evidence contains the company, ticker, or mention. An
`inferred_from_industry` candidate is only a research lead and MUST remain
`needs_verification` until external verification changes its external status.
External status values such as `not_requested`, `not_fetched`, and
`data_date=null` MUST remain availability/status markers, not market facts.

Rationale: a useful research layer must not confuse what Gooaye said, what the
local mapping inferred, what external data verified, and what an LLM summarized.

### VI. No Investment Advice

The system MUST NOT provide buy/sell/hold recommendations, target prices,
guaranteed returns, personalized investment advice, or a statement that implies
an investment action. Reports and synthesis artifacts MUST retain no investment
advice notices and MUST reject obvious prohibited advice output.

Rationale: this project supports evidence-based research organization, not
regulated investment recommendation.

### VII. No Live Market API Without Approval

External market data MUST remain a boundary scaffold or local fixture provider
unless a future approved phase explicitly adds a live provider. Current fixture
verification MUST NOT read API keys, call HTTP providers, or fabricate missing
company, ticker, price, financial, or news facts. The default project boundary
is no live market API.

Rationale: live provider integration changes data freshness, costs, legal risk,
and failure modes, so it requires its own spec and tests.

### VIII. Manual Cache Rebuild

SQLite cache rebuild MUST remain a manual operation. Side-effect tools and
workflow steps MAY warn that cache metadata may be stale, but MUST NOT
automatically run `rebuild_cache` after writing artifacts.

Rationale: cache state is derived and can be regenerated, but automatic rebuilds
hide side effects and make workflow outcomes harder to audit.

### IX. TDD and Verification Gates

New behavior MUST be covered by targeted tests written before implementation
where practical. Documentation/spec-only phases MUST include docs tests that
lock the intended guidance. Before claiming completion, the relevant targeted
tests, `python -m pytest`, and `python -m compileall src scripts` MUST be run or
the reason for skipping MUST be stated.

Rationale: this project has many safety boundaries; tests are the executable
record that those boundaries still hold.

## Research and Data Boundaries

Research phases MUST preserve local artifact ownership:

- Transcript, summary, mention, report, mapping, external boundary, stock lens,
  synthesis, and review artifacts remain local files under the established
  `data/` or `evals/` paths.
- Historical artifacts and eval reports are audit records and MUST NOT be
  rewritten unless a user explicitly requests regeneration.
- `.env` is local convenience configuration. It MUST NOT be committed and MUST
  NOT be read by docs/eval-only phases.
- MCP responses MUST use their existing success, dry-run, and error envelopes
  unless a future approved phase changes that contract.

## Spec Kit Development Workflow

Future functional work MUST use the full Spec Kit flow before implementation:

1. `$speckit-constitution` establishes or amends project principles.
2. `$speckit-specify` captures user-facing requirements.
3. `$speckit-clarify` resolves high-impact ambiguity before technical planning.
4. `$speckit-plan` creates the technical plan and design artifacts.
5. `$speckit-checklist` creates feature-specific quality and safety checks.
6. `$speckit-tasks` creates dependency-ordered implementation tasks.
7. `$speckit-analyze` checks spec, plan, and tasks for contradictions.
8. `$speckit-implement` executes the approved task list.
9. `$speckit-converge` compares code with spec/plan/tasks and adds missing work.

`$speckit-taskstoissues` is optional and is used only when GitHub issue handoff
is needed. Small docs/test corrections may be handled directly when the user
provides a concrete plan, but they still MUST preserve this constitution.

## Governance

This constitution supersedes conflicting local habits, ad hoc phase plans, and
generated Spec Kit output. Amendments MUST update this file, include a Sync
Impact Report, and propagate any changed rules into affected templates, docs,
tests, and agent instructions. Versioning follows semantic governance:

- MAJOR for incompatible governance changes or removed safety boundaries.
- MINOR for new principles, new required workflow gates, or materially expanded
  safety requirements.
- PATCH for wording clarifications that do not change meaning.

Every implementation review MUST check compliance with dry-run behavior, LLM
acknowledgement, secret handling, evidence separation, external-data boundaries,
manual cache rebuild, no investment advice, and verification commands.

**Version**: 1.0.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-06-30
