# Codex MCP Setup

本文件說明如何把本專案的 stdio MCP server 接到 Codex CLI / Codex TUI 類 client。請將所有 placeholder path 換成本機 repo 位置；不要把個人 `~/.codex/config.toml`、API key 或含個人絕對路徑的設定 commit 進 repo。

## 1. 前置條件

請先確認 Python 環境已安裝專案 dependencies：

```powershell
python -m pip install -e .[dev]
```

確認測試與 MCP server runner 可用：

```powershell
python -m pytest
python -m compileall src scripts
python scripts/run_mcp_server.py
```

`run_mcp_server.py` 是 stdio server；手動執行時等待 client 連線是正常行為，可用 Ctrl+C 停止。

建立或更新 SQLite cache：

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
```

## 2. CLI 驗證

接 MCP client 前，先用 CLI 確認資料可查：

```powershell
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 5 --search-mode auto

python scripts/search_mentions.py --podcast gooaye --query 台積電 --type company
```

也可以執行本機 setup validation：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

## 3. Codex User-level Config 範例

以下是 placeholder 範例。請把 `D:/path/to/podcast-ingest-core` 換成你的 repo 實際路徑。

```toml
[mcp_servers.podcast-ingest-core]
command = "python"
args = ["D:/path/to/podcast-ingest-core/scripts/run_mcp_server.py"]
cwd = "D:/path/to/podcast-ingest-core"
startup_timeout_sec = 20
tool_timeout_sec = 120
enabled = true
default_tools_approval_mode = "prompt"
```

注意：

- 不要把 user-level config commit 到 repo。
- 如果需要 API key，請使用本機環境變數，不要寫進 config。
- `semantic_summarize_episode` 即使出現在 MCP tools 中，也仍需要 `confirm=true` 與 exact `api_cost_ack`。

## 4. Codex CLI Command 範例

也可以用 Codex CLI 新增 server：

```powershell
codex mcp add podcast-ingest-core -- python D:/path/to/podcast-ingest-core/scripts/run_mcp_server.py
```

使用 `config.toml` 可更明確指定 `cwd`、timeout 與 approval mode。若用 CLI add 後仍需要調整 `cwd`，建議打開 `~/.codex/config.toml` 手動補上。

## 5. Codex TUI 驗證

1. 啟動 `codex`
2. 輸入 `/mcp`
3. 確認 `podcast-ingest-core` server active
4. 詢問 Codex：

```text
請用 podcast-ingest-core 搜尋股癌 EP672 有沒有提到台積電。
```

5. 確認它使用 `search_transcripts` 或 `search_mentions` tool。

## 6. 建議測試 Prompt

```text
請用 podcast-ingest-core MCP 搜尋 gooaye 裡提到「台積電」的 transcript evidence。
```

```text
請用 podcast-ingest-core MCP 查 gooaye EP672 的 transcript validation 狀態。
```

```text
請用 podcast-ingest-core MCP 搜尋 mentions 中 type=company 且 query=台積電 的結果。
```

```text
請 dry-run transcribe_episode，不要真的執行，先告訴我會做什麼。
```

```text
請 dry-run semantic_summarize_episode，不要呼叫 LLM，先列出風險與 required acknowledgement。
```

## 7. 不應 Commit 的內容

不要 commit：

- 個人的 `.codex/config.toml`
- 含個人絕對路徑的設定
- API key
- `.env`
- transcript / audio / summary / SQLite cache 大檔，除非專案政策明確允許

