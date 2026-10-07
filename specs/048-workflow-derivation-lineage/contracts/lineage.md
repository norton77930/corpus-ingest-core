# Lineage contract

## Generation and approval

Tool25 keeps all arguments and existing fields. Add metadata_writes in Core results and MCP preview: [canonical sibling workflow_derivation.lineage.json] for generation, [] for reuse. planned_writes and planned_reuses still contain only05/06. Declare existing receipt reads in preview when inspected. Preview remains zero-write/provider/network.

The receipt uses effective allowed_tools and actual consumed lecture/request data captured before provider execution. Hash actual staged output bytes. Use the same directory publication transaction for05/06 and receipt. Recognized receipt replacement is the sole new exception to046 extra-file preservation. Refuse malformed, foreign-identity or unsupported reserved-name records before provider construction during generation, including force. Reuse does not inspect provenance for freshness or modify it. Existing exact cost acknowledgement, rollback/recovery and report-failure behavior remains.

Updated derivation Skill requires metadata_writes, validates a generation receipt's exact filename and same parent as the pair, and requires [] for reuse. Missing/malformed/contradictory metadata stops before confirm. Display it in approval text. Do not add requires_llm or report_writes. Keep explicit force approval and one-preview/one-confirm/stop. Ship with the backend change. Lecture Skill and Tools26/27 remain unchanged.

## Read-only Tool28

inspect_workflow_derivation_lineage(podcast_id: str, episode_ref: str). No defaults, special latest/next selectors, caller paths, confirm, force, ack or provider options. Thin MCP delegates to Core and serializes the closed result. Invalid arguments return a fixed safe invalid-input error. Unexpected exceptions map to a fixed safe inspection-failed error, never exception text.

Ordered evaluation (first applicable row wins):

| Condition | status / reason | changed_roles |
| --- | --- | --- |
| Canonical identity/profile unavailable | blocked / identity_unavailable | [] |
| Unsafe managed path, special/reparse file | blocked / unsafe_path | [] |
| Existing recovery siblings | blocked / recovery_required | [] |
| Neither output nor receipt exists | not_generated / no_derivation | [] |
| Incomplete pair, including orphan receipt | blocked / incomplete_pair | [] |
| Complete pair, no receipt | untracked / no_record | [] |
| Receipt read fails or exceeds64 KiB | blocked / record_unreadable | [] |
| Unsupported schema | blocked / unsupported_schema | [] |
| Invalid JSON/schema/digests/roles | blocked / invalid_record | [] |
| Identity or canonical stem differs | blocked / identity_mismatch | [] |
| Valid receipt with context_origin=custom | not_evaluated / custom_context | [] |
| Required comparison input unavailable, invalid or over existing limit | blocked / inputs_unavailable | [] |
| Output unreadable or over64 MiB | blocked / outputs_unavailable | [] |
| Default-context comparisons all equal | current / matches_record | [] |
| One or more comparisons differ | stale / observed_changes | Changed roles below |

Use existing canonical path resolution, bounded reads and safety/recovery helpers. No stale-title fallback. Initial pair existence checks do not claim its content is valid. Custom-context rows validate record, identity, safe paths and complete pair but do not hash contents or reopen any custom path. Missing records never imply currentness.

Changed roles are ordered lecture_03, lecture_04, lecture_07, effective_context, recipe, request, output_05, output_06. Include each differing comparison, including request when an input change also changes rendered messages. recipe compares recipe_version. Blocked results never expose partial comparisons. Public shape/constants are in data-model.md.

The query never invokes generation, publication, cache rebuild, repair or providers, and does not gate existing reuse. It proves only equality to recorded derivation inputs and outputs observed now; it does not prove lecture freshness against transcripts, semantic correctness, provider/model currentness or an atomic snapshot.
