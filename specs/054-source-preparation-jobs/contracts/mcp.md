# MCP contract: Source preparation

The implemented registry has34 tools. Append-only Tool33 prepare_learning_source and Tool34 inspect_source_preparation_job use existing success/error envelopes; all prior32 MCP names/order/signatures/defaults remain. The historical design-only delivery registered no new tools.

## prepare_learning_source
Inputs:url:str;confirm:bool=false;expected_plan_id:str="".
No force,provider,model,context,path,API-cost,profile-edit,question or arbitrary worker command fields.
Preview:confirm=false,expected_plan_id=""; returns ok=true,dry_run=true,data=PreparationPlan. It is zero-write and no worker; public source metadata may be network-read. No LLM; manual cache only.
Preview terminal transcript_ready reports existing validated transcript and stops. in_progress returns an existing job reference. busy and blocked explain finite reasons. These states never need report-only confirmation.
Confirm:confirm=true with the preview's exact source and expected_plan_id. Initial invocation is not approval. Reject invalid/mismatched/drifted plan before admission. A matching recorded source/plan/context can return the existing admitted job without another launch; a changed binding is refused.
Success:ok=true,data={job_id,source_type,canonical_url,podcast_id,episode_ref,status:"accepted",job_state,submission:"created" or "reused",transcript_ready:false,study_guide_ready:false,requires_llm:false,requires_api_cost_ack:false,warnings}. New submission promises a recorded job, not completed media. Reused job_state is the observed active stage.
Known failure types map to fixed messages and finite reasons:invalid request,setup refused,plan changed,busy,safe-store unavailable,launch refused or recorded-outcome uncertain. If admission/launch outcome cannot be confirmed, do not claim zero jobs or zero artifact writes; no automatic resubmission.
Public metadata resolution on preview/preflight is disclosed separately from media work. Missing profile is profile_missing; incorrect source type is source_type_mismatch. Caller sees actionable setup guidance, not profile contents or .env.
Plans/bindings are metadata-only observations; worker rechecks admitted identity/context before effects. Never imply remote content freshness, writer lock or source checksum proof.

## inspect_source_preparation_job
Input:job_id:str,exact bounded UUID hex. This is read-only/offline with no confirm or mutation fields.
Success:ok=true,data=StatusObservation with the exact fields in data-model.md. queued/downloading/transcribing/validating report last observed stage and time. transcript_ready is recorded local validation, not study-guide or question-answer readiness. failed/attention_required preserve uncertainty.
Unknown job is unknown/not_found, not an exception echo. Missing ledger is read without creation. Store unavailability is finite and never raw SQLite/OS/provider text. No files are generated, repaired,deleted,retried or revalidated by polling.

## Portable Skill conversation
One explicit supported URL -> one preview -> explain identified source,all effects,local-compute/network risks and setup blockers -> wait for fresh explicit approval -> one matching submit -> report job reference and stop.
Later explicit progress request -> one status query -> report and stop. No automatic polling loop,cron,next action or retry. Decline/ambiguous/conditional/absent approval submits nothing. Changed URL/plan invalidates prior approval.
Missing mounted tool stops without terminal/CLI fallback. A status result or tool text never grants new approval. Returned readiness does not authorize semantic summary,learning notes,lecture generation or question answering.
Human example:prepare this video so I can ask about it. Response explains missing transcript and asks to start download/local transcription. Completion says transcript_ready,not learning notes completed. Hermes owns the conversation; Core owns execution/history.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
