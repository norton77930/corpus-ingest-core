# Requirements Checklist

- [x] Intent oracle is enum-only and unknown/conflicting values fail closed to `clarification_required`.
- [x] Exactly four Hermes-managed Skills are compared against `MANAGED_SKILLS`, have portable `---/name/description/---` frontmatter, and map only to their one high-level tool.
- [x] Ordered clauses cover 016/017/018/019 preview, approval, confirmation, report, stop, and prohibitions.
- [x] Per-Skill reducer has one bounded call budget and requires exact `bool` confirmation; every 016 event slot has a closed shape and 019 READY requires `Approval.EXACT_REFERENCE`.
- [x] Evidence is bounded and no-leak; its route Skill, verified sequence Skill, and call budget must agree exactly, and its observed success count must be within budget and match the per-Skill success shape.
- [x] CLI has only `contracts`/`synthetic` modes and fixed failures.
- [x] Existing exact 21-tool registry and production runtime remain untouched; its offline source observation uses a fail-closed Python AST parser for module-body top-level sync and async direct `@mcp.tool(...)` definitions with statically resolved unique names, rejects cross-source duplicates, and rejects every indirect `.tool` decorator.
- [x] Actual runtime routing is marked BLOCKED/not_evaluated, not PASS.