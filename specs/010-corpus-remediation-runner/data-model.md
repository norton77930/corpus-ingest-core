# Data Model: Corpus Remediation Runner

## CorpusRemediationRun

One dry-run or confirmed remediation run for one podcast.

**Fields**:

- `podcast_id`: requested podcast identifier.
- `run_mode`: `dry_run` or `confirmed`.
- `confirm`: whether execution was confirmed.
- `source_remediation_plan_json_path`: refreshed 009 remediation plan JSON path.
- `source_remediation_plan_markdown_path`: refreshed 009 remediation plan Markdown path.
- `report_json_path`: latest run report JSON path when written, otherwise null for dry-run.
- `report_markdown_path`: latest run report Markdown path when written, otherwise null for dry-run.
- `filters`: `RunSelectionFilter`.
- `counts`: `RunOutcomeCounts`.
- `rows`: ordered list of `RunActionRow`.
- `warnings`: run-level warnings.
- `not_investment_advice`: true.

**Validation rules**:

- Dry-run rows may be returned but must not be written to report artifacts.
- Confirmed run reports must not include generation timestamps.
- Summary counts must equal row totals.
- Rows are sorted deterministically by selected action order.

## RunSelectionFilter

Bounded selection criteria applied before execution.

**Fields**:

- `episode_ref`: optional episode reference filter.
- `action_family`: optional action-family filter.
- `max_actions`: optional positive maximum selected action count.

**Validation rules**:

- Confirmed execution requires at least `episode_ref` or `action_family`.
- `max_actions` must be positive when provided.
- Filters are applied before `max_actions`.

## RunActionRow

One derived action row from a 009 remediation action.

**Fields**:

- `action_id`: source remediation action id.
- `podcast_id`: requested podcast identifier.
- `episode_ref`: episode reference.
- `title`: title when present in the remediation plan.
- `artifact_family`: artifact family.
- `source_status`: status from the source remediation action.
- `outcome_status`: one of `selected`, `excluded`, `blocked`, `skipped`, `executed`, `reused`, `failed`, `rejected`.
- `reason`: concise factual reason.
- `planned_reads`: deterministic planned input paths or path patterns.
- `planned_writes`: deterministic planned output paths or path patterns.
- `output_paths`: concrete output paths when execution produced or reused artifacts.
- `warnings`: non-fatal warning strings.

**Validation rules**:

- Rows must not include raw transcript text, evidence snippets, semantic body text, prompts, raw LLM output, or secret values.
- Excluded rows must identify why the source action is outside v1 execution scope.
- Failed rows must include a failure reason without traceback or secret leakage.

## RunOutcomeCounts

Top-level count summary.

**Fields**:

- `row_count`: all returned rows.
- `selected_count`: ready deterministic rows selected for dry-run or execution.
- `executed_count`: confirmed selected rows that generated artifacts.
- `reused_count`: confirmed selected rows whose target artifacts already existed or were reused by existing generator behavior.
- `failed_count`: confirmed selected rows that failed.
- `skipped_count`: rows skipped due filters, max limit, failed dependency, or non-ready source status.
- `blocked_count`: rows blocked by source remediation status.
- `excluded_count`: rows excluded because family or behavior is outside v1 scope.
- `warning_count`: total run and row warnings.

## Deterministic Execution Scope

Allowed artifact families:

1. `extractive_summary`
2. `mentions`
3. `episode_intelligence`
4. `industry_mapping`
5. `external_boundary`

Excluded artifact families:

- `audio`
- `transcript`
- `semantic_summary`
- `semantic_review`
- stock-lens and stock-lens synthesis families
- unknown families

## Failure State Transition

- `selected` rows become `executed`, `reused`, or `failed` during confirmed execution.
- If a selected row fails, later same-run selected rows that depend on that artifact become `skipped` with a failed-dependency reason.
- Unrelated selected rows continue to receive outcomes.
