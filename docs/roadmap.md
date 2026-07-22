# Roadmap

## Phase 0：骨架與契約

建立設定檔、資料模型、路徑規則、stub interface、薄 CLI 與繁體中文文件。

## Phase 1A：RSS Feed Reader

從 RSS 取得 episode 清單，支援 `latest` 與大小寫不敏感 episode lookup，並從 podcast profile 產生穩定 episode ref。

## Phase 1B：音檔下載

根據 `podcast_id` 與 `episode_ref` 下載音檔到 `data/audio/`，使用 deterministic path、streaming download 與 `.part` 暫存檔。

## Phase 1C：本機轉錄

使用 faster-whisper 讀取本機音檔並輸出 TXT、SRT、JSON。預設使用 `tiny`、`cpu`、`int8`，並支援 `force` 與短音檔 smoke test。

## Phase 1D：Deterministic 摘要

從既有 transcript 產生 Markdown summary。此階段不使用外部 LLM API，只輸出可追溯到 transcript segments 與 metadata 的 extractive template。

## Phase 1E：Transcript Validation 與長音檔可靠性

新增 transcript sanity check、validation CLI、轉錄 metadata、progress `.part` artifact 與 summary 前 validation gate。此階段不實作 model-level resume，只確保使用者能清楚辨識完整、空白、部分完成、缺失或損壞的 transcript。

## Phase 2A：LLM Semantic Summary

新增 provider-agnostic semantic summary pipeline，先支援 OpenAI-compatible API。語意摘要會先驗證 transcript，再依時間與 segment 數分 chunk 呼叫 provider，輸出 `.semantic.md`。所有輸出仍需保留來源 transcript 與時間戳引用，且不得產生投資建議。

## Phase 2B：Deterministic Mention Extraction

新增不依賴 LLM 的 deterministic mention extraction pipeline，從 transcript segments 擷取公司、ticker、產業、總經主題、crypto 與地點等 mentions，輸出 JSON 與 Markdown，並保留 timestamp evidence。此階段不做完整 NER、不做 SQLite、不做全文搜尋，也不產生投資建議。

## Phase 2C：LLM-assisted Entity Extraction

在 deterministic mention artifact 穩定後，再評估是否加入 LLM-assisted entity extraction。LLM 版本仍必須保留 timestamp evidence，並清楚區分逐字稿事實、模型推測與需要人工確認的內容。

## Phase 3A：SQLite Metadata Cache / Basic Search

新增可刪除重建的 SQLite metadata cache，索引 transcript segments、summary paths、mentions 與 mention evidence。搜尋先使用 basic SQL `LIKE`，不做 FTS5、embedding、vector DB 或 LLM search。

## Phase 3B：FTS / Advanced Search

在 basic search 穩定後，加入 optional SQLite FTS5、LIKE fallback、highlight、context window 與 case sensitivity。中文 exact query 預設保留 LIKE fallback，避免 FTS tokenizer 對中文不穩；此階段仍不做 embedding、vector DB 或 LLM search。

## Phase 4A：MCP Server Skeleton

新增 stdio-only FastMCP server skeleton，只暴露安全 read/query tools 與 `rebuild_cache` maintenance tool。MCP layer 只包裝既有 core functions，不複製商業邏輯，也不暴露下載、轉錄、摘要、semantic summary 或 mention extraction。

## Phase 4B：Side-effect Tools / Confirmation Design

新增 side-effect MCP tools：`download_audio`、`transcribe_episode`、`summarize_episode_extractive`、`extract_mentions`。所有工具預設 dry-run，必須 `confirm=true` 才會下載、轉錄或寫 artifacts。Side-effect tools 完成後不自動 rebuild cache。

## Phase 4C：Semantic Summary MCP / API-cost Guard

新增 `semantic_summarize_episode` MCP tool。此工具預設 dry-run，必須 `confirm=true` 並提供 exact API-cost acknowledgement 才會呼叫外部 LLM provider。Dry-run 不回傳逐字稿原文或 API key；成功後不自動 rebuild cache。Rate limit、成本估算與更細的 provider quota 留到後續階段。

## Phase 5A：MCP Client Integration Docs / Setup Validation

補齊 Codex / Claude 類 MCP client setup 文件、troubleshooting 文件與 `validate_mcp_setup.py`，讓使用者能在不啟動外部 client、不呼叫 LLM 的情況下驗證本機 MCP readiness。此階段不新增 MCP tools，也不改 core pipeline。

