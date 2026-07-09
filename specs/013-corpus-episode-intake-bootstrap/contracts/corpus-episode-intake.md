# Contract: Corpus Episode Intake Bootstrap

## Core Function

```python
run_corpus_episode_intake(
    podcast_id: str,
    *,
    episode_ref: str = "latest",
    confirm: bool = False,
) -> CorpusEpisodeIntakeRunResult
```

Behavior:
- Defaults to dry-run.
- Missing, empty, or whitespace-only `episode_ref` normalizes to `latest`.
- Resolves `latest` or one explicit episode reference through the configured feed reader.
- Dry-run does not write seed metadata, run reports, audio files, transcripts, downstream artifacts, cache files, or provider artifacts.
- Confirmed execution writes one seed metadata artifact only when one episode is resolved.
- Confirmed execution writes latest JSON/Markdown intake run reports for seeded, reused, failed, or rejected outcomes.
- Confirmed execution does not call `download_audio()`, `transcribe_episode()`, `run_corpus_remediation()`, `rebuild_cache()`, LLM providers, or MCP surfaces.
- All outputs omit full source URLs, audio URLs, URL query strings, raw descriptions, secret-like values, prompt text, raw LLM output, and traceback bodies.

## Storage Helpers

```python
corpus_episode_seed_asset_path(podcast_id: str, episode_ref: str) -> Path
```

Returns deterministic seed path:
- `data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json`

```python
corpus_episode_intake_run_asset_paths(podcast_id: str) -> CorpusEpisodeIntakeRunAssetPaths
```

Returns deterministic latest report paths:
- `data/corpus/{podcast_id}/corpus-episode-intake-run.json`
- `data/corpus/{podcast_id}/corpus-episode-intake-run.md`

## CLI

```powershell
python scripts/run_corpus_episode_intake.py --podcast gooaye
python scripts/run_corpus_episode_intake.py --podcast gooaye --episode latest
python scripts/run_corpus_episode_intake.py --podcast gooaye --episode EP677 --confirm
```

CLI behavior:
- Parses arguments only.
- Calls `run_corpus_episode_intake(...)`.
- Prints metadata-only JSON to stdout on success.
- Prints bounded error messages to stderr on expected core errors.
- Does not print source URLs, audio URLs, query strings, raw descriptions, secret values, tracebacks, transcript text, prompt text, or raw LLM output.

## JSON Result and Report Shape

Top-level fields:
- `podcast_id`
- `run_mode`
- `confirm`
- `selector`
- `resolved_episode_ref`
- `report_json_path`
- `report_markdown_path`
- `filters`
- `row_count`
- `selected_count`
- `seeded_count`
- `reused_count`
- `failed_count`
- `skipped_count`
- `rejected_count`
- `warning_count`
- `rows`
- `warnings`
- `not_investment_advice`

Rules:
- No `generated_at` or equivalent timestamp field.
- No full source URL or audio URL field.
- Paths are local paths only.
- Failure rows record bounded error category, not raw exception text or traceback body.

## Seed JSON Shape

Top-level fields:
- `podcast_id`
- `episode_ref`
- `title`
- `published_at`
- `duration`
- `guid_status`
- `has_audio_url`
- `seed_source`
- `selector`
- `warning_count`
- `warnings`
- `not_investment_advice`

Rules:
- No full source URL, audio URL, URL query string, raw description, prompt text, raw LLM output, secret-like value, or generation timestamp.

## Markdown Report

Content:
- Summary metadata and counts.
- Per-row outcome with selector, episode, title, published time, has-audio flag, outcome, reason, seed path, and warning count.
- Boundary notice stating no download, no transcription, no downstream remediation, no LLM, no MCP, no cache rebuild, no source URL output, and no investment advice.

Rules:
- Same no-leak and no-timestamp boundaries as JSON.
