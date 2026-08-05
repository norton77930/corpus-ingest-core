# Spec Kit Registry

Phase 7D: Spec Kit Backfill via Full Workflow records existing capabilities as
backfilled as-built Spec Kit packages. `001-gooaye-research-system` remains the
umbrella product spec. Packages `002` through `007` document implemented
capability groups and map them to roadmap phase history, core modules,
CLI/scripts, tests, and safety boundaries.
Package `008` is the implemented runtime feature for the corpus artifact
index. Package `009` is the corpus remediation plan runtime feature built on
top of the refreshed 008 index. Package `010` is the dry-run-first corpus
remediation runner runtime feature built on top of the refreshed 009 plan.
Package `011` is the dry-run-first corpus local transcription runner runtime
feature for local-audio transcript gaps. Package `012` is the dry-run-first
single-episode corpus audio download runner runtime feature for missing-audio
gaps. Package `013` is the dry-run-first RSS episode seed bootstrap runner.
Package `014` is the dry-run-first fresh episode workflow runner that dispatches
one next safe stage across packages `013`, `012`, `011`, and `010`. Its
dry-run is strict zero-file and reuses one fresh in-memory index/plan snapshot.
Package `015` is the standalone strict-zero-file semantic summary/review runner.
Package `016` is the human-controlled corpus episode completion workflow runner:
it previews one action across intake through semantic review, then permits one
matching confirmed action through Core, CLI, the reviewed MCP tool, or the
portable Skill. Implemented package `017` is the request-bounded latest-episode
deterministic workflow: it pins one latest episode, advances only intake/
download/local-transcription/deterministic-remediation stages, stops before
semantic work, and exposes one reviewed MCP tool plus a portable Skill. SPEC 017 is Implemented.
The 2026-07-17 `seeded`/`downloaded` mapping gap is a resolved
historical blocker; the recorded metadata-only EP679 outcome is
`ready_for_semantic_summary`. Package `018` is the implemented latest-episode verified research report workflow: it has strict zero-write preview, exact episode-scoped `expected_episode_ref` plus exact `api_cost_ack` before protected access, pinned 017 deterministic preparation, semantic review exact `passed` gate, fixed-safe deterministic research, checkpoint/artifact-driven resumption, and atomic source-digest report bundle publication. It exposes one appended reviewed MCP tool and a portable approval Skill; it has no live market API or investment advice.
Package `019` is the **implemented** explicit-episode verified research report workflow: preview local readiness for a named `episode_ref` (including historical episodes), then confirm-only assemble/publish or reuse an 018-equivalent digest bundle when lineage and review already pass—no LLM, RSS, download, or `api_cost_ack`; MCP tool 16 and portable Skill. Package `020` is the **implemented** offline read-only manifest-first verified research report catalog: bounded list/search safe metadata and exact-bundle self-consistency inspection. It appends MCP Tool 17 as a read-query only; no body search/raw manifest/absolute paths/export/DB/cache/network/LLM/latest-currentness claim, and inspect fixes `source_currentness_status=not_evaluated`. Package `021` is **Implemented** for its thin interfaces: exact-locator offline source revalidation through a bounded CLI and appended MCP Tool 18; Tools 1–17 remain unchanged. Package `022` is **Implemented**: offline episode-centric verified research report coverage (local inventory × 020-safe bundles), thin CLI, and append-only MCP Tool 19; Tools 1–18 unchanged. Package `023` is **Implemented**: historical verified-report path (zero-write suggest + Skill one-confirm-stop); MCP Tool 20; Tools 1–19 unchanged.

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
selected value to `.specify/feature.json`. The persisted file is local-only,
gitignored, and must remain untracked; a clean clone need not contain it. Set
`SPECIFY_FEATURE_DIRECTORY` again before invoking the next Spec Kit command,
or let an official script recreate the ignored local selection file. Never
commit a fixed selector that makes one package appear uniquely active.

## Capability Packages

