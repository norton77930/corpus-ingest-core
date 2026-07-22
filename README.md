# Podcast Ingestion Core

Podcast Ingestion Core 是一個通用的 Podcast 擷取核心。目前已完成 RSS episode listing、episode lookup、音檔下載、本機 faster-whisper 轉錄、transcript validation、deterministic extractive Markdown 摘要、OpenAI-compatible LLM semantic summary pipeline、deterministic mention extraction、SQLite metadata cache / search，以及 stdio-only MCP server。Web UI、排程、embedding 與 vector search 仍未實作。

第一個 podcast profile 是 Gooaye 股癌，但核心程式不得寫死股癌。所有 podcast-specific 設定都放在 `config/podcasts.yaml`。

## AI Agent Handoff / Where to Start

本 README 是 quick orientation（目錄結構、CLI 範例、phase history），不是完整 governance source。新接手的 AI agent 或開發者請從這裡開始：

- Handoff entrypoint（10 分鐘理解 repo）：[`docs/agent-handoff.md`](docs/agent-handoff.md)
- AI 開發規範（instruction hierarchy、change classification、DoR/DoD）：[`docs/ai-development-framework.md`](docs/ai-development-framework.md)
- 驗證矩陣（每種變更該跑什麼 tests）：[`docs/verification-matrix.md`](docs/verification-matrix.md)
- 架構決策記錄（ADR index）：[`docs/architecture-decision-records/README.md`](docs/architecture-decision-records/README.md)
- Repo-level agent hard constraints：[`AGENTS.md`](AGENTS.md)

## 專案目標

- 用同一組 core functions 支援多個 Podcast。
- 讓 CLI scripts 只負責解析參數並呼叫 core functions。
- 讓核心能力未來能直接包成 MCP tools。
- 所有輸出檔案都放在 `data/`，並使用 deterministic 命名，方便工具查找。

## 目錄結構

```text
config/
  podcasts.yaml
  industry_chain_mappings.yaml
  external_data_boundary.yaml
  external_market_data_fixtures.yaml
  gooaye_lens.yaml
  llm_profiles.yaml
data/
  audio/
  transcripts/
  summaries/
  mentions/
  reports/
  mappings/
  external/
  stock-lens/
  cache/
  corpus/
docs/
  agent-handoff.md
  ai-development-framework.md
  verification-matrix.md
  architecture-decision-records/
  architecture.md
  mvp-requirements.md
  roadmap.md
  mcp-readiness.md
  mcp-usage.md
  codex-mcp-setup.md
  claude-mcp-setup.md
  mcp-troubleshooting.md
scripts/
  list_episodes.py
  download_episode.py
  transcribe_episode.py
  validate_transcript.py
  summarize_episode.py
  run_corpus_episode_intake.py
  generate_corpus_index.py
  generate_corpus_remediation_plan.py
  run_corpus_audio_download.py
  run_corpus_remediation.py
  run_corpus_local_transcription.py
  run_corpus_episode_workflow.py
  run_corpus_semantic_remediation.py
  run_corpus_episode_completion_workflow.py
  run_corpus_latest_episode_deterministic_workflow.py
  run_latest_episode_verified_research_report_workflow.py
  extract_mentions.py
  rebuild_cache.py
  search_transcripts.py
  search_mentions.py
  validate_mcp_setup.py
  run_mcp_server.py
src/
  podcast_ingest_core/
tests/
```

## Core Functions

```python
list_episodes(podcast_id, limit)
get_episode(podcast_id, episode_ref)
download_audio(podcast_id, episode_ref)
transcribe_episode(
    podcast_id,
    episode_ref,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
    force=False,
    audio_path=None,
    progress_callback=None,
)
validate_transcript(podcast_id, episode_ref)
summarize_episode(
    podcast_id,
    episode_ref,
    force=False,
    max_quotes=10,
    window_seconds=300,
    allow_partial=False,
)
semantic_summarize_episode(
    podcast_id,
    episode_ref,
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    force=False,
    chunk_seconds=600,
    max_segments_per_chunk=120,
    allow_partial=False,
)
extract_mentions(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    max_evidence_per_mention=5,
)
generate_episode_intelligence_report(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    window_seconds=300,
    max_evidence_per_section=5,
)
generate_industry_chain_mapping(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    max_candidates_per_node=5,
    max_evidence_per_candidate=5,
)
generate_external_data_boundary(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
)
verify_external_data_boundary(
    podcast_id,
    episode_ref,
    confirm=False,
    force=False,
    allow_partial=False,
    provider="fixture",
    fixture_path=DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
)
load_gooaye_lens_model(path=DEFAULT_GOOAYE_LENS_CONFIG_PATH)
generate_stock_lens_report(
    podcast_id,
    stock_query,
    force=False,
    allow_partial=False,
    max_evidence_items=10,
)
generate_stock_lens_synthesis_report(
    podcast_id,
    stock_query,
    confirm=False,
    force=False,
    allow_partial=False,
    api_cost_ack="",
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    max_prompt_chars=24000,
)
run_research_workflow(
    podcast_id,
    episode_ref,
    stock_query=None,
    confirm=False,
    force=False,
    allow_partial=False,
    include_semantic_summary=False,
    include_stock_lens_synthesis=False,
    include_external_data_verification=False,
    api_cost_ack="",
    semantic_provider="openai-compatible",
    semantic_model=None,
    semantic_base_url=None,
    semantic_api_key_env="OPENAI_API_KEY",
    semantic_chunk_seconds=600,
    semantic_max_segments_per_chunk=120,
    synthesis_provider="openai-compatible",
    synthesis_model=None,
    synthesis_base_url=None,
    synthesis_api_key_env="OPENAI_API_KEY",
    synthesis_max_prompt_chars=24000,
    external_data_provider="fixture",
    external_fixture_path=DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
    max_evidence_per_mention=5,
    report_window_seconds=300,
    max_evidence_per_section=5,
    max_candidates_per_node=5,
    max_evidence_per_candidate=5,
    max_stock_evidence_items=10,
)
initialize_cache(db_path=None)
index_episode(podcast_id, episode_ref, force=False, db_path=None)
rebuild_cache(podcast_id=None, force=False, db_path=None)
search_transcripts(query, podcast_id=None, limit=20, db_path=None, search_mode="auto", context_segments=0, case_sensitive=False)
search_mentions(query, podcast_id=None, mention_type=None, limit=20, db_path=None, case_sensitive=False)
run_corpus_episode_intake(podcast_id, episode_ref="latest", confirm=False)
generate_corpus_index(podcast_id)
generate_corpus_remediation_plan(podcast_id)
run_corpus_audio_download(podcast_id, episode_ref=None, confirm=False)
run_corpus_remediation(
    podcast_id,
    confirm=False,
    episode_ref=None,
    action_family=None,
    max_actions=None,
    force=False,
    allow_partial=False,
)
run_corpus_local_transcription(
    podcast_id,
    episode_ref=None,
    confirm=False,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
)
run_corpus_episode_workflow(
    podcast_id,
    episode_ref="latest",
    stage="next",
    confirm=False,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
    force=False,
    allow_partial=False,
    max_actions=None,
)
run_corpus_semantic_remediation(
    podcast_id,
    episode_ref,
    action="next",
    confirm=False,
    api_cost_ack="",
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    chunk_seconds=600,
    max_segments_per_chunk=120,
    progress_callback=None,
)
run_corpus_episode_completion_workflow(
    podcast_id,
    episode_ref="latest",
    action="next",
    confirm=False,
    api_cost_ack="",
    transcription_model=None,
    transcription_device="cpu",
    transcription_compute_type="int8",
    transcription_vad_filter=False,
    semantic_provider="openai-compatible",
    semantic_model=None,
    semantic_base_url=None,
    semantic_api_key_env="OPENAI_API_KEY",
    semantic_chunk_seconds=600,
    semantic_max_segments_per_chunk=120,
    progress_callback=None,
)
run_corpus_latest_episode_deterministic_workflow(
    podcast_id,
    confirm=False,
    transcription_model=None,
    transcription_device="cpu",
    transcription_compute_type="int8",
    transcription_vad_filter=False,
)
run_latest_episode_verified_research_report_workflow(
    podcast_id,
    confirm=False,
    expected_episode_ref=None,
    api_cost_ack="",
    stock_query=None,
    include_fixture_verification=False,
)
```

