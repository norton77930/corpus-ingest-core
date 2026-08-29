# Implementation Plan: Episode Verified Research Report Workflow

**Branch**: `019-episode-verified-research-report-workflow` | **Date**: 2026-07-22 | **Spec**: [spec.md](spec.md)

## Summary

Add one Core-owned **explicit-episode** verified report workflow that previews local readiness with zero writes, rejects reserved latest selectors, and on confirm only assembles/publishes (or reuses) an 018-equivalent digest bundle when lineage and review gates already pass. No LLM, RSS, download, or `api_cost_ack`. Surfaces: thin CLI, MCP tool 16, portable Skill.

## Technical Context

- **Language**: Python 3.12; existing project stack only.
- **Reuse**: `assemble_verified_research_report`, `publish_verified_research_report_bundle`, `validate_current_verified_research_lineage`, `report_safety`, `canonical_transcript`, `artifact_lock` / episode claims as needed for publish.
- **Storage**: Existing report paths under `data/research-reports/`; optional checkpoint under `data/corpus/{podcast_id}/verified-research/`.
- **Testing**: pytest fixtures/monkeypatches only; no real LLM/network/download.
- **Constraints**: dry-run first; explicit `episode_ref`; registry becomes exactly 16 tools; preserve tools 1–15.

## Constitution Check

| Principle | How 019 complies |
| --- | --- |
| Local artifacts / traceability | Assembly uses local sources + lineage SHA graph; digest versioning |
| Thin interfaces | Behavior in Core; CLI/MCP/Skill thin |
| Dry-run first | `confirm=False` default, zero-write preview |
| LLM opt-in / secrets | No LLM path; no ack; no `.env` provider reads |
| Evidence separation | Reuse 018 report classifications |
| No investment advice | Reuse report_safety / 018 payload flags |
| No live market API | Unchanged |
| Manual cache rebuild | No automatic rebuild |
| TDD / verification | RED tests before GREEN per tasks |

**Gate**: PASS — no constitution amendment required (reviewed 2026-07-22).

## Project Structure

```text
specs/019-episode-verified-research-report-workflow/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── contracts/episode-verified-research-report-workflow.md
└── checklists/{requirements,safety}.md

src/corpus_ingest_core/
├── episode_verified_research_report_workflow_runner.py  # NEW
├── verified_research_report.py                          # REUSE (no semantic change required if already episode-scoped)
├── verified_research_lineage.py                         # REUSE
├── mcp_server.py                                        # APPEND tool 16
├── models.py / errors.py / __init__.py / storage.py     # exports/paths as needed

scripts/run_episode_verified_research_report_workflow.py
.agents/skills/episode-verified-research-report/SKILL.md
tests/test_episode_verified_research_report_workflow_runner.py
tests/test_episode_verified_research_report_skill.py
tests/test_mcp_tool_registry_contract.py  # 16 tools
```

## Design Decisions

1. **Separate workflow from 018**: Keep `run_latest_episode_verified_research_report_workflow` unchanged; add `run_episode_verified_research_report_workflow(podcast_id, episode_ref, *, confirm=False, ...)`.
2. **No ack parameter** on the public confirmed path (or accept but ignore is forbidden—do not require it).
3. **Readiness inspection** is a pure function over local paths + lineage validator; preview and confirm share the same inspection before publish.
4. **Blocked inventory** returns structured role/gate list in result metadata only.
5. **MCP**: append after 018 as tool 16; setup validator exact-16; Skill protocol mirrors 016/018 style without ack.

## Implementation Phases (for tasks)

1. RED tests: signature, zero-write preview, selector rejection, blocked inventory, publish/reuse, no provider/RSS hooks.
2. Core runner + exports/errors/models.
3. CLI + MCP + Skill + setup/docs/registry.
4. Regress 015–018 + full pytest.

## Verification

```powershell
$env:SPECIFY_FEATURE_DIRECTORY="specs/019-episode-verified-research-report-workflow"
python -m pytest tests/test_episode_verified_research_report_workflow_runner.py tests/test_episode_verified_research_report_skill.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
git diff --check
```

No real confirmed run against production data is required for package completion.
