# Quickstart: Corpus Local Transcription Runner

## Prerequisites

- Local corpus artifacts are available under `data/`.
- At least one episode has a local audio artifact and no transcript outputs.
- The local transcription dependency is installed for confirmed runs.
- No `.env`, LLM provider, RSS, network, or MCP setup is required for this feature.

## Preview Eligible Local Transcription Work

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye
```

Expected outcome:

- The command refreshes the corpus remediation plan.
- Stdout is metadata-only JSON.
- Eligible rows have `outcome_status` set to `selected`.
- Missing-audio, existing-transcript, corrupt, unreadable, partial, semantic, downstream, stock-lens, and unknown rows are skipped or absent with factual reasons.
- No `data/corpus/gooaye/corpus-local-transcription-run.json` or `.md` artifact is written.
- No transcript output is written.

## Confirm One Local Transcription

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm
```

Expected outcome:

- The command refreshes the corpus remediation plan before selection.
- Exactly one episode is eligible for execution.
- Confirmed execution uses the selected local audio path.
- No audio download occurs.
- Transcript `.json`, `.txt`, and `.srt` outputs may be written by the existing transcription capability.
- `data/corpus/gooaye/corpus-local-transcription-run.json` and `.md` are written after confirmed execution is attempted.
- Stdout includes report paths and selected/executed/reused/failed/skipped/rejected counts.

## Confirm With Runtime Options

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm --model small --device cuda --compute-type float16
```

Expected outcome:

- Runtime options are passed to the transcription capability.
- The no-download, no-LLM, no-MCP, no-cache-rebuild, and no-secret-output boundaries remain unchanged.

## Rejection Scenarios

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye --confirm
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP999 --confirm
```

Expected outcome:

- Missing episode reference is rejected before transcription work starts and does not write a run report.
- A specified episode that is not eligible produces no transcription call; when a result is produced, it records a rejected or skipped reason.

## Verification Commands

```powershell
python -m pytest tests/test_corpus_local_transcription_runner.py
python -m pytest tests/test_corpus_remediation_plan.py tests/test_corpus_index.py
python -m pytest tests/test_mcp_tool_registry_contract.py
python -m pytest
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```
