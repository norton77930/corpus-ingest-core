# Spec Kit Registry

> Spec 033 has saved and statically audited its exact 17-file official pinned Hermes source bundle. The audit is `SPEC033_PINNED_SOURCE_AUDIT_IMPLEMENTED` with terminal `BLOCKED_SOURCE_GRAPH`: it distinguishes an AST-owned `model_tools.py` import-time discovery caller from `main.py`/`oneshot.py` call-time candidates, while failing closed at dynamic plugin execution and incomplete capability ordering. Its detached review root seals the reviewed-artifact manifest before and after focused tests without a self-hash cycle. `runtime_status=not_run`; `live_actions_authorized=false`; final verifier remains for Main after reviews. Spec 032 is immutable predecessor evidence with `BLOCKED_CREDENTIAL_SEAM`.

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
Package `019` is the **implemented** explicit-episode verified research report workflow: preview local readiness for a named `episode_ref` (including historical episodes), then confirm-only assemble/publish or reuse an 018-equivalent digest bundle when lineage and review already pass—no LLM, RSS, download, or `api_cost_ack`; MCP tool 16 and portable Skill. Package `020` is the **implemented** offline read-only manifest-first verified research report catalog: bounded list/search safe metadata and exact-bundle self-consistency inspection. It appends MCP Tool 17 as a read-query only; no body search/raw manifest/absolute paths/export/DB/cache/network/LLM/latest-currentness claim, and inspect fixes `source_currentness_status=not_evaluated`. Package `021` is **Implemented** for its thin interfaces: exact-locator offline source revalidation through a bounded CLI and appended MCP Tool 18; Tools 1–17 remain unchanged. Package `022` is **Implemented**: offline episode-centric verified research report coverage (local inventory × 020-safe bundles), thin CLI, and append-only MCP Tool 19; Tools 1–18 unchanged. Package `023` is **Implemented**: historical verified-report path (zero-write suggest + Skill one-confirm-stop); MCP Tool 20; Tools 1–19 unchanged. Package `024` is **Implemented**: gap backlog (B-lite, 022 projection); MCP Tool 21; Tools 1–20 unchanged. Package `025` is the implemented behavior-frozen core consolidation. Package `035` is **Implemented**: append-only MCP Tool 22 `generate_stock_lens_report` exposing the existing deterministic stock lens seam; Tools 1-21 unchanged, dry-run-first, no LLM/ack/network/live market API, and no investment advice. Package `026` is **Blocked**: the repository and local runtime include one-instance Streamable HTTP, a pinned non-root sidecar, recoverable Hermes config/four-Skill integration, direct exact-21 validation, boolean-only before/after endpoint-equality evidence, and a portable operations runbook. C6已經reviewers與single live v2 run驗證為PASS-current，且不宣稱snapshots間沒有transient mutation；C7仍缺safe runtime evidence，v0.20.0 hooks只是候選。Live config values、session dumps與raw responses皆為禁止 evidence，因此026仍不是Implemented。Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS.

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
- `024-verified-report-gap-backlog`: Implemented offline gap backlog Core/CLI/Tool 21 (B-lite; reuses 022); Tools 1–20 unchanged.
- `035-stock-lens-mcp-tool`: Implemented append-only MCP Tool 22 exposing the existing deterministic stock lens; dry-run-first side-effect, no LLM/network/live market API, no investment advice; Tools 1-21 unchanged. It completes Spec 001 User Story 3 for agents.
- `025-core-consolidation`: Implemented behavior-frozen internal consolidation (path-safety single source, run-report writer dedupe, MCP facade split, registry-derived docs-count checker, shared test fixture); the registry had exact 21 tools with unchanged order at the time.
- `026-hermes-mcp-integration`: Blocked integration package. Single-instance loopback Streamable HTTP, pinned non-root sidecar, recoverable config/four-Skill sync, boolean-only endpoint-equality validator, and migration/rollback runbook are present. C6 is PASS-current from both reviewers and the single live v2 run; C7 remains unproved, with Hermes v0.20.0 tag `v2026.8.3` hooks recorded only as an uninstalled candidate path.
- `027-hermes-skill-routing-contracts`: Complete offline assurance package for closed four-Skill routing, protocol reducers, and safe evidence; it does not modify runtime/MCP and actual Hermes routing remains BLOCKED/not_evaluated.
- `028-hermes-runtime-skill-routing-observation`: Complete offline pinned-source capability gate. Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run. Any future work involving Hermes upgrade, Skill sync, hooks/plugin/collector, Docker/MCP/network, live config/session access, inference, or runtime observation must establish and receive separate approval for a new R2 successor spec; Spec 028 does not automatically authorize it.
- `029-hermes-blocked-tool-attempt-runtime-smoke`: v0.19 G0 Offline Refactor only. It pins source, baseline disposable-overlay/lease/rollback models, direct-register plugin, and exact-21 deny-only adapter. The current source/runtime contract remains `BLOCKED_RUNTIME_SEAM`; G1/G2/G3a are not re-approved, and no Hermes/Docker/MCP runtime action occurred.
- `030-hermes-g1r-offline-remediation`: Offline Implemented static-only G1R controller-plan gate. It reuses 029 safe projections, requires closed tmpfs/no-argv/no-log/no-durable/no-TTY/no-shell/no-host-port controls, and projects opaque credentials only. Its fixed safe evidence remains `runtime_status=not_run`; G2/G3a/live execution are unauthorized.
- `031-hermes-g2-credentialless-activation-gate`: Immutable predecessor. Spec 031 is **Offline Implemented** with terminal `BLOCKED_CREDENTIAL_SEAM`; its definition-only fixture was not built, run, or inspected.
- `032-hermes-g2-offline-attempt-executor`: Offline implementation staged for sealed offline authority/lease, factory-issued in-memory single-process ledger, fake-driver executor, closed command/metadata boundary, and future-only adapter/filesystem ledger. Production remains `BLOCKED_CREDENTIAL_SEAM` with `runtime_status=not_run`; fake-driver `PASS_OFFLINE_EXECUTOR_CONTRACT` is not live activation. Required reviews and the sole offline verifier are pending; G2/H4/Docker/Hermes/C6 remain unauthorized.
- `033-hermes-v019-pinned-source-loader-audit`: Static-only acquisition and audit of the exact 17-file official `NousResearch/hermes-agent` pinned-commit bundle. `SPEC033_PINNED_SOURCE_AUDIT_IMPLEMENTED` terminates at `BLOCKED_SOURCE_GRAPH`: the bounded `discover_plugins` loader edges are proven, but dynamic plugin module execution and config/credential/provider ordering depend on source outside the fixed allowlist. `runtime_status=not_run`; no live action is authorized.
- `034-hermes-v019-pinned-startup-source-graph`: Task #82 current terminal is **startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**. H2 remains fixed at H1 digest `90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d` and exactly 20 source paths; no expansion is authorized. The child verifies and changes into only its exact no-link project snapshot cwd before sentinel/import/test startup, so C6's relative configs retain snapshot-approved bytes after workspace replacement. Receipt authority has no public injected verification seam; plugin proof is owner-local exact spec/module/loader/return/register/context flow; and rename-parent fsync precedes `bundle_renamed` journal with narrow both-missing recovery. Credential/provider construction data flow, whole-program closure, actual activation, and dynamic/external-secret/runtime paths remain blocked. `runtime_status=not_run`, no live authorization, fresh re-reviews and the Main-only final invocation remain pending and unrun.

