# Data Model: Corpus Fresh Episode Workflow Runner

## Corpus Episode Workflow Run

Represents one dry-run or confirmed next-stage workflow evaluation for one podcast and selector.

Fields:
- `podcast_id`: requested podcast identifier.
- `run_mode`: `dry_run` or `confirmed`.
- `confirm`: whether a confirmed stage attempt was requested.
- `selector`: requested selector, normalized to `latest` when missing or blank.
- `episode_ref`: canonical episode reference when resolved.
- `stage`: requested stage value; v1 supports `next` only.
- `selected_stage`: one of `intake`, `audio_download`, `local_transcription`, `deterministic_remediation`, `completed`, or `blocked`.
- `report_json_path`: latest workflow JSON report path for confirmed attempts only.
- `report_markdown_path`: latest workflow Markdown report path for confirmed attempts only.
- `counts`: workflow stage count summary.
- `rows`: ordered workflow stage rows.
- `warnings`: non-fatal workflow warnings.
- `not_investment_advice`: always true.

Validation rules:
- `podcast_id` must be non-empty.
- missing or blank selector becomes `latest`.
- v1 rejects any stage other than `next`.
- dry-run report paths are null and no workflow report is written.
- confirmed attempts write latest deterministic workflow reports.

## Workflow Stage Row

Represents one stage candidate, selected stage, skipped/manual-only stage, or executed stage outcome.

Fields:
- `stage`: stage family name.
- `status`: `selected`, `executed`, `reused`, `failed`, `skipped`, `blocked`, `rejected`, `manual_only`, or `completed`.
- `reason`: bounded reason text.
- `planned_reads`: metadata-only planned read paths or source labels.
- `planned_writes`: metadata-only planned write paths.
- `output_paths`: paths written or reused by the selected stage when known.
- `source_report_paths`: report paths from the selected existing runner when known.
- `stage_counts`: selected existing runner count metadata when available.
- `warnings`: row-level warning strings.

Validation rules:
- A confirmed run may have at most one row with an executed/reused/failed selected-stage outcome.
- Manual-only rows must never trigger execution.
- Reasons and warnings must be sanitized before serialization.

## Workflow Stage Counts

Summary of workflow rows and selected stage outcomes.

Fields:
- `row_count`
- `selected_count`
- `executed_count`
- `reused_count`
- `failed_count`
- `skipped_count`
- `blocked_count`
- `rejected_count`
- `manual_only_count`
- `warning_count`

Validation rules:
- Counts must be derived from rows and warnings.
- Confirmed execution attempts exactly one selected stage or one rejected/blocked report outcome.

## Workflow Warning

Represents a non-fatal warning for manual follow-up, skipped unsafe work, cache staleness, or bounded failure metadata.

Fields:
- `scope`: `run` or stage name.
- `episode_ref`: canonical episode reference when known.
- `message`: sanitized warning text.

Validation rules:
- Warnings must not contain full URLs, query strings, raw transcript text, prompt text, raw LLM output, secrets, or traceback bodies.