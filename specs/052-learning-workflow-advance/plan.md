# Single-episode learning advance implementation plan
Goal: one dry-run-first MCP entry executes one approved learning action using existing Core runners.
Spec:spec.md | Date2026-10-04 | Branch:none | Execution:root inline, one writer; user approved planning+implementation.

## Technical Context
Python3.11+, existing FastMCP/pytest; no new dependencies/storage/CLI/Skill/UI. Fixed single-episode scope. Preview051 once (up to four underlying scoped queries); exactly missing00 may need one050detail plus public047/049/048 qualification. Then at most one selected extra generator preview. Confirm recomputes the same and dispatches at most one runner; no post-execution query/action/retry. Existing filesystem caps and provider/report behavior unchanged.

## Constitution Check
I local metadata/evidence;II thickCore/thinMCP;III preview lists fixed read roles and exact write classes;IV exact-ack existing provider path/no secrets;V metadata binding and scoped freshness warnings;VI no advice;VII no live marketAPI;VIII manual cache;IX TDD/reviews/full/converge.9 gates PASS before/after design, no amendment. Existing workspace required by user; no worktree/Git objects.

## Research and Design
Use public051 overview, not private051 projection helpers or MCP routing. New learning_workflow_advance.py validates IDs/control inputs, observes051 once, refuses attention except the strictly qualified missing-cover case, gets one selected public runner preview and validates exact result type/identity/modes/cost/canonical output and metadata lists. Reads are fixed role descriptions; unknown child paths/warnings/body fields never forwarded. Canonical paths constructed using existing storage functions and validated bundle stem; no new filesystem inspection. SHA256 sorted compact JSON over IDs/action/cost/write/reuse/metadata/report paths yields opaque metadata-only plan_id. No content hash/approval persistence/atomicity claim. Confirm requires exact known expected_action +64hex expected_plan_id; exact cost ack checked before observation for generation. Cover forwards empty ack. Plan drift raises fixed LearningWorkflowPlanChangedError; known child confirmed errors propagate for safe phase mapping; unknown executor exceptions warn that local files may have changed. Successful confirmed result validates actual type/identity/mode/owned outputs/reports before closed projection; unexpected post-dispatch result warns side effects may have happened. Return preview_again, no automatic remaining-action inspection.

## Planned paths
Create learning_workflow_advance.py,mcp_tools_learning_advance.py; tests/test_learning_workflow_advance.py,test_mcp_learning_workflow_advance.py,test_spec_052_learning_advance_docs.py; package052. Modify facade final import/re-export,setup validator,current32-count docs/guards. Authorized historical docs:038 tasks/checklists/completion-record,044 spec status/implementation-log closeout note. Prior runtime/Skills/042/044-051 packages preserved except044 authorized docs. No model/codec/generator/secure-helper modifications.

## Review Focus
- Invalid control/identity before query; nonplain/bool spoofed metadata (T003/T005).
- Same action but changed canonical write plan, episode or cost (T005).
- Cover changes to generation after selection: empty ack; child rejection remains (T005/T011).
- Post-publication/report exceptions and malformed confirmed result: no zero-write/retry claim (T005/T007).
- Legacy/custom/stale/recovery refusals and complete no-op; actual fixture snapshots (T003/T011).

## Delivery strategy
T001 baseline/docsRED ->T002 evidence/bookkeeping ->T003/004 previewRED/GREEN ->T005/006 confirmRED/GREEN ->T007/008 MCP ->T009/010 registry/docs ->T011 real fixture regressions ->T012 fresh read-only reviews ->T013 full gates ->T014 converge/status. Every behavior slice focused failing check first; no commits. Task ledger in implementation-log.md. No unresolved shared interfaces or self-consistency defects.

Cover qualification decision2026-10-04:actual050 treats missing00 as a partial lecture,so051 gates it. Preserve050/051 unchanged. Only when051 reports recovery_blocked/manual_review_required may052 obtain one additional public050 detail; qualify exactly absent00 with readable/current03/04/07 and valid matching study receipt,05/06 both absent(no receipt) or both complete(valid matching receipt),and all four recovery locations strictly absent/safe. Then public047 must agree complete_cover;049 must be current and048 current(if pair present) or not_generated. Any unknown/unsafe/partial/legacy/stale/custom/exception stops. This is missing-cover completion,not recovery repair. Add cover_absence_checked_separately warning. Bound:051 once plus at most050detail/047/049/048 once each,one selected extra preview and one confirmed executor. No post-execution query. Normal path stays051+selectedpreview. Prior statements requiring observed/clear mean normal path;this tightly scoped qualification is the only exception. FR002/FR003/FR011 and US1/AC2 cover it;T011 focused real fixtures prove it.
