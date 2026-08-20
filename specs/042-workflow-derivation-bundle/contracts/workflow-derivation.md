# Contract: Workflow Derivation Runner

## CLI

Thin wrapper. Parses arguments, calls Core, prints metadata-only JSON.

Required: `--podcast-id`, `--episode-ref`.

Optional: `--confirm`, `--force`, `--api-cost-ack`, `--workflow-context` (default `config/operator_workflow.yaml`), provider knobs matching the study-guide CLI subset.

Must not accept a transcript path. Must not print lecture body, prompt, or secrets.

## Core

`run_workflow_derivation(podcast_id, episode_ref, *, confirm=False, force=False, api_cost_ack="", workflow_context=None, ...)`

Dry-run: no writes, no provider. Confirm: ack before provider; atomic pair write; lecture files unchanged.

## Index

`SUPPORTED_ARTIFACT_FAMILIES` gains `workflow_derivation`. `ARTIFACT_LADDER` unchanged.

## MCP

No new tool. Live registry remains 24 names, last `ingest_youtube_video`.
