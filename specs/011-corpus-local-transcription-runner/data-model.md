# Data Model: Corpus Local Transcription Runner

## CorpusLocalTranscriptionRun

One dry-run or confirmed local transcription run for one podcast.

**Fields**:

- `podcast_id`: requested podcast identifier.
- `run_mode`: `dry_run` or `confirmed`.
- `confirm`: whether execution was confirmed.
- `source_remediation_plan_json_path`: refreshed 009 remediation plan JSON path.
- `source_remediation_plan_markdown_path`: refreshed 009 remediation plan Markdown path.
- `report_json_path`: latest run report JSON path when written, otherwise null for dry-run or pre-selection rejection.
- `report_markdown_path`: latest run report Markdown path when written, otherwise null for dry-run or pre-selection rejection.
- `filters`: `LocalTranscriptionFilter`.
- `counts`: `LocalTranscriptionOutcomeCounts`.
- `rows`: ordered list of `LocalTranscriptionRow`.
- `warnings`: run-level warnings.
- `not_investment_advice`: true.

**Validation rules**:

- Dry-run rows may be returned but must not be written to report artifacts.
- Confirmed run reports must not include generation timestamps.
- Summary counts must equal row totals.
- Rows are sorted deterministically by episode reference and source action id.

## LocalTranscriptionFilter

Bounded selection criteria applied before execution.

**Fields**:

- `episode_ref`: optional episode reference filter.

**Validation rules**:

- Confirmed execution requires `episode_ref`.
- Dry-run may omit `episode_ref` to preview all eligible and skipped rows.
- Confirmed execution never accepts batch limits or action-family filters in v1.

## LocalTranscriptionRow

One derived row from a transcript remediation action and local artifact metadata.

**Fields**:

- `action_id`: source remediation action id when present.
- `podcast_id`: requested podcast identifier.
- `episode_ref`: episode reference.
- `title`: title when present in refreshed metadata.
- `transcript_status`: transcript status from refreshed corpus metadata.
- `audio_status`: audio status from refreshed corpus metadata.
- `audio_path`: selected local audio path when available.
- `outcome_status`: one of `selected`, `skipped`, `executed`, `reused`, `failed`, `rejected`.
- `reason`: concise factual reason.
- `planned_reads`: deterministic planned input paths.
- `planned_writes`: deterministic planned output paths.
- `output_paths`: concrete transcript output paths when execution produced or reused artifacts.
- `warnings`: non-fatal warning strings.

**Validation rules**:

- Rows must not include raw transcript text, prompts, raw LLM output, traceback bodies, or secret values.
- Selected rows require audio status available, existing local audio path, transcript status missing, and source action status ready.
- Unsafe transcript states become skipped or rejected rows, not overwrite candidates.

## LocalTranscriptionOutcomeCounts

Top-level count summary.

**Fields**:

- `row_count`: all returned rows.
- `selected_count`: eligible rows selected for dry-run or execution.
- `executed_count`: confirmed selected rows that generated transcript artifacts.
- `reused_count`: confirmed selected rows whose target artifacts appeared before execution completed.
- `failed_count`: confirmed selected rows that failed.
- `skipped_count`: rows skipped due missing audio, unsafe transcript state, existing transcript, unknown family, or non-ready source status.
- `rejected_count`: explicitly requested confirmed episode that does not meet local selection criteria.
- `warning_count`: total run and row warnings.

## State Transitions

- Dry-run eligible rows remain `selected`.
- Confirmed selected row becomes `executed`, `reused`, or `failed`.
- Confirmed episode that does not meet local selection criteria becomes `rejected` with no transcription call.
- Missing episode reference is a pre-selection error and does not write a run report.
