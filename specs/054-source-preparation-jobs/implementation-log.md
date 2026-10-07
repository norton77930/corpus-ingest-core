# SPEC 054 implementation evidence

Status: implemented; offline-verified. Root is the sole writer. No branch, worktree, commit, deployment or live source/provider invocation.

## Preflight

Explicit SPECIFY_FEATURE_DIRECTORY selects specs/054-source-preparation-jobs. Official check-prerequisites with -Json -RequireTasks -IncludeTasks selected the absolute package. requirements checklist 8/8 and safety checklist 9/9 are complete; no extensions.yml hooks exist. Constitution is unchanged. The user explicitly approved implementing the planned Skill/MCP/Core scope in the existing dirty workspace.

A 748-file runtime baseline is retained locally under .pytest-tmp/54-runtime-baseline.json. The prior 32 MCP names, order, signatures and schemas are frozen under .pytest-tmp/54-prior-registry.json. Neither snapshot includes private settings or .env.

## RED / GREEN slices

- T004 ledger RED: 15 failed in 3.05s (.pytest-tmp/54jobs-red), missing module. T005 GREEN: 15 passed in 4.82s (.pytest-tmp/54jobs-green).
- T006 source/approval RED: 24 failed in 5.68s (.pytest-tmp/54preview-red), missing module. First Core GREEN exposed a real drift classification error: 1 failed, 38 passed in 5.89s (.pytest-tmp/54core-green).
- T008 follow-up RED: 2 failed, 23 passed in 4.28s (.pytest-tmp/54preview-fixes-red): missing configuration returned profile_missing after approval, and ready transcripts hid an unsafe declared audio path. Minimal fixes reclassify detected confirmation drift and inspect all declared paths before readiness. T007–T010 GREEN: 40 passed in 9.50s (.pytest-tmp/54core-green2), exit 0.
- T011 progress RED: 2 failed, 42 deselected in 2.01s (.pytest-tmp/54hooks-red): both existing executors lacked the optional progress_callback. T012 adds finite stages and resolved identity at actual execution boundaries, with no events in preview and defaults preserved. Its verification follows.

All tests use owned temporary registries, stores and artifacts, with public metadata/network acquisition faked. Current evidence does not prove real Hermes mounting or host behavior.

T012 verification: tests/test_youtube_video_ingest.py, test_x_video_ingest.py, test_source_preparation.py, test_source_preparation_jobs.py and test_data_dir_fixture_contract.py with --basetemp=.pytest-tmp/54hooks-green: 101 passed in 68.36s, exit 0. T004-T012 are complete.

T013/T015 worker and launch RED: 11 failed in 5.50s (.pytest-tmp/54worker-red). T014/T016 GREEN: 51 passed in 23.11s (.pytest-tmp/54worker-green). Status/path/metadata follow-up RED: 7 failed, 40 deselected in 5.83s (.pytest-tmp/54bounds-red). T017-T020 GREEN: 58 passed in 20.74s (.pytest-tmp/54bounds-green). T021 actual owned-process proofs: 2 passed, 11 deselected in 13.24s (.pytest-tmp/54process); submitting process exited before worker completion, and termination of the specifically recorded owned worker retained audio and its execution slot. No live media or provider calls. T013-T021 are complete.

## MCP, host lifecycle and independent review

MCP initial RED:11 failed/1 deselected (missing newtools), then the real SDK test exposed a test import-order defect (global Popen patch before SDK type annotations). After fixture correction, native stdio revealed a real lifecycle failure: accepted queued jobs never reached acquisition after client disconnect. An immediate Job policy check alone did not fix nested venv-launcher ancestry. Windows stdio new admissions now fail with worker_host_incompatible; matching existing jobs still coalesce. No SDK/host policy is changed. Existing independent loopback HTTP is supported, not deployed by this feature. Native owned SDK HTTP submit/disconnect/later status:14 passed in30.42s (.pytest-tmp/54transport-green), exit0. This is actual SDK transport execution with fake acquisition/transcription, not Hermes execution or live source work.

Host/error focused RED:8 failed/24 deselected in33.59s (.pytest-tmp/54host-red). Launch failures now retain only safely recorded job_id. All fixtures are owned and fixed; no provider/source download occurred. Failed host/probe experiments are retained locally as evidence, not reported as passes. The early compatible-stdio test was rejected as insufficient and replaced with actual supported HTTP transport; no claim of compatible Windows stdio execution is made.

