# Tasks: X Video Ingest MCP Tool

**Input**: [plan.md](plan.md), [spec.md](spec.md)
**Prerequisites**: constitution unchanged; specify/clarify encoded; plan ready

## Phase 1 — Core result + report (US2 foundation)

- [x] T001 Add `run_mode` and `not_investment_advice` to `XVideoIngestResult`; preview=`preview`, confirm=`confirmed`
- [x] T002 Add `storage.x_video_ingest_run_asset_paths` and persist confirm report via `write_part_staged_report_pair`
- [x] T003 Update `tests/test_x_video_ingest.py` for new fields, preview zero-write of the report, and confirm report bytes

## Phase 2 — MCP Tool 23 (US1 + US3)

- [x] T004 [P] Add `tests/test_mcp_x_video_ingest.py`: preview envelope, zero-write, invalid URL, confirm delegates to Core, no `work_dir`/`device` on signature
- [x] T005 Add `mcp_tools_x_video.py` and import it last from `mcp_server.py`; re-export `ingest_x_video`
- [x] T006 Extend facade boundary `GROUP_MODULES` and any new alias

## Phase 3 — Registry chain 22 → 23 (US3)

- [x] T007 Add group file to `hermes_skill_protocol._MCP_TOOL_SOURCE_FILES` and change size 22→23
- [x] T008 Change deny adapter size 22→23
- [x] T009 Regenerate Spec 029 snapshot with `python scripts/export_spec029_tool_descriptor_snapshot.py`
- [x] T010 Update registry contract, setup validation, hermes protocol test, live-smoke tool_count pin
- [x] T011 Update governed docs to 23 or mark older 22 claims historical (`README`, `docs/*`, `specs/README.md`, `docs/agent-handoff.md`)
- [x] T012 Update exact-22 docs tests (`test_architecture_spec_docs`, `test_ai_governance_docs`, `test_spec_020_*`, `test_mcp_tool_registry_contract`)

## Phase 4 — Verification

- [x] T013 Targeted pytest listed in plan.md
- [x] T014 `python -m pytest` then `python -m compileall src scripts` then `git diff --check`

## Analyze notes

- Spec, plan, and tasks agree: X-only, preview network-read, full confirm wrap, no Skill.
- 035 is the wiring template; 036 is the Core behavior template.
- Historical packages 036–039 still say "exactly 22" in `specs/README.md`; those lines must be marked historical when the live count becomes 23.
- Hermes 026–034 remain blocked; this package does not run them live.
