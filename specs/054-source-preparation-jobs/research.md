# Source preparation research and decisions

Date:2026-10-06. Repository evidence is the primary design input; no live source or private settings were accessed during planning.

1. `youtube_video_ingest.py` and `x_video_ingest.py` already resolve metadata, derive identity, check registration, acquire audio, call local transcription and write reports. Reuse these executors with bounded optional progress hooks; do not duplicate media logic or let a Skill implement it.
2. Both ingest previews contact the public source but write nothing. Confirm refuses missing/wrong source profiles before download. Diagnose this explicitly; do not automatically edit committed or local registry files.
3. `corpus_episode_completion_workflow_runner.py` advances one selected stage; the latest deterministic runner reaches semantic-summary readiness. Neither is a general persistent background preparation job manager. Existing single-action consent protocols remain unchanged.
4. `learning_bundle_recovery._canonical_bundle` requires a learning-notes source. EP679's finance profile therefore returned identity_unavailable, mapped upward to recovery_blocked. New preparation must report configuration incompatibility directly and distinguish transcript readiness from lecture readiness.
5. An existing x-raytar lecture was found despite no learning source in the selected default registry. Inspect declared local artifacts separately from configuration eligibility; never infer that a file does not exist from a missing profile.
6. A Skill-only chain is smaller but makes long execution and reconnect behavior depend on agent context. Choose Core-owned persisted jobs plus a single-source detached worker. No Hermes runtime/provider fork, sidecar revival, generic queue or new third-party dependency.
7. Use a separate standard-library SQLite job ledger under `data/preparation-jobs/`; it is operational metadata, never the transcript-search cache. Atomic admission transactions enforce one active source and coalesce duplicates across MCP processes sharing the same data root. Safe managed-parent/store checks precede access; ambiguity blocks instead of opening redirected stores.
8. A dedicated short-lived worker owns one admitted job. A client/MCP disconnect does not terminate it. Worker/store uncertainty never triggers automatic re-execution. Stalled state is a diagnostic observation, not proof the worker is dead; no automatic lease stealing.
9. Reuse optional progress events around actual executor stages. No percent-complete or ETA. Worker heartbeats and process outcomes distinguish active metadata from interrupted/uncertain work; events contain finite codes only.
10. V1 does not automatically register sources, import platform captions, generate semantic summaries, answer questions, generate lectures or rebuild cache. These are separate future scopes; public URLs do not authorize external LLM calls.

## Hermes integration evidence

The official [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp), consulted2026-10-05, documents local stdio and HTTP server connections and startup tool discovery. This supports a portable MCP/Skill approach; it does not prove the operator's Hermes version, mount, data root, worker lifecycle or Skill compliance. Runtime acceptance must record those checks separately and never read or print complete Hermes settings or `.env`.

## Resolved planning defaults

Single-host worker per selected data root; one active source; no automatic retry or profile mutation; job records retained without purge; metadata-only status; fresh plan approval; force=false; unchanged current32 tools until implementation. Topology question affects setup examples/host acceptance, not the Core request contract. Unknown or unsafe stores, artifacts and ownership refuse admission. No open requirement ambiguity is being hidden as implemented behavior.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.

Native Windows lifecycle references: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [nested job inheritance](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs), [immediate-job query scope](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject). Local installed MCP SDK assigns a kill-on-close Job to the stdio server. Actual owned-process failures exposed the venv-launcher ancestor limit; product does not modify SDK/host policy.