- `001-gooaye-research-system`: umbrella product spec.
- `002-ingestion-transcript-core`: deterministic local ingestion and transcript artifacts.
- `003-metadata-search-mcp-core`: deterministic metadata, search, MCP exposed tools, and eval/review only docs.
- `004-deterministic-research-artifacts`: deterministic research reports, mappings, stock lens, and local fixture verification.
- `005-research-workflow-orchestration`: deterministic workflow with optional LLM and MCP exposed workflow wrapper.
- `006-llm-safety-synthesis-smoke-review`: optional LLM, smoke validation, and eval/review only safety gates.
- `007-spec-kit-governance`: Spec Kit scaffold, constitution, templates, AGENTS, and docs tests.
- `008-corpus-artifact-index`: deterministic offline per-episode corpus artifact status index.
- `009-corpus-remediation-plan`: deterministic offline full-ladder corpus remediation/action plan.
- `010-corpus-remediation-runner`: dry-run-first deterministic corpus remediation runner.
- `011-corpus-local-transcription-runner`: dry-run-first single-episode local transcription runner.
- `012-corpus-audio-download-runner`: dry-run-first single-episode audio download runner.
- `013-corpus-episode-intake-bootstrap`: dry-run-first RSS episode seed bootstrap runner.
- `014-corpus-fresh-episode-workflow-runner`: dry-run-first one-stage fresh episode workflow runner.
- `015-corpus-semantic-remediation-runner`: standalone strict-zero-file semantic summary/review runner.
- `016-corpus-episode-completion-workflow-runner`: human-controlled strict-zero-file completion workflow, one MCP tool, and portable Skill.
- `017-corpus-latest-episode-deterministic-workflow`: implemented request-bounded latest-episode processing through local deterministic readiness, one MCP tool, and portable Skill.
- `018-latest-episode-verified-research-report-workflow`: implemented strict-zero-write preview and episode-scoped verified research report workflow, source-digest atomic bundle, one appended MCP tool, and portable Skill.
- `019-episode-verified-research-report-workflow`: implemented explicit-episode (historical) verified research report assemble/publish workflow; 018-equivalent bundle; no upstream stages/LLM/ack; MCP tool 16 + Skill.
- `020-verified-research-report-catalog`: implemented offline read-only manifest-first catalog list/search/inspect; append-only MCP Tool 17 read-query; self-consistency only, `source_currentness_status=not_evaluated`.
- `021-verified-research-report-source-revalidation`: Implemented thin exact-locator CLI and append-only MCP Tool 18 source revalidation interface; Tools 1–17 unchanged, read-only/offline/zero-write.
- `022-verified-research-report-coverage-index`: Implemented offline episode-centric coverage join; thin CLI and append-only MCP Tool 19; Tools 1–18 unchanged; read-only/offline/zero-write.
- `023-historical-episode-verified-report-path`: Implemented historical path suggest Core/CLI/Tool 20 + portable Skill; one human confirm per request; Tools 1–19 unchanged.

## roadmap phase Mapping

