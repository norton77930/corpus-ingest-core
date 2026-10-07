# Feature Specification: Single-episode learning workflow advance

**Feature Branch**: None (user prohibits branch/worktree creation)
**Created**: 2026-10-04
**Status**: Implemented
**Input**: User approved one MCP entry to preview/confirm exactly one learning action and requested038/044 completion-record cleanup.

## User Scenarios & Testing
### US1 - Preview one learning action (P1)
An operator names one episode and sees whether lecture generation, cover completion or derivation generation is next, including cost and planned artifact/metadata/report writes.
Why: remove manual reconciliation across existing diagnostic/generation tools. Independent test: temporary local fixture + write/provider/network tripwires.
1. Given a ready learning-notes summary without lecture, preview selects generate_lecture with required cost acknowledgement and exact file plan, without writes/provider.
2. Given a current lecture lacking its cover or derivation, preview selects complete_cover (no LLM) or generate_derivation (LLM).
3. Given both bundles are reusable and current, preview reports scoped complete with no action; confirmed calls cannot manufacture a reuse/report action.

### US2 - Confirm only the approved action (P1)
An operator returns the preview action and metadata-only plan identifier and explicitly confirms one operation.
Independent test: injected state/plan drift and fake temporary provider integration.
1. Given unchanged eligible plan and valid acknowledgement when needed, exactly one existing runner executes; no chained follow-up query/action/retry/cache rebuild.
2. Given changed action/cost/write plan or a recovery/stale/untracked/custom/unknown observation, stop before dispatch and request new preview/manual review.
3. Given publication/report failure, preserve existing phase-specific failure meaning; no rollback claim or automatic retry. Failed/malformed result after dispatch warns that files may have changed.

### US3 - Use MCP and accurate completion records (P2)
Agent clients get one appended Tool32 with explicit identity and dry-run defaults;038/044 records reflect repository evidence.
Independent test: MCP envelope/signature/count/facade guards plus historical package evidence tests.
1. Given explicit IDs, thin MCP delegates once; response contains finite metadata only, never caller acknowledgement or private exception text.
2. Given old documents disagree with implemented code, update completion markers and cite current checks without inventing new live evaluation.
3. Given newTool32 registration, Tools1-31 names/order/signatures remain unchanged.

### Edge Cases
Invalid/padded/path/latest/next IDs or nonboolean confirm rejected before any child call. Confirm requires explicit known expected_action and lowercase64hex expected_plan_id. Cost-bearing actions require existing exact acknowledgement before inspection/dispatch. Preview accepts no confirmation bindings and ignores acknowledgement. Cover confirmation always passes empty ack to child, preventing a later generation race from acquiring cost authorization. Missing sources are not filled. Recovery remnants or unsafe/unknown locations always stop;051 manual_review_required for exactly missing00 may qualify through the strict cover checks below; stale/untracked/custom provenance and conflicting observations require manual review. Each request recomputes status; at most one selected extra preview and one confirmed runner. Failed confirmation stops with no retries. All scoped observations are non-atomic; callers serialize writers.

### Safety and Data Boundaries
A single action per confirm, force=False. No automatic repair, deletion, regeneration chain, summary production, download, transcription, scheduler, newCLI/UI/Skill/dependency/live market provider or investment advice. Preview zero writes/environment/provider/network; confirmed generation uses existing exact-ack guarded provider path only. Reports belong to existing child runner; no duplicate coordinator report. Manual cache rebuild. Tools1-31 and prior Core/generator/codec/secure-reader/Skill code preserved. Only authorized038/044 completion documents may change. No branch/worktree/commit/staging/deployment or real provider/corpus/cache operations during development.

