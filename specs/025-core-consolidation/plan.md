# Implementation Plan: Core Consolidation

**Date**: 2026-08-08 | **Spec**: [spec.md](spec.md)

## Summary

Six dependency-ordered, independently revertible batches consolidating D1–D5 debt behind a behavior freeze. Acceptance anchor: `tests/test_mcp_tool_registry_contract.py` unmodified and green throughout.

## Constitution Check

No amendment. Principle II (stable core contracts) is the epic's core FR; Principle IX satisfied by characterization-first and guard tests; no LLM/secret/cache/advice surface touched.

## Batches

| Batch | Size | Content |
| --- | --- | --- |
| B1 | S | `tests/conftest.py` (opt-in reflective `tmp_data_dirs`), `storage.DATA_DIR` env override (`PODCAST_INGEST_DATA_DIR`, inert by default), guard tests, 1–2 exemplar migrations |
| B2 | M | Characterization truth table first; `path_safety.py` shared skeleton (`allow_absolute` profile); four runners become thin wrappers keeping names + round-trips; boundary guard |
| B3 | M | `run_report_io.write_part_staged_report_pair` byte-equivalent extraction of the 5 weak `.part` writers; error mapping stays per-runner; boundary guard |
| B4 | L | `mcp_runtime.py` (single `FastMCP` + envelopes/redaction) + 4 tool-group modules (1–6 read / 7–12 side-effect / 13–16 corpus workflows / 17–21 verified-report queries); `mcp_server.py` = facade (import order = registration order; full tool + dependency-alias re-exports); completion triple-validation collapsed via `confirmed_request_rejection_reason`; facade guard |
| B5 | M | Registry-derived doc-count checker (current/historical marker classification, unmarked fails); two-step pin removal; one-time doc sync incl. `specs/README.md` 023/024 rows |
| B6 | S | Schema-version constant import; evals-dir single defining module + module-level re-exports; known-debt register; verification-matrix / agent-handoff boundary map updates |

## Project Structure

```text
specs/025-core-consolidation/
src/podcast_ingest_core/path_safety.py          (new)
src/podcast_ingest_core/run_report_io.py        (new)
src/podcast_ingest_core/mcp_runtime.py          (new)
src/podcast_ingest_core/mcp_tools_read.py       (new)
src/podcast_ingest_core/mcp_tools_side_effect.py (new)
src/podcast_ingest_core/mcp_tools_corpus_workflows.py (new)
src/podcast_ingest_core/mcp_tools_verified_report_queries.py (new)
src/podcast_ingest_core/mcp_server.py           (becomes facade)
src/podcast_ingest_core/storage.py              (env-overridable DATA_DIR)
tests/conftest.py                                (new)
tests/test_path_safety_characterization.py      (new)
tests/test_path_safety_boundary.py               (new)
tests/test_run_report_io_boundary.py             (new)
tests/test_mcp_server_facade_boundary.py         (new)
tests/test_docs_registry_count_consistency.py    (new)
tests/test_data_dir_fixture_contract.py          (new)
```

## Risks

1. Predicate rejected-set drift → characterization committed green pre-refactor; no-leak suites gate.
2. Registration order / import side effects → single registration path; group modules import `mcp_runtime` only; facade guard bans back-imports.
3. Silent monkeypatch misses in `tests/test_mcp_server.py` → mechanical grep inventory of `mcp_server.<attr>` uses across the 7 touching test files drives the re-export list; no test edits allowed in B4 except the new guard.
4. Doc-test cascade codifying a stale count → checker computes N from live registry; two-step landing before removing old pins.
5. Weak-writer failure-semantics drift → raw `OSError` re-raise; serialization kwargs byte-identical; existing `.part` failure tests unchanged.

## Verification

```powershell
# per batch: targeted first, then the standard gate
python -m pytest tests/<batch-targets> -q
python -m pytest
python -m compileall src scripts
git diff --check
```
