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
- `query_verified_research_report_catalog`
- `revalidate_verified_research_report_sources`
- `query_verified_research_report_coverage`
- `suggest_historical_verified_report_next_step`
- `list_verified_report_gap_backlog`

`rebuild_cache` 是 maintenance tool，只索引既有 artifacts，不會下載音檔、轉錄、摘要或抽 mentions。Search tools 不會自動 rebuild cache；如果 cache 不存在，請先執行 `rebuild_cache`。`query_verified_research_report_catalog` 是 Tool 17 appended-only 的 read-query tool，不是 side-effect：不需要 `confirm` 或 acknowledgement，且不會寫入、匯出、重建 cache 或重新發布報告。`revalidate_verified_research_report_sources` 是 Tool 18 appended-only 的 exact-locator read-query：Tools 1–17 unchanged，不需要 `confirm` 或 acknowledgement，只接受 `podcast_id`、`episode_ref` 與 lowercase 64-hex `source_digest`；不接受 path/output/latest/limit/query/provider/network，離線、零寫入且不提供投資建議。`query_verified_research_report_coverage` 是 Tool 19 appended-only episode-centric coverage read-query：Tools 1–18 unchanged，不需 `confirm`/ack，以 exact `podcast_id` 回傳 inventory×bundle 覆蓋（可選 `has_bundle`、`limit`），不讀 report body、不寫入。`suggest_historical_verified_report_next_step` 是 Tool 20 appended-only read-query：Tools 1–19 unchanged，以 exact `podcast_id`+`episode_ref` 回傳 historical 下一動建議（zero-write preview composition）。

### Confirmed Local Side-Effect Tools

- `download_audio`
- `transcribe_episode`
- `summarize_episode_extractive`
- `extract_mentions`
- `generate_stock_lens_report`

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

### Latest Episode Deterministic Processing Tool

- `run_corpus_latest_episode_deterministic_workflow`

017 tool 預設 `confirm=false`，只解析一次當前 latest 並回傳 zero-file 計畫。SPEC 017 is Implemented. The 2026-07-17 `seeded`/`downloaded` mapping issue is a resolved historical blocker; recorded metadata-only confirmed EP679 evidence ends at `ready_for_semantic_summary`. An explicit natural-language request for one configured podcast's latest episode authorizes the portable `corpus-latest-episode-processing` Skill to acknowledge once, call this dedicated MCP workflow exactly once with `confirm=true`, report once, and stop. It must not make a `confirm=false` preview-before-confirm call, retry, use a fallback/terminal/CLI, invoke semantic summary/review, rebuild cache, batch, schedule, or make a second call. The Core pins the same canonical episode, processes only intake, download, local transcription, and deterministic remediation, then stops at `ready_for_semantic_summary` without `.env` or LLM/provider access.

### Latest Episode Verified Research Report Tool

- `run_latest_episode_verified_research_report_workflow`

018 tool follows a mandatory preview → explicit episode-scoped approval → one confirmed call protocol. First call with `confirm=false`; it resolves latest once and returns a strict-zero-file plan, canonical `episode_ref`, risk summary, and required exact `api_cost_ack`. Do not treat preview as approval. After the user supplies the same `expected_episode_ref` and the exact acknowledgement text, call once with `confirm=true`. Invalid acknowledgement or a changed canonical reference is rejected before RSS, environment/provider access, writers, or child stages. Confirmed execution uses the pinned deterministic ladder, permits semantic work only through a passed review gate, and publishes a deterministic, digest-versioned JSON/Markdown/manifest bundle atomically. It neither retries, schedules, rebuilds cache, uses a live external provider, nor provides investment advice.

Use the portable `latest-episode-verified-research-report` Skill for this human-controlled protocol. It must not substitute CLI, terminal, retry, scheduler, fallback, or another side-effect tool.

### Explicit Episode Verified Research Report Tool

- `run_episode_verified_research_report_workflow`

019 tool is for a **named** `episode_ref` (including historical episodes), not latest-only. Preview with `confirm=false` and an explicit episode reference; it returns readiness (`ready`/`blocked`) and missing/stale roles with zero writes. Confirm with the same exact `episode_ref` only when local artifacts and lineage already pass: it assembles and atomically publishes (or reuses) an 018-equivalent digest bundle. It does **not** require `api_cost_ack`, does not call LLM providers, does not download/transcribe, and does not chain 015–017. Reserved selectors `latest`/`next` are rejected. Use the portable `episode-verified-research-report` Skill: preview → explicit approval of `episode_ref` → one confirmed MCP call → stop.

### Verified Research Report Catalog Query Tool

- `query_verified_research_report_catalog` (Tool 17)

Tool 17 is append-only: reviewed Tools 1–16 keep their contracts and order. It is an offline read-only manifest-first query, not a side-effect tool, so it has no `confirm` or acknowledgement parameter. Use `action=list` with optional exact `podcast_id` / `episode_ref`, `action=search` with a nonblank safe-metadata query, or `action=inspect` with exact `podcast_id`, `episode_ref`, and lowercase 64-hex `source_digest`.

