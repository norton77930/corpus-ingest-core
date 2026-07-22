# Feature Specification: Episode Verified Research Report Workflow

**Feature Branch**: `019-episode-verified-research-report-workflow`

**Created**: 2026-07-22

**Status**: Implemented

**Input**: For one **explicit** podcast episode reference (including historical episodes), preview readiness then, after confirmation, assemble and atomically publish an 018-equivalent verified research report when local artifacts and lineage already pass—without LLM, download, RSS, or `api_cost_ack`.

## User Scenarios & Testing

### User Story 1 — Preview Readiness for a Named Episode (P1)

An operator supplies `podcast_id` and an explicit `episode_ref` (for example `EP650`). Preview inspects local artifacts and lineage only, returns a strict zero-write plan: ready vs blocked roles, risks, and whether a matching bundle can be adopted. It never resolves “latest,” never contacts RSS, and never requires acknowledgement text.

**Why this priority**: Historical episode reporting is the primary product gap after 018 (latest-only).

**Independent Test**: Call preview with a fixture-ready episode and a fixture-missing episode; assert zero filesystem writes and distinct ready/blocked inventories.

**Acceptance scenarios**:

1. Given `confirm=False` and a non-empty explicit `episode_ref`, when preview runs, then it writes no checkpoint, staging directory, report bundle, lineage file, or child artifact.
2. Given a reserved selector (`latest`, `next`, or casefold equivalents), when preview or confirm is requested, then the request is rejected before any owned side effect.
3. Given missing or stale required roles, when preview runs, then the result is non-writing and lists each missing/stale role and gate in metadata-only form.

### User Story 2 — Confirm Assemble and Publish When Ready (P1)

After preview, the operator confirms with the same exact `episode_ref` (and optional `stock_query` / fixture flags). Confirmed work does **not** call LLM providers, does **not** require `api_cost_ack`, does **not** download or transcribe, and does **not** invoke 015/016/017/research child runners. It validates transcript identity, current lineage, review exact `passed`, assembles the classified report, and atomically publishes or reuses the digest-versioned bundle.

**Why this priority**: This is the shippable MVP outcome—same report quality as 018 for any named episode that is already prepared.

**Independent Test**: With a complete fixture tree and valid lineage, confirm once; assert `completed` or `reused` and the three-file bundle. With one role removed, assert `blocked` and no publish.

**Acceptance scenarios**:

1. Given all required local artifacts and lineage quality gate pass, when confirm runs, then `report.json`, `report.md`, and `manifest.json` publish atomically under `v1-{source_digest}` (or an identical valid bundle is reused).
2. Given any required role missing, stale, or review not exact `passed`, when confirm runs, then outcome is `blocked`, no new bundle is published, and the result lists missing/stale roles.
3. Given confirmation with a different `episode_ref` than intended operational selection (empty, whitespace-only, or reserved selector), when confirm runs, then rejection occurs before assembly or claim acquisition.

### User Story 3 — Safe Reuse and Fail-Closed Conflict (P2)

A later confirmation for the same episode and options reuses a complete matching bundle without rewriting, and fails closed on conflict or source mutation.

**Why this priority**: Operators re-run reports without duplicating digests when sources are unchanged.

**Independent Test**: Confirm twice on identical fixtures → second `reused`; mutate one source byte → fail closed or new digest, never silent corrupt reuse.

**Acceptance scenarios**:

1. Given identical sources and a valid existing manifest/bundle, confirmation reuses without a second publication.
2. Given changed sources or a conflicting final directory that does not fully match expected bytes, publication fails closed (or produces a new digest version when assembly legitimately changes).

## Safety and Data Boundaries

- Preview is strict zero-write.
- Episode selection is **explicit `episode_ref` only**; casefold-reject reserved latest/next selectors at Core and MCP early gates.
- Confirmed work is assemble/publish only: **no** RSS, **no** environment/provider construction for LLM, **no** `api_cost_ack`, **no** download/transcription, **no** semantic summary generation, **no** re-review writer, **no** research workflow child dispatch, **no** automatic 015/016/017 chaining.
- Report classification, source safety, lineage quality gate, atomic three-file publish, and no-investment-advice rules **reuse 018’s report contract** (same payload classifications and bundle layout).
- No live market API, no scheduler, no multi-episode batch, no force/partial/retry, no output-path override, no automatic cache rebuild, no investment advice.
- Blocked results are metadata-only (role names, gate categories); no transcript body, secrets, or traceback dumps.
- 018 latest-episode workflow, 015–017 public contracts, and the prior MCP tool order remain intact; 019 appends one tool.

## Requirements

