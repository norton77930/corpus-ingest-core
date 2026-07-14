# MCP Usage

## 啟動前檢查

Phase 4A MCP server 是本機 stdio server。啟動前建議先確認 SQLite cache 與 CLI search 可用：

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 5 --search-mode auto
python scripts/search_mentions.py --podcast gooaye --query 台積電 --type company
```

啟動 server：

```powershell
python scripts/run_mcp_server.py
```

此指令會進入 stdio server 等待 MCP client 連線，不會啟動 Web server。

## Codex / Claude 設定範例

請把路徑改成你本機 repo 的實際位置，不要把個人絕對路徑 commit 進專案。

```toml
[mcp_servers.podcast-ingest-core]
command = "python"
args = ["D:/path/to/podcast-ingest-core/scripts/run_mcp_server.py"]
```

## Tools

### Read / Query Tools

- `list_episodes`
- `get_episode`
- `validate_transcript`
- `search_transcripts`
- `search_mentions`
- `rebuild_cache`

`rebuild_cache` 是 maintenance tool，只索引既有 artifacts，不會下載音檔、轉錄、摘要或抽 mentions。Search tools 不會自動 rebuild cache；如果 cache 不存在，請先執行 `rebuild_cache`。

### Confirmed Local Side-Effect Tools

- `download_audio`
- `transcribe_episode`
- `summarize_episode_extractive`
- `extract_mentions`

Side-effect tools 預設 `confirm=false`，只回傳 action plan，不會執行。確認 runtime、IO、overwrite 與 cache stale 風險後，才再次以 `confirm=true` 呼叫。

```text
Call transcribe_episode with confirm=false first to review the action plan.
Call transcribe_episode again with confirm=true only if you accept the runtime and resource cost.
```

Side-effect tools 成功後不會自動 rebuild cache；若要讓新 transcript / summary / mentions 被 search 查到，請手動執行 `rebuild_cache`。

### API-Cost Tool

- `semantic_summarize_episode`

此 tool 預設也是 dry-run，但它會把 transcript text 傳送到外部 LLM provider，可能產生 API 費用，因此除了 `confirm=true`，還需要 exact acknowledgement。

### Workflow Tool

- `run_research_workflow`

Phase 6L consolidated workflow tool，dry-run first：`confirm=false` 只回傳 planned reads/writes、step order、external API / cost risk、cache stale warning 與 required acknowledgement，不寫 artifacts、不呼叫 LLM、不回 raw transcript。`confirm=true` 執行本機 deterministic research steps；若包含 `include_semantic_summary=true` 或 `include_stock_lens_synthesis=true`，仍必須提供 exact `api_cost_ack`。完成後不會自動 rebuild cache；若要讓 search metadata 更新，請手動呼叫 `rebuild_cache`。

MCP 版刻意只暴露 core workflow 參數的子集：不含 fixture external data verification（`include_external_data_verification`）與 reviewed semantic context opt-in（`include_semantic_context_in_synthesis`）。需要完整參數時請使用 CLI `python scripts/run_research_workflow.py`。

### Human-Controlled Episode Completion Tool

- `run_corpus_episode_completion_workflow`

016 completion tool 使用 preview → human approval → one action 的流程。先以
`action=next, confirm=false` 取得 canonical episode、selected action、planned
reads/writes 與風險；只有在使用者明確同意後，才以該 canonical episode、同一個
explicit action 與 `confirm=true` 執行一次。confirmed mode 會拒絕 `next` 與
`latest`。若 selected action 是 `semantic_summary`，使用者還必須提供 exact
`api_cost_ack`；MCP server 不會載入 `.env`，也不會自動 rebuild cache。完成或
blocked/rejected 後必須停止，不會自動改跑下一個 action。

需要讓 Agent 依人類控制流程操作時，掛載 repository 的 portable
`corpus-episode-completion` Skill。它只使用此 MCP tool：preview、解釋、等待
明確同意、確認同一個 canonical action、回報並停止；MCP 不可用時不改用 CLI、
terminal、scheduler 或 retry。

## Safety

MCP tools 不接受任意本機檔案路徑，也不構成投資建議。

`semantic_summarize_episode` 是 API-cost tool，會呼叫外部 LLM provider，可能將 transcript text 傳送到本機外並產生費用。它比其他 side-effect tools 更嚴格：

- `confirm=false`：只回傳 dry-run action plan，不呼叫 LLM，不回傳逐字稿原文。
- `confirm=true`：仍必須提供 exact `api_cost_ack`。
- `api_cost_ack` 必須完全等於：

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

範例流程：

```text
Call semantic_summarize_episode with confirm=false first to review the action plan.
Only call again with confirm=true and the exact api_cost_ack string if you accept the external API call, data transfer, and cost risk.
```

Semantic summary tool 不會回傳 API key、不接受任意 transcript path，也不會自動 rebuild cache。成功後若要讓 search cache 知道新的 `.semantic.md`，請手動執行 `rebuild_cache`。

## Client Setup

- Codex setup：[`codex-mcp-setup.md`](codex-mcp-setup.md)
- Claude setup：[`claude-mcp-setup.md`](claude-mcp-setup.md)
- Troubleshooting：[`mcp-troubleshooting.md`](mcp-troubleshooting.md)

本機 readiness check：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```
