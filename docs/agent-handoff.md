# AI Agent Handoff Entrypoint

> Spec 029 is **Offline Implemented** only: live preflight not run; G2-G3 not authorized; source contract remains `BLOCKED_RUNTIME_SEAM`. A future PASS is only an expected high-level MCP tool-call attempt policy-blocked before dispatch, not internal Skill selection, fallback, 019 outcome, or Core execution.

這是新 AI agent（Opus 4.8、GPT-5.5 或其他）接手本 repo 的第一份文件。目標：10 分鐘內理解專案、知道哪些檔案是 source of truth、哪些邊界不可逾越、如何開始與驗證工作。

## Project Summary

Podcast Ingestion Core 是一個本機優先的通用 Podcast 擷取與研究核心：RSS episode listing、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive 摘要、opt-in 的 OpenAI-compatible LLM semantic summary、deterministic mention extraction、SQLite metadata cache / search、共用單一 FastMCP 的 stdio 與 loopback Streamable HTTP sidecar（目前恰好 24 個 reviewed tools），以及 deterministic research workflow（stock lens synthesis、external data boundary）。第一個 podcast profile 是 Gooaye 股癌，但核心程式不得寫死股癌；所有 podcast-specific 設定在 `config/podcasts.yaml`。本專案支援 evidence-based 研究整理，明確**不**提供投資建議。
Corpus packages 008–018 add local artifact indexing/planning, bounded intake/download/transcription/deterministic remediation, a one-stage fresh workflow, standalone `015-corpus-semantic-remediation-runner`, the human-controlled `016-corpus-episode-completion-workflow-runner`, `017-corpus-latest-episode-deterministic-workflow`, and `018-latest-episode-verified-research-report-workflow`. 016 previews in memory with strict zero-file behavior, 017 locks latest once and stops at `ready_for_semantic_summary`, and 018 validates a previewed exact episode reference plus exact acknowledgement before it pins, gates, researches, and atomically publishes a digest-versioned verified report bundle.
The local stdio registry has exact 24 reviewed tools. Tool 24, `ingest_youtube_video`, is append-only after unchanged Tools 1–23. Tool 23, `ingest_x_video`, remains the X ingest preview/confirm tool. Preview is zero-write but resolves public metadata over the network. Tool 22, `generate_stock_lens_report`, remains a dry-run-first side-effect stock lens (no LLM, no `api_cost_ack`, no network, no live market API, no investment advice). Tool 21, `list_verified_report_gap_backlog`, remains a read-query inventory gap backlog (no confirm/ack). Tool 20 remains historical next-step suggestion. Tool 19 remains coverage join. Tool 18 remains exact-locator source revalidation. Tool 17 retains its catalog contract.
For historical context, 016 introduced 13 reviewed tools before 017 added the fourteenth tool; the registry therefore had exact 14 reviewed tools before 018 added the fifteenth; 019 added the sixteenth; 020 appends the seventeenth.

## First 10 Minutes（閱讀順序）

1. `AGENTS.md` — repo-level agent rules 與 hard constraints（最短、最優先）。
2. `.specify/memory/constitution.md` — 九大原則，所有邊界的正式定義。
3. 本文件 — 邊界與 guard tests 的對應、known risks。
4. `docs/ai-development-framework.md` — instruction hierarchy、change classification、Definition of Ready/Done、completion report 格式。
5. `docs/verification-matrix.md` — 每種變更該跑哪些 targeted tests 與 full checks。
6. `specs/README.md` — Spec Kit registry：umbrella spec 與 backfilled capability packages。
7. `docs/architecture.md` — 架構現況（Phase 6T 研究系統）。

## Source-of-Truth Files

| 主題 | Source of truth |
| --- | --- |
| Agent hard constraints | `AGENTS.md` |
| 專案原則 / 安全邊界 | `.specify/memory/constitution.md`（v1.0.0） |
| 邊界的 executable record | `tests/`（尤其 Batch 2 guard tests，見下表） |
| 驗證指令 | `docs/verification-matrix.md` |
| 功能規格 | `specs/`（`specs/README.md` 是 registry） |
| 架構決策 | `docs/architecture-decision-records/README.md` |
| Runtime 行為 | `src/podcast_ingest_core/`（CLI/MCP 只是 thin wrappers） |
| Podcast/LLM/boundary 設定 | `config/*.yaml` |

README.md 是 quick orientation 與 CLI 範例，不是 governance source。

## Implemented / Not Implemented

- **已實作**：RSS episode listing、episode lookup、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive Markdown 摘要、opt-in LLM semantic summary pipeline、deterministic mention extraction、SQLite metadata cache / search、stdio MCP、loopback-only Streamable HTTP sidecar transport、research workflow orchestration、stock lens synthesis、external data boundary（local fixture only）。
- **Corpus 已實作**：008–024，包括 014–023 既有 corpus/verified-report 路徑，以及 gap backlog（024 / Tool 21）；confirmed summary requires exact acknowledgement before profile/`.env`, deterministic review uses no LLM configuration, 018 atomically publishes an identity-validated digest bundle only after review passes, and 019 publishes the same bundle class for a named episode without LLM/ack when lineage already passes.
- **Spec 026 Blocked**：sidecar image/health、OpenAB config/四 Skills、direct exact-21 readiness、`hermes mcp test`、portable runbook 與 boolean-only endpoint-equality validator 已存在。C6已由required reviewers＋唯一live v2 run驗證為PASS-current；C7仍缺safe runtime evidence，Hermes v0.20.0 tag `v2026.8.3` hooks只是未安裝候選。不可標Implemented，也不可重跑validator/inference、讀live config values/session dump、保存raw response、升級或啟用hooks補證。
- **未實作**：Web UI、排程、embedding、vector search、live market API（明確不批准，見邊界）。

