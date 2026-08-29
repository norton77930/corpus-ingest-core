# Contract: Corpus Semantic Remediation Runner

## Public Core API

```python
def run_corpus_semantic_remediation(
    podcast_id: str,
    *,
    episode_ref: str,
    action: str = "next",
    confirm: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    chunk_seconds: int = 600,
    max_segments_per_chunk: int = 120,
    progress_callback: Callable[..., None] | None = None,
) -> CorpusSemanticRemediationRunResult:
    ...
```

The function is exported from `corpus_ingest_core`. Existing public signatures and result schemas remain unchanged.

## Validation Contract

- `podcast_id` follows the existing safe storage component rules.
- `episode_ref` is required and must be a canonical safe episode reference. Blank, `latest`, path-like, URL-like, traversal, UNC, query/fragment, control-character, and unsupported values raise `CorpusSemanticRemediationRunnerFailedError` before snapshot evaluation.
- `action` is one of `next`, `semantic_summary`, or `semantic_review`.
- Confirmed execution rejects `next`; it requires one explicit semantic action.
- `provider` matches `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`; `model` is null or a bounded ASCII identifier that may include `/` or `:` but not a URI, query, fragment, control character, secret-like text, or advice-like text; `api_key_env` matches an uppercase environment-variable-name pattern. These identifiers are validated even though only provider/model may be serialized.
- `chunk_seconds` and `max_segments_per_chunk` are positive integers.
- Confirmed `semantic_summary` requires the repository's exact `SEMANTIC_API_COST_ACK`. Core validates it before snapshot building or provider construction. Invalid acknowledgement raises the dedicated runner error and writes zero files.
- Confirmed `semantic_review` does not inspect or require acknowledgement and does not resolve any LLM setting.

## Preview Contract

Every request that passes input validation and, for confirmed summary, exact acknowledgement validation and therefore reaches corpus evaluation builds exactly one `_CorpusIndexSnapshot`, then exactly one `_CorpusRemediationPlanSnapshot` from that exact index result and payload. Invalid input and invalid acknowledgement call zero snapshot builders. The requested episode is isolated before semantic state is reduced.

With `confirm=False`:

- no directory or file is created, modified, deleted, allocated, or persisted;
- 008/009 public generators and persisters are not called;
- semantic summary and review executors are not called;
- `.env` and credential values are not read;
- no LLM profile or local environment configuration is resolved;
- no provider is constructed or called;
- execution progress callbacks are not called;
- report paths are `None`;
- the result is derived only from the one fresh in-memory snapshot pair.

`action=next` returns the computed selection. An explicit preview action returns `selected` when it matches; an executable mismatch returns a bounded `rejected` row while retaining the freshly computed `selected_action`. Terminal state remains `completed` or `blocked`.

## State Machine Contract

| Transcript | Semantic summary | Latest semantic review | Selected action/state |
|---|---|---|---|
| missing, empty, partial, corrupt, unreadable, or otherwise not `valid` | any | any | `blocked` / manual-only |
| valid | missing | missing | `semantic_summary` |
| valid | unreadable | any | `blocked` / manual-only |
| valid | readable | missing | `semantic_review` |
| valid | readable | passed | `completed` |
| valid | readable | any present state other than exact `passed`, including default `available`, blank, arbitrary, failed, blocked, or unreadable | `blocked` / manual-only |

Another episode's state cannot influence this table. A valid canonical episode absent from the snapshot is blocked/manual-only. Existing duplicate-review discovery continues to select the latest valid timestamped candidate under the 008 contract.

A snapshot exception produces `selected_action=blocked`, a single row with `action=blocked`, `status=failed`, `manual_only=true`, and only the exception category. Dry-run report paths are null; a validated confirmed attempt writes this bounded latest report.

## Confirmed Dispatch Contract

Confirmed mode recomputes state from a fresh snapshot. If the explicit request does not match the executable selection, no executor runs:

- an executable action drift is `rejected`;
- a fail-closed terminal state remains `blocked`;
- a completed state rejects further execution.

A validated confirmed attempt receives the latest runner report paths and writes the runner report even when drift, a terminal state, or a contained executor failure prevents successful work.

### `semantic_summary`

The runner invokes `semantic_summarize_episode(...)` at most once and forwards only:

- canonical `podcast_id` and `episode_ref`;
- exact acknowledgement;
- `provider`, `model`, `base_url`, and `api_key_env`;
- `chunk_seconds`, `max_segments_per_chunk`, and `progress_callback`.

