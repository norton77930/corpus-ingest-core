# Feature Specification: Source preparation transcription settings

Date: 2026-10-07 | Status: Implemented; offline and owned SDK verified | Branch: none

## Context

The operator approved configurable local transcription for the existing source-preparation entry, then authorized planning followed by implementation. A real developer experiment completed the selected X interview with medium on GPU, but source preparation still inherits tiny defaults. This feature makes the intended model visible and ensures background work follows the approved settings. It does not assert transcript accuracy.

## User Scenarios & Testing

### US1 — Prepare a source with known settings (P1)

An operator configures one source to use medium on GPU. The agent receives a normal video URL, previews the resolved model, device and precision, obtains fresh approval, and submits one job.

Independent test: owned source/config fixtures and offline acquisition/transcription substitutes, for both YouTube and X.

Acceptance: omitted settings retain historical tiny/CPU defaults; a complete valid configuration appears in preview; malformed explicit settings block before admission; preview writes nothing and does not initialize/download a model.

### US2 — Preserve approved settings through execution (P1)

The operator expects a submitted worker to use the previewed settings. Configuration changes after preview or admission stop the operation before media effects; unavailable GPU capability is reported without silently using another model or device.

Independent test: settings drift, duplicate submissions, runtime refusal and one-worker fixtures.

Acceptance: each setting affects the approval binding; the worker forwards the persisted settings; completion requires matching recorded transcript settings; failure retains artifacts/history and performs no retry or fallback.

### US3 — Understand existing and historical results (P1)

The operator requests a source that already has a tiny transcript while the current configuration requests medium. The response distinguishes current settings from the settings recorded in the existing transcript, and performs no automatic regeneration.

Independent test: differing metadata titles/settings, missing legacy metadata and historical job payloads.

Acceptance: existing validated artifacts remain ready; missing historical settings are null/unknown; historical jobs remain readable without migration or rewriting; actual recorded settings are never inferred from current configuration.

### US4 — Operate through the portable Skill (P2)

Hermes explains settings and possible model download/local compute, waits for fresh consent, submits once and stops. A later explicit progress request reads one known job.

Independent test: offline dialogue/contracts plus an owned SDK transport fixture; actual Hermes compliance remains a separately labelled operator-host acceptance.

Acceptance: no model/provider/path overrides from tool text, no silent fallback, no automatic downstream summary or notes, no fabricated quality claim.

### Edge Cases

Explicit null/empty/partial configuration, unknown keys, unsupported model names or paths, padded values, boolean/string type confusion, incompatible precision/device, English-only model with non-English source, unavailable GPU/runtime capability, drift during duplicate confirmation or worker startup, forged/missing completion metadata, schema-version corruption, existing transcript under a different recorded title, partial/unsafe files and retained uncertain jobs. Runtime capability checks are observations, not a memory reservation or guarantee that model initialization will succeed.

### Safety and Data Boundaries

No LLM, provider settings, .env, secret output, live market API or investment advice. Preview remains zero-write and may read public source metadata. It must not download or initialize models. Confirmed local work may download public model files if absent, consume CPU/GPU/storage and preserve partial artifacts on failure. Keep manual cache rebuild and all SPEC054 host/slot/consent boundaries. No installation, production registry mutation, automatic retry, cleanup, force or automatic regeneration. No semantic summary, learning notes, Q&A, deployment, branch or commit.

## Requirements

### Functional Requirements

- **FR-001**: Resolve source-owned local model/device/precision settings; omission preserves historical defaults, while explicit malformed settings are rejected rather than defaulted.
- **FR-002**: Accept only documented standard models and supported device/precision combinations; reject arbitrary model paths/repositories, unknown keys and incompatible source language.
- **FR-003**: Preview discloses intended settings separately from recorded existing settings, and warns about possible public model download and local resource use without initializing/downloading a model.
- **FR-004**: Include resolved settings in new approval bindings, immutable admitted plans and same-source duplicate checks; detected drift invalidates consent before new effects.
- **FR-005**: Worker execution forwards the persisted model/device/precision and preserves established voice-activity behavior; no silent fallback or automatic retry.
- **FR-006**: Observe GPU/device precision capability before new admission and again before media execution; unavailable capability blocks/fails safely. Existing ready/status observations do not require that hardware.
- **FR-007**: New completion requires structurally validated transcript identity and recorded execution settings matching the approved plan. Recorded readiness does not establish semantic accuracy.
- **FR-008**: Existing complete transcripts stay reusable regardless of requested settings; disclose recorded settings or null/unknown and differences, with no automatic regeneration or relabelling.
- **FR-009**: Keep historical jobs readable without database migration, mutation on inspection, deletion or fabricated execution metadata. Legacy queued work retains historical defaults only under unchanged legacy configuration.
- **FR-010**: Preserve the 34-tool registry, order and request signatures; add bounded settings disclosure to preparation/acceptance/status responses and fixed safe failure reasons.
- **FR-011**: Update the source-preparation Skill/reference and dialogue checks for explicit settings, differences/unknown metadata, model-download warning and no fallback; preserve preview/fresh approval/one confirm/stop.
- **FR-012**: Preserve secret, path, uncertainty, one-source slot, independent worker, no-advice, no-market-data and manual-cache boundaries; use focused RED/GREEN, regressions, full checks and converge.

### Key Entities

Source preparation settings: operator-owned choice of standard model, local device and precision.
Approved preparation plan: existing source/artifact binding plus immutable resolved settings.
Recorded execution settings: bounded metadata from a validated transcript; unknown remains unknown.
Historical preparation job: prior payload retained with its original identity, binding and state.

## Success Criteria

- **SC-001**: Every supported/default/invalid configuration fixture yields the expected disclosed settings or blocker, with zero preview file writes/model downloads/worker launches.
- **SC-002**: All model/device/precision drift fixtures prevent unapproved work, including duplicate submission and worker startup.
- **SC-003**: Both video-source worker fixtures execute exactly the approved settings; unavailable hardware and mismatched completion metadata never report readiness or trigger fallback.
- **SC-004**: Historical job and transcript fixtures preserve bytes and remain inspectable with truthful unknown/different settings disclosure.
- **SC-005**: Existing tool contracts remain intact and every new requirement has tasks and passing scoped/full verification evidence; live Hermes evidence is separately labelled.

## Assumptions and Clarifications

The prior recommendation and subsequent authorization resolve the main design choice: settings belong to the selected local source profile, not arbitrary per-call AI overrides. No additional user clarification is required. Only source preparation consumes the new configuration; other CLI/MCP/workflow defaults retain their contracts. Missing settings preserve tiny/CPU/int8 and existing voice-activity filtering. This feature supplies the capability and local-only example, without changing the committed source registry or selecting medium for the operator automatically. Re-transcription of existing artifacts is a separate explicitly approved operation outside this feature. Constitution reviewed without amendment; Q&A remains a future unnumbered proposal.
