# Feature Specification: Gooaye Research System

**Feature Branch**: `001-gooaye-research-system`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "讓 LLM 讀完股癌 podcast，分析內容與重點，依照產業鏈與股癌提到的線索找到對應股票；建立可自動跑完此流程的 Skill；並能用股癌的觀點分析任意股票。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 單集股癌重點研究報告 (Priority: P1)

使用者想指定一集股癌 podcast，取得一份可閱讀的研究報告。報告要整理本集主題、股癌明確提到的產業鏈線索、公司或股票 mentions、宏觀變數、風險與不確定事項，並且每個重要判斷都要盡量附上 transcript timestamp evidence。

**Why this priority**: 這是所有後續股票 mapping 與股癌觀點分析的資料基礎。如果單集內容沒有被可靠整理，後面的產業鏈與股票分析都會放大錯誤。

**Independent Test**: 可以用一集已完成 transcript validation 的 episode 產生報告，人工檢查報告是否列出主題、mentions、產業鏈線索、timestamp evidence 與不構成投資建議的限制。

**Acceptance Scenarios**:

1. **Given** 一集 podcast 已有完整 transcript，**When** 使用者要求產生 episode intelligence report，**Then** 系統輸出本集主題、產業鏈線索、mentions、風險、不確定事項與 timestamp evidence。
2. **Given** transcript 中沒有提到某個產業或股票，**When** 報告產生，**Then** 系統不得把未提到的股票當成股癌提到的內容。
3. **Given** transcript validation 顯示 missing、corrupt 或 incomplete，**When** 使用者要求產生報告，**Then** 系統拒絕產生正式報告並清楚說明原因。

---

### User Story 2 - Podcast 線索到產業鏈與股票 mapping (Priority: P2)

使用者想知道股癌在一集或多集內容中提到的線索，可能對應到哪些產業鏈節點與股票。系統要區分「podcast 明確提到」、「由產業鏈關係推導」、「需要外部資料查證」三種來源，不得把推導內容包裝成 podcast 事實。

**Why this priority**: 使用者真正想要的價值不是純摘要，而是把 podcast 中的線索變成可追蹤的產業鏈與股票研究入口。

**Independent Test**: 可以用包含「台積電」、「AI」、「GPU」、「利率」等 mentions 的 transcript，檢查 mapping 是否保留 evidence、relation type、confidence 與 needs-verification 狀態。

**Acceptance Scenarios**:

1. **Given** transcript evidence 提到「台積電」，**When** 系統建立 mapping，**Then** 台積電可以被列為明確 mention，並附上 timestamp evidence。
2. **Given** transcript 提到產業鏈主題但未明確提到股票，**When** 系統建立 mapping，**Then** 相關股票只能列為「推導候選」或「需要查證」，不得列為股癌明確提到。
3. **Given** mapping 依賴外部市場資料，**When** 系統輸出結果，**Then** 必須標示資料來源日期或明確標示尚未查證。

---

### User Story 3 - 股癌觀點股票分析 (Priority: P3)

使用者想輸入任意股票，取得一份「用股癌看產業鏈與市場的角度」整理出的分析框架。報告要說明該股票和已知 podcast evidence 的關聯、產業鏈位置、股癌可能會關心的變數、主要風險與需要外部查證的資料，但不得回答應不應該買賣。

**Why this priority**: 這是最接近使用者長期目標的能力，但必須建立在前兩個 user stories 的可靠 evidence 與 mapping 之上。

**Independent Test**: 可以輸入一支已在 transcript 中被提及的股票，檢查報告是否引用 podcast evidence；再輸入一支沒有 evidence 的股票，檢查系統是否明確說明 podcast 資料不足。

**Acceptance Scenarios**:

1. **Given** 使用者輸入一支 podcast 曾提到的股票，**When** 系統產生 Gooaye Lens report，**Then** 報告包含 podcast evidence、產業鏈位置、觀點框架、風險與不確定事項。
2. **Given** 使用者輸入一支 podcast 沒有提到的股票，**When** 系統產生報告，**Then** 報告不得假裝有 podcast evidence，必須標示資料不足並列出需要查證的外部資料。
3. **Given** 使用者詢問是否該買賣某股票，**When** 系統回應，**Then** 系統必須拒絕給出買賣建議，只能整理 evidence、分析框架與需要使用者自行判斷的變數。

---

### User Story 4 - 自動化 Skill 工作流 (Priority: P4)

使用者想透過一個 Skill 或 MCP tool-use prompt，自動執行新 episode 的研究流程，包括檢查 transcript、產生語意摘要、抽 mentions、建立 mapping、產出研究報告，並提示 cache 或資料查證狀態。

**Why this priority**: 自動化能降低重複操作成本，但必須等單集報告、mapping 與安全規則穩定後才適合交給 Skill 串接。

**Independent Test**: 可以用一個已完成 transcript 的 episode 進行 dry-run，檢查系統列出會執行的步驟、會寫入的 artifacts、外部 API 風險與下一步確認方式。

**Acceptance Scenarios**:

1. **Given** 使用者要求 dry-run 新 episode workflow，**When** Skill 執行，**Then** 系統只回 action plan，不呼叫外部 API、不寫入新 artifact。
2. **Given** 使用者確認執行本機 side-effect 步驟，**When** workflow 完成，**Then** 系統提示哪些 artifacts 已產生，以及 search cache 是否需要手動重建。
3. **Given** workflow 中有外部 LLM 或外部市場資料步驟，**When** 使用者未明確確認資料傳送與費用風險，**Then** 系統不得執行該步驟。

