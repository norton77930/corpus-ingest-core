# Implementation Plan: Hermes Skill Routing Contracts

## Scope

Add the assurance-only `hermes_skill_protocol` module, its fixed-mode validator, the Spec 027 package, focused tests, and status pointers. The module is intentionally not imported by `mcp_server.py`, `mcp_runtime.py`, `mcp_tools_*`, or a production workflow.

## Delivery slices

1. Closed intent oracle with fail-closed unknown handling.
2. Four-Skill artifact allowlist, exact tool mapping, and ordered protocol clauses.
3. Frozen bounded events, per-Skill reducers, strict exact `bool`, and fixed call budgets.
4. Safe fixed-shape evidence that requires the complete canonical four-binding allowlist.
5. A `contracts` CLI that reads paths only from `MANAGED_SKILLS`, plus synthetic happy and hostile projections.
6. Spec/documentation status synchronization.

## Evidence

Each slice starts with a focused failing pytest, then receives the smallest implementation and a focused green pytest. Final targeted regression covers the new tests, four managed Skill tests, MCP registry protection, selected workflow seams, and governance/docs tests. Full pytest, compileall, and `git diff --check` are reserved final verification and excluded from this execution.

## Risk control

No raw natural language crosses the oracle seam. The CLI accepts no endpoint, config, session, prompt, event, or result input. All non-enum/invalid inputs reduce to bounded failure codes; no caller value is returned.