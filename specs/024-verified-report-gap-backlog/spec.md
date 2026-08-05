# Feature Specification: Verified Report Gap Backlog

**Feature Branch**: `024-verified-report-gap-backlog`  
**Created**: 2026-08-05  
**Status**: Implemented

**Input**: Offline, read-only **gap backlog** for one podcast: which local inventory episodes still lack a canonical verified research report bundle—without calling 023 suggest, without writes, and without auto-remediation.

## Clarifications

### Session 2026-08-05

- Q: B-lite vs B-full (attach 023 suggest per row)? → A: **B-lite only** — coverage gaps only; no per-row 023 suggest.
- Q: Include orphan bundles (bundle without inventory)? → A: **No** — backlog is `has_bundle=false` rows only (inventory gaps; orphans already have bundles).
- Q: New MCP tool? → A: **Yes** — append-only Tool 21 read-query.
- Q: Call 023 suggest? → A: **Never** in v1.
- Q: One-action human remediation? → A: Out of scope here; operators use 023 Skill after picking a gap row.

## User Scenarios & Testing

### User Story 1 — List Gap Backlog (Priority: P1)

An operator supplies exact `podcast_id` and receives a bounded, deterministic list of inventory episodes with `has_bundle=false`, plus podcast-level gap counts from the full coverage join.

**Why this priority**: 022 can filter gaps, but operators need a named backlog surface for historical backfill planning without inventing filters.

**Independent Test**: Mixed inventory/bundle fixtures; only gap inventory rows appear; zero writes; counts match coverage join totals.

**Acceptance Scenarios**:

1. **Given** inventory EP1 with bundle and EP2 without, **When** backlog runs, **Then** only EP2 is listed and gap counts reflect one inventory gap.
2. **Given** missing catalog root and three inventory episodes, **When** backlog runs, **Then** all three appear as gaps, zero writes.
3. **Given** orphan bundle-only EP9, **When** backlog runs, **Then** EP9 is not listed (has bundle).

### User Story 2 — Thin CLI and MCP Tool 21 (Priority: P1)

Operators call the same seam via CLI and append-only MCP Tool 21 (read-query).

**Acceptance Scenarios**:

1. CLI prints JSON-safe backlog only.
2. Tool 21 appends after Tools 1–20; Tools 1–20 unchanged; no confirm/ack.
3. Invalid `podcast_id` / limit fail closed before discovery.

## Safety and Data Boundaries

- Read-only/offline/zero-write.
- Reuses 022 coverage join semantics (no second path scanner).
- No 023 suggest, no 016/019 confirm, no body reads, no 021 revalidation.
- No investment advice; no live market API.

## Requirements

- **FR-001**: Core MUST expose `list_verified_report_gap_backlog(podcast_id, *, limit=50)` returning an immutable backlog page.
- **FR-002**: Implementation MUST reuse `list_verified_research_report_coverage(..., has_bundle=False, limit=limit)` for row selection and join totals (no parallel discovery rules).
- **FR-003**: Rows MUST be inventory gaps only (`has_bundle=false`); order deterministic by `episode_ref`.
- **FR-004**: Page MUST include `gap_count` (= coverage `without_bundle_count`), `returned_count`, `limit`, `coverage_status`, `catalog_root_status`, `not_investment_advice=true`.
- **FR-005**: Limits `1..100`, default 50; invalid inputs raise before discovery.
- **FR-006**: Zero-write (tree snapshot).
- **FR-007**: Thin CLI `scripts/list_verified_report_gap_backlog.py`.
- **FR-008**: MCP Tool 21 `list_verified_report_gap_backlog` append-only read-query.
- **FR-009**: No new dependency; Tools 1–20 unchanged.

## Success Criteria

- Operator can list backfill candidates for one podcast without writes or LLM.
- Registry exact 21 tools after append.
- Behavior matches 022 `has_bundle=false` filter for the same fixtures.

## Assumptions

1. Gap definition is coverage `has_bundle=false` (not 021 currentness).
2. Operators use 023 Skill after selecting one gap row.

## Out of Scope (v1)

- Per-row 023 suggest (B-full)
- Auto-remediation, batch confirm, scheduler
- Orphan-only views, export zip, body search