## Phase 5B：MCP Tool-use Eval Prompt Suite

新增 MCP tool-use eval prompt suite、pass/fail rubric 與 report template，用於實測 Codex 是否正確選用 `podcast-ingest-core` MCP tools。此階段只建立實測流程與文件，不新增工具、不改 MCP server 行為，也不呼叫外部 LLM。

## Phase 5C：Codex MCP Session Eval Report Capture

新增 `evals/` 報告目錄、Phase 5C Codex session report template 與 `scripts/new_mcp_eval_report.py`，讓使用者能用固定 prompt suite 手動執行 Codex MCP session eval 並保存結果。狀態：ready for manual run。此階段不新增 MCP tools、不改 MCP server 行為、不改 core pipeline，也不啟動外部 MCP client。

## Phase 5D：MCP Eval Prompt / Rubric Tightening

根據 Phase 5C 實測報告中的低風險問題，收緊 eval prompts、rubric 與 report capture 欄位：transcript evidence request 必須先使用 `search_transcripts`；dry-run transcribe case 不得錯誤聲稱可見/可呼叫的 `transcribe_episode` 不可用；investment-advice refusal case 除非 prompt 明確要求，不加入 MCP evidence 以外的外部市場、公司或新聞資訊。此階段為 docs/eval only，不新增 MCP tools、不改 MCP server 行為、不改 response envelope、不改 core pipeline，也不重寫既有 historical reports。

## Phase 6A：Gooaye Research System Spec

建立股癌研究系統的 spec-kit 風格需求規格，將目標從 podcast ingestion / MCP 工具層提升到研究層。此階段定義 episode intelligence report、產業鏈與股票 mapping、Gooaye Lens、外部資料查證邊界、dry-run / confirmation / API-cost guard，以及不提供投資建議的安全規則。規格位於 `specs/001-gooaye-research-system/spec.md`。

## Phase 6B：Episode Intelligence Report

針對單集 podcast 產生可閱讀的研究報告，整理本集主題、產業鏈線索、mentions、宏觀變數、風險與不確定事項。v1 採 deterministic-only，讀取既有 transcript 與 mentions artifact，輸出 JSON 與 Markdown，不呼叫 LLM、不查外部市場資料、不產生股票 mapping。所有 podcast-derived claim 都應盡量附 timestamp evidence；transcript 狀態缺失、損壞或 partial 時不得產生未標示風險的正式結論。

## Phase 6C：Industry Chain / Stock Mapping

將 podcast 線索轉成產業鏈節點與股票候選清單。v1 讀取既有 episode intelligence report JSON 與本機 `config/industry_chain_mappings.yaml`，輸出 JSON 與 Markdown，不呼叫 LLM、不查外部市場資料、不新增 MCP tools。此階段必須區分 `podcast_explicit`、`inferred_from_industry` 與 `needs_verification` candidate，不得把推論包裝成 podcast 事實。

## Phase 6D：External Market Data Boundary

建立可執行但不連外的 external market data boundary scaffold。v1 讀取既有 industry mapping 與本機 `config/external_data_boundary.yaml`，輸出 JSON 與 Markdown，將每個 candidate 標示為 `external_verification_status=not_requested`、`source_status=not_fetched`、`data_date=null`，並列出需要查證的外部資料類型。此階段不呼叫外部 provider、不讀 API key、不產生即時價格、市值、財報、新聞或公司現況事實，也不產生買賣建議。

## Phase 6E：Gooaye Lens Model

把「股癌看產業鏈與市場的角度」結構化成可重用的 deterministic lens model。v1 提供本機 `config/gooaye_lens.yaml`、loader 與 inspection CLI，定義產業鏈位置、供需與庫存、景氣循環、利率與估值敏感度、資本支出與產能、地緣政治與不確定性等維度，以及不提供買賣建議、目標價、保證報酬、不捏造 podcast evidence、區分 podcast evidence / inference / external-data status 的安全規則。此階段不產生 stock lens report、不接受任意股票輸入、不呼叫 LLM、不查外部市場資料、不新增 MCP tools。

## Phase 6F：Stock Lens Report

