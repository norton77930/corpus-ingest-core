# Contract: Corpus Local Transcription Runner

## Core Function

Future public function:

```text
run_corpus_local_transcription(
    podcast_id: str,
    *,
    episode_ref: str | None = None,
    confirm: bool = False,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
) -> CorpusLocalTranscriptionRunResult
```

Contract:

- Accepts exactly one podcast identifier.
- Refreshes the 009 corpus remediation plan before selecting transcription work.
- Defaults to dry-run.
- Dry-run writes no transcript outputs and no run report artifacts.
- Confirmed execution requires exactly one `episode_ref`.
- Selects only transcript actions where local audio is available, the local audio path exists, source action status is ready, and transcript status is exactly missing.
- Skips download, corrupt/partial transcript repair, semantic, deterministic downstream, LLM, stock-lens, synthesis, unknown, blocked, optional, or gated actions from execution.
- Calls existing transcription core directly for confirmed execution.
- Passes explicit selected local `audio_path` into confirmed transcription work.
- Uses `force=False` for confirmed transcription in v1.
- Does not call RSS, network, SQLite cache rebuild, `.env`, LLM providers, MCP tools, or local scripts.
- Returns mode, source plan paths, report paths when written, summary counts, warnings, and local transcription rows.

## Storage Helper

Future helper:

```text
corpus_local_transcription_run_asset_paths(
    podcast_id: str,
) -> CorpusLocalTranscriptionRunAssetPaths
```

Returned paths:

- `json_path`: `data/corpus/{podcast_id}/corpus-local-transcription-run.json`
- `markdown_path`: `data/corpus/{podcast_id}/corpus-local-transcription-run.md`

## CLI

Future commands:

```powershell
python scripts/run_corpus_local_transcription.py --podcast gooaye
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm --model small --device cuda --compute-type float16
```

Stdout contract:

- JSON object with `podcast_id`, `run_mode`, `confirm`, `filters`, source remediation plan paths, optional report paths, summary counts, warnings, and rows.
- Dry-run stdout includes selected/skipped rows but report paths are null.
- Confirmed stdout includes report paths after writing run report artifacts.

Stderr contract:

- Human-readable error only when the run is rejected before producing a result or fails before producing a result.
- Progress lines may report metadata counts and paths only.
- No raw transcript text, prompt text, raw LLM output, `.env` values, API keys, tokens, provider secret values, or traceback bodies.

## Artifact JSON Shape

Confirmed run report top-level JSON object:

```json
{
  "podcast_id": "gooaye",
  "run_mode": "confirmed",
  "confirm": true,
  "source_remediation_plan_json_path": "data/corpus/gooaye/corpus-remediation-plan.json",
  "source_remediation_plan_markdown_path": "data/corpus/gooaye/corpus-remediation-plan.md",
  "report_json_path": "data/corpus/gooaye/corpus-local-transcription-run.json",
  "report_markdown_path": "data/corpus/gooaye/corpus-local-transcription-run.md",
  "filters": {
    "episode_ref": "EP672"
  },
  "row_count": 0,
  "selected_count": 0,
  "executed_count": 0,
  "reused_count": 0,
  "failed_count": 0,
  "skipped_count": 0,
  "rejected_count": 0,
  "warning_count": 0,
  "rows": [],
  "warnings": [],
  "not_investment_advice": true
}
```

Rules:

- No `generated_at` field.
- Paths are deterministic strings.
- Rows are sorted deterministically by episode reference and source action id.
- No raw transcript text, prompt text, raw LLM output, traceback body, or secret values.

## Markdown Shape

Confirmed run Markdown must include:

- Title for the requested podcast.
- Run mode and episode filter.
- Source remediation plan paths.
- Summary counts table.
- Local transcription outcome table.
- Warnings section when warnings exist.
- No investment advice notice.

Markdown must not include:

- Raw transcript text.
- Prompt text.
- Raw LLM output.
- Secret values.
- Traceback bodies.
- Investment advice or market claims.
