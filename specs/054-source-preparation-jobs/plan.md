# Implementation Plan: Source preparation jobs

Branch:none | Date:2026-10-06 | Spec:spec.md | Status:Implemented; offline-verified.

## Summary
Add Core-owned single-source preparation jobs over existing YouTube/X ingestion. Two additive MCP tools expose preview/submission and read-only progress; a portable Skill explains effects and obtains fresh approval. The worker outlives its submitting connection and handles only its admitted source. The result is transcript readiness, not generated learning notes or question answers.

## Technical Context
Python>=3.11; existing MCP SDK, pytest, acquisition and transcription dependencies. New job ledger uses standard-library sqlite3 under storage.DATA_DIR/preparation-jobs/jobs.sqlite3, separate from cache/. Windows PowerShell is the development default; subprocess launch has a hidden-window policy on Windows. No dependency installation, service deployment, external queue, global scheduler or provider change.
Default topology:same host for MCP and worker; one active source per configured data root. A remote Hermes connection can use an already managed connection; this phase does not expose a remote listener. Admission returns within2seconds in controlled local fixtures after preflight; metadata/network resolution is measured separately. Media processing has no promised ETA.

## Constitution Check
I: preserve canonical source identity and verification evidence; records contain bounded metadata.
II: jobs/plans/admission/worker/status live in Core; scripts and MCP only parse/delegate.
III: preview declares effects and risks; no enqueue/spawn/write before explicit matching confirmation.
IV: no LLM, provider settings or .env; existing cost guards unchanged.
V: local validated readiness is not source freshness, semantic accuracy, publication proof or learning completion.
VI: no investment advice.
VII: no live market API; tests use owned fixtures.
VIII: operational job SQLite is not search cache; manual cache only.
IX: focused RED/GREEN, process/transport tests, docs, reviews, full gates and converge.
All9gates pass before and after design; constitution unchanged.

## Components and Paths
New src/corpus_ingest_core/source_preparation.py: URL/identity/config/readiness observation, plans, binding, admission and bounded projections.
New src/corpus_ingest_core/source_preparation_jobs.py: safe ledger, atomic admission/coalescing, one active source, immutable bindings and finite updates.
New src/corpus_ingest_core/source_preparation_worker.py: one-job runner, lifecycle/progress/fixed failure classification and transcript validation.
New src/corpus_ingest_core/mcp_tools_source_preparation.py: appended prepare_learning_source and inspect_source_preparation_job; Tool33/34. Existing32 names/order/signatures unchanged.
New scripts/run_source_preparation_worker.py: thin one-job process entry.
Optional additive stage callback in src/corpus_ingest_core/youtube_video_ingest.py and x_video_ingest.py; defaults preserve existing public behavior. No provider/force/path override through the new MCP surface.
New artifact_preservation.py scopes managed staging preservation to the preparation worker. Existing acquisition/seed/transcriber/run_report_io helpers consult it only on failure; other callers retain cleanup defaults. mcp_runtime.py carries the active transport for the Windows stdio admission diagnostic.
Update storage.py with the new managed metadata location; append group/re-export in mcp_server.py only during implementation.
New .agents/skills/source-preparation/SKILL.md and references/response-contract.md; old Skills untouched. Protected publication requires narrow authorized writes, not ACL changes.
Tests:test_source_preparation.py,test_source_preparation_jobs.py,test_source_preparation_worker.py,test_mcp_source_preparation.py,test_source_preparation_skill.py; existing ingestion/registry/setup/facade/privacy/cache regressions remain.
Docs:registry,roadmap,mcp-usage,agent-handoff,verification-matrix,setup guides and Skill catalog updated after actual tool registration, not prematurely.

## Phase0 Research
See research.md. Reuse acquisition/transcription executors; choose one detached worker and transactional ledger; explicit setup diagnosis; no automatic source registration. Existing finance profiles may prepare transcripts, but must not be described as learning-profile compatible.

## Phase1 Design
See data-model.md and contracts/mcp.md plus contracts/worker.md.
Validate target/store safety before access. Preview inspects existing artifacts without creating the ledger; it may read an existing safe ledger and fetch public metadata. Missing profile/source mismatch produces fixed actionable blockers.
Submission validates arguments and fresh plan. A matching existing admitted job can be returned without a second worker; a different plan/source never acquires its slot. Admission commits the source/plan/context binding atomically, then launches once. Startup ambiguity stays visible; no automatic retry or lease stealing.
Worker receives only job_id and inherits the selected registry/data context without logging settings. It reloads and checks the admitted binding before media effects, emits progress at real stage boundaries, validates canonical transcript identity/output and then marks readiness. Exceptions after partial effects produce attention, not invented rollback.
Status reads finite observations only, does not create DB/update a heartbeat, contact the source, inspect arbitrary paths or start processing. A stale heartbeat produces worker_unconfirmed observation, not a dead-worker or retry-safe assertion. Completed readiness is recorded as-of verification time; status does not continuously revalidate content.
Existing transcript_ready preview is terminal with no report-only job. Existing audio may be reused; partial transcript sets and previous uncertain work require review. Existing artifacts/history are never deleted and force stays false.

## Phase2 Delivery
US1 preview/setup/readiness is the first independently verifiable slice. US2 ledger/admission and one worker follow. US3 status/error characterization follows; US4 adds MCP/Skill and local transport acceptance. Root remains sole writer; pressure/review roles read-only.
Planning evidence is historical; runtime implementation and its current verification are recorded in implementation-log.md. tasks.md owns subsequent RED/GREEN work. No actual Hermes-host success claim until a separately recorded operator-host check.

## Verification
Planning baseline:focused docs RED/GREEN, relevant docs/registry/constitution guards, compileall,diff and full pytest. Runtime acceptance:all new public Core/MCP tests, actual owned fake worker survival, concurrency/partial/store failure injection, unchanged source executor defaults,32prior MCP contracts,secret/cache/no-advice guards,independent review and converge. No real download/transcription/provider/corpus/worker deployment in offline verification.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