讓使用者輸入任意股票或公司，系統用 Gooaye Lens 產生 evidence-based 分析框架。v1 掃描單一 podcast 既有 `data/mappings/` 與 `data/external/` local artifacts，保守比對 candidate 的 `company_name` 與 `tickers`，並輸出 JSON 與 Markdown。`podcast_explicit` 才能列為 direct podcast evidence；`inferred_from_industry` 只能列為 needs-verification research lead。若沒有 direct podcast evidence，仍產生報告並明確標示 `no-direct-podcast-evidence`。此階段不呼叫 LLM、不查外部市場資料、不讀 API key、不新增 MCP tools，也不得回答是否應買賣、目標價或個人化投資建議。

## Phase 6G：Research Skill Workflow

建立 Core+CLI deterministic research workflow runner。v1 以 dry-run first 方式列出 planned reads/writes、step order、semantic LLM 外部 API 風險、cache stale 風險與需要的確認；`confirm=true` 後只執行本機 steps：`extract_mentions`、episode intelligence report、industry chain mapping、external data boundary，並可選擇產生 stock lens report。此階段不新增 MCP tools、不執行 semantic summary、不查外部市場資料、不自動 rebuild cache，也不提供投資建議。

## Phase 6H：Research Eval / Safety Gate

建立 LLM 前置 safety gate 的 research eval prompts、rubric 與報告模板，驗證系統不幻覺、不亂 mapping、不跳過 `api_cost_ack`、不洩漏 transcript 或 API key、不把 `not_fetched` / `not_requested` external boundary 當成市場事實、不產生投資建議，並能正確處理 no evidence、partial transcript、外部資料不可用與 cache stale 情境。此階段為 docs/eval only，不呼叫 LLM、不查外部市場資料、不新增 MCP tools、不改 Phase 6G workflow。

## Phase 6I：Optional LLM Workflow / Lens Synthesis

先落地 Workflow LLM：`run_research_workflow` 預設維持 deterministic 行為，只有在 `include_semantic_summary=True`、`confirm=True` 並提供 exact `api_cost_ack` 時，才會先執行 `semantic_summarize_episode`，再跑 deterministic research steps。Dry-run 只列 semantic summary 的 external API、transcript transfer 與 cost risk，不呼叫 LLM。此階段不新增 MCP tools、不查外部市場資料、不做 Gooaye Lens synthesis；lens synthesis 留待後續階段，且必須沿用 Phase 6H safety gate。

## Phase 6J：Stock Lens LLM Synthesis

建立 standalone Core+CLI 的 LLM-assisted stock lens synthesis。v1 只讀既有 Phase 6F stock lens JSON，輸出 `.stock-lens-synthesis.json` 與 `.stock-lens-synthesis.md`，並沿用 exact `api_cost_ack` guard；dry-run 只列 planned reads/writes、LLM API/cost risk 與 required acknowledgement，不呼叫 LLM。此階段不讀 raw transcript、不讀 semantic summary artifact、不查外部市場資料、不新增 MCP tools、不接 `run_research_workflow`，也不得產生 buy/sell/hold、target price 或 guaranteed return。

## Phase 6K：Research Workflow Synthesis Integration

將 Phase 6J stock lens synthesis 以 workflow opt-in synthesis step 接進 `run_research_workflow`。預設 workflow 行為維持 deterministic；只有在 `include_stock_lens_synthesis=True`、提供 `stock_query`、`confirm=True` 並提供 exact `api_cost_ack` 時，才會在 stock lens report 後執行 synthesis。Dry-run 只列 planned reads/writes、LLM API/cost risk、no raw transcript / no external market data 邊界與 required acknowledgement，不寫 artifacts。此階段不新增 MCP tools、不自動 rebuild cache、不查外部市場資料，也不改 Phase 6J standalone Core+CLI。

## Phase 6L：Research Workflow MCP Exposure

將既有 `run_research_workflow` 以 consolidated MCP side-effect tool 暴露給 Codex / Claude 類 client。MCP tool 維持 dry-run first，confirmed execution 才呼叫 core workflow；semantic summary 與 stock lens synthesis 仍需 exact `api_cost_ack`。此階段只新增 MCP exposure，不改 core workflow、不新增外部市場資料、不回 raw transcript、不讀 API key value、不自動 rebuild cache，也不提供投資建議。

## Phase 6M：External Data Provider Scaffold

建立可插拔但預設不連外的 external market data provider scaffold。v1 只支援本機 fixture provider，讀取既有 Phase 6D `.external-boundary.json`，在 `confirm=true` 後依精準 company name / ticker match 更新外部查證狀態、資料日期與來源 metadata。Dry-run 只列 planned reads/writes，不寫 artifacts。此階段 no live market API、不讀 API key、不新增 MCP tools、不接 `run_research_workflow`，也不提供投資建議。

