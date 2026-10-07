# Feature Specification: Workflow Derivation Lineage

**Created**: 2026-10-04
**Status**: Implemented; offline-verified, authorized2026-10-04.
**Input**: Explain current capabilities after047 and plan the next stage.

## Context and bounded scope

Tool 25 generates05/06 from lecture03/04/07 and effective operator allowed_tools. Tool 27 can say these files are reusable, but does not evaluate their origin/currentness. Record the actual inputs and outputs of future confirmed derivation generations and provide a separate read-only comparison query. This phase covers derivation lineage only: it does not prove the lecture was generated from the current semantic summary/transcript, nor validate output quality.

Authorized surfaces: extend Tool 25 with a separate metadata_writes list and one owned lineage file; add read-query Tool 28 inspect_workflow_derivation_lineage. Tool 25 argument signatures and pair writes/reuses stay unchanged. Tool 26 and Tool 27 behavior/envelopes stay unchanged. Planning snapshot had27 tools; implementation appends Tool28. No automatic chaining, no automatic regeneration, no backfill of old files.

## User Scenarios & Testing

### User Story 1 - Record the origin of new derivations (Priority: P1)

An operator previews and confirms a new generation, sees the metadata write in the preview, and receives05/06 with a matching provenance record.

**Why this priority**: Without a record from actual generation, later comparisons cannot establish which inputs produced an existing pair.
**Independent Test**: A fake provider generates a fixture pair; the provenance record matches the exact consumed inputs and published bytes, and a publication failure leaves no mixed pair/record state.

**Acceptance Scenarios**:
1. Generation preview lists05/06 separately from the lineage metadata write and produces no files/provider calls.
2. Confirmed generation with exact cost acknowledgement publishes the pair and record together; ordinary extra-file bytes remain unchanged.
3. Failure writing/hashing the staged record or pair occurs before commit; previous files remain or the existing typed rollback/cleanup state is preserved.

### User Story 2 - Inspect changes without regeneration (Priority: P1)

An operator asks whether a named derivation still matches its recorded inputs and outputs.

**Why this priority**: Reusable presence and unchanged derivation inputs are different questions.
**Independent Test**: Mutate one fixture dependency/output at a time; the query identifies fixed changed-role labels while producing zero writes/network/provider calls.

**Acceptance Scenarios**:
1. A valid default-context record whose inputs/output bytes match reports current; a changed lecture, effective tool list, recipe/request or pair reports stale.
2. A complete old pair without a record reports untracked; no pair/record reports not_generated. Neither writes history or claims freshness.
3. A valid custom-context record reports not_evaluated because this MCP query accepts no custom path. Partial/orphan/invalid records and unsafe/recovery states report blocked.

### User Story 3 - Preserve explicit approval and compatibility (Priority: P2)

An agent can explain the new metadata side effect and the separate inspection result without silently regenerating an episode.

**Why this priority**: The new record must be included in the existing explicit approval flow.
**Independent Test**: Offline derivation Skill cases reject missing/malformed metadata_writes, display valid metadata writes, and keep one-preview/one-confirm/stop. Registry tests pin all existing slots and Tool 27 semantics.

**Acceptance Scenarios**:
1. Updated derivation Skill recognizes either pair-generation plus one matching sibling metadata write, or reuse with zero metadata writes; missing or contradictory metadata stops before confirm.
2. Tool 27 continues to use its existing two-artifact planned_writes/reuse contract, with source_currentness=not_evaluated; Tool 28 does not change that meaning.
3. Stale/untracked/custom results require a separate user decision; the query never invokes Tool 25, force, cleanup, backfill or cache rebuild.

### Edge Cases

Invalid/reserved identity, changed canonical title, partial pair, orphan receipt, JSON duplicate keys, malformed/unknown schema, mismatched identity, oversized metadata/input/output, unsafe/reparse/special files, four recovery siblings, metadata filename collision, Windows newline translation, input changes during a provider call, custom context without a stored path, context whitespace/comments versus order/duplicate changes, force replacement and post-publication report failure.

### Safety and Data Boundaries

Zero-write offline query. Only confirmed generation with existing exact api_cost_ack writes the record. Preview/reuse never manufacture provenance. No provider settings, .env, credential, prompt/body text, allowed tool names or absolute paths in the stored record or query response; only identity, version, context discriminator and digests in the record. No network/market API, automatic cache rebuild, investment advice, scheduler or multi-stage execution. Trusted managed roots and externally serialized writers remain prerequisites; no crash durability, adversarial tamper-proof attestation or atomic read snapshot claim.

## Requirements

### Functional Requirements

