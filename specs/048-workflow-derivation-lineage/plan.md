# Implementation Plan: Workflow Derivation Lineage

Status: Implemented; offline-verified, user-authorized2026-10-04. Planning history and execution evidence are tracked separately.

## Technical context
Existing Python core, dataclasses, hashlib/json, pytest and thin FastMCP facade; no new dependency, database or service. Filesystem-backed managed episode directories, Windows newline behavior and existing staged directory publication remain authoritative. Planning registry had27 tools; implementation appends Tool28.

## Constitution check
Pass at design time: local evidence, thick Core/thin interfaces, previewed metadata writes, exact existing provider acknowledgement, fixed offline query, no investment advice or live market API, manual cache, TDD and full implementation verification. No constitution amendment. Receipt is metadata within the existing publication transaction; ordinary report/source-path evidence remains in existing outputs. No transcript is sent by this feature.

## Structure and seams
- New src/corpus_ingest_core/workflow_derivation_lineage.py: pure strict receipt codec, canonical hashing and finite inspection values. It must not import workflow_derivation.py.
- Existing workflow_derivation.py: capture actual inputs/request before provider; preflight reserved-name ownership; stage/hash pair and receipt before first rename. Public inspect_workflow_derivation_lineage reuses local identity/path/context helpers and the pure module. Avoid cross-module private-helper imports.
- models.py: append defaulted metadata_writes list to WorkflowDerivationResult.
- mcp_tools_workflow_derivation.py: additive Tool25 preview field. New mcp_tools_workflow_lineage.py holds the thin Tool28 wrapper; mcp_server.py imports it last. A second decorator in the existing Tool25 group would register before Tools26/27, so the new group preserves slots.
- .agents/skills/workflow-derivation-bundle/SKILL.md and offline oracle: disclose/validate metadata, preserve approval/ack/stop. No lecture Skill or Tool26/27 behavior changes.
- tests/test_workflow_derivation_lineage.py and tests/test_mcp_workflow_derivation_lineage.py: receipt/query contracts; extend publication, Skill, registry and docs guards.

## Delivery and verification
Codec -> US1 generation -> US2 inspection -> US3 Skill/registry -> regression/review/converge. One active writer; reviewers read-only. No branches/worktrees/commits. Preserve dirty044-047 work. US1 is independently testable but must ship with US3 Skill handling. Detailed schema/precedence/limits are normative in data-model.md and contracts/lineage.md. The046 exception applies only to the recognized owned receipt during generation.

Focused failing checks precede each behavior change. Cover Windows bytes, source mutation during fake provider execution, strict bounded JSON, collisions, publication/report failures, zero query side effects, private-data sentinels, existing tool compatibility and Skill approval. Then full pytest, compileall src scripts, diff checks and recorded skip reasons. No real providers or artifact operations. Planning-only verification does not establish runtime acceptance.

## Limits
No atomic inspection snapshot, malicious-tampering attestation, model/semantic quality or lecture-to-transcript freshness. Legacy pair is untracked; custom context is not_evaluated. Backend and derivation Skill must ship together. No new dependency or approved scope expansion.
