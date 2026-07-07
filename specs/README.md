# Spec Kit Registry

Phase 7D: Spec Kit Backfill via Full Workflow records existing capabilities as
backfilled as-built Spec Kit packages. `001-gooaye-research-system` remains the
umbrella product spec. Packages `002` through `007` document implemented
capability groups and map them to roadmap phase history, core modules,
CLI/scripts, tests, and safety boundaries.

Workflow record: constitution reviewed, no amendment. The backfill follows
`$speckit-constitution`, `$speckit-specify`, `$speckit-clarify`,
`$speckit-plan`, `$speckit-checklist`, `$speckit-tasks`, `$speckit-analyze`,
`$speckit-implement`, and `$speckit-converge`. taskstoissues: not used.

## Official Spec Kit Layout and Active Feature Selection

Official Spec Kit feature packages live under `specs/<feature>`. The
backfilled packages in this registry intentionally use that layout, and each
package keeps its own `spec.md`, `plan.md`, `tasks.md`, and
`checklists/requirements.md`. The `.specify` directory stores scaffold, memory, templates, scripts, integration, and workflow metadata; it is not the feature spec directory.

Phase 7D.1: Spec Kit Active Feature Guidance documents how to run official
Spec Kit scripts or skills against one backfilled package at a time. The
backfilled packages do not pin a single active feature by default, because this
repository now has multiple as-built packages. Before running package-specific
commands, choose the active feature explicitly in PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/003-metadata-search-mcp-core"
.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

The official scripts prioritize `SPECIFY_FEATURE_DIRECTORY` and may persist the
selected value to `.specify/feature.json`. To switch packages, set
`SPECIFY_FEATURE_DIRECTORY` again before invoking the next Spec Kit command. Do
not commit a fixed `.specify/feature.json` for this backfill, because that would
make one package look like the only active feature.

## Capability Packages

- `001-gooaye-research-system`: umbrella product spec.
- `002-ingestion-transcript-core`: deterministic local ingestion and transcript artifacts.
- `003-metadata-search-mcp-core`: deterministic metadata, search, MCP exposed tools, and eval/review only docs.
- `004-deterministic-research-artifacts`: deterministic research reports, mappings, stock lens, and local fixture verification.
- `005-research-workflow-orchestration`: deterministic workflow with optional LLM and MCP exposed workflow wrapper.
- `006-llm-safety-synthesis-smoke-review`: optional LLM, smoke validation, and eval/review only safety gates.
- `007-spec-kit-governance`: Spec Kit scaffold, constitution, templates, AGENTS, and docs tests.

## roadmap phase Mapping

- Phase 0 and Phase 1A-1E map to `002-ingestion-transcript-core`.
- Phase 2B, Phase 3A-3B, and Phase 4A-5D map to `003-metadata-search-mcp-core`.
- Phase 6B-6F and Phase 6M map to `004-deterministic-research-artifacts`.
- Phase 6G, Phase 6I, Phase 6K, Phase 6L, and Phase 6N map to `005-research-workflow-orchestration`.
- Phase 2A, Phase 6H, Phase 6J, and Phase 6O-6U map to `006-llm-safety-synthesis-smoke-review`.
- Phase 7A-7D.1 map to `007-spec-kit-governance`.

## core modules Mapping

- `002`: `feed_reader.py`, `downloader.py`, `transcriber.py`, `validator.py`, `summarizer.py`, `storage.py`, `models.py`, `config.py`, `errors.py`.
- `003`: `entity_extractor.py`, `cache.py`, `search.py`, `mcp_server.py`.
- `004`: `episode_intelligence.py`, `industry_mapping.py`, `external_data_boundary.py`, `external_data_verification.py`, `gooaye_lens.py`, `stock_lens.py`.
- `005`: `research_workflow.py`, `mcp_server.py`, `semantic_summarizer.py`, `stock_lens_synthesis.py`, `external_data_verification.py`.
- `006`: `semantic_summarizer.py`, `llm_provider.py`, `llm_profiles.py`, `local_env.py`, `stock_lens_synthesis.py`, `research_llm_smoke_review.py`, `semantic_summary_smoke_review.py`.
- `007`: `.specify/memory/constitution.md`, `.specify/templates/`, `.agents/skills/`, `AGENTS.md`.

