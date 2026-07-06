# Ingestion Transcript Core Quickstart

**Status: Backfilled / As-built**

## Manual Validation

```powershell
python scripts/list_episodes.py --podcast gooaye
python scripts/download_episode.py --podcast gooaye --episode EP672
python scripts/transcribe_episode.py --podcast gooaye --episode EP672
python scripts/validate_transcript.py --podcast gooaye --episode EP672
python scripts/summarize_episode.py --podcast gooaye --episode EP672
```

## Expected Boundaries

- Deterministic summary does not call LLM providers.
- `.env` is not required for deterministic transcript validation.
- Missing or invalid transcripts are reported before research steps.
- no investment advice appears in ingestion or transcript outputs.
