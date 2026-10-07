# Source preparation data model

The runtime implements the shapes below. Canonical public URL is source identity, not execution authority. No transcript/prompt/chat/question/secret bodies in the ledger. Current verification is recorded in implementation-log.md.

## PreparationPlan
source_type:x-video or yt-video; canonical_url:public canonical supported URL; podcast_id and episode_ref:explicit resolved identity; status:action_available,transcript_ready,in_progress,busy or blocked; reason:finite decision code.
plan_id:lowercase64hex for action_available, otherwise null. Bind canonical identity, selected data/config context digest, observed file-role metadata and stages. No byte-snapshot, remote-freshness or lock guarantee.
stages:download when needed,transcription,validation; reads,writes,reuses:bounded role/path lists. Job-store effects separately declared. requires_confirmation:true only action_available; requires_llm=false; requires_api_cost_ack=false.
network_read reflects actual public metadata resolution. transcript_ready is based on validated canonical artifacts at readiness_verified_at. study_guide_ready=false always:054 neither evaluates nor generates lectures, even if separate lecture files exist.
Known blockers:unsupported_source,metadata_unavailable,profile_missing,source_type_mismatch,unsafe_path,inspection_unavailable,partial_artifacts,previous_outcome_unconfirmed,store_unavailable. Finance-vs-learning mismatch is disclosed as downstream_lecture_not_evaluated/learning_profile_incompatible, not used to deny otherwise supported transcript preparation.
No arbitrary warnings/errors; partial or unknown observations cannot become an empty/reusable plan.

## PreparationJob
job_id:opaque lowercase UUID hex; schema_version:1; source_type/canonical_url/podcast_id/episode_ref; approved_plan_id; configuration-context digest; created_at,updated_at,heartbeat_at and readiness_verified_at UTC timestamps; owner token and worker metadata; immutable declared roles; finite status/stage/reason; bounded outcome flags.
Admission and slot claim use one transaction; a coalesced source/plan has one job_id and owner. A different source returns busy. Same URL with incompatible plan/context never launches a second worker.

## State transitions
queued -> downloading -> transcribing -> validating -> transcript_ready.
If audio is reusable, queued -> transcribing. A successful download alone never reaches transcript_ready.
Each active stage may end in failed or attention_required. Worker launch failure before processing may be failed/launch_failed; uncertain launch or partial effects is attention_required/outcome_unconfirmed.
No automatic transition from failed/attention_required into queued; no automatic retry. No new source is processed on completion. Read-only status may report attention_required/worker_unconfirmed for stale owner observations without mutating the record or claiming death.

## StatusObservation
job_id,podcast_id,episode_ref,status,reason,stage,created_at,last_observed_at,readiness_verified_at,transcript_ready,study_guide_ready,read_only,network_access,warnings.
read_only=true;network_access=false;study_guide_ready=false. Stage reports the last observed event, not percent-complete. transcript_ready is true only for a recorded validated terminal result.
Unknown reference:status=unknown,reason=not_found,nullable identity/times/stage,false readiness. Unsafe/unavailable store:bounded attention result with no raw path or exception. No absent-store creation or schema mutation in status.

## Retention and safety
Records remain local operational history; no TTL purge, cache rebuild or credential persistence. Validate safe managed root, ledger and SQLite sidecars before use; reject links/reparse/unsafe paths. Do not open a missing ledger during preview/status. Bounded rows/events/strings; no arbitrary job path, SQL or settings inputs. The owner metadata does not establish authentication or exactly-once publication after a crash.

## Concrete limits and slot ownership
Input URL<=2048characters;job_id=32lowercasehex;each serialized job<=64KiB;at most1024retained jobs per store. Capacity exhaustion refuses a new job without deleting history. Transcript inspection<=64MiB per owned file and directory enumeration<=256entries;limit excess is blocked inspection,not absence. No raw bodies persisted.
Heartbeat cadence30seconds;after120seconds without an observation,status may report worker_unconfirmed. Clock ambiguity also requires attention;no ETA or inference of death.
slot_state=reserved,active or released,independent of the human-facing diagnostic. Ambiguous startup or an unconfirmed worker retains its occupied slot;stale status never frees it. Known refusal before any worker start or verified worker termination may release the slot through the owner/admission protocol. Preserved partial artifacts still block a new attempt for that source. If ownership cannot be established,return attention/busy and require operator handling outside this phase.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