## Non-Negotiable Boundaries

每條邊界都有 guard test；改動任何一條屬 safety-boundary 變更，需人類批准並評估 constitution 修訂。

| 邊界 | 內容 | Guard tests |
| --- | --- | --- |
| `.env` / secret policy | `.env` 是 local-only：不得讀取、列印、grep、摘要或提交。API key、token、provider secret 不得出現在 committed 檔案、stdout、MCP responses 或 review reports | `tests/test_repository_secret_boundary.py`、`tests/test_repository_gitignore_policy.py` |
| No raw transcript stdout | LLM-facing CLI 的 stdout/stderr 不得含 transcript 原文、prompt 內容或 API key 值；semantic CLI stdout 是鎖定的 metadata-only JSON | `tests/test_llm_cli_no_leak.py` |
| Exact `api_cost_ack` | Confirmed LLM 執行前必須提供 exact ack 字串；guard 在 core-level 強制（`llm_provider.create_provider` 建 provider 前與 `semantic_summarize_episode` 進入點），wrappers 為第一線。常數定義於 `llm_provider`，經 `semantic_summarizer.SEMANTIC_API_COST_ACK` re-export，不得複製散落 | `tests/test_llm_ack_guard_contracts.py` |
| Dry-run first | Side-effect workflows/tools 預設 dry-run（`confirm=False`）；confirmed 執行必須顯式 `confirm=True` 或 CLI `--confirm` | `tests/test_mcp_tool_registry_contract.py`、`tests/test_research_workflow.py` |
| No live market API | External market data 只用 boundary scaffold / local fixture；不讀 API key、不打 HTTP provider、不捏造市場事實 | `tests/test_external_data_boundary.py`、`tests/test_external_data_verification.py` |
| 015 strict zero-file / one executor | Explicit episode only; dry-run resolves no profile/`.env` and writes zero files; confirmed summary/review dispatches exactly one executor; reports are metadata-only with no `generated_at`; index/plan/cache remain manual | `tests/test_corpus_semantic_remediation_runner.py` |
| 016 completion workflow / Skill | strict-zero-file preview selects one next action; confirmed rejects `next`/`latest` and drift, dispatches exactly one runner, writes a metadata-only report, and the portable Skill permits no local fallback or automatic second action | `tests/test_corpus_episode_completion_workflow_runner.py`、`tests/test_corpus_episode_completion_skill.py`、`tests/test_mcp_setup_validation.py` |
| 017 latest deterministic workflow / Skill | SPEC 017 is Implemented. The resolved historical `seeded`/`downloaded` mapping blocker has recorded metadata-only EP679 evidence ending at `ready_for_semantic_summary`. An explicit natural-language latest-episode request is the one-time execution authorization: the portable Skill acknowledges once, calls the dedicated MCP tool once with `confirm=true`, reports once, and stops. The MCP tool remains dry-run by default outside that protocol; no semantic work, retry, fallback, CLI/terminal use, cache rebuild, or second call is allowed | `tests/test_corpus_latest_episode_deterministic_workflow_runner.py`、`tests/test_corpus_latest_episode_processing_skill.py`、`tests/test_mcp_tool_registry_contract.py` |
| 018 verified research report / Skill | Preview is strict zero-write. Confirmed work must supply the previewed `expected_episode_ref` and exact `api_cost_ack` before RSS, environment/provider, writer, or child-stage access. The Core pins latest once, requires semantic review exact `passed`, fixes research options, validates source/provenance, and atomically publishes/reuses/fails closed a digest-versioned bundle. The portable Skill uses preview → explicit approval → one confirmed MCP call → report and stop; it has no CLI/terminal fallback, retry, scheduler, live market API, automatic cache rebuild, or investment advice | `tests/test_latest_episode_verified_research_report_workflow_runner.py`、`tests/test_latest_episode_verified_research_report_skill.py`、`tests/test_mcp_tool_registry_contract.py`、`tests/test_mcp_setup_validation.py` |
| No investment advice | 不得產生 buy/sell/hold、target price、guaranteed returns 或個人化投資建議；review gate 會拒絕 prohibited advice 輸出 | `tests/test_research_llm_smoke_review.py`、`tests/test_gooaye_lens.py` |
| No automatic cache rebuild | Side-effect tools 完成後不得自動 `rebuild_cache`，只回 cache stale warning；rebuild 是手動操作 | `tests/test_cache_rebuild_guard.py` |
| Thin CLI / thick core | Runtime 行為住在 `src/podcast_ingest_core`；`scripts/` 與 MCP tools 只解析輸入、呼叫 core、格式化輸出 | `tests/test_contracts.py` |
| MCP JSON envelope | MCP responses 維持既有 envelope：`{"ok": true, "data": ...}`、`{"ok": false, ...}`、dry-run 含 `"dry_run": true`；目前恰好 24 個 reviewed tools | `tests/test_mcp_tool_registry_contract.py`、`tests/test_mcp_server.py` |
| 019 explicit-episode verified report / Skill | Preview is strict zero-write for a named `episode_ref` (reject latest/next). Confirm assembles/publishes only when local artifacts and lineage already pass; no `api_cost_ack`, no LLM/RSS/download, no 015–017 chaining. Blocked lists missing/stale roles. historically MCP Tool 16 + portable Skill | `tests/test_episode_verified_research_report_workflow_runner.py`、`tests/test_episode_verified_research_report_skill.py`、`tests/test_mcp_tool_registry_contract.py` |
| 025 path-safety 結構單一來源 | 路徑安全結構 regex 只得定義於 `path_safety.py`；四個 runner 的 `_is_safe_local_path` 是薄包裝、真值表凍結（含刻意保留的變體差異） | `tests/test_path_safety_boundary.py`、`tests/test_path_safety_characterization.py` |
| 025 run-report 寫入協定單一來源 | `_write_run_report` 一律委派 `run_report_io` 弱協定或 `audit_report_pair` 強協定，禁止內嵌 `.part` staging；弱→強升級為後續獨立 spec | `tests/test_run_report_io_boundary.py` |
| 025 MCP facade 邊界 | `src` 僅一處 `FastMCP(`；`@mcp.tool()` 只存在 `mcp_tools_*` 群組模組；群組不得 import `mcp_server`；facade re-export 別名契約完整；completion 拒絕訊息單一來源於 Core | `tests/test_mcp_server_facade_boundary.py` |
| 025 docs 計數一致性 | 受治理文件的 tool 計數宣稱必須等於 live registry 數或帶 historical 標記；`*closeout*` 檔豁免 | `tests/test_docs_registry_count_consistency.py` |
| 025 測試資料目錄 fixture | conftest fixture 反射覆蓋全部 storage `*_DIR` 與 evals 旁路常數；`PODCAST_INGEST_DATA_DIR` 未設時預設不變；新測試檔不得再複製 `_use_tmp_data_dirs` | `tests/test_data_dir_fixture_contract.py` |
| 026 Hermes sidecar boundary | stdio/HTTP共用單一 FastMCP；HTTP僅loopback Streamable HTTP、non-root/no ports/no SSE；config/四 Skills採pre-mutation manifest-bound recovery。v2 direct validator不跑 inference，只輸出metadata/content equality booleans，拒絕`.env`/reparse/special entries；C6須reviewer＋唯一live run，C7須另案safe runtime evidence，否則維持Blocked。禁止protected digest/path/value、private endpoint、session/raw response輸出與目前計畫外的Hermes upgrade/hooks | `tests/test_mcp_http_transport.py`、`tests/test_hermes_deployment_contract.py`、`tests/test_hermes_integration.py`、`tests/test_hermes_live_smoke.py` |
| 027 Hermes Skill contract layer | Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS. It validates closed routing/protocol projections only, never production MCP, runtime inference, hooks, config, prompts, sessions, or C6. | `tests/test_hermes_skill_protocol.py`、`tests/test_spec_027_hermes_skill_protocol_docs.py` |
| 028 Hermes runtime capability gate | Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run. | `tests/test_hermes_runtime_capability.py`、`tests/test_spec_028_hermes_runtime_capability_docs.py` |

