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
- `confirm=False` performs no stage execution and is strict zero-file: it creates, modifies, or deletes no seed, audio, transcript, index, plan, 010-014 report, downstream artifact, or `.part` file.
- `confirm=True` attempts exactly one selected next stage through its existing public runner, accepts any refreshed rejected/blocked/failed outcome without trying another stage, and writes latest workflow reports.
- Core dispatches to existing core functions only; it must not shell out to scripts.

## Stage Selection Contract

The selected `next` stage follows this order:

1. `intake`: selected when the episode is not yet seeded/discoverable and 013 can resolve the selector.
2. `audio_download`: selected when seed/corpus metadata exists, audio is missing, and the package-private 012 preview reports a ready audio action.
3. `local_transcription`: selected when local audio is available and transcript is exactly missing according to the package-private 011 preview.
4. `deterministic_remediation`: selected when transcript is ready and the package-private 010 preview reports ready deterministic actions for the episode. Ready deterministic actions are selected even while later dependency-chain families (e.g. `industry_mapping`, `external_boundary`, `semantic_review`) remain blocked on not-yet-built upstream; the confirmed run executes the ready families and the operator re-invokes to advance the ladder.
5. `completed` or `blocked`: selected when no executable safe v1 stage remains. The remediation stage falls through to `blocked` only when no ready deterministic action remains (for example, only the LLM-gated `semantic_review` family is left).

Unseeded selection may read the `configured podcast RSS feed`. Seeded selection builds one fresh `in-memory corpus snapshot` and passes the same plan result/payload through all three previews with `source_persisted=False`. Snapshot or preview exceptions fail closed with category-only metadata and no later probe or dispatch.

Public standalone 010-012 runners remain compatible: their dry-runs refresh and persist 008/009, execute no external side effect, and write no own stage report. No new public parameters, exports, result fields, CLI JSON fields, or MCP tools are introduced.


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

Confirmed attempts let exactly one selected public runner perform its existing refreshed index/plan and stage/report writes, then write latest deterministic 014 reports:

- `data/corpus/{podcast_id}/corpus-episode-workflow-run.json`
- `data/corpus/{podcast_id}/corpus-episode-workflow-run.md`

014 dry-run must leave every local path and tree manifest unchanged, including stale index/plan/report sentinels and all `.part` paths.

## Safety Contract

All JSON, Markdown, stdout, and stderr output must exclude:

- full source URLs and URL query strings
- raw transcript text and evidence snippets
- semantic summary/review body text
- prompt text and raw LLM output
- `.env` values, API keys, tokens, provider secret values
- traceback bodies
- buy/sell/hold recommendations, target prices, guaranteed returns, personalized investment advice, or implied investment actions
