# Quickstart: Corpus Semantic Remediation Runner

## Prerequisites

- Use one explicit canonical episode reference such as `EP672`; `latest` is not supported.
- Complete intake, audio download, local transcription, and deterministic remediation separately before using 015.
- Run dry-run first and confirm only the single action selected by the fresh preview.
- Confirmed semantic summary may send transcript text to an external LLM provider and may incur cost. Confirmed semantic review is local and deterministic.

## Preview One Episode Safely

```powershell
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP672
```

The default action is `next`. Expected behavior:

- Builds one fresh in-memory corpus index snapshot and one remediation-plan snapshot for the explicit episode.
- Selects `semantic_summary` when a valid transcript exists but the semantic summary is missing.
- Selects `semantic_review` when a readable semantic summary exists but its deterministic review is missing.
- Returns `completed` when the latest semantic review passed.
- Returns `blocked` with manual-only guidance for an invalid transcript, unreadable summary, or failed, blocked, or unreadable review.
- Creates, modifies, and deletes zero files. It does not persist refreshed index/plan artifacts, allocate `.part` files, resolve LLM profiles or local environment secrets, construct a provider, call an LLM, execute review, or invoke progress callbacks.
- Prints metadata-only structured JSON. It never prints transcript, prompt, semantic body, raw provider response, base URL, secret, or traceback content.

Dry-run may also request one explicit preview action:

```powershell
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP672 --action semantic_summary
```

This still performs no action and writes no report. The result shows whether the requested action matches the freshly selected action.

## Confirm Semantic Summary

Only confirm `semantic_summary` when the preview selected it. The acknowledgement must match exactly:

```powershell
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP672 --action semantic_summary --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

Expected behavior:

- Validates the exact acknowledgement before profile, local environment, credential, or provider resolution.
- Recomputes the episode state from one fresh in-memory snapshot and rejects action drift without executing another action.
- Calls the existing semantic summary executor at most once and stops after an executed, reused, or failed outcome.
- Never runs semantic review automatically.
- Writes the existing semantic summary artifact only through the established semantic summary capability.
- Writes the latest runner JSON and Markdown reports after the validated confirmed attempt.
- Warns that persisted corpus index/plan and SQLite cache metadata may now be stale; refresh them manually when needed.

Provider, model, profile, endpoint, credential-variable name, and chunking options are optional safe configuration inputs. Never place a secret value in a command argument; use the configured credential environment-variable name.

## Confirm Semantic Review

Only confirm `semantic_review` when the preview selected it:

```powershell
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP672 --action semantic_review --confirm
```

Expected behavior:

- Requires no `--api-cost-ack`, LLM profile, model, endpoint, or credential option.
- Does not read local environment configuration, construct a provider, transfer transcript text, or call an LLM.
- Recomputes state and rejects action drift without generating a summary or executing another fallback action.
- Calls the existing deterministic semantic review capability at most once and preserves its timestamped JSON/Markdown report contract.
- Treats a failed or blocked review as terminal/manual-only; it does not retry or regenerate the summary.
- Writes the latest runner JSON and Markdown reports after the validated confirmed attempt.

## Structured Outcomes, Reports, and Exit Codes

Structured outcomes include `selected`, `executed`, `reused`, `completed`, `blocked`, `rejected`, and runner-contained `failed`. These outcomes use exit code `0` so callers can inspect the JSON status. Invalid input, unsupported or unsafe selectors/actions, missing or incorrect acknowledgement, and uncontained CLI/system errors use a non-zero exit code.

Dry-run and invalid input/acknowledgement write no runner report. A validated confirmed attempt writes:

- `data/corpus/gooaye/corpus-semantic-remediation-run.json`
- `data/corpus/gooaye/corpus-semantic-remediation-run.md`

The latest reports contain metadata, safe local paths, counts, statuses, risk flags, bounded warnings, and safe provider/model identifiers when applicable. They do not include a generation timestamp or unsafe source/provider bodies. The runner does not refresh 008/009 artifacts, rebuild SQLite cache, call 010 or 014, or add an MCP tool.

## Verification Commands

```powershell
python -m pytest tests/test_corpus_semantic_remediation_runner.py tests/test_corpus_index.py tests/test_corpus_remediation_plan.py
python -m pytest tests/test_corpus_remediation_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_audio_download_runner.py tests/test_corpus_episode_intake.py tests/test_corpus_episode_workflow_runner.py
python -m pytest tests/test_llm_ack_guard_contracts.py tests/test_llm_cli_no_leak.py tests/test_llm_provider_factory_boundary.py tests/test_mcp_tool_registry_contract.py tests/test_cache_rebuild_guard.py tests/test_repository_secret_boundary.py tests/test_architecture_spec_docs.py
python -m pytest
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```
