# Feature Specification: X Video Ingest MCP Tool

**Feature Branch**: `040-x-video-ingest-mcp`
**Created**: 2026-08-19
**Status**: Implemented

**Input**: Expose the existing Spec 036 X video ingestion seam over MCP as append-only Tool 23. Core and CLI already turn a public X video URL into a corpus episode. No tool reaches that seam, so an agent cannot ingest X video without a terminal. Follow the Spec 004 → 035 precedent.

## Clarifications

### Session 2026-08-19

- Q: X only, or YouTube too? → A: **X only.** YouTube stays CLI-only (039). A later spec may copy this envelope.
- Q: Is this exposure or new capability? → A: **Exposure plus the two Core gaps HANDOFF named.** The tool is a thin wrapper over `run_x_video_ingest`. The result gains `run_mode` and `not_investment_advice`, and a confirmed run persists a metadata-only report.
- Q: Preview vs corpus dry-run? → A: **Keep the family `confirm=false` / `"dry_run": true` envelope, and name the result mode `preview`.** Preview is zero-write and **does** resolve public metadata over the network. The envelope MUST also carry `network_read: true` and `network_read_scope: "public_metadata_only"`. Docs MUST say this is not the corpus runner zero-network dry-run.
- Q: Does confirm include transcription? → A: **Yes.** Confirmed execution calls the existing full ingest (audio + seed + transcribe). MCP v1 does not expose `device`, `compute_type`, `model`, or `work_dir`. GPU stays on the CLI.
- Q: Skill? → A: **No.**
- Q: `api_cost_ack`? → A: **No.** Transcription is local. No LLM.

## User Scenarios & Testing

### User Story 1 — Preview an X URL before writing (Priority: P1)

An operator or agent supplies a public X video URL and receives a plan: identity, title, planned writes, cache-stale warning, and an explicit statement that preview read public metadata and wrote nothing.

**Why this priority**: Spec 036 already proved the Core seam. The blocker for agents is the missing tool, and the safety blocker is pretending this preview is a corpus-style zero-network dry-run.

**Independent Test**: Stub metadata resolve. `confirm=false` returns the plan, writes zero files, and never downloads or transcribes.

**Acceptance Scenarios**:

1. **Given** a valid public X status URL and a registered `x-video` profile, **When** the tool is called with `confirm=false`, **Then** the response is `ok` with `"dry_run": true`, `run_mode=preview`, `network_read=true`, `network_read_scope=public_metadata_only`, planned writes for seed/audio/transcript/report, and no files created.
2. **Given** the same call, **When** the operator reads `risks` and the tool docstring, **Then** they are told preview resolves public metadata and is not a corpus zero-network dry-run.
3. **Given** a URL that is not an X status URL, **When** preview runs, **Then** the tool returns a structured error and writes nothing.

### User Story 2 — Confirm once to ingest (Priority: P1)

After accepting the plan, the same URL is confirmed once. Core downloads with a guest token, extracts mono 16 kHz WAV, writes the seed, transcribes through the existing path, persists a metadata-only run report, and warns that cache must be rebuilt manually.

**Why this priority**: That is the existing CLI capability. Exposure without confirm is only a plan.

**Independent Test**: Stub download, extract, and transcribe. `confirm=true` writes seed, audio, transcript trio, and the run report; the source video is not under `data/`.

**Acceptance Scenarios**:

1. **Given** a previewed URL and a registered profile, **When** the tool is called with `confirm=true`, **Then** it executes the existing ingest once and returns paths plus `not_investment_advice=true` and the cache-stale warning.
2. **Given** a missing or wrong `source_type` profile, **When** confirm runs, **Then** it fails before download.
3. **Given** a completed confirm, **When** the operator inspects `data/`, **Then** there is no source video file, and SQLite cache was not rebuilt.

### User Story 3 — Append-only registry (Priority: P1)

Tool 23 appends after unchanged Tools 1–22.

**Why this priority**: The registry count is a pinned chain. Adding a tool any other way renumbers the set.

**Independent Test**: Live registry list, AST projection, Spec 029 snapshot, and governed docs all resolve to 23 with Tools 1–22 names, order, signatures, and defaults unchanged.

**Acceptance Scenarios**:

1. The registry exposes exactly 23 tools; the first 22 keep name, order, signature, and defaults.
2. The AST-derived registry projection and the Spec 029 descriptor snapshot both resolve to 23.
3. Governed docs state 23, or mark an older count as historical.

### Edge Cases