- Phase 0 and Phase 1A-1E map to `002-ingestion-transcript-core`.
- Phase 2B, Phase 3A-3B, and Phase 4A-5D map to `003-metadata-search-mcp-core`.
- Phase 6B-6F and Phase 6M map to `004-deterministic-research-artifacts`.
- Phase 6G, Phase 6I, Phase 6K, Phase 6L, and Phase 6N map to `005-research-workflow-orchestration`.
- Phase 2A, Phase 6H, Phase 6J, and Phase 6O-6U map to `006-llm-safety-synthesis-smoke-review`.
- Phase 7A-7D.1 map to `007-spec-kit-governance`.
- Corpus artifact index runtime work maps to `008-corpus-artifact-index`.
- Corpus remediation plan runtime work maps to `009-corpus-remediation-plan`.
- Corpus remediation runner runtime work maps to `010-corpus-remediation-runner`.
- Corpus local transcription runner runtime work maps to `011-corpus-local-transcription-runner`.
- Corpus audio download runner runtime work maps to `012-corpus-audio-download-runner`.
- Corpus episode intake bootstrap runtime work maps to `013-corpus-episode-intake-bootstrap`.
- Corpus fresh episode workflow runner runtime work maps to `014-corpus-fresh-episode-workflow-runner`.
- Corpus semantic remediation runner runtime work maps to `015-corpus-semantic-remediation-runner`.
- Corpus episode completion workflow runner runtime work maps to `016-corpus-episode-completion-workflow-runner`.
- Corpus latest deterministic workflow runtime work maps to `017-corpus-latest-episode-deterministic-workflow`.
- Latest verified research report runtime work maps to `018-latest-episode-verified-research-report-workflow`.
- Explicit-episode verified research report runtime work maps to `019-episode-verified-research-report-workflow`.
- Verified research report catalog runtime work maps to `020-verified-research-report-catalog`.
- Verified research report source revalidation runtime work maps to `021-verified-research-report-source-revalidation`.
- Verified research report coverage index runtime work maps to `022-verified-research-report-coverage-index`.

## core modules Mapping

- `002`: `feed_reader.py`, `downloader.py`, `transcriber.py`, `validator.py`, `summarizer.py`, `storage.py`, `models.py`, `config.py`, `errors.py`.
- `003`: `entity_extractor.py`, `cache.py`, `search.py`, `mcp_server.py`.
- `004`: `episode_intelligence.py`, `industry_mapping.py`, `external_data_boundary.py`, `external_data_verification.py`, `gooaye_lens.py`, `stock_lens.py`.
- `005`: `research_workflow.py`, `mcp_server.py`, `semantic_summarizer.py`, `stock_lens_synthesis.py`, `external_data_verification.py`.
- `006`: `semantic_summarizer.py`, `llm_provider.py`, `llm_profiles.py`, `local_env.py`, `stock_lens_synthesis.py`, `research_llm_smoke_review.py`, `semantic_summary_smoke_review.py`.
- `007`: `.specify/memory/constitution.md`, `.specify/templates/`, `.agents/skills/`, `AGENTS.md`.
- `008`: `corpus_index.py`, `storage.py`, `models.py`, `errors.py`.
- `009`: `corpus_remediation_plan.py`, `corpus_index.py`, `storage.py`, `models.py`, `errors.py`.
- `010`: `corpus_remediation_runner.py`, `corpus_remediation_plan.py`, `storage.py`, `models.py`, `errors.py`.
- `011`: `corpus_local_transcription_runner.py`, `corpus_remediation_plan.py`, `transcriber.py`, `storage.py`, `models.py`, `errors.py`.
- `012`: `corpus_audio_download_runner.py`, `corpus_remediation_plan.py`, `downloader.py`, `storage.py`, `models.py`, `errors.py`.
- `013`: `corpus_episode_intake.py`, `feed_reader.py`, `corpus_index.py`, `corpus_remediation_plan.py`, `corpus_audio_download_runner.py`, `storage.py`, `models.py`, `errors.py`.
- `014`: `corpus_episode_workflow_runner.py`, `corpus_episode_intake.py`, `corpus_index.py`, `corpus_remediation_plan.py`, `corpus_audio_download_runner.py`, `corpus_local_transcription_runner.py`, `corpus_remediation_runner.py`, `storage.py`, `models.py`, `errors.py`.
- `015`: `corpus_semantic_remediation_runner.py`, `corpus_index.py`, `semantic_summarizer.py`, `semantic_summary_smoke_review.py`, `storage.py`, `models.py`, `errors.py`.
- `016`: `corpus_episode_completion_workflow_runner.py`, `corpus_episode_intake.py`, `corpus_episode_workflow_runner.py`, `corpus_semantic_remediation_runner.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`, and `.agents/skills/corpus-episode-completion/SKILL.md`.
- `017`: `corpus_latest_episode_deterministic_workflow_runner.py`, `corpus_episode_intake.py`, `corpus_episode_workflow_runner.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`, and `.agents/skills/corpus-latest-episode-processing/SKILL.md`.
- `018`: `latest_episode_verified_research_report_workflow_runner.py`, `verified_research_report.py`, `corpus_latest_episode_deterministic_workflow_runner.py`, `research_workflow.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`, and `.agents/skills/latest-episode-verified-research-report/SKILL.md`.
- `019`: `episode_verified_research_report_workflow_runner.py`, `verified_research_report.py`, `verified_research_lineage.py`, `mcp_episode_verified_research_report.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`, and `.agents/skills/episode-verified-research-report/SKILL.md`.
- `020`: `verified_research_report_catalog.py`, `mcp_verified_research_report_catalog.py`, `secure_local_snapshot.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`.
- `021`: `verified_research_report_source_revalidation.py`, `mcp_verified_research_report_source_revalidation.py`, `verified_research_lineage.py`, `verified_research_report.py`, `secure_local_snapshot.py`, `mcp_server.py`, `storage.py`, `models.py`, `errors.py`.
- `022`: `verified_research_report_coverage.py`, `mcp_verified_research_report_coverage.py`, `corpus_index.py` (inventory discovery only), `verified_research_report_catalog.py` (safe summary discovery), `mcp_server.py`, `models.py`, `errors.py`.

