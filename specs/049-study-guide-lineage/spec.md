# Feature Specification: Study-guide lineage

Created2026-10-04. Status: Implemented. No feature branch.
Input: user requests planning the next phase and immediate implementation. Scope chosen from048 capability inventory; authorized2026-10-04. Existing dirty044-048 work is preserved.

## User Scenarios & Testing
### US1 Record actual lecture generation (P1)
As an operator I want to know which semantic summary produced my lecture.
Independent test: fake provider generates one lecture; receipt fingerprints exact consumed summary/request and staged03/04/07 bytes.
1. Given an eligible summary, when confirmed generation succeeds, then four lecture files and one receipt publish together.
2. Given a summary changes during provider execution, when queried later, then lineage is stale.
3. Given reuse or cover-only, when confirmed, then receipt bytes remain unchanged, including legacy absence.
### US2 Inspect without side effects (P1)
As an operator I want a finite current/stale/untracked/not_generated/blocked result without generating anything.
Independent test: temporary corpus state table plus forbidden-provider/writer tripwires.
1. Given complete legacy03/04/07 without receipt, when inspected, then untracked.
2. Given tracked unchanged summary/outputs/request, then current; changes return ordered roles.
3. Given malformed, foreign, unsafe or interrupted state, then blocked with a fixed reason.
### US3 See metadata before consent (P2)
As an agent user I want the preview to disclose lineage writes separately.
Independent test: actual Tool26 plans and offline Skill contract cases.
1. Given generation, then metadata_writes contains one sibling receipt; cover-only/reuse contain none.
2. Given incompatible metadata, then Skill stops before confirm.

## Requirements
- FR-001: Only actual generation writes study_guide.lineage.json; exact versioned JSON stores identity/stem hash, consumed semantic summary hash, ordered rendered request hash, recipe version and staged output03/04/07 hashes. No source bodies, settings, provider identifiers, paths or timestamps in receipt.
- FR-002: Capture inputs/request before provider construction. Hash actual staged bytes after platform newline conversion. Record complete outputs in the existing same directory publication, retaining rollback/cleanup/report failure meanings.
- FR-003: Preflight existing reserved name before provider in preview and generation, including force. Malformed/unknown schema/foreign identity blocks generation; only recognized matching receipt may be replaced. Revalidate before staging. This is the sole owned-file exception to044 regular-extra preservation.
- FR-004: Add default-empty metadata_writes to StudyGuideBundleResult and Tool26 preview/confirm. Keep existing artifact writes/reuses/report fields and five parameter signature; generation declares one receipt, reuse/cover-only none.
- FR-005: Reuse/cover-only preserve receipt bytes or absence and all other regular files. Existing05/06 still block regeneration even force; Tool25 preserves lecture receipt. No automatic regeneration, no backfill, repair or deletion.
- FR-006: Add Core inspect_study_guide_lineage and append Tool29 with exactly required podcast_id/episode_ref, preserving Tools1-28 order/signatures. Return only finite status/reason/changed_roles and explicit read_only/network_access/scope/warnings.
- FR-007: Strict duplicate-key/exact-field/type/digest validation,64KiB receipt cap,2MiB summary cap,64MiB per output cap; no links/reparse/subdirectories/special entries in managed bundles. Refuse .part/.old/.wfderive.part/.wfderive.old remnants. Expected failures become blocked, unexpected MCP errors fixed text.
- FR-008: Use current canonical transcript identity/title and learning-notes profile; no older-title fallback. Compare whole semantic summary bytes consumed by current runner, current recipe/request and03/04/07 output bytes. Ignore00 and derivation artifacts for comparison. Reading transcript metadata does not establish summary-to-transcript provenance.
- FR-009: Inspection performs no writes, provider/network access, report creation, environment loading, downloads, transcription, source completion or cache rebuild. Hash mismatch is observation, not semantic quality or authenticity proof; non_atomic_observation warning is mandatory.
- FR-010: Update study-guide-bundle Skill to validate/show metadata_writes and narrow ownership exception; preserve preview/explicit consent/one confirm/stop, exact acknowledgement and all old stop boundaries. Tool 27 suggestion and Tool28 inspection semantics remain unchanged.
- FR-011: Synchronize29-tool registry/setup/facade/current docs. Retain no advice, bounded external data and manual cache boundaries; no new dependencies.
- FR-012: TDD, targeted/full pytest, compileall and diff checks; separate read-only reviews; converge all requirements. Preserve unrelated dirty files. No branches/worktrees/commits/staging/deployments or real provider/corpus mutation.

## Edge Cases and precedence
Invalid explicit identity is a fixed ValueError before profile access. Unavailable/non-learning profile or canonical identity is blocked/identity_unavailable. Inspect safe bundle entries before recovery; unsafe_path outranks recovery_required. No03/04/07 and no receipt ->not_generated/no_study_guide. Partial outputs or orphan receipt ->blocked/incomplete_lecture. Complete legacy ->untracked/no_record before source-body read. Complete tracked: receipt validation -> identity -> summary -> outputs -> comparison. Missing/oversized/unreadable/invalidUTF8/finance-shaped summary ->inputs_unavailable; output read failure ->outputs_unavailable. Receipt unreadable/oversized ->record_unreadable; invalid ->invalid_record; schema ->unsupported_schema; foreign ->identity_mismatch. Changes ordered semantic_summary,recipe,request,output_03,output_04,output_07. Missing00 does not invalidate03/04/07 lineage. Regular unrelated files are not compared.

## Success Criteria
- SC-001: Fake generation receipt matches consumed input/request and on-disk output bytes, including LF/CRLF and provider-time mutation.
- SC-002: Every finite state/reason and role order has a public Core check; thin Tool29 fixed-error and side-effect tripwires pass.
- SC-003: Ownership collision and publication-fault checks show no unapproved overwrite and retain old state or documented recovery; reuse/cover-only/Tool25 preserve receipt.
- SC-004: Existing28 signatures/order unchanged, Tool29 appended, current docs reflect29; full regression and independent reviews close concrete findings.

## Assumptions and limits
Scope is lecture versus semantic summary only, not summary versus transcript. No automatic freshness enforcement in Tool26 reuse or Tool 27. No migration, signed receipts, model provenance, atomic inspection, crash durability or adversarial race guarantee. No UI, scheduling, batch, learning catalog, market data or vector search.

## Clarifications2026-10-04
No high-impact question remains: use048 local pattern; receipt excludes00; preserve legacy absence and stale reuse; inspect bytes of the full consumed summary, even sections omitted from rendered prompt. User explicitly authorizes plan then implementation, so no repeated design approval.
