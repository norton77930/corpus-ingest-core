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

請把 `D:/path/to/corpus-ingest-core` 換成你的 repo 實際路徑。不要在設定中放 API key。

```json
{
  "mcpServers": {
    "corpus-ingest-core": {
      "command": "python",
      "args": [
        "D:/path/to/corpus-ingest-core/scripts/run_mcp_server.py"
      ],
      "cwd": "D:/path/to/corpus-ingest-core"
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

The local reviewed registry has exactly 35 tools. Tool 27, `suggest_learning_workflow_next_step`, is an offline read-query for one explicit episode: one lecture/derivation preview suggestion, reusable completion, or a blocker; no execution, source-freshness or content-quality claim. Tool 26, `generate_study_guide_bundle`, is append-only after unchanged Tools 1–25; preview is zero-write and zero-network, and confirm delegates once to the lecture runner (generation needs the exact `api_cost_ack`; reuse and cover-only do not; existing 05/06 block regeneration). Tool 25, `derive_workflow_bundle`, is append-only after unchanged Tools 1–24; its preview is zero-write and zero-network, and confirm calls an LLM and needs the exact `api_cost_ack`. Tool 24, `ingest_youtube_video`, is the YouTube ingest tool. Tool 23, `ingest_x_video`, remains the X ingest tool. Preview is zero-write but reads public metadata over the network. Tool 22, `generate_stock_lens_report`, remains a dry-run-first side-effect stock lens (no LLM, no `api_cost_ack`, no network, no live market API, no investment advice). Tool 21 is append-only: Tools 1–20 keep their contracts/order. It is an offline read-only inventory gap backlog (`podcast_id`, optional `limit`); no `confirm` or acknowledgement. Tool 20 remains historical next-step suggestion. Tool 19 remains coverage join. Tool 18 remains exact-locator source revalidation. Tool 17 retains its offline read-only manifest-first list/search/inspect contract, including `source_currentness_status=not_evaluated` for inspect.

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


Tool28 `inspect_workflow_derivation_lineage` appends an offline explicit-episode lineage query. Tool25 now declares separate metadata_writes for its owned generation receipt; ship with the updated derivation Skill. Tool27 still reports presence/reuse only. Legacy untracked/custom not_evaluated results do not authorize regeneration. See SPEC048 contract.

Tool29 `inspect_study_guide_lineage(podcast_id, episode_ref)` adds an offline read-only comparison of lecture03/04/07 against its recorded semantic summary. Tool26 generation declares separate `metadata_writes` for `study_guide.lineage.json`; ship with the updated study-guide Skill. Cover-only/reuse preserve provenance or legacy absence. No summary-to-transcript freshness claim; Tool27/28 behavior stays unchanged. See SPEC049.

Tool30 `inspect_learning_bundle_recovery(podcast_id, episode_ref)` provides offline, read-only recovery diagnosis for five fixed bundle locations and both lineage records. Recovery entries and uncertain publication require manual review; no cleanup, repair, latest-winner or source-freshness claim. Tools1-29 and Skills retain their behavior. See SPEC050 and docs/api.md.

Tool31 `inspect_learning_workflow_status(podcast_id, episode_ref)` provides a single offline read-only overview of Tools27-30:progress, both lineage scopes and recovery. Recovery gates further diagnostics; legacy/custom/stale observations retain distinct attention reasons. No executable suggested_call, action authorization or end-to-end freshness claim. Existing30 tool contracts/Skills remain unchanged. See SPEC051 and docs/api.md.

Tool32 `advance_learning_workflow` previews and confirms one explicit-episode learning action with metadata action/plan binding; no automatic chain or repair. See docs/api.md and SPEC052. Existing Tools1-31 retain their contracts.


SPEC054 adds Tool33 `prepare_learning_source` and Tool34 `inspect_source_preparation_job`. For Windows background preparation, use an already independently managed loopback HTTP MCP host; stdio new submissions report `worker_host_incompatible`. See [source preparation](api.md#source-preparation-jobs-tools-3334). No host policy, service deployment or Skill installation is performed automatically.

SPEC056 adds read-only Tool35 `query_source_content` and source-content-qa Skill for prepared RSS/YouTube/X timed evidence/notes. No cache prerequisite, preparation, repository provider or publication. Host model privacy/billing applies. See [Tool35](api.md#prepared-source-content-query-tool-35); actual Hermes acceptance is separate.
