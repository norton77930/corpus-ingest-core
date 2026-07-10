# Contract: Corpus Fresh Episode Workflow Runner

## Public Core Function

```python
run_corpus_episode_workflow(
    podcast_id: str,
    *,
    episode_ref: str = "latest",
    stage: str = "next",
    confirm: bool = False,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    max_actions: int | None = None,
) -> CorpusEpisodeWorkflowRunResult
```

Contract rules:
- `podcast_id` identifies exactly one configured or local podcast corpus.
- `episode_ref` defaults to `latest` when missing or blank.
- `stage` supports only `next` in v1; other values raise a workflow-specific error.
- `confirm=False` performs no stage execution and writes no workflow report.
- `confirm=True` attempts exactly one selected next stage and writes latest workflow reports.
- Core dispatches to existing core functions only; it must not shell out to scripts.

## Stage Selection Contract

The selected `next` stage follows this order:

1. `intake`: selected when the episode is not yet seeded/discoverable and 013 can resolve the selector.
2. `audio_download`: selected when seed/corpus metadata exists, audio is missing, and 012 dry-run reports a ready audio action.
3. `local_transcription`: selected when local audio is available and transcript is exactly missing according to 011 dry-run criteria.
4. `deterministic_remediation`: selected when transcript is ready and 010 dry-run reports ready deterministic actions for the episode.
5. `completed` or `blocked`: selected when no executable safe v1 stage remains.

The workflow must not execute semantic summary/review, LLM, stock-lens, synthesis, MCP, cache rebuild, download batch, transcript repair, or any non-selected stage.

## Result Shape

`CorpusEpisodeWorkflowRunResult` exposes metadata-only fields:

- `podcast_id`
- `run_mode`
- `confirm`
- `selector`
- `episode_ref`
- `stage`
- `selected_stage`
- `report_json_path`
- `report_markdown_path`
- `filters`
- flattened count fields
- `rows`
- `warnings`
- `not_investment_advice`

Rows include:

- `stage`
- `status`
- `reason`
- `planned_reads`
- `planned_writes`
- `output_paths`
- `source_report_paths`
- `stage_counts`
- `warnings`

## CLI Contract

```powershell
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest --stage next --confirm
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode EP677 --stage next --confirm --model small --device cuda --compute-type float16
```

CLI rules:
- Parses arguments only, calls core, serializes result JSON to stdout.
- Requires explicit `--stage next` whenever `--confirm` is present.
- Prints bounded error type/category to stderr on expected workflow errors.
- Does not print raw exception bodies or tracebacks.
- Passes transcription options only to core; core decides whether they are used.
- Passes remediation options only to core; core decides whether they are used.

## Storage Contract

Confirmed attempts write latest deterministic reports:

- `data/corpus/{podcast_id}/corpus-episode-workflow-run.json`
- `data/corpus/{podcast_id}/corpus-episode-workflow-run.md`

Dry-run must not write these paths.

## Safety Contract

All JSON, Markdown, stdout, and stderr output must exclude:

- full source URLs and URL query strings
- raw transcript text and evidence snippets
- semantic summary/review body text
- prompt text and raw LLM output
- `.env` values, API keys, tokens, provider secret values
- traceback bodies
- buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or implied investment actions
