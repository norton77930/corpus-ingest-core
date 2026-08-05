# Feature Specification: Verified Research Report Coverage Index

**Feature Branch**: `022-verified-research-report-coverage-index`  
**Created**: 2026-08-05  
**Status**: Implemented

**Input**: Offline, read-only, episode-centric coverage of which local podcast episodes have (or lack) canonical verified research report bundles, joining local episode inventory with the 020 catalog view—without body reads, writes, revalidation, or investment claims.

## User Scenarios & Testing

### User Story 1 — List Episode Coverage for One Podcast (Priority: P1)

An operator supplies an exact `podcast_id` and receives a bounded, deterministic list of local episode coverage rows: whether each episode appears in the local inventory, whether it has one or more canonical verified-report bundles, and the bounded list of `source_digest` values when present.

**Why this priority**: After 020 catalog (bundle-centric) and 021 revalidation (single locator), operators still cannot answer “which episodes in this podcast lack a verified report?”

**Independent Test**: Fixture tree with inventory-only, bundle-only, and inventory+bundle episodes; assert join semantics, sort, limits, and zero writes.

**Acceptance Scenarios**:

1. **Given** a podcast with local inventory episodes and no research-reports root, **When** coverage runs, **Then** every inventory episode returns `has_bundle=false`, counts are consistent, and zero files are written.
2. **Given** inventory episode A with one canonical bundle and inventory episode B with none, **When** coverage runs, **Then** A reports `has_bundle=true` with its `source_digest`, B reports `has_bundle=false`, ordered by `episode_ref` ascending.
3. **Given** a bundle for episode C with no inventory artifacts, **When** coverage runs, **Then** C appears as an orphan coverage row (`inventory_present=false`, `has_bundle=true`) and page totals include an orphan count.

### User Story 2 — Filter Missing or Present Bundles (Priority: P1)

An operator filters coverage to only episodes missing bundles (backfill candidates) or only episodes that already have bundles.

**Why this priority**: Gap lists drive historical 019 backfill prioritization without dumping full corpus pages.

**Independent Test**: Mixed fixture; `has_bundle=false` returns only gaps; `has_bundle=true` returns only covered rows; totals still describe the full podcast join before row filtering.

**Acceptance Scenarios**:

1. **Given** mixed coverage, **When** `has_bundle=false`, **Then** only gap rows are returned within `limit`, sorted deterministically.
2. **Given** mixed coverage, **When** `has_bundle=true`, **Then** only rows with at least one bundle are returned.
3. **Given** invalid `has_bundle` type or invalid limit, **When** coverage runs, **Then** input is rejected before traversal.

### User Story 3 — Thin CLI and Append-Only MCP Read Query (Priority: P2)

An operator runs a thin CLI or MCP Tool 19 to obtain the same sanitized JSON coverage page Core produces.

**Why this priority**: Matches project thin-interface pattern and keeps discovery agent-accessible without side effects.

**Independent Test**: CLI and MCP each call Core once; Tools 1–18 unchanged; registry exact 19 tools.

**Acceptance Scenarios**:

1. **Given** valid podcast_id, **When** CLI runs, **Then** stdout is JSON-safe coverage only (no paths, bodies, secrets).
2. **Given** MCP Tool 19, **When** called, **Then** it appends after Tool 18, delegates once to Core, and uses the existing success/error envelope.
3. **Given** Tools 1–18, **When** registry is inspected, **Then** order and contracts are unchanged.

### Edge Cases

- Exact `podcast_id` required; no multi-podcast scan, latest/next, prefix, or glob.
- Multiple bundles per episode: report `bundle_count` and a bounded sorted `source_digests` list (cap 10 digests; excess reflected only as higher `bundle_count`).
- Missing inventory directories and missing catalog root are valid empty sides of the join, not hard failures.
- Reserved episode refs `latest`/`next` never appear as inventory or coverage rows.
- Per-directory entry caps (1,000) fail closed to an incomplete coverage status rather than unbounded scan.
- Coverage never claims source currentness or report quality; it does not call 021 revalidation.

