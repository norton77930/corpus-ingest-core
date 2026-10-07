# Developer Handoff: 046

Implemented by Codex after explicit user authorization. See [implementation evidence](implementation-log.md) and completed [tasks](tasks.md). The prompt below is the historical planning handoff; do not restart completed tasks. Preserve all uncommitted044/045/046 changes.

```text
Implement specs/046-workflow-derivation-hardening using Spec Kit.
Read AGENTS.md, docs/agent-handoff.md, spec.md, plan.md,
contracts/derivation-safety.md, tasks.md and quickstart.md.
Set SPECIFY_FEATURE_DIRECTORY=specs/046-workflow-derivation-hardening.
One writer. Follow T001-T026 with focused RED -> minimal GREEN.
Harden Tool25 only: validated identity/paths, refusal of pre-existing recovery,
byte-preserving05/06 publication, explicit transaction states and fixed MCP errors.
Keep26 tools, signatures, success schemas, exact generation acknowledgement,
no-cost reuse and report protocol. Preserve ordinary extra-file bytes.
No Tool26/shared-helper refactor, new dependencies, pipeline, source digest feature,
live provider, .env read, automatic recovery, cache rebuild, branch or commit.
Update only the allowlisted current Skill/docs/oracles; preserve044/045 history.
Run targeted/full checks, separate behavior and engineering review, then converge.
Report exact tests/skips/fault evidence and limits; never call offline oracles live agent proof.
```

Expected delivery: three runtime files plus focused tests/current guidance; implementation-log.md with RED/GREEN and failure-state evidence. Unknown errors never expose raw provider text; published/report failures never trigger regeneration. Read the context/report/path exceptions in the contract before claiming broad path safety.
