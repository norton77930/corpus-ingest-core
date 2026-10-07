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
[mcp_servers.corpus-ingest-core]
command = "python"
args = ["D:/path/to/corpus-ingest-core/scripts/run_mcp_server.py"]
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
- `suggest_learning_workflow_next_step` (Tool 27; offline read-query, no execution)
- `inspect_workflow_derivation_lineage` (Tool 28; offline lineage query, no execution)

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

### Workflow Derivation Tool

- `derive_workflow_bundle` (Tool 25)

Tool 25 appends after unchanged Tools 1–24. 它把 Spec 042 的 `05`/`06` derivation 接上 MCP,所以那個能力不再只能從終端機執行。`confirm=false` 是 **preview**:零寫入,而且**零網路** —— 它在建構 LLM provider 之前就返回,所以不需要 `api_cost_ack`,這一點與 Tools 23/24 不同。`confirm=true` 會呼叫外部 LLM 並產生費用,必須帶精確的 `api_cost_ack`;該門檻由 Core 的 `require_exact_api_cost_ack` 把關,這個工具只負責原樣轉交。確認重用既有的完整 `05`/`06` 配對時不會呼叫 provider,因此也不需要 ack。

工具**不接受** `provider`、`model`、`base_url`、`api_key_env`、`reasoning_effort`、`read_timeout_seconds` 或 `workflow_context`。前六個是操作者環境的憑證與端點;最後一個指向一個**內容會被送進 LLM prompt 的檔案**,交給 agent 指定等於開一條讀取任意檔案的路。工作流程情境一律讀 `config/operator_workflow.yaml`。

```powershell
python scripts/run_workflow_derivation.py --podcast <id> --episode <ref>
```

### Study-guide Tool

- `generate_study_guide_bundle` (Tool 26)

Tool 26 appends after unchanged Tools 1–25. 它把既有 learning-notes summary 的講義接到 MCP，不是從影片一次產生講義、衍生與摘要。`confirm=false` 是 **preview**：零寫入、零網路，也不建構 provider。它會列出 reads、講義寫入、reuses，以及確認後會寫的兩份 run report。只有計畫會重生 `03`/`04`/`07` 時，preview 才標示需要 LLM。`confirm=true` 只呼叫一次講義 Core。生成需要精確的 `api_cost_ack`；完整重用與只補封面不需要，也不呼叫 LLM。目錄裡已有 `05` 或 `06` 時，重生講義（含 `force`）會拒絕，而且不寫檔、不建 provider。補封面與允許的生成會保留講義以外的位元組。衍生要另外再要求 `derive_workflow_bundle`。

