# ADR-0005: LLM Input/Output Boundary

## Status

Accepted（constitution v1.0.0 原則 IV、V）

## Context

LLM 呼叫會把資料送出本機並產生費用。必須明確控制：什麼資料可以進 LLM、什麼輸出可以落地、執行前要什麼確認。

## Decision

- LLM 執行是 opt-in：confirmed 執行前必須提供 exact `api_cost_ack` 字串；常數單一來源定義於 `llm_provider.SEMANTIC_API_COST_ACK`，經 `semantic_summarizer.SEMANTIC_API_COST_ACK` 與 `mcp_server` re-export，不得複製散落。
- Input 邊界：semantic summary 是唯一可送 transcript 原文給 LLM 的路徑，且只在明確 ack 後；stock lens synthesis 只吃 `phase-6f-stock-lens-json-only` 輸入（可選 reviewed semantic context），不吃 raw transcript。
- Output 邊界：LLM-facing CLI 的 stdout/stderr 不含 transcript 原文、prompt 內容或 API key 值；semantic CLI stdout 是鎖定的 metadata-only JSON schema。`.env` 值、API keys、provider secrets 不得出現在 committed 檔案、MCP responses 或 review reports。
- LLM 輸出必須與 podcast evidence / deterministic inference / external status 分離標示（原則 V）。

## Consequences

- 任何新 LLM-facing 路徑都要接上 wrapper-level ack guard 與 no-leak 測試；core-level guard（見下）是第二線，不是 wrapper guard 的替代。
- **F-03（resolved, Batch 3A）**：exact ack 已在 core-level 強制 — `llm_provider.create_provider` 新增 keyword-only `api_cost_ack`，建構任何 provider 前驗證；`semantic_summarize_episode` 新增 keyword-only `api_cost_ack`，於進入點（所有 early return 之前）驗證。Migration note：直接呼叫這兩個 function 的 library caller 必須傳入 exact ack，否則 raise `LLMProviderConfigError`（fail closed）。殘餘風險：直接建構 `OpenAICompatibleProvider` 可繞過 factory gate。**規則（Batch 3B）**：app code 必須經 `create_provider`，不得直接呼叫 `OpenAICompatibleProvider` constructor，由 `tests/test_llm_provider_factory_boundary.py` static guard 強制（`src/`、`scripts/` 內皆無直接建構）；runtime constructor-level 禁止仍列為 Batch 3C 候選。
- Ack 字串不得集中化重構或改字面值（會破壞 exact-match guard），除非批准的 phase 同步更新 guards。

## Guardrails & Tests

- `tests/test_llm_ack_guard_contracts.py` — exact ack、單一來源、core-level guard（F-03 resolved：core signature 與 provider-construction gate contracts）。
- `tests/test_llm_provider_factory_boundary.py` — provider 只在 `create_provider` factory 建構（`src/`、`scripts/` app code 不得直接 new `OpenAICompatibleProvider`）；`create_provider` 維持 keyword-only `api_cost_ack`（Batch 3B）。
- `tests/test_llm_cli_no_leak.py` — no raw transcript / prompt / key on stdout。
- `tests/test_semantic_summarizer.py`、`tests/test_stock_lens_synthesis.py` — input 邊界與 pipeline 行為。
- `tests/test_repository_secret_boundary.py` — committable 檔案無 secret-like 值。
