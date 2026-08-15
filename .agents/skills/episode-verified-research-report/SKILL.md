---
name: episode-verified-research-report
description: Preview and, after explicit episode_ref approval, publish one verified research report for a named episode through one MCP call (assemble/publish only; no api_cost_ack).
---

# Episode Verified Research Report

Use this Skill when the user wants a verified research report for a **named**
episode (including historical `EP###`), not for “latest only” (use the 018
Skill for latest).

## Protocol

1. Call `run_episode_verified_research_report_workflow` once with
   `confirm=false`, the operator-supplied `podcast_id`, and exact `episode_ref`.
   Show readiness (`ready` / `blocked`), missing/stale roles, and risks. If preview
   is `blocked`, list missing/stale roles and stop.
   Do not invent `latest` or substitute another episode.
2. Ask for and wait for a new explicit approval of that exact `episode_ref`
   (and optional `stock_query` / fixture flag only if the user requested them).
   There is **no** `api_cost_ack` for this tool.
3. Call `run_episode_verified_research_report_workflow` exactly once with
   `confirm=true` and the approved `episode_ref`.
4. Report the `completed`, `reused`, `blocked`, or error outcome once and stop.

Do not use CLI or a terminal fallback. Do not retry, schedule, loop, force,
partial mode, rebuild cache, call 015/016/017/018, call LLM tools, resolve
RSS latest, or provide investment advice. If blocked, list missing roles only;
do not auto-chain remediation.
