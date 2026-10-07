# Research: 047

Repository-local inspection on 2026-10-03. No live artifacts, .env, provider or external websites were read. A separate read-only research role checked the preview composition seams; implementation remains unstarted.

| Decision | Repository evidence and rationale | Alternative deferred |
| --- | --- | --- |
| Single next-step query | study_guide_bundle.py:61-216 and workflow_derivation.py:52-125 already expose no-write previews | New disk inventory would duplicate their validity rules |
| Lecture before derivation | Lecture incomplete checks and 05/06 regeneration conflict precede preview return (study_guide_bundle.py:95-104) | Always call both previews: unnecessary context reads and conflicting suggestions |
| Reuse public projection | describe_study_guide_plan distinguishes generation from cover-only via requires_llm | Duplicating filename logic or importing private validators |
| Bounded meaning of complete | workflow_derivation.py:89-94 uses presence of 05/06; it does not validate their bodies | Digest/source-currentness and quality verification require a separate spec |
| Context failure blocks reuse | workflow_derivation.py:76-77 loads context before reuse | Bypassing it would disagree with the execution tool |
| Generic stage blockers | Partial lecture/pair and malformed context use generic domain errors; errors.py provides structured state errors for unsafe/recovery cases | Parsing human exception text or altering runner error contracts |
| Current modes differ | Lecture _result uses dry-run; derivation _result uses preview | Changing either success contract is out of scope |
| Append one read-query | mcp_server imports study-guide group last; test_mcp_tool_registry_contract locks 26 | Modifying Tool25/26 signatures or combining writes |
| No automatic follow-up | 045 portable Skills require their own preview/approval/confirm/stop | One-call multi-stage generation expands cost and partial-failure policy |

No unresolved technical dependency for this bounded design. Contract limitations are deliberate: generic prerequisite diagnostics, no upstream progress plan, no atomic snapshot or freshness guarantee. The proposed Tool 27 is a scope choice for user review, not already approved runtime behavior.