## Requirements
- FR-001: One explicit episode and strict parameter validation before any query; two required IDs, confirm=False, expected_action='', expected_plan_id='', api_cost_ack=''. No caller force/provider/context/path surface.
- FR-002: Preview uses existing051 overview once; normal path requires observed/clear recovery with no attention. A strictly qualified missing-cover-only case may use public050detail/047/049/048 as defined below; all other attention outcomes block. Validate identity/scope/read-only/network/action/cost metadata; unknown/failed observations block. Current or not_generated lineage only; other states require manual review.
- FR-003: Select only generate_lecture/complete_cover/generate_derivation. Get one extra preview of selected existing runner with confirm=False,force=False; reject action/mode/cost/shape/path disagreement. Return planned reads (fixed role descriptions), artifact writes/reuses, lineage metadata writes and child report writes. Complete is scoped preview reuse only, zero executor/report writes.
- FR-004: Return deterministic metadata-only plan_id binding episode/action/cost/writes/reuses/metadata/report paths. Confirm requires expected action/id and recomputes both; mismatch stops before dispatch. The identifier is not a content digest, secret, persistent approval or file lock and does not claim byte snapshots/source freshness.
- FR-005: Generation confirmation requires existing exact API-cost acknowledgement before inspection or provider; preview never uses it. Cover confirmation ignores supplied acknowledgement and delegates empty value. Never synthesize/default/return acknowledgement.
- FR-006: Confirm delegates exactly once to selected existing Core runner, confirm=True,force=False, default context/provider. No MCP-to-MCP routing, retries, second action, post-dispatch query, report duplication or automatic cache rebuild.
- FR-007: Return finite metadata result with executed action, canonical outputs/report paths and explicit preview_again follow-up. Never return source bodies/provider data/private child warnings/unknown fields. Failed or malformed post-dispatch result must not imply zero side effects.
- FR-008: Preserve phase-specific child publication/rollback/cleanup/report errors through fixed safe MCP messages; unknown failures warn inspect before retry. Drift uses fixed plan-changed error. No arbitrary exception text.
- FR-009: Append thin MCP Tool32 advance_learning_workflow; dry-run first, existing ok/data/error envelopes with top dry_run on successful previews. Current registry/setup/docs/count guards updated32; first31 exact contracts preserved.
- FR-010: Reconcile038 task/checklist completion and044 implemented status with existing code/test evidence; preserve historical22/26 tool snapshots and distinguish offline verification from historical live-confirm evidence. Do not amend prior runtime behavior.
- FR-011: Preview/blocked/complete paths have zero writes/provider/environment/network/cache/report execution. Real integration uses only owned temporary fixtures and fake providers; before/after byte snapshots prove no preview mutation.
- FR-012: Full Spec Kit/TDD, targeted/full tests, compileall/diff, independent fresh read-only review and converge; root sole writer, baseline protected-file/31-contract audit.

## Key Entities
Learning step preview = explicit IDs + selected action + metadata plan + opaque metadata binding. Confirmed step = same plan + one existing runner result + explicit stop/follow-up marker. No new persistence/artifact family.

## Success Criteria
- SC-001: One entry previews all three supported actions and scoped completion without new writes or external calls.
- SC-002: Every invalid identity/binding/ack, blocked observation and detected plan drift prevents confirmed dispatch.
- SC-003: Every eligible confirm executes at most one existing runner and preserves existing output/report failure distinctions.
- SC-004: Tool32/current docs agree, first31 contracts unchanged,038/044 completion records have evidence.
- SC-005: Requirements mapped to tasks/tests, independent findings closed, full checks pass and convergence has no unbuilt work.

## Assumptions and Clarifications
2026-10-04: user approved recommended single-step MCP/Core design and immediate implementation; zero repeated approval needed. No critical unanswered question. Narrow metadata binding adds expected_plan_id to protect approved file-plan changes; it does not pin file contents. Existing generators recompute at confirm and may observe concurrent changes: caller serialization required, no new locking/TOCTOU guarantee. Refused/unknown provenance can be handled manually through existing tools; new entry never force-regenerates. Alternatives rejected: client-only routing leaves manual coordination; multi-stage automatic completion expands authorization and rollback scope. Constitution9 principles unchanged.

Cover qualification decision2026-10-04:actual050 treats missing00 as a partial lecture,so051 gates it. Preserve050/051 unchanged. Only when051 reports recovery_blocked/manual_review_required may052 obtain one additional public050 detail; qualify exactly absent00 with readable/current03/04/07 and valid matching study receipt,05/06 both absent(no receipt) or both complete(valid matching receipt),and all four recovery locations strictly absent/safe. Then public047 must agree complete_cover;049 must be current and048 current(if pair present) or not_generated. Any unknown/unsafe/partial/legacy/stale/custom/exception stops. This is missing-cover completion,not recovery repair. Add cover_absence_checked_separately warning. Bound:051 once plus at most050detail/047/049/048 once each,one selected extra preview and one confirmed executor. No post-execution query. Normal path stays051+selectedpreview. Prior statements requiring observed/clear mean normal path;this tightly scoped qualification is the only exception. FR002/FR003/FR011 and US1/AC2 cover it;T011 focused real fixtures prove it.
