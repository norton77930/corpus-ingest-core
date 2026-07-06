# Tasks: LLM Safety Synthesis Smoke Review

**Status: Backfilled / As-built**

These retrospective tasks trace implemented behavior to code and tests. They are
not a new runtime backlog.

## Phase 1: As-built Traceability

- [x] T001 Trace semantic summary safety to `semantic_summarizer.py`, `summarize_episode.py`, and `test_semantic_summarizer.py`
- [x] T002 Trace provider calls and profile loading to `llm_provider.py`, `llm_profiles.py`, `local_env.py`, `test_llm_profiles.py`, and `test_local_env.py`
- [x] T003 Trace stock lens synthesis to `stock_lens_synthesis.py`, `generate_stock_lens_synthesis_report.py`, and `test_stock_lens_synthesis.py`
- [x] T004 Trace smoke CLI to `run_research_llm_smoke.py` and `test_research_llm_smoke.py`
- [x] T005 Trace deterministic review gate to `research_llm_smoke_review.py`, `review_research_llm_smoke.py`, and `test_research_llm_smoke_review.py`
- [x] T006 Trace research safety eval docs to `test_research_safety_eval_docs.py`
- [x] T008 Trace Phase 6U Semantic Summary Smoke Validation to `run_semantic_summary_smoke.py` and `test_semantic_summary_smoke.py`
- [x] T009 Trace semantic summary review gate to `semantic_summary_smoke_review.py`, `review_semantic_summary_smoke.py`, and `test_semantic_summary_smoke_review.py`
- [x] T010 Trace direct semantic CLI exact `api_cost_ack` guard and no raw transcript stdout boundary to `summarize_episode.py` and `test_semantic_summarizer.py`
- [x] T011 Trace Phase 6U.1 semantic review guard false positive fix to `semantic_summary_smoke_review.py` and `test_semantic_summary_smoke_review.py`
- [x] T012 Trace Phase 6U.1 stderr progress to `semantic_summarizer.py`, `run_semantic_summary_smoke.py`, and `test_semantic_summary_smoke.py`

## Phase 2: Constitution Checks

- [x] T007 Confirm dry-run, exact `api_cost_ack`, secret boundary, evidence separation, external status, no live market API, no investment advice, and manual cache rebuild boundaries

## Spec Kit workflow record

This package completed `$speckit-tasks`, `$speckit-analyze`,
`$speckit-implement`, and `$speckit-converge` as retrospective documentation.

- [x] T013 Trace Phase 6V reviewed semantic context opt-in to `stock_lens_synthesis.py`, `run_research_llm_smoke.py`, and `test_stock_lens_synthesis.py`.
- [x] T014 Trace Phase 6V.1 review gate boundary/context consistency to `research_llm_smoke_review.py` and `test_research_llm_smoke_review.py`.
