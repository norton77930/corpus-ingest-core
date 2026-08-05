# AI Agent Handoff Entrypoint

這是新 AI agent（Opus 4.8、GPT-5.5 或其他）接手本 repo 的第一份文件。目標：10 分鐘內理解專案、知道哪些檔案是 source of truth、哪些邊界不可逾越、如何開始與驗證工作。

## Project Summary

Podcast Ingestion Core 是一個本機優先的通用 Podcast 擷取與研究核心：RSS episode listing、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive 摘要、opt-in 的 OpenAI-compatible LLM semantic summary、deterministic mention extraction、SQLite metadata cache / search、stdio-only MCP server（恰好 18 個 reviewed tools），以及 deterministic research workflow（stock lens synthesis、external data boundary）。第一個 podcast profile 是 Gooaye 股癌，但核心程式不得寫死股癌；所有 podcast-specific 設定在 `config/podcasts.yaml`。本專案支援 evidence-based 研究整理，明確**不**提供投資建議。
Corpus packages 008–018 add local artifact indexing/planning, bounded intake/download/transcription/deterministic remediation, a one-stage fresh workflow, standalone `015-corpus-semantic-remediation-runner`, the human-controlled `016-corpus-episode-completion-workflow-runner`, `017-corpus-latest-episode-deterministic-workflow`, and `018-latest-episode-verified-research-report-workflow`. 016 previews in memory with strict zero-file behavior, 017 locks latest once and stops at `ready_for_semantic_summary`, and 018 validates a previewed exact episode reference plus exact acknowledgement before it pins, gates, researches, and atomically publishes a digest-versioned verified report bundle.
The local stdio registry has exact 19 reviewed tools. Tool 19, `query_verified_research_report_coverage`, is append-only after Tools 1–18; it is a read-query episode-centric coverage join (no confirm/ack). Tool 18, `revalidate_verified_research_report_sources`, remains append-only exact-locator source revalidation. Tool 17 retains its catalog contract.
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

- **已實作**：RSS episode listing、episode lookup、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive Markdown 摘要、opt-in LLM semantic summary pipeline、deterministic mention extraction、SQLite metadata cache / search、stdio-only MCP server（19 tools）、research workflow orchestration、stock lens synthesis、external data boundary（local fixture only）。
- **Corpus 已實作**：008–022，包括 strict-zero-file 014 workflow、standalone semantic remediation runner、human-controlled completion workflow、pinned latest deterministic readiness、latest verified research report（018）、explicit-episode assemble/publish（019）、offline catalog（020）、source revalidation（021），以及 episode-centric coverage index（022 / Tool 19）；confirmed summary requires exact acknowledgement before profile/`.env`, deterministic review uses no LLM configuration, 018 atomically publishes an identity-validated digest bundle only after review passes, and 019 publishes the same bundle class for a named episode without LLM/ack when lineage already passes.
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
| MCP JSON envelope | MCP responses 維持既有 envelope：`{"ok": true, "data": ...}`、`{"ok": false, ...}`、dry-run 含 `"dry_run": true`；恰好 18 個 reviewed tools | `tests/test_mcp_tool_registry_contract.py`、`tests/test_mcp_server.py` |
| 019 explicit-episode verified report / Skill | Preview is strict zero-write for a named `episode_ref` (reject latest/next). Confirm assembles/publishes only when local artifacts and lineage already pass; no `api_cost_ack`, no LLM/RSS/download, no 015–017 chaining. Blocked lists missing/stale roles. historically MCP Tool 16 + portable Skill | `tests/test_episode_verified_research_report_workflow_runner.py`、`tests/test_episode_verified_research_report_skill.py`、`tests/test_mcp_tool_registry_contract.py` |

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
- **Provider factory boundary**（Batch 3B）：新增 `tests/test_llm_provider_factory_boundary.py` static guard — 禁止 `src/` 與 `scripts/` 直接建構 `OpenAICompatibleProvider(...)`，一律須經 `create_provider`；runtime constructor-level 禁止仍列為 Batch 3C 候選。
- **README cleanup**：README 很長且含大量 phase history，完整重整尚未進行；大量 exact-substring docs tests 使搬移成本高。
