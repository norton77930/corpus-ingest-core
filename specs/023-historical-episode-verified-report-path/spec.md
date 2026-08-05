# Feature Specification: Historical Episode Verified Report Path

**Feature Branch**: `023-historical-episode-verified-report-path`  
**Created**: 2026-08-05  
**Status**: Implemented

**Input**: Give operators a human-controlled path to advance one **named historical episode** toward a verified research report: discover gaps via 022, remediate readiness via existing 016/015 tools one action at a time, then publish via 019—without a mega side-effect runner or automatic multi-step loops.

## Clarifications

### Session 2026-08-05

Retroactive formal clarification for as-built 023 (implementation already matched these defaults; recorded for Spec Kit audit).

- Q: May the Skill perform two confirmed side-effect MCP calls in one user request (e.g. 016 then 019)? → A: **No.** Exactly one confirmed side-effect call per request; a new user request is required for any second confirm.
- Q: When an eligible verified-report bundle already exists, does suggest recommend revalidation (021) or republish? → A: **Neither.** Return `report_present` with digests only; 021 remains a separate operator action.
- Q: How are invalid selectors reported from Core? → A: **Raise** `HistoricalVerifiedReportPathInputError` (fail closed); do not emit a suggestion code `invalid_input`.
- Q: Does suggest claim source currentness? → A: **No.** Bundle presence uses 020-safe eligible summaries only; never calls 021 and never sets currentness claims.
- Q: Is a new side-effect mega-runner allowed in v1? → A: **No.** Skill-first; only compose existing 016/019 confirms after human approval.

## User Scenarios & Testing

### User Story 1 — Suggest the Single Next Safe Step (Priority: P1)

An operator supplies exact `podcast_id` and exact `episode_ref` (never `latest`/`next`). Core returns a bounded, zero-write suggestion: report already present, ready to publish via 019, or the next 016 completion action (or blocked).

**Why this priority**: 022 lists gaps; operators still need a single authoritative next-step for one episode without inventing tool sequences.

**Independent Test**: Fixtures for (a) has bundle, (b) ready for 019, (c) missing semantic, (d) reserved selector rejection; assert zero writes and stable suggestion codes.

**Acceptance Scenarios**:

1. **Given** an episode with ≥1 eligible bundle, **When** suggest runs, **Then** it reports `report_present` with bounded digests and does not recommend publish or completion.
2. **Given** no bundle but 019 readiness ready, **When** suggest runs, **Then** it recommends `publish_verified_report` targeting Tool 019 only.
3. **Given** not ready for 019, **When** suggest runs, **Then** it recommends at most one 016 selected action (or blocked metadata) and never chains confirm.

### User Story 2 — Portable Skill: One Human Gate Per Request (Priority: P1)

A Skill guides preview → explicit approval → **one** confirmed MCP side-effect call → stop. A new user request is required for any second action.

**Why this priority**: Historical path must match 016/018/019 human-control culture.

**Independent Test**: Skill contract tests lock protocol order, forbidden fallbacks, and stop-after-one-confirm.

**Acceptance Scenarios**:

1. **Given** a suggested publish step, **When** the Skill runs, **Then** it previews 019 (`confirm=false`), waits for exact `episode_ref` approval, confirms once, reports, and stops.
2. **Given** a suggested completion action, **When** the Skill runs, **Then** it uses 016 preview/confirm rules (including exact ack only for semantic_summary) and never auto-runs 019 in the same request.
3. **Given** MCP unavailable, **When** the Skill runs, **Then** it reports setup failure without CLI/terminal fallback.

### User Story 3 — Thin CLI and Append-Only MCP Read Query (Priority: P2)

Operators can call the suggest seam via CLI and MCP Tool 20 (read-query only).

**Why this priority**: Matches thin-interface pattern; keeps suggestion agent-accessible.

**Acceptance Scenarios**:

1. CLI prints JSON-safe suggestion only.
2. Tool 20 appends after Tools 1–19; no confirm/ack; Tools 1–19 unchanged.
3. Invalid selectors fail closed before side-effect previews.

## Safety and Data Boundaries

- Suggest is offline read-only/zero-write: may call existing **preview** paths (`confirm=false` only) and 020-safe discovery; never `confirm=true`, never provider construction for LLM, never cache rebuild.
- Skill never auto-chains a second confirmed action in the same user request; never invents `latest`; never investment advice.
- No new side-effect mega-runner; 015–022 public contracts unchanged except append-only Tool 20.
- Suggest does not recommend 021 revalidation or republish when a bundle is already present (`report_present` only).

## Requirements

- **FR-001**: Core MUST expose `suggest_historical_verified_report_next_step(podcast_id, episode_ref)` returning an immutable suggestion.
- **FR-002**: Exact selectors only; reject empty/`latest`/`next` (casefold) before previews.
- **FR-003**: Suggestion codes MUST be bounded: `report_present` | `publish_verified_report` | `completion_action` | `blocked`. Invalid selectors MUST raise `HistoricalVerifiedReportPathInputError` before previews (not a suggestion code).
- **FR-004**: When no bundle and 019 preview is ready → recommend publish only.
- **FR-005**: When not ready → recommend at most one 016 selected action (or blocked) from preview; never recommend multiple actions.
- **FR-006**: Suggest path MUST be zero-write (tree snapshot tests).
- **FR-007**: Thin CLI `scripts/suggest_historical_verified_report_next_step.py`.
- **FR-008**: MCP Tool 20 `suggest_historical_verified_report_next_step` append-only read-query.
- **FR-009**: Portable Skill under `.agents/skills/historical-episode-verified-report-path/SKILL.md` with one-confirm-stop protocol.
- **FR-010**: No new dependency; no change to Tools 1–19 contracts.

## Success Criteria

- Operator can get one next-step for a named historical episode without writes.
- Skill contract forbids CLI fallback, retry, scheduler, and second confirm without a new request.
- Registry exact 20 tools after append.

## Assumptions

1. 016 preview with explicit `episode_ref` and `action=next` is the remediation selector.
2. 019 preview is the publish readiness authority.
3. Bundle presence uses 020-safe eligible summaries for that episode (not 021 currentness).

## Out of Scope (v1)

- Mega-tool that runs intake→semantic→publish in one confirm
- Batch multi-episode automation, scheduler, retry loops
- Changing 015–022 side-effect semantics
- Live market API, investment advice
