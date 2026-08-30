---
name: youtube-video-ingest
description: Safely preview and ingest one YouTube video into the corpus with one explicit human approval.
---

# YouTube Video Ingest

Use the mounted MCP tool to bring one YouTube video into the corpus. Keep the
human in control: one preview, one explicit approval, one matching confirmed
call, then stop.

## Procedure

1. Call `ingest_youtube_video` with the exact `url` the user gave and `confirm=false`.
2. Explain the derived podcast id and episode reference, the resolved title, the planned writes, and the returned warnings.
3. State plainly that this preview already resolved public source metadata over the network. It is zero-write but not zero-network, so the source host has already been contacted once before the human is asked anything.
4. Explain what confirming would add: downloading the source media, extracting audio, transcribing locally on this machine, and writing corpus artifacts. The source video itself is never kept.
5. Ask one explicit approval question and wait for the answer.
6. Treat absent, ambiguous, conditional, or negative replies as no approval.
7. After explicit approval, call the same MCP tool with the same `url` and `confirm=true`, exactly once.
8. Pass `title` only when the human supplied one, and `force=true` only when the human explicitly asked to overwrite existing artifacts. This tool needs no `api_cost_ack` because it calls no external LLM.
9. Report the bounded result and stop. Do not start another preview or action unless the user makes a new request.

The confirmed run does not rebuild the search index. Report the cache-stale warning and let the human decide when to rebuild.

If the MCP tool is unavailable, report a setup problem. Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, or autonomous loop as a fallback.
