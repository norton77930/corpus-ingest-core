# Quickstart: Latest Episode Verified Research Report Workflow

Do not run a real confirmed workflow for validation. Use fixture or monkeypatched tests only.

## CLI Preview

```powershell
python scripts/run_latest_episode_verified_research_report_workflow.py --podcast gooaye
```

The default is strict zero-write preview. Record the returned canonical episode reference and exact required `api_cost_ack`; preview is not approval.

## MCP / Skill Protocol

1. Call `run_latest_episode_verified_research_report_workflow` with `confirm=false`.
2. Show the canonical episode, planned local writes, transcript-transfer/API-cost risks, exact `expected_episode_ref`, and exact acknowledgement.
3. Wait for a new explicit episode-scoped approval.
4. Call once with `confirm=true`, the unchanged `expected_episode_ref`, and exact `api_cost_ack`.
5. Report the bounded completion/reuse/blocked/rejected/failed result once and stop.

The portable `latest-episode-verified-research-report` Skill must not fall back to CLI or terminal, retry, scheduler, force, partial mode, cache rebuild, another side-effect tool, a second latest resolution, or a live provider. The workflow uses no live market API and provides no investment advice.

## Fixture Verification

An approved call may select local fixture verification only through the bounded `include_fixture_verification` option. It does not authorize a live market API.

## Test Commands

```powershell
python -m pytest tests/test_latest_episode_verified_research_report_workflow_runner.py tests/test_semantic_summary_smoke_review.py
python -m pytest tests/test_latest_episode_verified_research_report_skill.py tests/test_mcp_server.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_setup_validation.py
python -m pytest tests/test_repository_secret_boundary.py tests/test_research_safety_eval_docs.py
python -m pytest tests/test_corpus_semantic_remediation_runner.py tests/test_corpus_episode_completion_workflow_runner.py tests/test_corpus_latest_episode_deterministic_workflow_runner.py tests/test_research_workflow.py
```

No test command should perform a real confirmed run, download, transcription, external LLM/API call, or live market request. Exact `api_cost_ack` and `expected_episode_ref` are test fixtures, not credentials.