## How to Start a New Feature

新功能（runtime / MCP / LLM / side-effect）必須走 full Spec Kit flow：

```text
constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge
```

- Feature package 放在 `specs/<feature>`（下一個可用編號見 `specs/README.md`）。
- 對某個 package 跑 official scripts / skills 前，先設定 `SPECIFY_FEATURE_DIRECTORY`（見 `specs/README.md` 的 Official Spec Kit Layout and Active Feature Selection）。
- 小型 docs/test 修正若由 user 提供 concrete plan，可直接處理，但仍必須遵守 constitution。詳見 `docs/architecture-decision-records/ADR-0006-spec-kit-governance.md`。

## How to Verify Changes

依 `docs/verification-matrix.md`：先跑該變更類型的 targeted tests，再跑 full checks：

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

完成宣稱必須引用實際輸出；skip 任何驗證要說明原因。

## When to Stop and Ask for Human Approval

- 任何 safety-boundary 變更（上表九條之一）或 constitution 修訂。
- 新增 live provider、外部 API、依賴或大型架構變更。
- 刪除或改寫歷史 artifacts / eval reports。
- Key rotation / revocation：**human-only**，agent 不得代行。
- 發現測試與文件矛盾且無法判斷哪邊是 drift 時：停止並回報，不要用大規模 test rewrite 掩蓋。

## Known Risks / Batch 3 Candidates

