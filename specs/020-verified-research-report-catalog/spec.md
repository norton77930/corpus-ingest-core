# Feature Specification: Verified Research Report Catalog

**Feature Branch**: `020-verified-research-report-catalog`
**Created**: 2026-07-26
**Status**: Implemented

**Input**: Provide an implemented local, read-only/offline catalog for canonical verified research report bundles: list, safe-metadata search, and exact-bundle self-consistency inspection through Core, thin CLI, and appended MCP Tool 17.

## User Scenarios & Testing

### User Story 1 — List Canonical Local Bundles (Priority: P1)

An operator lists canonical local verified report bundles, optionally filtering by exact `podcast_id` and/or exact `episode_ref`, to discover available reports without opening report or transcript content.

**Why this priority**: Discovery is the minimal useful catalog capability and establishes safe bounded traversal.

**Independent Test**: Fixture root with valid, malformed, symlinked, and out-of-root candidates; assert only canonical in-root bundle summaries appear in deterministic order, limited to the requested bound. A missing root returns an empty page and writes zero files.

**Acceptance Scenarios**:

1. **Given** a missing `data/research-reports` root, **When** list runs, **Then** it returns an empty result, performs zero writes, and reports no error.
2. **Given** canonical eligible bundles and optional exact filters, **When** list runs, **Then** it returns only matching summaries sorted by `(podcast_id, episode_ref, report_version)` ascending and bounded by `limit`.
3. **Given** symlinks, junctions, noncanonical version names, or paths resolving outside the catalog root, **When** traversal runs, **Then** it skips/rejects them without following or exposing them.

### User Story 2 — Search Safe Derived Metadata (Priority: P1)

An operator searches normalized terms over manifest-derived safe metadata in discovered canonical bundles, without reading `report.json`, `report.md`, transcript, or source artifact bodies.

**Why this priority**: Search makes a local catalog usable while retaining the report-content boundary.

**Independent Test**: Instrument fixture reads so report/transcript reads fail; verify matching results use only whitelisted manifest fields and deterministic order.

**Acceptance Scenarios**:

1. **Given** a nonblank normalized query, **When** search runs, **Then** it searches only the documented safe metadata projection and returns bounded deterministic matches.
2. **Given** a blank query, **When** search runs, **Then** it is rejected as invalid rather than becoming an unbounded browse operation.
3. **Given** a manifest with a secret-like, unsafe URI, raw-path, or oversized/unrecognized field, **When** search runs, **Then** that value is neither searched nor returned.

### User Story 3 — Inspect One Exact Bundle (Priority: P1)

An operator gives exact `podcast_id`, `episode_ref`, and `source_digest` to inspect one bundle's local self-consistency. The result distinguishes valid self-consistency from malformed, missing, or untrusted candidates and never claims source freshness.

**Why this priority**: A catalog result must be auditable without re-running upstream workflows.

**Independent Test**: Valid fixture and tampered variants for identity, directory contents, manifest schema, report hashes/sizes, and report identity; assert valid only when all checks pass and always assert `source_currentness_status=not_evaluated`.

**Acceptance Scenarios**:

1. **Given** an exact canonical in-root bundle with exactly `report.json`, `report.md`, and `manifest.json`, **When** inspect runs, **Then** it verifies canonical identity, manifest schema, hashes, sizes, and report identity and returns a sanitized verdict.
2. **Given** an extra file, missing file, mismatched digest/version/identity, malformed manifest, hash/size mismatch, symlink/junction, or out-of-root resolution, **When** inspect runs, **Then** it fails closed with bounded category metadata and no raw manifest.
3. **Given** a self-consistent historic bundle, **When** inspect succeeds, **Then** it says only bundle self-consistency and sets `source_currentness_status=not_evaluated`.

### Edge Cases

- Exact filters are equality filters; no prefix, glob, case-fold, latest/next, or implicit episode selector exists.
- Canonical version directories match `v1-[a-f0-9]{64}` only; `source_digest` is the lowercase 64-hex suffix.
- Limits are integers `1..100`, default `50`; invalid values reject before traversal.
- Traversal is bounded and level-by-level: root → podcast directory → episode directory → version directory. Per-level entry counts are capped at 1,000; excess is a bounded incomplete/invalid result, never recursive scanning.

## Safety and Data Boundaries

