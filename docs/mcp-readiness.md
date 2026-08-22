# MCP Readiness

> Spec 029 is **Offline Implemented** only: live preflight not run; G2-G3 not authorized; source contract remains `BLOCKED_RUNTIME_SEAM`. A future PASS is only an expected high-level MCP tool-call attempt policy-blocked before dispatch, not internal Skill selection, fallback, 019 outcome, or Core execution.

## 設計目標

本專案先把核心能力設計成可被 MCP tools 直接包裝的 Python functions。Phase 4A 建立 stdio MCP server skeleton；Phase 4B 新增 side-effect tools，全部採 dry-run first 與 explicit confirmation。Phase 4C 新增 semantic summary MCP tool，並加入外部 API、資料傳送與費用 acknowledgement gate。
Phase 5A 補齊 Codex / Claude 類 MCP client setup 文件與本機 readiness validation script。Spec 026 保留 stdio，並以同一個 `FastMCP` instance 增加 loopback-only Streamable HTTP runner與 Hermes sidecar；direct MCP/config/Skills 已實機驗證，C6 boolean-only endpoint equality也已通過targeted tests、POSIX synthetic checks、兩位reviewers與唯一live v2 run，狀態為PASS-current。C7仍Blocked；Hermes v0.20.0 tag `v2026.8.3` hooks僅是未安裝、未runtime驗證的候選能力。Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS.

## 可包裝的 Core Functions

- `list_episodes(podcast_id, limit)`
- `get_episode(podcast_id, episode_ref)`
- `download_audio(podcast_id, episode_ref)`
- `transcribe_episode(podcast_id, episode_ref)`
- `summarize_episode(podcast_id, episode_ref)`
- `semantic_summarize_episode(podcast_id, episode_ref, ...)`
- `extract_mentions(podcast_id, episode_ref, ...)`
- `initialize_cache(db_path=None)`
- `index_episode(podcast_id, episode_ref, force=False, db_path=None)`
- `rebuild_cache(podcast_id=None, force=False, db_path=None)`
- `search_transcripts(query, podcast_id=None, limit=20, db_path=None, search_mode="auto", context_segments=0, case_sensitive=False)`
- `search_mentions(query, podcast_id=None, mention_type=None, limit=20, db_path=None, case_sensitive=False)`

這些 functions 使用明確的輸入參數與資料模型，MCP layer 只做 thin wrapper，不複製核心邏輯。

## Phase 4A MCP Tools

- `list_episodes`：列出 podcast episodes，不回傳完整 audio URL，只回傳 `audio_url_present`。
- `get_episode`：查詢單集 metadata，支援 `latest` 與大小寫不敏感 episode ref。
- `validate_transcript`：檢查既有 transcript artifacts 狀態。
- `search_transcripts`：查 SQLite cache 中的 transcript segments，支援 search mode、highlight 與有限 context window。
- `search_mentions`：查 SQLite cache 中的 deterministic mentions 與 evidence。
- `rebuild_cache`：maintenance tool，只索引既有 artifacts，不下載、不轉錄、不摘要、不抽 mentions。

## Phase 4B Side-effect MCP Tools

- `download_audio`：預設只回 action plan；`confirm=true` 才下載音檔，且不回傳完整 audio URL。
- `transcribe_episode`：預設只回 action plan；`confirm=true` 才執行 long-running transcription，參數使用 model / device / compute type allow-list。
- `summarize_episode_extractive`：預設只回 action plan；`confirm=true` 才讀既有 transcript 並寫 extractive summary，不呼叫 LLM。
- `extract_mentions`：預設只回 action plan；`confirm=true` 才用 deterministic rules 寫 mentions artifacts，不呼叫 LLM。

Phase 4B 當時刻意不暴露 `semantic_summarize_episode`；Phase 4C 已在 API cost acknowledgement gate 下補上此 tool。

## Phase 4C Semantic Summary MCP Tool

- `semantic_summarize_episode`：預設只回 action plan；`confirm=true` 仍不足以執行，還必須提供 exact `api_cost_ack`。
- Required acknowledgement：

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

此 tool 可能呼叫外部 LLM API、將 transcript text 傳送到本機外並產生費用，因此 dry-run 不回傳逐字稿原文、不回傳 API key，也不接受任意本機路徑。成功後不會自動 rebuild cache；若要索引新的 semantic summary artifact，請手動執行 `rebuild_cache`。

Tool response 統一使用 JSON envelope：

```json
{"ok": true, "data": []}
```

```json
{"ok": false, "error_type": "SearchError", "message": "SQLite cache 不存在。請先執行 rebuild_cache maintenance tool。"}
```

Side-effect dry-run response：

```json
{"ok": true, "dry_run": true, "requires_confirmation": true, "tool": "transcribe_episode", "next_step": "Call this tool again with confirm=true to execute."}
```

## 016 Human-Controlled Completion Tool and Portable Skill

016 made the reviewed local stdio registry exact 13 tools at the time by adding
`run_corpus_episode_completion_workflow`; the existing twelve tool signatures and envelopes remain
unchanged. Its default is a strict-zero-file preview across intake, audio,
transcription, deterministic remediation, semantic summary, and semantic
review. A dry-run returns one selected action or a bounded blocked/completed
state, never a full-chain execution.

