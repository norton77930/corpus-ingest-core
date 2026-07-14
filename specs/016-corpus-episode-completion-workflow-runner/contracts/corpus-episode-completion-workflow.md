# Contract: Corpus Episode Completion Workflow

## Public Core API

```python
def run_corpus_episode_completion_workflow(
    podcast_id: str,
    *,
    episode_ref: str = "latest",
    action: str = "next",
    confirm: bool = False,
    api_cost_ack: str = "",
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
    progress_callback: Callable[..., None] | None = None,
) -> CorpusEpisodeCompletionWorkflowRunResult:
    ...
```

### Request rules

- `podcast_id` is one safe podcast component.
- Dry-run accepts `episode_ref=latest` or one safe explicit episode selector.
- Confirmed mode rejects `latest` and requires the canonical episode reference
  returned by the preceding dry-run.
- `action` is `next`, `intake`, `audio_download`,
  `local_transcription`, `deterministic_remediation`, `semantic_summary`,
  or `semantic_review`.
- Confirmed mode rejects `next` and requires one explicit executable action.
- Confirmed `semantic_summary` requires the exact shared
  `SEMANTIC_API_COST_ACK` value before any read/config/provider/executor/writer
  work.
- Semantic-summary numeric options must be positive. Safe identifiers relevant
  to the selected action must be bounded and contain no
  URL/query/control/secret-like content.
- Semantic review ignores all semantic provider/model/base-url/env-name/chunk
  options without validating or resolving them and does not use the
  acknowledgement.
- No `force`, partial, retry, batch, scheduler, or multi-action option exists.

### Return and error rules

- Dry-run returns one bounded selection/terminal row and null report paths.
- A valid confirmed call recomputes state. Terminal or drifted state returns
  without a stage runner or 016 report. Exact executable equality calls at most
  one existing public runner, maps one outcome row, writes the 016 report pair,
  and stops.
- Deterministic remediation fixes `max_actions=1` for both preview and the
  confirmed 010 call.
- Structured blocked/rejected/contained-failed outcomes are returned normally.
- Invalid request or acknowledgement raises
  `CorpusEpisodeCompletionWorkflowRunnerFailedError` with a fixed safe message.
- An uncontained report-write or system error may raise the same dedicated error
  with category-only metadata; raw dependency messages and traceback bodies are
  never exposed.

## Thin CLI

```text
python scripts/run_corpus_episode_completion_workflow.py
  --podcast PODCAST
  [--episode latest|CANONICAL_REF]
  [--action next|intake|audio_download|local_transcription|
            deterministic_remediation|semantic_summary|semantic_review]
  [--confirm]
  [--api-cost-ack TEXT]
  [--transcription-model IDENTIFIER]
  [--transcription-device IDENTIFIER]
  [--transcription-compute-type IDENTIFIER]
  [--transcription-vad-filter]
  [--semantic-provider IDENTIFIER]
  [--semantic-model IDENTIFIER]
  [--semantic-base-url URL]
  [--semantic-api-key-env NAME]
  [--semantic-chunk-seconds POSITIVE_INT]
  [--semantic-max-segments-per-chunk POSITIVE_INT]
```

- Default invocation is `action=next`, `confirm=false`.
- CLI prints one metadata-only JSON object from Core serialization.
- Structured Core outcomes exit zero. Invalid inputs, invalid acknowledgement,
  or uncontained safe command errors exit non-zero without traceback or unsafe
  content.
- Dry-run and non-semantic actions do not load LLM profiles or `.env`.
- Confirmed semantic summary validates the exact acknowledgement before
  profile/local-environment loading. Only after that guard may the existing CLI
  configuration loader resolve approved defaults.
- Confirmed semantic review bypasses all LLM configuration loading.

## MCP Tool

### Name

`run_corpus_episode_completion_workflow`

### Input

The tool mirrors the public Core parameters except `progress_callback`. All
defaults and validation rules are identical. It does not perform local profile
or `.env` loading; any confirmed semantic-summary credential is supplied
through the MCP server process environment named by the validated env-name
option.

### Envelopes

Dry-run success:

```json
{
  "ok": true,
  "dry_run": true,
  "requires_confirmation": true,
  "data": {}
}
```

`requires_confirmation` is true only when the bounded result contains an
executable selected action. It is false for completed, blocked, rejected, or
contained failed terminal state.

Confirmed/terminal structured result:

```json
{
  "ok": true,
  "data": {}
}
```

Safe invalid/uncontained error:

```json
{
  "ok": false,
  "error_type": "CorpusEpisodeCompletionWorkflowRunnerFailedError",
  "message": "corpus episode completion workflow command failed"
}
```

- The error envelope never contains `str(exc)`, traceback, URL, raw content,
  provider response, or secret values.
- Existing twelve MCP tool names, input schemas, and envelopes remain unchanged.
- The reviewed registry contains exactly thirteen tools.

## Portable Agent Skill

### Location and metadata

`.agents/skills/corpus-episode-completion/SKILL.md`

Frontmatter:

```yaml
---
name: corpus-episode-completion
description: Safely preview and advance one podcast episode by one explicit MCP-managed action with human approval.
---
```

### Mandatory procedure

1. Call `run_corpus_episode_completion_workflow` with `action=next` and
   `confirm=false`.
2. Explain the canonical episode reference, selected action, planned reads,
   planned writes, blockers, network/local-compute/transcript-transfer/API-cost
   risks, and exact acknowledgement requirement.
3. Ask one explicit approval question and wait for the answer.
4. Treat absent, ambiguous, conditional, or negative replies as no approval.
5. After explicit approval, call the same MCP tool with the canonical episode
   reference, exact selected executable action, and `confirm=true`.
6. For semantic summary, include the exact acknowledgement only after the human
   explicitly provides the exact acknowledgement text. The agent must not
   synthesize or substitute the acknowledgement.
7. Report the bounded result and stop. Do not start another preview or action
   unless the user makes a new request.

If the MCP tool is unavailable, report a setup problem. Do not use a terminal,
CLI, another side-effect tool, cron/scheduler, retry, or autonomous loop as a
fallback.

## Confirmed Report Contract

Paths:

```text
data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json
data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.md
```

- Each file uses atomic `.part` replacement; the pair is not transactional.
- Reports are written only after early validation, fresh executable
  action-equality, and one stage-runner attempt.
- Payload includes normalized safe request metadata, selected/executed action,
  one bounded row, counts, warnings, risk/acknowledgement flags, safe local
  paths, safe provider/model identifiers when relevant, report paths, and
  `not_investment_advice=true`.
- Payload omits `generated_at`, feed/source URL, endpoint/base URL, query or
  fragment, transcript/evidence/semantic/prompt/provider bodies, credential
  variable/value, raw exception message, traceback body, and investment advice.

## Existing Contract Preservation

- 013, 014, and 015 public signatures and result schemas do not change.
- 010-015 standalone dry-run/confirmed behavior does not change.
- 008/009 public persistence behavior and artifact schemas do not change.
- The first twelve MCP tools remain byte-for-byte schema compatible.
- Cache/index/plan refresh remains a separate manual operation, except for the
  established confirmed 010-012 pre-execution refresh performed inside those
  unchanged public runners.