- **FR-001**: Record exactly the lecture03/04/07 strings and effective allowed_tools actually consumed by one generation; capture before provider execution and never reconstruct them by reading potentially changed files afterward.
- **FR-002**: Record hashes of the effective rendered request and a versioned recipe, plus actual staged05/06 bytes after platform text encoding/newline handling. Do not treat body.encode as the published bytes.
- **FR-003**: Publish05/06 and workflow_derivation.lineage.json in the same existing directory transaction. The lineage filename is the only new owned-file exception to046 non-pair preservation during generation; all other extras stay byte-identical. Preserve current rollback/cleanup/report-failure distinctions.
- **FR-004**: Keep planned_writes/planned_reuses restricted to05/06. Add metadata_writes separately to Core results and Tool 25 preview: one canonical sibling lineage path for generation, empty for reuse. Preview is zero-write/network/provider and includes all additional metadata reads/writes. Preserve Tool 25 inputs and existing pair fields.
- **FR-005**: Reuse, preview and lecture cover-only do not create, refresh or replace lineage records. Legacy complete pairs remain reusable and are reported untracked by inspection. Explicit force generation can establish provenance only by actually generating a new pair with acknowledged cost.
- **FR-006**: Add one explicit-identity offline read query with exactly podcast_id and episode_ref; return current, stale, untracked, not_generated, not_evaluated or blocked with fixed reasons/changed-role labels. Reject latest/next and unsafe identity before access; accept no caller path/confirm/force/ack/provider options.
- **FR-007**: Validate strict bounded metadata including exact schema/role keys, duplicate-key refusal, digest syntax, identity and context origin. Malformed/unsupported records are blocked, never untracked/current. Generation refuses an existing unrecognized lineage-name collision before provider access, including force.
- **FR-008**: Evaluate only the currently configured default effective context. A valid record of custom-context generation reports not_evaluated/custom_context without storing, reopening or revealing its custom path. Compare only effective allowed_tools, preserving order and duplicates; ignore unused YAML fields, comments and whitespace removed by the existing loader.
- **FR-009**: Expose no raw bodies, hashes, context names, paths, arbitrary warnings or exception text through the query. Bound all reads and distinguish unverifiable/missing inputs from changed inputs. No implicit execution or repair.
- **FR-010**: Update only the derivation Skill metadata validation/explanation and its offline oracle. Preserve conditional ack, explicit force approval, one-preview/one-confirm/stop, and no local fallback. Tool 26, Tool 27 and the lecture Skill remain unchanged. Append Tool 28 only after implementation authorization.
- **FR-011**: Compare saved generation inputs with current observations; changes during generation cannot be silently blessed as the generation inputs. Report failures never erase or retroactively refresh a committed record. No automatic freshness gating of existing reuse or Tool 27 is added.
- **FR-012**: Require focused RED/GREEN, real fixture integration, failure injection, preservation/registry/Skill compatibility regression, full tests, separate behavior/engineering review and Spec Kit converge before completion.

### Key Entities

- Generation provenance record: versioned identity, context origin, digests of consumed inputs/rendered request and committed pair bytes.
- Inspection observation: transient finite status/changed roles, explicitly limited to derivation inputs and outputs.
- Metadata write plan: additional declared side effect for new generation, separate from the existing pair role lists.

## Success Criteria

- **SC-001**: All generated fixture records match captured request inputs and actual staged output bytes, including LF/CRLF cases and source mutation during fake provider execution.
- **SC-002**: The six inspection outcomes and each changed-role category match the contract matrix in offline fixtures, with zero query writes/provider/network/cache calls and no injected private data in public results.
- **SC-003**: All publication-failure cases retain a matching old or new pair/record, or report the existing explicit incomplete-recovery state; unrelated files remain byte-identical.
- **SC-004**: Existing Tools1-27 keep their slots/signatures, Tool 25 only gains the documented additive metadata field, Tool 27 completion semantics remain unchanged, and all required tests pass.

## Assumptions and exclusions

The user authorized this bounded implementation on2026-10-04. Only the05/06 lineage is covered. Lecture-to-summary/transcript provenance, provider/model freshness, semantic quality, cryptographic signatures, bulk inventory, UI, recovery executor, automatic regeneration and migrations/backfills are excluded. Stale is informational and does not change existing reuse policy. Additive Tool 25 metadata and updated derivation Skill must ship together; the updated Skill refuses older previews lacking that field.

## Clarifications resolved for this proposal

Scope is one derivation family to keep publication ownership review bounded. Existing records are never fabricated. Custom contexts cannot be verified by a default-only query. Existing valid records may be replaced only with actual generation; unrelated reserved-name collisions require operator review. Complete Tool 27 results remain presence/readability reuse, not lineage validation. These are explicit proposed product choices, with no unresolved technical placeholder.
