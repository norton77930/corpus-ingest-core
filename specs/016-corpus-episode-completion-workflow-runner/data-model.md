# Data Model: Corpus Episode Completion Workflow Runner

## Design Rules

- All public additions are immutable dataclasses and additive to existing
  contracts.
- One result describes one podcast, one canonical episode, and at most one
  executor attempt.
- Dry-run report paths are null and every dry-run performs zero file changes.
- Strings in runner-owned models are bounded metadata or safe local paths.
  Feed/source URL, endpoint/base URL, query/fragment, transcript/evidence/
  semantic/prompt/provider bodies, credential values, raw exceptions, and
  tracebacks are never model fields.
- The latest 016 report payload has no `generated_at` field.

## `CorpusEpisodeCompletionWorkflowRunFilter`

Normalized non-secret request metadata retained for audit and serialization.

| Field | Type | Rules |
|---|---|---|
| `episode_ref` | `str` | Original normalized selector in dry-run; canonical explicit ref in confirmed mode |
| `action` | `str` | `next` or one executable ladder action; confirmed mode rejects `next` |
| `transcription_model` | `str \| None` | Safe local model identifier only |
| `transcription_device` | `str` | Safe local device identifier |
| `transcription_compute_type` | `str` | Safe local compute identifier |
| `transcription_vad_filter` | `bool` | Bounded local transcription option |
| `semantic_provider` | `str \| None` | Safe provider identifier only when summary metadata is relevant |
| `semantic_model` | `str \| None` | Safe model identifier; no endpoint |
| `semantic_chunk_seconds` | `int` | Positive chunk duration |
| `semantic_max_segments_per_chunk` | `int` | Positive segment cap |

The filter excludes `semantic_base_url`, credential-variable names, credential
values, environment-file paths, acknowledgement text, and callback objects.

## `CorpusEpisodeCompletionWorkflowRunCounts`

| Field | Type |
|---|---|
| `row_count` | `int` |
| `selected_count` | `int` |
| `executed_count` | `int` |
| `reused_count` | `int` |
| `completed_count` | `int` |
| `failed_count` | `int` |
| `blocked_count` | `int` |
| `rejected_count` | `int` |
| `manual_only_count` | `int` |
| `warning_count` | `int` |

All counts are non-negative. `row_count` is exactly one for every contained
selection or stage outcome. `executed_count` is at most one.

## `CorpusEpisodeCompletionWorkflowRunWarning`

| Field | Type | Rules |
|---|---|---|
| `scope` | `str` | Allowlisted scope such as `completion_workflow`, `stage`, `corpus_metadata`, or `cache` |
| `episode_ref` | `str \| None` | Canonical safe reference when available |
| `message` | `str` | Fixed allowlisted metadata-only warning |

## `CorpusEpisodeCompletionWorkflowRunRow`

One selected, terminal, rejected, or attempted outcome.

| Field | Type | Rules |
|---|---|---|
| `episode_ref` | `str \| None` | Canonical selected episode when resolution succeeded |
| `action` | `str` | Selected ladder action or terminal `completed`/`blocked` |
| `status` | `str` | `selected`, `executed`, `reused`, `completed`, `failed`, `blocked`, or `rejected` |
| `reason` | `str` | Fixed allowlisted reason only |
| `requires_confirmation` | `bool` | True only for an executable dry-run selection |
| `requires_api_cost_ack` | `bool` | True only for semantic summary |
| `network_risk` | `bool` | True for feed/intake/audio network work or semantic provider work |
| `local_compute_risk` | `bool` | True for local transcription |
| `transcript_transfer_risk` | `bool` | True only for semantic summary |
| `may_incur_api_cost` | `bool` | True only for semantic summary |
| `manual_only` | `bool` | True for fail-closed states requiring operator intervention |
| `planned_reads` | `list[str]` | Safe local paths plus exact labels such as configured feed/in-memory snapshot |
| `planned_writes` | `list[str]` | Safe local paths or an exact timestamped-review label; empty for terminal states |
| `output_paths` | `list[str]` | Safe concrete output paths from the one attempted runner |
| `source_report_paths` | `list[str]` | Safe existing report paths used as state metadata |
| `stage_counts` | `dict[str, int]` | Allowlisted non-negative count keys from the stage result |
| `provider` | `str \| None` | Safe semantic provider identifier only when relevant |
| `model` | `str \| None` | Safe local/semantic model identifier only when relevant |
| `failure_category` | `str \| None` | Exception class/category only; no message |
| `warnings` | `list[str]` | Fixed metadata-only warnings |

