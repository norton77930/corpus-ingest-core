# MCP Troubleshooting

## 問題 1：MCP Server 沒出現在工具列表

先在 repo 根目錄確認 runner 與 Python 程式可用：

```powershell
python scripts/run_mcp_server.py
python -m compileall src scripts
python -m pytest
```

檢查 MCP client config 的 `command`、`args` 與 `cwd`。Windows 建議使用正斜線 `/` 或 escaped backslash，並明確設定 `cwd`。

## 問題 2：Search Tool 回報 Cache Missing

SQLite cache 是衍生資料，不會自動建立。請執行：

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
```

再重新執行 search tool。

## 問題 3：Search 查不到資料

先用 CLI 驗證：

```powershell
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 5 --search-mode auto

python scripts/search_mentions.py --podcast gooaye --query 台積電 --type company
```

如果 CLI 也查不到，請確認 transcript / mentions artifacts 是否存在，並重新執行 `rebuild_cache`。

## 問題 4：Side-effect Tool 沒真的執行

這是預期行為：

- 預設 `confirm=false` 是 dry-run。
- 必須 `confirm=true` 才會執行下載、轉錄或寫 artifacts。
- `semantic_summarize_episode` 還需要 exact `api_cost_ack`。

## 問題 5：Semantic Summary 被拒絕

請檢查：

- `OPENAI_API_KEY` 是否存在於本機環境變數。
- model 是否透過 CLI/MCP input 或 `OPENAI_MODEL` 設定。
- `api_cost_ack` 是否完全相符。
- transcript validation 是否為 `valid`，或在可接受風險時明確使用 `allow_partial=true`。

Exact acknowledgement：

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

## 問題 6：Windows Path 問題

建議：

- 使用正斜線 `/`，例如 `D:/path/to/corpus-ingest-core/scripts/run_mcp_server.py`。
- 或使用 escaped backslash。
- 儘量設定 `cwd`。
- 先在 PowerShell 直接跑：

```powershell
python scripts/run_mcp_server.py
```

## 問題 7：MCP Server 啟動後等待不退出

stdio server 等待 MCP client 連線是正常行為。手動 smoke test 可用 Ctrl+C 停止。

## 本機 Validation

可以用本專案提供的 validation script 做一次整體檢查：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