`summarize_episode` 是 deterministic / extractive template，不呼叫外部 LLM API，也不產生語意推論。`semantic_summarize_episode` 會使用 OpenAI-compatible API 產生語意摘要，重要判斷應盡量附 timestamp evidence，且不構成投資建議。`extract_mentions` 使用 deterministic rules 從 transcript segments 擷取 mentions，每筆 mention 都保留 timestamp evidence。`generate_episode_intelligence_report` 使用 deterministic rules 從既有 transcript 與 mentions artifact 產生單集 episode intelligence report，不呼叫 LLM、不查外部市場資料、不產生股票 mapping 或投資建議。`generate_industry_chain_mapping` 使用本機 deterministic mapping config 從既有 episode intelligence report 產生產業鏈節點與股票候選，會明確區分 podcast explicit evidence 與 inferred / needs-verification 研究線索。`generate_external_data_boundary` 使用本機 boundary config 從既有 industry mapping 產生外部資料查證邊界 scaffold，不呼叫外部 provider、不讀 API key、不產生市場現況事實。`verify_external_data_boundary` 是 Phase 6M fixture provider scaffold：dry-run first，`confirm=True` 才會用本機 fixture 嘗試更新既有 external boundary；它有 confirm guard、no live market API、no MCP tool changes，也不提供投資建議。`load_gooaye_lens_model` 只載入與驗證本機 Gooaye Lens 分析框架，不產生股票報告、不呼叫 LLM、不查外部市場資料。`generate_stock_lens_report` 使用 podcast-wide local artifacts 與 Gooaye Lens 產生股票/公司研究框架，不呼叫 LLM、不查外部市場資料、不提供買賣建議、目標價或保證報酬。`generate_stock_lens_synthesis_report` 是 Phase 6J Stock Lens LLM Synthesis：dry-run first，預設 LLM input boundary 是 6F stock lens JSON only，confirmed execution 必須提供 exact api_cost_ack；Phase 6V 可明確 opt in reviewed semantic summary context，但仍不讀 raw transcript、不查外部市場資料、no MCP tool changes，也不提供買賣建議。`run_research_workflow` 是 dry-run first 的本機 research workflow runner，串接 mentions、episode intelligence、industry mapping、external boundary 與可選 stock lens；Phase 6I 支援 optional semantic summary execution inside research workflow，Phase 6K 支援 workflow opt-in synthesis，可用 `include_stock_lens_synthesis=True` 把 Phase 6J synthesis 接在 stock lens report 後面。Phase 6N 支援 optional workflow fixture verification，可用 `include_external_data_verification=True` 在 external boundary 後以本機 fixture provider 更新外部查證狀態；此步驟 no live market API、no API key、no MCP tool changes、no automatic cache rebuild，也不提供投資建議。`generate_corpus_index` 只掃描本機 per-episode artifacts 與 semantic review metadata，寫入 deterministic corpus status JSON/Markdown；它不讀 RSS、不讀 SQLite cache、不呼叫 LLM、不讀 `.env`、不新增 MCP tool，也不輸出 raw transcript/evidence/semantic body。`generate_corpus_remediation_plan` 會先刷新 corpus index，再從本機 status metadata 推導 full-ladder 缺口、blockers、warnings 與 manual-only action text，寫入 deterministic remediation JSON/Markdown；它不執行下載、轉錄、摘要、workflow、LLM、MCP 或 cache rebuild，也不輸出 raw transcript/evidence/semantic body/prompt/raw LLM output。`run_corpus_audio_download` 會先刷新 remediation plan，dry-run 只回傳 audio missing 且 action ready 的候選 metadata，不讀 RSS、不呼叫 network/downloader、不寫 run report；confirmed execution 必須指定單一 episode，才會呼叫既有 `download_audio()`，並寫入 latest deterministic audio download run report，內容不含 source URL、query string、secret 或 traceback。`run_corpus_remediation` 會先刷新 remediation plan，dry-run 只回傳 selected/skipped/blocked/excluded metadata；confirmed execution 必須指定 episode 或 action family，只執行 transcript-ready deterministic families（extractive summary、mentions、episode intelligence、industry mapping、external boundary），並寫入 latest deterministic run report。`run_corpus_local_transcription` 會先刷新 remediation plan，dry-run 只回傳本機 audio available 且 transcript missing 的候選 metadata；confirmed execution 必須指定單一 episode，且只用 explicit local `audio_path` 呼叫既有轉錄 core，不下載音檔、不修 corrupt/partial transcript、不碰 LLM/MCP/cache rebuild，並寫入 latest deterministic local transcription run report。`run_corpus_episode_workflow` 是 fresh episode 的 dry-run-first 安全入口：依序判斷 intake、audio download、local transcription、deterministic remediation 的下一個 safe stage；dry-run 不寫 workflow report、不執行 stage，confirmed execution 必須使用 `stage="next"` 且只執行一個 stage，寫入 latest deterministic workflow run report。LLM 步驟都必須 `confirm=True` 並提供 exact `api_cost_ack` 才會呼叫外部 LLM。此 workflow 仍不查外部市場資料、no raw transcript for stock lens synthesis、no MCP tool changes，也不自動 rebuild cache。`rebuild_cache` 只索引既有 artifacts，不會自動下載、轉錄、摘要、抽 mentions、產生研究報告、產生 mapping、產生 external boundary 或產生 stock lens report。

014 stabilization 的精確契約：`confirm=False` 是 strict zero-file，除可讀 configured podcast RSS feed 與 local artifacts 外，不建立、修改或刪除任何檔案；seeded selection 只建立一份 in-memory index/plan snapshot 並依序 preview 012/011/010。這與 standalone 010/011/012 dry-run 刻意保留的 fresh 008/009 persistence 行為不同。

`run_corpus_semantic_remediation(...)` 是 standalone、single-episode 的 015 semantic remediation Core。每次 valid request 只建立 exactly one fresh in-memory 008/009 snapshot，先隔離 explicit canonical episode，再選 `semantic_summary`、`semantic_review`、`completed` 或 blocked/manual-only；它 does not call 010 or 014。Dry-run 是 strict zero-file，且不 resolve profile、`.env`、credential 或 provider。Confirmed `semantic_summary` 必須 explicit action 並在 before profile / `.env` / provider construction 驗證 exact api_cost_ack；confirmed `semantic_review` 是 deterministic，完全不讀任何 LLM 設定。每次 confirmed run 最多呼叫 one executor，寫 confirmed-only latest JSON/Markdown report（no generated_at），does not rebuild index、plan 或 SQLite cache，且不新增 MCP tool，exact 12 tools 維持不變。

