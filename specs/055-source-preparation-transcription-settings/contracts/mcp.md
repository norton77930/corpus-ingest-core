# MCP response contract

Registry remains34 tools; request signatures unchanged. prepare_learning_source(url,confirm=false,expected_plan_id="") and inspect_source_preparation_job(job_id) remain Tools33/34. No per-call model/path/provider/force override and no silent fallback.

Add transcription and actual_transcription to preview/accepted/status data. Each is an exact model/device/compute_type/vad_filter object or null. transcription describes configured/approved execution; actual_transcription describes complete supported recorded metadata, never inferred from current settings. New ready jobs require equality. Legacy jobs without recorded settings expose null.

Preview has25 fields; accepted15; status16. Original fields/types/consent/state meaning stays unchanged. Updated strict Skill rejects missing/unknown fields and unsupported/contradictory settings.

Fixed new blockers: invalid_transcription_settings and transcription_runtime_unavailable. No raw config/backend diagnostics. Confirmation drift remains plan_changed. A worker's pre-effect runtime refusal is a finite failed status, not retry/fallback authority.

Warnings add model_download_possible for executable work, existing_transcription_unknown for ready artifacts missing supported metadata, and existing_transcription_differs for ready metadata different from current settings. At most one existing-metadata warning. Existing manual_cache, learning_documents_not_evaluated and learning_profile_incompatible remain.

Capability-only CUDA observation does not initialize/download a model or reserve VRAM. Existing ready/status needs no GPU. Preview can resolve public metadata; confirmed execution may download public model files to the operator's runtime model cache. Corpus/job write roles stay bounded to the selected data root; no arbitrary cache/path override is exposed.

Ready existing artifacts have no binding/confirmation/writes and stop. Historical/legacy settings never adopt current profile values. No LLM, automatic retry/regeneration, semantic summary, Q&A, notes or cache rebuild.