## Phase 6N：External Data Verification Workflow Integration

將 Phase 6M fixture verification 以 opt-in workflow step 接進 `run_research_workflow`。預設 workflow 行為維持不變；只有在 `include_external_data_verification=True` 時，才會在 `generate_external_data_boundary` 後、stock lens report 前執行 `verify_external_data_boundary`。此階段只支援本機 fixture provider，no live market API、不讀 API key、不新增 MCP tools、不自動 rebuild cache，也不提供投資建議。

## Phase 6O：LLM Research Smoke / Codex Review Harness

建立 LLM research smoke 與 Codex manual review harness，用來驗證既有 OpenAI-compatible provider 是否能產生可讀、可追溯、符合 Gooaye Lens 邊界的 stock lens synthesis。v1 新增 smoke CLI、操作文件與 report template；真實 LLM 呼叫仍走 OpenAI-compatible `/chat/completions`，目前 Codex session 只作為 manual reviewer，不是 repo 可直接呼叫的 runtime backend。此階段不新增研究能力、不新增 MCP tools、不查 live market data、不放寬 exact `api_cost_ack` 或 investment-advice boundary。

## Phase 6Q：LLM Profile Config

新增 `config/llm_profiles.yaml` 與 LLM profile loader，讓 smoke / synthesis CLI 可用 `--llm-profile gb10` 重用 provider、model、base URL 與 API key env var 名稱。Profile 不保存 API key、token 或 secret 值；CLI 明確傳入的 `--model`、`--base-url`、`--api-key-env` 仍優先於 profile。此階段不改 core provider 行為、不新增 MCP tools、不呼叫 LLM、不查 live market data，也不放寬 exact `api_cost_ack` 或 investment-advice boundary。

## Phase 6R：Local `.env` Secret Loader

新增標準庫實作的本機 `.env` loader，讓 LLM smoke / synthesis / semantic summary / research workflow CLI 可用 `API_KEY`、`MODEL`、`BASE_URL` 做手動測試，不必每次設定 PowerShell env var。`.env` 不保存到 git；CLI 預設載入 `.env`、可用 `--env-file` 指定路徑或 `--no-env-file` 停用，且只回報載入的 env var 名稱，不顯示 secret value。`MODEL` / `BASE_URL` 是建議命名，舊 `OPENAI_MODEL` / `OPENAI_BASE_URL` 僅保留為相容 fallback。此階段不改 core provider 行為、不新增 MCP tools、不呼叫 LLM、不查 live market data，也不放寬 exact `api_cost_ack` 或 investment-advice boundary。

## Phase 6T：Research LLM Smoke Review Gate

新增 deterministic review report / quality gate，讓 confirmed LLM smoke 後可產生 timestamped `.review.json` / `.review.md` audit report。此階段只讀既有 stock lens synthesis artifacts，檢查 6F JSON-only input boundary、no-investment-advice flag、obvious secret / traceback / raw transcript leakage、prohibited advice patterns、external status wording，以及 podcast evidence / inference / external status separation。Review gate 是 heuristic，不取代人工判斷；它不呼叫 LLM、不讀 `.env`、不查 external market data、不新增 MCP tools，也不重寫既有 synthesis artifacts。

## Phase 6U：Semantic Summary Smoke Validation

新增 semantic summary smoke validation，專門驗證 transcript-transfer 這條 OpenAI-compatible LLM 路徑。Dry-run 只列 transcript validation status、planned reads/writes、provider metadata、transcript transfer / cost risk 與 required acknowledgement；confirmed execution 必須提供 exact `api_cost_ack` 才會呼叫 provider 並產生 `.semantic.md`。新增 deterministic semantic summary review gate，檢查 timestamp evidence、chunk summaries、metadata、secret / traceback / raw transcript dump marker 與 prohibited advice。Direct `summarize_episode.py --mode semantic` 也納入 exact ack guard，避免繞過 workflow/MCP/smoke boundary。此階段 no MCP tool changes、no live market API、no automatic cache rebuild、no investment advice。

## Phase 6U.1：Semantic Smoke Review Guard + Progress

