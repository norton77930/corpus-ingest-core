# ADR-0002: Dry-Run First / Explicit Confirm Boundary

## Status

Accepted（constitution v1.0.0 原則 III）

## Context

Side-effect workflows 會寫 artifacts、下載音檔、呼叫 provider、產生成本。本機研究自動化必須先看得到計畫中的寫入與風險，才能執行。

## Decision

所有 side-effect workflows/tools 預設 dry-run：MCP side-effect tools 一律 `confirm=False` 預設，CLI 用顯式 `--confirm`。Dry-run 回應列出 planned reads、planned writes、step order、required confirmation 與 known risks，且不寫檔、不呼叫 provider。

## Consequences

- Agent 與人類都能在執行前 audit 副作用；誤觸成本大幅降低。
- 新增 side-effect tool 時必須同時實作 dry-run 路徑，且 confirm 預設為 False。
- Dry-run 輸出本身也受 no-leak 邊界約束（見 ADR-0005）。

## Guardrails & Tests

- `tests/test_mcp_tool_registry_contract.py` — 全部 6 個 side-effect tools 預設 `confirm=False`；dry-run envelope 含 `"dry_run": true`。
- `tests/test_research_workflow.py` — workflow dry-run/confirm 行為。
- `tests/test_llm_cli_no_leak.py` — dry-run stdout 不洩漏 transcript/prompt/key。
