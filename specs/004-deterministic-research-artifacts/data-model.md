# Deterministic Research Artifacts Data Model

**Status: Backfilled / As-built**

## Entities

- EpisodeIntelligenceReport: one-episode report with metadata, timeline,
  mentions, industry clues, macro variables, risks, warnings, and evidence.
- IndustryChainMapping: nodes and stock candidates from deterministic local config.
- StockCandidate: company, ticker, relation type, evidence status, and verification status.
- ExternalDataBoundary: required checks, `not_requested`, `not_fetched`, and `data_date=null`.
- ExternalDataVerification: local fixture updates to external status and source metadata.
- GooayeLensModel: local dimensions and safety rules.
- StockLensReport: deterministic stock/company research framework.

## Boundaries

- `podcast_explicit` requires podcast evidence.
- `inferred_from_industry` remains a research lead and `needs_verification`.
- Fixture data is external evidence, not podcast evidence.
- External status fields are not market facts.
