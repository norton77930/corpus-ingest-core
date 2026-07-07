# MVP 需求

> **狀態：Phase 1–4A 歷史快照（historical snapshot）。** 本文件記錄 MVP 初期（Phase 0 → 4A）的需求與邊界，**不是** current scope 的權威來源。目前的產品範圍與安全邊界以 `.specify/memory/constitution.md`、`docs/architecture.md`、`docs/agent-handoff.md` 為準；current status 見 `docs/roadmap.md` 的「目前狀態與下一步」。
>
> 後續 Phase 6x 研究層（episode intelligence、industry mapping、Gooaye/stock lens、stock lens synthesis、research workflow，以及 `download_audio` / `transcribe_episode` / `run_research_workflow` 等 dry-run-first side-effect MCP tools）**刻意超出本快照**。下方「明確不做」是 Phase 1–4A 當時的邊界；其中「不做股票分析或投資建議」已由 constitution 原則 VI 細化為：**允許** evidence-based 研究整理，**仍禁止** buy/sell/hold、目標價、保證報酬等 investment *advice*。

## 目前已完成

- 建立 Python `src` layout 專案、繁體中文 README 與設計文件。
- 從 `config/podcasts.yaml` 載入 podcast profile，第一個 profile 為 `gooaye`。
- `list_episodes()` 與 `get_episode()` 可讀取 RSS，支援 `latest` 與大小寫不敏感 episode ref lookup。
- `download_audio()` 可用 streaming HTTP 下載音檔，並寫入 deterministic `data/audio/` 路徑。
- `transcribe_episode()` 可使用本機 faster-whisper 輸出 TXT、SRT 與 JSON。
- `summarize_episode()` 可從既有 transcript 產生 deterministic Markdown 摘要。
- `semantic_summarize_episode()` 可透過 OpenAI-compatible provider 產生 LLM 語意摘要。
- `extract_mentions()` 可用 deterministic rules 從 transcript segments 產生 mentions JSON 與 Markdown。
- `initialize_cache()`、`rebuild_cache()`、`search_transcripts()`、`search_mentions()` 可建立 SQLite metadata cache 並做 LIKE / optional FTS5 search。
- `validate_transcript()` 可檢查 transcript 是否 valid、empty、partial、missing、corrupt 或 incomplete。
- Phase 4A 已建立 stdio-only MCP server skeleton，暴露安全 read/query tools 與 `rebuild_cache` maintenance tool。
- CLI scripts 維持薄層，只解析參數、呼叫 core functions 並輸出 JSON。

## Phase 1C.1 轉錄可執行性要求

- 預設轉錄設定為 `model=tiny`、`device=cpu`、`compute_type=int8`。
- CLI 支援 `--model`、`--device`、`--compute-type`、`--vad-filter`、`--force`。
- `--force` 會忽略既有逐字稿並重新轉錄。
- 逐字稿輸出必須先寫入 `.part` 暫存檔，成功後才替換正式 `.txt`、`.srt`、`.json`。
- CLI 可用 `--audio-path` 指定短音檔做 smoke test，不必每次轉錄完整 Podcast 長集數。
- core function 不輸出 console log；進度提示由 CLI 負責。
- 轉錄 JSON 必須包含 `generated_at`、來源音檔資訊、`last_segment_end_seconds` 與 `completed: true`。
- 轉錄期間可留下 `.json.part` progress artifact；正式輸出成功後必須清理 `.part`。

## 明確不做

- 不暴露會長時間執行或大量 IO 的 MCP tools。
- 不做 Web UI。
- 不做排程。
- 不做 embedding / vector search。
- 不做 LLM-assisted extraction。
- 不硬寫 API key。
- 不把股癌寫死在核心程式。
- 不做股票分析或投資建議。

## Phase 2A Semantic Summary 要求

- 語意摘要模式固定為 `semantic-llm`。
- 預設 provider 為 `openai-compatible`，API key 從環境變數讀取，預設 `OPENAI_API_KEY`。
- Model 不硬寫；優先使用 CLI `--model`，其次 `OPENAI_MODEL`，缺少時必須清楚報錯。
- Base URL 優先使用 CLI `--base-url`，其次 `OPENAI_BASE_URL`，最後使用 OpenAI-compatible 預設 `/v1` endpoint。
- Semantic summary 必須先執行 transcript validation，拒絕 missing、corrupt、incomplete outputs，partial 預設拒絕。
- Empty transcript 可產生明確 empty semantic summary，且不呼叫 LLM。
- Transcript segments 依 `chunk_seconds` 與 `max_segments_per_chunk` 分批送入 provider，避免一次塞入整集逐字稿。
- 語意摘要必須標示不構成投資建議，所有重要判斷應盡量附 timestamp evidence。

## Phase 2B Mention Extraction 要求

- Mention extraction 模式固定為 `deterministic-rules`。
- 輸出位置固定為 `data/mentions/{podcast_id}/{episode_ref}__{safe_title_slug}.mentions.json` 與 `.mentions.md`。
- Extraction 必須先執行 transcript validation，拒絕 missing、corrupt、incomplete outputs，partial 預設拒絕。
- Empty transcript 可成功產生 `mention_count=0` 的 mentions artifact。
- 每個 mention 必須保留來自 transcript segment 的 timestamp evidence。
- Dictionary rules 先內建於 extractor module，支援 company、stock_or_ticker、industry、macro_topic、crypto、place 等類型。
- Mention extraction 不使用 LLM，不代表完整語意理解，也不構成投資建議。