## Safety and Data Boundaries

- Read-only/offline/zero-write: no create, modify, delete, export, copy, zip, publish, or path output.
- No DB/FTS/vector/cache; no RSS/HTTP/LLM/.env/download/transcription/remediation; no provider construction.
- No report.json / report.md / transcript / source-artifact body reads for coverage rows (bundle side reuses 020-safe summary discovery only).
- Public output: no absolute paths, raw manifests, secrets, traceback bodies, stock queries, or investment advice.
- Does not change 018–021 public contracts; MCP Tool 19 is append-only.

## Requirements

- **FR-001**: Core MUST expose `list_verified_research_report_coverage(podcast_id, *, has_bundle=None, limit=50)` returning an immutable coverage page.
- **FR-002**: Left side MUST be local episode inventory discovery for the exact podcast (same local artifact/seed families as corpus index discovery) without persisting an index or writing files.
- **FR-003**: Right side MUST discover canonical bundles for that podcast using 020-equivalent safe eligibility (canonical `v1-[a-f0-9]{64}`, safe projection) without report/transcript body reads.
- **FR-004**: Rows MUST be the sorted union of inventory episode refs and catalog episode refs for that podcast, each with `inventory_present`, `has_bundle`, `bundle_count`, and bounded `source_digests`.
- **FR-005**: Optional `has_bundle` filter MUST apply after join and before limit; page summary counts MUST describe the full unfiltered join for that podcast when traversal is complete.
- **FR-006**: Limits MUST be integers `1..100` (default 50); invalid inputs reject before traversal.
- **FR-007**: Coverage MUST be zero-write and offline; incomplete entry caps set a bounded incomplete status.
- **FR-008**: Public results MUST omit bodies, absolute paths, raw manifests, secrets, and traceback bodies; `not_investment_advice=true`.
- **FR-009**: Thin CLI `scripts/query_verified_research_report_coverage.py` MUST delegate once to Core and print JSON-safe output.
- **FR-010**: MCP MUST append Tool 19 `query_verified_research_report_coverage` after Tools 1–18 without changing their order or contracts.
- **FR-011**: No new dependency; no change to Tool 17/18 behavior.

## Key Entities

- **Episode inventory set**: Local episode refs discovered from seeds and per-episode artifacts for one podcast, without network or writes.
- **Bundle set**: Canonical eligible verified-report bundles for that podcast (020-safe summaries).
- **Coverage row**: One episode_ref join record with presence flags and bounded digests.
- **Coverage page**: Bounded returned rows plus podcast-level summary counts and traversal/coverage status.

## Success Criteria

- Operators can list gap episodes (`has_bundle=false`) for one podcast without reading report bodies.
- Missing roots/dirs yield empty sides and zero writes.
- Tool 19 is append-only; Tools 1–18 remain compatible; registry exact 19 tools.
- Tree snapshots prove zero writes for success and failure paths.

## Assumptions

1. Local inventory discovery matches corpus index episode-ref discovery families (audio, transcript, summaries, mentions, reports, mappings, external, episode-seeds, semantic reviews) without requiring a persisted `corpus-index.json`.
2. Bundle layout remains `data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/` as in 018–020.
3. Multiple digests per episode are rare; exposing up to 10 digests in the row is sufficient for v1 operators.
4. Coverage is not a freshness claim; operators use 021 for exact-locator source revalidation.

## Out of Scope (v1)

- Source revalidation, inspect self-consistency deep checks beyond 020 summary eligibility, publish/assemble, remediation, RSS, LLM
- Cross-podcast scan, export, DB/FTS/vector, body search, automatic backfill, scheduler
- Changing 020 list/search/inspect or Tool 17/18 contracts
- Investment advice or market data