- `036-x-video-corpus-ingestion`: **Implemented and confirmed against a real X post.** One confirmed run downloaded 259.96 MiB, extracted a mono 16 kHz WAV matching the video's 2003.9 s, wrote the seed with a real `published_at`, and left the episode at `audio: available` / `transcript: valid`, searchable after a manual cache rebuild; gooaye was unchanged throughout. Both review axes passed. `code-reviewer` after five fixes (ASCII-only sentence endings breaking zh grouping, yt-dlp merged-filename resolution, re-download on recovery, non-atomic seed write, whitespace-only title); `architecture-reviewer` after one (the X surface was not enforcing the `source_type` discriminant it introduced) and judged dependency direction, guard placement, the reuse claim and the deferred MCP tool sound as implemented. All nine Success Criteria are met: the deterministic and semantic summarisers both run on an X episode with no source-specific branching. Known follow-ups for the next source spec: `source_type` does not propagate through corpus index → remediation plan → runner; divergent title provenance between this flow and `corpus_local_transcription_runner` can fork one episode's artifacts; and the semantic summary template is finance-shaped, so an AI-teaching episode gets several empty market sections. Adds X videos as a corpus source. The seam was proved by trial on 2026-08-15: a hand-shaped 366-segment episode validated, indexed, cached, and searched end-to-end with no change to any other podcast. Clarify then found the cheap route — `transcribe_episode` already accepts `audio_path` and uses its profile only for `language` — so the only new capability is acquisition (yt-dlp + PyAV writing audio into `data/audio/`), with transcription, emission, indexing and search all reused. Non-RSS sources become explicit via an additive `PodcastProfile.source_type`. The 30-90s groups are computed on demand, never persisted. Adds `yt-dlp` and `av`. **v1 at the time added no MCP tool**: the registry stayed at exactly 22, and exposure waited for this successor spec on the 004 → 035 precedent.
- `038-multi-document-study-guide`: **Specified / in implementation.** New `study_guide` corpus family: four files (`00` deterministic cover + `03`/`04`/`07` evidence-bound lecture docs) generated from an existing `learning-notes` semantic summary. Does not send transcript text to an LLM (Principle IV unamended). `01`/`02`/`05`/`06` are out of v1 because `05`/`06` are workflow derivations. No MCP tool; registry stayed at exactly 22 at the time. Not on `ARTIFACT_LADDER`.
- `039-youtube-video-corpus-ingestion`: **Implemented** (unit/integration verified; live YouTube confirm not run). YouTube as a third corpus source (`source_type` / `seed_source` = `yt-video`) plus the Spec 036 seam closures: remediation no longer suggests `download_episode.py` for `x-video` / `yt-video` missing audio; local transcription uses the seed/index title; episode-ref alphabet gains `_`. Core plus thin CLI; no MCP tool; registry stayed at exactly 22 at the time; no new dependency.
- `037-semantic-summary-profiles`: **Implemented, reviewed on both axes, and confirmed by one real end-to-end run; green under full regression (24 failed / 1628 passed against the 24/1584 baseline — identical failure list, +44 new tests).** The confirmed run on `x-raytar/2071290493581840707` produced a 50 KB study-shaped document in the FR-014 order with 49 timestamp evidences (the finance-shaped predecessor had 22), zero occurrences of market vocabulary, no investment disclaimer, and all eight `semantic_review_artifact` checks passing including `prohibited_advice`. Its 不確定事項 section is the load-bearing evidence that the shape change reached behaviour and not just headings: the model flagged that the reusable-prompt section was reconstructed from spoken description rather than quoted verbatim, and that transcript-mentioned model versions were recorded without external correction — the `learning-notes` constraint 不要補充逐字稿沒有的內容 doing exactly the work Principle V asks of it. `code-reviewer` and `architecture-reviewer` both passed with nothing at High or Medium and no in-scope contradiction; six findings were fixed (explicit YAML null silently meaning finance, two spec-package doc-drift defects, an FR ordering claim that contradicted the implemented ack-first order, an untested factory error branch, and a pulled-forward heading-injection invariant). Turns the hardcoded finance prompt shape into a selectable summary profile. `summary_profiles.py` holds both shapes as pure data; an additive `PodcastProfile.summary_profile` (default `finance`, plus `learning-notes`) selects one, threaded through `create_provider` as a keyword-only argument so `SemanticSummaryProvider` never moves and all five existing protocol fakes pass unmodified. Deliberately separate from `source_type`: source answers where content came from, profile answers what it is. The rendered envelope stays frozen because four readers depend on it (`semantic_review_artifact`, `stock_lens_synthesis`, `corpus_index`, `verified_research_lineage`); only the prompts and the `## 摘要限制` body vary. gooaye's prompts and rendered Markdown are pinned byte-identical against hardcoded literals, because every published verified research report descends from a semantic summary. Dropping the investment disclaimer for `learning-notes` is safe and proved by test rather than argued: `matched_investment_advice_guard` strips disclaimers before scanning, so it is a prohibition detector, not a disclaimer requirement — a no-disclaimer summary passes, and one carrying actual advice still fails. An unknown or non-string `summary_profile` is refused at profile load, before any transcript read or LLM call. No MCP tool, no new dependency, no new artifact path; the registry stayed at exactly 22 at the time.
- `040-x-video-ingest-mcp`: **Implemented.** Append-only MCP Tool 23 `ingest_x_video` exposing Spec 036 `run_x_video_ingest`. Preview is zero-write but resolves public metadata (`run_mode=preview`, `network_read=true`). Confirmed execution wraps the existing ingest and persists a metadata-only run report. Tools 1–22 unchanged; live registry was exactly 23 at the time. No Skill, no new dependency.
- `041-youtube-video-ingest-mcp`: **Implemented.** Append-only MCP Tool 24 `ingest_youtube_video` exposing Spec 039 `run_youtube_video_ingest`. Same preview envelope as 040. Tools 1–23 unchanged; live registry is exactly 24. No Skill, no new dependency.
- `042-workflow-derivation-bundle`: **Implemented.** Separate `workflow_derivation` family for prototype `05_prompt_examples.md` and `06_apply_to_my_workflow.md`. Requires an available Spec 038 lecture plus `config/operator_workflow.yaml`. Does not send transcript text to an LLM. No MCP; registry stays at 24. Not on `ARTIFACT_LADDER`.

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
- Hermes sidecar/config/Skill integration and portability work maps to blocked package `026-hermes-mcp-integration`.
- Offline Hermes Skill routing/protocol assurance maps to `027-hermes-skill-routing-contracts`; it is not runtime routing evidence.
- Offline pinned Hermes runtime-observation capability gating maps to `028-hermes-runtime-skill-routing-observation`; it terminates at `BLOCKED_CAPABILITY` and is not runtime observation evidence.

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
- `026`: `mcp_runtime.py`, `mcp_server.py`, `hermes_integration.py`, `mcp_tools_*`, and the existing four portable Skill directories.

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
- `026`: `run_mcp_http_server.py`, `manage_hermes_integration.py`, `validate_hermes_integration.py`, `build_hermes_sidecar.sh`, and `deploy/hermes/`.

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
- `026`: `test_mcp_http_transport.py` and `test_mcp_server_facade_boundary.py` cover one-instance stdio/HTTP compatibility; `test_hermes_deployment_contract.py` covers the sidecar/Compose boundary; `test_hermes_integration.py` covers pre-mutation manifests, config/four-Skill recovery, backup/rollback integrity, and redaction; `test_hermes_live_smoke.py` covers protocol-plus-application success, deterministic framed content tokens, hostile-entry fail-close, malformed/missing snapshots, and boolean-only no-leak evidence. Both reviewers and the single live v2 gate passed for C6; C7 remains blocked.

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
- Hermes MCP sidecar/config/Skill integration: blocked package `026`; direct transport/recovery are operational and C6 endpoint equality is PASS-current from reviewer-approved live evidence. C7 still lacks approved safe runtime evidence; v0.20.0 hooks remain a docs-only candidate.
- optional LLM: packages `005` and `006`.
- local fixture: package `004` and workflow integration in `005`.
- MCP exposed: packages `003`, `005`, `016`, `017`, `018`, `019`, `020`, `021`, `022`, and `035`; blocked package `026` adds a transport/deployment route without changing the exact 21-tool registry.
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
- corpus episode completion is human-controlled: strict-zero-file preview uses one in-memory snapshot, confirmed rejects `next`/`latest` and drift before one explicit runner dispatch, exact summary acknowledgement precedes profile/`.env`/provider work, and the reviewed local stdio MCP registry had exact 13 tools at the time. The portable Skill has no CLI/terminal fallback, retry, scheduler, or automatic second action.
- corpus latest deterministic workflow is request-bounded: confirmed mode resolves latest once, then runs only deterministic intake/download/transcription/remediation stages until `ready_for_semantic_summary`; it has no semantic/LLM/provider/env work, retry, scheduler, batch, cache rebuild, or automatic second MCP call. The reviewed local stdio MCP registry had exact 14 tools before 018.
- latest verified research report workflow is episode-scoped: preview is strict zero-write, confirmed mode checks exact `expected_episode_ref` and exact `api_cost_ack` before protected access, reuses pinned deterministic preparation, requires review exact `passed`, invokes fixed-safe research, and atomically publishes/reuses/fails closed a source-digest JSON/Markdown/manifest bundle. It uses no live market API, no retry/scheduler/cache rebuild, and no investment advice; the reviewed local stdio MCP registry had exact 15 tools at the time.
- explicit-episode verified research report workflow (019) is assemble/publish only for a named `episode_ref`: preview is strict zero-write, confirm requires local lineage/review readiness, rejects `latest`/`next`, uses no `api_cost_ack`/LLM/RSS/download/015–017 chaining, and reuses the 018 digest bundle publisher. Historical registry size after 019 was exact 16 tools.
- verified research report catalog (020) is offline read-only and manifest-first: bounded list/search over safe metadata only, exact-locator inspect for self-consistency with fixed `source_currentness_status=not_evaluated`, no body search/raw manifest/absolute paths/export/DB/cache/network/LLM. Tool 17 is append-only read-query; historical registry size after 020 was exact 17 tools.
- verified research report source revalidation (021) is exact-locator, offline, zero-write: separates bundle self-consistency from source currentness, never dereferences hostile paths, shares 018 lineage/digest rules without publish/repair, and appends Tool 18 as read-query.
- verified research report coverage (022) is episode-centric offline zero-write: joins local inventory discovery with 020-safe bundle summaries for one exact `podcast_id`, optional `has_bundle` filter, bounded digests, no body reads, and appends Tool 19 as read-query. Registry size after 022 landed was exact 20 tools; Tools 1–18 remained unchanged.
- historical verified report path (023) is zero-write suggest-only: it reads local coverage/lineage state, returns the single next safe human-gated step for one named episode, never executes runners, never recommends revalidation or republish when a bundle exists, and appends Tool 20 as read-query.
- verified report gap backlog (024) is a B-lite offline projection: it reuses the 022 coverage join with `has_bundle=false`, lists inventory gaps only (no orphan bundles, no per-row 023 suggest), stays zero-write, and appends Tool 21 as read-query. Registry size after 024 landed was exact 21 tools.
- core consolidation (025) is behavior-frozen: the registry had exact 21 tools with unchanged order/signatures at the time, runner/CLI outputs stay byte-identical, and internal boundaries (path-safety structure, run-report staging, single `FastMCP` facade, registry-derived docs counts, shared test fixture) gain grep-style guard tests.
- Hermes integration (026) preserves that registry and stdio route while adding only a loopback Streamable HTTP sidecar. Its v2 validator hashes protected bytes only as opaque in-memory input and emits equality booleans, rejecting `.env`/reparse/special entries. It forbids SSE, published ports, second FastMCP construction, config clobber, unmanaged Skill copy, protected digest/path/value output, raw response/session evidence, Hermes upgrade/hooks under the current plan, and status promotion while C6/C7 are blocked.
- stock lens MCP exposure (035) is dry-run-first exposure only: it wraps the unchanged Core seam, reads only local mapping/external-boundary artifacts, makes no LLM/network/live market API call, needs no `api_cost_ack`, keeps podcast evidence separated from inferred leads, and appends Tool 22 after unchanged Tools 1-21.
- no investment advice: no buy/sell/hold, target price, guaranteed return, or personalized recommendation.

