# Architecture

This document reflects the Phase 7C system shape. Podcast Ingestion Core is still a thin-CLI / thick-core Python package, but the repo now includes a research layer, optional LLM paths, MCP exposure, deterministic eval / review gates, official Spec Kit bootstrap files, and a project-specific Spec Kit constitution.

## Core Principles

- CLI scripts parse arguments and call `podcast_ingest_core` core functions; runtime behavior belongs in the package.
- Podcast-specific configuration stays in `config/podcasts.yaml`; core modules must accept a generic `podcast_id`.
- Source artifacts remain local files under `data/`; SQLite cache and eval reports are derived or audit artifacts.
- Side-effect operations are dry-run first where practical. LLM calls require explicit acknowledgement.
- Research outputs must separate podcast evidence, deterministic inference, external verification status, and LLM-generated synthesis.
- Phase 7A is documentation/spec stabilization only: no runtime behavior change, no MCP behavior change, no LLM call, and no `.env` read.
- Phase 7B bootstraps official Spec Kit scaffold: `.specify` stores memory/templates/scripts/workflow metadata, `.agents/skills` stores Codex `$speckit-*` skills, and `AGENTS.md` stores repo-level agent instructions.
- Phase 7C is Spec Kit Constitution + Workflow Alignment: `.specify/memory/constitution.md` and `.specify/templates/` encode the project gates for dry-run, exact LLM acknowledgement, evidence separation, external-data status, no live market API, no `.env` read, and no investment advice.
- Future feature work should use the full Spec Kit flow: `$speckit-constitution`, `$speckit-specify`, `$speckit-clarify`, `$speckit-plan`, `$speckit-checklist`, `$speckit-tasks`, `$speckit-analyze`, `$speckit-implement`, and `$speckit-converge`; `$speckit-taskstoissues` is only for GitHub issue handoff.
- Phase 7D is Spec Kit Backfill via Full Workflow: `specs/README.md` maps existing capability-group backfill packages such as `002-ingestion-transcript-core` and `006-llm-safety-synthesis-smoke-review` to roadmap phases, modules, CLI/scripts, and tests. This remains docs/spec/tests only with no runtime behavior change, no MCP behavior change, no LLM call, no `.env` read, no live market API, and no investment advice.
- Phase 7D.1 is Spec Kit Active Feature Guidance: feature packages live under `specs/<feature>`, while `.specify/` stores scaffold, memory, templates, scripts, integration, and workflow metadata. Backfilled packages do not pin one active feature by default; set `SPECIFY_FEATURE_DIRECTORY` before running package-specific Spec Kit scripts or skills, and reset it when switching packages. This is Spec Kit command usability documentation only with no runtime behavior change, no `.env` read, no live market API, and no investment advice.
- Phase 6U semantic summary smoke validates the transcript-transfer LLM path through dry-run-first smoke CLI and deterministic review gate. Confirmed execution requires exact `api_cost_ack`; CLI output keeps no raw transcript stdout, no MCP behavior change, no live market API, and no investment advice.
- Phase 6V reviewed semantic context is optional for stock lens synthesis. Default synthesis remains `phase-6f-stock-lens-json-only`; opt-in synthesis may read only review-passed `.semantic.md` metadata/final summary context and marks `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`, with no raw transcript, no live market API, no MCP behavior change, and no investment advice.
- Phase 6V.1 aligns the research LLM smoke review gate with boundary/context consistency: JSON-only synthesis must have no semantic context, and reviewed semantic synthesis must include non-empty, review-passed semantic context.

## Current Module Groups