- **F-03**（resolved, Batch 3A）：exact `api_cost_ack` guard 已下沉至 core-level — `semantic_summarize_episode` 進入點驗證、`llm_provider.create_provider` 建 provider 前驗證；CLI/MCP/workflow 包裝層 guard 保留為第一線（`tests/test_llm_ack_guard_contracts.py` 已更新為新 invariant）。
- **F-14**（resolved, Batch 3B）：storage.py 的 Phase 0 dead stub `search_transcripts`（實際只有一個，非兩個）已移除，連同僅供其 return annotation 使用的 `TranscriptSearchResult` import；public `search_transcripts` / `search_mentions` 一律解析到 `search.py`（`tests/test_contracts.py` 新增 module-provenance 斷言）。
- **F-18**（resolved, Batch 3B）：`research_workflow.py` 未使用的 `rebuild_cache` import 已移除；兩處以 `raising=True` 依賴該屬性的 monkeypatch guard 改為 patch 真正的 `cache.rebuild_cache`；`test_cache_rebuild_guard.py` allowlist 維持不變（`CACHE_STALE_WARNING` 字面值仍含 `rebuild_cache`）。
- **Provider factory boundary**（resolved, Batch 3B + 3C）：static guard（`tests/test_llm_provider_factory_boundary.py`）禁止 `src/` / `scripts/` 直接建構 `OpenAICompatibleProvider(...)`；Batch 3C 以 private factory token 在 constructor 拒絕 bare / forged construction，只允許 `create_provider`（exact `api_cost_ack` 後）建出 instance。
- **README cleanup**（resolved, 2026-08-22）：README 已改寫為人類導向的英文入口，並新增 `README.zh-TW.md` 中文版。
  完整 core function 清單、輸出路徑、CLI 與 MCP registry 移到 [`docs/api.md`](api.md)；agent handoff 狀態、Spec 編號、
  blocked 標記與 Phase 6H–7D.1 階段史移到本文件下方的 Relocated from README 區段。原本 pin README 的 exact-substring
  docs tests 已改為斷言新的 canonical 位置，邊界內容一字未鬆綁。

---

## Relocated from README (2026-08-22)

Everything below moved out of `README.md` so that the README could become a
human-facing introduction. Nothing here was rewritten; these are the same
status claims, boundary notes, and phase history, in the same words. This
section, not the README, is the place to record agent handoff state.

### Current status snapshot

Podcast Ingestion Core 是一個通用的 Podcast 擷取核心。目前已完成 RSS episode listing、episode lookup、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive Markdown 摘要、OpenAI-compatible LLM semantic summary pipeline、deterministic mention extraction、SQLite metadata cache / search，以及共用同一個 `FastMCP` instance 的本機 stdio 與 loopback Streamable HTTP sidecar。Hermes direct MCP/config/Skills 接入已可運作；Spec 026 的 C6 before/after metadata/content endpoint equality 已經 required reviewers 與唯一 live v2 run 驗證為 PASS-current，且不宣稱 snapshots 間沒有 transient mutation。C7 仍缺安全 runtime evidence；v0.20.0 tag `v2026.8.3` hooks只是候選，整體狀態維持 Blocked。Web UI、排程、embedding 與 vector search 仍未實作。

### Hermes / Spec 026-028 integration status

部署、config/Skill plan→apply→rollback、direct-safe validator 與移植方式見 [`deploy/hermes/README.md`](deploy/hermes/README.md) 與 [`specs/026-hermes-mcp-integration/quickstart.md`](specs/026-hermes-mcp-integration/quickstart.md)。Direct transport 已驗證可用；C6 的 boolean-only endpoint-equality validator 已通過 targeted tests、POSIX synthetic checks、兩位 reviewers 與唯一 live v2 run，狀態為 PASS-current且不得重跑。C7 仍 Blocked；Hermes v0.20.0 tag `v2026.8.3` hooks 只是未安裝、未實機驗證的候選能力。禁止讀取 live config values/session dump、保存 raw response、升級或啟用 hooks來補證。Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS. Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run.

### Semantic summary smoke and reviewed semantic context (Phase 6U-6V.1)

Phase 6U 補上 semantic summary smoke validation。這條路徑在 confirmed execution 會送 transcript text outside this machine；dry-run 只列 planned reads/writes、transcript transfer risk、cost risk 與 required acknowledgement，不呼叫 LLM、不寫 artifact、不輸出逐字稿內容。Confirmed semantic summary smoke 以及 direct `--mode semantic` CLI 都必須提供 exact `api_cost_ack`。CLI stdout 維持 no raw transcript stdout、不顯示 secret value；此階段 no MCP tool changes、no live market API、no automatic cache rebuild、no investment advice。
Phase 6U.1 修正 semantic review guard false positive：semantic summary review 允許 podcast 內容中 speaker 過去買進 / 持有這類 transcript-derived 描述，但仍拒絕直接 buy/sell/hold、建議買進、目標價與保證報酬。Confirmed semantic smoke 也加入 stderr progress，stdout 仍維持 JSON，且 progress 不輸出 raw transcript、prompt、API key 或 LLM response。
Phase 6V adds optional reviewed semantic context for stock lens synthesis. Default synthesis remains `phase-6f-stock-lens-json-only` and does not read `.semantic.md`. When explicitly enabled with `--include-semantic-context`, synthesis may include only matched episode semantic summaries with a latest passed review report; the input boundary becomes `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`. The context excludes `## Chunk Summaries`, does not read raw transcript text, does not read `.env`, does not fetch live market data, and makes no MCP tool changes. Reviewed semantic summary context is an LLM intermediate artifact, not podcast raw evidence and not an external market fact. Phase 6V.1 aligns the deterministic review gate with boundary/context consistency: JSON-only synthesis must have no semantic context, and reviewed semantic synthesis must include non-empty, review-passed semantic context.

