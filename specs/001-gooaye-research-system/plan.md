# Gooaye Research System Implementation Plan

## Technical Context

Phase 7A: Architecture / Spec Kit Stabilization records the current implementation state after Phase 6T. This is a docs/spec-only stabilization pass: no runtime behavior change, no MCP behavior change, no LLM call, no `.env` read, and no artifact schema change.

Phase 7B: Official Spec Kit Bootstrap adds the official Spec Kit scaffold. `.specify` now stores memory, templates, scripts, workflow metadata, and integration metadata; `.agents/skills` stores Codex skills mode `$speckit-*` skills; `AGENTS.md` stores repo-level agent rules.

Phase 7C: Spec Kit Constitution + Workflow Alignment turns the scaffold into project governance. It updates the constitution, templates, AGENTS, architecture, roadmap, and spec plan so future work uses the full Spec Kit flow. This is docs/spec/tests only: no runtime behavior change, no MCP behavior change, no LLM call, no `.env` read, no live market API, and no investment advice.

Phase 7D: Spec Kit Backfill via Full Workflow performs capability-group backfill for existing implemented behavior. `specs/README.md` is the registry, `001-gooaye-research-system` remains the umbrella product spec, and packages such as `002-ingestion-transcript-core` and `006-llm-safety-synthesis-smoke-review` document as-built capability groups. This is docs/spec/tests only: no runtime behavior change, no MCP behavior change, no LLM call, no `.env` read, no live market API, and no investment advice.

Phase 7D.1: Spec Kit Active Feature Guidance documents official Spec Kit command usability for the backfilled packages. Feature packages live under `specs/<feature>`; `.specify/` stores scaffold, memory, templates, scripts, integration, and workflow metadata. Backfilled packages do not pin one active feature by default. Before running package-specific Spec Kit scripts or skills, set `SPECIFY_FEATURE_DIRECTORY`; the official scripts may persist the value to `.specify/feature.json`, and switching packages means setting the env var again. This is docs/spec/tests only: no runtime behavior change, no MCP behavior change, no LLM call, no `.env` read, no live market API, and no investment advice.

The current stack is a Python package with thin CLI scripts, local file artifacts under `data/`, deterministic YAML config, optional OpenAI-compatible LLM calls, stdio MCP exposure, SQLite cache/search, and pytest contract coverage.

## Architecture Decisions

- Keep core behavior in `src/corpus_ingest_core`; scripts remain thin wrappers.
- Preserve local artifacts as the source of truth for the research layer.
- Keep deterministic research steps separate from optional LLM steps.
- Keep stock lens synthesis input constrained to `phase-6f-stock-lens-json-only` by default; Phase 6V opt-in reviewed semantic context must use `phase-6f-stock-lens-json-plus-reviewed-semantic-summary` and pass Phase 6V.1 boundary/context consistency checks.
- Keep external market data as boundary or local fixture data only; no live market API.
- Keep `.env` local-only. It must not be committed and must not be read by docs/eval-only commands.
- Keep investment safety explicit: no buy/sell/hold, no target price, no guaranteed return.

## Phase Status

- Phase 6B-6F provide deterministic episode intelligence, industry mapping, external boundary, Gooaye Lens, and stock lens report artifacts.
- Phase 6G-6N provide local workflow orchestration, optional semantic summary, optional stock lens synthesis, MCP exposure, fixture verification, and workflow fixture integration.
- Phase 6O-6T provide LLM smoke tooling, LLM profile and `.env` ergonomics, raw-output debug support, guard tuning, and deterministic smoke review gate.
- Phase 7A aligns architecture and spec-kit documents with the implemented Phase 6T state.
- Phase 7B formally bootstraps official Spec Kit scaffold while preserving existing Gooaye research system spec files.
- Phase 7C aligns `.specify/memory/constitution.md`, `.specify/templates/`, and agent/docs guidance with project safety gates and the full Spec Kit flow: `$speckit-constitution`, `$speckit-specify`, `$speckit-clarify`, `$speckit-plan`, `$speckit-checklist`, `$speckit-tasks`, `$speckit-analyze`, `$speckit-implement`, `$speckit-converge`, with `$speckit-taskstoissues` reserved for GitHub issue handoff.
- Phase 7D backfills existing capabilities into Spec Kit packages using the full Spec Kit flow, including `$speckit-clarify`, `$speckit-analyze`, and `$speckit-converge`.
- Phase 7D.1 documents active feature selection for official Spec Kit scripts and skills through `SPECIFY_FEATURE_DIRECTORY` and `.specify/feature.json`, without moving feature packages out of `specs/<feature>`.

## Next Work

After Phase 7D.1, the recommended next functional phase is Phase 6U semantic summary smoke validation or a small prompt/output-quality tuning phase. That work should use the same dry-run first, exact acknowledgement, no live market API, no investment advice boundaries, and the full Spec Kit flow before implementation.
