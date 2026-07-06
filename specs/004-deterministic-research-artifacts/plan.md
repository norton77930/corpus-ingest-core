# Deterministic Research Artifacts Implementation Plan

**Status: Backfilled / As-built**

## Summary

This package records deterministic research artifacts built from local podcast
artifacts, local configs, and local fixture data.

## Technical Context

- Core modules: `episode_intelligence.py`, `industry_mapping.py`,
  `external_data_boundary.py`, `external_data_verification.py`,
  `gooaye_lens.py`, `stock_lens.py`.
- CLI/scripts: `generate_episode_intelligence_report.py`,
  `generate_industry_chain_mapping.py`, `generate_external_data_boundary.py`,
  `verify_external_data_boundary.py`, `inspect_gooaye_lens.py`,
  `generate_stock_lens_report.py`.
- Tests: `test_episode_intelligence.py`, `test_industry_mapping.py`,
  `test_external_data_boundary.py`, `test_external_data_verification.py`,
  `test_gooaye_lens.py`, `test_stock_lens_report.py`.

## Constitution Check

- dry-run: verification has confirm guard; generation reuses artifacts unless force is used.
- exact `api_cost_ack`: not applicable; no LLM calls in this package.
- secret boundary: `.env` is not read.
- external-data boundary: fixture verification only; no live market API.
- evidence separation: podcast evidence, inference, and external status are separate.
- investment safety: no investment advice.
- manual cache rebuild: no automatic cache rebuild after artifact writes.

## Spec Kit workflow record

This as-built plan follows constitution, specify, clarify, plan, checklist,
tasks, analyze, implement, and converge steps.