Independent fresh-context read-only reviews: /root/review_054_engineering and /root/review_054_behavior. Both read standards and requirements separately; no reviewer mutated files or ran tests. Findings: mixed-case .env guard; real executor cleanup of partial managed artifacts; readiness returning before every directory scan; finance incompatibility not projected; first-store cross-process initialization. Root reproduced review cases:4 failed/3 passed in11.21s (.pytest-tmp/54review-red); mixed-case/initialization RED3 failed/1 passed in7.11s (.pytest-tmp/54review-red2); seed/report publication RED2 failed/1 passed in3.36s (.pytest-tmp/54publication-red). Scoped preservation, all-directory scan, safe profile rechecks, casefold guard, persisted warning and transactional zero-byte initialization GREEN:73 passed/2 deselected in36.33s (.pytest-tmp/54review-green). Tests cover real lower-level extraction/publication helpers with owned I/O failures; old defaults remain unchanged.

Public empty-reservation follow-up RED:1 failed/32 deselected in1.16s (.pytest-tmp/54race-public-red); read-only observation of an empty reservation no longer initializes or blocks it. Re-review identified stdio coalescing regression:RED1 failed/1 passed/32 deselected in2.11s (.pytest-tmp/54coalesce-red); host refusal moved after compatible active-job matching.

Skill original RED:10 failed in8.42s (.pytest-tmp/54skill-red), missing publication/reference/oracles. Published only new Skill/reference and appended catalog through narrow authorized protected writes; no ACL/provider/global installation changes. Re-review identified documented error vs actual message envelope; actual error contract added, RED2 failed/9 passed in8.42s (.pytest-tmp/54skill-green1), including a case-sensitive instruction-check defect. Reference now uses actual ok/message/error_type/reason/optional job_id; instruction checks ignore capitalization. Static dialogue oracles are explicitly labelled non-agent execution and now include actual-shaped progress observations. No actual Hermes mounting/compliance claim.

Registry focused RED5 failed/28 passed in8.78s (.pytest-tmp/54registry-red). First registry GREEN1 failed/32 passed in21.57s (.pytest-tmp/54registry-green) exposed bare tool-name documentation omission; fixed names retained alongside signatures.

Tool runner intermittently failed before PowerShell startup with wait for runner spawn_ready. Those failures are infrastructure errors, not test results; affected commands were retried.

## Final regression evidence

- Broad runtime/ingestion/registry/facade/setup acceptance:195 passed in99.93s, exit0 (.pytest-tmp/54target). Final source/job/Skill/docs/HTTP/fixture/console acceptance:139 passed in115.95s, exit0 (.pytest-tmp/54final-target).
- Additional readonly-store RED:1 failed/20 deselected in1.07s (.pytest-tmp/54wal-red). A WAL-format database could create SQLite sidecars during observation. Core now rejects WAL/SHM entries and noncanonical SQLite journal versions before opening; the final targeted run includes the passing no-mutation check. No database conversion, deletion or cleanup was added.
- Implemented-lifecycle docs RED:1 failed/3 passed in2.58s (.pytest-tmp/54closeout-docs-red); current package/registry/roadmap now disclose implemented runtime,34 tools and the Windows stdio restriction. Final status waits for the full gates.
- Both independent reviewers closed with no remaining actionable findings after the focused fixes. They reviewed the runtime, actual SDK transport fixtures, Skill reference and labelled dialogue oracles; actual Hermes compliance and remote hosting remain unverified.
- Exact registry freeze:current34 tools; prior32 names/order/Python signatures/input schemas equal the saved baseline, exit0. Existing MCP parameters did not change. Core ingestion has the approved additive keyword-only progress_callback=None, documented and unused by default.
- Full attempt .pytest-tmp/54full was interrupted after an early failure; it is not a full-suite pass. Reproduction with -x (.pytest-tmp/54firstfail):1 failed/53 passed in37.39s. tests/test_contracts.py still expected the old Core ingestion signature. The guard now includes the approved optional callback and asserts its None default and keyword-only form; targeted contracts/registry/YouTube/X:67 passed in10.60s, exit0 (.pytest-tmp/54core-contract). No runtime change was needed.
- compileall -q src scripts returned exit0. git diff --check returned exit0 with line-ending warnings. Staged diff is empty. The748-file baseline audit currently reports only43 explicitly scoped existing paths changed, with no unrelated mutation; final audit follows bookkeeping.