The existing executor remains the owner of transcript loading, provider calls, summary reuse, and atomic semantic-summary writing. The runner maps an existing artifact to `reused`, a new artifact to `executed`, and a bounded exception to `failed`; it never invokes review afterward.

### `semantic_review`

The runner invokes `review_semantic_summary_smoke(podcast_id, episode_ref)` at most once. It does not pass or inspect LLM configuration, read local environment configuration, construct a provider, or call the summary executor. The existing review capability remains the owner of timestamped JSON/Markdown writes and its current partial-pair failure behavior. Passed review maps to `executed`; every other returned review state maps to `blocked`/manual-only; a bounded exception maps to `failed`. Because an exception returns no review result, 015 records no inferred or rescanned output path even if one partial executor artifact exists. No retry, cleanup, summary regeneration, or fallback follows.

## Runner Report Contract

A validated confirmed attempt writes latest metadata reports at:

```text
data/corpus/{podcast_id}/corpus-semantic-remediation-run.json
data/corpus/{podcast_id}/corpus-semantic-remediation-run.md
```

The writer uses the repository's existing atomic `.part` replacement pattern for each runner-owned file; the JSON/Markdown pair is not represented as a transaction. Dry-run, invalid input, and invalid acknowledgement create no report and no `.part` file. If runner-report writing fails after an executor artifact was created, the dedicated safe command error is uncontained, CLI exits non-zero, existing artifacts remain, and no cleanup, fallback, or retry occurs.

The JSON payload is the JSON-compatible form of `CorpusSemanticRemediationRunResult` and includes:

- podcast, episode, run mode, confirmation, requested/selected/executed action;
- report paths, normalized non-secret filters, flattened counts;
- one row with status, fixed reason, risk/ack flags, safe planned reads/writes, safe outputs/source reports, safe provider/model identifiers, exception category, and warnings;
- top-level bounded warnings and `not_investment_advice: true`.

It does not include `generated_at`, raw transcript/evidence/semantic/prompt/provider content, raw base URL, URL query/fragment, secret values, raw exception messages, or traceback bodies. Markdown renders the same bounded metadata.

Confirmed reports warn that persisted corpus index/remediation plan and SQLite cache metadata may be stale and must be refreshed separately. The runner never refreshes them automatically.

## Thin CLI Contract

```text
python scripts/run_corpus_semantic_remediation.py \
  --podcast PODCAST \
  --episode EPISODE \
  [--action next|semantic_summary|semantic_review] \
  [--confirm] \
  [--api-cost-ack TEXT] \
  [--llm-profile NAME] \
  [--llm-profile-path PATH] \
  [--provider NAME] \
  [--model NAME] \
  [--base-url URL] \
  [--api-key-env NAME] \
  [--env-file PATH | --no-env-file] \
  [--chunk-seconds N] \
  [--max-segments-per-chunk N]
```

CLI ordering is part of the safety contract:

1. Parse and normalize input without loading local environment configuration.
2. If confirmed summary is requested, validate the exact acknowledgement. On failure, print a fixed safe error to stderr and exit non-zero before profile or environment loading.
3. Confirmed review bypasses profile/environment/provider resolution entirely, regardless of unused LLM flags.
4. Dry-run bypasses all profile and `.env` resolution even when LLM flags are supplied; Core constructs no provider and performs no semantic/review execution.
5. Only a confirmed summary with valid acknowledgement may use the existing CLI loader rules to resolve profile and optional local environment configuration.
6. Call the thick Core function once and print sanitized JSON to stdout. Progress output, if enabled by the existing summary executor, is bounded metadata on stderr only.

Exit codes:

- `0`: structured dry-run, selected, executed, reused, completed, blocked, rejected, or runner-contained failed outcome;
- non-zero: invalid input, invalid acknowledgement, or an uncontained command/system error.

Neither stdout nor stderr includes a transcript, semantic body, prompt, raw response, base URL, secret, traceback, or prohibited investment-advice language.

## Compatibility Contract

Feature 015:

- does not call or import 010 or 014 runners;
- does not alter 010 or 014 behavior;
- does not persist refreshed 008/009 snapshots;
- does not rebuild SQLite cache;
- does not change semantic summary or timestamped review artifact schemas;
- does not add a force or partial-transcript option;
- does not add batch, scheduler, retry, full-chain, automatic review, stock-lens continuation, or live market data;
- does not register an MCP tool and preserves the exact 12-tool registry and response envelopes.
