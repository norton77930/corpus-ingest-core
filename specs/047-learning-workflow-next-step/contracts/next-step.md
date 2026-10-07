# Contract: Learning Workflow Next Step (Tool 27)

## Entry points

Core: `suggest_learning_workflow_next_step(podcast_id: str, episode_ref: str) -> LearningWorkflowNextStep`.
MCP: same required arguments; standard `tool_success` / `tool_error` envelopes. No confirm, force, api_cost_ack, context, provider, path, latest or batch parameter. Read-query; not tool_action_plan and no dry_run flag. Tools 1-26 retain their existing contracts; this query is appended.

## Decision matrix

| Lecture preview | Derivation preview | status / next_action | requires_llm / requires_api_cost_ack |
| --- | --- | --- | --- |
| Valid generation | Not called | action_available / generate_lecture | true / true |
| Valid cover-only | Not called | action_available / complete_cover | false / false |
| Valid reuse | Valid generation | action_available / generate_derivation | true / true |
| Valid reuse | Valid reuse | complete / null | null / null |
| Expected refusal | Not called | blocked / null, stage lecture | null / null |
| Valid reuse | Expected refusal | blocked / null, stage derivation | null / null |
| Inconsistent result | Not called further | blocked / null, failed stage | null / null |

For action_available, suggested_call.tool is generate_study_guide_bundle for either lecture action, derive_workflow_bundle for derivation. suggested_call.arguments contains only podcast_id, episode_ref, confirm:false, force:false. No ack literal, no dispatch. For complete/blocked, suggested_call=null. blocked_stage is null except blocked. See data-model.md for every required output field.

Reason enum: lecture_generation_needed, cover_completion_needed, derivation_generation_needed, previews_reusable, lecture_prerequisite_failed, derivation_prerequisite_failed, unsafe_path, recovery_required, derivation_conflict, unexpected_preview. Exact normal mapping follows row order. Complete reason is previews_reusable.

## Child result validation

Before projection require exact requested identity and confirm is False. Lecture run_mode must be dry-run; derivation run_mode must be preview. reused must be a Boolean; planned_writes/planned_reuses must be lists of distinct nonempty strings with no overlap. No unexpected public shape is silently coerced. Reuse requires zero writes and four lecture reuses / two derivation reuses. Nonreuse lecture requires either four writes/zero reuses and projected requires_llm=true, or one write/three reuses and projected requires_llm=false. Nonreuse derivation requires two writes/zero reuses. Derived lecture bundle_dir and derivation lecture_dir must match lexically before complete/action projection; do not resolve untrusted returned paths. The query performs no additional file reads from result paths.

Malformed result or projection raises no raw serialization exception: return blocked with unexpected_preview. A child-call exception is handled separately below. Completion means only both existing previews report reusable at query time; empty/stale 05/06 can satisfy that existing contract. The query is not an artifact content validator.

## Refusals and safe errors

- Query validates identity before child/config access using existing public storage validation; reject latest/next case-insensitively, invalid types/blanks/traversal; preserve valid case/underscores. Core ValueError and MCP error_type=ValueError have fixed message `Invalid explicit episode identity.`
- Typed child state reasons unsafe_path and recovery_required -> blocked with same reason; lecture derivation_conflict -> blocked derivation_conflict. Child invalid_identity -> fixed identity error. State reasons relevant only to confirmed publication, or unknown typed reasons -> blocked unexpected_preview.
- Non-state StudyGuideBundleError -> blocked lecture_prerequisite_failed; non-state WorkflowDerivationError -> blocked derivation_prerequisite_failed. Other expected PodcastIngestCoreError (configuration/profile errors) or ValueError from a child -> its stage-specific prerequisite_failed. Test fixed-class handling without arbitrary exception type names.
- All other child exceptions -> fixed LearningWorkflowQueryError; MCP error_type=LearningWorkflowQueryError and message `Learning workflow query could not be evaluated safely.`. MCP's own unexpected exception -> error_type=InternalError with the same fixed message.
- Never str(exc), dynamic class names, raw child warnings/results, raw paths, prompts, transcript, context lists or body excerpts in output. No catch/retry/force/repair fallback.

## Fixed informational fields

Always read_only=true, network_read=false, source_currentness=not_evaluated, completion_basis=existing_preview_contracts. warnings always exactly:
1. `Completion reflects existing preview reuse only; content quality and source freshness are not verified.`
2. `This query authorizes no execution; preview and approve the selected operation separately.`

These fields concern the query. A later successful confirm writes reports even for reuse; this query writes no reports. Metadata here does not replace the full execution preview, cost acknowledgement or current-state revalidation.

## Acceptance case families

C01 identity/refusal/order; C02 lecture generation; C03 cover-only; C04 derivation generation; C05 both reuse with limited completion meaning; C06 generic prerequisites; C07 typed recovery/unsafe/conflict; C08 partial 05/06/context errors; C09 invalid child shape/mode/identity/bundle directory; C10 unknown exception/private sentinels; C11 zero writes/network/provider/cache and bounded child counts; C12 append-only registry/envelopes/signatures and unchanged 045 protocols. All offline.
