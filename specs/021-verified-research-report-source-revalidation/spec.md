# Feature Specification: Verified Research Report Source Revalidation

**Feature Branch**: `021-verified-research-report-source-revalidation`
**Created**: 2026-07-27
**Status**: Implemented

**Input**: Revalidate source lineage and canonical source snapshots for one exact published verified-research-report bundle, locally and without writes.

## User Scenario

An operator supplies the exact `(podcast_id, episode_ref, lowercase-64-hex source_digest)` locator. Core first establishes bundle self-consistency, then—only for a valid bundle—checks supported assembly options, current validated lineage, published/current lineage agreement, canonical source metadata, and the publisher-owned digest rule.

Bundle/currentness separation is mandatory: missing or invalid bundles return downstream `not_evaluated` and must not read artifacts outside that bundle. `current` means only this local snapshot was revalidated now; it does not promise continuing freshness.

## Requirements

- **FR-001**: Core exposes `revalidate_verified_research_report_sources(podcast_id, episode_ref, source_digest)` returning immutable `VerifiedResearchReportSourceRevalidation`.
- **FR-002**: The exact locator is the sole selector: no latest, next, prefix, glob, batch, or catalog-wide operation.
- **FR-003**: Statuses are bounded: bundle `valid|invalid|not_found`; lineage `current|missing|stale_or_invalid|mismatch|not_evaluated`; currentness `current|stale_or_invalid|not_evaluated`.
- **FR-004**: Hostile paths never dereferenced. Manifest, lineage, fixture, snapshot, and source-artifact path values are comparison data only, never read authority.
- **FR-005**: The workflow is read-only/offline/zero-write; it has no provider, network, cache, publish, staging, claim, repair, or regeneration behavior.
- **FR-006**: Tool 18 is append-only and Tools 1–17 unchanged. It accepts precisely the three locator inputs and delegates once to Core.
- **FR-007**: Public output contains no raw manifest, report/transcript/source body, paths including absolute paths, URI, stock query, secrets, or traceback body. It gives not investment advice.

## Explicit Non-goals

No change to SPEC 020 list/search/inspect or Tool 17; no output path, export, copy, zip, adoption, migration, assemble narrative, republish, or source modification; no timestamp/mtime/version-directory/digest freshness inference; no DB/FTS/vector/cache; no RSS/HTTP/LLM/.env/download/transcription/remediation; no live market API or dependency addition.

## Success Criteria

A valid exact bundle can reach `source_currentness_status=current` only after every gate passes. Invalid/missing bundle tests prove all downstream readers remain untouched. Canonical-before-read sentinels prove hostile paths never dereferenced, and tree snapshots prove zero writes.
