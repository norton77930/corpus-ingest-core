# Data Model: 047

All data is transient. No new artifacts, database, schema migration, history or cache entries.

## LearningWorkflowNextStep

Defined in the new Core module and serialized explicitly/with dataclasses.asdict through the existing tool_success convention.

| Field | Values |
| --- | --- |
| podcast_id, episode_ref | Validated exact requested identity |
| status | action_available, complete, blocked |
| lecture_mode | generation, cover_only, reuse, blocked |
| derivation_mode | not_evaluated, generation, reuse, blocked |
| blocked_stage | lecture, derivation, or null |
| reason_code | Finite contract enum |
| next_action | generate_lecture, complete_cover, generate_derivation, or null |
| suggested_call | Tool name plus arguments object, or null |
| requires_llm | Boolean for action_available; otherwise null |
| requires_api_cost_ack | Same Boolean as requires_llm; otherwise null |
| read_only, network_read | Always true, false respectively |
| source_currentness | Always not_evaluated |
| completion_basis | Always existing_preview_contracts |
| warnings | Fixed two-item list from contract; never child warnings |

Inputs: exactly two strings, no arbitrary kwargs. Invalid identity yields fixed ValueError at Core and fixed error envelope at MCP. Unexpected child execution exceptions yield fixed LearningWorkflowQueryError defined in the new module, subclassing existing PodcastIngestCoreError; never publish cause text.

## State evaluation

Start -> validated identity -> lecture preview. Lecture work -> action_available/stop. Lecture expected refusal -> blocked/stop. Lecture reuse -> derivation preview -> generation/action_available OR reuse/complete OR refusal/blocked. Inconsistent preview -> blocked unexpected_preview at its stage. Unexpected exception -> fixed error, no further child call. A later query evaluates again; there is no persisted transition or automatic action.

All child objects are discarded after projection; no raw bodies, path lists, context tool names, report destinations, timestamps or digests appear in the public model.
