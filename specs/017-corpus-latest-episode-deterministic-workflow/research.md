# Research: Latest Episode Deterministic Workflow

## Decision: Use a separate core-owned workflow, not a Skill loop over 016

**Rationale**: 016 deliberately previews and executes one explicit action. A
new core runner can keep 016 unchanged while pinning one latest episode and
stopping reliably on deterministic failure.

**Alternatives considered**:

- Have the Skill call 016 repeatedly: rejected because an Agent loop can lose
  the canonical target, retry unexpectedly, or stop with an incomplete report.
- Expand 016 to execute the full chain: rejected because it weakens its explicit
  human one-action contract.

## Decision: Resolve latest once with intake, then use canonical refs

**Rationale**: `run_corpus_episode_intake(..., episode_ref="latest",
confirm=False)` is the existing bounded selector. All later probes and stage
executions receive its safe canonical episode reference, preventing an RSS
update from changing the in-flight target.

**Alternatives considered**:

- Pass `latest` to every stage: rejected because each feed read can select a
  different episode.

## Decision: Reuse existing single-stage runners and advance remediation one action at a time

**Rationale**: Existing public runners own artifact validation and write
semantics. The new runner uses the private
`_select_next_stage(..., allow_semantic_handoff=True)` selector only for a
canonical-episode next-stage probe, dispatches intake/audio/transcription with
their public functions, and calls `run_corpus_remediation(..., max_actions=1)`
for a single deterministic family. It re-probes between successful actions.
This keeps each remediation failure from advancing a later family. The 014 public workflow contract remains unchanged. The target-scoped classifier ignores
only non-target filter-generated `skipped` rows; it fails closed on missing row
identity, non-target non-`skipped` rows, and target semantic statuses other than
`blocked` or `excluded`.

**Alternatives considered**:

- Run all remediation families in one `run_corpus_remediation` call: rejected
  because the existing runner can continue independent families after one
  failure.
- Copy existing private planning/dispatch helpers: rejected because it would
  duplicate stage logic and risk drift.

## Decision: Keep MCP dry-run default while the Skill supplies explicit confirmation

**Rationale**: Existing side-effect MCP tools default to `confirm=False`. The
new tool retains that contract; the dedicated Skill sends `confirm=True` only
after it recognizes an unambiguous user processing request as the approved
authorization.

**Alternatives considered**:

- Make the MCP default confirmed: rejected because it breaks the project-wide
  dry-run-first boundary.

## Decision: Preserve existing safe report conventions

**Rationale**: The new immutable result and confirmed-only report will contain
only safe identifiers, statuses, counts, paths, warnings, and failure
categories. It will use the runner sanitization patterns already exercised by
015 and 016.

**Alternatives considered**:

- Return raw feed URLs, transcript fragments, or exception text for debugging:
  rejected by the repository secret and evidence-output boundaries.