`run_corpus_episode_completion_workflow(...)` 是 016 的 single-episode completion Core：dry-run 以 strict zero-file 判斷從 intake 到 semantic review 的下一個 action；人類確認後只能對 canonical episode 明確執行一個 matching action，然後停止。stdio MCP 的同名 `run_corpus_episode_completion_workflow` tool 保持此 preview → human approval → one action 的界線，不讀 `.env`、不自動 rebuild cache，也不提供投資建議。

`run_corpus_latest_episode_deterministic_workflow(...)` 是 017 的 one-request latest-episode Core：dry-run 只解析當下 latest 並回傳 strict-zero-file 的 deterministic 處理計畫。SPEC 017 is Implemented. The 2026-07-17 `seeded`/`downloaded` child-outcome mapping problem is a resolved historical blocker; recorded metadata-only confirmed EP679 evidence ends with `outcome=ready_for_semantic_summary`, `ready_count=1`, `blocked_count=0`, and `failed_count=0`. The contract locks one canonical episode at start, processes intake、下載、本機轉錄與必要 deterministic remediation, fails closed on a failed/blocked stage, and stops at `ready_for_semantic_summary` without `.env`、provider、semantic summary/review、retry、or cache rebuild.

`run_latest_episode_verified_research_report_workflow(...)` 是 SPEC 018 的 latest-episode verified research report Core。預設 `confirm=False` 僅解析一次 latest 並回傳 strict-zero-file preview，不建立 checkpoint、staging 或 report bundle。confirmed request 必須在 RSS、環境/provider、writer 與 child stage 前提供 preview 所得的 exact `expected_episode_ref`，以及完全相等的 `api_cost_ack`；它重用 pinned 017 deterministic ladder，在 semantic summary/review exact `passed` gate 後，以固定安全 research options 建立 deterministic JSON、Markdown 與 manifest bundle。bundle 採 content digest version、atomic directory publish、identical-content reuse 與 conflict fail-closed；不自動 rebuild cache、不查 live market API，且不構成投資建議。

`validate_transcript` 可用來確認逐字稿是完整、空白、部分完成、缺失或損壞。

`run_corpus_episode_intake` 是 dry-run first 的 RSS episode bootstrap runner：dry-run 可解析 `latest` 或單一 explicit episode selector，但不寫檔、不下載、不轉錄、不碰 LLM/MCP/cache；confirmed execution 只寫安全 seed metadata 與 latest deterministic intake report，讓 008/009/012 可以接續發現、規劃與下載 audio。

## 輸出路徑規則

所有產物都位於 `data/`：

- 音檔：`data/audio/{podcast_id}/{episode_ref}__{safe_title_slug}.{ext}`
- 逐字稿：`data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.txt`
- 字幕：`data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.srt`
- 逐字稿 metadata：`data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.json`
- 摘要：`data/summaries/{podcast_id}/{episode_ref}__{safe_title_slug}.md`
- 語意摘要：`data/summaries/{podcast_id}/{episode_ref}__{safe_title_slug}.semantic.md`
- Mentions JSON：`data/mentions/{podcast_id}/{episode_ref}__{safe_title_slug}.mentions.json`
- Mentions Markdown：`data/mentions/{podcast_id}/{episode_ref}__{safe_title_slug}.mentions.md`
- Episode intelligence JSON：`data/reports/{podcast_id}/{episode_ref}__{safe_title_slug}.intelligence.json`
- Episode intelligence Markdown：`data/reports/{podcast_id}/{episode_ref}__{safe_title_slug}.intelligence.md`
- Industry mapping JSON：`data/mappings/{podcast_id}/{episode_ref}__{safe_title_slug}.industry-map.json`
- Industry mapping Markdown：`data/mappings/{podcast_id}/{episode_ref}__{safe_title_slug}.industry-map.md`
- External data boundary JSON：`data/external/{podcast_id}/{episode_ref}__{safe_title_slug}.external-boundary.json`
- External data boundary Markdown：`data/external/{podcast_id}/{episode_ref}__{safe_title_slug}.external-boundary.md`
- Stock lens JSON：`data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens.json`
- Stock lens Markdown：`data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens.md`
- Stock lens synthesis JSON：`data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens-synthesis.json`
- Stock lens synthesis Markdown：`data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens-synthesis.md`
- Corpus index JSON：`data/corpus/{podcast_id}/corpus-index.json`
- Corpus index Markdown：`data/corpus/{podcast_id}/corpus-index.md`
- Corpus episode seed JSON：`data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json`
- Corpus episode intake run JSON：`data/corpus/{podcast_id}/corpus-episode-intake-run.json`
- Corpus episode intake run Markdown：`data/corpus/{podcast_id}/corpus-episode-intake-run.md`
- Corpus remediation plan JSON：`data/corpus/{podcast_id}/corpus-remediation-plan.json`
- Corpus remediation plan Markdown：`data/corpus/{podcast_id}/corpus-remediation-plan.md`
- Corpus remediation run JSON：`data/corpus/{podcast_id}/corpus-remediation-run.json`
- Corpus remediation run Markdown：`data/corpus/{podcast_id}/corpus-remediation-run.md`
- Corpus local transcription run JSON：`data/corpus/{podcast_id}/corpus-local-transcription-run.json`
- Corpus local transcription run Markdown：`data/corpus/{podcast_id}/corpus-local-transcription-run.md`
- Corpus audio download run JSON：`data/corpus/{podcast_id}/corpus-audio-download-run.json`
- Corpus audio download run Markdown：`data/corpus/{podcast_id}/corpus-audio-download-run.md`
- Corpus episode workflow run JSON：`data/corpus/{podcast_id}/corpus-episode-workflow-run.json`
- Corpus episode workflow run Markdown：`data/corpus/{podcast_id}/corpus-episode-workflow-run.md`
- Corpus semantic remediation run JSON：`data/corpus/{podcast_id}/corpus-semantic-remediation-run.json`
- Corpus semantic remediation run Markdown：`data/corpus/{podcast_id}/corpus-semantic-remediation-run.md`
- Corpus episode completion workflow run JSON：`data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json`
- Corpus episode completion workflow run Markdown：`data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.md`
- Corpus latest deterministic workflow run JSON：`data/corpus/{podcast_id}/corpus-latest-episode-deterministic-workflow-run.json`
- Corpus latest deterministic workflow run Markdown：`data/corpus/{podcast_id}/corpus-latest-episode-deterministic-workflow-run.md`
- Verified research checkpoint：`data/corpus/{podcast_id}/verified-research/{episode_ref}.checkpoint.json`
- Verified research report bundle：`data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/report.json`、`report.md`、`manifest.json`
- SQLite metadata cache：`data/cache/podcast_ingest.sqlite3`
- Episode cache：`data/cache/{podcast_id}/episodes.json`

`podcast_id` 必須是小寫 slug。Episode ref 由 RSS title 與 podcast profile 的 `default_episode_prefix` 解析，例如 `EP672`。檔名 title slug 會移除 Windows 不合法字元、控制字元、emoji 與高風險符號。

## CLI 範例

產生 podcast-level corpus status index：

```powershell
python scripts/generate_corpus_index.py --podcast gooaye
```