## CLI/scripts Mapping

- `002`: `list_episodes.py`, `download_episode.py`, `transcribe_episode.py`, `validate_transcript.py`, `summarize_episode.py`.
- `003`: `extract_mentions.py`, `rebuild_cache.py`, `search_mentions.py`, `search_transcripts.py`, `run_mcp_server.py`, `validate_mcp_setup.py`, `new_mcp_eval_report.py`.
- `004`: `generate_episode_intelligence_report.py`, `generate_industry_chain_mapping.py`, `generate_external_data_boundary.py`, `verify_external_data_boundary.py`, `inspect_gooaye_lens.py`, `generate_stock_lens_report.py`.
- `005`: `run_research_workflow.py`.
- `006`: `summarize_episode.py`, `generate_stock_lens_synthesis_report.py`, `run_research_llm_smoke.py`, `review_research_llm_smoke.py`, `run_semantic_summary_smoke.py`, `review_semantic_summary_smoke.py`.
- `007`: no runtime CLI changes.
- `008`: `generate_corpus_index.py`.
- `009`: `generate_corpus_remediation_plan.py`.
- `010`: `run_corpus_remediation.py`.
- `011`: `run_corpus_local_transcription.py`.
- `012`: `run_corpus_audio_download.py`.
- `013`: `run_corpus_episode_intake.py`.
- `014`: `run_corpus_episode_workflow.py`.
- `015`: `run_corpus_semantic_remediation.py`.
- `016`: `run_corpus_episode_completion_workflow.py`, `validate_mcp_setup.py`.
- `017`: `run_corpus_latest_episode_deterministic_workflow.py`, `validate_mcp_setup.py`.
- `018`: `run_latest_episode_verified_research_report_workflow.py`, `validate_mcp_setup.py`.
- `019`: `run_episode_verified_research_report_workflow.py`, `validate_mcp_setup.py`.
- `020`: `query_verified_research_report_catalog.py`, `validate_mcp_setup.py`.
- `021`: `revalidate_verified_research_report_sources.py`, `validate_mcp_setup.py`.
- `022`: `query_verified_research_report_coverage.py`, `validate_mcp_setup.py`.

## tests Mapping

