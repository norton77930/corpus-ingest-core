# Data Model: Latest Episode Deterministic Workflow

## LatestEpisodeDeterministicWorkflowRequest

| Field | Meaning | Validation |
| --- | --- | --- |
| `podcast_id` | Configured profile to process | Safe configured identifier only |
| `confirm` | Dry-run or side-effect execution | Defaults to `false` |
| `transcription_model` | Optional local model override | Local-only metadata, never provider config |
| `transcription_device` | Local compute device | Existing transcription validation |
| `transcription_compute_type` | Local compute precision | Existing transcription validation |
| `transcription_vad_filter` | Local VAD switch | Boolean only |

The request has no episode selector: the workflow is explicitly for one latest
episode. It has no force, partial, semantic, provider, credential, or cache
parameters.

## LatestEpisodeSnapshot

| Field | Meaning | Rule |
| --- | --- | --- |
| `podcast_id` | Selected configured profile | Safe identifier |
| `episode_ref` | Canonical latest episode reference | Resolved once per invocation |
| `selector` | Original selector | Always `latest` |

The snapshot is established by the initial intake preview. All subsequent stage
probes and executions use only `episode_ref`, never `latest`.

**identity fields**: every post-resolution row preserves the configured
`podcast_id`, the original `selector="latest"`, and the canonical `episode_ref`.
A row may not substitute a later RSS latest value or an episode reference from
another podcast; either condition is fail-closed.

## LatestEpisodeDeterministicWorkflowRunRow

One row represents the selector resolution, one stage attempt, one deterministic
remediation action, or a terminal outcome.

| Field | Meaning |
| --- | --- |
| `episode_ref` | Safe canonical reference or `null` before resolution |
| `stage` | `intake`, `audio_download`, `local_transcription`, `deterministic_remediation`, `ready_for_semantic_summary`, or `blocked` |
| `action_id` | Safe remediation action identifier when applicable |
| `status` | `selected`, `executed`, `reused`, `ready`, `blocked`, `failed`, or `rejected` |
| `reason` | Sanitized bounded explanation |
| `planned_reads` / `planned_writes` | Safe paths or approved labels |
| `output_paths` / `source_report_paths` | Safe local paths only |
| `failure_category` | Exception type category only |
| `warnings` | Sanitized bounded warnings |

**action identity coherence**: the selector's safe remediation `action_id` and
its priority-winning target execution row belong to one canonical action. When
both action identifiers are present but differ, composition fails closed and
does not copy status metadata, paths, failure category, or warnings from the
mismatched execution row. An identifier that is present but malformed also
fails closed under the same metadata-isolation rule. Only when the source
identifier is absent or `null` may the valid selected identifier be retained
for bounded-progress detection.

**semantic row rules**: during internal handoff classification, canonical target remediation evidence is at least one well-formed target row. If present, target semantic rows may only use `blocked` or `excluded`; any other target semantic
status is invalid. A well-formed target deterministic row establishes target evidence
for every known status, including `skipped`, `reused`, and `executed`; later
selection logic still classifies `selected`, `blocked`, `failed`, or `rejected`
actions. An empty remediation result is valid only when the fresh canonical target
plan row is well formed and explicitly records `actions=[]`, proving that no
residual action was omitted. Otherwise empty rows and results containing only
non-target `skipped` rows are invalid. A non-target row may be ignored only when its status is `skipped`; missing identity or any non-target non-`skipped` row fails
closed.
The public terminal handoff row uses stage `ready_for_semantic_summary`, status
`ready`, and the canonical identity fields. It has no semantic action
identifier, executor result, raw semantic content, provider metadata, or
credential fields, and is emitted only when the selected episode has no
remaining deterministic work.

## LatestEpisodeDeterministicWorkflowRunResult

The immutable public result contains `podcast_id`, `run_mode`, `confirm`,
`selector`, `episode_ref`, `outcome`, confirmed-only report paths, normalized
filters, counts, ordered rows, warnings, and `not_investment_advice=true`.

`outcome` values are:

- `dry_run`: the pinned episode and next deterministic work were previewed.
- `ready_for_semantic_summary`: no deterministic work remains; no semantic work
  has been attempted.
- `blocked`, `failed`, or `rejected`: the run stopped without a fallback action.

`executed` and `reused` are row statuses, not top-level outcomes. After either
status, the confirmed runner continues probing the pinned episode until it
reaches `ready_for_semantic_summary` or stops on `blocked`, `failed`, or
`rejected`.

## State Transitions

```text
latest selector
  -> canonical snapshot
  -> intake (if seed missing)
  -> audio_download (if audio missing)
  -> local_transcription (if transcript missing)
  -> deterministic_remediation (one action at a time)
  -> ready_for_semantic_summary

Any selected action -> blocked | failed | rejected (terminal for the run)
```

The next invocation may resume only from valid local artifacts. An already-ready
episode performs no stage execution.