Current full rerun: .\\.venv\\Scripts\\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/54full2 --tb=short. Git safe.directory is added only through process-local GIT_CONFIG_* environment entries, without changing Git configuration files. The completed results are recorded under Final gates and convergence below.


Tool-count follow-up: full rerun54full2 exposed three remaining existing Tool30/31/32 guards with len(tools)==32. Focused RED:3 failed/32 passed in10.78s (.pytest-tmp/54other-slots-red). Only their current total changes to34; the original slot/schema/facade assertions remain. Targeted MCP recovery/advance/status plus registry GREEN:50 passed in19.09s, exit0 (.pytest-tmp/54other-slots-green). These test changes require a fresh full run after54full2 finishes.

As-built package wording now separates historical planning from implemented34-tool runtime and names actual SDK HTTP acceptance plus the stdio blocker. Focused docs:4 passed in0.65s, exit0 (.pytest-tmp/54docs-asbuilt). A documentation tool call did not acknowledge after several minutes and its orchestration was terminated; direct file inspection identified the incomplete quickstart portion, which was applied with byte-preserving replacements. No runtime process was terminated by that recovery.

Current baseline audit:748 recorded files,46 explicitly scoped existing changes,702 protected files unchanged,15 scoped new paths,0 unexpected changed/new paths and0 staged paths; exit0 (.pytest-tmp/54-final-audit.py). An initial new-file inventory mistakenly included11 existing egg-info build metadata files omitted from the original source baseline. Their recorded timestamps predate this phase (2026-08-22/29), and Git diff for both packaging directories is empty. The audit now excludes packaging metadata from new source inventory; no cleanup or installation occurred.


## Requirement evidence inventory

The following inventory supports final convergence; completed gate and convergence results are recorded below.

| Requirement | Implementation and focused evidence |
| --- | --- |
| FR-001 | source_preparation._source/_resolve; unsupported/canonical YouTube/X URL fixtures |
| FR-002 | _profile/context_digest; missing/type/mixed-case env/registry drift checks |
| FR-003 | _artifacts/validate_transcript_ready; reusable audio, complete/partial/unsafe/all-directory fixtures |
| FR-004 | _preview; byte-preserving zero-write preview and absent-ledger checks |
| FR-005 | prepare_learning_source; exact binding, changed identity/config/artifact refusal before admission |
| FR-006 | jobs.admit/launch_worker; quick acknowledgment, fixed recorded launch/outcome classifications |
| FR-007 | transactional one-slot ledger; eight threaded submissions and two owned first-creation processes |
| FR-008 | one-job worker; owned submitter exit and actual SDK HTTP disconnect/reconnect; unsupported Windows stdio refused |
| FR-009 | jobs.update/inspect; truthful boundary hooks, timestamp/stale/clock/unknown/offline projections |
| FR-010 | canonical TXT/SRT/JSON validation; wrong identity/completed/segment output failure; study_guide_ready always false and finance warning |
| FR-011 | scoped artifact_preservation; actual acquisition/seed/transcript/report failure and owned-worker interruption checks |
| FR-012 | bounded metadata/IDs/records/directories/store, safe ancestors/sidecars and fixed safe MCP errors |
| FR-013 | portable Skill/reference and22 labelled dialogue cases; no polling/fallback/downstream chain, static oracles only |
| FR-014 | saved32-tool name/order/signature/schema freeze, additive33/34 and default-preserving Core callback; current34 count guards |
| FR-015 | focused RED/GREEN evidence, actual owned processes/transports, two independent read-only reviews, full gates and final convergence |
| FR-016 | owned fake metadata/media, no LLM/provider/.env/live market API; manual-cache/no-advice/privacy regressions |

SC-001: source/setup/readiness fixtures plus zero-write snapshots. SC-002: test_launcher_uses_only_fixed_command_context_and_hidden_window times confirmation below2seconds with metadata faked; independent gated-worker/SDK tests prove acknowledgment precedes completion. SC-003: atomic duplicate/different-source thread/process admission. SC-004: actual owned SDK client disconnect then later status with transcript_ready and study_guide_ready=false. SC-005: launch/publication/interruption/heartbeat/store failure injections retain bounded uncertainty and artifacts. SC-006:22 recorded dialogue cases and actual-shaped response fields, explicitly not live agent behavior. SC-007: frozen prior MCP contracts, protected hash audit, targeted/full gates and reviews.