- `002`: `test_feed_reader.py`, `test_downloader.py`, `test_transcriber.py`, `test_validator.py`, `test_summarizer.py`, `test_contracts.py`.
- `003`: `test_entity_extractor.py`, `test_cache.py`, `test_search.py`, `test_mcp_server.py`, `test_mcp_setup_validation.py`, `test_docs_mcp_eval.py`, `test_mcp_eval_report_script.py`.
- `004`: `test_episode_intelligence.py`, `test_industry_mapping.py`, `test_external_data_boundary.py`, `test_external_data_verification.py`, `test_gooaye_lens.py`, `test_stock_lens_report.py`.
- `005`: `test_research_workflow.py`, `test_mcp_server.py`.
- `006`: `test_semantic_summarizer.py`, `test_llm_profiles.py`, `test_local_env.py`, `test_stock_lens_synthesis.py`, `test_research_llm_smoke.py`, `test_research_llm_smoke_review.py`, `test_semantic_summary_smoke.py`, `test_semantic_summary_smoke_review.py`, `test_research_safety_eval_docs.py`.
- `007`: `test_architecture_spec_docs.py`, `test_spec_kit_bootstrap.py`, `test_spec_kit_constitution.py`, `test_spec_kit_backfill_docs.py`.
- `008`: `test_corpus_index.py`.
- `009`: `test_corpus_remediation_plan.py`.
- `010`: `test_corpus_remediation_runner.py`.
- `011`: `test_corpus_local_transcription_runner.py`.
- `012`: `test_corpus_audio_download_runner.py`.
- `013`: `test_corpus_episode_intake.py`, plus seed handoff coverage in `test_corpus_index.py`, `test_corpus_remediation_plan.py`, and `test_corpus_audio_download_runner.py`.
- `014`: `test_corpus_episode_workflow_runner.py` covers six real corpus states, zero writer calls/tree manifest drift, shared snapshot identity, and deep failure no-leak; standalone compatibility remains covered by `test_corpus_audio_download_runner.py`, `test_corpus_local_transcription_runner.py`, `test_corpus_remediation_runner.py`, `test_corpus_index.py`, and `test_corpus_remediation_plan.py`.
- `015`: `test_corpus_semantic_remediation_runner.py` covers the complete state table, real 008/009 zero-file manifests, exact acknowledgement ordering, real semantic/review cores, no-leak, cache, MCP, and 014 compatibility guards.
- `016`: `test_corpus_episode_completion_workflow_runner.py` covers strict-zero-file previews, fresh confirmed one-action dispatch, reports, acknowledgement/no-leak boundaries, and CLI; `test_mcp_server.py`, `test_mcp_tool_registry_contract.py`, `test_mcp_setup_validation.py`, and `test_corpus_episode_completion_skill.py` cover the reviewed MCP and portable Skill surfaces.
- `017`: `test_corpus_latest_episode_deterministic_workflow_runner.py` covers latest pinning, deterministic stage ordering, stop/resume/noop, reports, and thin CLI; `test_mcp_server.py`, `test_mcp_tool_registry_contract.py`, `test_repository_secret_boundary.py`, and `test_corpus_latest_episode_processing_skill.py` cover the reviewed MCP and portable Skill surfaces.
- `018`: `test_latest_episode_verified_research_report_workflow_runner.py` covers approval ordering, strict zero-write preview, pinned helper reuse, semantic/research gates, provenance, digest bundle publication/reuse/conflict; `test_latest_episode_verified_research_report_skill.py`, `test_mcp_server.py`, `test_mcp_tool_registry_contract.py`, and `test_mcp_setup_validation.py` cover CLI, MCP, setup-validator, and portable Skill surfaces.
- `019`: `test_episode_verified_research_report_workflow_runner.py` covers explicit-episode preview/confirm, reserved selector rejection, blocked inventory, assemble/publish/reuse/conflict, and no LLM/RSS/015–017 chaining; `test_episode_verified_research_report_workflow_cli.py`, `test_episode_verified_research_report_skill.py`, `test_mcp_server.py`, `test_mcp_tool_registry_contract.py`, and `test_mcp_setup_validation.py` cover CLI, MCP, and portable Skill surfaces.
- `020`: `test_verified_research_report_catalog.py` covers bounded list/search/inspect, body-read guards, containment/reparse, and `source_currentness_status=not_evaluated`; `test_verified_research_report_catalog_cli.py`, `test_spec_020_verified_research_report_catalog_docs.py`, `test_mcp_server.py`, and `test_mcp_tool_registry_contract.py` cover CLI, docs, and append-only Tool 17.
- `021`: `test_verified_research_report_source_revalidation.py` covers exact locator, bundle/currentness separation, hostile-path sentinels, lineage/digest reuse, and zero-write offline matrix; `test_verified_research_report_source_revalidation_cli.py`, `test_spec_021_verified_research_report_source_revalidation_docs.py`, `test_mcp_server.py`, and `test_mcp_tool_registry_contract.py` cover CLI, docs, and append-only Tool 18.
- `022`: `test_verified_research_report_coverage.py` covers inventory×bundle join, orphan rows, has_bundle filter, limits, and zero-write; `test_verified_research_report_coverage_cli.py`, `test_spec_022_verified_research_report_coverage_docs.py`, and `test_mcp_tool_registry_contract.py` cover CLI, docs, and append-only Tool 19.