```powershell
python scripts/run_study_guide_bundle.py --podcast <id> --episode <ref>
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


## SPEC 045: Learning workflow Skills

Use `study-guide-bundle` for a named episode with an existing learning-notes semantic summary; use `workflow-derivation-bundle` for an existing lecture and the configured default operator-workflow context. These are independent requests: preview, explain, wait for explicit approval, confirm once, report and stop. Neither Skill fills missing sources or starts the other operation automatically. Existing tool registry and Core behavior are unchanged.

Generation requires the user's exact API-cost acknowledgement after preview. Lecture reuse/cover-only and complete derivation-pair reuse pass an empty acknowledgement, even if one exists in conversation history. Every successful confirm writes run reports, including reuse. A preview is not a digest pin; state is recomputed on confirm, and a no-cost plan that becomes generation must stop on refusal without retry.

SPEC 046: Tool 25 refuses pre-existing recovery entries and unsafe local paths before preview/reuse/generation; force never overrides refusal. It preserves all regular non-pair file bytes and maps MCP failures to fixed safe messages. Distinct errors identify rollback failure, published cleanup/report failure and reused report failure. Only this attempt owns its rollback/cleanup; no automatic recovery of old entries or agent retry. Writers must be serialized; publication is not crash-durable, race-proof or one artifact/report transaction.

Validation is offline: static instruction contracts, actual-backend characterization and synthetic conversation oracles. These do not prove live agent compliance. No CLI/terminal/filesystem fallback, automatic cache rebuild, installation or deployment is performed.


### Learning workflow next-step query (Tool 27)

`suggest_learning_workflow_next_step(podcast_id, episode_ref)` is an offline read-query with two required explicit identifiers. It accepts no confirm, force, api_cost_ack, file path, context or provider options. Tools 1-26 retain their order and contracts.

The query evaluates the existing lecture preview first. It suggests `generate_lecture` or `complete_cover` and stops when lecture work remains. Only a reusable lecture permits the derivation preview, which can suggest `generate_derivation` or report `complete`. Expected prerequisite errors become `blocked` with the failing stage; detailed missing-source/context diagnoses are not guessed from error text. Unsafe/recovery/conflict states retain fixed reason codes. All results contain metadata only, with no raw source/context text, paths or exception messages.

An available action includes `suggested_call` arguments with `confirm=false` and `force=false`, plus `requires_llm` and `requires_api_cost_ack` for a later confirmed operation. Generation requires both; cover completion requires neither. Complete/blocked have null action/cost fields. The query itself writes no reports, constructs no provider, contacts no network and never rebuilds cache or dispatches the suggested tool.

`complete` means both existing previews reported reusable. It does not validate 05/06 content quality or source freshness (`source_currentness=not_evaluated`); empty/stale pair files can meet the existing presence-based reuse contract. Context errors can block despite both files existing. Sequential previews are not an atomic snapshot. Start the selected existing Skill/operation with its own preview and explicit approval; the query grants no execution permission and does not chain lecture and derivation.

Example query arguments (no execution): `{"podcast_id":"x-raytar","episode_ref":"2071290493581840707"}`. No new CLI or execution Skill was added.

### Workflow derivation lineage (Tool 28)

`inspect_workflow_derivation_lineage(podcast_id, episode_ref)` is an offline read query with exactly two required explicit identifiers. It accepts no caller path, force, confirm or acknowledgement. Results under `data` include status, fixed reason, ordered changed_roles, scope=workflow_derivation_inputs_outputs, read_only=true and network_access=false. Outcomes: current, stale, untracked, not_generated, not_evaluated/custom_context, blocked. No bodies, digests, paths or arbitrary exception text are returned. It never generates, repairs or rebuilds caches.

Tool25 adds `metadata_writes` separately from its unchanged two-output writes/reuses. Generation previews list workflow_derivation.lineage.json; reuse lists none and leaves existing records unchanged. Actual generation publishes05/06 plus this owned record in one directory swap, with hashes of consumed lecture03/04/07, effective configured tools, rendered request and staged output bytes. Generation refuses unrecognized reserved-name collisions before provider construction. Existing report-failure/recovery distinctions remain. Updated workflow-derivation-bundle Skill requires/discloses metadata_writes; older previews lacking it are incompatible.

Legacy pairs are untracked; a recorded custom context is not_evaluated by the default-only query. Current means equality to recorded derivation inputs/outputs observed now, not lecture-to-transcript freshness or semantic quality. No automatic backfill/regeneration and no atomic observation claim. See specs/048-workflow-derivation-lineage/contracts/lineage.md.

### Study-guide lineage (Tool 29)

`inspect_study_guide_lineage` requires explicit podcast_id and episode_ref; no confirm/force/ack. Existing ok/data envelope returns status=current/stale/untracked/not_generated/blocked, fixed reason, ordered changed_roles, scope=study_guide_inputs_outputs, read_only=true, network_access=false, warnings=[study_guide_scope_only,non_atomic_observation]. No source bodies, paths, hashes or arbitrary exception text in query. Legacy03/04/07 is untracked; partial outputs/orphan receipt blocked. Current compares full consumed semantic summary, recipe/request and actual output bytes;00 is excluded. Generation publishes one strict bounded receipt with the lecture; Tool26 preview separates metadata_writes from writes/reuses/report_writes. Unsafe/recovery state refuses inspection or generation. No backfill, repair, enforcement or authenticity proof.

Tool29 `inspect_study_guide_lineage(podcast_id, episode_ref)` adds an offline read-only comparison of lecture03/04/07 against its recorded semantic summary. Tool26 generation declares separate `metadata_writes` for `study_guide.lineage.json`; ship with the updated study-guide Skill. Cover-only/reuse preserve provenance or legacy absence. No summary-to-transcript freshness claim; Tool27/28 behavior stays unchanged. See SPEC049.

### Learning-bundle recovery (Tool 30)

`inspect_learning_bundle_recovery` accepts `podcast_id` and `episode_ref` as two required explicit identity strings. It inspects only the public bundle plus `.part`, `.old`, `.wfderive.part` and `.wfderive.old`, offline and read-only. Roles00/03/04/07 and05/06 are absent, partial or complete. Both owned lineage records are checked against the original public identity and local output bytes. Ordinary extra files are counted without opening or exposing their names.

The response is the existing `{"ok": true, "data": ...}` envelope. Data includes `status`, `reason`, `manual_review_required`, five `locations`, `scope="learning_bundle_recovery"`, `read_only=true`, `network_access=false`, and fixed diagnostic warnings. States: `clear` (no observed recovery/anomaly), `recovery_present` (safe recovery directory exists), or `blocked` (identity, unsafe/unavailable inspection, partial groups or receipt/output anomalies). Unknown inspection is never absence. Record `valid`/output `match` checks recorded output consistency only; it does not establish source freshness, authenticity, publication outcome or a latest winner. Missing legacy records remain absent, without backfill.

No confirm/force/ack/provider/path inputs, writes, network, generation, cleanup, repair commands or automatic cache rebuild. Failed/ambiguous publication requires human review. Tools1-29 and existing Skills retain their behavior. Directory entries are capped at256; records64KiB and output files64MiB. See [SPEC050](../specs/050-learning-bundle-recovery/spec.md) and [the closed response contract](../specs/050-learning-bundle-recovery/data-model.md). Restart an already running MCP server to expose Tool30.

### Learning workflow status overview (Tool 31)

`inspect_learning_workflow_status` takes two required explicit identity strings: `podcast_id` and `episode_ref`. It provides one offline, read-only overview of next-step progress (Tool27), study-guide lineage (Tool29), workflow derivation lineage (Tool28), and recovery (Tool30). Recovery is evaluated first; any blocked or recovery-present result skips all three other queries as `not_evaluated/recovery_gate`. Otherwise each public Core query runs once, sequentially.

The existing `{"ok": true, "data": ...}` envelope contains compact `recovery`, `next_step`, `study_guide_lineage`, and `workflow_derivation_lineage` observations, `status`, `attention_required`, and ordered `attention_reasons`. Top `observed` means no diagnostic attention signal; it is not end-to-end readiness or a publication/freshness guarantee. `attention_required` distinguishes stale/untracked/custom-context provenance and conflicting observations; `blocked` indicates a refused or unavailable observation. A next-step `complete` can coexist with stale lineage and attention: completion retains existing preview reuse semantics. Pending `not_generated` alone is ordinary unfinished work.

No child paths, bodies, fingerprints, arbitrary warnings or `suggested_call` are forwarded. No execution authorization, confirm/force/ack/provider/path/context inputs, writes, network/provider/environment/report/cache calls, retry, repair, cleanup or generation chain. Existing Tools1-30 and Skills retain their contracts; use Tool27 for separate preview guidance and Tool30 for detailed recovery. Fixed warnings include non-atomic observation, unevaluated summary-to-transcript freshness, no execution authorization and unproven publication outcome. Unexpected child failure becomes a finite blocked section; independent clear-gated diagnostics still run.

See [SPEC051](../specs/051-learning-workflow-status/spec.md), [response model](../specs/051-learning-workflow-status/data-model.md) and [query contract](../specs/051-learning-workflow-status/contracts/status.md). Restart an existing MCP process manually to expose Tool31.

### Single learning workflow action (Tool 32)

`advance_learning_workflow` accepts required explicit `podcast_id`/`episode_ref`, default `confirm=false`, and optional `expected_action`, `expected_plan_id`, `api_cost_ack`. Preview uses Tool31 Core observations and one selected runner preview, then returns `{"ok":true,"dry_run":true,"data":...}` with action, cost requirements, fixed read-role descriptions, artifact writes/reuses, lineage metadata writes, report writes and metadata-only `plan_id`. Unknown/recovery/stale/untracked/custom/conflicting observations block with no execution. Both current bundles return scoped `complete`, not source-freshness proof.

After explicit approval, confirm returns the preview action/id as `expected_action`/`expected_plan_id`; generation requires the existing exact cost acknowledgement. It recomputes the current plan; detected action/cost/path-plan drift stops before dispatch. Cover always passes empty ack, including when caller supplies an acknowledgement. Execute exactly one existing Core runner with `force=false`, default context/provider, then report and stop. No chained action, post-execution query, retry, repair, duplicate report or automatic cache rebuild. Successful execution returns owned outputs/child report paths and `follow_up=preview_again`; it does not claim the next action was inspected.

Plan identity binds metadata only, not file content or persistent approval. Observations are non-atomic; callers serialize writers. Existing child publication/rollback/cleanup/report failures retain safe phase messages. Unexpected errors or results after dispatch warn local files may have changed; no retry/rollback guarantee. No force/provider/path/context input. Acknowledgement, raw content, arbitrary child warnings and exceptions are not returned. Tools1-31 retain exact signatures/order. See [SPEC052](../specs/052-learning-workflow-advance/spec.md) and [the contract](../specs/052-learning-workflow-advance/contracts/advance.md). Restart an existing MCP server manually to expose Tool32; no deployment is performed.

Tool32 may qualify only a missing00 cover through detailedTool30 and existing next-step/lineage queries. All recovery locations must be absent;lecture03/04/07 and any05/06 must have valid matching/current records. Other partial/legacy/stale/custom/unsafe/unknown states stop. No prior tool contract changes or recovery repairs.


## SPEC 053: Unified learning entry Skill

Use `learning-workflow-advance` when asking for the next learning step of one explicit podcast/episode. It binds only Tool32 `advance_learning_workflow`: one zero-write/offline preview, disclose artifact/reuse/lineage/report plans and costs, wait for fresh cycle approval and exact cost text for generation, confirm once, report and stop. Cover sends empty acknowledgement; complete/blocked states never confirm. Returned action/plan_id are approval bindings, not content snapshots or locks. Missing tools, drift, malformed replies and failures stop without fallback, retries or automatic next action/cache rebuild.

Example: request one learning step for a named podcast and episode; review the returned action/files/cost, then approve this cycle. Existing explicitly selected study-guide/derivation Skills remain independent. No full-chain/batch/repair/force operation is added. Portable Skill and response reference must be loaded by the agent host manually when needed; no installation or live client compliance guarantee. Evidence is offline instruction contracts, labelled dialogue oracles, temporary fake-provider backend checks and read-only synthetic pressure/review.


### Source preparation jobs (Tools 33/34)

Tool33 `prepare_learning_source`; Tool34 `inspect_source_preparation_job`.

`prepare_learning_source(url, confirm=False, expected_plan_id="")` previews one
configured YouTube/X video. Preview may fetch public metadata, but creates no
job and downloads nothing. Review source identity, stage/file/reuse plans and
local compute/storage costs; fresh approval then binds the exact plan_id.
Confirmation returns a job_id promptly; acceptance is not transcript completion.

`inspect_source_preparation_job(job_id)` reads recorded metadata offline. It
never polls a source, repairs, retries, frees stale slots or rebuilds cache.
Stages: queued, downloading, transcribing, validating; completion requires
validated canonical transcripts. No LLM, Q&A, summary or learning documents are
generated. Finance profiles can prepare transcripts but show incompatibility
with downstream lecture generation. Partial artifacts and uncertain outcomes
require operator inspection; force is false, history is preserved.

Windows stdio submissions are blocked with worker_host_incompatible: nested
process jobs cannot provide the required connection-independent lifetime.
Use an already independently managed loopback HTTP MCP host; no host policy is
changed and this feature does not deploy one. Existing ready transcripts and
read-only progress remain available. Other hosts must permit independent child
workers; offline SDK tests do not certify a specific Hermes mounting.

Portable [source-preparation Skill](../.agents/skills/source-preparation/SKILL.md)
obtains approval, submits once, reports and stops. A later explicit request
queries one known job once. Cache rebuilding stays manual.

SPEC055 adds optional source-profile transcription settings to these existing
tools; the registry now has 35 tools and request parameters are unchanged.
Operator YAML (local profile, not a tool argument):

```yaml
preparation_transcription:
  model: medium
  device: cuda
  compute_type: float16
