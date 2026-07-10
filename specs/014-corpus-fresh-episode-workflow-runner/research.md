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

## Decision: Derive stage choice from existing dry-run outputs and local metadata

**Rationale**: Existing runners already refresh the needed corpus index/remediation state. The workflow runner can call their dry-run modes to choose a stage and then call only the selected runner with confirmation.

**Alternatives considered**:
- Read every artifact family directly: rejected because it would duplicate 008/009 logic.

## Decision: Workflow report is confirmed-only and deterministic

**Rationale**: Existing corpus side-effect runners write latest reports only after confirmed attempts. Keeping the same rule preserves dry-run no-write behavior.

**Alternatives considered**:
- Write dry-run reports: rejected because dry-run no-write is a project norm.
- No workflow report: rejected because confirmed orchestration needs an audit artifact.

## Decision: Exclude semantic, LLM, stock-lens, MCP, cache rebuild, and batch behavior

**Rationale**: These areas introduce cost, secret, provider, registry, or broad side-effect risk. 014 is intended to unblock latest-episode deterministic testing only.

**Alternatives considered**:
- Add gated semantic stage: deferred to a future feature because it needs API cost acknowledgement and stricter output safety gates.
- Add MCP tool: deferred to a future feature because it changes tool registry contracts.