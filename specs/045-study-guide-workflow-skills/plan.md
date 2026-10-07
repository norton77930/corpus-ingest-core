# Implementation Plan: Study-guide and Workflow Derivation Skills

**Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Branch**: existing main; no new branch or worktree
**Status**: implemented; see implementation-log.md for verification and limitations

## Summary

Add two portable SKILL.md documents over existing Tool 26 and Tool 25, with focused offline contract coverage and operator documentation. No production Python, new tools, provider changes or artifact writer changes. Each Skill is one preview, one approval, at most one confirm, then stop. The design treats the wrappers' different cost/error/recovery semantics explicitly.

## Technical Context

**Language/Version**: Markdown Skills; existing Python >=3.11 pytest environment for tests.
**Dependencies**: existing pytest and existing Core/MCP test fixtures; no new dependency.
**Storage**: two instruction documents; no persisted approval/session record.
**Testing**: static instruction contract tests, existing-wrapper characterization, offline dialogue cases with expected traces.
**Platform**: portable MCP-capable agents; Windows PowerShell development environment.
**Project Type**: agent instructions and tests over a local Python library/MCP server.
**Performance**: one preview and at most one confirm per authorized cycle; no new latency SLA.
**Constraints**: metadata-only, no tool discovery calls, no filesystem fallback, exact cost acknowledgement, unchanged 26-tool registry.
**Scale**: two Skills, two story-specific test files, one cross-Skill test file, a small dialogue fixture and docs updates.

## Constitution Check

Constitution 1.0.1 reviewed, no amendment. Pre-design and post-design gates pass:

| Principle | Application |
| --- | --- |
| I Local artifacts/evidence | Report returned metadata; no new bodies or source claims |
| II Thin interfaces/thick Core | No runner or production helper; Skills orchestrate the existing public tools |
| III Dry-run first | One successful validated preview before each approval |
| IV LLM opt-in/secrets | User exact ack only for generation; no config/body/.env inspection |
| V Evidence separation | Instruction text does not turn inference or external status into facts |
| VI No investment advice | Both Skills state the boundary |
| VII No live market API | No new provider or external data integration |
| VIII Manual cache | Report stale warnings; no rebuild call |
| IX TDD/verification | RED instruction checks before Skill text; targeted then full checks; honest eval limits |

No exception is requested. Preserve the already dirty 044 working tree; its presence is known authorization context, not permission to rewrite it.

## Project Structure

Planning package: spec.md, plan.md, research.md, data-model.md, contracts/skill-protocol.md, quickstart.md, tasks.md, checklists/requirements.md, checklists/approval-safety.md, handoff.md and workflow-record.md.

Implementation allowlist:

- `.agents/skills/study-guide-bundle/SKILL.md` (new)
- `.agents/skills/workflow-derivation-bundle/SKILL.md` (new)
- `tests/test_study_guide_bundle_skill.py` (new)
- `tests/test_workflow_derivation_bundle_skill.py` (new)
- `tests/test_learning_workflow_skill_contracts.py` (new)
- `tests/fixtures/learning_workflow_skill_cases.json` (new synthetic dialogue cases)
- `.agents/skills/README.md`
- `docs/mcp-usage.md`, `docs/agent-handoff.md`, `docs/verification-matrix.md`
- `specs/README.md` and this package's progress/evidence files

No `src/`, `scripts/`, config, dependency, transport, existing Skill, artifact, cache or historical eval edits. Additional paths require a demonstrated in-scope need; runtime hardening requires separate scope approval. Planning itself changes only this package, the registry entry and the AGENTS marker plan link.

## Phase 0 - Research

See [research.md](research.md). One explicitly requested read-only research role compared Tool 25/26 and existing Skill patterns. All technical unknowns are resolved by the local code and existing tests. No user preference remains blocking.

## Phase 1 - Design

### Portable Skills

Use directory-matching YAML `name` and a single `description`, no client-specific fields or executable code fences. Descriptions:

- study-guide-bundle: `Preview and, after explicit approval, generate or reuse one episode study guide through its MCP tool.`
- workflow-derivation-bundle: `Preview and, after explicit approval, generate or reuse one episode workflow derivation through its MCP tool.`

Each document embeds stable protocol anchors P01-P10 from the [contract](contracts/skill-protocol.md) with self-contained instructions. Do not require a deployed Skill to read spec files, Python source or another Skill. Name only its own callable tool; mention the other output family descriptively as prohibited automatic follow-up.

### Approval and response model

Use the transient state model in [data-model.md](data-model.md). Do not implement a Python approval engine. Check observable MCP envelope metadata; paths are for display/classification only and are never dereferenced. No claim of digest-bound approval. Missing or unknown shapes fail closed at the agent instruction level.

Tool 26 uses explicit requires_llm with compatible role sets. Tool 25 uses exact 05/06 writes/reuses because no requires_llm is exposed. Its unconditional risks text is not the cost authority. Both confirmed reuse paths write reports; Tool 25 does not expose report_writes, so do not invent report paths.

For no-cost branches always pass api_cost_ack="". This also prevents accidental generation after state drift. For generating branches accept only the exact user-supplied shared literal after this preview. Generic yes does not synthesize the literal.

### Failure limits

Tool 26 fixed errors can be safely summarized by known type and exact fixed message. Preserve post-publication and rollback distinctions; unknown messages become a generic uncertain-status summary. Tool 25 exposes raw errors and older recovery behavior: never echo raw error JSON, claim automatic cleanup is absent in Core, or promise no writes after its generic error. Known or reported recovery trouble stops the Skill before confirm; unseen trouble cannot be detected by a Skill-only change. No live smoke is required or authorized.

### Test design

1. Follow existing portable Skill tests for frontmatter and ordered clauses, but assert explicit rule anchors and operative clauses rather than entire paragraph formatting.
2. Check exact ack literal against `SEMANTIC_API_COST_ACK` imported in tests. Static Skill prose necessarily includes a copy; the test prevents drift.
3. Characterize actual Tool 25/26 shapes using existing tmp_data_dirs, fake providers and/or monkeypatched Core results. Reuse fixtures/helpers where suitable, do not copy storage-dir monkeypatch implementations.
4. Include synthetic dialogue case data (C01-C20 in contract). Validate required case coverage, rule references, expected legal tool/argument traces and safe user-facing outcomes. This validates fixture/contract consistency, not actual model execution. Do not build a fake agent that follows independent hardcoded rules and call it a Skill behavior test.
5. Review the wording against all dialogue cases separately from automated checks. If an actual host evaluation is not run, mark it unperformed; never report fixture checks as live compliance.
6. Run existing Skill, registry, facade, setup, ack, docs and secret guards without weakening them. No change to live tool count or prior tools' tests to accommodate drift.

## Phase 2 - Handoff

Generate tasks ordered RED -> Skill text -> GREEN -> cross-Skill boundary checks -> documentation -> regression -> separate reviews -> converge. One active writer. US1 and US2 are independently testable; implement sequentially for predictable test integration. Reviewers may compare contracts read-only. Taskstoissues is not used.

## Complexity Tracking

No constitution exception, new framework or shared runtime abstraction. Backend hardening and source currentness remain separate candidates, not hidden deliverables.
