# Data Model: 046

No new persisted database or result fields.

| Entity | Fields / invariants |
| --- | --- |
| Request | podcast_id, episode_ref, confirm, force, api_cost_ack; existing Core-only provider/context options |
| Canonical identity | metadata podcast/episode/title match; transcript/summary/lecture paths derived by existing storage functions |
| Context | default or Core/CLI override; local lexical absolute path, validated ancestors, regular UTF-8 file <=2 MiB, existing allowed_tools semantics |
| Entry inventory | direct names and regular-file state; only 05/06 are replaceable; non-pair bytes preserved |
| Recovery sibling | exact four suffixes; any entry type means refusal; inspection failure means unsafe_path |
| Attempt | created_staging, moved, committed; booleans set only after successful owned operations |
| State error | WorkflowDerivationStateError.reason_code; finite internal classification, no new MCP reason field |
| Result | existing WorkflowDerivationResult unchanged; preview fields and report paths retain meaning |

Transitions: validate -> preview return OR reuse/report OR exact ack/provider/validate output -> staging -> moved backup -> committed -> backup cleanup -> report -> success. Failures before commit may restore; failed restore retains recovery evidence. Failures after commit never trigger rollback. Reuse report failure does not imply regenerated artifacts. A subsequent request with retained bundle recovery is refused until operator handling outside this feature.
