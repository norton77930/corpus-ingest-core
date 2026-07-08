# Contract: Corpus Remediation Plan

## Core Function

Future public function:

```text
generate_corpus_remediation_plan(podcast_id: str) -> CorpusRemediationPlanResult
```

Contract:

- Accepts exactly one podcast identifier.
- Refreshes the corpus artifact index before deriving remediation state.
- Writes `data/corpus/{podcast_id}/corpus-remediation-plan.json`.
- Writes `data/corpus/{podcast_id}/corpus-remediation-plan.md`.
- Returns output paths and summary counts.
- Does not execute remediation actions.
- Does not call RSS, network, SQLite cache, LLM providers, MCP tools, or cache rebuild.

## Storage Helper

Future helper:

```text
corpus_remediation_plan_asset_paths(podcast_id: str) -> CorpusRemediationPlanAssetPaths
```

Returned paths:

- `json_path`: `data/corpus/{podcast_id}/corpus-remediation-plan.json`
- `markdown_path`: `data/corpus/{podcast_id}/corpus-remediation-plan.md`

## CLI

Future command:

```powershell
python scripts/generate_corpus_remediation_plan.py --podcast gooaye
```

Stdout contract:

- JSON object with `podcast_id`.
- `plan_json_path` and `plan_markdown_path`.
- summary counts: `episode_count`, `action_count`, `blocked_action_count`, `optional_action_count`, `gated_action_count`, `warning_count`.

Stderr contract:

- Human-readable error only when the run fails.
- No raw transcript text, evidence text, prompt text, raw LLM output, `.env` values, API keys, tokens, or provider secret values.

## Artifact JSON Shape

Top-level JSON object:

```json
{
  "podcast_id": "gooaye",
  "source_corpus_index_json_path": "data/corpus/gooaye/corpus-index.json",
  "source_corpus_index_markdown_path": "data/corpus/gooaye/corpus-index.md",
  "episode_count": 0,
  "action_count": 0,
  "blocked_action_count": 0,
  "optional_action_count": 0,
  "gated_action_count": 0,
  "warning_count": 0,
  "episodes": []
}
```

Rules:

- No `generated_at` field.
- Paths are deterministic strings.
- Episode rows are sorted deterministically.
- Action rows are sorted by dependency order, then artifact family.
- No raw transcript, evidence, semantic body, prompt, raw LLM output, or secret values.

## Markdown Shape

Markdown must include:

- Title for the requested podcast.
- Source corpus index paths.
- Summary counts table.
- Episode remediation table.
- Optional detailed actions section when actions exist.
- Warnings section when warnings exist.

Markdown must not include:

- Raw transcript text.
- Evidence snippets.
- Semantic summary body text.
- Prompt text.
- Raw LLM output.
- Secret values.
- Investment advice or market claims.
