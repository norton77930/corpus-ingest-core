# Quickstart: Corpus Episode Intake Bootstrap

## Prerequisites

- Existing 008/009/012/011/010 corpus features are available.
- Configured podcast profile exists in `config/podcasts.yaml`.
- Dry-run and confirmed intake may read the configured podcast RSS feed.

## Dry-run Latest Episode

```powershell
python scripts/run_corpus_episode_intake.py --podcast gooaye --episode latest
```

Expected:
- Resolves one latest episode from the configured feed.
- Prints metadata-only JSON.
- Does not write seed metadata.
- Does not write `corpus-episode-intake-run.json` or `.md`.
- Does not download audio.
- Does not print full source URLs, audio URLs, query strings, raw descriptions, or secret-like values.

## Confirm One Episode Seed

```powershell
python scripts/run_corpus_episode_intake.py --podcast gooaye --episode EP677 --confirm
```

Expected:
- Resolves the explicit episode from the configured feed.
- Writes one local seed metadata artifact under `data/corpus/gooaye/episode-seeds/`.
- Writes latest run report artifacts:
  - `data/corpus/gooaye/corpus-episode-intake-run.json`
  - `data/corpus/gooaye/corpus-episode-intake-run.md`
- Reports `seeded`, `reused`, `failed`, or `rejected` outcome metadata.
- Omits full source URLs, audio URLs, query strings, raw descriptions, secret-like values, traceback bodies, transcript text, prompt text, and raw LLM output.

## Manual Follow-up After Confirmed Intake

Confirmed episode intake does not automatically download, transcribe, run downstream remediation, or rebuild cache. The next explicit steps remain:

```powershell
python scripts/generate_corpus_index.py --podcast gooaye
python scripts/generate_corpus_remediation_plan.py --podcast gooaye
python scripts/run_corpus_audio_download.py --podcast gooaye --episode EP677 --confirm
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP677 --confirm
python scripts/run_corpus_remediation.py --podcast gooaye --episode EP677 --confirm
python scripts/rebuild_cache.py --podcast gooaye --force
```

## Validation Commands

```powershell
python -m pytest tests/test_corpus_episode_intake.py
python -m pytest tests/test_corpus_index.py tests/test_corpus_remediation_plan.py tests/test_corpus_audio_download_runner.py
python -m pytest tests/test_feed_reader.py
python -m pytest tests/test_mcp_tool_registry_contract.py
python -m pytest tests/test_ai_governance_docs.py tests/test_architecture_spec_docs.py tests/test_spec_kit_backfill_docs.py tests/test_spec_kit_constitution.py tests/test_spec_kit_bootstrap.py
python -m pytest
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```
