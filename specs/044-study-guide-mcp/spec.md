# Feature Specification: Safe Study-guide MCP Access

**Feature**: `044-study-guide-mcp`
**Created**: 2026-10-02
**Status**: Implemented
**Baseline**: `b42b5a2`
**Input**: 使用者要求確認 repo 現況並規劃下一階段 SPEC，交由 Claude 或 Grok 開發；2026-10-02 續示「我說是交給claude / Grok 開發, 請進行下一步」，本次將 044 補成可執行的開發交接套件。

## Purpose and Scope

讓已連接 MCP 的使用者，從**已存在的 learning-notes semantic summary** 預覽並產生 `00/03/04/07` 學習講義。完成後，使用者可另行要求既有 `derive_workflow_bundle` 產生 `05/06`。這兩個操作各自確認，不自動串接。

目前 Spec 038 的講義核心與 CLI 已存在；Spec 043 已將下游工作流衍生公開為 MCP Tool 25，但講義沒有 MCP 入口。下一階段只補齊這個入口，以及公開入口前必要的共用目錄保護。

講義與工作流衍生是不同 artifact families，卻共用 bundle directory。基準版本的講義 directory replacement 只放入四份講義，會移除同目錄的 `05/06`。本規格要求：補封面時保留其他檔案；既有衍生檔存在時，拒絕重生其上游講義。不得把保留檔案誤稱為已驗證它仍對應新的講義。

## Clarifications

### Session 2026-10-02

本輪正式 clarify 掃描未發現需要使用者重新選擇的產品範圍問題；新增問答數為 0。使用者已指定交給 Claude／Grok 開發，本輪完成規劃，不代做 runtime implementation。以下為依 repo 證據收斂的技術定義，不冒充使用者逐項回答：

- 補封面是只新增 `00`；`03/04/07`、`05/06` 與其他安全的一般檔案須 raw-byte 保留，包含 CRLF、BOM 與非 UTF-8 bytes，不能解碼再編碼。
- 任何操作發現事先存在的同 bundle `.part`／`.old`／`.wfderive.part`／`.wfderive.old` 都拒絕，包括 preview/reuse；不觸碰殘留物、不自動 recovery。這是 runner preflight gate，不改底層既有恢復協定。
- Cover-only 沿用缺少或一般檔案 `00` 未通過 bounded UTF-8 readability 的情境；若是 filesystem/permission/safety 錯誤则拒絕，不把錯誤視為覆寫授權。
- Canonical transcript JSON 允許在本機讀取以取得 identity/title，並列入 planned reads；其 segments/body 不進 provider。這不是「完全不讀 transcript 檔案」的保證。
- 成功把完整 staging rename 成公開 bundle 是 publication commit point。commit 前單一故障需回復舊 bundle；commit 後清理或 run-report 故障不得宣稱 rollback，必須回報新完整 bundle 已發布且停止。
- rollback 本身也失敗時，保留可回復舊資料與 staging、回報 recovery required；不能承諾檔案系統持續故障下仍可恢復公開路徑。
- baseline 工具總數仍為 25；本次規劃的交付是新增第 26 個工具所需 plan/tasks/contracts，不是修改現有 registry。

## User Scenarios & Testing

### User Story 1 — 在 agent 中預覽講義 (Priority: P1)

使用者指定一個來源與 episode，想知道講義是否可產生、哪些檔案會被重用、哪些操作需要 LLM。

**Why this priority**: 現有 agent 路徑在講義這一步需要退回終端機。

**Independent Test**: 使用合成 semantic summary，直接呼叫新工具的預覽路徑，對照檔案樹與 provider/network sentinels。

**Acceptance Scenarios**:

1. **Given** 合法 learning-notes summary 且沒有講義，**When** 預覽，**Then** 列出來源讀取、四份輸出、確認後的 LLM 需求與報告寫入，零寫入、零網路、零 provider construction。
2. **Given** 四份講義完整，**When** 預覽且未指定 force，**Then** 列為重用，不誤稱需要 LLM；清楚區別講義不重寫與 confirmed run report 仍會寫入。
3. **Given** `03/04/07` 完整而僅缺 `00`，**When** 預覽，**Then** 說明只補封面、不呼叫 LLM，現有講義和衍生檔不會被移除。
4. **Given** 缺 summary、finance profile、未知來源或不合法 episode，**When** 預覽，**Then** 回傳結構化且不洩漏本文的錯誤，沒有副作用。

### User Story 2 — 明確確認一份講義 (Priority: P1)

使用者確認單一 episode 的講義工作；有 LLM 需求時提供既有 exact acknowledgement。

**Why this priority**: 必須可從預覽走到可使用的講義，而非只增加查詢。

**Independent Test**: 以 fake provider 走 MCP → 真實 Core → 隔離 artifact directory，驗證四份檔案及 metadata-only 回應。

**Acceptance Scenarios**:

