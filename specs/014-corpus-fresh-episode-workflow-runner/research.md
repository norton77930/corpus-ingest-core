# Research: Corpus Fresh Episode Workflow Runner

## Decision: Build 014 as a thin orchestrator over existing corpus runners

**Rationale**: 013, 012, 011, and 010 already own their side-effect boundaries, report shapes, and safety tests. Reusing them avoids duplicating download, transcription, remediation, and intake logic.

**Alternatives considered**:
- Reimplement artifact state transitions in 014: rejected because it would duplicate existing tested runner logic.
- Shell out to scripts: rejected because the project constitution requires thick core and thin CLI.

## Decision: Support only `stage=next` in v1

**Rationale**: The user goal is to test the latest episode safely. `next` keeps the workflow simple while still preventing accidental full-chain execution.

**Alternatives considered**:
- Explicit stage enum: more control, but more manual decision burden.
- Full-chain one-command execution: rejected because it can download, transcribe, and write downstream artifacts in one confirmation.

## Decision: Confirmed execution attempts one stage and stops

**Rationale**: One-stage confirmation aligns with existing dry-run-first safety patterns and lets the operator inspect each state transition before continuing.

**Alternatives considered**:
- Continue automatically after success: rejected because it weakens auditability and can cause expensive or long-running transcription unexpectedly.

## Decision: Build one private in-memory corpus snapshot for seeded selection

**Rationale**: 008 and 009 already own artifact discovery and action planning, but their public entry points persist outputs. Package-private build/persist boundaries let 014 recompute fresh state once without writing, then reuse the same result and payload for 012, 011, and 010 previews with `source_persisted=False`.

**Implementation boundary**: `_CorpusIndexSnapshot` and `_CorpusRemediationPlanSnapshot` carry existing result metadata, JSON-compatible payload, and Markdown. Their build functions perform no directory creation or file write; existing public generators preserve persistence order and atomic `.part` replacement.

**Alternatives considered**:
- Call public standalone dry-run runners from 014: rejected because they intentionally refresh and persist 008/009.
- Read every artifact family directly in 014: rejected because it would duplicate 008/009 logic and drift from standalone selection.

## Decision: Preserve standalone 010-012 compatibility

**Rationale**: Public 010, 011, and 012 dry-runs continue to persist fresh index/plan state, execute no external side effect, and write no own stage report. Only 014 uses the package-private previews over an unpersisted shared snapshot.

**Alternatives considered**:
- Change every standalone runner to zero-file: rejected because it would break established refresh-and-write behavior outside 014.

## Decision: Workflow report is confirmed-only and deterministic

**Rationale**: Existing corpus side-effect runners write latest reports only after confirmed attempts. 014 additionally treats `confirm=False` as strict zero-file behavior across seed, index, plan, stage, workflow, downstream, and `.part` artifacts.

**Alternatives considered**:
- Write or refresh any dry-run artifact: rejected because 014 must leave the complete tree manifest unchanged.
- No workflow report: rejected because confirmed orchestration needs an audit artifact.

## Decision: Exclude semantic, LLM, stock-lens, MCP, cache rebuild, and batch behavior

**Rationale**: These areas introduce cost, secret, provider, registry, or broad side-effect risk. 014 is intended to unblock latest-episode deterministic testing only.

**Alternatives considered**:
- Add gated semantic stage: deferred to a future feature because it needs API cost acknowledgement and stricter output safety gates.
- Add MCP tool: deferred to a future feature because it changes tool registry contracts.