# Contract: Corpus Remediation Runner

## Core Function

Future public function:

```text
run_corpus_remediation(
    podcast_id: str,
    *,
    confirm: bool = False,
    episode_ref: str | None = None,
    action_family: str | None = None,
    max_actions: int | None = None,
    force: bool = False,
    allow_partial: bool = False,
) -> CorpusRemediationRunResult
```

Contract:

- Accepts exactly one podcast identifier.
- Refreshes the 009 corpus remediation plan before selecting actions.
- Defaults to dry-run.
- Dry-run writes no downstream artifacts and no run report artifacts.
- Confirmed execution requires `episode_ref` or `action_family`.
- Selects only ready deterministic action families: `extractive_summary`, `mentions`, `episode_intelligence`, `industry_mapping`, `external_boundary`.
- Excludes download, transcription, semantic, LLM, stock-lens, synthesis, unknown, blocked, optional, or gated actions from execution.
- Calls existing core functions directly for confirmed deterministic execution.
- Propagates `force` and `allow_partial` to confirmed deterministic core function calls.
- Does not call RSS, network, SQLite cache rebuild, `.env`, LLM providers, MCP tools, or local scripts.
- Returns mode, filters, source plan paths, report paths when written, summary counts, warnings, and action rows.

## Storage Helper

Future helper:

```text
corpus_remediation_run_asset_paths(podcast_id: str) -> CorpusRemediationRunAssetPaths
```

Returned paths:

- `json_path`: `data/corpus/{podcast_id}/corpus-remediation-run.json`
- `markdown_path`: `data/corpus/{podcast_id}/corpus-remediation-run.md`

## CLI

Future commands:

```powershell
python scripts/run_corpus_remediation.py --podcast gooaye
python scripts/run_corpus_remediation.py --podcast gooaye --action-family mentions --confirm
python scripts/run_corpus_remediation.py --podcast gooaye --episode EP672 --confirm
```

Stdout contract:

- JSON object with `podcast_id`, `run_mode`, `confirm`, `filters`, source remediation plan paths, optional report paths, summary counts, and warnings.
- Dry-run stdout includes selected/skipped/blocked/excluded rows but report paths are null.
- Confirmed stdout includes report paths after writing run report artifacts.

Stderr contract:

- Human-readable error only when the run is rejected or fails before producing a result.
- No raw transcript text, evidence text, prompt text, raw LLM output, `.env` values, API keys, tokens, or provider secret values.

## Artifact JSON Shape

Confirmed run report top-level JSON object:

```json
{
  "podcast_id": "gooaye",
  "run_mode": "confirmed",
  "confirm": true,
  "source_remediation_plan_json_path": "data/corpus/gooaye/corpus-remediation-plan.json",
  "source_remediation_plan_markdown_path": "data/corpus/gooaye/corpus-remediation-plan.md",
  "filters": {
    "episode_ref": null,
    "action_family": "mentions",
    "max_actions": null
  },
  "row_count": 0,
  "selected_count": 0,
  "executed_count": 0,
  "reused_count": 0,
  "failed_count": 0,
  "skipped_count": 0,
  "blocked_count": 0,
  "excluded_count": 0,
  "warning_count": 0,
  "rows": [],
  "warnings": [],
  "not_investment_advice": true
}
```

Rules:

- No `generated_at` field.
- Paths are deterministic strings.
- Action rows are sorted deterministically by dependency order, then episode reference, then artifact family.
- No raw transcript, evidence, semantic body, prompt, raw LLM output, or secret values.

## Markdown Shape

Confirmed run Markdown must include:

- Title for the requested podcast.
- Run mode and filters.
- Source remediation plan paths.
- Summary counts table.
- Action outcome table.
- Warnings section when warnings exist.
- No investment advice notice.

Markdown must not include:

- Raw transcript text.
- Evidence snippets.
- Semantic summary body text.
- Prompt text.
- Raw LLM output.
- Secret values.
- Investment advice or market claims.
