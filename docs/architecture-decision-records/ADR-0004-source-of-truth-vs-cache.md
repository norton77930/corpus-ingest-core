# ADR-0004: Source of Truth vs Cache

## Status

Accepted（constitution v1.0.0 原則 I、VIII）

## Context

系統同時有檔案 artifacts（transcripts、summaries、mentions、reports）與 SQLite metadata cache。必須明確哪個是權威資料，否則 cache 會被誤當事實來源，自動 rebuild 也會隱藏副作用。

## Decision

`data/` 下的檔案 artifacts 是 source of truth，deterministic 命名、保留 source paths / status / warnings 可追溯。SQLite cache（`data/cache/`）是 derived index，只服務 search/metadata 查詢。Cache rebuild（`scripts/rebuild_cache.py` / `rebuild_cache` core function）是**手動**操作：side-effect tools 完成後只回 cache stale warning，不自動 rebuild。歷史 artifacts 與 eval reports 是 audit records，不得改寫，除非 user 明確要求 regeneration。

## Consequences

- Cache 損壞或過期可安全重建，不影響事實。
- 寫入 artifacts 的工具之後，search 結果可能暫時 stale——這是設計行為，不是 bug。
- 自動 rebuild 屬 safety-boundary 變更，需批准。

## Guardrails & Tests

- `tests/test_cache_rebuild_guard.py` — confirmed workflow 與 MCP side-effect tools 不自動 rebuild；`rebuild_cache` 引用僅限 reviewed modules。
- `tests/test_cache.py`、`tests/test_search.py` — cache/search 行為。
- `tests/test_contracts.py::test_storage_paths_are_deterministic_and_under_data`。
