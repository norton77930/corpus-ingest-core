# Data Model: Corpus Remediation Plan

## CorpusRemediationPlan

Podcast-level derived artifact for one podcast.

**Fields**:

- `podcast_id`: requested podcast identifier.
- `source_corpus_index_json_path`: refreshed corpus index JSON path.
- `source_corpus_index_markdown_path`: refreshed corpus index Markdown path.
- `episode_count`: number of episode rows.
- `action_count`: total remediation actions.
- `blocked_action_count`: actions blocked by missing or unreadable dependencies.
- `optional_action_count`: optional actions, including semantic actions.
- `gated_action_count`: actions requiring external acknowledgement or manual confirmation outside this feature.
- `warning_count`: total corpus and row warnings.
- `episodes`: ordered list of `EpisodeRemediationRow`.

**Validation rules**:

- Content must not include generation timestamps.
- Episode rows are sorted deterministically by episode reference.
- Summary counts must equal the totals derived from episode rows.

## EpisodeRemediationRow

One episode's remediation status and action backlog.

**Fields**:

- `podcast_id`: requested podcast identifier.
- `episode_ref`: episode reference.
- `title`: title when available from local status metadata, otherwise empty string.
- `missing_artifacts`: artifact families missing from the refreshed corpus index.
- `blockers`: list of `RemediationBlocker`.
- `warnings`: non-fatal row warnings.
- `actions`: ordered list of `RemediationAction`.

**Validation rules**:

- Rows must not duplicate episode references.
- Rows must not contain raw transcript, evidence, semantic body, prompt, or raw LLM output text.
- Downstream actions must identify blockers when upstream artifacts are missing or unreadable.

## RemediationAction

One suggested next action.

**Fields**:

- `action_id`: deterministic stable id for the row and artifact family.
- `artifact_family`: one of `audio`, `transcript`, `extractive_summary`, `mentions`, `semantic_summary`, `semantic_review`, `episode_intelligence`, `industry_mapping`, `external_boundary`.
- `action_type`: one of `download`, `transcribe`, `generate`, `review`, `inspect`.
- `status`: one of `ready`, `blocked`, `optional`, `gated`.
- `order`: numeric order from the artifact dependency ladder.
- `reason`: concise factual reason based on missing or unreadable local status.
- `blocking_artifacts`: artifact families that must be repaired before this action is ready.
- `suggested_command`: optional advisory command text.
- `manual_only`: true when the command would perform a side effect or lacks dry-run semantics.
- `requires_api_cost_ack`: true for semantic LLM actions that would require acknowledgement in a separate future execution.

**Validation rules**:

- The feature must not execute `suggested_command`.
- LLM-related commands must be marked gated and must not include secret values.
- Side-effect command examples must not imply that the remediation plan executed them.

## RemediationBlocker

A dependency reason that prevents an action from being ready.

**Fields**:

- `blocked_artifact`: artifact family that cannot currently be generated or reviewed.
- `blocking_artifact`: missing or unreadable dependency.
- `blocking_status`: dependency status such as `missing` or `unreadable`.
- `message`: concise factual explanation.

## RemediationWarning

Non-fatal issue discovered while deriving the plan.

**Fields**:

- `scope`: `corpus` or `episode`.
- `episode_ref`: episode reference when applicable.
- `artifact_family`: artifact family when applicable.
- `message`: warning text copied or derived from local status metadata without raw artifact body content.

## Artifact Dependency Ladder

The v1 ladder is deterministic:

1. audio
2. transcript
3. extractive_summary
4. mentions
5. semantic_summary
6. semantic_review
7. episode_intelligence
8. industry_mapping
9. external_boundary

Transcript is the required upstream dependency for extractive summary, mentions, semantic summary, semantic review, episode intelligence, industry mapping, and external boundary. Semantic review also depends on semantic summary. Industry mapping depends on episode intelligence. External boundary depends on industry mapping.
