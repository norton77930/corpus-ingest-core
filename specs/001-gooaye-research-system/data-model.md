# Gooaye Research System Data Model

## Evidence Boundary

Podcast evidence is any claim traceable to transcript metadata, transcript segments, mention evidence, or generated reports that preserve timestamp evidence. Podcast evidence should include episode ref, timestamp, and source artifact when available.

Deterministic mentions are extracted from transcript segments. They can support company, ticker, industry, macro topic, crypto, location, and person references, but they are still local text evidence rather than verified market facts.

## Research Inference Boundary

Industry mapping creates research leads from local config and episode intelligence. A candidate marked `podcast_explicit` is tied to podcast evidence. A candidate marked `inferred_from_industry` is a local deterministic inference and must remain `needs_verification` unless external verification data exists.

Stock lens reports merge podcast-wide local artifacts into a research framework. They must keep direct podcast evidence, inferred research leads, and external verification needs in separate sections.

## External Verification Boundary

External boundary artifacts describe what still needs checking. Candidate fields such as external verification status, `not_requested`, `not_fetched`, and `data_date=null` are status markers, not market facts.

The current external verification provider is local fixture only. Fixture data may update source status and data date, but it remains external evidence and must not turn an inferred candidate into podcast evidence. Phase 7A records that there is no live market API.

## LLM Output Boundary

Semantic summary may use transcript text only after explicit API-cost acknowledgement. Stock lens synthesis is narrower than semantic summary: it reads Phase 6F stock lens JSON by default and records the `phase-6f-stock-lens-json-only` boundary. Phase 6V opt-in may add reviewed semantic summary context and records `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`; Phase 6V.1 review gate checks boundary/context consistency.

Stock lens synthesis output is a narrative artifact, not a replacement for deterministic reports. It must preserve no investment advice, no target price, no guaranteed return, and the separation between podcast evidence, inference, and external verification status.

## Review Artifacts

Phase 6T review reports are deterministic audit artifacts. They read existing stock lens synthesis JSON/Markdown and write review JSON/Markdown under `evals/research-llm-smoke/reports/`. They do not call an LLM, read `.env`, fetch market data, or rewrite synthesis artifacts.

Local `.env` files can hold API key values for manual CLI smoke tests, but `.env` must not be committed and values must not be printed in reports or docs.