US1/AC1-3 map to preview/setup/readiness tests; US2/AC1-3 to quick confirmation/coalescing/drift tests; US3/AC1-3 to finite status/validated readiness/interruption tests; US4/AC1-3 to consent/missing-tool/stop-on-transcript dialogue oracles and backend response tests. All12 acceptance scenarios have evidence with actual Hermes acceptance expressly excluded from offline claims.


## Paths changed in this implementation phase

This list is relative to the748-file start-of-implementation snapshot and excludes earlier044-053 work and existing packaging metadata. Existing approved files have scoped edits; all other recorded files match their original bytes.

### New files

- `.agents/skills/source-preparation/SKILL.md`
- `.agents/skills/source-preparation/references/response-contract.md`
- `scripts/run_source_preparation_worker.py`
- `specs/054-source-preparation-jobs/implementation-log.md`
- `src/corpus_ingest_core/artifact_preservation.py`
- `src/corpus_ingest_core/mcp_tools_source_preparation.py`
- `src/corpus_ingest_core/source_preparation.py`
- `src/corpus_ingest_core/source_preparation_jobs.py`
- `src/corpus_ingest_core/source_preparation_worker.py`
- `tests/fixtures/source_preparation_dialogues.json`
- `tests/test_mcp_source_preparation.py`
- `tests/test_source_preparation.py`
- `tests/test_source_preparation_jobs.py`
- `tests/test_source_preparation_skill.py`
- `tests/test_source_preparation_worker.py`

### Modified existing files

- `.agents/skills/README.md`
- `README.md`
- `docs/agent-handoff.md`
- `docs/ai-development-framework.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/claude-mcp-setup.md`
- `docs/codex-mcp-setup.md`
- `docs/install-and-porting.md`
- `docs/mcp-readiness.md`
- `docs/mcp-usage.md`
- `docs/roadmap.md`
- `docs/verification-matrix.md`
- `scripts/validate_mcp_setup.py`
- `specs/054-source-preparation-jobs/contracts/mcp.md`
- `specs/054-source-preparation-jobs/contracts/worker.md`
- `specs/054-source-preparation-jobs/data-model.md`
- `specs/054-source-preparation-jobs/plan.md`
- `specs/054-source-preparation-jobs/quickstart.md`
- `specs/054-source-preparation-jobs/research.md`
- `specs/054-source-preparation-jobs/spec.md`
- `specs/054-source-preparation-jobs/tasks.md`
- `specs/README.md`
- `src/corpus_ingest_core/mcp_runtime.py`
- `src/corpus_ingest_core/mcp_server.py`
- `src/corpus_ingest_core/run_report_io.py`
- `src/corpus_ingest_core/storage.py`
- `src/corpus_ingest_core/transcriber.py`
- `src/corpus_ingest_core/x_video_ingest.py`
- `src/corpus_ingest_core/youtube_video_ingest.py`
- `tests/test_ai_governance_docs.py`
- `tests/test_architecture_spec_docs.py`
- `tests/test_console_entry_points.py`
- `tests/test_contracts.py`
- `tests/test_mcp_learning_bundle_recovery.py`
- `tests/test_mcp_learning_workflow_advance.py`
- `tests/test_mcp_learning_workflow_next_step.py`
- `tests/test_mcp_learning_workflow_status.py`
- `tests/test_mcp_server_facade_boundary.py`
- `tests/test_mcp_setup_validation.py`
- `tests/test_mcp_tool_registry_contract.py`
- `tests/test_mcp_workflow_derivation.py`
- `tests/test_spec_020_verified_research_report_catalog_docs.py`
- `tests/test_spec_054_source_preparation_docs.py`
- `tests/test_x_video_ingest.py`
- `tests/test_youtube_video_ingest.py`


Late title-boundary investigation:two initially failing supplemental assertions (.pytest-tmp/54title-red,2 failed/23 deselected in5.56s) incorrectly required refusal when public title metadata changes between worker preflight and executor. Inspection confirms the worker already passes title=approved_plan.title, so both executors retain approved filenames and final transcript title; this is metadata approval binding, not a remote freshness guarantee. No runtime defect or code change resulted. The supplemental checks now verify two metadata observations, successful readiness and every emitted artifact belonging to the approved writes. Their post-full result is recorded separately; they were added after full54full3 collection.


