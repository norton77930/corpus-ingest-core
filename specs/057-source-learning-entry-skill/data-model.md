# Conversation data and transitions

No new runtime entities, database or persistent workflow state.

| Entity | Fields | Validation |
|---|---|---|
| Learning request | original question/notes intent, scope, format, remaining call/character budget | User conversation only; lost intent requires clarification |
| Source reference | podcast_id, episode_ref; optional source_type/canonical_url | Known explicit IDs or validated Tool33 identity; no title-derived guesses |
| Approval | canonical_url, plan_id, configured transcription, disclosed effects | Fresh approval for one executable preview; drift stops |
| Handoff | request + source + safe job_id + approved settings if known | In current conversation; busy job never becomes this source's job |
| Evidence | source_version, ordered ordinals/text offsets, coverage | Fresh Tool35 inspect; one pinned scope/version; accumulated budget |
| Host evidence | availability, actual trace/output, source hashes, outcome | SDK/synthetic evidence cannot replace actual Hermes execution |

Transitions: request -> known ready IDs -> inspect/read/answer; URL request -> one preview -> ready -> inspect/read/answer; preparation_needed -> await approval -> one submission -> report/stop. Later progress -> one job status -> report/stop. Explicit learning continuation -> validate retained context -> one status -> matching ready -> fresh inspect/read/answer; otherwise report/stop. Completed notes do not generate formal artifacts.

Unknown, failed, attention, unsafe/malformed or source/job mismatch never transition to preparation or QA automatically. Source_changed discards mixed evidence and requires new inspect/retrieval under the existing QA contract.
