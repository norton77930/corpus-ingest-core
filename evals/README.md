# Evals

`evals/` 用來存放 MCP tool-use eval 的報告與流程文件。這些報告協助記錄 Codex / Claude 類 MCP client 是否正確使用 `corpus-ingest-core` tools。

報告可以包含：

- Prompt
- Expected tool
- Actual tool
- Tool arguments
- Pass / Fail
- Issue summary
- Follow-up action

報告不應包含：

- API key、token、cookie 或任何 secret
- 個人的 Codex / Claude config
- 含個人絕對路徑的設定
- 完整 transcript dump 或大量逐字稿原文
- 外部 LLM raw response

若需要保存原始工具輸出或 session log，請先確認沒有 secret、個人路徑或大量 transcript 原文。原始 log 建議放在 `evals/**/raw/`，此路徑預設不應提交。
