# Grok / Hermes 接手說明

2026-10-08。此次交付包含 SPEC044–058 累積實作、測試、Skill 與規格。請先確認收到包含本文件及 `scripts/verify_learning_mcp.py` 的交付版本；記錄 `git rev-parse HEAD`、工作目錄狀態與實際 Python/MCP/Hermes 版本。遠端為 `norton77930/corpus-ingest-core`，分支 `main`。

## 已有功能

| 範圍 | 可做的事 |
|---|---|
| Podcast / YouTube / X | 來源擷取、本機轉錄、逐字稿與時間段查詢 |
| 學習內容 | 講義、工作流程衍生、來源版本與恢復狀態、下一步建議及單步推進 |
| 自然語言入口 | 已備妥來源直接問答；新影片先預覽準備計畫，經核准後提交背景工作；查狀態與明確繼續整理 |
| 固定學習筆記 | 說明原文議題、講者理由及例子、值得回聽段落；AI 補充獨立標示，專案套用由使用者另行要求 |
| 移植驗證 | 指定資料根目錄或既有 loopback MCP，核對來源版本及分頁；檢查完整 Skill 資源 |

完整 MCP registry 為 **35 tools**。學習入口可只向 Hermes 暴露同一個 server 的三個 native tools：`prepare_learning_source`、`inspect_source_preparation_job`、`query_source_content`。請依實際 Hermes 版本確認篩選方式；篩選後的 registry 可能只有3個，不代表完整 server 應變成3個。

## 接手順序

1. 閱讀 `AGENTS.md`、`docs/agent-handoff.md`、`docs/ai-development-framework.md`。SPEC058 開發任務已完成；實際主機驗收另行記錄，不以 repository 測試代替。
2. 確認 VM 的既有環境、資料根目錄及 transport。不得假設本機 `.pytest-tmp/54m/data` 存在於 VM。不要覆寫 VM 的工作目錄修改、設定或歷史資料；若需要更動設定或搬來源，先列出具體變更。
3. 掛載完整 `source-learning-entry`、`source-preparation`、`source-content-qa` Skill 目錄及其 references，並確認 Hermes 已載入。唯一學習筆記範本為 `.agents/skills/source-content-qa/references/learning-notes-template.md`。
4. 執行 `python scripts/verify_learning_mcp.py inventory`。這只檢查檔案，不能證明 Hermes 已載入。
5. 對 VM 已備妥的一個明確來源，執行 `verify --data-dir <實際資料根目錄> --podcast <ID> --episode <REF> --start <秒> --end <秒>`；也可改用 `--mcp-url http://127.0.0.1:<既有埠>/mcp`。兩種連線擇一。這驗證選定段落的送達，不驗證答案正確性。
6. 再直接透過 Hermes 提問，記錄實際 Tool trace、來源 ID/version、涵蓋範圍及回答。不要把獨立 SDK 成功結果記成 Hermes 驗收通過。

## 尚待實際環境驗收

- 本機已有測試來源：X `https://x.com/NateWiki/status/2106893534980685927`，ID `x-natewiki` / `2106893534980685927`。已記錄 medium / CUDA / float16 / VAD=true。VM 需另行核對硬體與設定，不可默默改成 tiny 或 CPU。
- 本機獨立 SDK 已讀取11頁、1088段、60834字元，來源檔案保持不變。但目前掛載的 MCP inspect 回覆 `source_missing`；URL preview 回覆 `metadata_unavailable`。原因尚未確認，不要直接認定為資料根目錄錯誤，也不要用重新下載掩蓋。
- 新來源：一次 preview，揭露模型與下載/轉錄影響；取得本次來源與 plan 綁定的明確核准後，confirm 一次並停止。Windows stdio 的背景提交可能被 `worker_host_incompatible` 擋住；需要另外確認既有相容主機。
- 「處理好了嗎？」只查一次狀態；「繼續整理」才銜接同一來源的已備妥內容。不得自動輪詢、重試、串接下一步或重建 cache。
- 用 [三題驗收表](../specs/058-learning-mcp-acceptance/content-acceptance.md) 檢查 TDD、追問、米其林廚房的回答與回聽段落，區分講者內容與 AI 補充。
- SPEC058 OP001–003、SPEC057 T017/T018 仍待真實人工/主機證據，不能因這次 commit/push 自動勾選。

## 已有驗證證據

完整測試2917 passed、27 skipped，exit0；全部 skip 為 Windows 無法建立 symlink 的 OSError。完成狀態更新後另有54 passed / 1 skipped及18 passed；compileall、diff check通過。提交前 secret/ignore/交付文件與 registry 檢查另有55 passed、0 skipped，exit0。全套測試後沒有程式或測試變動。沒有呼叫真實 LLM provider 或新提交下載/轉錄工作。

詳細命令、RED/GREEN、獨立審查、來源保留與限制見 [SPEC058 實作紀錄](../specs/058-learning-mcp-acceptance/implementation-log.md)；操作參考 [quickstart](../specs/058-learning-mcp-acceptance/quickstart.md)。`.env`、音檔、逐字稿、cache、`.pytest-tmp` 和本機模型皆不屬 Git 交付內容。
