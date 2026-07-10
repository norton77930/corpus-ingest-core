# Quickstart: Corpus Fresh Episode Workflow Runner

## Prerequisites

- Existing 013, 012, 011, and 010 corpus runners are available.
- Configured podcast profile exists in `config/podcasts.yaml` when `latest` must be resolved.
- Dry-run should be used first before every confirmed stage attempt.

## Dry-run Latest Episode

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest
```

Expected:
- Resolves or evaluates one episode selector.
- Prints metadata-only JSON with the selected next stage.
- Does not execute intake, download, transcription, or deterministic remediation.
- Does not write `corpus-episode-workflow-run.json` or `.md`.
- Does not print full URLs, raw transcript/evidence text, prompt text, raw LLM output, secrets, or traceback bodies.

## Confirm One Next Stage

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest --stage next --confirm
```

Expected:
- Attempts exactly one selected next stage.
- Requires both `--stage next` and `--confirm`; omit `--stage next` only for dry-run preview.
- Writes latest workflow reports:
  - `data/corpus/gooaye/corpus-episode-workflow-run.json`
  - `data/corpus/gooaye/corpus-episode-workflow-run.md`
- Stops after that stage even if the stage succeeds.
- Reports whether the stage was executed, reused, failed, rejected, blocked, skipped, or completed.

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
