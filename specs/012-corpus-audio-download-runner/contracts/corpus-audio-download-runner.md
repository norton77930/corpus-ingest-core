# Contract: Corpus Audio Download Runner

## Core Function

```python
run_corpus_audio_download(
    podcast_id: str,
    *,
    episode_ref: str | None = None,
    confirm: bool = False,
) -> CorpusAudioDownloadRunResult
```

Behavior:
- Always refreshes 009 remediation plan before selection.
- Defaults to dry-run.
- Dry-run does not call `download_audio()`, read RSS, call network, write audio files, or write run report artifacts.
- Confirmed execution rejects missing, empty, or whitespace-only `episode_ref` before downloader dispatch.
- Confirmed execution rejects requested episodes that are absent or not selected by refreshed criteria.
- Confirmed eligible execution calls `download_audio(podcast_id, episode_ref)` exactly through core code, without shelling out to scripts.
- Confirmed execution maps downloader result to `downloaded` when `downloaded=True` and `reused` when `already_exists=True`.
- Confirmed execution writes latest JSON/Markdown reports and returns their paths.
- All outputs omit full source URLs and URL query strings.

## Storage Helper

```python
corpus_audio_download_run_asset_paths(podcast_id: str) -> CorpusAudioDownloadRunAssetPaths
```

Returns deterministic latest report paths:
- `data/corpus/{podcast_id}/corpus-audio-download-run.json`
- `data/corpus/{podcast_id}/corpus-audio-download-run.md`

## CLI

```powershell
python scripts/run_corpus_audio_download.py --podcast gooaye
python scripts/run_corpus_audio_download.py --podcast gooaye --episode EP672 --confirm
```

CLI behavior:
- Parses arguments only.
- Calls `run_corpus_audio_download(...)`.
- Prints metadata-only JSON to stdout on success.
- Prints bounded error messages to stderr on expected core errors.
- Does not print source URLs, query strings, secret values, tracebacks, transcript text, prompt text, or raw LLM output.

## JSON Report Shape

Top-level fields:
- `podcast_id`
- `run_mode`
- `confirm`
- `source_remediation_plan_json_path`
- `source_remediation_plan_markdown_path`
- `report_json_path`
- `report_markdown_path`
- `filters`
- `row_count`
- `selected_count`
- `downloaded_count`
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
- No full source URL field.
- Paths are local paths only.
- Failure rows record bounded error category, not raw exception text or traceback body.

## Markdown Report

Content:
- Summary metadata and counts.
- Per-row outcomes with episode, audio status, outcome, reason, local output path, and warning count.
- Boundary notice stating no transcription, no LLM, no MCP, no cache rebuild, no source URL output, and no investment advice.

Rules:
- Same no-leak and no-timestamp boundaries as JSON.
