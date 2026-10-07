# Implementation Plan: Learning Workflow Next Step

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md) | **Status**: Implemented; offline-verified
**Branch**: Existing working tree; no branch/worktree/commit created.

## Summary

Add a bounded Core composition of the existing lecture and derivation previews and expose it as the appended Tool 27 `suggest_learning_workflow_next_step`. The planning baseline had26 tools; implementation appends the read-query as Tool27. The query reports one action, reusable completion, or a blocked stage without executing anything. It is not a general corpus readiness inventory.

## Technical Context

**Language/Version**: Python >=3.11 (pyproject.toml).
**Dependencies**: Existing FastMCP, dataclasses and pytest only; no additions.
**Storage**: No new storage; delegate local reading to reviewed 044/046 previews.
**Testing**: pytest with tmp_data_dirs, child-call spies, side-effect sentinels and bounded fixture trees.
**Platform**: Windows PowerShell primary; preserve existing portable Python behavior.
**Type**: Local Core + thin read-query MCP interface.
**Performance/Scale**: One episode, at most one lecture and one derivation preview, no corpus-wide loop or added scan; inherit existing bounded content reads. No fabricated latency SLA.
**Constraints**: No child runner edits, private helper imports, wrapper-to-wrapper calls, arbitrary file/provider inputs, auto-force, network/provider/writer/cache/confirmed execution, or new CLI/Skill.

## Constitution Check

Pre-design and post-design: all nine principles pass; no amendment proposed.

| Principle | Design obligation |
| --- | --- |
| I local evidence | Decisions reflect transient local previews; no new research/freshness claim |
| II thick Core | Decision tree in new Core module; MCP delegates once |
| III dry-run | Query itself cannot write; proposed next call is always a fresh preview |
| IV LLM/secret | No provider/.env access; only future cost requirement, no ack synthesis/body output |
| V evidence separation | complete explicitly means reuse by preview, not verified quality/lineage |
| VI investment safety | Fixed status metadata only; no advice or recommendations about investments |
| VII market boundary | No network/live market source |
| VIII manual cache | No cache read/rebuild or automatic artifact action |
| IX verification | RED/GREEN, documented contract tests, targeted then full checks and converge |

## Project Structure

Planning package: spec.md, plan.md, research.md, data-model.md, contracts/next-step.md, quickstart.md, tasks.md, checklists/, capability-map.md, handoff.md, workflow-record.md.

Implementation paths:
- `src/corpus_ingest_core/learning_workflow_next_step.py`: local result dataclass, fixed errors, explicit identity validation, preview-result validation and decision tree.
- `src/corpus_ingest_core/mcp_tools_learning_workflow.py`: new single tool, fixed-error mapping, standard success envelope.
- `src/corpus_ingest_core/mcp_server.py`: append import/re-export after study-guide tool.
- `tests/test_learning_workflow_next_step.py`, `tests/test_mcp_learning_workflow_next_step.py`: new offline tests.
- Existing registry/facade/setup and docs-count tests plus `scripts/validate_mcp_setup.py`: additive tool registration coverage.
- Current registry docs (`docs/api.md`, `docs/mcp-usage.md`, client setup/readiness/install docs, agent handoff/framework, verification matrix and architecture), specs/README.md: current count/tool listing only; leave historical counts labeled historical.
- `tests/test_spec_047_learning_next_step_docs.py`: planning guidance guard; change planned-state assertions only at actual implementation closeout.

Frozen: study_guide_bundle.py, workflow_derivation.py, shared path/report helpers, current result models, source/profile/prompt/provider/storage contracts, Tools 1-26 and both 045 Skills. Existing dirty changes are baseline, not permission to overwrite them.

## Design decisions

1. Validate exact identity first using existing public storage identity/path validation, not a new regex or a private runner function.
2. Call lecture Core preview with only identity, confirm=False, force=False. Validate identity, confirm=False, run_mode='dry-run', Boolean reused, and coherent plan lists. Project LLM flag with describe_study_guide_plan; use no report paths in public result.
3. Lecture generation/cover completion short-circuits derivation. Only explicit full reuse permits derivation preview, whose actual run_mode is 'preview', not 'dry-run'. Do not normalize or change those existing modes.
4. Validate derivation identity/mode/plan and same bundle directory as the lecture observation. Two previews are not an atomic snapshot; fixed freshness and quality disclaimers are mandatory.
5. Map only known typed preview refusal reasons; generic domain exceptions become stage-specific prerequisite blockers. Unknown exceptions become fixed query errors; inconsistent result shapes become blocked unexpected_preview. No exception-message parsing.
6. Suggested call is data only: existing tool name, exact identity and false flags. No dispatch helper, confirm endpoint or approval token. Future confirmed calls retain existing report writes and conditional cost rules.
7. Add Tool 27 last; registry read-query classification and all prior contracts must remain intact. No new CLI, provider/dependency, Skill routing expansion or ARTIFACT_LADDER changes.

## Implementation sequence

Foundation contract/identity checks -> US1 lecture decision -> US2 derivation/reuse/blockers -> US3 MCP and registry -> docs/regression/review/converge. Each behavior slice begins with a meaningful failing check. One active writer; read-only research/review may run independently. See tasks.md for paths and dependencies.

## Verification and complexity

Use quickstart.md. Full regression is required for runtime completion; planning validation uses docs tests and relevant registry tests only. No constitution violation or complexity exception. No shared publisher refactor, lineage manifest, recovery executor or learning catalog is introduced.
