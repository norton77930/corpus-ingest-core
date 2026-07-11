# ADR-0006: Spec Kit Governance

## Status

Accepted（constitution v1.0.0 Spec Kit Development Workflow、原則 IX）

## Context

Repo 用官方 Spec Kit scaffold（`.specify/`、`.agents/skills`、`specs/`）管理功能開發。需要明確：什麼變更必須走 full flow、什麼可以直接處理、文件指引如何防 drift。

## Decision

- 新功能性工作（runtime / MCP / LLM / side-effect）必須走 full Spec Kit flow：`constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge`，feature package 放 `specs/<feature>`。
- 小型 docs/test 修正若由 user 提供 concrete plan，可直接處理，但必須遵守 constitution，且 docs/spec-only phase 必須有 docs tests 鎖定指引（原則 IX）。
- `specs/001-gooaye-research-system` 是 umbrella product spec；`002`–`007` 是 backfilled as-built capability packages；`specs/README.md` 是 registry。
- 對單一 package 操作前用 `SPECIFY_FEATURE_DIRECTORY` 選 active feature；它是明確 selector 且優先於 persisted local state。Official scripts 可把選擇寫到 `.specify/feature.json`。
- `.specify/feature.json` 是 local-only workflow metadata，必須保持 gitignored 與 untracked；不得讓一個本機選擇變成 repository-wide active feature pin。

## Consequences

- 功能變更有 spec 追溯；docs 修正保持輕量但仍有測試鎖定。
- 新 spec package 需更新 `specs/README.md` registry 與 mapping 表。
- Constitution 修訂需 Sync Impact Report 並傳播到 templates / docs / tests / agent instructions。
- Clean clone 不需要包含 `.specify/feature.json`；設定 `SPECIFY_FEATURE_DIRECTORY` 或執行 official script 即可建立/更新 ignored local selection。
- Secret/committable surface guards 排除這個 local-only file，但仍掃描其他 tracked `.specify/` scaffold。

## Guardrails & Tests

- `tests/test_spec_kit_constitution.py` — constitution 專案化、版本化、與 templates 對齊。
- `tests/test_spec_kit_bootstrap.py` — scaffold 與 AGENTS.md 規則存在。
- `tests/test_spec_kit_backfill_docs.py` — registry 完整、packages 無 template residue、safety boundaries 記錄在案。
- `tests/test_ai_governance_docs.py` — governance docs（handoff / framework / ADRs）存在且含關鍵邊界。
- `tests/test_repository_gitignore_policy.py` 與 `tests/test_repository_secret_boundary.py` — selector file 必須 gitignored、untracked，且不屬 committable scan surface。