## Batch Guard Tests（audit hardening）

除了上方 capability packages 各自的 tests，另有一層 cross-cutting 的安全/契約守衛測試，來自 audit-remediation 的 Batch 2 / 2.5 / 3A / 3B / 3C（非編號功能階段）。它們正式追蹤於 `docs/agent-handoff.md` 與 `docs/verification-matrix.md`，並 cross-cut packages `003` / `005` / `006` / `007`：

- **Batch 2**（安全/契約守衛）：`test_repository_secret_boundary.py`、`test_repository_gitignore_policy.py`、`test_mcp_tool_registry_contract.py`、`test_llm_ack_guard_contracts.py`、`test_llm_cli_no_leak.py`、`test_cache_rebuild_guard.py`。
- **Batch 2.5**（AI handoff governance docs 守衛）：`test_ai_governance_docs.py`。
- **Batch 3A**（exact `api_cost_ack` 下沉 core，provider 建構前先驗證）：`test_llm_ack_guard_contracts.py`。
- **Batch 3B**（provider factory boundary：`OpenAICompatibleProvider` 只能於 `llm_provider.py` 內建構）：`test_llm_provider_factory_boundary.py`。
- **Batch 3C**（runtime ban：constructor 只接受 `create_provider` 的 private factory token）：同 `test_llm_provider_factory_boundary.py`。

