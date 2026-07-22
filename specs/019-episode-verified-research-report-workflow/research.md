# Research: Episode Verified Research Report Workflow

## Decision 1 — Separate entrypoint vs overload 018

- **Decision**: New Core function + MCP tool 16.
- **Rationale**: 018 encodes latest pin, ack, and optional upstream stages; overloading would regress the fifteenth tool contract and Skill protocol.
- **Alternatives**: Extend 018 with mode flags — rejected (contract complexity, agent confusion).

## Decision 2 — Assemble-only vs run missing stages

- **Decision**: Assemble/publish only when local artifacts + lineage already pass.
- **Rationale**: Grilling lock; keeps 019 out of cost/network; 015–017 remain the stage tools.
- **Alternatives**: Semantic+research on confirm — deferred; full ladder — out of scope.

## Decision 3 — Acknowledgement

- **Decision**: No `api_cost_ack`.
- **Rationale**: No provider construction; ack is a cost boundary, not a general approval token (episode approval is explicit `episode_ref` + `confirm=True`).
- **Alternatives**: Always require ack for UX parity with 018 — rejected as misleading.

## Decision 4 — Episode resolution

- **Decision**: Explicit `episode_ref` only; local artifacts; no RSS.
- **Rationale**: Historical reports must be reproducible offline; latest remains 018.
- **Alternatives**: RSS identity check — deferred (network flaky, unnecessary for assemble-only).

## Decision 5 — Reuse 018 assembly stack

- **Decision**: Call existing assembler/publisher/lineage without forking payload schema.
- **Rationale**: Same user-visible report; less drift; 018 already episode-scoped at assembly layer.
- **Alternatives**: New report schema — rejected for v1.

## Decision 6 — Blocked UX

- **Decision**: Metadata inventory of missing/stale roles and gates only.
- **Rationale**: Actionable without implying automatic chaining or investment guidance.
- **Alternatives**: Suggest next Skill/tool names — deferred (v2 candidate).

## Decision 7 — Registry size

- **Decision**: Exactly 16 reviewed tools after 019.
- **Rationale**: Append-only pattern from 016→017→018.
- **Alternatives**: CLI-only — rejected by product surface decision.
