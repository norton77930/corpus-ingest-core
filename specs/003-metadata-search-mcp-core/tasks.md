# Tasks: Metadata Search MCP Core

**Status: Backfilled / As-built**

These retrospective tasks trace implemented behavior to code and tests. They are
not a new runtime backlog.

## Phase 1: As-built Traceability

- [x] T001 Trace deterministic mentions to `entity_extractor.py`, `extract_mentions.py`, and `test_entity_extractor.py`
- [x] T002 Trace cache rebuild to `cache.py`, `rebuild_cache.py`, and `test_cache.py`
- [x] T003 Trace transcript and mention search to `search.py`, `search_transcripts.py`, `search_mentions.py`, and `test_search.py`
- [x] T004 Trace MCP stdio server behavior to `mcp_server.py`, `run_mcp_server.py`, and `test_mcp_server.py`
- [x] T005 Trace MCP setup validation to `validate_mcp_setup.py` and `test_mcp_setup_validation.py`
- [x] T006 Trace MCP eval docs and report capture to `docs/mcp-eval-prompts.md`, `new_mcp_eval_report.py`, `test_docs_mcp_eval.py`, and `test_mcp_eval_report_script.py`

## Phase 2: Constitution Checks

- [x] T007 Confirm dry-run, secret boundary, evidence separation, manual cache rebuild, no live market API, and no investment advice boundaries

## Spec Kit workflow record

This package completed `$speckit-tasks`, `$speckit-analyze`,
`$speckit-implement`, and `$speckit-converge` as retrospective documentation.