### Research safety phase history (Phase 6H-6V.1)

Phase 6H 是 LLM 前置 safety gate，用來驗證研究層與未來 LLM workflow 不會幻覺、跳過 `api_cost_ack`、洩漏 raw transcript / API key、把 external boundary 當成已查證市場資料，或產生投資建議。

Research eval 文件：

- 流程與 rubric：[`docs/research-safety-eval.md`](docs/research-safety-eval.md)
- 可貼到 Codex session 的 prompts：[`docs/research-eval-prompts.md`](docs/research-eval-prompts.md)
- Phase 6H report template：[`evals/research-safety/phase-6h-research-session-template.md`](evals/research-safety/phase-6h-research-session-template.md)
- Phase 6O LLM smoke：[`docs/research-llm-smoke.md`](docs/research-llm-smoke.md)
- Phase 6O smoke template：[`evals/research-llm-smoke/phase-6o-llm-smoke-template.md`](evals/research-llm-smoke/phase-6o-llm-smoke-template.md)

Phase 6H 不呼叫 LLM、不讀 API key、不查外部市場資料、不新增 MCP tools，也不改 Phase 6G workflow。Phase 6I 已加入 optional semantic summary execution inside research workflow。Phase 6J 已加入 Stock Lens LLM Synthesis，輸入邊界是 6F stock lens JSON only，必須 exact api_cost_ack，no raw transcript、no external market data、no MCP tool changes。Phase 6K 已加入 workflow opt-in synthesis：`include_stock_lens_synthesis` 只在 workflow confirmed 且 exact ack 後執行 synthesis。Phase 6L 已加入 `run_research_workflow` MCP exposure：dry-run first，confirmed execution 才包裝 core workflow，LLM steps 仍需 exact ack，且 no automatic cache rebuild。Phase 6N 已加入 `include_external_data_verification` optional workflow fixture verification：只支援本機 fixture provider，no live market API、no API key、no MCP tool changes、no automatic cache rebuild，也不提供投資建議。Phase 6O 已加入 research-llm-smoke：real OpenAI-compatible smoke + Codex manual review，exact ack，no direct Codex-session backend、no live market data、no investment advice。Phase 6Q 已加入 LLM profile config：`--llm-profile pro4500` 可重用 provider/model/base URL/env var 名稱，但不保存 API key 值。Phase 6R 已加入本機 `.env` secret loader：手動 LLM smoke 可用 `API_KEY`、`MODEL`、`BASE_URL`，CLI metadata 只顯示 env var 名稱、不顯示 secret value。Phase 6T 已加入 research LLM smoke review report / quality gate：confirmed smoke 後可產生 deterministic review artifacts，no LLM call、no `.env` read、no external market data。Phase 6V 已加入 reviewed semantic context opt-in：stock lens synthesis 預設仍是 6F stock lens JSON only，明確啟用後才使用 review-passed `.semantic.md` context，no raw transcript、no live market data、no MCP tool changes、no investment advice。Phase 6V.1 已對齊 review gate boundary/context consistency：JSON-only artifact 不得帶 semantic context，reviewed semantic boundary 必須帶 review-passed context。

### Spec Kit / architecture phase history (Phase 7A-7D.1)

Phase 7A 是 Architecture / Spec Kit Stabilization，範圍是 docs/spec-only。它把目前 Phase 6T 研究系統整理回 spec-kit 可追蹤結構，不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 external market data，也不放寬 no investment advice 邊界。Phase 7A 後，下一個功能性候選階段是 Phase 6U semantic summary smoke 或小型 LLM output-quality tuning。

Phase 7B 是 Official Spec Kit Bootstrap。專案已正式加入官方 `specify init` 等價 scaffold：`.specify` 保存 Spec Kit memory、templates、scripts、workflow 與 integration metadata；`.agents/skills` 保存 Codex skills mode 的 `$speckit-*` skills；`AGENTS.md` 保存 repo-level agent rules。Phase 7B 不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 live market API，也不放寬 no investment advice 邊界。

Phase 7C 是 Spec Kit Constitution + Workflow Alignment。此階段把 `.specify/memory/constitution.md` 從官方 placeholder 專案化，並同步 `.specify/templates/`、`AGENTS.md`、architecture、roadmap 與 spec plan。Phase 7C 是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice。Phase 7C 後，新功能應走 full Spec Kit flow：`$speckit-constitution`、`$speckit-specify`、`$speckit-clarify`、`$speckit-plan`、`$speckit-checklist`、`$speckit-tasks`、`$speckit-analyze`、`$speckit-implement`、`$speckit-converge`；`$speckit-taskstoissues` 只在需要 GitHub issue handoff 時使用。Phase 6U semantic summary smoke 仍是後續可能的功能階段。

