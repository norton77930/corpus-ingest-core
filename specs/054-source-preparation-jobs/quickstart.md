# Source preparation validation and operator walkthrough

Status:Implemented; offline-verified. The registry appends Tool33 prepare_learning_source and Tool34 inspect_source_preparation_job. Use the portable source-preparation Skill with those mounted tools. Source profiles must already be configured, and Windows background submissions require already independently managed loopback HTTP. No service installation or live source/provider execution occurred during implementation.

## Package and runtime verification
From repo root with the repo .venv:

    $env:SPECIFY_FEATURE_DIRECTORY='specs/054-source-preparation-jobs'
    .\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
    .\.venv\Scripts\python.exe -m pytest tests/test_spec_054_source_preparation_docs.py -q
    .\.venv\Scripts\python.exe -m compileall -q src scripts
    git diff --check

## Preparation conversation
Operator supplies one supported video URL and asks to prepare it for questions.
Hermes previews; explains the resolved source,which media/transcript files will be reused or written,local computation and public metadata network access.
Missing configuration:explain profile_missing or source_type_mismatch and stop; do not edit the source registry.
Operator approves the displayed source/plan. Submit once; return job_id and current stage without waiting for full transcription.
A later explicit progress question triggers one read-only status call. On success,say transcript_ready. No answer to the original content question or learning-note generation is automatic.

### 中文對話示例 (operator example; actual Hermes conversation unverified)

使用者：「幫我準備這支影片：[影片網址]。」

Hermes 在預覽確認來源已設定、尚無逐字稿後：「需要下載音訊並在本機轉錄，再檢查逐字稿檔案。開始後會寫入預覽列出的檔案與工作紀錄。要開始嗎？」

使用者：「好，開始。」

Hermes 提交一次後：「已建立工作 [工作編號]，目前的狀態是 [工具回報的階段]。之後可以用這個編號查進度。」

使用者稍後：「剛剛的工作處理好了嗎？」

Hermes 查詢一次，若回報驗證完成：「逐字稿已驗證完成，可以進入下一步內容處理。這次流程沒有生成學習筆記或講義。」

若預覽回報來源未註冊，Hermes 說明需要先完成來源設定並停止，不提交工作。若查詢回報結果不明，Hermes 說明需要確認目前狀態，不自動重跑。

## Runtime offline acceptance
Use only owned temporary registry/data/job store and fake media executors. Cover complete/partial/missing/configured/incompatible sources; unsafe paths; matching/changed approvals; duplicate and different-source concurrency; spawn/store/publication failures; client disconnect and independent worker completion. No fixture-specific fake mode or arbitrary executable exposed by production MCP.
Full checks and unchanged existing ingestion/Core/MCP/Skill/privacy/cache regressions are required before runtime completion.

## Operator-host acceptance
Record actual Hermes version,selected server transport,current tool discovery,shared data/registry context and one selected source plan. Do not read or print full settings or .env.
The same-host topology is the default; actual Hermes mounting is unverified. Windows stdio can inspect readiness/status and reuse an already admitted matching job, but cannot admit a new background job. Check the existing independent loopback HTTP host before a real submission. An existing secure remote MCP connection can be used without adding a remote listener.
A real source download/transcription needs episode-scoped approval after preview. This phase calls no LLM; future summary/lecture stages retain fresh cost confirmation. Missing tools stop rather than falling back to terminal. Offline/local SDK evidence is not Hermes-host compliance.


Implementation host clarification (2026-10-06): Windows stdio new submissions report worker_host_incompatible before admission. Python venv launchers can add nested Jobs, so querying only the immediate Job cannot prove independence from the client tree. Use already independently managed loopback HTTP hosting; no new listener deployment or host-policy change is part of this phase. Matching already-admitted jobs can coalesce through stdio without another worker, and ready/status reads remain available. Owned local SDK HTTP disconnect/reconnect evidence is separate from unverified Hermes-host acceptance.

Managed audio/seed/transcript/report staging survives preparation failure via a scoped ContextVar; other callers retain historical cleanup. The worker still cleans its own external temporary acquisition directory. Operational SQLite transaction journals follow SQLite rules; history is never purged. Safe zero-byte first-creation reservations are observationally empty and can be initialized only by approved transactional admission; unknown nonempty stores remain blocked. warnings includes learning_profile_incompatible for non-learning profiles.
