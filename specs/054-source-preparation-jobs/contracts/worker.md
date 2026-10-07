# One-source worker contract

Root remains the sole implementation writer. Runtime worker is a separate process owning one admitted job, not a generic scheduler. Offline tests start only owned fixture workers; no production worker deployment or service installation occurred.

## Ownership and launch
Job admission transaction claims one active source per selected data root before launch. Duplicate matching requests return that job without another spawn. Other sources return busy. Worker loads immutable job/source/approved-plan/context,claims its exact owner token and refuses an incompatible or unknown record.
Use the repo interpreter and thin scripts/run_source_preparation_worker.py with bounded job_id only. Carry the selected registry/data context consistently; do not log or persist complete settings/environment. Windows launch uses hidden-window creation flags; no visible interactive helper.
MCP/client exit does not kill the admitted worker. The worker processes one source then exits; it never starts another job. No service installation,deployment,remote listener or unapproved host configuration change.

## Execution and progress
Recheck source identity/context and declared roles before effects. Existing public media acquisition/transcription executors stay authoritative; force=false and no arbitrary options. Optional bounded stage callbacks are additive and unused by old callers.
Emit downloading,transcribing,validating only at actual corresponding boundaries. Heartbeats are metadata observations. Validate complete canonical TXT/SRT/JSON and matching episode identity before terminal transcript_ready.
No LLM,.env,provider settings,semantic summary,lecture/derivation,Q&A or automatic cache. No percent/ETA. Metadata/report-write failure is not equivalent to no output publication.

## Interruptions and failures
There is no automatic retry,lease stealing,cleanup,rollback or restoration. Preserve partial files and history. Known pre-effect refusal is failed; uncertain launch,worker disappearance,partial artifacts or ambiguous publication is attention_required with a fixed safe reason.
Status is read-only:it may derive worker_unconfirmed from stale observations but cannot infer worker death or rewrite the job. A later manual attempt needs inspection and a fresh plan/approval; this phase adds no retry executor.
Atomic admission prevents duplicate active ownership; it does not promise exactly-once filesystem publication across crashes. Process tests must prove survival after client disconnect without real source calls.

## Finite ownership observations
Follow the30second heartbeat/120second stale-observation defaults and slot_state rules in data-model.md. A timeout is not a termination proof. Reserved/active slots remain occupied on ambiguous launch or owner loss;only verified refusal/termination releases them. No code path steals a lease or starts a second worker from stale status. This phase offers no automatic recovery executor.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
