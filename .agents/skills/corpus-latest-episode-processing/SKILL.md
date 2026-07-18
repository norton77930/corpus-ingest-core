---
name: corpus-latest-episode-processing
description: Process one configured podcast's latest deterministic workflow once with confirmed MCP execution after an explicit request.
---

# Latest Episode Deterministic Processing

Use this Skill only when the user clearly asks to process a configured podcast's latest episode, for example: "幫我處理 Gooaye 最新一集。"

## Procedure

1. Map the spoken podcast name to a configured podcast id. If the name is not an unambiguous configured id, ask the user instead of guessing.
2. Acknowledge once that the explicit natural-language request is a one-time execution authorization. The MCP tool itself remains dry-run by default when called without this Skill protocol.
3. Call `run_corpus_latest_episode_deterministic_workflow` exactly once with `confirm=true`, supplying that podcast id.
4. Report the metadata-only result once and stop. The confirmed Core workflow pins one canonical latest episode, advances only local deterministic stages, and stops at `ready_for_semantic_summary`.

Do not call with `confirm=false` before the confirmed call. Do not call this tool more than once for one user request. Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, batch, cache rebuild, or autonomous loop as a fallback. Do not invoke semantic summary or semantic review. Do not resolve a new latest episode during the same request.
