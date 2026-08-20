# Feature Specification: YouTube Video Ingest MCP Tool

**Feature Branch**: `041-youtube-video-ingest-mcp`
**Created**: 2026-08-20
**Status**: Implemented

**Input**: Expose Spec 039 `run_youtube_video_ingest` as append-only Tool 24, copying the Spec 040 envelope.

## Clarifications

### Session 2026-08-20

Reused Spec 040 decisions:

- YouTube only (X remains Tool 23).
- Thin wrap of the existing Core ingest.
- Preview keeps `"dry_run": true`, names `run_mode=preview`, and sets `network_read=true` / `network_read_scope=public_metadata_only`.
- Confirm runs the full existing ingest (audio + seed + transcribe) and writes a metadata-only report.
- MCP does not accept `work_dir`, `device`, `compute_type`, `model`, cookies, or credentials.
- No Skill, no LLM, no `api_cost_ack`.

## User Scenarios & Testing

### User Story 1 — Preview a YouTube URL (Priority: P1)

An agent supplies a public YouTube URL and receives a plan: identity, planned writes, cache-stale warning, and an explicit statement that preview read public metadata and wrote nothing.

**Acceptance Scenarios**:

1. `confirm=false` returns `ok`, `"dry_run": true`, `run_mode=preview`, `network_read=true`, `network_read_scope=public_metadata_only`, and creates no files under `data/`.
2. A non-YouTube URL returns a structured error envelope, not a raw exception.

### User Story 2 — Confirm once (Priority: P1)

After accepting the plan, confirm writes audio, seed, transcript, and a metadata-only run report. Cache is not rebuilt.

### User Story 3 — Append-only registry (Priority: P1)

Tool 24 appends after unchanged Tools 1–23. Live registry is exactly 24.

## Safety and Data Boundaries

- Preview is zero-write, not zero-network.
- Guest token only. No cookies, credentials, or stored session.
- No LLM, no `.env`, no live market API, no investment advice.
- No automatic cache rebuild.

## Requirements

- **FR-001**: MCP MUST expose `ingest_youtube_video(url, confirm=false, title=None, force=false)` as Tool 24.
- **FR-002**: Thin wrapper over `run_youtube_video_ingest`.
- **FR-003**: Preview envelope matches Spec 040 (`dry_run`, `run_mode=preview`, `network_read`, `network_read_scope`, `not_investment_advice`).
- **FR-004**: Preview resolves public metadata and writes zero files.
- **FR-005**: `YoutubeVideoIngestResult` MUST include `run_mode` and `not_investment_advice`.
- **FR-006**: Confirm persists a metadata-only JSON+Markdown report via `run_report_io`.
- **FR-007**: Confirm warnings include cache-stale and no-advice.
- **FR-008**: New group module imported last.
- **FR-009**: Registry, AST projection, deny adapter, and Spec 029 snapshot resolve to 24.
- **FR-010**: Governed docs state 24 or mark older counts historical.
- **FR-011**: MCP MUST NOT accept `work_dir` / GPU / model / cookies / credentials.
- **FR-012**: Wrong or missing `source_type` and invalid URLs fail as structured envelopes.

## Success Criteria

- An agent can preview then confirm a YouTube URL over MCP without a terminal.
- Registry is exactly 24 with Tools 1–23 unchanged.
- Full pytest adds no non-Hermes failures.

## Out of Scope

Skill, playlists, cookies, live network confirm, Hermes live, Spec 038 `05`/`06`.
