# Data Model: Corpus Audio Download Runner

## CorpusAudioDownloadRunResult

Represents one dry-run or confirmed audio download run for a single podcast.

Fields:
- `podcast_id`: requested podcast identifier.
- `run_mode`: `dry_run` or `confirmed`.
- `confirm`: whether side-effect execution was requested.
- `source_remediation_plan_json_path`: refreshed 009 plan JSON path.
- `source_remediation_plan_markdown_path`: refreshed 009 plan Markdown path.
- `report_json_path`: latest confirmed run JSON path, or null for dry-run.
- `report_markdown_path`: latest confirmed run Markdown path, or null for dry-run.
- `filters`: `CorpusAudioDownloadRunFilter`.
- `counts`: `CorpusAudioDownloadOutcomeCounts`.
- `rows`: ordered list of `CorpusAudioDownloadRunRow`.
- `warnings`: run-level warnings.
- `not_investment_advice`: always true.

Validation:
- Dry-run results must have null report paths.
- Confirmed results must have report paths when a confirmed attempt or rejection is recorded.
- Result content must not include `generated_at` or equivalent generation timestamps.

## CorpusAudioDownloadRunFilter

Fields:
- `episode_ref`: optional episode reference.

Validation:
- Confirmed execution requires exactly one non-empty, trimmed episode reference.
- Dry-run may omit episode reference and preview all eligible rows.

## CorpusAudioDownloadOutcomeCounts

Fields:
- `row_count`
- `selected_count`
- `downloaded_count`
- `reused_count`
- `failed_count`
- `skipped_count`
- `rejected_count`
- `warning_count`

Validation:
- Counts must equal the number of rows and warnings serialized in the result.
- `downloaded_count`, `reused_count`, and `failed_count` are zero for dry-run.

## CorpusAudioDownloadRunRow

Represents one audio action derived from refreshed remediation metadata.

Fields:
- `action_id`: source remediation action id or deterministic fallback.
- `podcast_id`
- `episode_ref`
- `audio_status`
- `outcome_status`: `selected`, `downloaded`, `reused`, `failed`, `skipped`, or `rejected`.
- `reason`: bounded factual reason.
- `planned_reads`: metadata-only source plan paths or empty list.
- `planned_writes`: expected local audio/report paths when known, never source URLs.
- `local_audio_path`: local output path when known.
- `content_type`: downloader-reported content type when available.
- `size_bytes`: downloader-reported local size when available.
- `warnings`: row-level bounded warning messages.

Validation:
- Rows must never contain full source URLs, URL query strings, API keys, tokens, `.env` values, provider secret values, prompt text, raw LLM output, or traceback bodies.
- Confirmed execution can only attempt rows with `outcome_status=selected`.
- Non-target rows remain skipped in confirmed runs; requested non-selected rows become rejected.

## CorpusAudioDownloadRunWarning

Fields:
- `scope`: `run` or `episode`.
- `episode_ref`: episode reference for episode warnings, otherwise null.
- `message`: bounded warning message.

Validation:
- Warning text is controlled by the runner and must not copy arbitrary source URL or exception text.

## Storage Helper

`corpus_audio_download_run_asset_paths(podcast_id)` returns:
- `data/corpus/{podcast_id}/corpus-audio-download-run.json`
- `data/corpus/{podcast_id}/corpus-audio-download-run.md`

Validation:
- The helper only returns paths and does not create files.
