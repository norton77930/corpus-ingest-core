# Data Model

| Model | Closed fields | Purpose |
| --- | --- | --- |
| `Intent` | seven enum categories | upstream bounded routing category; never request text |
| `Skill` | four managed Skill names | exact allowlist identity |
| `Tool` | four high-level tool names | fixed Skill/tool mapping |
| `SkillRoute` | disposition + optional `Skill` | route, no-side-effect, or clarification decision |
| `SkillArtifact` | `Skill` + source text | offline source input; source text is never evidence |
| `ProtocolEvent` | event kind, tool, exact `bool`, approval enum, action enum, `PreviewOutcome` | bounded event projection, never raw Hermes event |
| `SequenceVerification` | exact verified `Skill`, bool, failure enum, counts | reducer/call-budget result bound to one Skill |
| `ContractEvidence` | route, Skill, booleans, failure enum, capped count | fixed safe JSON projection |

`Approval` includes `Approval.EXACT_REFERENCE` for the 019 READY branch; 018 retains its distinct exact-reference-and-acknowledgement approval. A 016 sequence has a closed shape for every 016 event slot: preview, approval, confirmed call, report, and stop each reject fields that do not belong to that slot.

`SkillArtifact.skill` must be a `Skill`; malformed `SkillArtifact.skill` values fail closed before hashing, enum access, or frontmatter inspection. Every public success requires `0 <= observed_call_count <= call_budget`; valid success counts are `016=2, 017=1, 018=2, and 019=1 or 2`. `ArtifactValidation` carries `managed_allowlist_ok`; `registry_tool_names` is accepted only when exactly equal to the safe extracted set from `_registry_tool_names_from_source()`. That static source extraction uses Python `ast` to collect unambiguous direct `@mcp.tool(...)` calls only from module-body top-level `FunctionDef` and `AsyncFunctionDef` names. Any other direct reference, including an alias assignment, fails closed. The function name is used when absent; a single `name=` must be a non-empty constant string. Duplicate registry names, dynamic/non-string `name`, repeated `name`, or `**kwargs` fail closed. `SyntaxError/OSError` and ambiguous decorator shapes also fail closed. A cross-source duplicate fails closed, and the aggregate definition count must equal the unique-name count. Any indirect `.tool` decorator, or any `mcp`-referencing decorator that is not an accepted direct module-body declaration, fails closed. The extracted set must contain exactly 21 names and all four canonical high-level workflow tool names. `ContractEvidence.to_dict()` has the fixed fields `schema_version`, `ok`, `route`, `skill`, `artifact_ok`, `managed_allowlist_ok`, `sequence_ok`, `failure_code`, `call_count`, and `hermes_runtime_observation`. Its count is capped and it contains no path, source text, digest, prompt, argument, response, exception, or argv.