- This capability is read-only/offline: it creates, modifies, deletes, exports, copies, zips, outputs to a path, and republishes nothing.
- It does not use DB/FTS/vector/cache; it does not read report/transcript/source-artifact bodies for list or search. Inspect reads only the exact three bundle members needed for structural and integrity checks: `manifest.json` is capped at 1 MiB and each `report.json`/`report.md` snapshot is capped at 16 MiB.
- It performs no RSS/HTTP/LLM/.env/download/transcription/remediation, no latest selector, no provider construction, and no cache rebuild.
- Public output contains sanitized manifest-derived safe metadata only: no raw manifest, report body, transcript body, source paths, absolute paths, URI query/fragment data, secrets, or traceback body.
- The catalog does not make podcast, market, or investment claims. It preserves `not_investment_advice=true` when manifest-derived and never provides investment advice.

## Requirements

- **FR-001**: Core MUST expose `list_verified_research_reports`, `search_verified_research_reports`, and `inspect_verified_research_report` as read-only seams.
- **FR-002**: List MUST support optional exact `podcast_id` and `episode_ref` filters, deterministic ascending `(podcast_id, episode_ref, report_version)` sort, default limit 50, and maximum limit 100.
- **FR-003**: A missing catalog root MUST return an empty list/search result with zero writes.
- **FR-004**: Search MUST use only a documented safe manifest-derived metadata projection and MUST NOT read report, transcript, or source-artifact body content.
- **FR-005**: Inspect MUST require exact `podcast_id`, exact `episode_ref`, and lowercase 64-hex `source_digest`; it MUST validate canonical identity, exactly three files, manifest schema, manifest file hashes/sizes, and report identity.
- **FR-006**: A successful inspect MUST claim only local bundle self-consistency and MUST return `source_currentness_status=not_evaluated`.
- **FR-007**: Every traversal and exact lookup MUST reject or skip symlink, junction, and resolved out-of-root paths, and accept version names only matching `v1-[a-f0-9]{64}`.
- **FR-008**: Traversal MUST be bounded, nonrecursive beyond the documented three directory levels, and fail closed/bounded when entry caps are exceeded.
- **FR-009**: Public results MUST omit raw manifest objects, report/transcript bodies, source paths, absolute paths, unsafe URI data, credential-like values, and traceback bodies.
- **FR-010**: v1 MUST NOT export/copy/zip/re-publish bundles, accept output paths, use DB/FTS/vector/cache, contact RSS/HTTP, invoke LLMs, read `.env`, download/transcribe/remediate, or resolve latest/next.
- **FR-011**: A thin CLI `scripts/query_verified_research_report_catalog.py` MUST expose `list`, `search`, and `inspect` subcommands and print JSON-safe Core results only.
- **FR-012**: MCP MUST append reviewed Tool 17, `query_verified_research_report_catalog`, after Tools 1–16 without changing their order or contracts; it exposes list/search/inspect operations through the existing envelope.
- **FR-013**: No new dependency is permitted. Existing 015–019 contracts, report publication, and storage ownership remain unchanged.

## Key Entities

- **Catalog root**: Existing local `data/research-reports` directory, treated as untrusted read-only input.
- **Canonical bundle locator**: Exact `(podcast_id, episode_ref, source_digest)` addressing `v1-{source_digest}` beneath the catalog root.
- **Safe metadata projection**: Whitelisted scalar manifest fields suitable for list/search output; never a raw manifest.
- **Bundle self-consistency verdict**: Structural/integrity result for one exact bundle, explicitly separate from whether upstream sources remain current.

## Success Criteria

- List/search return no more than the requested valid limit in deterministic order.
- Missing roots and all rejected candidates cause zero writes.
- Search fixture tests prove no report/transcript body read occurs.
- Inspect accepts only exact three-file canonical self-consistent bundles and labels all successful verdicts `source_currentness_status=not_evaluated`.
- Tool 17 is append-only, while Tools 1–16 remain compatible.

## Assumptions

1. `data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/` remains the local bundle layout defined by 018/019.
2. The accepted manifest `schema_version` is the current `REPORT_SCHEMA_VERSION` from `src/podcast_ingest_core/verified_research_report.py`: `latest-episode-verified-research-report-v1`; a future manifest schema requires a separately approved compatibility rule.
3. The chosen default/max limits (50/100) and per-level entry cap (1,000) are v1 contract constants, not configuration or user-supplied paths.
4. A manifest can establish self-consistency only for its contained files; checking current source artifacts is deliberately out of scope.

## Out of Scope (v1)

- New catalog operations beyond the implemented list/search/inspect Core, CLI, and MCP Tool 17 surfaces
- Raw report viewing, full-text/transcript search, export, copy, zip, or republishing
- Database, FTS, vector, embedding, cache, RSS, HTTP, LLM, `.env`, downloads, transcription, remediation, latest selection, and batch workflows
- Source-currentness, lineage revalidation, report regeneration, or investment advice
