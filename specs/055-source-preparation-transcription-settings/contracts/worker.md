# Worker contract

One opaque job_id, one execution, no source/settings/exception stdout. Existing selected source/data/runtime inheritance and host/slot rules remain.

Payload2 reloads immutable plan.transcription, checks fresh source/profile/context/plan and CUDA capability before media, and forwards persisted model/device/compute_type to the existing source executor. Preserve force=false, progress callback and vad_filter=true.

V2 plan reload recomputes its canonical approval digest; a valid-value settings mutation with unchanged binding is corruption, not execution authority. The worker independently compares fresh and persisted settings before effects. Legacy payload/hash rules remain unchanged.

After identity/structure validation, require bounded recorded model/device/compute_type/vad_filter equal to the approved tuple before storing actual_transcription and transcript_ready. Missing/mismatched evidence gives validation_failed, never readiness/fallback. Post-effect exceptions preserve uncertainty/artifacts/slot.

Payload1 retains old hash/context/default execution only while new configuration stays absent. Explicit reconfiguration invalidates old admission before media. Do not fabricate status settings or migrate historical records.

No retry, worker replacement, cancellation, cleanup, downgrade, force, cache rebuild or downstream generation. Runtime capability is observational; later library/VRAM/model loading can still fail without fallback.