1. **Given** 新產生或允許的強制重生，**When** exact `api_cost_ack` 缺失或不符，**Then** 在 provider construction 前拒絕，不寫講義或報告。
2. **Given** 合法來源與 exact ack，**When** confirm，**Then** 產生 `00/03/04/07` 與既有格式的 run report；不產生 `01/02/05/06`，不執行下載、轉錄、semantic summary 或 cache rebuild。
3. **Given** 完整講義且 force=false，**When** confirm，**Then** 重用四檔，不需 ack、不建 provider；仍允許寫既有 metadata-only run report。
4. **Given** 只缺封面，**When** confirm 且沒有 ack，**Then** 補封面成功，`03/04/07` 及既有 `05/06` 的位元組保持不變。

### User Story 3 — 保護既有衍生與其他檔案 (Priority: P1)

使用者先產生講義，再產生工作流衍生，之後操作講義時不應默默失去已完成的內容。

**Why this priority**: 這是已用隔離假資料確認的資料保留缺口，公開 MCP 前必須處理。

**Independent Test**: 講義目錄放入四份講義、兩份衍生與一份額外 sentinel，逐一測試重用、補封面、force、部分檔案、失敗回復。

**Acceptance Scenarios**:

1. **Given** 有任一 `05` 或 `06` 衍生檔，**When** force=true 或其他將重生 `03/04/07` 的請求，**Then** preview 與 confirm 都拒絕，provider 呼叫與檔案變更皆為零。force 不能繞過。
2. **Given** 沒有衍生檔、但有其他一般檔案，**When** 允許的重生成功，**Then** 只替換講義擁有的四份檔案，其餘檔案位元組不變。
3. **Given** 補封面或允許的重生在 publication commit 前發生單一寫入／rename 失敗，**When** 回傳失敗且 recovery 操作可用，**Then** 已存在的公開 bundle 恢復或保持原狀；rollback 也失敗則保留舊資料並明示 recovery required，不誤報成功。
4. **Given** 目錄含 symlink、junction、reparse point 或非預期子目錄，**When** 需要替換目錄，**Then** fail closed，不跟隨連結、不遞迴複製，也不移除目標內容。
5. **Given** publication 已完成而後續 cleanup／run-report 寫入失敗，**When** 回傳結構化失敗，**Then** 說明完整 bundle 已發布，不 rollback、不重試、不再呼叫 provider；留存殘留物供人工處理。

### Edge Cases

- 只有 `05` 或只有 `06`：同樣視為既有衍生，禁止上游重生。
- 缺部分 `03/04/07`：沿用既有 partial refusal；即使 force=true，只要有衍生仍拒絕。
- 全套重用仍須符合既有來源/profile 驗證，不因檔案存在而跳過既有 Core gate。
- `latest`、`next`、空識別或路徑穿越字串：不進行來源探索，對新 MCP surface 結構化拒絕。
- 不宣稱舊講義與目前 summary 的內容新鮮度；目前沒有來源 digest lineage，另案處理。
- 若事先已有同 bundle `.part` / `.old` / `.wfderive.part` / `.wfderive.old`，所有 runner 操作均 fail closed，不讀取其本文、不刪除、不改名、不 recovery；底層 helper 既有 recovery 協定不重設計。
- unsafe path 包含 bundle 及其到 configured storage root 的路徑元件；source summary 亦須於讀取前驗證安全路徑與一般檔案。檢查採 no-follow metadata，不以 resolve 後的路徑抹去連結證據。
- 額外一般檔案只保留 bytes，不宣稱內容已驗證或仍對應目前講義；不強制保留 mtime、ACL 或 inode。目錄內容檢查同樣適用 preview/reuse，避免讀取不安全 owned files。
- 同時寫同一 bundle 不在 v1 保證範圍；使用者應序列化操作。不得聲稱跨行程併發安全。

## Safety and Data Boundaries

- 只處理本機既有 semantic summary；不將 transcript 傳送到新的 LLM 路徑。
- preview 零寫入、零網路，不讀 `.env`、不解析 provider 憑證。
- exact `api_cost_ack` 由 Core 在實際需要 LLM 時把關，wrapper 原樣傳遞，不額外要求純重用／補封面提供 ack。
- MCP 不收 provider、model、endpoint、credential、input/output path override。
- 回應只含狀態、路徑、計畫、警告等 metadata；不得含 summary、prompt、LLM 原文、secret 或 traceback。
- no live market API；no investment advice；manual cache rebuild。原有 finance prompt、semantic envelope、artifact ladder 保持。
- 修改限於新工具、講義目錄保留／拒絕邏輯及必要 tests/docs。不得改寫真實 `data/` 或 `evals/`。

## Requirements

### Functional Requirements

