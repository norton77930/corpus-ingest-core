# Data Model: Workflow Derivation Bundle

## OperatorWorkflowContext

- `path`: local file used for this run
- `allowed_tools`: non-empty list of tool/surface names
- `notes`: optional free text the model may use as operator description, not as speaker quotes

Validation: missing file, unreadable UTF-8, missing/empty `allowed_tools` → named error.

## WorkflowDerivationResult

- `podcast_id`, `episode_ref`
- `confirmed`: bool
- `run_mode`: `preview` | `confirmed`
- `planned_writes`: list of paths
- `prompt_examples_path`, `apply_path`: null on preview
- `report_json_path`, `report_markdown_path`: null on preview
- `warnings`
- `not_investment_advice`: true

## Family status (`workflow_derivation`)

- `missing`: neither file exists
- `partial`: exactly one readable, or any unreadable
- `available`: both `05` and `06` exist and are readable UTF-8

`study_guide` status ignores these two files.

## On-disk files

Beside the lecture:

- `05_prompt_examples.md`
- `06_apply_to_my_workflow.md`

Run report:

- `data/corpus/{podcast_id}/workflow-derivation-runs/{episode_ref}.workflow-derivation.json`
- matching `.md`
