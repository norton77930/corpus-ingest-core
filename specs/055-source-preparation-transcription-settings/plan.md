# Implementation Plan: Source preparation transcription settings

Branch: none | Date: 2026-10-07 | Spec: [spec.md](spec.md) | Status: Implemented; offline and owned SDK verified

## Summary

Source-owned preparation_transcription resolves a bounded immutable model/device/compute_type tuple. Tool33/34 disclose requested and recorded settings; new plans bind/persist settings, and the worker forwards them to the existing video executor. Registry remains34 tools; request signatures remain unchanged. Preserve old records/defaults with no silent fallback or regeneration.

## Technical Context

Python>=3.11; existing dataclasses/PyYAML/MCP/pytest/faster-whisper/CTranslate2. No added dependency or installation. CUDA preflight lazily queries device count and supported precision only; no model/cache initialization or download, memory reservation or library-load guarantee. Model loading can fail later without fallback. Native Windows new submissions retain the stdio blocker; existing managed loopback HTTP supports background lifetime.

SQLite columns/user_version remain unchanged. Exact JSON payload versions1/2 coexist without migration. New version2 persists transcription and actual_transcription; version1 remains readable, unchanged on inspection, and does not gain fabricated settings.

## Constitution Check

I: retain identity and bounded recorded evidence; unknown stays unknown.
II: Core owns parsing/probing/binding/storage/execution; MCP/CLI remain thin.
III: zero-write preview, disclosed model download/resource risks, matching confirmation.
IV: no LLM/.env/provider access; existing cost gates unchanged.
V: structural readiness is not accuracy/source freshness/learning completion.
VI/VII: no investment advice or live market API.
VIII: manual cache rebuild only.
IX: focused RED/GREEN, scoped/full checks, fresh read-only review and converge.

All nine gates pass at design; constitution unchanged. User explicitly authorized implementation after planning; no branch/commit/worktree or another optional approval ceremony.

## Design and Paths

See research.md, data-model.md, contracts/mcp.md, contracts/worker.md and quickstart.md.

- preparation_transcription.py: new frozen value, strict finite names/combinations, safe configuration errors, lazy capability check and bounded recorded-metadata projection.
- models.py/config.py: optional PodcastProfile.preparation_transcription, consumed only by source preparation; other executors keep their defaults.
- source_preparation.py: requested/actual disclosure, context/plan bindings, difference/unknown/model-download warnings and selected validated JSON snapshot preservation.
- source_preparation_jobs.py: exact dual payload validation, immutable nested settings and recorded completion, unchanged SQLite schema/read-only inspection.
- source_preparation_worker.py: drift/capability checks, persisted kwargs, verified matching metadata before new readiness, historical compatibility and no fallback.
- mcp_tools_source_preparation.py: finite safe new reasons, unchanged signatures/order.
- .agents/skills/source-preparation/SKILL.md and references/response-contract.md: bounded settings disclosure and unchanged fresh approval/single confirm/stop.
- tests/test_preparation_transcription.py, tests/test_source_preparation_transcription.py, existing preparation/jobs/worker/MCP/Skill/config fixtures and new spec docs tests.
- docs/mcp-usage.md, install-and-porting.md, agent-handoff.md, verification-matrix.md, roadmap.md, specs/README.md and AGENTS.md plan marker. No production registry edits.

## Compatibility

Absent mapping retains tiny/cpu/int8 and vad_filter=true. Present mapping requires exactly model/device/compute_type. Models: tiny/base/small/medium and English-only .en variants, large-v3, turbo. English-only models require language=en. CPU supports int8/float32; CUDA int8/float16/float32. Arbitrary paths/repositories are refused.

New hashes include resolved settings. Legacy workers use historical hash/context rules only while the new mapping stays absent. Existing ready transcripts are inspected before capability/launch checks and never overwritten; recorded metadata may differ or be unknown. New completion requires recorded model/device/compute_type/vad_filter equal to the persisted tuple. Historical completion rules remain unchanged; historical status settings are null.

## Verification and Delivery

Root is sole writer; research/reviews read-only. Sequential RED/GREEN slices: config, preview/binding, ledger compatibility, worker, MCP/Skill, docs. Owned media substitutes/process/SDK tests prove settings/lifetime, not live Hermes compliance. Any optional authorized real-source check must be isolated and reuse existing audio/cache.

Run scoped tests, full pytest with short basetemp, compileall src scripts and diff check. Git ownership workaround is process-local and limited to this repository. Never alter global Git settings. Converge adds only genuine uncovered tasks after implementation. Record all results and limits in implementation-log.md.
