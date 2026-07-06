# Requirements Checklist: LLM Safety Synthesis Smoke Review

**Purpose**: Validate LLM safety, synthesis, smoke, and review requirements quality.
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)
**Status: Backfilled / As-built**

## Requirement Completeness

- [x] CHK001 Are exact `api_cost_ack` requirements documented? [Completeness]
- [x] CHK002 Are semantic summary and stock lens synthesis input boundaries documented? [Coverage]
- [x] CHK003 Are smoke CLI and review gate requirements documented? [Coverage]
- [x] CHK007 Is Phase 6U Semantic Summary Smoke Validation documented with `run_semantic_summary_smoke.py` and `review_semantic_summary_smoke.py`? [Coverage]
- [x] CHK008 Are transcript transfer, exact `api_cost_ack`, no raw transcript stdout, no MCP tool changes, no live market API, and no investment advice documented? [Safety]
- [x] CHK009 Is Phase 6U.1 semantic review guard false positive handling documented? [Safety]
- [x] CHK010 Is stderr progress documented without raw transcript, prompt, API key, or LLM response leakage? [Safety]

## Requirement Clarity

- [x] CHK004 Is `phase-6f-stock-lens-json-only` documented as the synthesis input boundary? [Clarity]
- [x] CHK005 Are `.env`, API key, token, and secret boundary rules documented? [Clarity]

## Constitution Gates

- [x] CHK006 Are dry-run, external status, no live market API, no investment advice, and manual cache rebuild boundaries documented? [Safety]

## Spec Kit workflow record

Checklist generation corresponds to `$speckit-checklist` for this as-built package.

- [x] CHK010 Is Phase 6V reviewed semantic context documented as opt-in, review-gated, no raw transcript, no live market API, no MCP tool changes, and no investment advice? [Safety]
- [x] CHK011 Is Phase 6V.1 boundary/context consistency documented for both JSON-only and reviewed semantic synthesis artifacts? [Safety]
