# Data Model: Corpus Artifact Index

## Corpus Index

Podcast-level derived status artifact.

Fields:

- `podcast_id`: requested podcast identifier.
- `index_mode`: fixed mode string, `deterministic-corpus-artifact-index-v1`.
- `source_scope`: fixed value, `local-per-episode-artifacts-only`.
- `episode_count`: number of episode rows.
- `artifact_family_counts`: object keyed by supported artifact family name, each with available/missing/unreadable counts.
- `warning_count`: total warning count across corpus and episode rows.
- `episodes`: ordered list of Episode Corpus Row values.
- `not_investment_advice`: boolean, always true.

Validation rules:

- Must not contain generation timestamp fields.
- Must not contain raw transcript text, evidence snippets, semantic summary body text, LLM prompt text, or raw LLM output.
- Must be deterministic for unchanged local artifacts.

## Episode Corpus Row

Status record for one discovered episode.

Fields:

- `podcast_id`: podcast identifier.
- `episode_ref`: episode identifier parsed from supported artifact file names.
- `title`: title read from readable metadata when available; otherwise episode reference.
- `artifact_status`: object keyed by supported artifact family.
- `missing_artifacts`: ordered list of supported artifact families with missing status.
- `warnings`: ordered list of metadata warnings for this episode.

Identity:

- Unique by `(podcast_id, episode_ref)`.
- Episodes are discovered only from supported local per-episode artifact families.

Ordering:

- Rows sort by `episode_ref` using the existing deterministic path/discovery conventions.

## Artifact Family Status

Status for one supported per-episode artifact family.

Common fields:

- `status`: one of `available`, `missing`, `unreadable`, or a domain status when the family has an existing validated status.
- `paths`: object of relevant JSON, Markdown, text, SRT, or audio paths.
- `candidate_count`: number of matching local candidate artifacts when duplicate candidates exist.
- `warnings`: metadata warnings for the artifact family.

Family-specific fields:

- transcript: `validation_status`, `segment_count`, `last_segment_end_seconds`, `problem_count`, `warning_count`.
- extractive summary: `exists`, `path`.
- semantic summary: `exists`, `path`.
- semantic review: `review_status`, `review_json_path`, `review_markdown_path`, `check_count`, `failed_check_count`, `warning_count`, `blocked_check_count`.
- mentions: `mention_count`.
- episode intelligence report: `report_status`, `transcript_status`, `segment_count`.
- industry mapping: `mapping_status`, `node_count`, `candidate_count`, `warning_count`.
- external boundary: `boundary_status`, `candidate_count`, `warning_count`.
- audio: `exists`, `path`, `candidate_count`.

Unreadable handling:

- A malformed readable-metadata artifact marks that family `unreadable`.
- The episode row remains in the index.
- Other artifact families for the same episode remain independently reportable.

## Semantic Review Status

Latest semantic summary review metadata for one episode.

Fields:

- `status`: `passed`, `failed`, `blocked`, `missing`, or `unreadable`.
- `review_json_path`: selected review JSON path when present.
- `review_markdown_path`: selected review Markdown path when present.
- `check_count`: number of checks in the review report.
- `failed_check_count`: failed check count.
- `warning_count`: warning check count.
- `blocked_check_count`: blocked check count.

Selection rule:

- Use only semantic review reports matching the requested `podcast_id` and `episode_ref`.
- Select the latest timestamped review report deterministically from file names.
- Do not read semantic summary Markdown body text to determine review status.
