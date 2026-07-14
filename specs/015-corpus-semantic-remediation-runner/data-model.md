# Data Model: Corpus Semantic Remediation Runner

## Design Rules

- All additions are immutable dataclasses and are additive to existing public contracts.
- One result describes one podcast, one explicit canonical episode, and at most one semantic executor attempt.
- Dry-run report paths are `None`; a validated confirmed attempt receives deterministic latest report paths.
- Strings stored in runner-owned models are bounded metadata. Transcript, semantic body, prompt, raw provider response, base URL, secret value, traceback body, and raw exception text are never model fields.
- The latest runner payload has no `generated_at` field.

## `CorpusSemanticRemediationRunFilter`

Normalized non-secret request metadata retained for audit and serialization.

| Field | Type | Rules |
|---|---|---|
| `episode_ref` | `str` | Explicit canonical reference; never blank or `latest` |
| `action` | `str` | `next`, `semantic_summary`, or `semantic_review`; confirmed mode rejects `next` |
| `provider` | `str \| None` | Safe provider identifier only when semantic summary metadata is relevant; otherwise null |
| `model` | `str \| None` | Safe model identifier; no endpoint value |
| `chunk_seconds` | `int` | Positive summary chunk size |
| `max_segments_per_chunk` | `int` | Positive summary chunk segment cap |

The filter intentionally excludes `base_url`, credential values, and local environment paths.

## `CorpusSemanticRemediationRunCounts`

One-row aggregate counts used by JSON, Markdown, and CLI output.

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

All counts are non-negative. `row_count` is one for a normal bounded decision and may remain one for a contained snapshot or executor failure. `manual_only_count` is one only when the row requires operator intervention.

## `CorpusSemanticRemediationRunWarning`

A bounded, non-fatal warning.

| Field | Type | Rules |
|---|---|---|
| `scope` | `str` | Allowlisted runner scope such as `semantic_remediation` or `cache` |
| `episode_ref` | `str \| None` | Canonical safe reference when applicable |
| `message` | `str` | Allowlisted metadata-only message; never dependency free text |

## `CorpusSemanticRemediationRunRow`

The single decision or attempt outcome.

| Field | Type | Rules |
|---|---|---|
| `episode_ref` | `str` | Canonical selected episode |
| `action` | `str` | Computed `semantic_summary`, `semantic_review`, `completed`, or `blocked` state |
| `status` | `str` | `selected`, `executed`, `reused`, `completed`, `failed`, `blocked`, or `rejected` |
| `reason` | `str` | Allowlisted reason phrase only |
| `requires_api_cost_ack` | `bool` | True only for semantic summary |
| `transcript_transfer_risk` | `bool` | True only for semantic summary |
| `may_incur_api_cost` | `bool` | True only for semantic summary |
| `manual_only` | `bool` | True for terminal fail-closed states |
| `planned_reads` | `list[str]` | Safe local paths or exact allowlisted in-memory labels |
| `planned_writes` | `list[str]` | Safe local paths or exact allowlisted non-path labels; empty for terminal states |
| `output_paths` | `list[str]` | Safe output paths returned by the selected executor |
| `source_report_paths` | `list[str]` | Safe existing timestamped review paths used as state truth |
| `provider` | `str \| None` | Safe provider identifier only for summary metadata |
| `model` | `str \| None` | Safe model identifier only for summary metadata |
| `failure_category` | `str \| None` | Exception class category only; no message or traceback |
| `warnings` | `list[str]` | Allowlisted metadata-only warnings |

Dry-run never predicts a concrete timestamped semantic-review report filename. Its planned write uses the exact label `timestamped semantic review JSON/Markdown reports`; confirmed execution reports only safe concrete paths returned by the existing review capability.

## `CorpusSemanticRemediationRunResult`

Public return type for Core callers and the source of the CLI/report JSON shape.