```

Omission retains tiny/cpu/int8 with VAD enabled. An explicit mapping requires
all three fields. Models: tiny, tiny.en, base, base.en, small, small.en, medium,
medium.en, large-v3, turbo; .en requires an English source. CPU accepts
int8/float32, CUDA accepts int8/float16/float32. No arbitrary model paths,
repositories or silent fallback. Preview observes configured CUDA capability
without loading/downloading a model or guaranteeing VRAM. Confirmed work may
download public model files to the runtime cache and consume local resources.

`transcription` shows configured/approved settings; `actual_transcription`
shows complete supported metadata recorded in a validated transcript. Unknown
historical metadata is null. Existing transcripts stay ready without automatic
regeneration, even when current settings differ. New job completion requires
matching actual metadata. Settings changes invalidate approval. Historical job
inspection preserves original records; SQLite schema remains unchanged.

Copy the updated source-preparation Skill and its response-contract reference
together when porting. SDK fixtures verify local transport/worker behavior;
live Hermes mounting and transcript accuracy remain separate operator checks.
See [SPEC055 quickstart](../specs/055-source-preparation-transcription-settings/quickstart.md).

### Prepared source content query (Tool 35)

Tool35 `query_source_content` supports inspect, read and literal search.

`query_source_content(podcast_id, episode_ref, action="inspect", expected_source_version="", query="", start_seconds=None, end_seconds=None, cursor="", limit=40, max_chars=8000)` reads one already prepared RSS/YouTube/X transcript without SQLite. Inspect returns metadata/version only; read returns timed text; search is literal case-insensitive keyword matching. Read/search require the inspected version. Follow next_cursor with unchanged scope; coverage/chunk offsets distinguish complete delivery from truncation or final-page-only evidence. Changed/unsafe/ambiguous/partial/empty sources fail closed. No network, provider, writes, preparation or automatic cache rebuild. Returned evidence may be processed/billed by Hermes host model. Chat notes do not publish formal lectures; existing generation confirmation/api_cost_ack remain. This is not universal video-platform support.

Use the portable [source-content-qa Skill](../.agents/skills/source-content-qa/SKILL.md) for timed answers and complete/partial learning notes. See [SPEC056 quickstart](../specs/056-source-content-query/quickstart.md). Synthetic/SDK acceptance is distinct from real Hermes mounting.


## SPEC057 source learning entry

Load source-learning-entry for one URL plus a source question/learning-note request, or known prepared podcast_id/episode_ref. It coordinates existing prepare_learning_source, inspect_source_preparation_job and query_source_content from the same mounted server; no new MCP tool, registry remains 35 tools. URL preview can read public metadata; ready hands exact IDs to fresh QA inspect. Missing transcripts require disclosed model/effects and fresh approval; submit once and stop. A later progress question stops after one status call; explicit continue-learning validates the retained job/source before QA. Busy may be another source; do not attach its job. Context lasts in the conversation, not a durable queue.

Example: paste one YouTube/X URL and ask for source reasoning/examples and replay passages; after submission ask whether processing is ready, then explicitly continue notes. The entry requires source-preparation response references and source-content-qa plus its single editable note template. Standalone preparation/QA routes keep their boundaries. Windows stdio new submissions still block with worker_host_incompatible; use only an already independently managed compatible HTTP host for preparation. See [operator acceptance](../specs/057-source-learning-entry-skill/quickstart.md). Actual Hermes acceptance remains pending; SDK/synthetic results are separate.
