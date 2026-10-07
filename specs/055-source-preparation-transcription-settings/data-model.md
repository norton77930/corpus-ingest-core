# Data model

## Source settings

Optional frozen PodcastProfile.preparation_transcription. Local mapping requires exactly model/device/compute_type canonical strings. Absence retains tiny/cpu/int8; explicit null/partial/unknown keys are invalid. vad_filter=true is the fixed existing behavior and appears in canonical projections.

Models: tiny, tiny.en, base, base.en, small, small.en, medium, medium.en, large-v3, turbo. .en requires language=en. CPU allows int8/float32; CUDA int8/float16/float32. No arbitrary model paths/repositories.

## Plan and metadata

transcription: exact model/device/compute_type/vad_filter object, persisted immutably and included in approval hashes. actual_transcription: complete bounded metadata from the identity/structure-validated JSON snapshot, or null if unexecuted/unsupported/unknown. Never infer actual metadata from configuration or a requested TranscriptAsset.

## Job versions

SQLite table/user_version=1 remain unchanged.

- JSON payload1 keeps exact historical keys/plan. Read-only status shows null settings. Queued execution retains historical defaults only while new configuration remains absent and old context/hash matches; no fabricated provenance.
- JSON payload2 requires plan.transcription and adds top-level actual_transcription, null until verified completion. Ready actual values must equal approved settings; non-ready states cannot claim actual values. Unknown versions/malformed tuples/inconsistent states remain unavailable.

Inspection does not migrate/write records. Owner tokens, one-source slot, heartbeat/staleness and uncertainty remain unchanged. Safe runtime-unavailable failure before effects releases the slot; failures after effects preserve existing uncertainty rules.
