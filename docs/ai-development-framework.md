# AI Development Framework

本文件定義 AI agent（Opus 4.8、GPT-5.5 或未來模型）在本 repo 的開發規範：指令層級、變更分類、驗證要求、patch discipline 與完成報告格式。新 agent 請先讀 `docs/agent-handoff.md`。

## Instruction Hierarchy

由高至低；低層不得與高層矛盾：

1. **User 的明確指示**（含批准範圍與明確不批准清單）。
2. **`AGENTS.md`** — repo-level hard constraints。
3. **`.specify/memory/constitution.md`** — 九大原則與 governance；supersedes conflicting local habits。
4. **`docs/`** — 操作指引（本文件、`docs/agent-handoff.md`、`docs/verification-matrix.md`、ADRs）。
5. **`specs/`** — feature-level 規格（`specs/README.md` 是 registry）。
6. **`tests/`** — 邊界的 executable record。文件與測試矛盾時，先判斷是文件 drift 還是測試 brittle，回報後再改，不得單方面改測試遷就文件。

## Model Role Expectations

- 任何模型接手前：讀完 `docs/agent-handoff.md` 的 First 10 Minutes 清單。
- 不確定邊界時：查 constitution 與對應 guard test，而不是猜。
- 遇到 user 指示與 hard constraint 衝突：停止並回報，不要靜默選邊。
- 完成宣稱必須附實際驗證輸出（見 Completion Report Template）。
- 不得宣稱不存在的 guard、test 或行為；文件主張必須可對應到 repo 內的檔案。

## Feature Lifecycle

新功能必須走 full Spec Kit flow：

```text
constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge
```

`$speckit-taskstoissues` 只在需要 GitHub issue handoff 時使用。何時可以不走 full flow，見 `docs/architecture-decision-records/ADR-0006-spec-kit-governance.md`。

## Definition of Ready（可以開始實作的條件）

- 批准範圍明確：哪些檔案/行為可改、哪些明確不批准。
- 變更已分類（見 Change Classification），對應的 targeted tests 已識別。
- Working tree 乾淨（`git status --short`），preflight checks 通過。
- 若涉及新功能：對應 spec package 存在或已批准直接處理。
- 若涉及 safety boundary：已取得人類批准。

## Definition of Done（可以宣稱完成的條件）

- 變更範圍內的 targeted tests 通過。
- Full checks 通過：`python -m pytest`、`python -m compileall src scripts`、`git diff --check`。
- 只 stage 批准範圍內的檔案（絕不 `git add .`；不 stage `.env`、`data/`、raw LLM output、`.tmp`、`.pytest-tmp`）。
- Completion report 已依模板產出，含實際驗證輸出與 boundary confirmation。
- 未解決的風險已記錄，未擅自擴大範圍處理。

## Change Classification 與 Required Checks

七種變更類型；每類的 targeted tests 以 `docs/verification-matrix.md` 的 Per-change-type 表為準（該表是 source of truth，本文件不重複維護清單）：

| 類型 | 定義 | 額外要求 |
| --- | --- | --- |
| docs-only | 只改 `docs/`、README、AGENTS.md 等文件 | 不改 runtime；docs-only phase 必須有 docs tests 鎖定指引（constitution 原則 IX） |
| spec-only | 只改 `specs/`、`.specify/` | 不留 template residue（`test_spec_kit_backfill_docs.py` 會擋） |
| deterministic runtime | 改 `src/` 的 deterministic 行為 | TDD：先寫 targeted test；不改 public contracts 除非批准 |
| MCP tool | 改 MCP tool 集合、參數或 envelope | tool 集合是 reviewed set（恰 14 個）；同步 `docs/mcp-usage.md` 與 README tool 清單 |
| LLM-facing | 改 LLM provider、prompt、ack、semantic pipeline | 不弱化 ack / no-leak / no-advice guards；不呼叫真實外部 API 測試 |
| side-effect workflow | 改下載、轉錄、artifact 寫入、workflow 步驟 | 維持 dry-run first 與 manual cache rebuild |
| safety-boundary | 改動 `docs/agent-handoff.md` 所列九條邊界之一 | **需人類批准**；評估 constitution 修訂；full pytest |

## Patch Discipline

- Small diff：每個變更可追溯到批准的 task；不順手改相鄰程式碼。
- Targeted tests first，full checks before completion。
- 不引入新依賴、新 build step、新架構模式，除非任務明確需要且已批准。
- 文件變更注意既有 exact-substring docs tests：優先「新增」段落，避免刪改被斷言的文字。
- 新增任何 committable 檔案都會被 repo-wide secret 掃描涵蓋：不得含 secret-like 字樣（`sk-…` 樣式）或內網 endpoint URL。

## Forbidden Actions

除非 user 明確批准，agent 不得：

- 讀取、grep、cat、摘要或提交 `.env`（`.env.example` 是唯一 committable template）。
- 呼叫外部 LLM API、下載音檔、轉錄音檔。
- 新增 live market API 或任何外部 HTTP provider。
- 產生投資建議（buy/sell/hold、target price、guaranteed returns）。
- 自動 rebuild SQLite cache。
- 修改 public API signatures、MCP tool 集合或 envelope。
- 改寫或刪除 `data/`、`evals/` 歷史 artifacts。
- `git add .`、force push、`git reset --hard`、跳過 hooks。
- Key rotation / revocation（human-only）。
- 用大規模 test rewrite 掩蓋文件或行為 drift。

## Completion Report Template

完成任務時，最終回覆至少包含：

1. **Summary** — 實作了哪些 tasks、哪些未實作與原因、是否建立 commit。
2. **Files Changed** — 表格：File / Change Summary / Related Task / Runtime Impact。
3. **Verification** — 表格：Command / Result / Notes；必含 targeted tests、`python -m compileall src scripts`、`python -m pytest`、`git diff --check` 的實際結果。
4. **Boundary Confirmation** — 逐條確認 `docs/agent-handoff.md` 的 Non-Negotiable Boundaries 未被觸碰或弱化。
5. **Git Commit** — commit hash、`git status --short`、staged files summary（若有 commit）。
6. **Remaining Risks / Next Candidates** — 未解決風險與後續建議。

## Rollback / Git Discipline

- Commit 前：`git status --short`、`git diff --stat`、`git diff --check`，逐檔明確 stage。
- 一輪一個聚焦 commit；訊息用 conventional prefix（`docs:`、`test:`、`chore:` 等）。
- 需要回退時：優先 `git revert <hash>` 建立新 commit，不做 history rewrite。
- 發現已 staged/committed 不該入庫的內容（secret、artifact）：停止並回報，由人類決定 rotation 與清理方式。
