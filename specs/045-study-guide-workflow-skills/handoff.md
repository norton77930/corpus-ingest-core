# Claude / Grok Implementation Handoff: SPEC 045

Implemented by Codex on 2026-10-03 after the user requested direct development. See [implementation evidence](implementation-log.md) and completed [tasks](tasks.md). The prompt below is the historical pre-implementation handoff; do not restart completed tasks. Preserve the existing worktree, including all 044 fixes.

## Copyable prompt

```text
Implement SPEC 045: specs/045-study-guide-workflow-skills.
Read AGENTS.md, docs/agent-handoff.md, docs/ai-development-framework.md,
then spec.md, plan.md, contracts/skill-protocol.md, tasks.md and quickstart.md.
Use SPECIFY_FEATURE_DIRECTORY=specs/045-study-guide-workflow-skills.

Deliver two portable Skills:
- study-guide-bundle -> generate_study_guide_bundle
- workflow-derivation-bundle -> derive_workflow_bundle
Each is one preview, explicit approval, at most one matching confirm, report/stop.
No automatic chain, upstream completion, fallback, retry, repair or cache rebuild.

Follow tasks in order with focused RED then minimal GREEN. One writer.
Do not modify production src/scripts/config, dependencies, MCP signatures or
registry count. Preserve all 044 working-tree changes. Do not create branch,
worktree, commit or deployment. No real provider, .env, download or transcription.

Critical details:
- Tool 26: run_mode=dry-run, explicit requires_llm and report_writes.
- Tool 25: run_mode=preview; no requires_llm/report_writes. Classify only
  exact 05/06 writes/reuses. Its generic risks text overstates reuse costs.
- Every successful confirm writes reports, including reuse.
- No-LLM branches send api_cost_ack="", even if the user supplied an old ack.
- Generating branches require the user's exact shared ack after this preview;
  generic yes never synthesizes it. Explain actual summary/lecture/context input.
- Preview is not a digest pin; Core recomputes state.
- Tool 25 retains legacy recovery cleanup and raw error transport. Do not claim
  Skill prose fixes those. Stop on known/reported recovery, never echo raw errors.
- Do not build a test-only fake agent and call it proof of Skill execution.
  Distinguish instruction tests, backend characterization and unperformed live eval.

Run targeted tests, then full pytest, compileall and diff --check using
.\.venv\Scripts\python.exe and a fresh short basetemp. Report skip reasons.
Review behavior and engineering standards separately; be honest if self-review.
Run speckit-converge, append missing tasks if any, complete in-scope gaps,
record actual evidence in this package's implementation-log.md and update status.
Do not reuse planning-session counts as implementation evidence.
```

## Completion evidence required

Changed paths with purpose; task status; focused RED/GREEN results; exact targeted/full commands and counts; compile/diff status; skips; instruction/backend/live-test distinction; no-runtime-change review; unresolved limitations; no commit unless separately requested.
