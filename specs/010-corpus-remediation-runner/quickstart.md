# Quickstart: Corpus Remediation Runner

## Prerequisites

- Local repository checkout.
- Local artifacts may exist under `data/**`.
- Corpus remediation plan generation from package 009 is available.
- No RSS, network, SQLite cache, `.env`, LLM provider, or MCP client is required for v1.

## Preview a Run

```powershell
python scripts/run_corpus_remediation.py --podcast gooaye
```

Expected outcome:

- The 009 corpus remediation plan is refreshed first.
- stdout prints a dry-run JSON result with selected/skipped/blocked/excluded counts.
- No `data/corpus/gooaye/corpus-remediation-run.json` or `.md` artifact is written.
- No deterministic generator action is executed.

## Confirm a Family-Bounded Run

```powershell
python scripts/run_corpus_remediation.py --podcast gooaye --action-family mentions --confirm
```

Expected outcome:

- Only ready deterministic `mentions` actions are selected.
- Excluded, blocked, skipped, reused, executed, and failed counts are reported.
- `data/corpus/gooaye/corpus-remediation-run.json` and `.md` are written after confirmed execution is attempted.
- Cache rebuild is not automatic.

## Confirm an Episode-Bounded Run

```powershell
python scripts/run_corpus_remediation.py --podcast gooaye --episode EP672 --confirm
```

Expected outcome:

- Only ready deterministic actions for `EP672` are selected.
- Actions are processed in dependency order.
- One action failure is recorded without hiding unrelated action outcomes.

## Validate Safety Boundaries

```powershell
python -m pytest tests/test_corpus_remediation_runner.py --basetemp=.pytest-tmp/run-010-runner
python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-010-mcp
```

Expected outcome:

- Dry-run writes no artifacts.
- Confirmed execution requires a filter.
- Download, transcription, semantic, LLM, MCP, network, `.env`, and cache rebuild behavior is not executed.
- JSON, Markdown, stdout, and stderr contain no raw transcript text, evidence snippets, semantic body text, prompt text, raw LLM output, or secret values.
- MCP reviewed tool count remains unchanged.

## Standard Checks

```powershell
python -m pytest --basetemp=.pytest-tmp/run-010-full
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```

Expected outcome:

- Full test suite passes.
- Source and scripts compile.
- Diff has no whitespace errors.