這個 CLI 只讀本機 per-episode artifacts，會重寫 `data/corpus/{podcast_id}/corpus-index.json` 與 `.md`。stdout 是 metadata-only JSON，包含輸出路徑、episode count、warning count 與 artifact family counts；不含 transcript 原文、evidence snippet、semantic summary body、prompt、raw LLM output、API key 或 provider secret。

產生 podcast-level corpus remediation plan：

```powershell
python scripts/generate_corpus_remediation_plan.py --podcast gooaye
```

這個 CLI 會先刷新 corpus index，再重寫 `data/corpus/{podcast_id}/corpus-remediation-plan.json` 與 `.md`。stdout 是 metadata-only JSON，包含輸出路徑、episode count、warning count、action count、blocked/optional/gated action counts；不執行任何 remediation action，不讀 RSS/SQLite cache/`.env`，不呼叫 network/LLM/MCP，也不輸出 transcript/evidence/semantic body/prompt/raw LLM output 或 secret。

Preview 或 confirmed 執行單集 audio download：

```powershell
python scripts/run_corpus_audio_download.py --podcast gooaye
python scripts/run_corpus_audio_download.py --podcast gooaye --episode EP672 --confirm
```

這個 CLI 會先刷新 corpus remediation plan；因此 standalone dry-run 仍會持久化 fresh corpus index 與 remediation plan。預設 dry-run 只在 stdout 回傳 metadata-only JSON，不讀 RSS、不呼叫 network/downloader、不寫 `corpus-audio-download-run.json/.md`、不寫 audio。`--confirm` 必須搭配單一 `--episode`，只會在 audio status 是 `missing` 且 audio action 是 `ready` 時呼叫既有 `download_audio()`。Confirmed run 會寫 latest `data/corpus/{podcast_id}/corpus-audio-download-run.json` 與 `.md`，內容無 timestamp、無 source URL/query string/secret/traceback，且不提供投資建議；寫入或 reuse audio 後只提示轉錄、下游 remediation 與 cache rebuild 仍需手動執行。

Preview 或 confirmed 執行 deterministic corpus remediation：

```powershell
python scripts/run_corpus_remediation.py --podcast gooaye
python scripts/run_corpus_remediation.py --podcast gooaye --action-family mentions --confirm
python scripts/run_corpus_remediation.py --podcast gooaye --episode EP672 --confirm
```

這個 CLI 會先刷新 corpus remediation plan；因此 standalone dry-run 仍會持久化 fresh corpus index 與 remediation plan。預設 dry-run 只在 stdout 回傳 metadata-only JSON，不寫 `corpus-remediation-run.json/.md`，也不執行 artifact generator。`--confirm` 必須搭配 `--episode` 或 `--action-family`，只會呼叫既有 deterministic core functions，不 shell out 到 scripts；v1 不執行 download、transcribe、semantic summary/review、stock-lens、LLM、RSS/network、SQLite cache rebuild、`.env` 或 MCP。Confirmed run 會寫 latest `data/corpus/{podcast_id}/corpus-remediation-run.json` 與 `.md`，內容無 timestamp、無 raw transcript/evidence/semantic body/prompt/raw LLM output/secret，且不提供投資建議。

Preview 或 confirmed 執行單集本機轉錄：

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm --model small --device cuda --compute-type float16
```

這個 CLI 會先刷新 corpus remediation plan；因此 standalone dry-run 仍會持久化 fresh corpus index 與 remediation plan。預設 dry-run 只在 stdout 回傳 metadata-only JSON，不寫 `corpus-local-transcription-run.json/.md`、不寫 transcript、不載入 Whisper model、不下載音檔。`--confirm` 必須搭配單一 `--episode`，只會在 local audio path 存在且 transcript status 是 `missing` 時呼叫既有 `transcribe_episode()`，並明確傳入 `audio_path` 與 `force=False`。Confirmed run 會寫 latest `data/corpus/{podcast_id}/corpus-local-transcription-run.json` 與 `.md`，內容無 timestamp、無 raw transcript/prompt/raw LLM output/secret/traceback，且不提供投資建議；寫 transcript 後只提示 cache 可能 stale，不自動 rebuild cache。

Preview 或 confirmed 執行 fresh episode workflow 的下一個 safe stage：

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest --stage next --confirm
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode EP677 --stage next --confirm --model small --device cuda --compute-type float16
```

這個 CLI 的 014 dry-run 是 strict zero-file：013 可讀取 configured RSS 解析 selector；有 seed 時只建立一次 fresh in-memory corpus index/plan snapshot，並用同一份 snapshot preview 012/011/010。它不建立、修改或刪除 seed、audio、transcript、index、plan、010-014 reports、downstream artifacts 或 `.part`；planned reads 可含安全 local dependency paths，非 path 值只允許兩個 exact labels。Confirmed execution 必須明確帶 `--stage next --confirm`，每次只 dispatch 一個既有 public runner；該 runner 可依原契約刷新 index/plan 並寫 selected-stage artifacts，014 記錄結果後停止且寫入 latest workflow report。semantic/LLM/stock-lens/MCP/cache rebuild/batch 工作仍只列為 manual follow-up，不自動執行。

Preview 或 confirmed 執行單集 semantic remediation：

```powershell
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP700
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP700 --action semantic_summary --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP700 --action semantic_review --confirm
```

015 不接受 `latest`；dry-run `action=next` 只回 metadata 且 strict zero-file。Confirmed summary 的 exact api_cost_ack 必須 before profile、`.env`、credential 與 provider construction；review 不需 acknowledgement，且不 resolve profile/`.env` 或呼叫 LLM。Validated confirmed attempt 寫 `corpus-semantic-remediation-run.json/.md`，內容 no generated_at、無 transcript/semantic/prompt/raw response/base URL/secret/traceback；index、plan 與 cache 可能 stale，需手動刷新。

Preview 或在使用者明確確認後執行單集 completion workflow：

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode EP677 --action audio_download --confirm
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode EP677 --action semantic_summary --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

016 dry-run 是 strict zero-file：有 seed 時只在記憶體建立一份 fresh 008/009 snapshot，依序選出 intake、audio download、local transcription、deterministic remediation、semantic summary 或 semantic review 的下一個 safe action。confirmed 必須使用 dry-run 回傳的 canonical episode 與同一個 explicit action；`next`、`latest` 或 stale action 會被拒絕，每次最多 dispatch 一個既有 runner 後停止。semantic summary 的 exact ack 必須在任何 profile/`.env`/provider work 前完成；semantic review 不讀 LLM 設定。有效 confirmed attempt 才會原子寫入 `data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json` 與 `.md`，不自動刷新 index、plan 或 SQLite cache。

如由 Agent 操作，使用同名 MCP tool `run_corpus_episode_completion_workflow` 與 repository 的 portable `corpus-episode-completion` Skill：先 preview、說明風險、等待人類對 canonical action 的明確同意，再執行一個 action 並停止；沒有 MCP 時不得改用 CLI、terminal、scheduler 或自動重試。

預覽或 controlled confirmed 執行 latest deterministic workflow：

```powershell
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye --confirm
```

SPEC 017 is Implemented. 如由 Agent 收到「幫我處理 Gooaye 最新一集」等明確請求，`corpus-latest-episode-processing` Skill 將該 explicit natural-language request 視為一次 execution authorization：acknowledge once、僅以 `confirm=true` 呼叫一次 dedicated `run_corpus_latest_episode_deterministic_workflow` MCP tool、回報 metadata-only result once，然後停止。MCP tool 本身仍預設 `confirm=false` dry-run；Skill 不得先 preview、不得 second call，亦不得使用 CLI/terminal fallback、排程、批次、重試、cache rebuild 或 semantic summary/review。