Phase 7D 是 Spec Kit Backfill via Full Workflow。此階段用 full Spec Kit flow 將已開發能力做 capability-group backfill：`specs/README.md` 是 registry，`001-gooaye-research-system` 保留為 umbrella product spec，`002-ingestion-transcript-core` 到 `007-spec-kit-governance` 記錄 as-built capability packages，其中 `006-llm-safety-synthesis-smoke-review` 覆蓋 optional LLM/smoke/review gate。Phase 7D 是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice，且明確記錄 `$speckit-clarify`、`$speckit-analyze`、`$speckit-converge` 的 backfill 步驟。

Phase 7D.1 是 Spec Kit Active Feature Guidance。此階段補清楚 official Spec Kit command usability：feature packages 的正確位置是 `specs/<feature>`，`.specify/` 是 scaffold/memory/templates/scripts metadata；多個 backfilled packages 不預設 pin 單一 active feature。要對某個 package 跑 official scripts / skills，先設定 `SPECIFY_FEATURE_DIRECTORY`，例如 `$env:SPECIFY_FEATURE_DIRECTORY="specs/003-metadata-search-mcp-core"`；官方 script 可能保存到 `.specify/feature.json`，切換 package 時重新設定即可。Phase 7D.1 不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 live market API，也不提供 investment advice。Phase 6U semantic summary smoke 仍是後續可能的功能階段。


### Spec034 Task #82 v8 review repair — current

**startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**. Spec034 remains offline/static-only with H2 exactly 20 upstream paths at H1 SHA-256 `90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d`; no 21st path is authorized. The isolated child accepts only a regular no-link/reparse-free project snapshot as its payload cwd, changes there before sentinel/Pytest/product import, and retains capability snapshot then project snapshot then stdlib only. Consequently C6's three relative config reads use snapshot-approved bytes even if original workspace configs change after snapshotting. Public receipt projection has no injected verifier; private issuance recomputes current canonical facts. AST proof follows one owner-local package spec/module/loader/return/register/context flow. Bundle rename parent fsync precedes the `bundle_renamed` journal with an explicit platform best-effort fallback, and exact nonce-bound both-missing recovery alone is retry-safe. Runner/journal/trust tests remain non-final. Every prior root is not approval evidence. Fresh code and architecture re-reviews remain required; Main alone may run the documented one-shot command after both PASS, and it is not run here.

> Spec034 Task #77 current terminal is **startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**. Its H2-frozen exact 20-file official `NousResearch/hermes-agent` bundle is static/offline only: startup order and the fixed `security-guidance` plugin identity chain are closed, while credential/provider construction data flow, whole-program closure, dynamic/user/project/entry-point plugin paths, runtime/secret edges, and actual activation remain blocked or unobserved. `runtime_status=not_run`; `live_actions_authorized=false`. The fresh review-only bootstrap/final trust chain is reserved for Main after both reviews PASS and remains unrun.

---

## Handoff — podcast-ingest-core, 2026-08-19

> Relocated from `HANDOFF-2026-08-19.md` in the repo root on 2026-08-22, so the
> root holds only what a first-time reader needs. The text is unchanged; only the
> heading levels moved one step down so the document nests under this one.

Written for the next agent picking this repo up. Read this before `README.md`;
it tells you what state the repo is actually in, which is not the same as what
the docs describe in aggregate.

### 1. Where the repo is right now

Specs 036–042 (X/YouTube ingest, summary profiles, study-guide lecture,
MCP tools 23–24, workflow derivation `05`/`06`) are on `main`. Task F /
Hermes 026–034 remains blocked: those tests fail or hang on digest pins
and nested sentinels. That is not a product regression. Do not start F
to “fix” the suite.

Copy `.env.example` to a local `.env` (gitignored). Never commit it.

**Suite baseline:** the documented non-Hermes ignore set in
`docs/install-and-porting.md` should pass. Unrestricted `python -m pytest`
still enters the blocked Hermes chain.

### 2. Environment traps that cost real time

**`.env` is local-only.** It holds `API_KEY`, `MODEL`, and `BASE_URL`
values. Committed `config/llm_profiles.yaml` stores only the environment
*name* `api_key_env: API_KEY`, never a key or endpoint. The committed
`gb10` profile is `unavailable: true`; `load_llm_profile("gb10")` fails
closed and names `pro4500` as the replacement. Operator docs and
`tests/test_architecture_spec_docs.py` pin `--llm-profile pro4500`.
Isolated fixture YAMLs may still use the name `gb10` / model `GB10`;
that is test data, not a working operator profile.

**Diagnostic:** every semantic summary records the provider and model in
its Metadata block. When an LLM call fails, read the last successful
artifact before blaming the service.

**Transcription** uses faster-whisper. CUDA (`--device cuda`) is
optional and faster; CPU is the supported fallback.

**Cache is never rebuilt automatically.** After any write that should
become searchable, run `python scripts/rebuild_cache.py --podcast <id>`
yourself. Every side-effect tool warns about this rather than doing it.

### 3. The two constraints that will bite you if you don't know them

**The rendered semantic summary Markdown is a contract, not a document.** Four
modules read its structure:

| Reader | Depends on |
| --- | --- |
| `semantic_review_artifact.py:143` | literal `## Chunk Summaries` |
| `semantic_review_artifact.py:151` | `Summary mode: semantic-llm`, `Provider:`, `Model:`, `Transcript status:` |
| `stock_lens_synthesis.py:494` | `re.split(r"(?im)^##\s+Chunk Summaries\s*$", …, maxsplit=1)` |
| `verified_research_lineage.py:820` | `summary_mode == "semantic-llm"` |

A summary profile may change what the LLM is asked to produce and the body text
under `## 摘要限制`. It may not change a heading, the Metadata block, or
`SUMMARY_MODE`. `tests/test_summary_profiles.py` enforces that no profile body
line can start with `#`.

**gooaye's output is a pinned fixed point.** Every published verified research
report descends from a semantic summary, so drifting the `finance` prompts by
one character is a data-integrity event, not a style change.
`tests/test_summary_profiles.py:31-68` hardcodes the prompt literals and
`tests/test_semantic_summarizer.py` pins the whole rendered document. If you
change those tests to make them pass, you have caused the thing they exist to
prevent.

### 4. Candidate tasks

Ordered by what the author of Spec 037 would pick up next. Each is
independently shippable. **A, B, and D are spec-gated** — this repo runs
Spec Kit (`specs/<nnn>-<name>/` with `spec.md`, `plan.md`, `tasks.md`,
`checklists/`), and Specs 036 and 037 are the two best templates to imitate.

#### Task A — `038`: the multi-document study guide *(highest value to the user)*

**Why this one.** Spec 037 made a single semantic summary read as study
material, and it works well. But the user's actual target has always been the
hand-written sequence in `../prompt-engineering/output/`: `00_video_info.md`,
`01_transcript_en.md`, `02_transcript_zh_tw.md`, `03_full_summary.md`,
`04_learning_notes.md`, `05_prompt_examples.md`, `06_apply_to_my_workflow.md`,
`07_final_study_guide.md`. Spec 036 Assumption 6 recorded that sequence as the
**target, not something to redesign**.

**What Spec 037 learned that constrains this.** The real learning-notes run
disclosed in its own 不確定事項 section that its reusable-prompt examples were
*reconstructed from spoken description, not quoted verbatim*. That is the
honest behaviour, and it is also the reason `05_prompt_examples.md` and
`06_apply_to_my_workflow.md` were held out of 037: they are workflow-specific
derivations, not summarisation of a transcript. Forcing them into a
summarisation prompt makes the model invent content the transcript does not
contain, which the repo's evidence rule forbids. **A spec that treats all eight
documents as one artifact family will produce fabrication in two of them.** The
design question to answer first is which documents are evidence-bound and which
are explicitly derivations, and whether derivations belong in this repo at all.

**Scope.** New artifact family, new `corpus_index` families, new canonical-path
rules, and a decision on whether translation (`02_transcript_zh_tw.md`) is in
scope — Spec 037 explicitly excluded translation.

#### Task B — `039`: YouTube as a third source, closing the `source_type` seam

**Why together.** Spec 036 left a seam and named it precisely
(`specs/036-x-video-corpus-ingestion/tasks.md:404-411`): `source_type` does not
propagate through corpus index → remediation plan → runner. Today
`corpus_remediation_plan.py` emits a "ready" audio action suggesting
`scripts/download_episode.py` for an x-video episode with missing audio, and the
seed's `has_audio_url=True` suppresses the "feed audio unavailable" blocker.
Execution then fails soft with the source refusal. It is the first operational
confusion an operator hits, and 036 called it **the seam the next source spec
must close**. Adding a third source without closing it triples the confusion.

**What is already reusable.** 036 proved the cheap route: `transcribe_episode`
already accepts `audio_path`, which bypasses `download_audio` entirely, and uses
its profile only for `language`. So a new source needs acquisition code and
nothing else. `yt-dlp` is already a dependency and already handles YouTube.

**Also in scope by necessity.** Divergent title provenance
(`corpus_local_transcription_runner` passes no `title`, so re-transcribing writes
a trio at `{ref}__{ref}.*` while the ingest flow derives paths from
`seed.title`; `storage.find_transcript_asset_paths` then resolves the ambiguity
by `sorted()[0]`). A third source makes this more likely, not less.

#### Task C — clean up the `gb10` profile *(done)*

Chose mark-unavailable over rename or silent repoint. Committed `gb10` keeps
`model: GB10` plus `unavailable: true`; `load_llm_profile` raises
`LLMProviderConfigError` and lists available profiles (`pro4500`). Operator
docs and the architecture pin moved to `--llm-profile pro4500`. Isolated
fixture YAMLs were left as `gb10`/`GB10`. Not spec-gated.

#### Task D — `040`: MCP exposure for X ingestion (Tool 23) *(implemented in tree)*

Spec 036 deliberately shipped Core plus a thin CLI and no MCP tool, on this
repo's own precedent: Spec 004 built the stock lens Core and CLI, and exposure
waited for Spec 035 as Tool 22. The registry count is a pinned chain running
through the Hermes AST projection, the Spec 029 descriptor snapshot, the deny
adapter, and the docs-count consistency check — they all move together.

