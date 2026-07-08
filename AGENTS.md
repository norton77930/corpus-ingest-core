# Repository Agent Instructions

New agents: start with [`docs/agent-handoff.md`](docs/agent-handoff.md) (10-minute repo handoff, boundaries mapped to guard tests) and [`docs/ai-development-framework.md`](docs/ai-development-framework.md) (instruction hierarchy, change classification, completion report format). The Engineering Rules below are hard constraints and remain authoritative.

This repository uses Spec Kit with Codex skills. For new feature work, prefer the Spec Kit flow before implementation:

- `$speckit-constitution` to establish or amend project principles.
- `$speckit-specify` to create or update user-facing requirements.
- `$speckit-clarify` to resolve high-impact ambiguity before planning.
- `$speckit-plan` to create the technical plan.
- `$speckit-checklist` to create feature-specific quality and safety checks.
- `$speckit-tasks` to break the plan into actionable work.
- `$speckit-analyze` to check spec, plan, and tasks for consistency before implementation.
- `$speckit-implement` to execute approved tasks.
- `$speckit-converge` to compare code against spec, plan, and tasks after implementation and add missing work.

Use `$speckit-taskstoissues` only when GitHub issue handoff is needed. The normal full Spec Kit flow is:

```text
constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge
```

<!-- SPECKIT START -->
For the active Corpus Artifact Index feature, read
[`specs/008-corpus-artifact-index/plan.md`](specs/008-corpus-artifact-index/plan.md)
for technologies, project structure, shell commands, and implementation context.
<!-- SPECKIT END -->

## Engineering Rules

- Use Windows PowerShell by default.
- Keep the thin CLI / thick core boundary: scripts parse arguments and call `podcast_ingest_core` functions.
- Use TDD for new behavior and keep changes surgical.
- Side-effect workflows stay dry-run first where practical.
- `.env` is local-only and must not be read, printed, shared, or committed unless the user explicitly asks for a local manual test setup and no secret values are exposed.
- `.env` must not be committed.
- Do not provide buy/sell/hold recommendations, target prices, guaranteed returns, or personalized investment advice.
- Keep the no investment advice boundary.
- Keep external market data bounded: no live market API unless a future approved phase explicitly adds it.
- Do not automatically rebuild SQLite cache after side-effect tools; warn that cache may be stale.

## Verification

Run the relevant targeted tests first, then the standard full checks before claiming completion:

```powershell
python -m pytest
python -m compileall src scripts
```

Per-change-type targeted tests are listed in [`docs/verification-matrix.md`](docs/verification-matrix.md).
