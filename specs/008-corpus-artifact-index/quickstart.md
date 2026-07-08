# Quickstart: Corpus Artifact Index

## Prerequisites

- Use the repository root as the working directory.
- Do not read `.env`.
- Use only local test fixtures or existing local artifacts.
- Do not call RSS, network services, LLM providers, live market APIs, or MCP clients.

## Targeted Validation

Run the future targeted tests after implementation:

```powershell
python -m pytest tests/test_corpus_index.py tests/test_mcp_tool_registry_contract.py
```

Expected outcome:

- Empty corpus case writes valid index artifacts with `episode_count=0`.
- Fixture corpus case discovers local per-episode artifacts and reports statuses/counts/paths.
- Malformed metadata case marks only the affected artifact family `unreadable`.
- Semantic review case selects the latest review metadata deterministically.
- MCP tool registry remains unchanged.

## Manual CLI Smoke

After implementation, generate the index:

```powershell
python scripts/generate_corpus_index.py --podcast gooaye
```

Expected stdout:

- JSON object with `podcast_id`, `index_json_path`, `index_markdown_path`, `episode_count`, `warning_count`, and `artifact_family_counts`.
- No transcript text, evidence snippets, semantic summary body text, prompt text, raw LLM output, API key values, or provider secret values.

Expected artifacts:

```text
data/corpus/gooaye/corpus-index.json
data/corpus/gooaye/corpus-index.md
```

## Full Verification

Before claiming implementation complete, run:

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

The feature is not complete until targeted tests and full checks pass, or any skipped check is explicitly explained.
