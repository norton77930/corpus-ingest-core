# Repository Assessment — 2026-10-02

> 本文件保存第一輪盤點的歷史證據。後續使用者要求完成開發交接，已擴充完整 plan/tasks/contracts 並更新 AGENTS plan link；目前交接狀態請看 [workflow record](workflow-record.md) 與 [handoff](handoff.md)，勿把下方第一輪「只新增四份文件」當作後續變更清單。

## Scope and Baseline

本次是程式碼、文件與隔離測試的本機盤點，不是 production corpus 品質稽核；沒有讀 `.env`、沒有讀真實 transcript 本文、沒有真實 LLM／下載／轉錄、沒有 cache rebuild。

- Branch: `main`；HEAD: `b42b5a2c765ac41b8e22134a2752928f8d40443e`。
- 初始 working tree 乾淨，沒有 staged/untracked change。
- 相對本機 `origin/main` ahead 1；未 fetch，因此不是遠端即時狀態。
- HEAD 修復 workflow derivation `05/06` 的目錄發布及重用警告。
- Package version: `0.2.0`；最高既有 package: 043。
- 直接載入 live registry：25 個工具，最後為 `derive_workflow_bundle`；沒有 `study_guide` 工具。

## What Exists

RSS、X 與 YouTube ingestion；本機轉錄；deterministic 與 opt-in semantic summary；finance / learning-notes profiles；SQLite search；verified research report 與 catalog/coverage/gap backlog；study-guide lecture `00/03/04/07`；workflow derivation `05/06`；stdio/loopback HTTP MCP。

根據 source、specs 036–043 與 targeted tests 判斷，036–043 並非下一階段待開發項。`01/02` 翻譯、Web UI、排程、embedding/vector search 仍不在既有功能中。

## Findings that Affect Priorities

1. **Product gap**：Spec 038 lecture 只公開 Core/CLI；Spec 043 卻已公開依賴 lecture 的 derivation tool。新增 lecture MCP 可補齊一段實際操作流程。
2. **Preservation gap**：`study_guide_bundle._atomic_write_bundle` 以只含講義四檔的 staging directory 替換整個 bundle；`storage.workflow_derivation_paths_from_stem` 把 `05/06` 放在同一目錄。本次隔離 writer probe 輸出 `derivation_05_preserved=False`、`derivation_06_preserved=False`。這證明 writer seam，尚不是完整 public runner regression；044 的第一項 RED 必須補 public Core 測試。
3. **Document drift**：`AGENTS.md` 仍提 042 為 in-progress；registry 與 source 已到 043。handoff 的 DATA_DIR fail-fast 後續事項已存在於 `tests/conftest.py::pytest_configure`，不應再當新功能做一次。roadmap 的舊 024 latest 描述與後列 043 並存，不能只取第一個「latest」。本次記錄，不順手改歷史文件。
4. **Environment**：PATH `python` 是 `loopplane/.venv`，pytest 在 import `feedparser` 時中止；本 repo `.venv/Scripts/python.exe` 可正常執行 targeted suite。不需安裝新依賴或修改全域設定。

## Candidate Comparison

| 順序 | 候選 | 決策 |
| --- | --- | --- |
| 1 | 044 Safe Study-guide MCP Access | 建議：補現有流程缺口，附最小目錄保護，無新 provider/dependency |
| 2 | 講義／衍生 portable Skill | 待 044 可用後按使用需求規劃；保持每次一個確認動作 |
| 3 | Bundle source lineage/currentness | 獨立 spec；需要來源 digest、reuse 與再生政策，不塞進 wrapper 功能 |
| 延後 | 跨集語義整理、翻譯、Web UI、排程 | 新 artifact/成本/權限或部署面較大，本次沒有支持其優先於現有缺口的需求證據 |

不預先占用 045/046 編號。Known-risk 文件中的已完成項不列為新開發。

## Verification Record

- 初始 targeted（錯誤 PATH interpreter）：pytest configuration 失敗，`ModuleNotFoundError: feedparser`，沒有測試結果。
- 本 repo interpreter targeted：`test_spec_kit_backfill_docs`、`test_spec_kit_constitution`、`test_study_guide_bundle`、`test_workflow_derivation`、`test_mcp_workflow_derivation`、`test_mcp_tool_registry_contract`：**72 passed in 22.69s**。
- `python -m compileall -q src scripts`（本 repo interpreter）：exit 0。
- Full suite 與文件完成後檢查結果見本文件末尾的 Final Verification；不得用上述 targeted 結果代稱 full suite 通過。

## Changes and Limits

只新增 `specs/044-study-guide-mcp/` 的 proposed spec、需求 checklist、handoff 與此盤點；在 `specs/README.md` 登記 proposed package。無 runtime、config、test behavior 或 MCP registry 修改；無 commit、branch、worktree、remote、release 或 deployment。

本次沒有批准或實作新 MCP tool，也沒有修復 preservation gap。成功標準是可評估、可交接的規格；功能完成需由接手者另外提出實作與驗證證據。

## Final Verification

- Full baseline: `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/spec044-full` → **1520 passed, 36 skipped in 514.78s**，exit 0。Skipped 不計為通過。
- Compile: `.\.venv\Scripts\python.exe -m compileall -q src scripts` → exit 0。
- Diff hygiene: `git -c safe.directory=D:/SourceCode/CORP/FASBD/NewProd/GitHub/podcast-ingest-core diff --check` → exit 0。
- 四份新增 planning documents 的相對連結與 template-residue 檢查通過。
- Full run 在規劃文件完成前啟動；最終文件另跑 `test_spec_kit_backfill_docs.py`、`test_spec_kit_constitution.py`、`test_docs_registry_count_consistency.py`、`test_repository_secret_boundary.py`：**17 passed in 120.52s**，exit 0（本 repo interpreter，`--basetemp=.pytest-tmp/spec044-docs-final`）。