## Phase 3A / 3B SQLite Cache / Search 要求

- SQLite DB 固定為 `data/cache/podcast_ingest.sqlite3`。
- SQLite cache 是衍生資料，可刪除後重建；source of truth 仍是 `data/transcripts/`、`data/summaries/`、`data/mentions/`。
- Cache schema 至少包含 `episodes`、`transcript_segments`、`mentions`、`mention_evidence`。
- `rebuild_cache()` 只索引既有 artifacts，不自動下載、轉錄、摘要或抽 mentions。
- 搜尋保留 SQL `LIKE` fallback，並可在 SQLite 支援時使用 optional FTS5。
- 中文 exact query 應可穩定走 LIKE fallback；英文 query 可在 `search_mode=auto` 時使用 FTS5。
- Transcript search 結果應包含 highlight、實際 search mode，並可回傳有限前後文。
- 此階段不使用 embedding、vector DB 或 LLM search。
- Cache / search core functions 必須可由未來 MCP tools 直接包裝。

## Phase 4A MCP Server Skeleton 要求

- MCP server 使用官方 Python MCP SDK FastMCP，預設 stdio transport。
- MCP layer 只能呼叫既有 core functions，不得複製 RSS、SQLite、transcript 或 mention parsing logic。
- 第一批 tools 僅包含 `list_episodes`、`get_episode`、`validate_transcript`、`search_transcripts`、`search_mentions`、`rebuild_cache`。
- `download_audio()`、`transcribe_episode()`、`summarize_episode()`、`semantic_summarize_episode()`、`extract_mentions()` 不得在 Phase 4A 暴露為 MCP tools。
- Tool response 必須是 JSON envelope，成功為 `ok=true`，錯誤為 `ok=false`，不得直接暴露 traceback。
- MCP tools 不接受任意本機 file path、不自動 rebuild search cache、不自動呼叫外部 LLM，也不構成投資建議。

## Phase 1D 摘要要求

- 摘要模式固定為 `extractive-template`。
- 只讀取既有 transcript `.json` 與 `.txt`，不得自動下載或轉錄。
- 不呼叫 OpenAI、Anthropic、Gemini 或其他外部 LLM API。
- 沒有 transcript 時必須丟明確錯誤，不得假裝成功。
- Markdown 必須包含 metadata、摘要狀態、本集概覽、時間軸摘要、可引用片段與待 LLM 深度摘要 prompt。
- 寫檔必須先寫 `.part`，成功後才替換正式 summary。

## Phase 1E Transcript Validation 要求

- `validate_transcript()` 必須檢查 JSON、TXT、SRT 三種輸出是否存在。
- JSON 必須可 parse，且 `segments` 必須是 list。
- `segment_count` 與 `segments` 長度不一致時，狀態為 `partial`。
- 非空 segments 但 TXT 或 SRT 沒內容時，狀態為 `partial`。
- `completed: false` 時，狀態為 `partial`。
- 舊版 transcript 缺少新 metadata 時，不直接判 invalid，但要輸出 legacy warning。
- `summarize_episode()` 必須拒絕 missing、corrupt、incomplete 與預設 partial transcript；只有 `allow_partial=True` 時可摘要 partial transcript。

## 成功標準

- `python -m pytest` 通過。
- `python -m compileall src scripts` 通過。
- `python scripts/transcribe_episode.py --podcast gooaye --episode latest --model tiny --device cpu --compute-type int8` 可以開始以 CPU-friendly 設定執行。
- 若完整長集數在 CPU 上仍耗時過長，短音檔 smoke test 可透過 `--audio-path` 完成流程驗證。
- timeout 或寫檔失敗時不得留下半套正式 transcript output。
- `python scripts/summarize_episode.py --podcast gooaye --episode smoke-test --force` 可產生 Markdown 摘要，即使 transcript 沒有語音 segments。
- `python scripts/validate_transcript.py --podcast gooaye --episode smoke-test` 可輸出 JSON validation result。
- `python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode extractive --force` 維持不需 API key。
- `python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic --model <model>` 在 API key 設定完整時可產生 `.semantic.md`；缺少設定時必須清楚失敗。
- `python scripts/extract_mentions.py --podcast gooaye --episode EP672 --force` 可產生 deterministic mentions JSON 與 Markdown。
- `python scripts/rebuild_cache.py --podcast gooaye --force` 可從既有 artifacts 重建 SQLite cache。
- `python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 10 --search-mode auto` 可搜尋 transcript segments。
- `python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 10 --search-mode like --context-segments 1` 可搜尋 transcript segments 並回傳前後文。
- `python scripts/search_mentions.py --podcast gooaye --query 台積電 --type company` 可搜尋 mentions 與 timestamp evidence。
- `python scripts/run_mcp_server.py` 可啟動 stdio MCP server 並等待 client 連線。
