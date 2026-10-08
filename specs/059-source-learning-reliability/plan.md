# Implementation Plan: Source learning reliability and note quality

**Feature**: SPEC059 | **Date**: 2026-10-08 | **Spec**: [spec.md](spec.md)
**Branch**: existing workspace; no branch/worktree authorized.

## Summary

Improve existing Tool35 diagnostics and portable learning Skills. Recovery is host guidance, not an automatic repository retry executor: once per explicit task after a pinned version, conversation-only checkpoint and sequential pages. Keep verifier deterministic/no-retry, raise bounded default120000, repair portable lecture fixture.

## Technical Context

Language: Python>=3.11/current3.12. Dependencies: existing MCP SDK/FastMCP, stdlib, pytest; none added. Storage: prepared transcripts read-only, no new persisted state. Platform: Windows/Linux. Project: Core/thin MCP/CLI/Markdown Skills. Performance: bounded per-page output; one recovery adds inspect+retry after failure. Scale: two Skills/references, finite Core/MCP diagnostics, verifier default and portable fixture. Constraints: same35 tools/signatures/reasons, full64 version, unchanged cursor binding, no source/secret/host settings/op-log publication.

## Constitution Check

Pre-design and post-design PASS under v1.0.1; no amendment. I/V: traceable evidence and separate AI/partial scope. II: finite diagnosis in Core, wrapper fixed messages, CLI Core default. III/IV: no provider or side-effect retry/consent change/.env access. VI/VII/VIII: no investment advice/live market API/cache rebuild. IX: focused RED/GREEN, regressions, full pytest/compileall.

## Research and Design

See [research](research.md), [data-model](data-model.md), [contract](contracts/learning.md), [quickstart](quickstart.md).

Core SourceContentError gains optional finite diagnosis while preserving reason/string. Fixed categories identify inspect_arguments, version_format, cursor_format/cursor_binding; legal-looking mismatched version remains source_changed. MCP maps only allowed reason/category pairs to fixed text, never exception/request values. Preserve validation order and bounds.

Existing QA response-contract holds detailed recovery rules; SKILL entrypoints emphasize sequential copying and reference that one exception. Entry's other failures remain stop/no-retry. Remove source_changed automatic restart from current resources/oracles. Template stays conditional/editable.

Core DEFAULT_MAX_TOTAL_CHARS=120000 feeds verifier and CLI; max_calls20/timeout60/per-page remain. SPEC058 preserves historical defaults with current SPEC059 note. Test-only scripted host oracle plus mutation guards demonstrate backend seams without claiming Hermes inference.

## Project Structure

Core: src/corpus_ingest_core/{source_content_query,mcp_tools_source_content,learning_mcp_acceptance}.py. CLI: scripts/verify_learning_mcp.py. Skills: .agents/skills/{source-content-qa,source-learning-entry}/SKILL.md and existing references. Tests: tests/test_source_learning_reliability.py, test_spec_059_source_learning_docs.py, test_learning_mcp_acceptance.py, test_mcp_study_guide_bundle.py, test_source_content_qa_skill.py and existing oracle fixture. Documentation: specs/059-source-learning-reliability and current usage/install/verification guides.

## Execution and Validation

Inline, one writer; reviewers/pressure agents read-only. Follow [tasks](tasks.md), no commit/push/deployment. Run failing focused checks before each behavior change, regressions after, then full checks. Real host discovery and note quality are separate pending operator acceptance, not build tasks. Existing ignored local feature selector/temp output is not published.

## Complexity Tracking

No constitutional exceptions, new subsystem, tool parameter, session file or production retry helper.