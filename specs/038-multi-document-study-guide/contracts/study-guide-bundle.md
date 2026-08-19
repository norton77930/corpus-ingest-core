# Contract: `run_study_guide_bundle`

## Core

```text
run_study_guide_bundle(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
) -> StudyGuideBundleResult
```

Pinned via `inspect.signature` in `tests/test_contracts.py`.

## CLI

`scripts/run_study_guide_bundle.py`

- `--podcast` (required)
- `--episode` (required)
- `--confirm` (flag, default off)
- `--force` (flag, default off)
- `--api-cost-ack` (default empty)
- provider / model / base-url / api-key-env / reasoning-effort / read-timeout-seconds (same names as semantic CLI)

Stdout: metadata-only JSON (`result_to_dict`). Exit 1 on `PodcastIngestCoreError` with the exception class name, no body leak.

## Dry-run vs confirm

| | dry-run | confirm reuse | confirm write |
| --- | --- | --- | --- |
| filesystem writes | 0 | 0 on the four lecture files; report may update | atomic four-file replace + report |
| provider construction | never | never | only if `03`/`04`/`07` need generation |
| exact ack | not required | not required | required before `create_provider` |

A plan that will reuse must say reuse. A plan that will write must list the four write paths.

## Index

`SUPPORTED_ARTIFACT_FAMILIES` gains `study_guide` at the end. `ARTIFACT_LADDER` is unchanged.

## MCP

Unchanged. Exact 22 tools.