## Final gates and convergence

Full54full2 result:3 failed,2702 passed,26 skipped in1413.25s, exit1. Exactly the reproduced Tool30/31/32 current-count guards failed; all other cases passed. The failure is retained as evidence and superseded by the fresh post-fix full run.

Final full command: .\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/54full3 --tb=short. Actual result:2705 passed,26 skipped in1350.66s, exit0. All skipped cases report native symlink creation OSError; simulated reparse/nonplain-path checks ran. No live source/provider was invoked.

Convergence selected054 with official check-prerequisites -Json -RequireTasks -IncludeTasks; no extensions.yml hooks exist. Inspected16 functional requirements,7 success criteria,12 acceptance scenarios,9 plan decisions and9 unchanged constitution principles. Build findings:0 missing,0 partial,0 contradictions,0 unrequested;0 new tasks. During assessment tasks.md stayed byte-for-byte identical (SHA256 B39C6E9C164CCDBD5A622B7B8778961C102CDEF94982239F9C2D33ACA26F5C46). Administrative completion checkboxes and implemented lifecycle are updated separately after the full gate. No code/spec/plan/task rewrite was performed by the converge assessment itself.

Plan decisions checked:existing Python/dependency/Core boundary; separate bounded operational SQLite/history; one-source transactional coalescing; one fixed-context hidden worker with supported independent transport; finite readonly status; canonical transcript validation and explicit non-learning readiness; optional progress/scoped preservation with old defaults; appended MCP33/34 with32 frozen contracts; portable consent Skill and operator docs.

The offline implementation is complete. Actual Hermes mounting/agent compliance remains unverified; Windows stdio new jobs are refused, and operator-managed independent HTTP hosting is required there. Missing source profiles remain a diagnosed manual prerequisite. Readiness is structural validation as-of its timestamp, not semantic quality or remote freshness. No automatic retry/repair/cleanup/cache rebuild or downstream Q&A/learning generation. No branch,worktree,commit,staging,installation or deployment. Final administrative docs/compile/diff/protected audit results are recorded below after verification.


Supplemental post-full title-pinning checks:2 passed,23 deselected in5.34s, exit0 (.pytest-tmp/54title-pinned). No runtime code changed after full54full3; these two additional cases were not part of that full run.


Final administrative checks: .\.venv\Scripts\python.exe -m pytest -q tests/test_spec_054_source_preparation_docs.py tests/test_spec_registry_status_consistency.py tests/test_docs_registry_count_consistency.py tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/54admin-final --tb=short ->22 passed in25.21s, exit0. compileall -q src scripts ->exit0. git diff --check ->exit0,39 line-ending warnings. Final748-file audit ->46 scoped existing edits,702 protected unchanged,15 authorized new files,0 unexpected edits/new paths and0 staged paths, exit0. Completion metadata guard confirms31/31 unique tasks closed, all current package lifecycle statuses offline-verified, and exact full/supplemental evidence retained. Both independent review axes remain closed with0 actionable findings; the late title investigation required no runtime fix.


## 2026-10-06: user-authorized local real-source acceptance

The user supplied https://x.com/NateWiki/status/2106893534980685927 and explicitly requested local testing before their later Hermes port. This was an owned developer integration harness, not a live execution or compliance claim for the operator Skill in Hermes. Only this configured X source was tested live; acquisition/transcription were not faked. Existing profiles/corpus, failed-job history, model caches and search cache were not repaired, purged or rebuilt. No branch, commit, deployment, package installation, host-policy change, local secret .env or external LLM was used.

The real-source run exposed one missed worker-context bug: a claimed, already running worker called _preview(ignore_job_id=...) and redundantly checked whether it could spawn another child. A read-only subprocess launched with the actual creation flags returned worker_host_incompatible, which the worker mapped to plan_changed before media writes. In the parent context the approved/fresh plans were otherwise identical. The minimal fix in source_preparation.py skips _worker_flags only in the internal claimed-worker preflight; public preview/admission and launcher guards remain unchanged. No public API, MCP schema or worker policy was widened.