## `CorpusEpisodeCompletionWorkflowRunResult`

| Field | Type | Rules |
|---|---|---|
| `podcast_id` | `str` | Validated podcast identifier |
| `run_mode` | `str` | `dry_run` or `confirmed` |
| `confirm` | `bool` | Original confirmation mode |
| `selector` | `str` | Normalized requested selector |
| `episode_ref` | `str \| None` | Canonical resolved episode |
| `requested_action` | `str` | Normalized caller request |
| `selected_action` | `str` | Fresh selected action or terminal state |
| `executed_action` | `str \| None` | Non-null only after one runner call |
| `report_json_path` | `Path \| None` | Confirmed-only latest report path |
| `report_markdown_path` | `Path \| None` | Confirmed-only latest report path |
| `filters` | `CorpusEpisodeCompletionWorkflowRunFilter` | Non-secret request metadata |
| `counts` | `CorpusEpisodeCompletionWorkflowRunCounts` | One-row aggregates |
| `rows` | `list[CorpusEpisodeCompletionWorkflowRunRow]` | Exactly one bounded row |
| `warnings` | `list[CorpusEpisodeCompletionWorkflowRunWarning]` | Bounded warnings |
| `not_investment_advice` | `bool` | Always true |

## Storage and Error Additions

### `CorpusEpisodeCompletionWorkflowRunAssetPaths`

| Field | Type | Value |
|---|---|---|
| `json_path` | `Path` | `data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json` |
| `markdown_path` | `Path` | `data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.md` |

`corpus_episode_completion_workflow_run_asset_paths(podcast_id)` validates the
podcast component with the existing storage safety seam and returns paths
without creating directories.

### `CorpusEpisodeCompletionWorkflowRunnerFailedError`

Dedicated validation/system-boundary error for invalid podcast/selector/action,
unsafe identifiers, non-positive numeric options, confirmed `next`, confirmed
`latest`, and missing/incorrect semantic acknowledgement. Messages are fixed
and never interpolate dependency content, URLs, or secrets.

## State Transitions

| Fresh episode state | Selected action | Dry-run status | Manual only |
|---|---|---|---|
| Selector cannot resolve safely | `blocked` | `blocked` or contained `failed` | Yes |
| Canonical episode has no seed | `intake` | `selected` | No |
| Seed exists; audio is ready next | `audio_download` | `selected` | No |
| Local audio exists; transcript is ready next | `local_transcription` | `selected` | No |
| Valid transcript needs deterministic artifacts | `deterministic_remediation` | `selected` | No |
| Deterministic artifacts complete; semantic summary missing | `semantic_summary` | `selected` | No |
| Readable semantic summary; review missing | `semantic_review` | `selected` | No |
| Latest readable review passed | `completed` | `completed` | No |
| Invalid transcript, unavailable dependency, unreadable summary, failed/blocked/unknown review, or indeterminate state | `blocked` | `blocked` | Yes |
| Snapshot/probe exception | `blocked` | `failed` | Yes |
| Confirmed explicit action differs from fresh executable selection | Fresh selection | `rejected` | No |

Confirmed mode rejects non-canonical selection forms before state evaluation.
After one matching runner call, the row becomes `executed`, `reused`,
`completed`, `blocked`, `rejected`, or `failed` according to the existing
runner result. No second transition occurs.

## Serialization Invariants

- `result_to_dict()` flattens count fields like existing corpus runners.
- Every `Path` becomes a safe local string or null.
- Planned reads accept only safe local paths and exact labels:
  `configured podcast RSS feed` and `in-memory corpus snapshot`.
- Dry-run semantic review may use the exact non-path planned-write label
  `timestamped semantic review JSON/Markdown reports`; no future timestamped
  filename is predicted.
- Provider and model identifiers pass bounded allowlists; endpoint/base URL and
  credential-variable name are never serialized.
- JSON report, Markdown report, CLI JSON, and MCP data share the same bounded
  result payload semantics.
