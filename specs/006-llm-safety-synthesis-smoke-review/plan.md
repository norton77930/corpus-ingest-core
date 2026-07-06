# LLM Safety Synthesis Smoke Review Implementation Plan

**Status: Backfilled / As-built**

## Summary

This package records optional LLM behavior, safety gates, profile and `.env`
ergonomics, raw debug output, smoke CLI, and deterministic review gate.

## Technical Context

- Core modules: `semantic_summarizer.py`, `llm_provider.py`,
  `llm_profiles.py`, `local_env.py`, `stock_lens_synthesis.py`,
  `research_llm_smoke_review.py`, `semantic_summary_smoke_review.py`.
- CLI/scripts: `summarize_episode.py`,
  `generate_stock_lens_synthesis_report.py`, `run_research_llm_smoke.py`,
  `review_research_llm_smoke.py`, `run_semantic_summary_smoke.py`, `review_semantic_summary_smoke.py`.
- Tests: `test_semantic_summarizer.py`, `test_llm_profiles.py`,
  `test_local_env.py`, `test_stock_lens_synthesis.py`,
  `test_research_llm_smoke.py`, `test_research_llm_smoke_review.py`,
  `test_research_safety_eval_docs.py`, `test_semantic_summary_smoke.py`, `test_semantic_summary_smoke_review.py`.

## Constitution Check

- dry-run: synthesis and smoke default to dry-run, including Phase 6U Semantic Summary Smoke Validation.
- exact `api_cost_ack`: required before provider construction, including direct semantic CLI execution.
- secret boundary: `.env`, API key, token, and secret values are never printed.
- external-data boundary: no live market API and no MCP tool changes for Phase 6U.
- evidence separation: synthesis preserves podcast evidence, inference, external status, and LLM output boundaries.
- investment safety: prohibited advice guard enforces no investment advice; smoke CLIs keep no raw transcript stdout.
- Phase 6U.1: semantic review guard false positive handling and stderr progress preserve no prompt, no raw transcript, no API key, and no LLM response leakage.
- Phase 6V.1: research LLM smoke review gate enforces boundary/context consistency for JSON-only and reviewed semantic synthesis artifacts.
- manual cache rebuild: LLM artifact writes do not rebuild cache automatically.

## Spec Kit workflow record

This as-built plan follows constitution, specify, clarify, plan, checklist,
tasks, analyze, implement, and converge steps.

- Phase 6V: reviewed semantic context can be opt-in input for stock lens synthesis. Default remains phase-6f-stock-lens-json-only; opt-in uses phase-6f-stock-lens-json-plus-reviewed-semantic-summary, excludes ## Chunk Summaries, reads no raw transcript, reads no .env, uses no live market API, makes no MCP tool changes, and preserves no investment advice.
- Phase 6V.1: review gate accepts phase-6f-stock-lens-json-only only without semantic context, accepts phase-6f-stock-lens-json-plus-reviewed-semantic-summary only with non-empty review-passed semantic context, and fails unknown or inconsistent boundary/context combinations.
