# Feature Specification: Hermes Skill Routing Contracts

**Created**: 2026-08-10  
**Status**: Contract Layer Complete — offline assurance only. Actual Hermes runtime routing is **BLOCKED/not_evaluated**; no contract result is runtime evidence or a runtime PASS.

## Spec 028 successor pointer

Spec 028 succeeds this offline contract layer only for a pinned-source runtime-observation capability gate. It does not alter the four-Skill mapping, exact-21 registry, or C6. Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run. Spec 029 successor pointer: it derives its closed scenario expectations from this package but is Offline Implemented only; live preflight not run, G2-G3 not authorized, and no runtime evidence is claimed.

## Goal

Record and mechanically validate the closed routing, approval, call-budget, and safe-evidence contracts for the four Skills already managed by Spec 026. This package consumes bounded intent/event projections only; it is not a natural-language parser and never invokes Hermes, MCP, Docker, a hook, or a workflow.

## Requirements

- Route only closed intents: one-step advance→016; latest deterministic without semantic/report→017; latest verified report→018; named/historical verified report→019; read-only→no side-effect Skill; unknown/conflicting→`clarification_required`.
- Derive the exact managed allowlist from `hermes_integration.MANAGED_SKILLS` and require it to equal these four Skill/tool pairs: `corpus-episode-completion`/`run_corpus_episode_completion_workflow`; `corpus-latest-episode-processing`/`run_corpus_latest_episode_deterministic_workflow`; `latest-episode-verified-research-report`/`run_latest_episode_verified_research_report_workflow`; `episode-verified-research-report`/`run_episode_verified_research_report_workflow`. Drift fails closed.
- Validate ordered source clauses and fixed per-Skill approval reducers. `confirm` is an exact Boolean, not a truthy value; all 016 event slots are closed, and 019 READY requires exact-reference approval.
- Bind a verified sequence to its exact Skill and call budget before evidence can succeed; cross-Skill evidence substitutions fail closed.
- Reject malformed artifact Skill identities before enum/hash operations; drift-guard each Skill's prohibitions and permit only its canonical high-level tool from static exact-21 registry source names.
- Emit only bounded evidence; source text, raw event payloads, prompts, responses, argv, endpoints, config values, sessions, and exceptions are never output.
- Keep the exact 21-tool registry unchanged: no Tool 22 and no production MCP wrapper/runtime change.

## Non-goals

This package does not validate a Hermes inference, install/upgrade Hermes, enable hooks, access a network, read `.env` or live configuration, run the Spec 026/C6 validator, or change workflow call budgets.

## Success Criteria

Offline tests prove routing, the exact four-source allowlist/tool mapping/ordered clauses, reducers and budgets, strict Boolean confirmation, safe evidence, and the fixed-mode CLI. Contract completion retains `not_evaluated` for runtime routing.