預覽 latest verified research report workflow：

```powershell
python scripts/run_latest_episode_verified_research_report_workflow.py --podcast gooaye
```

SPEC 018 的 preview 是 strict zero-write，會回傳一個 canonical episode reference 與 exact required acknowledgement。只有在使用者對該 previewed episode 明確同意後，才以同一個 `--expected-episode-ref` 和 exact `--api-cost-ack` 執行一次 `--confirm`。確認必須發生在 RSS、environment/provider、writer 或 child stage 前；workflow 重用 pinned deterministic ladder，要求 semantic review exact `passed`，再以固定安全 options 完成 deterministic research。完成後將以 source digest version 的 `report.json`、`report.md` 與 `manifest.json` 原子發布，identical bundle reuse，conflict fail-closed；不做 retry、scheduler、live market API 或 cache rebuild，且不構成投資建議。

列出最新集數：

```powershell
python scripts/list_episodes.py --podcast gooaye --limit 10
python scripts/list_episodes.py --podcast gooaye --episode latest
```

下載音檔：

```powershell
python scripts/download_episode.py --podcast gooaye --episode latest
```

CPU 轉錄建議先用 `tiny` 或 `base` 模型驗證流程：

```powershell
python scripts/transcribe_episode.py --podcast gooaye --episode latest --model tiny --device cpu --compute-type int8
```

完整長集數在 CPU 上可能需要很久。若只是要先確認 faster-whisper、ffmpeg/PyAV 與輸出流程可用，可以用短音檔 smoke test：

```powershell
python scripts/transcribe_episode.py --audio-path path\to\sample.mp3 --podcast gooaye --episode smoke-test --model tiny --device cpu --compute-type int8 --force
```

若有 NVIDIA GPU，可在環境支援 CUDA 時嘗試：

```powershell
python scripts/transcribe_episode.py --podcast gooaye --episode latest --model small --device cuda --compute-type float16
```

長音檔建議流程：

```powershell
python scripts/transcribe_episode.py --podcast gooaye --episode latest --model tiny --device cpu --compute-type int8
python scripts/validate_transcript.py --podcast gooaye --episode latest
python scripts/summarize_episode.py --podcast gooaye --episode latest --force
```

CPU 跑 50 分鐘音檔可能很慢。`tiny` / `base` 適合先驗證流程，`small` / `medium` 可用來提升品質。若有 NVIDIA GPU，可嘗試 `--device cuda --compute-type float16`。如果 timeout 後看到殘留高 CPU Python process，先手動停止該 process 再重跑。

產生 deterministic Markdown 摘要：

```powershell
python scripts/summarize_episode.py --podcast gooaye --episode smoke-test --mode extractive --force
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode extractive --max-quotes 5 --window-seconds 300
```

摘要只讀既有 transcript，不會自動下載或轉錄。如果指定 episode 尚無 transcript，CLI 會回報 transcript missing。
如果 transcript 是 partial，summary 預設會拒絕；確定要產出可加 `--allow-partial`。

產生 LLM semantic summary 需要 API key 與 model。手動測試建議用本機 `.env`，此檔案已被 `.gitignore` 忽略，不能 commit：

```text
API_KEY=your-api-key
MODEL=your-model
BASE_URL=https://api.openai.com/v1
```

```powershell
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic --force --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

也可以直接用 CLI 覆蓋設定：

```powershell
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic --model your-model --base-url https://api.openai.com/v1 --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

`semantic` mode 會先執行 transcript validation，並把 transcript 依預設 600 秒與每 chunk 120 segments 分批送給 provider。LLM-facing CLI 預設會載入 `.env`，可用 `--env-file path\to\.env` 指定其他檔案，或用 `--no-env-file` 停用。若 `.env` 與 PowerShell session 都有同名變數，PowerShell session 優先。`MODEL` / `BASE_URL` 是目前建議命名；若未設定，仍會相容讀取舊的 `OPENAI_MODEL` / `OPENAI_BASE_URL`。若缺少 API key 或 model，CLI 會清楚回報設定錯誤；`extractive` mode 不需要 API key。語意摘要不構成投資建議，所有重要市場觀點、公司、人物與事件都應盡量回到 timestamp evidence。

Phase 6U 補上 semantic summary smoke validation。這條路徑在 confirmed execution 會送 transcript text outside this machine；dry-run 只列 planned reads/writes、transcript transfer risk、cost risk 與 required acknowledgement，不呼叫 LLM、不寫 artifact、不輸出逐字稿內容。Confirmed semantic summary smoke 以及 direct `--mode semantic` CLI 都必須提供 exact `api_cost_ack`。CLI stdout 維持 no raw transcript stdout、不顯示 secret value；此階段 no MCP tool changes、no live market API、no automatic cache rebuild、no investment advice。

Phase 6U.1 修正 semantic review guard false positive：semantic summary review 允許 podcast 內容中 speaker 過去買進 / 持有這類 transcript-derived 描述，但仍拒絕直接 buy/sell/hold、建議買進、目標價與保證報酬。Confirmed semantic smoke 也加入 stderr progress，stdout 仍維持 JSON，且 progress 不輸出 raw transcript、prompt、API key 或 LLM response。
Phase 6V adds optional reviewed semantic context for stock lens synthesis. Default synthesis remains `phase-6f-stock-lens-json-only` and does not read `.semantic.md`. When explicitly enabled with `--include-semantic-context`, synthesis may include only matched episode semantic summaries with a latest passed review report; the input boundary becomes `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`. The context excludes `## Chunk Summaries`, does not read raw transcript text, does not read `.env`, does not fetch live market data, and makes no MCP tool changes. Reviewed semantic summary context is an LLM intermediate artifact, not podcast raw evidence and not an external market fact. Phase 6V.1 aligns the deterministic review gate with boundary/context consistency: JSON-only synthesis must have no semantic context, and reviewed semantic synthesis must include non-empty, review-passed semantic context.

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile gb10 --confirm --force --include-semantic-context --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

LLM provider profile 可放在 `config/llm_profiles.yaml`，只保存 provider、model、base URL 與 API key 環境變數名稱，不保存 API key 值。預設 `gb10` profile 使用 `api_key_env=API_KEY`，因此可搭配 `.env` 的 `API_KEY=...` 使用。不要把 API key、token 或 secret 寫進 YAML。

擷取 deterministic mentions：

```powershell
python scripts/extract_mentions.py --podcast gooaye --episode EP672 --force
python scripts/extract_mentions.py --podcast gooaye --episode EP672 --max-evidence-per-mention 3
```

Mention extraction 不使用 LLM，不代表完整語意理解，只依 deterministic rules 從 transcript segments 掃描公司、ticker、產業、總經主題、crypto 與地點等 mention。每個 mention 都會附 timestamp evidence，且不構成投資建議。Phase 3 cache 可將 mentions 匯入 SQLite 並提供基礎跨集查詢；未來 MCP tools 可直接包裝這些 core functions。

產生 deterministic episode intelligence report：

```powershell
python scripts/generate_episode_intelligence_report.py --podcast gooaye --episode EP672 --force
python scripts/generate_episode_intelligence_report.py --podcast gooaye --episode EP672 --window-seconds 600 --max-evidence-per-section 3
```