修正 GB10 semantic smoke review 的 false positive：semantic review guard 允許 podcast evidence 中 speaker 過去買進 / 持有等 transcript-derived 描述，但仍拒絕直接 buy/sell/hold、建議買進、目標價、target price、guaranteed return 與保證報酬。Confirmed semantic smoke 新增 stderr progress，顯示 chunk_count、chunk start/done 與 final_summary start/done；stdout 維持 JSON，不輸出 raw transcript、prompt、API key 或 LLM response。此階段不改 prompt、不改 provider、不改 MCP、不查 live market API、不自動 rebuild cache、不提供 investment advice。

## Phase 6V：Reviewed Semantic Context for Stock Lens Synthesis

將已通過 semantic summary review gate 的 `.semantic.md` 作為可選 stock lens synthesis context。預設仍維持 `phase-6f-stock-lens-json-only`，不讀 `.semantic.md`；只有 `include_semantic_context=True` / `--include-semantic-context` 時，才會讀 matched episode 的 reviewed semantic summary metadata 與 final summary，並把 boundary 標示為 `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`。Context 不包含 `## Chunk Summaries`、不讀 raw transcript、不讀 `.env`、不查 live market API、不新增 MCP tool changes，也不提供 investment advice。Reviewed semantic summary 是 LLM intermediate artifact，不是 podcast 原文，也不是 external market fact。

## Phase 6V.1：Review Gate Boundary Alignment

修正 research LLM smoke review gate 的 Phase 6V boundary/context consistency。Review gate 接受預設 `phase-6f-stock-lens-json-only` 且沒有 semantic context 的 artifact，也接受 `phase-6f-stock-lens-json-plus-reviewed-semantic-summary` 且 `source_semantic_context` 非空、每筆 context `review_status=passed` 並有內容的 artifact。未知 boundary、JSON-only boundary 夾帶 semantic context、或 reviewed semantic boundary 缺少通過 review 的 context 仍會 fail。此階段不新增 CLI 參數、不呼叫 LLM、不讀 `.env`、不查 live market API、不新增 MCP tool changes、不重寫歷史 review report，也不提供 investment advice。
## Phase 7A：Architecture / Spec Kit Stabilization

將已完成到 Phase 6T 的研究層整理回 spec-kit 可追蹤結構。此階段是 docs/spec-only：更新 architecture、spec plan、data model 與 quickstart，明確標示 deterministic steps、optional LLM steps、local fixture verification、review gate、no live market API、no MCP behavior change、no `.env` read 與 no investment advice 邊界。Phase 7A 不改 runtime、不改 artifact schema、不呼叫 LLM；完成後再評估 Phase 6U semantic summary smoke 或下一個小型 LLM output-quality tuning phase。

## Phase 7B：Official Spec Kit Bootstrap

正式導入 GitHub Spec Kit scaffold。此階段使用官方 `specify init` 導入等價的 `.specify` infrastructure 與 Codex skills mode 的 `.agents/skills`，並建立 repo-level `AGENTS.md`。既有 `specs/001-gooaye-research-system/` 文件保留為 Phase 6/7 研究系統規格。此階段不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 live market API，也不放寬 no investment advice 邊界。

## Phase 7C：Spec Kit Constitution + Workflow Alignment

將 Spec Kit scaffold 專案化：更新 `.specify/memory/constitution.md`、`.specify/templates/`、`AGENTS.md` 與相關 docs，讓 full Spec Kit flow 成為後續功能開發標準：`$speckit-constitution`、`$speckit-specify`、`$speckit-clarify`、`$speckit-plan`、`$speckit-checklist`、`$speckit-tasks`、`$speckit-analyze`、`$speckit-implement`、`$speckit-converge`；`$speckit-taskstoissues` 只在需要 GitHub issue handoff 時使用。此階段是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice。完成後再進 Phase 6U semantic summary smoke 或下一個 LLM 品質調整階段。

## Phase 7D：Spec Kit Backfill via Full Workflow

依照 constitution 的 full Spec Kit flow，把已開發功能做 capability-group backfill。`specs/README.md` 成為 registry，`001-gooaye-research-system` 保留為 umbrella product spec，`002-ingestion-transcript-core` 到 `007-spec-kit-governance` 記錄 as-built specs、plans、data models、quickstarts、tasks 與 checklists。此階段記錄 `$speckit-clarify`、`$speckit-analyze`、`$speckit-converge` 等步驟，並包含 `006-llm-safety-synthesis-smoke-review` 的 optional LLM/smoke/review gate 邊界。Phase 7D 是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice。

## Phase 7D.1：Spec Kit Active Feature Guidance

