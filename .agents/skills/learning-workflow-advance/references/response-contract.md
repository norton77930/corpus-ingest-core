# Tool32 response contract

Validate lexically; do not resolve or open returned paths. Unknown fields/types/status/reasons/cost combinations stop. Use plain booleans, matching plain-string IDs, string lists and finite enums. No arbitrary text is execution approval.

## Envelope and fields
Preview exact success envelope: ok=true,dry_run=true,data object. Confirmed success: ok=true,data object, no top dry_run. Data has exactly these23 fields:

podcast_id,episode_ref,confirm,status,reason,next_action,plan_id,requires_llm,requires_api_cost_ack,reads,writes,reuses,metadata_writes,report_writes,executed_action,output_paths,report_paths,follow_up,diagnostic_reasons,scope,dry_run,network_read,warnings.

Scope is learning_workflow_step. Preview:confirm=false,dry_run=true,network_read=false. requires_confirmation and run_mode are not part of this Tool32 schema. IDs exactly match request. Lists reads/writes/reuses/metadata_writes/report_writes/report_paths/diagnostic_reasons/warnings contain strings;output_paths maps role strings to strings. plan_id is lowercase64hex when available/executed, otherwise null. No extra keys or coercion of integers to booleans.

| Preview status | reason | follow_up | plan |
| --- | --- | --- | --- |
| action_available | next_action_available | confirm_selected_action | one supported action,plan_id,cost flags and paths |
| complete | previews_reusable | none | null action/id,all plans empty,cost flagsfalse |
| blocked | inspection_unavailable or workflow_requires_attention | manual_review | null action/id,all plans empty,cost flagsfalse |

Every preview has executed_action=null,output_paths={},report_paths=[]. Blocked/complete also have writes/reuses/metadata_writes/report_writes=[] and requires_llm/requires_api_cost_ack=false. Complete/inspection_unavailable diagnostic_reasons=[]; workflow_requires_attention has nonempty unique known diagnostic labels below. Available diagnostics=[];next_action is exactly one row below with matching cost flags.

## Owned plans
Accept either slash style by lexical comparison. Reject empty/control-character paths, dot/dotdot components, duplicates, overlaps, unexpected roles/names or mixed parents. Artifact siblings share a directory stem equal to episode_ref or starting episode_ref+'__'; its parent name equals podcast_id. Prefix may be configured/absolute; no filesystem inference or redirect checks. Reports are a distinct sibling pair under podcast_id's study-guide-runs or workflow-derivation-runs folder with names shown below. Compare full approved path strings on confirm; no normalization across requests.

| next_action | requires_llm / requires_api_cost_ack | writes roles | reuses roles | metadata_writes |
| --- | --- | --- | --- | --- |
| generate_lecture | true / true | 00,03,04,07 | none | one study_guide.lineage.json sibling |
| complete_cover | false / false | 00 | 03,04,07 | none |
| generate_derivation | true / true | 05,06 | none | one workflow_derivation.lineage.json sibling |

Role filenames:00_video_info.md,03_full_summary.md,04_learning_notes.md,07_final_study_guide.md,05_prompt_examples.md,06_apply_to_my_workflow.md. Reports:lecture/cover uses episode_ref.study-guide-run.json and episode_ref.study-guide-run.md; derivation uses episode_ref.workflow-derivation.json and episode_ref.workflow-derivation.md. No role/path outside these lists. Exactly two report_writes; metadata separate from artifact/report effects. Receipt/report/artifact paths disjoint.

Reads always start with 'local recovery and lineage metadata','existing learning previews'. Available lecture/cover adds 'canonical learning-notes semantic summary','canonical identity metadata','optional episode seed and audio metadata'; derivation adds 'existing lecture03/04/07','configured default operator workflow context'. Complete/blocked have only the two initial roles. No other read text.

Warnings:single_action_only,metadata_plan_binding_only,non_atomic_observation,summary_transcript_freshness_not_evaluated,caller_must_serialize_writers, optional cover_absence_checked_separately (cover only), and exact 'SQLite cache may be stale; rebuild cache manually. This workflow never rebuilds it automatically.' Explain these meanings,not arbitrary warning text. Unknown warning makes reply incompatible. Diagnostic labels:recovery_blocked,recovery_present,next_step_blocked,study_guide_lineage_blocked,study_guide_lineage_stale,study_guide_lineage_untracked,workflow_derivation_lineage_blocked,workflow_derivation_lineage_stale,workflow_derivation_lineage_untracked,workflow_derivation_context_not_evaluated,observations_conflict. Do not echo unrecognized diagnostic text.

