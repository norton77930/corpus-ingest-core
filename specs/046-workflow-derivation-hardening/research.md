# Research: 046

Repository evidence only; no external lookup or runtime operation required.

| Decision | Evidence and rationale | Alternatives considered |
| --- | --- | --- |
| Prioritize Tool 25 hardening | 045 implementation-log and Skill P10 explicitly disclose automatic recovery/raw errors. workflow_derivation._atomic_write_pair restores old, deletes part/old and skips non-files. | Source freshness is useful but does not fix destructive/error behavior; combined pipelines amplify it. Both deferred. |
| Local validation and publisher | Tool 26 _require_no_recovery_remnants, _require_bundle_entries and _atomic_write_bundle demonstrate owned-state handling. | Shared publisher extraction would couple a reviewed 044 path and expand regression scope. |
| Safe canonical metadata read | semantic_summary_identity.canonical_semantic_summary_path uses direct read_text; Tool 26 _resolve_source_path uses secure_read_bytes. | Changing shared identity helper would alter unrelated callers. |
| Retain Core context override | run_workflow_derivation accepts workflow_context; MCP intentionally does not. | Removing override is unnecessary interface break. New bounded read and link refusal are explicitly proposed below. |
| Context limit and paths | Context currently uses unbounded read_text; proposed 2 MiB UTF-8 limit aligns with lecture read cap. Check lexical absolute ancestors without resolving links, then bounded binary read. | Do not misuse secure_local_snapshot authority rules with caller-chosen root. No claim of race-proof custom context access. |
| Byte stream preservation | Existing copy2 preserves ordinary bytes but ignores directories and follows links. Validate entries first and stream non-pair bytes without decoding. | Recursive copying would require a new directory ownership model. No cap on extra binary size, no inode/metadata equality promise. |
| Fixed errors in Tool 25 only | mcp_tools_workflow_derivation preview uses raw ValueError text; confirm uses shared _tool_call. Tool 26 has local finite _safe_error. | Global error-handler change would affect 25 other tools. |
| Keep weak reports | _write_run_report delegates write_part_staged_report_pair, as enforced by run-report boundary tests. | Atomic artifact/report transaction deferred. Distinct post-publication/reuse report errors are sufficient here. |

Compatibility notes: test_failed_publish_leaves_neither_derivation_file currently matches a generic string. Replace only its exception assertion with typed publish_failed and retain tree/byte restoration checks. Its copy2 injection must target the actual new copy seam. Preserve finance/missing lecture/context diagnostics in Core unless an explicitly documented new unsafe-state case applies. Keep all exact MCP argument/order/count and success tests. Update derivation Skill/oracle tests only for deliberate backend error/recovery changes.

Threat limits: trusted managed roots, serialized writers, ordinary filesystem failures. Directory swaps have an absent-name window; no crash durability, no hostile concurrent mutation guarantee, no semantic lineage verification. secure_local_snapshot is for bounded Core-derived reads, not arbitrary context roots or publication. Research role was read-only, with no test or write commands.
