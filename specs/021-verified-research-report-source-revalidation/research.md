# Research: Verified Research Report Source Revalidation

## Decision 1 — Exact locator, never discovery

Accept only exact `(podcast_id, episode_ref, lowercase-64-hex source_digest)`. Reject latest, next, glob, prefix, and batch selectors: revalidation must not choose evidence implicitly.

## Decision 2 — Bundle gate before currentness

Reuse SPEC 020 exact-bundle evidence for local self-consistency before source checks. A missing or invalid bundle yields downstream `not_evaluated`, preventing reads outside the exact bundle. This locks bundle/currentness separation.

## Decision 3 — Canonical-before-read

Hostile paths never dereferenced: manifest, lineage, fixture, snapshot, and source-artifact path values cannot become `Path`, `open`, `read_*`, or `resolve` authority. Core derives canonical paths from validated locator, storage helpers, and supported options; hostile strings are exact-comparison values only.

## Decision 4 — Shared current source snapshots

Reuse `validate_current_verified_research_lineage(...)`, canonical role ordering, review gates, and a one-read immutable source snapshot seam. Reuse the publisher-owned digest helper to avoid divergent canonical JSON/digest behavior.

## Decision 5 — Append-only interface

A separate Tool 18 is required because revalidation reads canonical sources beyond Tool 17's manifest-first catalog boundary. Tool 18 is append-only; Tools 1–17 unchanged.

## Rejected alternatives

Timestamp, mtime, version directory, or digest freshness inference; raw manifest paths; cache/indexes; automatic repairs; network, LLM/provider, `.env`, download, transcription, remediation, and market calls are rejected. The workflow is read-only/offline/zero-write.
