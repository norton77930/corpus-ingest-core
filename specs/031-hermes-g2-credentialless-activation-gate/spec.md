# Spec031: Hermes G2 credentialless activation gate

## Scope

G2 is a successor gate to the Spec029/030 static contracts. It has exactly no API key, no credential channel, no provider configuration, and no credential materialization. The package implements offline evidence only; it neither authorizes nor performs a live action.

## Requirements

1. Credential feasibility must be produced only from the repository-pinned source contract. The current manifest does not prove an official plugin-loader route that avoids provider construction; the sole valid feasibility terminal state is `BLOCKED_CREDENTIAL_SEAM`.
2. Observations, eligibility, rollback facts, and receipts must be factory-issued exact classes. Missing, unknown, extra, copied, forged, subclassed, or mutated values fail closed. Unknown state after a live-start indication is quarantined.
3. The sole plan reuses Spec030's ordered operation vocabulary, six tmpfs roles, `ONE_SHOT_STDIN`, and `LogSink.NONE`, while requiring an absent credential channel.
4. A future one-shot attempt requires the exact acknowledgement, a distinct G2 live lease, an atomic fixed marker at `.tmp/spec031-g2/attempt.json`, metadata-only inspection, and G2-owned rollback in `finally`.
5. The fixture probe must never call `plugin.register()` as a substitute for the official loader. Without pinned proof it remains `BLOCKED_CREDENTIAL_SEAM`.

## Non-goals

No Docker/Compose/container/image/network action, Hermes runtime/listener/MCP/Core dispatch/tool call/inference/query/chat/prompt, provider construction, credential/config/session/log access, C6 action, or live result claim is in scope.

## Completion amendment: zero-side-effect credential gate

1. Exact acknowledgement is insufficient: a factory-sealed approval must also attest passed reviews, verified human approval, reviewed revision, fixture identity, and baseline selector. The current repository cannot issue this approval and therefore terminates at `BLOCKED_REVIEW_GATE`.
2. Credential feasibility and all offline gates are evaluated before creating a live lease, claiming a persistent marker, or calling a driver. In the current `BLOCKED_CREDENTIAL_SEAM` state, attempt count is zero, retry count is zero, runtime is `not_run`, and no rollback is required.
3. Runtime-control and rollback observations are closed, exact-class fact sets. They contain only booleans, bounded integers, and fixed enums; they do not accept or retain runtime command, environment, mount, log, session, identifier, or path data.
4. Live-start unknown and failed cleanup have priority over credential blocking: their terminal receipts are quarantined. Cleanup can never change an activation failure to a pass. A ready eligibility type exists only as an unissuable contract seam for later separate approval.
5. Every receipt uses the fixed safe schema and reports blocked runtime controls as `not_run`/`false`/`0`. It contains no free-form errors or identifiers.
6. The scratch fixture is a blocked definition, not an activation-ready fixture: `fixture_build_authorized=false`, `official_loader_verified=false`, and `provider_materialization_status=blocked_unknown`.

Future live lease, driver, metadata inspection, and rollback execution are not implemented by this offline closure.

## Acceptance evidence

Focused observation/runtime/docs tests prove closed facts, zero-side-effect blocked precedence before marker/driver access, safe receipt projections, and static fixture/CLI constraints. H3 runs the static-only offline verifier exactly once; the live runner remains unexecuted.