### Edge Cases

- Transcript 是空白或無語音 segments 時，系統可以產生空報告，但必須明確標示沒有可分析內容。
- Transcript 是 partial 時，系統預設不得產生正式研究結論；只有使用者明確允許時，才可產生標示為 partial 的草稿。
- Podcast evidence 和外部資料互相矛盾時，系統必須並列差異並標示來源，不得自行消除矛盾。
- 同一公司有多個 ticker、ADR 或不同交易所代號時，系統必須標示 mapping 不確定性。
- 中文公司名、英文公司名、ticker 與常見別名不能被未經驗證地自動合併為同一實體。
- 使用者要求買賣建議、目標價、保證報酬或短線進出點時，系統必須拒絕，並改以 evidence-based 研究框架回應。
- 沒有 API key、外部資料不可用或 provider error 時，系統必須清楚說明缺少哪一段能力，而不是輸出看似完整的報告。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate an episode intelligence report from an already validated podcast transcript.
- **FR-002**: System MUST include timestamp evidence for each important podcast-derived claim whenever source transcript segments are available.
- **FR-003**: System MUST distinguish podcast facts, deterministic mentions, inferred industry-chain candidates, external-data facts, and analyst-facing assumptions.
- **FR-004**: System MUST reject or clearly downgrade reports when transcript validation status is missing, corrupt, incomplete, or partial.
- **FR-005**: System MUST produce a structured list of industry-chain nodes and related stock candidates from podcast clues.
- **FR-006**: System MUST attach relation type and confidence status to each stock or company mapping.
- **FR-007**: System MUST mark externally-derived company or market information with source status and data date when available.
- **FR-008**: System MUST allow users to request a Gooaye Lens report for an arbitrary stock or company.
- **FR-009**: System MUST state when a requested stock has no direct podcast evidence.
- **FR-010**: System MUST refuse to provide buy/sell/hold instructions, target prices, guaranteed returns, or personalized investment advice.
- **FR-011**: System MUST support dry-run planning for automated workflows before any write action, external API call, or long-running operation.
- **FR-012**: System MUST prevent API-cost or external-data-transfer steps unless the user gives explicit confirmation appropriate to that step.
- **FR-013**: System MUST keep raw transcript dumps out of dry-run responses and high-level reports unless the user explicitly asks for bounded excerpts with timestamps.
- **FR-014**: System MUST make report outputs auditable enough for a user to trace conclusions back to podcast evidence or source status.
- **FR-015**: System MUST preserve existing podcast ingestion, transcript, summary, mention, search, and MCP capabilities while adding the research layer.

### Key Entities *(include if feature involves data)*

- **EpisodeIntelligenceReport**: A structured report for one podcast episode, including title, episode ref, transcript status, themes, timeline, claims, mentions, industry clues, risks, and evidence.
- **EvidenceItem**: A traceable source reference containing episode ref, segment id, timestamp, quoted or summarized text, and source type.
- **IndustryChainNode**: A sector, theme, supply-chain role, macro driver, technology, product category, or demand/supply variable discussed or inferred from evidence.
- **StockCandidate**: A company or ticker possibly related to an industry-chain node, with relation type, evidence status, confidence, and verification status.
- **GooayeLens**: A reusable analysis frame describing how Gooaye-style reasoning weighs industry chain position, macro variables, supply/demand, valuation sensitivity, risk, and uncertainty.
- **StockLensReport**: A report for one stock or company using podcast evidence and GooayeLens, including what is known, what is inferred, and what needs external verification.
- **WorkflowRunPlan**: A dry-run description of an automated Skill workflow, including planned steps, inputs, outputs, side effects, external calls, risks, and required confirmations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can produce a complete episode intelligence report for a validated episode in one guided workflow with no more than one explicit confirmation for external LLM use.
- **SC-002**: At least 90% of podcast-derived claims in a generated episode report include timestamp evidence or are explicitly marked as metadata.
- **SC-003**: For a stock directly mentioned in a transcript, the stock lens report identifies at least one podcast evidence item or explicitly states why evidence is unavailable.
- **SC-004**: For a stock not mentioned in available podcast data, the system clearly states "no direct podcast evidence found" instead of fabricating a connection.
- **SC-005**: In evaluation prompts asking whether to buy a stock, the system refuses direct investment advice 100% of the time while still offering an evidence-based research framework.
- **SC-006**: Dry-run workflow responses never write files, never call external APIs, and always list planned writes, external-transfer risks, and required confirmations.
- **SC-007**: Reports separate podcast evidence, inference, and external verification status clearly enough that a reviewer can classify each major claim into one of those categories.
- **SC-008**: Existing Phase 1 through Phase 5 commands and tests continue to pass after each implementation phase of the research layer.

## Assumptions

- The first target podcast is Gooaye 股癌, but the underlying evidence model should not hard-code a single podcast where a generic podcast id can be preserved.
- The existing transcript validation, semantic summary, mention extraction, SQLite cache, search, and MCP tools remain the source foundation for the research layer.
- This feature is an investment research assistant, not a trading system and not a personalized financial advisor.
- External market data will be treated as volatile and must be timestamped or clearly marked as requiring verification.
- The first production-quality workflow should optimize for traceability and safety over recall; missing a possible stock candidate is preferable to hallucinating one.
- The first automated Skill can start with already-ingested episodes; automatic RSS ingestion, scheduled jobs, and background processing are out of scope for this feature spec.
- Semantic LLM use is allowed only through explicit API-cost and external-transfer acknowledgement.
