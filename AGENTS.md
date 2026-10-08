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
This repository contains multiple as-built Spec Kit packages and does not pin
one active feature. Before running official scripts or skills, set
`SPECIFY_FEATURE_DIRECTORY` explicitly following [specs/README.md](specs/README.md).
A historical reference such as
[`specs/019-episode-verified-research-report-workflow/plan.md`](specs/019-episode-verified-research-report-workflow/plan.md)
describes completed work only; it is not an active-feature selector.
Current user-authorized work is [SPEC059](specs/059-source-learning-reliability/plan.md):
source learning reliability and note quality; real-host acceptance remains separate.
Select this package explicitly; [SPEC058](specs/058-learning-mcp-acceptance/plan.md)
and earlier packages describe historical work.
Historical source learning entry: [SPEC057 plan](specs/057-source-learning-entry-skill/plan.md).
Historical prepared-source QA: [SPEC056 plan](specs/056-source-content-query/plan.md).
Historical source preparation: [SPEC054 plan](specs/054-source-preparation-jobs/plan.md);
source settings: [SPEC055 plan](specs/055-source-preparation-transcription-settings/plan.md).
These historical references do not select an active feature.
<!-- SPECKIT END -->

## Engineering Rules

- Use Windows PowerShell by default.
- Keep the thin CLI / thick core boundary: scripts parse arguments and call `corpus_ingest_core` functions.
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