## CLI/scripts Mapping

- `002`: `list_episodes.py`, `download_episode.py`, `transcribe_episode.py`, `validate_transcript.py`, `summarize_episode.py`.
- `003`: `extract_mentions.py`, `rebuild_cache.py`, `search_mentions.py`, `search_transcripts.py`, `run_mcp_server.py`, `validate_mcp_setup.py`, `new_mcp_eval_report.py`.
- `004`: `generate_episode_intelligence_report.py`, `generate_industry_chain_mapping.py`, `generate_external_data_boundary.py`, `verify_external_data_boundary.py`, `inspect_gooaye_lens.py`, `generate_stock_lens_report.py`.
- `005`: `run_research_workflow.py`.
- `006`: `summarize_episode.py`, `generate_stock_lens_synthesis_report.py`, `run_research_llm_smoke.py`, `review_research_llm_smoke.py`, `run_semantic_summary_smoke.py`, `review_semantic_summary_smoke.py`.
- `007`: no runtime CLI changes.

## tests Mapping

- `002`: `test_feed_reader.py`, `test_downloader.py`, `test_transcriber.py`, `test_validator.py`, `test_summarizer.py`, `test_contracts.py`.
- `003`: `test_entity_extractor.py`, `test_cache.py`, `test_search.py`, `test_mcp_server.py`, `test_mcp_setup_validation.py`, `test_docs_mcp_eval.py`, `test_mcp_eval_report_script.py`.
- `004`: `test_episode_intelligence.py`, `test_industry_mapping.py`, `test_external_data_boundary.py`, `test_external_data_verification.py`, `test_gooaye_lens.py`, `test_stock_lens_report.py`.
- `005`: `test_research_workflow.py`, `test_mcp_server.py`.
- `006`: `test_semantic_summarizer.py`, `test_llm_profiles.py`, `test_local_env.py`, `test_stock_lens_synthesis.py`, `test_research_llm_smoke.py`, `test_research_llm_smoke_review.py`, `test_semantic_summary_smoke.py`, `test_semantic_summary_smoke_review.py`, `test_research_safety_eval_docs.py`.
- `007`: `test_architecture_spec_docs.py`, `test_spec_kit_bootstrap.py`, `test_spec_kit_constitution.py`, `test_spec_kit_backfill_docs.py`.

## Classification

- deterministic: packages `002`, `003`, `004`, `005`, and `007`.
- optional LLM: packages `005` and `006`.
- local fixture: package `004` and workflow integration in `005`.
- MCP exposed: packages `003` and `005`.
- eval/review only: packages `003`, `006`, and `007`.

## Safety Boundaries

- Side-effect workflows remain dry-run first.
- Optional LLM paths require exact `api_cost_ack` and preserve the secret boundary.
- `.env` values are local-only and must not be printed or committed.
- Local fixture verification is no live market API.
- Research artifacts preserve evidence separation across podcast evidence, inference, external status, and LLM synthesis.
- MCP exposed side-effect tools warn about manual cache rebuild and do not rebuild automatically.
- no investment advice: no buy/sell/hold, target price, guaranteed return, or personalized recommendation.

## When a New Spec Package Is Required

- 新功能性工作（runtime / MCP / LLM / side-effect behavior）必須走 full Spec Kit flow 並建立新的 `specs/<feature>` package（用下一個未佔用編號）。
- `001-gooaye-research-system` 是 umbrella product spec；`002`–`007` 是 backfilled as-built capability packages，記錄既有能力，不驅動新開發。
- 小型 docs / spec / governance / test 修正若由 user 提供 concrete plan，可直接處理而不開新 package，但必須遵守 constitution，且 docs-only phase 必須有 docs tests 鎖定指引（constitution 原則 IX）。決策細節見 `docs/architecture-decision-records/ADR-0006-spec-kit-governance.md`。
- 對某個 package 執行 official scripts / skills 前，先依上方「Official Spec Kit Layout and Active Feature Selection」設定 `SPECIFY_FEATURE_DIRECTORY`。
