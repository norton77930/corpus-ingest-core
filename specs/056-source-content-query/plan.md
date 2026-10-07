# Implementation plan — SPEC 056

Selected explicitly through SPECIFY_FEATURE_DIRECTORY; no branch or worktree. Python Core + existing FastMCP; no new dependency. Root is the sole writer.

## Constitution check

Local evidence and timestamps retained; thin MCP delegates to Core. Entire feature is read-only, so no confirm flag is introduced. No repository provider is constructed; existing synthesis acknowledgement remains mandatory. Host AI data exposure/billing is stated. No market API/advice, SQLite access or cache rebuild. Focused RED precedes each behavior slice, then targeted and full pytest/compileall/diff checks. No constitution amendment.

## Design

Add source_content_query.py with a single public query_source_content function. Securely enumerate one Core-derived transcript directory, select exactly one identity/title-derived JSON candidate, reject ambiguity and recovery markers, securely load the nonempty TXT/SRT companions and normalize strict JSON segments. Do not use the legacy first-glob finder or ordinary validator rereads. Extend secure_snapshot/secure_read_bytes with an opt-in require_single_link flag checking pathname and opened-handle link counts and content stability; old callers retain default behavior.

Array ordinal is zero-based; original scalar segment_id is optional and bounded. JSON SHA256 is source_version. inspect returns metadata only. read/search require exact expected version. Cursor contains next selected index/text offset and a SHA256 binding of source identity/version/action/query/window. It is deterministic encoded JSON, not authorization. Validate every field and maximum length; rerun bounded snapshot validation on every call. Fixed output character budgets permit partial segment chunks with exact offsets, no silent dropping. Cursor selections are derived fresh from the pinned bytes.

Limits: 4096 directory entries; at most 8 JSON candidates; 16 MiB per artifact; 100000 segments; query <=256 characters; page 1–100 segments (default 40); text budget 1–12000 characters (default 8000); cursor <=1024 characters. Half-open [start,end) filters use segment overlap; start-only/end-only supported, finite nonnegative boundaries and end>start. Segments require ordered starts, finite end>=start, nonempty text. Zero-duration segments belong when start is inside the window.

coverage reports scope, selected count, returned ordinals/chunk offsets, scope_exhausted, complete and truncated. complete means this response alone contains the whole selected scope from its initial position; a continuation response cannot claim it. Host can accumulate consecutive pages of one pinned scope into complete notes. Search reports literal matches and scanning scope; full match coverage is not full source coverage.

Append thin mcp_tools_source_content.py and facade export last, fixed finite reason map. Add source-content-qa SKILL.md and compact reference/dialogue oracles. Update registry, setup validator, operator docs and current counts 34→35 while preserving historical specs. Test MCP through actual SDK as well as direct wrapper.

## Files and sequence

1. specs/056-source-content-query/* and docs contract check.
2. tests/test_source_content_query.py → Core + opt-in snapshot guard.
3. tests/test_mcp_source_content_query.py → MCP registration, errors, SDK and current counts.
4. tests/test_source_content_qa_skill.py, dialogue fixtures → portable Skill/reference.
5. docs/verification-matrix.md, roadmap, MCP/setup docs, specs registry and handoff.
6. Read-only pilot .pytest-tmp/54m/data; fresh independent review, full verification and converge.

Research, data model, contracts and quickstart are in adjacent artifacts. No CLI, settings schema, database migration or automatic output publication is needed.
