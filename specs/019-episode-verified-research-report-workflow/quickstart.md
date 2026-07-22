# Quickstart Validation: Episode Verified Research Report Workflow

## Prerequisites

- Configured `podcast_id` (e.g. `gooaye`)
- Local episode artifacts already prepared for a known `episode_ref` (via 015–017 paths as needed)
- Valid lineage for required roles if testing happy path
- MCP setup optional for tool-16 checks

## Scenarios (tests preferred over manual)

1. **Preview zero-write**  
   Call Core with `confirm=False`, explicit `EP###`.  
   Expect: readiness metadata; no new files under corpus/research-reports for that run.

2. **Reject latest**  
   Call with `episode_ref="latest"` (and `NEXT`).  
   Expect: rejection; zero writes.

3. **Blocked inventory**  
   Fixture missing semantic review.  
   Expect: `blocked` (confirm) or non-ready preview listing `semantic_review` (or equivalent).

4. **Publish / reuse**  
   Complete fixtures + lineage; confirm twice.  
   Expect: first `completed`, second `reused`; three-file bundle under `v1-{digest}`.

5. **No provider**  
   Monkeypatch provider factory to fail if called; confirm on ready fixtures.  
   Expect: success without provider call.

6. **Registry**  
   Setup validator / registry contract: exactly 16 tools; tool 16 is 019; tools 1–15 unchanged.

## Commands (after implementation)

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/019-episode-verified-research-report-workflow"
python -m pytest tests/test_episode_verified_research_report_workflow_runner.py tests/test_episode_verified_research_report_skill.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
```

Manual CLI shape (illustrative):

```powershell
python scripts/run_episode_verified_research_report_workflow.py gooaye EP650
python scripts/run_episode_verified_research_report_workflow.py gooaye EP650 --confirm
```
