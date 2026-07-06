# Metadata Search MCP Core Implementation Plan

**Status: Backfilled / As-built**

## Summary

This package records deterministic mentions, SQLite cache/search, MCP stdio
exposure, and MCP eval/report capture.

## Technical Context

- Core modules: `entity_extractor.py`, `cache.py`, `search.py`, `mcp_server.py`.
- CLI/scripts: `extract_mentions.py`, `rebuild_cache.py`, `search_mentions.py`,
  `search_transcripts.py`, `run_mcp_server.py`, `validate_mcp_setup.py`,
  `new_mcp_eval_report.py`.
- Tests: `test_entity_extractor.py`, `test_cache.py`, `test_search.py`,
  `test_mcp_server.py`, `test_mcp_setup_validation.py`, `test_docs_mcp_eval.py`,
  `test_mcp_eval_report_script.py`.

## Constitution Check

- dry-run: MCP side-effect tools default to dry-run.
- exact `api_cost_ack`: required only for semantic MCP paths, not base search.
- secret boundary: MCP responses must not expose `.env` or API key values.
- external-data boundary: no live market API.
- evidence separation: search returns transcript or mention evidence, not market facts.
- investment safety: no investment advice.
- manual cache rebuild: MCP completion warns but does not rebuild automatically.

## Spec Kit workflow record

This as-built plan follows constitution, specify, clarify, plan, checklist,
tasks, analyze, implement, and converge steps.
