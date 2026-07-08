# Contract: Corpus Artifact Index CLI And Artifacts

## CLI

Command:

```powershell
python scripts/generate_corpus_index.py --podcast gooaye
```

Options:

- `--podcast <podcast_id>`: required podcast identifier.

Exit behavior:

- Exit `0` on successful index generation, including empty local corpus.
- Exit non-zero on invalid podcast identifier, invalid path input, or unrecoverable filesystem write failure.
- Print domain error messages to stderr.
- Print metadata-only JSON to stdout.

Stdout shape:

```json
{
  "podcast_id": "gooaye",
  "index_json_path": "data/corpus/gooaye/corpus-index.json",
  "index_markdown_path": "data/corpus/gooaye/corpus-index.md",
  "episode_count": 0,
  "warning_count": 0,
  "artifact_family_counts": {
    "transcript": {"available": 0, "missing": 0, "unreadable": 0}
  }
}
```

Stdout must not contain raw transcript text, evidence text, semantic summary body text, prompt text, raw LLM output, API key values, or provider secret values.

## JSON Artifact

Path:

```text
data/corpus/{podcast_id}/corpus-index.json
```

Required top-level fields:

- `podcast_id`
- `index_mode`
- `source_scope`
- `episode_count`
- `artifact_family_counts`
- `warning_count`
- `episodes`
- `not_investment_advice`

Required episode fields:

- `podcast_id`
- `episode_ref`
- `title`
- `artifact_status`
- `missing_artifacts`
- `warnings`

Required supported artifact families:

- `audio`
- `transcript`
- `extractive_summary`
- `semantic_summary`
- `semantic_review`
- `mentions`
- `episode_intelligence`
- `industry_mapping`
- `external_boundary`

Stability:

- Output content must be deterministic for unchanged local artifacts.
- Output content must not include `generated_at`, current wall-clock time, random values, or absolute machine-specific temp paths.

## Markdown Artifact

Path:

```text
data/corpus/{podcast_id}/corpus-index.md
```

Required sections:

- Title identifying podcast and index mode.
- Summary with episode count, warning count, and artifact-family counts.
- Episode status table with one row per episode.
- Warnings section when warnings exist.
- Boundary notice stating that the artifact is local status metadata, not investment advice.

Markdown must not contain raw transcript text, evidence snippets, semantic summary body text, prompt text, raw LLM output, API key values, or provider secret values.

## MCP Contract

No MCP tool is added in v1. The reviewed MCP tool count and response envelope remain unchanged.