- Unregistered `podcast_id` derived from the handle: preview warns; confirm refuses before download.
- Existing audio for the same episode: plan omits a re-download; confirm reuses the file.
- Private or deleted post: metadata resolve fails closed with a Core error, no write.
- `force` on confirm: passed through to the existing transcriber only.
- Extra MCP arguments (`work_dir`, `device`, cookies, credentials): not accepted.

### Safety and Data Boundaries

- Side-effect and confirm-gated. Preview writes nothing.
- Preview is zero-write, not zero-network: it resolves public metadata so the plan is real.
- Confirmed execution downloads with a guest token only. No login, cookies, credential, or stored session.
- Accepts a source URL plus optional title/force. No arbitrary local write path. `work_dir` is not on the MCP surface.
- No LLM, no `api_cost_ack`, no `.env` read, no live market API.
- Does not rebuild the SQLite cache; the response carries the stale-cache warning.
- No investment advice.
- Ingesting one source MUST NOT modify another `podcast_id`'s artifacts.

## Requirements

- **FR-001**: MCP MUST expose `ingest_x_video(url, confirm=false, title=None, force=false)` as append-only Tool 23.
- **FR-002**: The tool MUST be a thin wrapper over `run_x_video_ingest`. It MUST NOT reimplement download, extract, seed write, or transcription.
- **FR-003**: `confirm=false` MUST return the standard action-plan envelope (`ok`, `dry_run=true`, `requires_confirmation`, `tool`, `action`, `inputs`, `writes`, `risks`, `next_step`) plus `run_mode=preview`, `network_read=true`, and `network_read_scope=public_metadata_only`, and MUST perform zero writes.
- **FR-004**: Preview MUST still resolve public metadata (existing Core behavior). It MUST NOT download video, extract audio, or transcribe.
- **FR-005**: `XVideoIngestResult` MUST include `run_mode` (`preview` or `confirmed`) and `not_investment_advice=true`.
- **FR-006**: A confirmed run MUST persist a metadata-only JSON+Markdown report through `run_report_io` under the podcast corpus directory. Preview MUST NOT write that report.
- **FR-007**: Confirmed response MUST carry the stale-cache warning and `not_investment_advice`.
- **FR-008**: Registration MUST occur in a dedicated `mcp_tools_x_video.py` group imported last, so Tools 1–22 keep their positions.
- **FR-009**: The facade MUST re-export the tool and any bounded constants tests patch through `mcp_server`.
- **FR-010**: The AST-derived registry projection MUST include the new group module and resolve to exactly 23 names.
- **FR-011**: The Spec 029 descriptor snapshot MUST be regenerated with `scripts/export_spec029_tool_descriptor_snapshot.py`, not hand-edited. The deny adapter size guard MUST move to 23.
- **FR-012**: Governed docs MUST state the live count or mark an older count as historical.
- **FR-013**: MCP MUST NOT accept `work_dir`, `device`, `compute_type`, `model`, cookies, or credentials.
- **FR-014**: No new runtime dependency. No Skill in v1. No YouTube tool in v1.

## Key Entities

- **X ingest preview**: zero-write plan built from public metadata.
- **X ingest confirmation**: one existing Core ingest plus a metadata-only run report.
- **Tool 23 `ingest_x_video`**: thin MCP wrapper, last in the registry.

## Success Criteria

- **SC-001**: An agent can preview an X video URL over MCP and see the planned writes without any file appearing under `data/`.
- **SC-002**: The same agent can confirm once and obtain audio, seed, transcript, and a run report without a terminal fallback.
- **SC-003**: A reader of the preview response can tell it used the network for metadata and did not write.
- **SC-004**: Registry is exactly 23 tools with Tools 1–22 unchanged in name, order, signature, and defaults.
- **SC-005**: Full repository regression shows no new failure outside the pre-existing Spec 026–034 blocked chain.

## Assumptions

- Spec 036 Core behavior remains the source of truth for identity, guest download, seed shape, and transcription reuse.
- Operators still rebuild cache manually when they want the new episode searchable.
- Confirmed MCP transcription may run for minutes on CPU; that is accepted for v1.
- YouTube MCP is a later package.

## Out of Scope (v1)

- YouTube or generic video ingest MCP
- A portable Skill
- Exposing `work_dir` / GPU / model on MCP
- Batch or playlist ingestion
- Credentials, cookies, or authenticated X access
- Automatic cache rebuild
- Live market API or investment advice
- Hermes live / C6 / hooks