Episode intelligence report 只讀既有 transcript 與 mentions artifact，不會自動下載、轉錄、摘要、抽 mentions、呼叫 LLM 或查外部市場資料。若 mentions artifact 缺失，報告仍可產生，但會標示 source warning 並讓 mention-derived sections 留空。Partial transcript 預設拒絕；確定要產出草稿可加 `--allow-partial`。

產生 deterministic industry chain / stock candidate mapping：

```powershell
python scripts/generate_industry_chain_mapping.py --podcast gooaye --episode EP672 --force
python scripts/generate_industry_chain_mapping.py --podcast gooaye --episode EP672 --max-candidates-per-node 3 --max-evidence-per-candidate 2
```

Industry mapping 只讀既有 episode intelligence report 與 `config/industry_chain_mappings.yaml`，不會呼叫 LLM 或查外部市場資料。`podcast_explicit` 表示 podcast evidence 中明確提到；`inferred_from_industry` 只代表本機 mapping config 推導出的未查證研究線索，預設 `needs_verification`，不代表股癌明確提到，也不構成投資建議。

產生 external market data boundary scaffold：

```powershell
python scripts/generate_external_data_boundary.py --podcast gooaye --episode EP672 --force
python scripts/generate_external_data_boundary.py --podcast gooaye --episode EP672 --allow-partial
```

External data boundary 只讀既有 industry mapping 與 `config/external_data_boundary.yaml`，不會呼叫外部市場資料 provider、不讀 API key、不產生價格、市值、財報、新聞或公司現況事實。每個 candidate 會標示 `external_verification_status=not_requested`、`source_status=not_fetched` 與 `data_date=null`，並列出後續需要查證的外部資料類型。

使用本機 fixture provider 驗證 external boundary：

```powershell
python scripts/verify_external_data_boundary.py --podcast gooaye --episode EP672
python scripts/verify_external_data_boundary.py --podcast gooaye --episode EP672 --confirm --force
python scripts/verify_external_data_boundary.py --podcast gooaye --episode EP672 --confirm --fixture-path config/external_market_data_fixtures.yaml
```

Phase 6M 只提供 fixture provider scaffold。預設 dry-run 不寫 artifacts；`--confirm` 是 confirm guard，確認後只讀本機 `config/external_market_data_fixtures.yaml` 或指定 fixture path，依 `company_name` / ticker 精準比對並更新既有 `.external-boundary.json/.md`。本階段 no live market API、不讀 API key、不新增 MCP tools、不接 research workflow，也不提供 no investment advice 以外的任何市場建議。

檢查 Gooaye Lens model：

```powershell
python scripts/inspect_gooaye_lens.py
python scripts/inspect_gooaye_lens.py --path config/gooaye_lens.yaml
```

Gooaye Lens model 是 Phase 6F stock lens report 的 deterministic 分析框架來源，定義產業鏈位置、供需與庫存、景氣循環、利率與估值敏感度、資本支出與產能、地緣政治與不確定性等維度。Phase 6E 只載入與驗證本機 config，不接受股票輸入、不寫 artifacts、不呼叫 LLM、不查外部市場資料，也不產生買賣建議、目標價或保證報酬。

產生 podcast-wide deterministic stock lens report：

```powershell
python scripts/generate_stock_lens_report.py --podcast gooaye --stock 台積電 --force
python scripts/generate_stock_lens_report.py --podcast gooaye --stock NVDA --max-evidence-items 5
```

Stock lens report 會掃描該 podcast 既有 `data/mappings/` 與 `data/external/` artifacts，保守比對 candidate 的 `company_name` 與 `tickers`。`podcast_explicit` 會列為 direct podcast evidence；`inferred_from_industry` 只會列為 needs-verification research lead，不代表 podcast 明確提到。若沒有 direct podcast evidence，報告仍會產生並明確標示 `no-direct-podcast-evidence`。此階段不呼叫 LLM、不查外部市場資料、不讀 API key、不新增 MCP tools，也不提供買賣建議、目標價或保證報酬。

產生 Phase 6J Stock Lens LLM Synthesis：

```powershell
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock 台積電
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock 台積電 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock 台積電 --llm-profile gb10 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

Stock lens synthesis 預設 dry-run，只列 planned reads/writes、LLM API/cost risk 與 required acknowledgement，不讀 API key、不呼叫 LLM、不寫 artifacts。Confirmed execution 只把 6F stock lens JSON only 的 compact evidence、lens dimensions、external boundary status 與 warnings 交給 LLM；no raw transcript、no `.semantic.md` input、no external market data lookup、no MCP tool changes，也不接 `run_research_workflow`。LLM 輸出若包含 buy/sell/hold、target price 或 guaranteed return 等投資建議語句，會拒絕寫入 synthesis artifact。

執行 Phase 6O LLM research smoke：

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --model your-model
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model --force
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile gb10 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --force --debug-llm-output
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --include-semantic-summary --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model --force
```

Phase 6O 是 OpenAI-compatible smoke + Codex manual review harness。真實 LLM 呼叫仍走 OpenAI-compatible `/chat/completions`；目前沒有 no direct Codex-session backend，Codex 只作為 manual reviewer 檢查 artifacts、prompt 邊界與品質。Smoke 預設跑 stock lens synthesis 並啟用 fixture external verification；semantic summary 必須明確加 `--include-semantic-summary`，因為它會傳送 transcript text。此階段 no live market data、不新增 MCP tools、不改 investment-advice boundary，也維持 no investment advice。
Phase 6Q 加入 LLM profile config，手動測試可用 `--llm-profile gb10` 讀取 `config/llm_profiles.yaml`。CLI 明確傳入的 `--model`、`--base-url`、`--api-key-env` 會覆寫 profile；YAML 不得包含 API key、token 或 secret 值。Phase 6R 加入本機 `.env` loader，LLM-facing CLI 預設讀取 `.env` 的 `API_KEY`、`MODEL`、`BASE_URL`，並只在 JSON metadata 顯示載入的 env var 名稱，不顯示值。
若要診斷 provider 回覆，可加 `--debug-llm-output`，raw LLM output 只會寫到已由 `.gitignore` 忽略的 `evals/research-llm-smoke/raw/`，不會成為正式 artifact。
Phase 6T 加入 deterministic review report / quality gate。Confirmed smoke 後可用下列命令產生 timestamped review report；它只讀既有 artifacts，no LLM call、no `.env` read、no external market data，也不重寫 synthesis artifacts：

```powershell
python scripts/review_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電
```

LLM smoke 文件與 review template：

Phase 6U semantic summary smoke validation：

```powershell
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile gb10
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile gb10 --confirm --force --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/review_semantic_summary_smoke.py --podcast gooaye --episode EP672
```

- [`docs/research-llm-smoke.md`](docs/research-llm-smoke.md)
- [`evals/research-llm-smoke/phase-6o-llm-smoke-template.md`](evals/research-llm-smoke/phase-6o-llm-smoke-template.md)

