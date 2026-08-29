# Implementation Plan: Verified Research Report Coverage Index

**Branch**: `feat/corpus-semantic-completion-workflows` (package `022-verified-research-report-coverage-index`)  
**Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

## Summary

Add a Core-owned, read-only/offline episode-centric coverage join: local inventory episode refs × 020-safe canonical bundle summaries for one exact `podcast_id`, with optional `has_bundle` filter, thin CLI, and append-only MCP Tool 19.

## Technical Context

- **Language**: Python 3.12; existing stack only; no new dependency.
- **Inventory**: Reuse `corpus_index._discover_episode_refs` (no persist / no `generate_corpus_index`).
- **Bundles**: Reuse catalog root + `_discover_summaries` package-private discovery (no report body reads).
- **Interfaces**: `scripts/query_verified_research_report_coverage.py`; MCP Tool 19 `query_verified_research_report_coverage`.
- **Testing**: filesystem fixtures, zero-write snapshots, filter/limit, MCP registry exact 19 tools.

## Constitution Check

| Principle | Compliance |
| --- | --- |
| Local artifacts | Joins local inventory + local bundles only |
| Thin interfaces | Core owns join; CLI/MCP parse/call/serialize |
| Dry-run first | No side effects; pure read |
| LLM / secrets | No LLM, `.env`, bodies, or secret output |
| Evidence separation | No reinterpretation of report claims |
| No investment advice | Metadata coverage only |
| Manual cache rebuild | No cache |
| TDD | RED before GREEN per slice |

**Gate**: PASS — no constitution amendment.

## Project Structure

```text
specs/022-verified-research-report-coverage-index/
src/corpus_ingest_core/verified_research_report_coverage.py  # NEW
src/corpus_ingest_core/mcp_verified_research_report_coverage.py  # NEW
scripts/query_verified_research_report_coverage.py  # NEW
tests/test_verified_research_report_coverage.py
tests/test_verified_research_report_coverage_cli.py
tests/test_spec_022_verified_research_report_coverage_docs.py
```

## Design Decisions

1. Episode-centric left-biased union: inventory ∪ catalog episode refs; orphans remain visible.
2. Do not persist corpus index; discovery only.
3. Cap `source_digests` at 10 per row; `bundle_count` remains exact for eligible summaries.
4. Append Tool 19 only; Tools 1–18 unchanged.
5. Summary counts always describe full join when `coverage_status=complete`.

## Verification

```powershell
python -m pytest tests/test_spec_022_verified_research_report_coverage_docs.py tests/test_verified_research_report_coverage.py tests/test_verified_research_report_coverage_cli.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
git diff --check
```