RED: .\.venv\Scripts\python.exe -m pytest -q tests/test_source_preparation_worker.py -k running_worker_does_not_require_permission --basetemp=.pytest-tmp/54-worker-host-red --tb=short -> 2 failed, 25 deselected in 1.65s, exit 1. Both X/YouTube workers returned 1 instead of 0 when their own child-launch policy was refused after admission. GREEN/regression: source_preparation, jobs, worker, MCP and Skill files -> 107 passed in 57.06s, exit 0 (.pytest-tmp/54-worker-host-green). The existing public-host/stdio refusal coverage still passes.

Preserved live attempts:
- .pytest-tmp/054-real-x-20261006-natewiki: job 76af79cb8d7a44f9bd59e42d53e4d11a stopped before download with plan_changed; the job record was preserved.
- .pytest-tmp/054-real-x-20261006-natewiki-fixed: job 8d56c04dbe184e14a47a6a08a1dee555 downloaded the actual interview WAV (127844284 bytes), then reported attention_required/outcome_unconfirmed at transcription. The default personal HF cache did not contain tiny according to a local-files-only probe. Audio/seed/job records were preserved; the job was not resubmitted or repaired.
- .pytest-tmp/54x3: public tiny model preloaded into a writable workspace-local HF cache; an intact copy of the prior downloaded WAV was reused in a new isolated fixture. One matching MCP preview/confirm submitted job 690d62a2e45345c88b4daee8db835f89. SDK disconnect followed by new status sessions observed background transcription/validation to transcript_ready. The passing job performed real local transcription and reused prior real acquisition; it did not redownload the video. The temporary loopback HTTP host was stopped after completion.

Passing evidence: waveform 16000 Hz, mono, 16-bit, 3995.1325s; the public extractor reports 3995.066s for the intended quoted interview, distinct from the separate 2282s talk on the page. WAV SHA256 stayed 423c6b5498952413669f20844ada15425a9198f6dd887a96764cf4e319fdc13f. Canonical English TXT/SRT/JSON passed validation with completed=true, 653 segments and last segment ending at 3994.99s. Tool34 reports transcript_ready and study_guide_ready=false. Final read-only inspection found no active job in the passing fixture. Passing harness time 409.27s excludes initial model preload.

Actual media runtime: Miniforge Python 3.12.9, mcp 1.29.0, yt-dlp 2026.8.19, faster-whisper 1.2.1, ctranslate2 4.8.0, av 17.1.0, huggingface-hub 0.34.3, onnxruntime 1.20.1. The model used the tool's existing tiny/CPU/int8 defaults. CORPUS_INGEST_CONFIG, CORPUS_INGEST_DATA_DIR, HF_HOME, HF_HUB_CACHE and anonymous public-model handling were scoped to test processes. The repo .venv still has transcription packages but lacks yt_dlp; PATH python belongs to another repository. No environments were installed or rewritten.

Current full gate: .\.venv\Scripts\python.exe -m pytest -q -rs --basetemp=.pytest-tmp/54v --tb=short -> 2680 passed, 55 skipped in 978.43s, exit 0. The 55 skips consist of 29 Git ownership refusals and 26 native symlink OSError cases. Supplementary Git guards -> 29 passed in 21.61s, exit 0 (.pytest-tmp/54g2), with process-local safe.directory using the repository's forward-slash absolute path. An initial backslash-form setting left those guards skipped and is not passing evidence. No global Git config changed. Combined current coverage is 2709 passing cases with 26 native-link skips; no single full-run 2709-passed claim is made. Simulated reparse/nonplain checks ran.

The earlier long .pytest-tmp/54-real-source-full basetemp caused Windows path-length failures in preverification snapshots. A focused reproduction failed, while the unchanged external verification file passed 10/10 in 1.64s with .pytest-tmp/54e. The long-path full run was stopped and preserved before the short-path full gate. compileall -q src scripts and git diff --check returned exit 0; 39 existing line-ending warnings remained.

Changed source paths for this correction: src/corpus_ingest_core/source_preparation.py, tests/test_source_preparation_worker.py; this implementation log records the evidence. All harness configuration, model/audio/transcript files and metadata-only reports remain ignored local artifacts. The readable local report is .pytest-tmp/54x3/test-report.md, with result.json, runtime.json and artifact/audio validation receipts. Actual Hermes mounting, agent approval compliance and transcript semantic accuracy remain unverified; the Windows production transport requirement remains independently managed loopback HTTP. No downstream learning documents or semantic summary were generated.