The repository portable `corpus-episode-completion` Skill is the human-control
layer for agents. It may only call this reviewed MCP tool: first
`action=next, confirm=false`, then explain the result and wait for an explicit
approval of the returned canonical episode and exact selected action. It must
not treat general approval as confirmation, invoke a CLI/terminal fallback,
retry, schedule work, or launch an automatic second action.

Confirmed requests reject `latest` and `next`, recompute state to reject drift,
and dispatch at most one matching Core runner. Confirmed semantic summary
requires the exact acknowledgement before profile, `.env`, or provider work;
semantic review has no LLM configuration. The tool writes a metadata-only
latest 016 report only after a valid confirmed action, and does not rebuild
index, plan, or SQLite cache automatically.

## 020 Read-Only Verified Report Catalog Tool

The current registry has exactly 25 reviewed tools. Tool 25, `derive_workflow_bundle`, is append-only after unchanged Tools 1–24; its preview is zero-write and zero-network, and confirm calls an LLM and needs the exact `api_cost_ack`. Tool 24, `ingest_youtube_video`, is the YouTube ingest tool. Tool 23, `ingest_x_video`, remains the X ingest tool. Preview is zero-write but reads public metadata over the network. Tool 22, `generate_stock_lens_report`, remains a dry-run-first side-effect stock lens (no LLM, no `api_cost_ack`, no network, no live market API, no investment advice). Tool 21, `list_verified_report_gap_backlog`, remains a read-query inventory gap backlog (no confirm/ack). Tool 20 remains historical next-step suggestion. Tool 19 remains coverage join. Tool 18 remains exact-locator offline revalidation. Tool 17 retains its offline manifest-first `list`, safe-metadata `search`, and exact-bundle `inspect` contract; inspect always reports `source_currentness_status=not_evaluated`.

## 對 MCP 友善的設計

- deterministic path：工具可用 `podcast_id` 與 `episode_ref` 找到對應檔案。
- 設定外部化：MCP server 不需要知道特定 podcast 的 RSS URL。
- CLI 無商業邏輯：MCP server 可直接呼叫核心，不需要透過 subprocess 呼叫 scripts。
- SQLite cache 是衍生資料：MCP tools 可呼叫 `rebuild_cache()` 重建，並透過 `search_transcripts()` / `search_mentions()` 查詢；原始 source of truth 仍是 data artifacts。
- 搜尋結果包含 deterministic highlight、timestamp evidence、實際 search mode 與有限 context window，方便未來 MCP tools 直接呈現。
- MCP tools 不接受任意本機路徑、不讀取任意檔案；只有 `semantic_summarize_episode` 在 exact acknowledgement 後才允許呼叫外部 LLM。
- Side-effect tools 預設不執行，必須 `confirm=true` 才會下載、轉錄或寫 artifacts。
- Side-effect tools 完成後不自動 rebuild cache；需要搜尋新 artifacts 時請手動呼叫 `rebuild_cache`。

## 目前限制

- Codex / Claude 類本機 client 使用 stdio；Hermes/OpenAB 只支援經核准的 host-network、loopback-only Streamable HTTP sidecar。沒有 bridge-network 變體、legacy SSE、port publication 或 automatic port fallback。
- Direct validator 驗證 exact 21-tool registry、one read-only、one `confirm=false` preview，並要求 protocol success＋application envelope `ok=true`。v2僅在具備descriptor-only no-follow primitives的POSIX runtime執行；native Windows在protected path access前fail closed。它以opaque in-memory content tokens比較三個surfaces，只輸出before/after metadata/content endpoint equality booleans，對missing/malformed、`.env`/`.env.*`、symlink/reparse、special entries fail closed；不宣稱snapshot間無transient mutation。兩位reviewers與唯一live v2 run均通過，C6為PASS-current且不得重跑。
- Hermes v0.19.0 safe CLI output 無法無歧義提供 one-call、actual confirm value、no-second-action、no-fallback 四項 structured evidence。v0.20.0 tag `v2026.8.3` hooks雖提供per-call tool name/arguments事件，但缺canonical fallback indicator且raw payload可能敏感；未有approved projection collector或runtime validation，因此C7仍是BLOCKED/FAIL。不得讀live config values/session dump、保存raw response、重跑inference、升級或啟用hooks。
- Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run.
- 尚未處理長時間任務的進度回報或取消機制。
- Semantic summary MCP tool 已暴露，但需要 exact API-cost acknowledgement；尚未實作 rate limit、成本估算或 provider-level quota。
- Phase 3B search 支援 optional SQLite FTS5，但中文搜尋仍保留 LIKE fallback；尚未做 embedding 或 vector search。

## 使用文件

Codex / Claude 本機 MCP client 設定範例請見：

- [mcp-usage.md](mcp-usage.md)
- [codex-mcp-setup.md](codex-mcp-setup.md)
- [claude-mcp-setup.md](claude-mcp-setup.md)
- [mcp-troubleshooting.md](mcp-troubleshooting.md)
- [Hermes sidecar deployment](../deploy/hermes/README.md)
- [Spec 026 quickstart](../specs/026-hermes-mcp-integration/quickstart.md)
- [Spec 027 offline Skill routing contracts](../specs/027-hermes-skill-routing-contracts/spec.md)
- [Spec 028 offline runtime-observation capability gate](../specs/028-hermes-runtime-skill-routing-observation/spec.md)

本機 setup validation：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

不要把包含個人絕對路徑的 `.codex/config.toml`、`.env` 或 API key commit 進專案。
