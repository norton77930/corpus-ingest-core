# Validation and local setup

Use the repo .venv explicitly; PATH Python may belong to another repo. Runtime completion requires current evidence in implementation-log.md.

## Local source configuration

Add this optional mapping to an existing selected operator-owned source profile, not the committed registry:

```yaml
preparation_transcription:
  model: medium
  device: cuda
  compute_type: float16
```

Omission retains tiny/cpu/int8. Explicit partial/null/invalid mappings are refused. Interpreter/worker need compatible CUDA libraries and a reachable writable model cache; no installation or CPU/tiny fallback. CPU operators may explicitly select medium/cpu/int8. Do not read .env; changing policy does not regenerate existing artifacts.

## Scoped checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_preparation_transcription.py tests/test_source_preparation_transcription.py tests/test_source_preparation.py tests/test_source_preparation_jobs.py tests/test_source_preparation_worker.py tests/test_mcp_source_preparation.py tests/test_source_preparation_skill.py --basetemp=.pytest-tmp/55t
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp/55f
.\.venv\Scripts\python.exe -m compileall -q src scripts
git diff --check
```

Owned fixtures only; no production media/providers. Git ownership workaround, if needed, is process-local and exact-repository only, never global.

## Dialogue acceptance

One configured URL previews settings and model-download/local resource risks. Fresh approval permits one matching confirmation; report job_id/state and stop. A later explicit query reads status once. Ready artifacts disclose actual/unknown/different settings without a new job. Native Windows stdio new submissions remain blocked; use an already independently managed loopback HTTP host. Missing mounted tools stop the Skill.

Offline/owned SDK tests are not live Hermes compliance; capture mounted tool traces separately. Readiness is not word accuracy. Original-audio review and semantic summary/notes remain separate operations with existing approval/API-cost guards.

## Hermes host acceptance (not yet executed)

Point the mounted MCP server at the selected Python runtime and local source registry. The worker inherits that interpreter/context; CUDA libraries must be available to that runtime. Copy the updated Skill and response reference together. The agent must not install software, edit profiles or supply model overrides in tool arguments.

Natural request: 「幫我把這支影片準備成逐字稿，先讓我看執行計畫：〈影片 URL〉。」

Check the displayed preview includes the configured model/device/precision, VAD, possible public model download, source/artifact roles and job metadata. Initial request permits preview only. After reviewing that preview: 「我同意依照這份預覽提交這支影片的準備工作。」

Expected trace: one Tool33 preview, one matching Tool33 confirmation after fresh approval, then stop with job_id; no automatic Tool34 call. Later: 「查一下這份工作的進度：〈job_id〉。」 permits one offline Tool34 observation. New ready status should report approved settings equal to recorded settings. A ready existing tiny transcript under current medium settings must instead disclose the difference and stop, preserving files. Historical unknown metadata must not be reported as medium. Settings changes or runtime refusal require operator intervention/new separately requested preview; no automatic fallback or retry.

Capture actual host tool traces to evaluate these expectations. Passing developer SDK fixtures does not mark this host acceptance complete. Learning notes still require the separate learning workflow and its preview/approval/cost guards.
