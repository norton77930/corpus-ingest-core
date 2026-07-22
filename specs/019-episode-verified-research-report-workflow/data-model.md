# Data Model: Episode Verified Research Report Workflow

## Input filter

`EpisodeVerifiedResearchReportWorkflowRunFilter` (name illustrative):

| Field | Rules |
| --- | --- |
| `podcast_id` | Non-empty configured podcast id |
| `episode_ref` | Required explicit canonical ref; reject blank and reserved selectors |
| `confirm` | Default `false` |
| `stock_query` | Optional; same normalization as 018 assembly |
| `include_fixture_verification` | Optional bool; default false |

**Not present**: `api_cost_ack`, path overrides, force, partial, retry, scheduler, live provider controls.

## Run result

Immutable metadata including:

- `podcast_id`, `episode_ref`, `confirm` mode, `outcome`
- `ready` / `blocked` flags as applicable
- `missing_roles` / `stale_roles` / `failed_gates` (lists of bounded strings)
- `source_digest`, `report_version`, bundle paths when published/reused
- `warnings`, `not_investment_advice=true`
- stage plan entries that are inspection/assembly/publish only (no LLM child stages)

## Readiness inventory

Per required role (base set matches 018 lineage base roles; plus fixture/stock when options enable them):

| Role | Ready when |
| --- | --- |
| transcript | Valid transcript contract + identity |
| semantic_summary | Present, identity-bound to transcript title |
| semantic_review | Authentic passed + current summary hash |
| mentions / intelligence / industry_mapping / external_boundary | Present + lineage-valid |
| fixture / stock_lens | Only if corresponding options enabled |

## Bundle

Identical to 018:

```text
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/
  report.json
  report.md
  manifest.json
```

Payload classifications unchanged: reviewed narrative, verified timeline facts, mentions, clues, deterministic inference, external boundary, optional stock appendix, limitations, `not_investment_advice`.

## Checkpoint (optional)

If confirm reaches a terminal owned outcome that persists history, use the same family of metadata-only checkpoint as 018 under:

`data/corpus/{podcast_id}/verified-research/{episode_ref}.checkpoint.json`

Preview and early rejection write none. Checkpoint never overrides artifact truth.