## Classification

- deterministic: packages `002`, `003`, `004`, `005`, and `007`.
- deterministic corpus status: package `008`.
- deterministic corpus remediation: package `009`.
- deterministic corpus remediation runner: package `010`.
- local transcription runner: package `011`.
- audio download runner: package `012`.
- episode intake bootstrap runner: package `013`.
- fresh episode workflow runner: package `014`.
- semantic remediation runner: package `015`.
- human-controlled episode completion workflow runner: package `016`.
- latest-episode deterministic workflow runner: implemented package `017`.
- latest-episode verified research report workflow: implemented package `018`.
- explicit-episode verified research report workflow: implemented package `019`.
- verified research report catalog (read-only): implemented package `020`.
- verified research report source revalidation (read-only): implemented package `021`.
- verified research report coverage index (read-only): implemented package `022`.
- optional LLM: packages `005` and `006`.
- local fixture: package `004` and workflow integration in `005`.
- MCP exposed: packages `003`, `005`, `016`, `017`, `018`, `019`, `020`, `021`, and `022`.
- eval/review only: packages `003`, `006`, and `007`.

## Safety Boundaries

- Side-effect workflows remain dry-run first.
- Optional LLM paths require exact `api_cost_ack` and preserve the secret boundary.
- `.env` values are local-only and must not be printed or committed.
- Local fixture verification is no live market API.
- Research artifacts preserve evidence separation across podcast evidence, inference, external status, and LLM synthesis.
- MCP exposed side-effect tools warn about manual cache rebuild and do not rebuild automatically.
- corpus episode intake is seed-only: dry-run may read configured RSS but writes nothing, confirmed execution writes only safe seed metadata and a run report, and it does not download, transcribe, call LLM/MCP, run downstream remediation, or rebuild cache automatically.
- corpus fresh episode workflow is one-stage only: 014 dry-run is zero-file and uses one in-memory snapshot, while standalone 010-012 dry-runs still persist fresh 008/009; confirmed execution requires `stage=next`, dispatches exactly one existing public runner, and does not execute semantic/LLM, MCP registry, cache rebuild, stock-lens, batch, or non-selected stages.
- corpus semantic remediation is standalone: dry-run is strict zero-file and bypasses profile/`.env`; confirmed summary requires exact api_cost_ack before profile/provider resolution; review is deterministic; exactly one executor runs; no generated_at latest report; no 010/014/MCP/cache integration; not investment advice.
- corpus episode completion is human-controlled: strict-zero-file preview uses one in-memory snapshot, confirmed rejects `next`/`latest` and drift before one explicit runner dispatch, exact summary acknowledgement precedes profile/`.env`/provider work, and the reviewed local stdio MCP registry has exact 13 tools. The portable Skill has no CLI/terminal fallback, retry, scheduler, or automatic second action.
- corpus latest deterministic workflow is request-bounded: confirmed mode resolves latest once, then runs only deterministic intake/download/transcription/remediation stages until `ready_for_semantic_summary`; it has no semantic/LLM/provider/env work, retry, scheduler, batch, cache rebuild, or automatic second MCP call. The reviewed local stdio MCP registry had exact 14 tools before 018.
- latest verified research report workflow is episode-scoped: preview is strict zero-write, confirmed mode checks exact `expected_episode_ref` and exact `api_cost_ack` before protected access, reuses pinned deterministic preparation, requires review exact `passed`, invokes fixed-safe research, and atomically publishes/reuses/fails closed a source-digest JSON/Markdown/manifest bundle. It uses no live market API, no retry/scheduler/cache rebuild, and no investment advice; the reviewed local stdio MCP registry has exact 15 tools.
- explicit-episode verified research report workflow (019) is assemble/publish only for a named `episode_ref`: preview is strict zero-write, confirm requires local lineage/review readiness, rejects `latest`/`next`, uses no `api_cost_ack`/LLM/RSS/download/015–017 chaining, and reuses the 018 digest bundle publisher. Historical registry size after 019 was exact 16 tools.
- verified research report catalog (020) is offline read-only and manifest-first: bounded list/search over safe metadata only, exact-locator inspect for self-consistency with fixed `source_currentness_status=not_evaluated`, no body search/raw manifest/absolute paths/export/DB/cache/network/LLM. Tool 17 is append-only read-query; historical registry size after 020 was exact 17 tools.
- verified research report source revalidation (021) is exact-locator, offline, zero-write: separates bundle self-consistency from source currentness, never dereferences hostile paths, shares 018 lineage/digest rules without publish/repair, and appends Tool 18 as read-query.
- verified research report coverage (022) is episode-centric offline zero-write: joins local inventory discovery with 020-safe bundle summaries for one exact `podcast_id`, optional `has_bundle` filter, bounded digests, no body reads, and appends Tool 19 as read-query. **Current reviewed local stdio MCP registry has exact 20 tools**; Tools 1–18 remain unchanged.
- no investment advice: no buy/sell/hold, target price, guaranteed return, or personalized recommendation.

