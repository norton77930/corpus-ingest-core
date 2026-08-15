# Safety Checklist

- [x] No `.env`, live config values, session dumps, raw prompt/response/args/results, endpoint, or credentials are read or emitted.
- [x] No Hermes inference, hooks, upgrade, Docker, OpenAB, network, or C6 validator is executed.
- [x] No production MCP wrapper imports this assurance-only module.
- [x] No Tool 22, exact-21 registry change, workflow runtime change, or automatic cache rebuild is introduced.
- [x] Unknown/hostile event, invalid confirmation, retry/fallback, blocked-019 continuation, malformed `SkillArtifact.skill`, and allowlist drift fail closed with bounded codes.
- [x] Per-Skill prohibition clauses are drift-guarded; `registry_tool_names` must exactly equal `_registry_tool_names_from_source()`'s safe 21-name source extraction, including all four canonical workflow tools, and rejects every registry tool except the one canonical high-level workflow tool for that Skill. Python AST source parsing fails closed on `SyntaxError`, `OSError`, an ambiguous decorator shape, every non-top-level direct reference, alias assignment, an indirect `.tool` decorator, every `mcp`-referencing decorator outside the accepted shape, indeterminate or duplicate registry names, and cross-source duplicate definitions with a mismatched definition count.
- [x] Contract PASS is explicitly distinct from actual Hermes runtime routing, which remains BLOCKED/not_evaluated.