- **FR-001**: The Core MUST expose `run_episode_verified_research_report_workflow` with `confirm=False` default and a required explicit `episode_ref` parameter on all modes.
- **FR-002**: Preview MUST be strict zero-write and MUST NOT resolve RSS latest, construct LLM providers, or read `.env` for provider secrets.
- **FR-003**: Confirmed execution MUST reject missing/blank `episode_ref` and casefold-reserved selectors (`latest`, `next`, and agreed equivalents) before claims, assembly, or publication.
- **FR-004**: Confirmed execution MUST NOT require `api_cost_ack` and MUST NOT call LLM provider factories.
- **FR-005**: Confirmed execution MUST NOT download audio, transcribe, run 015 semantic remediation, 016 completion, 017 latest deterministic, or `run_research_workflow` child stages.
- **FR-006**: Assembly and publication MUST reuse the existing verified-report assembler/publisher/lineage gate used by 018 (same digest versioning, classifications, source safety, and three-file atomic bundle rules).
- **FR-007**: Adoption/assembly MUST require valid transcript contract, identity-valid canonical transcript resolution (no 019-owned transcript picking via lineage/manifest alone), current semantic review exact `passed` with hash binding, and full required lineage roles for the requested options.
- **FR-008**: Optional `stock_query` and `include_fixture_verification` MUST follow the same assembly option semantics as 018 when present; when absent, stock/fixture roles are not required.
- **FR-009**: When readiness fails, outcome MUST be `blocked` (or equivalent terminal blocked) with an explicit inventory of missing/stale roles and failed gates; the inventory MUST NOT name automatic next runner invocations as executable side effects.
- **FR-010**: Successful paths MUST support `completed` (new publish) and `reused` (identical valid bundle) with per-bundle exclusive claims and source revalidation as in 018 publish semantics.
- **FR-011**: Checkpoints, if written, MUST be metadata-only under the episode’s verified-research path, subordinate to artifact truth, and MUST NOT be written on preview or early rejection.
- **FR-012**: Thin CLI, sixteenth MCP tool, portable Skill, setup validator, and docs MUST preserve dry-run-first, explicit episode approval, no live market API, and no investment advice; MCP registry becomes exactly **16** reviewed tools with prior fifteen order preserved and 019 appended.
- **FR-013**: Existing 015–018 public contracts MUST remain compatible; 018 remains the latest-only path that may run upstream stages under ack.
- **FR-014**: Public results MUST be JSON-safe sanitized metadata only (no raw transcript, secrets, credential assignments, unsafe URI data).
- **FR-015**: Portable Skill protocol MUST be: preview (`confirm=false`) → human supplies exact `episode_ref` (and options) → one confirmed MCP call → report once → stop; no CLI fallback, retry loop, or second side-effect tool.

## Assumptions (resolved in grilling; no open NEEDS CLARIFICATION)

1. Product type is capability extension; first gap is historical/specified-episode report, not catalog or multi-podcast.
2. Confirm depth is assemble+publish only (not B/C full ladder).
3. Surfaces are Core + CLI + MCP tool 16 + Skill.
4. No `api_cost_ack` because no LLM.
5. Episode selection is local explicit ref only; no RSS for 019.
6. Blocked lists roles/gates only; no auto-suggested runner names as v1 requirements.
7. Report body/layout equals 018 verified report contract.

## Key Entities

- **Explicit episode reference**: Operator-supplied canonical episode ref (not latest/next).
- **Readiness inventory**: Metadata listing required roles and whether each is present, stale, or failed gate.
- **Verified report assembly / bundle**: Same entities as 018 under `data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/`.
- **Optional checkpoint**: Metadata-only episode verified-research checkpoint if confirm reaches terminal persistence.

## Success Criteria

- Operator can preview any explicit historical episode with zero writes and see ready vs blocked roles.
- Operator can confirm a fully prepared historical episode and receive the same class of verified report bundle as 018 without providing `api_cost_ack`.
- Confirm never triggers LLM, download, RSS, or corpus child runners.
- Reserved selectors never reach assembly.
- Identical sources yield reuse; conflicts/source mutation fail closed.
- MCP registry has exactly 16 reviewed tools; tools 1–15 contracts and order unchanged.
- No investment advice and no live market API behavior is introduced.

## Out of Scope (v1)

- Web UI, scheduler, multi-episode batch, embedding/vector search
- Live market API, investment advice engine
- Upstream stage execution (intake/download/transcribe/summary/review/research)
- Report catalog/search/export feature (candidate future package)
- Second-podcast onboarding feature (configuration may still accept any configured `podcast_id`)
- Extending 018 tool in place instead of appending tool 16