## Successful confirmed reply
Require confirm=true,dry_run=false,status=executed,reason=step_executed,follow_up=preview_again,empty diagnostics. IDs, next_action,plan_id,cost flags,reads,writes/reuses/metadata_writes/report_writes match the approved preview. executed_action equals expected_action. network_read equals generation's true or cover's false. output_paths has exactly all roles for that action:00/03/04/07 for lecture/cover(including reused cover siblings),05/06 for derivation. Values equal planned owned write/reuse paths by role; report_paths equals approved report_writes. Unknown/incompatible confirmed reply is uncertain, not a reason to call again.

## Errors and uncertain outcomes
Require ok=false,error_type and message strings. Recognize a known phase only by both exact type and exact message. A different/extra/malformed/unknown pair receives generic execution-uncertain/local-inspection wording; never echo arbitrary message. Every confirmed error/transport outcome consumes the cycle.

| error_type | meaning | exact message |
| --- | --- | --- |
| LearningWorkflowPlanChangedError | new request/preview required,no retry | Learning workflow plan changed; preview again before confirming. |
| LearningWorkflowAdvanceError | files may have changed | The action may have changed local files; inspect local state before retrying. |
| LLMProviderConfigError | ack/config refused;do not claim plan drift | Confirmed generation requires the exact API-cost acknowledgement and a valid local provider configuration. |
| ValueError | invalid request | Invalid learning workflow request. |
| PodcastIngestCoreError or InternalError | generic action failure | Learning workflow action failed; inspect local state before retrying. |
| StudyGuideBundleStateError | invalid_identity | An explicit configured podcast and canonical episode reference are required; latest/next are unsupported. |
| StudyGuideBundleStateError | unsafe_path | A study-guide source or destination path is unsafe or unreadable; publication is refused. |
| StudyGuideBundleStateError | recovery_required | Existing study-guide or derivation staging/backup entries require operator review; no automatic recovery was attempted. |
| StudyGuideBundleStateError | derivation_conflict | Existing workflow derivations prevent regenerating their lecture; force does not override this protection. |
| StudyGuideBundleStateError | publish_failed | Study-guide publication failed before commit; the previous public bundle is unchanged or restored. |
| StudyGuideBundleStateError | rollback_failed | Publication and rollback failed; preserved backup/staging requires operator recovery. |
| StudyGuideBundleStateError | published_cleanup_failed | The complete study-guide bundle was published, but cleanup failed; review retained recovery entries before another operation. |
| StudyGuideBundleStateError | published_report_failed | The complete study-guide bundle was published, but its run report could not be completed; do not automatically regenerate. |
| StudyGuideBundleStateError | reused_report_failed | The existing bundle was reused, but its run report could not be completed; do not automatically regenerate. |
| WorkflowDerivationStateError | invalid_identity | An explicit configured podcast and canonical episode reference are required; latest/next are unsupported. |
| WorkflowDerivationStateError | unsafe_path | A workflow-derivation source or destination path is unsafe or unreadable; publication is refused. |
| WorkflowDerivationStateError | recovery_required | Existing study-guide or derivation staging/backup entries require operator review; no automatic recovery was attempted. |
| WorkflowDerivationStateError | publish_failed | Workflow-derivation publication failed before commit; the previous public bundle is unchanged or restored. |
| WorkflowDerivationStateError | rollback_failed | Workflow-derivation publication and rollback failed; preserved backup/staging requires operator recovery. |
| WorkflowDerivationStateError | published_cleanup_failed | The complete workflow-derivation pair was published, but cleanup failed; review retained recovery entries before another operation. |
| WorkflowDerivationStateError | published_report_failed | The complete workflow-derivation pair was published, but its run report could not be completed; do not automatically regenerate. |
| WorkflowDerivationStateError | reused_report_failed | The existing workflow-derivation pair was reused, but its run report could not be completed; do not automatically regenerate. |

Published cleanup/report failures may already have committed outputs; rollback_failed needs operator recovery. Only exact recognized publish_failed messages establish unchanged/restored old public outputs; never extend that claim to unknown errors, publication/report atomicity or crash durability. Report fixed known meanings once and stop; no automatic repair/retry.
