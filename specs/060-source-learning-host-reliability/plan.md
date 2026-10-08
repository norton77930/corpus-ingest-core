# Implementation Plan: Source learning host reliability

**Branch**: Existing main; no new branch/worktree. **Date**: 2026-10-08. **Status**: Implemented; local verification complete, actual operator acceptance pending.
**Spec**: [spec.md](spec.md). **Feature**: specs/060-source-learning-host-reliability.

## Summary

Repair the source-learning experience with a compact stateless cursor, response-based one-time recovery, host-visible discovery descriptions, foreground local routing and explicit source-grounded writing rules. Preserve expected_source_version, query binding, output bounds, approvals and the reviewed 35 tools. The user approved the plan and authorized implementation; actual operator/Hermes acceptance stays separate.

## Technical Context

- Language/version: Existing Python 3.12 workspace, standard-library base64/hashlib/struct; portable Markdown Skills.
- Dependencies: Existing FastMCP, MCP SDK, pytest and YAML support; no new dependency or Hermes integration layer.
- Storage: Read existing prepared transcripts. No new query/session state, cursor database or server secret.
- Platform: Windows local core/stdio tests and Linux Hermes deployment. Describe native-platform limitations explicitly.
- Scale: Existing 100000-segment / 16 MiB reader bounds. New cursor exactly 57 characters; verifier defaults max_calls20 and max_total_chars120000 remain.
- Public interfaces: Same Tool35 arguments, success metadata/coverage and finite errors. Cursor remains opaque; introduce a versioned encoding and preserve legacy decoding.
- Behavioral limits: Skills cannot mechanically block arbitrary Hermes tool choice or guarantee note quality. Live host acceptance is separate.

## Constitution Check

Reviewed constitution v1.0.1 before and after design; no amendment or exception needed.

- I: Preserve timestamps, exact chunk delivery, evidence and source identity/version.
- II: All cursor behavior remains in src/corpus_ingest_core/source_content_query.py; MCP/CLI remain thin.
- III: Preparation preview/fresh confirmation/background-job protocol is unchanged; no new side effects.
- IV: No repository LLM/provider calls or secret reads; generation acknowledgement stays unchanged. Host inference exposure remains disclosed.
- V: Source evidence, ASR uncertainty and AI explanation remain separate.
- VI/VII: No investment advice or live market provider.
- VIII: Cache rebuild remains manual.
- IX: Focused RED before each behavior change, relevant regressions and full checks before implementation closeout. Planning documents have their own checks.

## Research and Design

See [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/learning.md) and [quickstart](quickstart.md).

1. Cursor: emit c1. followed by canonical unpadded URL-safe Base64 for 40 bytes: a full 32-byte SHA256 integrity digest and two unsigned big-endian 32-bit fields (selected index, text offset). The digest covers a fixed c1 domain tag, the complete existing scope binding and both positions. No digest/version truncation. Fixed token length is 3 + 54 = 57. Reject malformed/corrupt/new unknown encodings with existing invalid_cursor diagnoses, and position/binding mismatch before returning text. Preserve the exact existing scope-binding serialization. A legacy no-prefix decoder retains historical rules and upgrades only newly emitted cursors. This is accidental-copy integrity, not an authentication mechanism.
2. Recovery: retained successful tool response is authoritative; discard failed request parameters. Reinspect exact IDs once, validate the original full version and reconstruct only unread scope by freshly copying its successful next_cursor, or empty cursor before first success. Keep scope/action and cumulative budgets, and do not reset the allowance. No new production retry executor.
3. Discovery: shorten all 23 current repository Skill descriptions to at most60 normalized Unicode characters; preserve each purpose without editing unrelated workflows. Make the entry description explicitly state YouTube/X learning and local MCP priority. Test actual Hermes desc[:57] + '...' behavior and a negative overlong case, not just the complete file text.
4. Entry/foreground: put local-first and no delegate_task/background AI rules in the relevant main Skills as well as contracts. Allow Skill/resource loading before the first source-processing call; that call is prepare_learning_source(confirm=false) for a supported URL. Missing/local-blocked paths stop and ask user choice. Existing server-side preparation jobs still need fresh approval and one confirm; no automatic learning continuation.
5. Writing: source-related concept requests require search/read evidence and surrounding context; standalone unrelated concepts do not. Add concrete neutral-speaker positive/negative examples and a pre-answer check of relevant read examples. All non-source explanation uses an explicit AI 補充 label. Default template remains a single editable resource with conditional headings, no unsolicited applications.
6. Verification: add real-reader synthetic cursor tests, test-only host recovery oracles, discovery/Skill contract guards and a default-budget whole-source SDK check. Keep these distinct from observed Hermes routing and note quality. Verify whole-source segment equality as well as scope_complete=true; never claim model correctness from the verifier.

## Project Structure

- Runtime: src/corpus_ingest_core/source_content_query.py; src/corpus_ingest_core/mcp_tools_source_content.py only if safe diagnosis mapping needs an existing-category adjustment.
- Setup compatibility: scripts/validate_mcp_setup.py accepts the exact historical and compact descriptions for its four governed Skills; metadata field/name checks stay strict. Tests include actual compact frontmatter and bad-field rejection.
- Skills: .agents/skills/source-learning-entry, source-content-qa and source-preparation main files and existing references; other .agents/skills/*/SKILL.md descriptions only.
- Tests: tests/test_source_learning_host_reliability.py (new), tests/test_source_content_query.py, tests/test_mcp_source_content_query.py, tests/test_source_learning_reliability.py, tests/test_source_content_qa_skill.py, tests/test_source_learning_entry_skill.py and tests/test_learning_mcp_acceptance.py. Update existing strict Skill frontmatter tests and setup metadata predicates for the compact descriptions while preserving approval/no-retry body checks and historical compatibility; keep strengthened rule guards and historical spec text.
- Documents: docs/verification-matrix.md, docs/api.md, docs/mcp-usage.md, docs/install-and-porting.md, .agents/skills/README.md, specs/README.md and AGENTS.md; SPEC060 design/contracts/checklists/quickstart/tasks. No personal handoff or implementation operation log.
- Planning guard: tests/test_spec_060_source_learning_docs.py validates package completeness, coverage and separate host acceptance.

## Execution and Validation

Use [tasks.md](tasks.md). One active writer, no parallel implementation. Independent read-only reviews/tests may be scheduled when explicitly required by an applicable method; no delegation of learning requests through Hermes. Complete US1, then US2, then US3, then US4, then regression/closeout. Before every behavior change: focused RED, smallest change, focused GREEN and relevant regressions.

The deterministic verifier remains no-retry and requires an explicit owned root or already managed loopback server, IDs and range. For whole-source acceptance, use zero as lower bound and an upper bound strictly above current inspect end_seconds, then require selected_segments and delivered_segments equal inspected segment_count. Its defaults are unchanged. Actual operator source verification and Hermes conversations require that environment; if unavailable report them pending, never substitute a synthetic result without naming it synthetic.

No branch, worktree, commit/push or deployment in this phase. Local closeout verification is complete; actual operator-source and Hermes acceptance remain pending. Changes after approval stay within the above paths and contracts.

## Complexity Tracking

No new subsystem, tool/schema/reason, API parameter, stored state or constitutional exception. Legacy decoding is the only compatibility branch. Host-runtime enforcement or a machine-managed reading orchestrator would require a separately approved future scope.
