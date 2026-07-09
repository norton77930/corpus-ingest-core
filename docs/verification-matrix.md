# Verification Matrix

本文件列出 repo 的 safety / contract guard tests 與各類變更應執行的驗證指令。新的 AI agent 或開發者在宣稱完成前，先跑對應的 targeted tests，再跑 full checks。變更分類定義與完成報告格式見 [`docs/ai-development-framework.md`](ai-development-framework.md)；邊界總覽見 [`docs/agent-handoff.md`](agent-handoff.md)；決策背景見 [ADR index](architecture-decision-records/README.md)。

## Standard full checks

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

pytest 已在 `pyproject.toml` 設定 repo-local basetemp（`--basetemp=.pytest-tmp/run`），請從 repo root 執行。原因：此機器的 `%TEMP%\pytest-of-*` 有損壞的 ACL，且過長的 basetemp 會讓 artifact 路徑超過 Windows 260 字元 MAX_PATH。`.pytest-tmp/` 已被 `.gitignore` 忽略。執行時若出現 `.pytest_cache` 的 `PytestCacheWarning`（本機 ACL 問題），屬無害警告。

## Safety / contract guard tests

| Guard 類別 | 測試檔 | 保護的 invariant |
| --- | --- | --- |
| Secret / private endpoint boundary | `tests/test_repository_secret_boundary.py` | committable 檔案不得含真實樣態 API key（`sk-…`）或內網 endpoint（10.x / 192.168.x / 172.16-31.x URL）；`.env` 永不被讀取 |
| Gitignore / local-only policy | `tests/test_repository_gitignore_policy.py` | `.env`、`.env.*`、local LLM profiles、raw LLM debug output、pytest temp、data/ 生成 artifacts 永不入庫；`.env.example` 保持 committable placeholder template |
| MCP tool registry / docs 對齊 | `tests/test_mcp_tool_registry_contract.py` | MCP 恰好暴露 12 個 reviewed tools；side-effect tools 預設 `confirm=False`；JSON envelope shape；README 與 `docs/mcp-usage.md` 列出全部 tools；MCP workflow wrapper 維持刻意的參數子集（audit F-08） |
| LLM ack guard 一致性 | `tests/test_llm_ack_guard_contracts.py` | CLI/MCP wrappers 在 confirmed LLM 執行前要求 exact `api_cost_ack`；ack 常數單一來源（定義於 `llm_provider`，經 `semantic_summarizer.SEMANTIC_API_COST_ACK` re-export）；core-level guard 已強制（audit F-03 resolved：`semantic_summarize_episode` 進入點與 `create_provider` 建 provider 前驗證） |
| No raw transcript / no secret stdout | `tests/test_llm_cli_no_leak.py` | LLM-facing CLI 的 dry-run stdout/stderr 不含 transcript 原文、API key 值或 prompt 內容；semantic CLI stdout 為鎖定的 metadata-only JSON schema |
| Cache 手動 rebuild | `tests/test_cache_rebuild_guard.py` | confirmed workflow 與 MCP side-effect tools 不自動 rebuild SQLite cache，只回 cache stale warning；`rebuild_cache` 引用僅限 reviewed modules（constitution 原則 VIII） |
| Provider factory boundary | `tests/test_llm_provider_factory_boundary.py` | app code（`src/` 與 `scripts/`）不得直接建構 `OpenAICompatibleProvider(...)`，一律經 `create_provider` 以強制 exact `api_cost_ack` gate；`create_provider` 維持 keyword-only `api_cost_ack`（F-03 後續、Batch 3B） |

Targeted 指令（可合併執行）：

```powershell
python -m pytest tests/test_repository_secret_boundary.py tests/test_repository_gitignore_policy.py tests/test_mcp_tool_registry_contract.py tests/test_llm_ack_guard_contracts.py tests/test_llm_cli_no_leak.py tests/test_cache_rebuild_guard.py tests/test_llm_provider_factory_boundary.py
```

## Per-change-type targeted verification

| 變更類型 | 先跑的 targeted tests |
| --- | --- |
| docs-only | `tests/test_ai_governance_docs.py`、`tests/test_architecture_spec_docs.py`、`tests/test_docs_mcp_eval.py`、`tests/test_research_safety_eval_docs.py`、`tests/test_spec_kit_*.py`、`tests/test_mcp_tool_registry_contract.py`（docs 對齊） |
| spec-only | `tests/test_spec_kit_backfill_docs.py`、`tests/test_spec_kit_constitution.py` |
| deterministic runtime | 對應模組的 targeted tests + `tests/test_contracts.py` |
| corpus artifact index | `tests/test_corpus_index.py`、`tests/test_mcp_tool_registry_contract.py`（確認 v1 不新增 MCP tool） |
| corpus remediation plan | `tests/test_corpus_remediation_plan.py`、`tests/test_mcp_tool_registry_contract.py`（確認 plan-only v1 不新增 MCP tool、不執行 remediation） |
| corpus remediation runner | `tests/test_corpus_remediation_runner.py`、`tests/test_corpus_remediation_plan.py`、`tests/test_corpus_index.py`、`tests/test_mcp_tool_registry_contract.py`（確認 dry-run first、confirmed filter guard、deterministic-only execution、no MCP tool change） |
| corpus local transcription runner | `tests/test_corpus_local_transcription_runner.py`、`tests/test_corpus_remediation_plan.py`、`tests/test_corpus_index.py`、`tests/test_transcriber.py`、`tests/test_mcp_tool_registry_contract.py`（確認 dry-run first、single-episode confirm guard、explicit local audio path、no download、no MCP tool change） |
| MCP tool 變更 | `tests/test_mcp_server.py`、`tests/test_mcp_setup_validation.py`、`tests/test_mcp_tool_registry_contract.py` + 同步 `docs/mcp-usage.md` |
| LLM-facing 變更 | `tests/test_semantic_summarizer.py`、`tests/test_stock_lens_synthesis.py`、`tests/test_research_llm_smoke.py`、`tests/test_*_review.py`、`tests/test_llm_profiles.py`、`tests/test_local_env.py`、`tests/test_llm_ack_guard_contracts.py`、`tests/test_llm_cli_no_leak.py` |
| side-effect workflow 變更 | `tests/test_research_workflow.py`、`tests/test_external_data_verification.py`、`tests/test_cache_rebuild_guard.py` |
| safety-boundary 變更 | full pytest + 上表全部相關列；需人類批准並評估 constitution 修訂 |

任何類型的變更，完成前都要跑 Standard full checks 並引用實際輸出。
