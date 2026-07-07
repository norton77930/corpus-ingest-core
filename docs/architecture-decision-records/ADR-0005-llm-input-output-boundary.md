# ADR-0005: LLM Input/Output Boundary

## Status

Accepted（constitution v1.0.0 原則 IV、V）

## Context

LLM 呼叫會把資料送出本機並產生費用。必須明確控制：什麼資料可以進 LLM、什麼輸出可以落地、執行前要什麼確認。

## Decision

- LLM 執行是 opt-in：confirmed 執行前必須提供 exact `api_cost_ack` 字串；常數單一來源是 `semantic_summarizer.SEMANTIC_API_COST_ACK`（`mcp_server` re-export），不得複製散落。
- Input 邊界：semantic summary 是唯一可送 transcript 原文給 LLM 的路徑，且只在明確 ack 後；stock lens synthesis 只吃 `phase-6f-stock-lens-json-only` 輸入（可選 reviewed semantic context），不吃 raw transcript。
- Output 邊界：LLM-facing CLI 的 stdout/stderr 不含 transcript 原文、prompt 內容或 API key 值；semantic CLI stdout 是鎖定的 metadata-only JSON schema。`.env` 值、API keys、provider secrets 不得出現在 committed 檔案、MCP responses 或 review reports。
- LLM 輸出必須與 podcast evidence / deterministic inference / external status 分離標示（原則 V）。

## Consequences

- 任何新 LLM-facing 路徑都要接上 wrapper-level ack guard 與 no-leak 測試。
- **F-03（known risk）**：ack guard 位於 CLI/MCP 包裝層，semantic core function 本身沒有 ack 參數；`tests/test_llm_ack_guard_contracts.py` 已 characterize 此現況。core-level 設計未定案，改動需批准。
- Ack 字串不得集中化重構或改字面值（會破壞 exact-match guard），除非批准的 phase 同步更新 guards。

## Guardrails & Tests

- `tests/test_llm_ack_guard_contracts.py` — exact ack、單一來源、F-03 characterization。
- `tests/test_llm_cli_no_leak.py` — no raw transcript / prompt / key on stdout。
- `tests/test_semantic_summarizer.py`、`tests/test_stock_lens_synthesis.py` — input 邊界與 pipeline 行為。
- `tests/test_repository_secret_boundary.py` — committable 檔案無 secret-like 值。
