# Claude MCP Setup

本專案的 MCP server 是本機 stdio server，不啟動 Web server、不使用 HTTP / SSE transport。Claude Desktop、Claude Code 或其他 Claude 類 MCP client 的設定格式可能因版本不同而略有差異；請依你的 client 文件調整。

## 前置檢查

```powershell
python -m pytest
python -m compileall src scripts
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

## Generic Claude MCP Config 範例

請把 `D:/path/to/podcast-ingest-core` 換成你的 repo 實際路徑。不要在設定中放 API key。

```json
{
  "mcpServers": {
    "podcast-ingest-core": {
      "command": "python",
      "args": [
        "D:/path/to/podcast-ingest-core/scripts/run_mcp_server.py"
      ],
      "cwd": "D:/path/to/podcast-ingest-core"
    }
  }
}
```

## Tool Safety

Read / query tools 可直接查詢既有 metadata 與 SQLite cache：

- `list_episodes`
- `get_episode`
- `validate_transcript`
- `search_transcripts`
- `search_mentions`
- `rebuild_cache`
- `query_verified_research_report_catalog` (Tool 17)
- `revalidate_verified_research_report_sources` (Tool 18)
- `query_verified_research_report_coverage` (Tool 19)
- `suggest_historical_verified_report_next_step` (Tool 20)
- `list_verified_report_gap_backlog` (Tool 21)

The local reviewed registry has exactly 21 tools. Tool 21 is append-only: Tools 1–20 keep their contracts/order. It is an offline read-only inventory gap backlog (`podcast_id`, optional `limit`); no `confirm` or acknowledgement. Tool 20 remains historical next-step suggestion. Tool 19 remains coverage join. Tool 18 remains exact-locator source revalidation. Tool 17 retains its offline read-only manifest-first list/search/inspect contract, including `source_currentness_status=not_evaluated` for inspect.

Local side-effect tools 預設 `confirm=false`，只回傳 dry-run action plan：

- `download_audio`
- `transcribe_episode`
- `summarize_episode_extractive`
- `extract_mentions`

`confirm=true` 才會下載、轉錄或寫入 artifacts。這些 tools 不接受任意本機 path，也不會自動 rebuild cache。

## API-cost Tool

`semantic_summarize_episode` 可能呼叫外部 LLM provider、傳送 transcript text 到本機外並產生費用。除了 `confirm=true`，還必須提供 exact `api_cost_ack`：

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

文件與設定都不要放任何真實 API key。若需要 API key，請在本機環境變數中設定，例如 `OPENAI_API_KEY`；本專案不會把 API key 寫入 MCP response。

本專案產生的搜尋、mentions 與 summaries 不構成投資建議。

