# ADR-0003: No Investment Advice Boundary

## Status

Accepted（constitution v1.0.0 原則 VI）

## Context

第一個 podcast profile 是股癌（財經主題）。系統整理 podcast 證據與研究線索，但產生 buy/sell/hold、target price、guaranteed returns 或個人化投資建議會帶來法規與誤用風險。

## Decision

系統不得產生投資建議。Reports 與 synthesis artifacts 保留 no investment advice 聲明（`not_investment_advice` 標記）；LLM smoke review gate 偵測並拒絕 prohibited advice 輸出（buy/sell/hold、target price、guaranteed return 樣式）；lens 設定層（`config/gooaye_lens.yaml`）也載明禁止產出。此邊界不得放寬。

## Consequences

- 所有輸出是研究整理，不是建議；下游使用者需自行判斷。
- 新 synthesis/report 路徑必須帶 no-advice 聲明並通過 review gate。
- 放寬此邊界屬 safety-boundary 變更：需人類批准 + constitution 修訂（MAJOR）。

## Guardrails & Tests

- `tests/test_research_llm_smoke_review.py` — prohibited_advice 偵測（"Buy … now"、target price、guaranteed return）。
- `tests/test_gooaye_lens.py` — lens safety text 必含 buy/sell/hold、target price 禁令。
- `tests/test_external_data_verification.py::test_verify_external_data_boundary_output_contains_no_advice`。
- `not_investment_advice=True` 標記散布於 workflow / stock lens / MCP tests。
