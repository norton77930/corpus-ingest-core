---
name: latest-episode-verified-research-report
description: Preview and, after explicit episode-scoped approval plus exact acknowledgement, complete one latest verified research report workflow through one MCP call.
---

# Latest Episode Verified Research Report

Use this Skill only for a configured podcast when the user requests a verified
research report for its latest episode.

## Protocol

1. Call `run_latest_episode_verified_research_report_workflow` once with
   `confirm=false` to preview. Show the canonical episode reference, ordered
   plan, local writes, transcript-transfer/API-cost risks, and exact required
   `api_cost_ack` text.
2. Ask for and wait for a new explicit episode-scoped approval. The user must
   provide the exact previewed `expected_episode_ref` and the exact
   `api_cost_ack`; do not infer, trim, or substitute either value.
3. Call `run_latest_episode_verified_research_report_workflow` exactly once
   with `confirm=true`, the approved `expected_episode_ref`, and exact
   `api_cost_ack`. Include optional `stock_query` only if the user explicitly
   requested the podcast-wide appendix.
4. Report the bounded completion, reuse, blocked, rejected, failed, or manual
   intervention outcome once and stop.

Do not use CLI or a terminal fallback. Do not retry, scheduler, schedule, loop, force,
select partial mode, rebuild cache, call another side-effect tool, resolve a
second latest episode, or call an external live provider. Do not replace the
preview/approval protocol with autonomous execution. The report is not
investment advice.
