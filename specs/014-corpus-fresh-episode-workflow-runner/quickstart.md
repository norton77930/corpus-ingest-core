# Quickstart: Corpus Fresh Episode Workflow Runner

## Prerequisites

- Existing 013, 012, 011, and 010 corpus runners are available.
- Configured podcast profile exists in `config/podcasts.yaml` when `latest` must be resolved.
- 014 dry-run should be used first before every confirmed stage attempt; it differs from standalone 010-012 dry-runs, which still refresh and persist 008/009.

## Dry-run Latest Episode

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest
```

Expected:
- Resolves or evaluates one episode selector.
- Prints metadata-only JSON with the selected next stage.
- Does not execute intake, download, transcription, or deterministic remediation.
- Is strict zero-file: the before/after tree manifest is identical, including seed, audio, transcript, index, plan, 010-014 reports, downstream artifacts, and stale sentinels.
- Creates no `.part` file and neither overwrites nor trusts stale index/plan/report files as stage truth.
- May include safe local dependency paths; the only non-path labels are exactly `configured podcast RSS feed` for intake and `in-memory corpus snapshot` for seeded state.
- Builds one seeded in-memory index/plan snapshot and reuses that same result/payload across audio, transcription, and remediation previews with `source_persisted=False`.
- Does not print full URLs, raw transcript/evidence text, prompt text, raw LLM output, secrets, or traceback bodies.

## Confirm One Next Stage

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest --stage next --confirm
```

Expected:
- Dispatches exactly one selected existing public runner and never falls through to another stage.
- Requires both `--stage next` and `--confirm`; omit `--stage next` only for dry-run preview.
- The selected runner may refresh/persist its existing index, plan, stage outputs, and stage report before 014 writes its own workflow report.
- Writes latest workflow reports:
  - `data/corpus/gooaye/corpus-episode-workflow-run.json`
  - `data/corpus/gooaye/corpus-episode-workflow-run.md`
- Stops after that stage even if the stage succeeds.
- Reports whether the stage was executed, reused, failed, rejected, blocked, skipped, or completed.
- If refreshed confirmed state returns rejected, blocked, or failed, records that outcome and stops.

## Confirm Transcription Stage With Options

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode EP677 --stage next --confirm --model small --device cuda --compute-type float16
```

Expected:
- Uses these transcription options only if local transcription is the selected next stage.
- Does not use transcription options for intake, audio download, deterministic remediation, completed, blocked, or rejected stages.

## Manual Follow-up

This runner does not automatically continue after a confirmed stage. Re-run dry-run to inspect the next stage, then confirm again when appropriate.

The runner also does not execute semantic summary/review, LLM synthesis, stock-lens, MCP tools, or SQLite cache rebuild. Those remain separate manual workflows.

## Validation Commands

```powershell
python -m pytest tests/test_corpus_episode_workflow_runner.py
python -m pytest tests/test_corpus_episode_intake.py tests/test_corpus_audio_download_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_remediation_runner.py
python -m pytest tests/test_corpus_index.py tests/test_corpus_remediation_plan.py
python -m pytest tests/test_mcp_tool_registry_contract.py
python -m pytest
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```