- ingestion: `feed_reader.py`, `downloader.py`, and `transcriber.py` list episodes, download audio, and create transcript artifacts.
- transcript validation and summaries: `validator.py`, `summarizer.py`, and `semantic_summarizer.py` validate transcript status, create deterministic extractive summaries, and optionally create LLM semantic summaries.
- mentions and search: `entity_extractor.py`, `cache.py`, and `search.py` create deterministic mentions and index/search transcripts and mentions.
- research reports: `episode_intelligence.py`, `industry_mapping.py`, `external_data_boundary.py`, `external_data_verification.py`, `gooaye_lens.py`, and `stock_lens.py` build deterministic research artifacts from existing local sources.
- LLM synthesis and smoke review: `stock_lens_synthesis.py`, `research_workflow.py`, `research_llm_smoke_review.py`, and `semantic_summary_smoke_review.py` support optional LLM synthesis, workflow orchestration, the Phase 6T review gate, and Phase 6U semantic summary smoke review.
- corpus status: `corpus_index.py` scans local per-episode artifacts and semantic review metadata, then writes deterministic JSON/Markdown under `data/corpus/{podcast_id}/`.
- interfaces: scripts under `scripts/` are thin CLIs; `mcp_server.py` wraps selected core functions in stdio MCP tools.
- shared contracts: `models.py`, `storage.py`, `errors.py`, `llm_provider.py`, `llm_profiles.py`, `local_env.py`, and `serialization.py` hold common data, paths, errors, provider settings, local `.env` loading, and JSON serialization.

## Data Flow

1. ingestion reads RSS metadata and writes audio/transcript files under `data/audio/` and `data/transcripts/`.
2. transcript validation classifies transcript status before summary or research steps run.
3. deterministic summaries and optional LLM semantic summary write `data/summaries/`.
4. deterministic mentions write `data/mentions/` and can be indexed into SQLite cache.
5. episode intelligence reads transcript metadata and mentions, then writes `data/reports/`.
6. industry mapping reads episode intelligence plus local mapping config, then writes `data/mappings/`.
7. external boundary writes `data/external/` with `not_requested`, `not_fetched`, and `data_date=null` until external checks are performed.
8. local fixture verification can update external boundary metadata from `config/external_market_data_fixtures.yaml`; this is a local fixture path, not a live provider.
9. stock lens reads podcast-wide mapping and external boundary artifacts, then writes `data/stock-lens/`.
10. LLM synthesis optionally reads Phase 6F stock lens JSON only and writes `.stock-lens-synthesis.*`.
11. Phase 6T review gate reads existing synthesis artifacts and writes deterministic review reports under `evals/research-llm-smoke/reports/`.
12. Phase 6U semantic summary smoke review reads existing `.semantic.md` artifacts and writes deterministic review reports under `evals/research-llm-smoke/reports/`.
13. Corpus artifact index reads only local per-episode artifact paths/metadata and latest semantic review status, then writes `data/corpus/{podcast_id}/corpus-index.json` and `.md` without raw transcript, evidence, semantic body, RSS, SQLite cache, `.env`, network, LLM, or MCP changes.
14. MCP tools expose read/search, selected side-effect tools, and consolidated research workflow; MCP completion warns about stale cache but does not rebuild automatically.

## Execution Modes

- deterministic steps: ingestion after user command, transcript validation, extractive summary, mention extraction, episode intelligence, industry mapping, external boundary, stock lens report, cache indexing, Phase 6T review gate, Phase 6U semantic summary smoke review gate, and corpus artifact index generation.
- optional LLM steps: semantic summary and stock lens synthesis. These require `confirm=True` and the exact API-cost acknowledgement before provider construction; `run_semantic_summary_smoke.py` dry-run keeps no raw transcript stdout. Phase 6V semantic context in synthesis is explicit opt-in and uses only review-passed semantic summary context, not raw transcript or live market data.
- local fixture step: external data verification currently supports only `provider="fixture"` and reads local YAML fixture data.
- not implemented: no live market API, no automatic market data provider, no scheduler, no web UI, no embedding/vector search, and no investment advice engine.

## Safety Boundaries

- Stock lens synthesis uses `phase-6f-stock-lens-json-only` by default and does not read raw transcript. Phase 6V opt-in may use `phase-6f-stock-lens-json-plus-reviewed-semantic-summary` with review-passed semantic context only.
- Semantic summary is the only current path that may send transcript text to an LLM, and only after explicit acknowledgement.
- `.env` is local convenience configuration for CLI use; it must not be committed and must not appear in docs, eval reports, or MCP responses with values.
- External boundary status fields are availability/status markers, not market facts.
- Reports must preserve no investment advice: no buy/sell/hold recommendation, no target price, and no guaranteed return.
- Phase 6T review gate is heuristic and deterministic. It helps catch obvious boundary violations but does not replace manual review.
- Corpus artifact index is status metadata only: it may report paths, counts, missing artifacts, unreadable JSON warnings, and latest semantic review status, but must not copy transcript/evidence/semantic body text and must not add MCP tools in v1.
