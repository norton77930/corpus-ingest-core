# Contract: Episode Verified Research Report Workflow

## Core

```python
def run_episode_verified_research_report_workflow(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
) -> EpisodeVerifiedResearchReportWorkflowRunResult:
    ...
```

### Semantics

| Mode | Behavior |
| --- | --- |
| `confirm=False` | Strict zero-write readiness preview for `episode_ref` |
| `confirm=True` | Validate explicit ref; inspect readiness; if ready, assemble+publish/reuse; else `blocked` with role inventory |

### Hard rejects (before side effects)

- Empty/whitespace `episode_ref`
- Casefold reserved selectors: at least `latest`, `next`
- Confirmed path MUST NOT require or validate `api_cost_ack`
- Confirmed path MUST NOT call `create_provider` / semantic summarize / research workflow / 015–017 runners

## CLI

`scripts/run_episode_verified_research_report_workflow.py`

- Parses `podcast_id`, `episode_ref`, `--confirm`, optional stock/fixture flags
- Calls Core; prints metadata-only JSON (no transcript/secrets)
- Default dry-run

## MCP

- Tool name: `run_episode_verified_research_report_workflow`
- Position: **reviewed tool 16** (appended after 018)
- Default `confirm=false`
- Envelope: existing `ok` / `data` / `dry_run` patterns
- Registry size: **exactly 16** with tools 1–15 order and contracts preserved

## Skill

`.agents/skills/episode-verified-research-report/SKILL.md`

1. Preview with `confirm=false` and operator-supplied `episode_ref`
2. Wait for explicit human confirmation of that exact ref (and options)
3. One `confirm=true` MCP call
4. Report once and stop  
No CLI fallback, retry loop, scheduler, cache rebuild, ack string, or investment advice.

## Compatibility

- 018 tool and Core remain latest-only with ack + optional upstream stages
- 015–017 unchanged
