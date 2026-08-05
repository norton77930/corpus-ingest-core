# Contract: Historical Verified Report Path

## Core

```text
suggest_historical_verified_report_next_step(
    podcast_id: str,
    episode_ref: str,
) -> HistoricalVerifiedReportNextStep
```

- Read-only/offline/zero-write.
- Rejects `latest`/`next`/empty.
- May call 019 and 016 only with `confirm=false`.

## CLI

```text
python scripts/suggest_historical_verified_report_next_step.py PODCAST_ID EPISODE_REF
```

## MCP Tool 20

- Name: `suggest_historical_verified_report_next_step`
- Inputs: `podcast_id`, `episode_ref`
- Read-query; no confirm/ack
- Append after Tools 1–19

## Skill

- Name: `historical-episode-verified-report-path`
- Protocol: suggest/preview → human approval → **one** confirmed side-effect MCP call → stop