## When a New Spec Package Is Required

- 新功能性工作（runtime / MCP / LLM / side-effect behavior）必須走 full Spec Kit flow 並建立新的 `specs/<feature>` package（用下一個未佔用編號）。
- `001-gooaye-research-system` 是 umbrella product spec；`002`–`007` 是 backfilled as-built capability packages，記錄既有能力，不驅動新開發。
- 小型 docs / spec / governance / test 修正若由 user 提供 concrete plan，可直接處理而不開新 package，但必須遵守 constitution，且 docs-only phase 必須有 docs tests 鎖定指引（constitution 原則 IX）。決策細節見 `docs/architecture-decision-records/ADR-0006-spec-kit-governance.md`。
- 對某個 package 執行 official scripts / skills 前，先依上方「Official Spec Kit Layout and Active Feature Selection」設定 `SPECIFY_FEATURE_DIRECTORY`。

- **034-hermes-v019-pinned-startup-source-graph** — Task #79 current terminal: **startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**. Fixed H2 authority remains exactly 20 paths at inventory SHA-256 `90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d`. The detached reviewed manifest authorizes only exact same-parent project snapshot bytes; a reviewer-approved local purelib capability manifest authorizes only exact capability snapshot bytes. The `-I -S` child uses those snapshots plus stdlib only and rejects links/extras/shadows with pre/post revalidation. Fresh code/architecture re-reviews and the Main-only documented bootstrap/final invocation remain pending and unrun.
