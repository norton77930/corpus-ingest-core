# Implementation Plan: Historical Episode Verified Report Path

**Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

## Summary

Skill-first historical path: read-only Core suggestion composing 020-safe bundle discovery + 019 preview + 016 preview; thin CLI; MCP Tool 20 read-query; portable Skill enforcing one human-approved confirmed MCP call per request.

## Constitution Check

Local-only, thin interfaces, dry-run first for side effects (suggest is pure read), no investment advice, no auto cache rebuild, TDD. **No constitution amendment.**

## Design Decisions

1. No mega side-effect runner — reuse 016/019 confirms only via Skill protocol.
2. Suggest never calls `confirm=true`.
3. Tool 20 append-only after 1–19.
4. Skill may optionally use Tool 19 coverage to help pick an episode, but never auto-select without human choice.

## Project Structure

```text
specs/023-historical-episode-verified-report-path/
src/podcast_ingest_core/historical_verified_report_path.py
src/podcast_ingest_core/mcp_historical_verified_report_path.py
scripts/suggest_historical_verified_report_next_step.py
.agents/skills/historical-episode-verified-report-path/SKILL.md
tests/test_historical_verified_report_path.py
tests/test_historical_verified_report_path_cli.py
tests/test_historical_verified_report_path_skill.py
tests/test_spec_023_historical_verified_report_path_docs.py
```

## Verification

```powershell
python -m pytest tests/test_historical_verified_report_path.py tests/test_historical_verified_report_path_cli.py tests/test_historical_verified_report_path_skill.py tests/test_mcp_tool_registry_contract.py -q
python -m pytest
python -m compileall src scripts
```