- **FR-001**: 提供單一 episode 的 study-guide MCP 操作，預設 preview，confirm 與 force 均需明確指定。
- **FR-002**: preview 必須準確列出 reads、artifact writes、reuses；confirmed run-report writes 必須單獨明示，避免「重用」被誤認為完全零寫入。
- **FR-003**: preview 保持零寫入、零網路、零 provider，並標示 `network_read=false`。
- **FR-004**: confirm 只委派一次既有講義 Core；wrapper 不產生講義、不自動串接其他 tool。
- **FR-005**: 新生成與允許的 force 需要 exact ack；完整重用與僅補封面不需要。兩層均不得合成或改寫使用者 ack。
- **FR-006**: 既有 `05/06` 的任一檔存在時，會重生 `03/04/07` 的操作必須在 preview/confirm 一致拒絕；拒絕不得寫檔或建 provider。
- **FR-007**: 補封面與其他允許的寫入不得移除非講義擁有檔案；保持其位元組，拒絕不安全目錄內容；失敗時保護原 bundle。
- **FR-008**: 只產生既有四份講義與 run report，不新增 artifact family、依賴、設定格式或自動 cache 行為。
- **FR-009**: 新工具參數僅限 `podcast_id`、`episode_ref`、`confirm`、`force`、`api_cost_ack`；錯誤與成功沿用現有 MCP envelope。
- **FR-010**: 新工具 append-only；目前 25 個工具的名稱、順序、簽章與 envelope 不變。實作後總數為 26；本次規劃不修改 live registry。
- **FR-011**: confirmed response metadata-only；既有 warnings 原樣保留。新增預览 LLM 說明需符合實際分支，不可說每次 confirm 都會呼叫 LLM。
- **FR-012**: 操作文件提供「已有 summary → preview → confirm → 另行要求 derivation」範例，明確說明此期没有一鍵從影片產生全套講義。
- **FR-013**: 明確 episode identity、安全 source/bundle path 與既有 recovery remnants 必須在 summary/lecture 本文、provider 或 writer 前檢查；identity metadata 可先安全讀取以定位 bundle。不安全目錄項目及四種 recovery siblings 預先存在時，preview/confirm/reuse 均零副作用拒絕；每份檔案的安全檢查先於其 bytes 讀取。
- **FR-014**: publication failure 必須分清 commit 前 rollback、rollback 失敗的 recovery-required、commit 後 published-but-incomplete-report/cleanup；錯誤訊息使用固定安全文字，不包含例外原文、本文或憑證，且禁止自動 retry。

### Key Entities

- **Lecture bundle**: `00_video_info.md`、`03_full_summary.md`、`04_learning_notes.md`、`07_final_study_guide.md`。
- **Workflow derivation**: 同目錄的 `05_prompt_examples.md` 與 `06_apply_to_my_workflow.md`，由既有不同 family 管理。
- **Operation plan**: 單一來源/episode、讀取、講義寫入、重用、報告寫入、是否需 LLM 與警告。
- **Run report**: 沿用 Spec 038 的 JSON/Markdown 執行 metadata，不包含生成本文。

## Success Criteria

- **SC-001**: 使用者可在無終端機操作下，從既有 learning-notes summary 完成一次 preview 和一次確認，取得四份講義的結果路徑。
- **SC-002**: 全部 preview 情境的檔案樹前後相同，provider/network 呼叫數均為零。
- **SC-003**: 全部 ack/refusal 情境在受保護動作前停止；重用與補封面能在沒有 ack 下成功且不呼叫 LLM。
- **SC-004**: 保留矩陣中的非講義檔案全部 byte-identical；禁止的上游重生全部 fail closed。
- **SC-005**: 既有工具全數相容；完整測試、編譯與 diff 檢查通過，任何未執行檢查均明示原因。

## Assumptions and Non-goals

- 優先改善 agent 學習流程；RSS learning-notes 同樣受支援，不新增來源限制。
- 不新增 Skill；先交付可驗證工具，再按真實使用需要規劃 portable Skill。
- 不含影片取得、semantic summary 自動產生、多集批次、排程、Web UI、embedding、翻譯 `01/02`、跨集綜合或額外 provider。
- 不自動刪除、搬移、失效標記或重新產生既有衍生；既有衍生阻擋上游重生時，只解釋原因，不指示 agent 擅自清理。
- 預設沿用已設定的 provider；本規格與其開發測試不授權真實 LLM 呼叫。
- Constitution 1.0.1 九項原則已對照，不需放寬；本套件明確界定單一 append-only MCP 新工具，其他工具與邊界不變。規劃完成後交由使用者指定的 Claude／Grok 實作，不另要求重做已完成的規劃。

## Workflow Status

本輪依正式 skills 與官方 scripts 完成開發前置流程，執行證據見 `workflow-record.md`。接手者從 `handoff.md` 與 `tasks.md` 開始實作，不重跑規劃；只有實際基準漂移或需求改變時才重開對應步驟。Implementation / converge 留給 Claude／Grok；本套件不得被標為功能已實作。
