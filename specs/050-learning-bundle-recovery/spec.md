# Feature Specification: Learning bundle recovery diagnosis
Created2026-10-04. Status: Implemented. No feature branch.
User explicitly approved the proposed SPEC050 read-only recovery scope and requested planning plus implementation. Existing044-049 dirty work remains owned by prior phases.

## User Scenarios & Testing
### US1 Observe one interrupted bundle (P1)
As an operator I want one view of the current public directory and fixed recovery siblings for one explicit episode.
Independent acceptance: temporary corpus directories, zero-write snapshots, no provider/network calls.
1. Given no recovery entries, when inspected, then clear/no_recovery_entries refers only to absence of recovery entries, not readiness/currentness.
2. Given any safe .part/.old/.wfderive.part/.wfderive.old directory, then recovery_present and manual_review_required, with all five fixed observations in order.
3. Given unsafe/unreadable state, then finite blocked result without following links or returning unknown names.
### US2 Understand recorded output consistency (P1)
As an operator I want to distinguish missing, invalid and matching receipt metadata inside each safe location.
Independent acceptance: fake-generation receipts copied into fixture siblings and corrupted/reduced-cap variants.
1. Given valid matching identity/stem and output hashes, then valid/match metadata, without claiming publication success or latest candidate.
2. Given invalid/unsupported/foreign/unreadable/orphan receipt or changed output, then finite record/output status and manual review.
3. Given legacy outputs with no receipt, then absent/not_evaluated; no backfill or body interpretation.
### US3 Use a bounded MCP query (P2)
As a client I want an appended read query with existing safe envelope and no execution options.
Independent acceptance: exact two-parameter Tool30, delegation/no-leak/registry/docs guards.
1. Given explicit IDs, then one Core call returns metadata only.
2. Given invalid IDs, then fixed ValueError before profile access; unexpected failure is fixed InternalError.

## Requirements
- FR-001: Add Core inspect_learning_bundle_recovery(podcast_id,episode_ref) and append-only Tool30. Require two explicit identities; reject latest/next, paths, empty/padded/invalid IDs before filesystem/profile access. Preserve Tools1-29 order/signatures and semantics.
- FR-002: Resolve current canonical transcript identity/title under learning-notes profile; derive original bundle stem. No old-title fallback, caller paths, timestamp ordering, glob of recovery directories or persisted path authority. Unavailable/ambiguous/deep malformed identity ->blocked/identity_unavailable.
- FR-003: Inspect exactly public,lecture_part(.part),lecture_old(.old),derivation_part(.wfderive.part),derivation_old(.wfderive.old), in that order. Absent root/leaf is not unreadable; unknown lstat/listing failures are never absence. Reject unsafe ancestors/leaf and unsafe direct child entries before body reads. No links/reparse/subdirectories/special files. Max256 direct entries per location via bounded secure listing.
- FR-004: Return fixed role presence00/03/04/05/06/07, lecture completeness for00/03/04/07, derivation completeness05/06, extra regular-file count and both receipt assessments. No arbitrary filenames, absolute paths, bodies, digests, settings, provider identifiers or exception text in public data. Extras are statted but never opened.
- FR-005: Decode existing strict048/049 receipt codecs at64KiB cap. Validate explicit podcast/episode plus original stem hash even for recovery sibling names. Valid receipt comparisons only concern actual local output bytes, capped64MiB per output. Missing/unreadable/mismatched outputs are finite outcomes. No input/request/recipe freshness comparison and no proof of authentic publication.
- FR-006: Finite top states clear/recovery_present/blocked, fixed reasons, manual_review_required bool and warnings including diagnostic_scope_only,non_atomic_observation,publication_outcome_not_proven. Any blocked location outranks recovery; unsafe_path outranks inspection_unavailable. Safe recovery presence requires manual review. Without recovery, partial file groups or invalid/orphan/mismatched/unreadable receipts ->blocked/manual_review_required. Clear means only no recovery/anomaly observed within scope.
- FR-007: Expected read/parse/path/profile failures are finite and private; no partial body reads from a refused location. Unexpected MCP exceptions produce fixed error text. Bound identity read64MiB, listing256 entries, receipt64KiB, output64MiB, at most five independently Core-derived locations.
- FR-008: Query is read-only, zero-network, zero-provider, zero reports/cache/environment loading. No automatic repair, deletion, rename, generation, source completion, retry, backfill or cache rebuild; no cleanup commands, suggested recoverable winner or execution authorization returned. Set read_only=true and network_access=false.
- FR-009: Do not change Tools25-29, their generators/Skills, receipts or recovery refusal behavior. No investment advice, market API, new dependencies, CLI, UI, batching, learning search or recovery executor.
- FR-010: TDD, current targeted/full pytest, compileall/diff check, independent read-only behavior/engineering reviews, converge and current30-tool docs/setup/facade guards. Preserve prior dirty files; no branch/worktree/commit/staging/deploy.

## Edge Cases and precedence
Invalid explicit identity ->ValueError; unavailable profile/canonical identity ->blocked/identity_unavailable with locations=[]. Successful identity produces exactly five fixed location rows even if absent or blocked. Blocked rows have unknown role presence/completeness and not_evaluated receipts; absent rows have false role presence, absent groups and absent receipts. Safe observed rows do not list extra names. Partial lecture group includes cover-only absence; this diagnosis does not authorize or replace Tool27 decisions.
Receipts: status absent/valid/invalid_record/unsupported_schema/identity_mismatch/record_unreadable/not_evaluated; output_status not_evaluated/missing/unavailable/mismatch/match; changed_roles contains only ordered output roles on mismatch. Valid/match does not establish freshness, latest candidate, successful swap/report/cleanup or safe deletion. All observations remain non-atomic.

## Success Criteria
- SC-001: Public location/state table covers all four remnant families and mixed combinations, absence/unsafe/unreadable precedence, without mutation.
- SC-002: Both receipt types have schema/identity/output cap and comparison fixture coverage including original stem in siblings and legacy absence; no names/content leaks.
- SC-003: Tool30 appends after29 exact contracts; no execution parameters, fixed errors, bounded reads and forbidden-side-effect checks pass.
- SC-004: All10 requirements have task/test evidence; full regression and two read-only reviews close concrete findings; converge has no unmet work before completion.

## Assumptions and Clarifications2026-10-04
Routine design resolved from044/046/048/049 and approved proposal; zero clarification questions. Diagnose one canonical learning episode only. No mutation of actual corpus for development. Matching receipt/output means recorded local bytes match, not newest/trusted/current inputs. Every recovery entry requires human review; nothing authorizes deletion or retry. Existing unfinished directory states are preserved byte-for-byte. No recovery executor in050.
