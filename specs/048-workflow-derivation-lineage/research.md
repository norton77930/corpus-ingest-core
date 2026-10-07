# Design decisions

Status: Proposed, 2026-10-04. Repository inspection only; no real provider calls.

1. Limit provenance to derivation05/06. Tool27 checks reusable presence, not source currentness. A separate query avoids changing that contract. Full lecture-to-transcript lineage requires another phase.
2. Capture lecture strings and effective allowed_tools before provider execution in workflow_derivation.py. Hash the actual ordered messages produced by _build_messages, plus an explicit recipe version. Re-reading after generation would bless concurrent source changes incorrectly.
3. Hash staged output files after write_text: Windows may translate newlines. Hashing the provider strings alone would record different bytes.
4. Add the receipt inside the existing owned staging directory before its first rename. A separate post-publication JSON write could leave mismatched versions. This explicitly supersedes046 non-pair preservation only for a recognized workflow_derivation.lineage.json during actual generation; all other extras remain protected.
5. Keep planned_writes/reuses restricted to the two outputs; add metadata_writes to the result and Tool25 preview. Tool27 validates two artifacts, so broadening that list would break compatibility. Ship the derivation Skill change together with Tool25.
6. Preserve allowed_tools ordering and duplicates as the existing loader does; ignore unused YAML and stripped whitespace. A custom context is recorded without its path; the default-only query returns not_evaluated instead of silently substituting default settings.
7. Legacy pairs are untracked. Reuse never creates provenance. Reserved-name invalid metadata blocks generation even with force, rather than deleting an unrelated extra file.
8. Receipt cap64 KiB; each output cap64 MiB; existing lecture/context bounded-read limits remain authoritative. Output size is checked on staged bytes before commit. These limits bound inspection and generation consistently.
9. Trusted roots and serialized writers remain assumptions. Digests detect observed differences, not malicious rewriting, semantic quality or model freshness; the query is not an atomic filesystem snapshot.

Evidence: src/corpus_ingest_core/workflow_derivation.py (input capture, _load_context, _build_messages, directory publisher); models.py WorkflowDerivationResult; mcp_tools_workflow_derivation.py; learning_workflow_next_step.py; tests/test_workflow_derivation_bundle_skill.py; specs/046-workflow-derivation-hardening/spec.md. A separate read-only research role inspected these seams; this is not an implementation review.
