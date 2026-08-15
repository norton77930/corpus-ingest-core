# Feature Specification: Offline Hermes Runtime Observation Capability Gate

**Created**: 2026-08-11  
**Status**: Complete — offline capability gate only.

## Goal

Determine, from one pinned first-party source manifest and bounded synthetic projections, whether Hermes can safely supply the six required runtime-observation capabilities. The gate is not a Hermes integration, collector, inference, or runtime test.

## Requirements

1. A canonical Skill identity is available.
2. A canonical Skill-to-tool linkage is available.
3. Fallback used is explicitly available.
4. Fallback not-used is explicitly available.
5. Guaranteed Skill/tool correlation is available.
6. An official no-side-effect positive control is available.

Only a synthetic projection with all six requirements present can return `PASS_CANONICAL_COVERAGE`. Missing or ambiguous capability is `BLOCKED_CAPABILITY`; malformed, non-enum, or non-Boolean evidence is bounded invalid evidence. The actual pinned manifest terminates at `BLOCKED_CAPABILITY`.

## Non-goals

No upgrade, Skill sync, hooks, collector, inference, runtime observation, Docker, MCP, network, OpenAB, configuration, session, `.env`, or C6 validator execution is in scope. The package stores no raw official page, no hook payload, no example prompt, and no arguments or results.

Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run.

## Successor authorization boundary

Any future work involving Hermes upgrade, Skill sync, hooks/plugin/collector, Docker/MCP/network, live config/session access, inference, or runtime observation must establish and receive separate approval for a new R2 successor spec; Spec 028 does not automatically authorize it.
