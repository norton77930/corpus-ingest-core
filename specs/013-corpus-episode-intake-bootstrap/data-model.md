# Data Model: Corpus Episode Intake Bootstrap

## CorpusEpisodeIntakeRunResult

Represents one dry-run or confirmed intake run for a single podcast and selector.

Fields:
- `podcast_id`: requested podcast identifier.
- `run_mode`: `dry_run` or `confirmed`.
- `confirm`: whether seed write was requested.
- `selector`: normalized selector, either `latest` or an explicit episode reference.
- `resolved_episode_ref`: canonical episode reference when resolved.
- `report_json_path`: latest confirmed run JSON path, or null for dry-run.
- `report_markdown_path`: latest confirmed run Markdown path, or null for dry-run.
- `filters`: `CorpusEpisodeIntakeFilter`.
- `counts`: `CorpusEpisodeIntakeOutcomeCounts`.
- `rows`: ordered list of `CorpusEpisodeIntakeRunRow`.
- `warnings`: run-level warnings.
- `not_investment_advice`: always true.

Validation:
- Dry-run results must have null report paths and must not write seed metadata.
- Confirmed results must have report paths when a confirmed attempt is recorded.
- Result content must not include `generated_at` or equivalent generation timestamps.

## CorpusEpisodeIntakeFilter

Fields:
- `episode_ref`: normalized selector; defaults to `latest`.

Validation:
- Missing, empty, or whitespace-only selector normalizes to `latest`.
- v1 allows `latest` or one explicit episode reference only.
- Batch selectors and latest-N are invalid in v1.

## CorpusEpisodeIntakeOutcomeCounts

Fields:
- `row_count`
- `selected_count`
- `seeded_count`
- `reused_count`
- `failed_count`
- `skipped_count`
- `rejected_count`
- `warning_count`

Validation:
- Counts must equal the rows and warnings serialized in the result.
- `seeded_count` and `reused_count` are zero for dry-run.

## CorpusEpisodeIntakeRunRow

Represents one selector resolution and optional confirmed seed outcome.

Fields:
- `podcast_id`
- `selector`
- `episode_ref`: canonical episode reference when resolved.
- `title`
- `published_at`
- `duration`
- `guid_status`: bounded status such as `present`, `missing`, or `redacted`.
- `has_audio_url`: whether feed metadata indicates an audio enclosure is available.
- `outcome_status`: `selected`, `seeded`, `reused`, `failed`, `skipped`, or `rejected`.
- `reason`: bounded factual reason.
- `planned_reads`: configured feed metadata source label, not full URLs.
- `planned_writes`: local seed/report paths, never source URLs.
- `seed_json_path`: local seed metadata path when known.
- `warnings`: row-level bounded warning messages.

Validation:
- Rows must never contain full source URLs, URL query strings, API keys, tokens, `.env` values, provider secret values, raw descriptions, prompt text, raw LLM output, or traceback bodies.
- Confirmed execution can only write seed metadata for a resolved row.

## CorpusEpisodeSeed

Represents local metadata that makes a feed-resolved episode visible to the offline corpus index.

Fields:
- `podcast_id`
- `episode_ref`
- `title`
- `published_at`
- `duration`
- `guid_status`
- `has_audio_url`
- `seed_source`: `rss`
- `selector`
- `warning_count`
- `warnings`
- `not_investment_advice`

Validation:
- Seed metadata must not contain full source URL, audio URL, URL query string, raw description, prompt text, raw LLM output, secret-like values, or traceback body.
- Seed metadata must not include a generation timestamp.
- One canonical seed file exists per podcast and episode reference.

## CorpusEpisodeIntakeRunWarning

Fields:
- `scope`: `run` or `episode`.
- `episode_ref`: episode reference for episode warnings, otherwise null.
- `message`: bounded warning message.

Validation:
- Warning text is controlled by the runner and must not copy arbitrary feed body, URL, exception, or traceback text.

## Storage Helpers

`corpus_episode_seed_asset_path(podcast_id, episode_ref)` returns:
- `data/corpus/{podcast_id}/episode-seeds/{episode_ref}.episode-seed.json`

`corpus_episode_intake_run_asset_paths(podcast_id)` returns:
- `data/corpus/{podcast_id}/corpus-episode-intake-run.json`
- `data/corpus/{podcast_id}/corpus-episode-intake-run.md`

Validation:
- Helpers only return paths and do not create files.
