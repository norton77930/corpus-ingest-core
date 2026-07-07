# Architecture Decision Records (ADR)

本目錄記錄已定案的核心架構決策。每個 ADR 用短格式：Status / Context / Decision / Consequences / Guardrails & Tests。ADR 是決策摘要；正式邊界定義以 `.specify/memory/constitution.md` 為準，executable record 是 `tests/`。

## Index

| ADR | 決策 | 對應 constitution 原則 |
| --- | --- | --- |
| [ADR-0001](ADR-0001-thin-cli-thick-core.md) | Thin CLI / thick core | II. Thin Interfaces over Thick Core |
| [ADR-0002](ADR-0002-dry-run-confirm-boundary.md) | Dry-run first / explicit confirm | III. Dry-Run First Side Effects |
| [ADR-0003](ADR-0003-no-investment-advice-boundary.md) | No investment advice | VI. No Investment Advice |
| [ADR-0004](ADR-0004-source-of-truth-vs-cache.md) | Artifacts 是 source of truth，cache 是 derived | I. Local Artifacts and Evidence Traceability、VIII. Manual Cache Rebuild |
| [ADR-0005](ADR-0005-llm-input-output-boundary.md) | LLM input/output boundary 與 exact ack | IV. LLM Opt-In and Secret Boundary、V. Evidence Separation |
| [ADR-0006](ADR-0006-spec-kit-governance.md) | Spec Kit governance 與 full flow 適用範圍 | Spec Kit Development Workflow、IX. TDD and Verification Gates |

## 修訂規則

- 改變既有決策：新增 superseding ADR 並將舊 ADR 的 Status 改為 Superseded，不改寫歷史內容。
- 涉及 safety boundary 的 ADR 變更需人類批准，並依 constitution Governance 段評估版本升級。
