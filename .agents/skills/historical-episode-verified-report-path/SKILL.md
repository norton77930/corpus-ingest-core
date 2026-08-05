---
name: historical-episode-verified-report-path
description: Human-controlled path for one named historical episode toward a verified research report—suggest next step, preview, one approved MCP confirm, then stop.
---

# Historical Episode Verified Report Path

Use this Skill when the user wants to advance **one named historical episode**
(for example `EP672`) toward a verified research report. Do not use this Skill
for latest-only flows (use the 017/018 Skills instead).

## Protocol

1. Ensure the operator has given an exact `podcast_id` and exact `episode_ref`.
   If they only want gaps, call `query_verified_research_report_coverage` with
   `has_bundle=false` once, present candidates, and **wait for the human to
   pick one episode_ref**. Do not auto-select.
2. Call `suggest_historical_verified_report_next_step` once with that exact
   `podcast_id` and `episode_ref`. Explain the suggestion code, recommended
   tool (if any), missing/stale roles, and whether exact `api_cost_ack` will be
   required later.
3. If suggestion is `report_present`, report digests and stop.
4. If suggestion is `publish_verified_report`:
   - Call `run_episode_verified_research_report_workflow` with `confirm=false`
     and the same `episode_ref`.
   - Ask for and wait for a new explicit approval of that exact `episode_ref`.
   - Call the same tool exactly once with `confirm=true`.
   - Report once and stop.
5. If suggestion is `completion_action`:
   - Call `run_corpus_episode_completion_workflow` with `confirm=false`,
     the canonical `episode_ref`, and `action=next` (or the suggested action
     only after re-preview matches).
   - Ask for and wait for explicit approval of the canonical episode and the
     exact selected executable action.
   - For `semantic_summary`, require the human to provide the exact
     acknowledgement text; do not invent it.
   - Call the completion tool exactly once with `confirm=true` and the approved
     action (and exact ack when required).
   - Report once and stop. Do **not** automatically call publish (019) in the
     same request.
6. If suggestion is `blocked`, report missing/stale roles and stop.

## Hard rules

- One confirmed side-effect MCP call per user request, then stop.
- Do not start another preview or confirm unless the user makes a new request.
- Do not use CLI, terminal, retry, scheduler, autonomous loop, force, partial
  mode, batch, or automatic cache rebuild.
- Do not resolve `latest` or substitute another episode.
- Do not call 017/018 latest tools for this historical path.
- Do not provide investment advice.
- If MCP is unavailable, report a setup problem only.