Dry-run 或執行本機 deterministic research workflow：

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --stock 台積電
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --include-semantic-summary
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --include-semantic-summary --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --semantic-model your-model
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --include-external-data-verification
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --include-external-data-verification --external-fixture-path config/external_market_data_fixtures.yaml
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --stock 台積電 --include-stock-lens-synthesis
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --stock 台積電 --include-stock-lens-synthesis --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --synthesis-model your-model
```

Research workflow 會先 dry-run，列出 planned reads/writes、step order、semantic LLM 外部 API 風險、cache stale 風險與 confirmation 狀態。預設只執行本機 deterministic steps：`extract_mentions`、`generate_episode_intelligence_report`、`generate_industry_chain_mapping`、`generate_external_data_boundary`，並在提供 `--stock` 時產生 stock lens report。Phase 6I 可用 `--include-semantic-summary` opt in；Phase 6K 可用 `--include-stock-lens-synthesis` opt in，把 stock lens synthesis 放在 stock lens report 之後。Phase 6N 可用 `--include-external-data-verification` opt in，把 fixture verification 放在 external boundary 後、stock lens report 前；此步驟只支援 `--external-data-provider fixture`，只讀本機 fixture，不查 live market API、不讀 API key。Dry-run 只列 semantic / synthesis / fixture plan 與 required acknowledgement，confirmed execution 中只有 LLM 步驟必須提供 exact `--api-cost-ack`。Stock lens synthesis 需要 `--stock`，預設只使用 6F stock lens JSON；Phase 6V 可用 `--include-semantic-context` / `--include-semantic-context-in-synthesis` opt in reviewed semantic context，仍不讀 raw transcript、不查外部市場資料。此 workflow 不自動 rebuild cache、不新增 MCP tools，也不提供投資建議。

重建 SQLite metadata cache 並搜尋：

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 10 --search-mode auto
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 10 --search-mode like --context-segments 1
python scripts/search_mentions.py --podcast gooaye --query 台積電
python scripts/search_mentions.py --podcast gooaye --query 台積電 --type company
```

SQLite cache 是衍生資料，可刪除後重建。原始 source of truth 仍是 `data/transcripts/`、`data/summaries/` 與 `data/mentions/`。Phase 3B 支援 optional SQLite FTS5；若本機 SQLite 不支援 FTS5，或 query 是中文 exact substring，`search_transcripts()` 會使用 LIKE fallback。搜尋結果會包含 `highlighted_text`、實際 `search_mode`，並可用 `--context-segments` 取得命中片段前後文。這一階段仍不做 embedding、vector search 或 LLM search。

啟動本機 MCP server：

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query 台積電 --limit 5 --search-mode auto
python scripts/run_mcp_server.py
```

MCP server 使用官方 Python MCP SDK 的 FastMCP 與 stdio transport，適合 Codex / Claude 本機 MCP client。Read/query tools 是：

- `list_episodes`
- `get_episode`
- `validate_transcript`
- `search_transcripts`
- `search_mentions`
- `rebuild_cache`

Side-effect tools 是：

- `download_audio`
- `transcribe_episode`
- `summarize_episode_extractive`
- `extract_mentions`
- `semantic_summarize_episode`
- `run_research_workflow`
- `run_corpus_episode_completion_workflow`
- `run_corpus_latest_episode_deterministic_workflow`
- `run_latest_episode_verified_research_report_workflow`

本機 reviewed stdio registry 共 15 個 tools。上述 side-effect tools 預設 `confirm=false`，只回傳 dry-run action plan，不會下載、轉錄或寫檔；確認 action plan 後才使用 `confirm=true`。`run_corpus_episode_completion_workflow` 維持 preview → human approval → one explicit action，`run_corpus_latest_episode_deterministic_workflow` 只處理 latest episode 的本機 deterministic stages 並在 semantic summary 前停止。`run_latest_episode_verified_research_report_workflow` 必須先 preview，再由使用者給出相同 canonical `expected_episode_ref` 與 exact `api_cost_ack` 後只 confirmed 呼叫一次。所有 side-effect tools 完成後都不會自動 rebuild SQLite cache，且不提供投資建議。例如：

```text
Call transcribe_episode with confirm=false first to review the action plan.
Call transcribe_episode again with confirm=true only if you accept the runtime and resource cost.
```

MCP responses 使用 JSON envelope：成功為 `{"ok": true, "data": ...}`，錯誤為 `{"ok": false, "error_type": "...", "message": "..."}`。Dry-run action plan 會回傳 `{"ok": true, "dry_run": true, "requires_confirmation": true, ...}`。Side-effect tools 完成後不會自動 rebuild cache；若要讓 search metadata 更新，請手動呼叫 `rebuild_cache`。MCP search、mentions 與 summaries 都不構成投資建議。

`semantic_summarize_episode` 是更嚴格的 API-cost tool。它會把 transcript text 傳送到外部 LLM provider，可能產生 API 費用，因此除了 `confirm=true`，還必須提供 exact acknowledgement：

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

第一次請以 `confirm=false` 呼叫，檢查 dry-run action plan、transcript validation preview、chunk 設定與風險。只有接受外部 API、資料傳送與費用風險時，才用 `confirm=true` 加上 exact `api_cost_ack` 執行。MCP response 不會回傳 API key，也不會在 dry-run 中回傳逐字稿原文。成功後不會自動 rebuild cache；若要讓 SQLite cache 知道新的 `.semantic.md` artifact，請手動執行 `rebuild_cache`。

Phase 6L 加入 `run_research_workflow` MCP exposure。這個 consolidated workflow tool 是 dry-run first：`confirm=false` 只列 planned reads/writes、step order、external API / cost risk、cache stale warning 與 required acknowledgement，不寫 artifacts、不呼叫 LLM、不回 raw transcript、不讀 API key value。`confirm=true` 會呼叫既有 core workflow；若包含 semantic summary 或 stock lens synthesis，仍必須提供 exact ack / `api_cost_ack`。Workflow MCP tool 不查 external market data、沒有 automatic cache rebuild，也不新增買賣建議、目標價或保證報酬能力。

## MCP Client Integration

本專案 MCP server 使用 stdio transport：

```powershell
python scripts/run_mcp_server.py
```

接到 Codex / Claude 類 MCP client 前，建議先跑本機 readiness check：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

Client setup 文件：

- Codex：[`docs/codex-mcp-setup.md`](docs/codex-mcp-setup.md)
- Claude：[`docs/claude-mcp-setup.md`](docs/claude-mcp-setup.md)
- Troubleshooting：[`docs/mcp-troubleshooting.md`](docs/mcp-troubleshooting.md)

這些文件只使用 placeholder path。不要 commit 個人 `.codex/config.toml`、含個人絕對路徑的設定、`.env` 或 API key。

## MCP Tool-use Eval

接上 Codex / Claude 類 MCP client 後，可用 eval prompt suite 檢查工具使用是否符合預期。開始前先跑：

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query 台積電
```

產生一份可填寫的 Codex MCP session eval report：

```powershell
python scripts/new_mcp_eval_report.py --name codex-session-001
```

Eval 文件：

- 流程與 rubric：[`docs/mcp-tool-use-eval.md`](docs/mcp-tool-use-eval.md)
- 可貼到 Codex session 的 prompts：[`docs/mcp-eval-prompts.md`](docs/mcp-eval-prompts.md)
- 實測報告模板：[`docs/mcp-eval-report-template.md`](docs/mcp-eval-report-template.md)
- Phase 5C report 目錄：[`evals/mcp-tool-use/README.md`](evals/mcp-tool-use/README.md)
- Phase 5C Codex session template：[`evals/mcp-tool-use/phase-5c-codex-session-template.md`](evals/mcp-tool-use/phase-5c-codex-session-template.md)

Phase 5B eval 不要求真實呼叫外部 LLM API，也不要求真的執行下載、轉錄、摘要或寫 artifacts；重點是確認 tool selection、dry-run、acknowledgement guard、cache stale 說明與不產生投資建議。Phase 5C 則提供 report capture 流程，讓使用者把實際 Codex MCP session 結果填回 `evals/`。

