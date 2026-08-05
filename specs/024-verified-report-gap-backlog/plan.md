# Implementation Plan: Verified Report Gap Backlog

**Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

## Summary

Thin operator-facing gap backlog over SPEC 022 coverage: Core wrapper with `has_bundle=False`, thin CLI, append-only MCP Tool 21. No 023 suggest, no writes.

## Constitution Check

Local artifacts only; thin CLI/MCP; read-only (no dry-run side effects needed); no LLM/secrets; no investment advice; no cache rebuild; TDD. **No constitution amendment.**

## Design Decisions

1. **Reuse 022** — single source of join/filter truth; backlog is a named projection, not a second scanner.
2. **B-lite** — no suggest fan-out (cost/complexity).
3. **Tool 21** append-only after 1–20.

## Project Structure

```text
specs/024-verified-report-gap-backlog/
src/podcast_ingest_core/verified_report_gap_backlog.py
src/podcast_ingest_core/mcp_verified_report_gap_backlog.py
scripts/list_verified_report_gap_backlog.py
tests/test_verified_report_gap_backlog.py
tests/test_verified_report_gap_backlog_cli.py
tests/test_spec_024_verified_report_gap_backlog_docs.py
```

## Verification

```powershell
python -m pytest tests/test_verified_report_gap_backlog.py tests/test_verified_report_gap_backlog_cli.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
```
