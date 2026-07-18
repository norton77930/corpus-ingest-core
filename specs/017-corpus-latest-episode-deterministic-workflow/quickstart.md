# Quickstart: Latest Episode Deterministic Workflow

## Preconditions

- Use a configured podcast profile such as `gooaye`.
- Do not place secrets in command arguments; this workflow does not need `.env`
  or LLM configuration.
- Ensure local transcription prerequisites are available before confirmed use.

## Preview

```powershell
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye
```

Expected outcome: metadata-only JSON identifies one canonical latest episode,
its next deterministic stage, planned local effects, risk flags,
`run_mode="dry_run"`, `confirm=false`, and `outcome="dry_run"`; no artifact is
written. The `dry_run=true` field belongs to the MCP action-plan envelope, not
the direct CLI result schema.

## Confirmed local processing

SPEC 017 is Implemented. A direct local operator may use the controlled
`--confirm` command after reviewing local runtime and storage impact:

```powershell
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye --confirm
```

The MCP tool remains dry-run by default. The 2026-07-17 `seeded`/`downloaded`
status-mapping defect is a historical blocker resolved before the recorded
metadata-only confirmed evidence: `episode_ref=EP679`,
`outcome=ready_for_semantic_summary`, `ready_count=1`, `blocked_count=0`, and
`failed_count=0`. This documentation update does not rerun that workflow.

## Agent use

Tell an MCP-capable Agent: `幫我處理 Gooaye 最新一集。` The explicit natural-language request is a one-time execution authorization. The installed
`corpus-latest-episode-processing` Skill acknowledges once, calls the dedicated
MCP workflow exactly once with `confirm=true`, reports the metadata-only result
once, and stops. It does not make a `confirm=false` preview-before-confirm call
or invoke semantic work, retry, fallback, terminal, CLI, cache rebuild, or a
second tool call.

## Verification

```powershell
python -m pytest tests/test_corpus_latest_episode_deterministic_workflow_runner.py
python -m pytest tests/test_mcp_server.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_setup_validation.py tests/test_corpus_latest_episode_processing_skill.py
python -m pytest
python -m compileall src scripts
```

Use the repository's diff check before handoff. Do not rebuild cache as part of
this workflow; do it manually only when needed.
