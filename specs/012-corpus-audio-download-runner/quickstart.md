# Quickstart: Corpus Audio Download Runner

## Prerequisites

- Existing 008/009 corpus features are available.
- Local `data/**` artifacts may be empty; dry-run must still return valid metadata.
- Confirmed execution may use RSS/network through the existing downloader.

## Dry-run Preview

```powershell
python scripts/run_corpus_audio_download.py --podcast gooaye
```

Expected:
- Refreshes the 009 corpus remediation plan first.
- Prints metadata-only JSON.
- Does not download audio.
- Does not read RSS or call network.
- Does not write `corpus-audio-download-run.json` or `.md`.
- Does not print full source URLs.

## Confirm One Download

```powershell
python scripts/run_corpus_audio_download.py --podcast gooaye --episode EP672 --confirm
```

Expected:
- Rejects if `EP672` is absent or not selected by refreshed audio criteria.
- Calls existing audio downloader only for `EP672` when selected.
- Writes latest run report artifacts:
  - `data/corpus/gooaye/corpus-audio-download-run.json`
  - `data/corpus/gooaye/corpus-audio-download-run.md`
- Reports `downloaded`, `reused`, `failed`, or `rejected` outcome metadata.
- Omits full source URLs, query strings, secret-like values, traceback bodies, transcript text, prompt text, and raw LLM output.

## Validation Commands

```powershell
python -m pytest tests/test_corpus_audio_download_runner.py
python -m pytest tests/test_corpus_remediation_plan.py tests/test_corpus_index.py tests/test_corpus_local_transcription_runner.py
python -m pytest tests/test_downloader.py
python -m pytest tests/test_mcp_tool_registry_contract.py
python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py
python -m pytest
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```

## Manual Follow-up After Confirmed Download

Confirmed audio download does not automatically transcribe, run downstream remediation, or rebuild cache. The next explicit steps remain:

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm
python scripts/run_corpus_remediation.py --podcast gooaye --episode EP672 --confirm
python scripts/rebuild_cache.py --podcast gooaye --force
```
