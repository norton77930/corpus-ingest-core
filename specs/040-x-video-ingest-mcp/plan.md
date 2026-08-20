# Implementation Plan: X Video Ingest MCP Tool

**Branch**: `040-x-video-ingest-mcp` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/040-x-video-ingest-mcp/spec.md`

## Summary

Expose Spec 036 `run_x_video_ingest` as append-only MCP Tool 23 `ingest_x_video`.
The tool is a thin dry-run-first wrapper. Preview keeps the family
`"dry_run": true` envelope and names the result `preview` because it is
zero-write but not zero-network. Confirmed execution calls the existing Core
ingest and persists a metadata-only run report. Registry moves 22 → 23 at the
source of the pinned chain, not literal-by-literal.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing FastMCP, yt-dlp, av, faster-whisper (no new deps)
**Storage**: local `data/` artifacts + corpus run report pair
**Testing**: pytest
**Target Platform**: Windows 11 / PowerShell
**Project Type**: library + thin CLI + MCP
**Performance Goals**: preview returns a real metadata plan; confirm may take minutes
**Constraints**: no `.env` read, no LLM, no credentials, no live market API, no Hermes live
**Scale/Scope**: one new tool, one Core result/report extension, registry chain

## Constitution Check

- Core logic stays in `x_video_ingest.py`; MCP is a thin wrapper. **Pass.**
- Side-effect workflows include confirm-gated preview with planned writes and risks. Preview documents the 036 network-read exception instead of calling LLM providers. **Pass (documented exception, no amendment).**
- No LLM, no `api_cost_ack`, no `.env`. **Pass.**
- No research synthesis; ingest is acquisition. **Pass.**
- No live market API. **Pass.**
- `not_investment_advice=true` on result and envelope. **Pass.**
- Cache rebuild remains manual; warning only. **Pass.**
- Verification: targeted MCP/X tests, then `python -m pytest` and `compileall`. **Pass.**

**No constitution amendment.**

## Design Decisions

1. **New group module, imported last** — `mcp_tools_x_video.py` after stock lens so Tools 1–22 keep slots. Same playbook as 035.
2. **Keep envelope `dry_run: true`** — do not break the MCP JSON contract. Add `run_mode=preview`, `network_read`, `network_read_scope`.
3. **Full confirm wrap** — do not invent an acquire-only Core split in v1.
4. **Hide `work_dir` / device / model** — path safety and bounded MCP surface.
5. **Regenerate the Spec 029 snapshot** with the official export script.
6. **Per-episode report** under `data/corpus/{podcast_id}/x-video-ingest-runs/` so two episodes do not overwrite one podcast-level file.

## Registry Impact

`exact 22` is a chain: `hermes_skill_protocol._registry_tool_names_from_source`,
Spec 029 deny adapter + snapshot, registry contract tests, setup docs, and the
docs-count consistency check. Update the source list and size, regenerate the
snapshot, then move current-tense "22" claims to 23 or mark them historical.

Do not run live Hermes, C6, or the final verifier.

## Project Structure

```text
specs/040-x-video-ingest-mcp/
src/podcast_ingest_core/mcp_tools_x_video.py
src/podcast_ingest_core/mcp_server.py
src/podcast_ingest_core/x_video_ingest.py
src/podcast_ingest_core/storage.py
src/podcast_ingest_core/hermes_skill_protocol.py
deploy/hermes/spec029/spec029_mcp_deny_adapter.py
deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json
tests/test_x_video_ingest.py
tests/test_mcp_x_video_ingest.py
tests/test_mcp_tool_registry_contract.py
tests/test_mcp_server_facade_boundary.py
tests/test_mcp_setup_validation.py
tests/test_hermes_skill_protocol.py
tests/test_docs_registry_count_consistency.py
```

## Verification

```powershell
python -m pytest tests/test_x_video_ingest.py tests/test_mcp_x_video_ingest.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_setup_validation.py tests/test_docs_registry_count_consistency.py tests/test_mcp_server_facade_boundary.py tests/test_hermes_skill_protocol.py -q
python -m pytest
python -m compileall src scripts
git diff --check
```
