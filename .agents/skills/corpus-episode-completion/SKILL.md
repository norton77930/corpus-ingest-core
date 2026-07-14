---
name: corpus-episode-completion
description: Safely preview and advance one podcast episode by one explicit MCP-managed action with human approval.
---

# Corpus Episode Completion

Use the mounted MCP tool to advance one podcast episode safely. Keep the human
in control: one preview, one explicit approval, one matching action, then stop.

## Procedure

1. Call `run_corpus_episode_completion_workflow` with `action=next` and `confirm=false`.
2. Explain the canonical episode reference, selected action, planned reads, planned writes, blockers, and network, local-compute, transcript-transfer, and API-cost risks.
3. Ask one explicit approval question and wait for the answer.
4. Treat absent, ambiguous, conditional, or negative replies as no approval.
5. After explicit approval, call the same MCP tool with the canonical episode reference, exact selected executable action, and `confirm=true`.
6. For `semantic_summary`, include the acknowledgement only after the human explicitly provides the exact acknowledgement text. Do not synthesize, shorten, or substitute it.
7. Report the bounded result and stop. Do not start another preview or action unless the user makes a new request.

If the MCP tool is unavailable, report a setup problem. Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, or autonomous loop as a fallback.
