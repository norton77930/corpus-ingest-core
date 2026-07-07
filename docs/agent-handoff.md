# AI Agent Handoff Entrypoint

這是新 AI agent（Opus 4.8、GPT-5.5 或其他）接手本 repo 的第一份文件。目標：10 分鐘內理解專案、知道哪些檔案是 source of truth、哪些邊界不可逾越、如何開始與驗證工作。

## Project Summary

Podcast Ingestion Core 是一個本機優先的通用 Podcast 擷取與研究核心：RSS episode listing、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive 摘要、opt-in 的 OpenAI-compatible LLM semantic summary、deterministic mention extraction、SQLite metadata cache / search、stdio-only MCP server（恰好 12 個 reviewed tools），以及 deterministic research workflow（stock lens synthesis、external data boundary）。第一個 podcast profile 是 Gooaye 股癌，但核心程式不得寫死股癌；所有 podcast-specific 設定在 `config/podcasts.yaml`。本專案支援 evidence-based 研究整理，明確**不**提供投資建議。

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

- **已實作**：RSS episode listing、episode lookup、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive Markdown 摘要、opt-in LLM semantic summary pipeline、deterministic mention extraction、SQLite metadata cache / search、stdio-only MCP server（12 tools）、research workflow orchestration、stock lens synthesis、external data boundary（local fixture only）。
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
| No investment advice | 不得產生 buy/sell/hold、target price、guaranteed returns 或個人化投資建議；review gate 會拒絕 prohibited advice 輸出 | `tests/test_research_llm_smoke_review.py`、`tests/test_gooaye_lens.py` |
| No automatic cache rebuild | Side-effect tools 完成後不得自動 `rebuild_cache`，只回 cache stale warning；rebuild 是手動操作 | `tests/test_cache_rebuild_guard.py` |
| Thin CLI / thick core | Runtime 行為住在 `src/podcast_ingest_core`；`scripts/` 與 MCP tools 只解析輸入、呼叫 core、格式化輸出 | `tests/test_contracts.py` |
| MCP JSON envelope | MCP responses 維持既有 envelope：`{"ok": true, "data": ...}`、`{"ok": false, ...}`、dry-run 含 `"dry_run": true`；恰好 12 個 reviewed tools | `tests/test_mcp_tool_registry_contract.py`、`tests/test_mcp_server.py` |

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
- **F-14**：storage dead stubs 尚未移除。
- **F-18**：unused import 尚未清理（僅 docs 記錄，未處理）。
- **README cleanup**：README 很長且含大量 phase history，完整重整尚未進行；大量 exact-substring docs tests 使搬移成本高。
