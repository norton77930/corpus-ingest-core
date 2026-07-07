# ADR-0001: Thin CLI / Thick Core

## Status

Accepted（constitution v1.0.0 原則 II）

## Context

同一組能力要同時服務 CLI scripts、MCP tools、tests 與未來自動化。若邏輯散落在 scripts，會出現重複實作與行為漂移。

## Decision

Runtime 行為一律住在 `src/podcast_ingest_core`。`scripts/` 與 MCP tools 是 thin wrappers：解析輸入、呼叫 core functions、格式化輸出。範例：`scripts/run_research_workflow.py` 只做 argparse 與 JSON 輸出，實際工作在 `podcast_ingest_core.run_research_workflow`。Public core functions 維持穩定 contract，變更需批准的 phase 加上測試與文件。

## Consequences

- CLI、MCP、tests 行為一致；新介面（未來 Web UI）可直接重用 core。
- 修 bug 或加行為時，改 core 並補 core-level tests，不在 wrapper 疊邏輯。
- 代價：wrapper 層偶有樣板重複（例如 ack 轉發），見 ADR-0005 的 F-03 記錄。

## Guardrails & Tests

- `tests/test_contracts.py` — package 必須匯出 required core functions、storage 路徑 deterministic。
- `tests/test_mcp_tool_registry_contract.py` — MCP wrappers 維持 reviewed 參數集。
- `AGENTS.md` Engineering Rules — thin CLI / thick core 為 hard constraint。
