# Quickstart: Corpus Remediation Plan

## Prerequisites

- Local repository checkout.
- Local artifacts may exist under `data/**`.
- No RSS, network, SQLite cache, `.env`, LLM provider, or MCP client is required.

## Generate a Plan

```powershell
python scripts/generate_corpus_remediation_plan.py --podcast gooaye
```

Expected outcome:

- `data/corpus/gooaye/corpus-index.json` and `.md` are refreshed first.
- `data/corpus/gooaye/corpus-remediation-plan.json` is written.
- `data/corpus/gooaye/corpus-remediation-plan.md` is written.
- stdout prints output paths and summary counts.
- No remediation action is executed.

## Validate Empty Corpus Behavior

```powershell
python -m pytest tests/test_corpus_remediation_plan.py -k empty --basetemp=.pytest-tmp/run-009-empty
```

Expected outcome:

- Empty local corpus writes valid empty JSON and Markdown plan artifacts.
- `episode_count=0`.
- `action_count=0`.

## Validate Safety Boundaries

```powershell
python -m pytest tests/test_corpus_remediation_plan.py --basetemp=.pytest-tmp/run-009-remediation
python -m pytest tests/test_mcp_tool_registry_contract.py --basetemp=.pytest-tmp/run-009-mcp
```

Expected outcome:

- Missing artifacts become ordered, non-executing remediation actions.
- Transcript blockers prevent downstream actions from appearing ready.
- Semantic actions are optional or gated.
- JSON and Markdown contain no raw transcript text, evidence snippets, semantic body text, prompt text, raw LLM output, or secret values.
- MCP reviewed tool count remains unchanged.

## Standard Checks

```powershell
python -m pytest --basetemp=.pytest-tmp/run-009-full
python -m compileall src scripts
git -c safe.directory=<repo-path> diff --check
```

Expected outcome:

- Full test suite passes.
- Source and scripts compile.
- Diff has no whitespace errors.