## Research Safety Eval

Phase 6H 是 LLM 前置 safety gate，用來驗證研究層與未來 LLM workflow 不會幻覺、跳過 `api_cost_ack`、洩漏 raw transcript / API key、把 external boundary 當成已查證市場資料，或產生投資建議。

Research eval 文件：

- 流程與 rubric：[`docs/research-safety-eval.md`](docs/research-safety-eval.md)
- 可貼到 Codex session 的 prompts：[`docs/research-eval-prompts.md`](docs/research-eval-prompts.md)
- Phase 6H report template：[`evals/research-safety/phase-6h-research-session-template.md`](evals/research-safety/phase-6h-research-session-template.md)
- Phase 6O LLM smoke：[`docs/research-llm-smoke.md`](docs/research-llm-smoke.md)
- Phase 6O smoke template：[`evals/research-llm-smoke/phase-6o-llm-smoke-template.md`](evals/research-llm-smoke/phase-6o-llm-smoke-template.md)

Phase 6H 不呼叫 LLM、不讀 API key、不查外部市場資料、不新增 MCP tools，也不改 Phase 6G workflow。Phase 6I 已加入 optional semantic summary execution inside research workflow。Phase 6J 已加入 Stock Lens LLM Synthesis，輸入邊界是 6F stock lens JSON only，必須 exact api_cost_ack，no raw transcript、no external market data、no MCP tool changes。Phase 6K 已加入 workflow opt-in synthesis：`include_stock_lens_synthesis` 只在 workflow confirmed 且 exact ack 後執行 synthesis。Phase 6L 已加入 `run_research_workflow` MCP exposure：dry-run first，confirmed execution 才包裝 core workflow，LLM steps 仍需 exact ack，且 no automatic cache rebuild。Phase 6N 已加入 `include_external_data_verification` optional workflow fixture verification：只支援本機 fixture provider，no live market API、no API key、no MCP tool changes、no automatic cache rebuild，也不提供投資建議。Phase 6O 已加入 research-llm-smoke：real OpenAI-compatible smoke + Codex manual review，exact ack，no direct Codex-session backend、no live market data、no investment advice。Phase 6Q 已加入 LLM profile config：`--llm-profile gb10` 可重用 provider/model/base URL/env var 名稱，但不保存 API key 值。Phase 6R 已加入本機 `.env` secret loader：手動 LLM smoke 可用 `API_KEY`、`MODEL`、`BASE_URL`，CLI metadata 只顯示 env var 名稱、不顯示 secret value。Phase 6T 已加入 research LLM smoke review report / quality gate：confirmed smoke 後可產生 deterministic review artifacts，no LLM call、no `.env` read、no external market data。Phase 6V 已加入 reviewed semantic context opt-in：stock lens synthesis 預設仍是 6F stock lens JSON only，明確啟用後才使用 review-passed `.semantic.md` context，no raw transcript、no live market data、no MCP tool changes、no investment advice。Phase 6V.1 已對齊 review gate boundary/context consistency：JSON-only artifact 不得帶 semantic context，reviewed semantic boundary 必須帶 review-passed context。

## Spec Kit / Architecture

Phase 7A 是 Architecture / Spec Kit Stabilization，範圍是 docs/spec-only。它把目前 Phase 6T 研究系統整理回 spec-kit 可追蹤結構，不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 external market data，也不放寬 no investment advice 邊界。Phase 7A 後，下一個功能性候選階段是 Phase 6U semantic summary smoke 或小型 LLM output-quality tuning。

Phase 7B 是 Official Spec Kit Bootstrap。專案已正式加入官方 `specify init` 等價 scaffold：`.specify` 保存 Spec Kit memory、templates、scripts、workflow 與 integration metadata；`.agents/skills` 保存 Codex skills mode 的 `$speckit-*` skills；`AGENTS.md` 保存 repo-level agent rules。Phase 7B 不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 live market API，也不放寬 no investment advice 邊界。

Phase 7C 是 Spec Kit Constitution + Workflow Alignment。此階段把 `.specify/memory/constitution.md` 從官方 placeholder 專案化，並同步 `.specify/templates/`、`AGENTS.md`、architecture、roadmap 與 spec plan。Phase 7C 是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice。Phase 7C 後，新功能應走 full Spec Kit flow：`$speckit-constitution`、`$speckit-specify`、`$speckit-clarify`、`$speckit-plan`、`$speckit-checklist`、`$speckit-tasks`、`$speckit-analyze`、`$speckit-implement`、`$speckit-converge`；`$speckit-taskstoissues` 只在需要 GitHub issue handoff 時使用。Phase 6U semantic summary smoke 仍是後續可能的功能階段。

Phase 7D 是 Spec Kit Backfill via Full Workflow。此階段用 full Spec Kit flow 將已開發能力做 capability-group backfill：`specs/README.md` 是 registry，`001-gooaye-research-system` 保留為 umbrella product spec，`002-ingestion-transcript-core` 到 `007-spec-kit-governance` 記錄 as-built capability packages，其中 `006-llm-safety-synthesis-smoke-review` 覆蓋 optional LLM/smoke/review gate。Phase 7D 是 docs/spec/tests only：no runtime behavior change、no MCP behavior change、no LLM call、no `.env` read、no live market API、no investment advice，且明確記錄 `$speckit-clarify`、`$speckit-analyze`、`$speckit-converge` 的 backfill 步驟。

Phase 7D.1 是 Spec Kit Active Feature Guidance。此階段補清楚 official Spec Kit command usability：feature packages 的正確位置是 `specs/<feature>`，`.specify/` 是 scaffold/memory/templates/scripts metadata；多個 backfilled packages 不預設 pin 單一 active feature。要對某個 package 跑 official scripts / skills，先設定 `SPECIFY_FEATURE_DIRECTORY`，例如 `$env:SPECIFY_FEATURE_DIRECTORY="specs/003-metadata-search-mcp-core"`；官方 script 可能保存到 `.specify/feature.json`，切換 package 時重新設定即可。Phase 7D.1 不改 runtime、不改 MCP、不呼叫 LLM、不讀 `.env`、不查 live market API，也不提供 investment advice。Phase 6U semantic summary smoke 仍是後續可能的功能階段。

Spec-kit 文件：

- 架構現況：[`docs/architecture.md`](docs/architecture.md)
- 技術計畫：[`specs/001-gooaye-research-system/plan.md`](specs/001-gooaye-research-system/plan.md)
- Data model：[`specs/001-gooaye-research-system/data-model.md`](specs/001-gooaye-research-system/data-model.md)
- Quickstart：[`specs/001-gooaye-research-system/quickstart.md`](specs/001-gooaye-research-system/quickstart.md)
- Agent rules：[`AGENTS.md`](AGENTS.md)
- Agent handoff entrypoint：[`docs/agent-handoff.md`](docs/agent-handoff.md)
- AI development framework：[`docs/ai-development-framework.md`](docs/ai-development-framework.md)
- Verification matrix：[`docs/verification-matrix.md`](docs/verification-matrix.md)
- ADR index：[`docs/architecture-decision-records/README.md`](docs/architecture-decision-records/README.md)

## 開發指令

```powershell
python -m pytest
python -m compileall src scripts
```

若要安裝開發依賴：

```powershell
python -m pip install -e .[dev]
```