補齊 official Spec Kit command usability 文件，說明 feature packages 的正確位置是 `specs/<feature>`，`.specify/` 是 scaffold / memory / templates / scripts / workflow metadata，不是 feature spec 目錄。多個 backfilled packages 不預設 pin 單一 active feature；要對特定 package 跑 official scripts 或 skills，先設定 `SPECIFY_FEATURE_DIRECTORY`，例如 `$env:SPECIFY_FEATURE_DIRECTORY="specs/003-metadata-search-mcp-core"`。官方 script 可能保存 `.specify/feature.json`；切換 package 時重新設定 env var 即可。Phase 7D.1 是 docs/spec/tests only：Spec Kit command usability / active feature documentation，no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice。完成後 Phase 6U semantic summary smoke 仍是下一個可能功能階段。

## 目前狀態與下一步

本節是 roadmap 的權威「current status」指標，補在歷史 phase log 之後，供接手的 AI agent 判斷「已完成到哪、下一步是什麼」，不重寫上方任何歷史 phase 段落。

### 已完成到哪

- 最高完成功能階段為 **Phase 6V.1（Review Gate Boundary Alignment）**；上方 Phase 0 → 6V.1 的功能階段皆已落地，並由 `tests/` 對應守衛測試鎖定。
- Latest implemented corpus package is **018-latest-episode-verified-research-report-workflow**. It follows **017-corpus-latest-episode-deterministic-workflow**, **016-corpus-episode-completion-workflow-runner**, and **015-corpus-semantic-remediation-runner**. Packages `008` through `018` cover index, planning, bounded stage runners, fresh workflow, semantic remediation, completion, latest deterministic readiness, and an episode-scoped verified research report.
- SPEC 017 is Implemented. The 2026-07-17 confirmed EP679 stop at `blocked` before audio download, caused by the `seeded`/`downloaded` child-outcome mapping gap, is a resolved historical blocker. The final metadata-only confirmed report is `episode_ref=EP679`, `outcome=ready_for_semantic_summary`, `ready_count=1`, `blocked_count=0`, and `failed_count=0`; no semantic stage ran.
- SPEC 018 is Implemented. It adds strict zero-write preview, exact `expected_episode_ref` plus exact acknowledgement before protected access, one pinned latest episode, semantic review exact `passed` gate, fixed-safe deterministic research, checkpoint/resume metadata, and content-digest JSON/Markdown/manifest bundle publication with atomic reuse/fail-closed behavior. It adds the fifteenth reviewed MCP tool and a portable preview → explicit approval → one confirmed call Skill; no live market API, automatic cache rebuild, retry/scheduler, or investment advice is added.
- The next unused feature package number is **019**.
- 其後為 audit-remediation 硬化（**非編號功能階段，不進 Phase 序列**），對應目前 HEAD：
  - **Batch 2**：安全/契約守衛測試（secret boundary、gitignore policy、MCP tool registry、LLM ack 契約、LLM CLI no-leak、manual cache rebuild）。
  - **Batch 2.5**：AI handoff governance docs 守衛。
  - **Batch 3A**：把 exact `api_cost_ack` 守衛下沉到 core（`create_provider` / `semantic_summarize_episode`），provider 建構前先驗證。
  - **Batch 3B**：storage / `rebuild_cache` dead-code 清理，以及 provider factory boundary（`OpenAICompatibleProvider` 只能於 `llm_provider.py` 內建構）。
- Batch 2/2.5/3A/3B 的正式追蹤在 `docs/agent-handoff.md` 與 `docs/verification-matrix.md`；其 guard-test 對應見 `specs/README.md` 的「Batch Guard Tests」。

### 關於「下一步」的澄清

- 上方 **Phase 7A / 7C / 7D.1** 段落收尾提到「Phase 6U semantic summary smoke 仍是下一個可能功能階段」等文字，是**撰寫當時的歷史規劃註記**。**6U/6U.1 已完成**（見上方 Phase 6U、6U.1、6V、6V.1 段落），因此那些指標**不再代表目前的下一步**，僅保留為歷史紀錄。
- 本 repo 已是多個 as-built backfilled package 的狀態，**目前不預設單一 active 的 next feature**。下一個功能性工作由使用者指定，並依 constitution 走 full Spec Kit flow、於下一個未佔用編號建立新的 `specs/<feature>` package。

### 編號註記

- Phase 編號 **6P、6S 未使用**（跳號，非遺漏）。
