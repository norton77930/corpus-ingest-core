# Claude / Grok：044 開發交接

本套件已提供 spec、clarifications、technical plan、research、data model、MCP contract、requirements checklist 與 28 個依序執行的 tasks。**接手從實作開始，不是重做規劃。** 本次沒有修改功能程式碼，所有 runtime tasks 都未勾選。

## 直接貼給開發者

> 請實作 `specs/044-study-guide-mcp`。先閱讀 repo `AGENTS.md`、`docs/agent-handoff.md`、`docs/ai-development-framework.md`，再讀這個 package 的 `spec.md`、`plan.md`、`contracts/study-guide-mcp.md`、`tasks.md` 與 `quickstart.md`。這是已完成開發前置規劃的交接，請沿用既定範圍執行 tasks，不要重新問我是否要做 044，也不要重做 specify/plan。先確認 HEAD 與計畫基準是否有實質漂移；僅在確有矛盾或必要的範圍擴張時提出具體問題。
>
> 請依序完成 28 項任務，以 public Core 的 cover-only byte preservation failing test 起步。每項行為先 focused RED，再最小改動、GREEN 與相關 regression。先保護講義／衍生共用目錄，再加入 append-only Tool26。維持唯一 writer，reviewer 唯讀；保留現有未提交的規劃與其他修改，不要求為了開始而提交／清空工作目錄。不得自行建立 branch、worktree、commit、remote 或 deployment。
>
> 不讀 `.env`，不呼叫真實 LLM、不下載、不轉錄、不操作真實 artifacts，不自動 rebuild cache。保留前 25 個 tools 的契約與順序，保持 Core/CLI result/report schema。完成後執行必要 targeted/full checks、分別審查功能要求與工程／架構邊界，再做 Spec Kit converge；有缺項就繼續完成，最後回報變更路徑、RED/GREEN 證據、完整驗證、skip 原因與風險。不要把 planning-session 測試結果當成你的實作驗證。

## 文件閱讀順序

| 文件 | 用途 |
| --- | --- |
| [spec.md](spec.md) | 14 個 FR、5 個 SC、3 個 P1 user stories，範圍与失敗承諾 |
| [plan.md](plan.md) | 變更邊界、Core/MCP 設計、完整 registry/docs inventory |
| [research.md](research.md) | 已選方案與被拒方案，避免重新猜設計 |
| [data-model.md](data-model.md) | reuse/cover-only/generate/refuse 及 commit 狀態表 |
| [MCP contract](contracts/study-guide-mcp.md) | 精確五參數、preview/confirm/error envelope、固定錯誤文字 |
| [tasks.md](tasks.md) | 28 個可執行任務、依賴、FR/SC coverage |
| [quickstart.md](quickstart.md) | 第一個 RED 與 offline verification 指令 |
| [requirements checklist](checklists/requirements.md)、[safety checklist](checklists/safety-contract.md) | 需求品質，不等於功能測試結果 |
| [workflow record](workflow-record.md) | 本輪正式 Spec Kit scripts 與階段紀錄 |
| [initial assessment](repo-assessment.md) | 上一轮 repo 基準與隔離 probe 證據；是歷史盤點 |

## 接手第一步

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = "specs/044-study-guide-mcp"
.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

接著執行 T001/T002，再從 T003 的 public Core failing check 開始。不要把 study-guide writer 的私有函式 probe 當作足夠的 regression；不要只加 MCP wrapper 就跳過資料保留前置工作。

這台機器請使用 `.\.venv\Scripts\python.exe`，PATH `python` 曾指到相鄰專案環境。以 invocation-local safe.directory 處理 sandbox Git ownership，不更改 global git config。`.specify/feature.json` 是官方 scripts 建立的 ignored selector，不提交。

## 完成邊界

必須交付 Core 保護、可用的 preview/confirm、Tool26 註冊、相關契約與 live docs 更新。不得只交 preview、只交規劃、只交 CLI、或以全部測試通過取代功能驗收。`05/06` 仍是獨立後續操作；沒有一鍵影片全流程、Skill、翻譯、排程、lineage 或併發框架。

目前 `main` 基準仍是 `b42b5a2`；本次只完成規劃文件與 AGENTS 的 plan link，不將新工具／preservation gap 記為已實作。