## Batch Guard Tests（audit hardening）

除了上方 capability packages 各自的 tests，另有一層 cross-cutting 的安全/契約守衛測試，來自 audit-remediation 的 Batch 2 / 2.5 / 3A / 3B（非編號功能階段）。它們正式追蹤於 `docs/agent-handoff.md` 與 `docs/verification-matrix.md`，並 cross-cut packages `003` / `005` / `006` / `007`：

- **Batch 2**（安全/契約守衛）：`test_repository_secret_boundary.py`、`test_repository_gitignore_policy.py`、`test_mcp_tool_registry_contract.py`、`test_llm_ack_guard_contracts.py`、`test_llm_cli_no_leak.py`、`test_cache_rebuild_guard.py`。
- **Batch 2.5**（AI handoff governance docs 守衛）：`test_ai_governance_docs.py`。
- **Batch 3A**（exact `api_cost_ack` 下沉 core，provider 建構前先驗證）：`test_llm_ack_guard_contracts.py`。
- **Batch 3B**（provider factory boundary：`OpenAICompatibleProvider` 只能於 `llm_provider.py` 內建構）：`test_llm_provider_factory_boundary.py`。

## When a New Spec Package Is Required

- 新功能性工作（runtime / MCP / LLM / side-effect behavior）必須走 full Spec Kit flow 並建立新的 `specs/<feature>` package（用下一個未佔用編號）。
- `001-gooaye-research-system` 是 umbrella product spec；`002`–`007` 是 backfilled as-built capability packages，記錄既有能力，不驅動新開發。
- 小型 docs / spec / governance / test 修正若由 user 提供 concrete plan，可直接處理而不開新 package，但必須遵守 constitution，且 docs-only phase 必須有 docs tests 鎖定指引（constitution 原則 IX）。決策細節見 `docs/architecture-decision-records/ADR-0006-spec-kit-governance.md`。
- 對某個 package 執行 official scripts / skills 前，先依上方「Official Spec Kit Layout and Active Feature Selection」設定 `SPECIFY_FEATURE_DIRECTORY`。