It reads only canonical local report-bundle metadata. It provides no body search, raw manifest, source or absolute paths, export/copy/zip/republish, DB/FTS/vector/cache, RSS/HTTP/network, LLM, `.env`, download, transcription, remediation, or latest/currentness claim. Inspect verifies local bundle self-consistency only and always returns `source_currentness_status=not_evaluated`. Boundary shorthand: no raw manifest; no DB/FTS/vector/cache; no RSS/HTTP/LLM/.env/download/transcription/remediation; no latest selector.

The equivalent thin CLI is `scripts/query_verified_research_report_catalog.py`:

```powershell
python scripts/query_verified_research_report_catalog.py list --podcast-id gooaye --limit 50
python scripts/query_verified_research_report_catalog.py search "EP672" --podcast-id gooaye
python scripts/query_verified_research_report_catalog.py inspect gooaye EP672 <lowercase-64-hex-source-digest>
```

### Verified Research Report Source Revalidation Tool

- `revalidate_verified_research_report_sources` (Tool 18)

Tool 18 appends after unchanged Tools 1–17. It is a read-query with no `confirm` or acknowledgement and accepts exactly `podcast_id`, `episode_ref`, and lowercase 64-hex `source_digest`. It revalidates one local bundle offline without writes; it has no path/output/latest/limit/query/provider/network input and returns no raw manifest, source path, or body.

The equivalent thin CLI accepts the same three positional locators only:

```powershell
python scripts/revalidate_verified_research_report_sources.py gooaye EP672 <lowercase-64-hex-source-digest>
```

### Verified Research Report Coverage Tool

- `query_verified_research_report_coverage` (Tool 19)

Tool 19 appends after unchanged Tools 1–18. It is a read-query with no `confirm` or acknowledgement. Inputs: exact `podcast_id`, optional `has_bundle`, optional `limit` (default 50, max 100). It joins local episode inventory with 020-safe bundle summaries, returns bounded coverage rows and summary counts, and never reads report bodies or writes files.

```powershell
python scripts/query_verified_research_report_coverage.py gooaye
python scripts/query_verified_research_report_coverage.py gooaye --has-bundle false --limit 20
```

### Historical Verified Report Next-Step Tool

- `suggest_historical_verified_report_next_step` (Tool 20)

Tool 20 appends after unchanged Tools 1–19. It is a read-query with no `confirm` or acknowledgement. Inputs: exact `podcast_id` and exact `episode_ref` (never `latest`/`next`). It returns a bounded suggestion (`report_present` / `publish_verified_report` / `completion_action` / `blocked`) without writes.

```powershell
python scripts/suggest_historical_verified_report_next_step.py gooaye EP672
```

### Verified Report Gap Backlog Tool

- `list_verified_report_gap_backlog` (Tool 21)

Tool 21 appends after unchanged Tools 1–20. Read-query only (`podcast_id`, optional `limit`). Lists inventory episodes missing a verified report bundle (022 `has_bundle=false` projection). Zero-write; does not call 023 suggest.

```powershell
python scripts/list_verified_report_gap_backlog.py gooaye --limit 20
```

### Stock Lens Tool

- `generate_stock_lens_report` (Tool 22)

Tool 22 appends after unchanged Tools 1–21. It completes Spec 001 User Story 3 over MCP: the deterministic stock lens already existed in Core and the CLI, but no tool exposed it. Side-effect and dry-run-first — `confirm=false` returns the action plan only. It reads local industry-mapping and external-data-boundary artifacts and writes one report under `data/stock-lens/{podcast_id}/`; it makes no live market API call, no network request and no LLM call. Direct podcast evidence and inferred industry leads stay separated, inferred leads keep `needs_verification`, and the report never gives buy/sell/hold advice, a target price, or a guaranteed return.

```powershell
python scripts/generate_stock_lens_report.py gooaye 台積電
```

### X Video Ingest Tool

- `ingest_x_video` (Tool 23)

Tool 23 appends after unchanged Tools 1–22. It exposes the existing Spec 036 X video ingest seam. `confirm=false` is a **preview**: zero-write, but it resolves public metadata over the network so the plan can be real. That is not the corpus runner zero-network dry-run. `confirm=true` downloads with a guest token, extracts audio, transcribes locally, and writes a metadata-only run report. No cookies, no credentials, no LLM, no `work_dir` on the tool, and no automatic cache rebuild.

```powershell
python scripts/run_x_video_ingest.py --url "https://x.com/<handle>/status/<id>"
```

### YouTube Video Ingest Tool

- `ingest_youtube_video` (Tool 24)

Tool 24 appends after unchanged Tools 1–23. It exposes the existing Spec 039 YouTube ingest seam. `confirm=false` is a **preview**: zero-write, but it resolves public metadata over the network. That is not the corpus runner zero-network dry-run. `confirm=true` downloads with a guest token, extracts audio, transcribes locally, and writes a metadata-only run report. No cookies, no credentials, no LLM, no `work_dir` on the tool, and no automatic cache rebuild.

```powershell
python scripts/run_youtube_video_ingest.py --url "https://www.youtube.com/watch?v=<id>"
```

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