| Field | Type | Rules |
|---|---|---|
| `podcast_id` | `str` | Validated podcast identifier |
| `run_mode` | `str` | `dry_run` or `confirmed` |
| `confirm` | `bool` | Original confirmation mode |
| `episode_ref` | `str` | Canonical explicit episode |
| `requested_action` | `str` | Normalized caller request |
| `selected_action` | `str` | Freshly reduced action or terminal state |
| `executed_action` | `str \| None` | Non-null only when one executor was called |
| `report_json_path` | `Path \| None` | Confirmed-only latest report path |
| `report_markdown_path` | `Path \| None` | Confirmed-only latest report path |
| `filters` | `CorpusSemanticRemediationRunFilter` | Non-secret normalized request metadata |
| `counts` | `CorpusSemanticRemediationRunCounts` | Outcome aggregates |
| `rows` | `list[CorpusSemanticRemediationRunRow]` | Exactly one bounded row |
| `warnings` | `list[CorpusSemanticRemediationRunWarning]` | Bounded runner warnings |
| `not_investment_advice` | `bool` | Always `True` |

## Storage and Error Additions

### `CorpusSemanticRemediationRunAssetPaths`

| Field | Type | Value |
|---|---|---|
| `json_path` | `Path` | `data/corpus/{podcast_id}/corpus-semantic-remediation-run.json` |
| `markdown_path` | `Path` | `data/corpus/{podcast_id}/corpus-semantic-remediation-run.md` |

`corpus_semantic_remediation_run_asset_paths(podcast_id)` validates the podcast component through the existing storage safety seam and returns these paths without creating directories.

### `CorpusSemanticRemediationRunnerFailedError`

Dedicated validation/system-boundary error for invalid selectors, actions, chunk values, and exact acknowledgement failures. Messages are fixed or category-only and never interpolate unsafe dependency content.

## Additive 008 Semantic Summary Metadata

The semantic-summary status payload gains bounded readability metadata while preserving all existing keys and public 008 behavior:

| Field | Missing | Readable | Unreadable |
|---|---|---|---|
| `status` | `missing` | `available` | `available` (legacy compatibility) |
| `exists` | `False` | `True` | `True` |
| `readable` | `False` | `True` | `False` |
| `readability_status` | `missing` | `readable` | `unreadable` |
| `path` / `paths.markdown` | null | safe path | safe path |

The builder fully decodes UTF-8 only when the file is at most 2 MiB, retains no body text, and emits only generic warnings. Oversized content receives `readable=False` and `readability_status=unreadable`. Extractive-summary behavior, legacy semantic `status`, 009 action behavior, and public index persistence remain unchanged.

## State Transitions

| Fresh selected-episode state | `selected_action` | Row status | Manual only |
|---|---|---|---|
| Transcript status is not `valid` | `blocked` | `blocked` | Yes |
| Valid transcript, summary missing | `semantic_summary` | `selected` | No |
| Summary unreadable | `blocked` | `blocked` | Yes |
| Readable summary, review missing | `semantic_review` | `selected` | No |
| Latest review exact `passed` | `completed` | `completed` | No |
| Any other present/latest review state, including default `available`, blank, arbitrary, failed, blocked, or unreadable | `blocked` | `blocked` | Yes |
| Episode absent from the fresh snapshot | `blocked` | `blocked` | Yes |
| Snapshot builder exception | `blocked` | `failed` | Yes |
| Explicit requested action differs from an executable fresh selection | Computed action | `rejected` | No |

Confirmed mode validates acknowledgement when required, recomputes state, and dispatches only if the explicit request exactly equals an executable selection. After dispatch, the row transitions to `executed`, `reused`, `failed`, or `blocked` according to the existing executor result; no second transition or rescan occurs.

## Serialization Invariants

- `result_to_dict()` flattens count fields in the same style as existing corpus runners.
- Every `Path` is converted to a safe local string or `None`.
- Provider and model identifiers are rejected unless they match bounded identifier rules and contain no URI, query, fragment, control, secret-like, or advice-like text. Payload values then pass through runner-owned allowlist sanitization before CLI/report output; base URL, credential-variable name, and env-file paths are never serialized.
- Runner reports and CLI JSON use the same JSON-compatible payload.
- No schema field can carry a raw exception message or source body.
