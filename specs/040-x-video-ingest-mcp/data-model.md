# Data Model: X Video Ingest MCP Tool

## XVideoIngestResult (extended)

Existing fields stay. Added:

| Field | Preview | Confirmed |
| --- | --- | --- |
| `run_mode` | `preview` | `confirmed` |
| `not_investment_advice` | `true` | `true` |
| `report_json_path` | `None` | corpus run report JSON |
| `report_markdown_path` | `None` | corpus run report Markdown |

`confirmed` remains the boolean already on the result. `run_mode` is the named
mode required by the spec (`preview` ≠ corpus `dry_run`).

## X video ingest run report

Written only on confirm, through `run_report_io.write_part_staged_report_pair`.

Paths:

```text
data/corpus/{podcast_id}/x-video-ingest-runs/{episode_ref}.x-video-ingest.json
data/corpus/{podcast_id}/x-video-ingest-runs/{episode_ref}.x-video-ingest.md
```

Payload (metadata only):

- `podcast_id`, `episode_ref`, `title`, `canonical_url`
- `run_mode`, `confirmed`
- `audio_path`, `seed_path`, `transcript_json_path`
- `planned_writes`, `warnings`
- `not_investment_advice: true`

No transcript body, no API key, no `.env` values.

## MCP preview envelope (additive)

Standard `tool_action_plan` keys plus:

- `run_mode`: `preview`
- `network_read`: `true`
- `network_read_scope`: `public_metadata_only`
- `not_investment_advice`: `true`

## Registry

Live reviewed set becomes exactly 23 names. Tool 23 is `ingest_x_video`.
Tools 1–22 are unchanged.
