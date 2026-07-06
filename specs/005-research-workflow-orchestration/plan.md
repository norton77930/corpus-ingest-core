# Research Workflow Orchestration Implementation Plan

**Status: Backfilled / As-built**

## Summary

This package records workflow orchestration across deterministic reports,
optional semantic summary, optional stock lens synthesis, optional local fixture
verification, and MCP exposure.

## Technical Context

- Core modules: `research_workflow.py`, `mcp_server.py`,
  `semantic_summarizer.py`, `stock_lens_synthesis.py`,
  `external_data_verification.py`.
- CLI/scripts: `run_research_workflow.py`.
- Tests: `test_research_workflow.py`, `test_mcp_server.py`.

## Constitution Check

- dry-run: default workflow behavior.
- exact `api_cost_ack`: required for semantic summary and stock lens synthesis.
- secret boundary: `.env` and API key values are never returned.
- external-data boundary: fixture provider only; no live market API.
- evidence separation: downstream artifacts preserve podcast evidence, inference, external status, and LLM synthesis.
- investment safety: no investment advice.
- manual cache rebuild: workflow warns cache may be stale.

## Spec Kit workflow record

This as-built plan follows constitution, specify, clarify, plan, checklist,
tasks, analyze, implement, and converge steps.

- Phase 6V: workflow and smoke CLI include optional pass-through flags for reviewed semantic context in stock lens synthesis. Default behavior remains 6F JSON-only, and MCP exposure is unchanged.