Spec 040 decided the envelope: preview keeps `"dry_run": true`, names
`run_mode=preview`, and sets `network_read=true` /
`network_read_scope=public_metadata_only`. Confirm persists a metadata-only
run report. `XVideoIngestResult` now carries `run_mode` and
`not_investment_advice`.

#### Task E — `stock_lens_synthesis` profile gate *(done)*

`generate_stock_lens_synthesis_report` now loads the podcast profile and refuses
any `summary_profile` other than `finance` (and unknown podcast ids) before
dry-run planning or provider construction. `run_research_workflow` applies the
same helper when `include_stock_lens_synthesis=True`, so a learning-notes
podcast cannot even plan that step. Deterministic stock lens, mentions,
episode-intelligence, and industry-mapping still only read `display_name`;
those remain a later gate if a fifth profile appears.

#### Task 041 — YouTube ingest MCP (Tool 24) *(implemented in tree)*

Append-only Tool 24 `ingest_youtube_video` copies the Spec 040 preview
envelope (`dry_run` + `run_mode=preview` + `network_read`). Confirm wraps
existing Spec 039 Core ingest and writes a metadata-only run report.
Registry pin chain is 23→24. No Skill, no new dependency.

#### Task F — the blocked Hermes chain *(do not start casually)*

Package `026` is **Blocked**, and Spec 027's contract layer is complete while
actual Hermes runtime routing is `BLOCKED` / `not_evaluated`. This is the source
of the remaining Hermes 030–034 digest failures (12 failed + 034 g4 hang on
this machine). `specs/README.md` records the state in detail, including which
evidence grades are forbidden (live config values, session dumps, and raw
responses are all disallowed as evidence). This is governance-grade work with a
long paper trail; read `specs/026-hermes-mcp-integration/` and
`specs/033-hermes-v019-pinned-source-loader-audit/` fully before touching it.
Do not start this task to “fix” the suite.

### 5. Smaller recorded follow-ups

Genuine but not worth a spec on their own. Full context in
`specs/037-semantic-summary-profiles/tasks.md` and
`specs/036-x-video-corpus-ingestion/tasks.md`.

- The default profile literal is duplicated: `models.py:22` hardcodes
  `"finance"` while `summary_profiles.py:21` defines `DEFAULT_SUMMARY_PROFILE`.
  Left as-is to keep `models.py` dependency-free.
- `source_type` is not validated at load (`config.py:87` accepts any string;
  enforcement lives at the RSS surfaces in `require_rss_profile`), while
  `summary_profile` is. The asymmetry is principled — `summary_profile` has no
  downstream enforcement surface — but the two philosophies now sit on adjacent
  lines. The architecture review explicitly said not to reopen for it.
- The profile is resolved three times and degraded back to a string in between
  (`config.py` → `semantic_summarizer.py:66` → `:148` → `llm_provider.py:109`).
  All O(1); the string-typed factory parameter is the price of source
  compatibility. Cosmetic.
- Whitespace-padded profile values (`" finance "`) are accepted and
  canonicalised. Harmless, untested.
- X identity is permanent: `x-{handle}` with `_`→`-` is baked into every on-disk
  path. Injective for valid X handles, but a handle rename splits one account
  across two podcast ids forever. Accepted knowingly.

### 6. How this repo expects you to work

Read `.specify/memory/constitution.md` — nine numbered principles, and plans are
expected to state explicitly how they satisfy each. The ones that most often
decide a design here:

- **III Dry-run first.** Side-effect workflows return a plan and write nothing
  without `confirm=true`. Spec 036 shipped a dry-run plan that *claimed a write
  it would not perform* (it would have reused existing audio); that was caught
  only because the operator asked to see the plan before running. A plan that
  promises something that will not happen defeats the requirement's reason to
  exist.
- **IV LLM opt-in.** Any LLM call requires the exact `api_cost_ack` string, and
  the guard runs before provider construction. Do not move it, and do not let
  any new argument resolve before it.
- **VI No investment advice.** Note the shape of this after Spec 037: the
  enforcing check is `matched_investment_advice_guard`, which strips disclaimers
  *before* it scans. It is a prohibition detector, not a disclaimer requirement.
  A summary cannot become compliant by carrying a disclaimer.
- **IX TDD.** One focused RED before GREEN, per slice.

Risk classification is real here. Cross-module correctness, error-handling
paths, and non-breaking interface changes get a `code-reviewer` pass;
architectural boundaries add `architecture-reviewer`. Both reviews on Spec 037
found things the implementing session could not see from inside, including two
doc-drift defects where the spec package described a mechanism opposite to what
shipped.

**Verification is evidence, not assertion.** When Spec 037 needed to claim
"gooaye's corpus index is unchanged", reasoning was sufficient to dismiss the
concern (`corpus_index` never imports `config`) — the claim was tested anyway by
stashing the change and regenerating with pre-change code, because a claim
defended by argument is not evidence. Do that.

### 7. Immediate next action

A–E, 040, 041, and 042 are on `main`. Spec 042 is the separate
`workflow_derivation` family (`05`/`06`); it is not mixed into 038.
Task F / Hermes 026–034 is untouched. Next optional work is a live
YouTube confirm of Tool 24, or MCP exposure for 042 later. Do not
casually start Hermes.
