# G1 read-only live preflight receipt

The separately approved v0.19 G1 read-only preflight completed without stopping,
restarting, creating, or reconfiguring a container; binding a listener; or
running Hermes inference. It did not inspect `.env`, container environment,
credential-bearing configuration, sessions, prompts, provider values, mount
source paths, or private endpoints.

The bounded machine-readable receipt is
`contracts/g1-read-only-preflight-receipt.json`. Its terminal status is
`BLOCKED_CONTROL_PLANE`, with `activation_authorized=false`.

## Established facts

- The baseline v0.19 runtime remains running from the previously pinned immutable
  image identity.
- The existing MCP sidecar remains running and healthy.
- The pinned clean source commit and hook contract remain `PASS-current`; no
  relevant runtime bytes were changed after that inspection.
- The offline deny adapter remains exact-21 and non-forwarding by G0 evidence,
  but no live listener or placement was activated.

## Unresolved controls

- The normal single-query CLI accepts the query through `-q` / `--query`, which
  places raw input in argv and is not an approved input seam.
- The stdin JSON gateway is a possible non-argv route, but its source creates a
  session/profile database and emits conversation material. A no-durable-write,
  no-log, fresh-session confinement has not been demonstrated.
- No opaque provider binding was identified that can be reused by a disposable
  sibling without reading, copying, or exposing credential-bearing values.
- A disposable sibling, isolated network, read-only plugin mount, tmpfs layout,
  exact effective tool surface, and rollback recipe were not created or proven
  by this read-only gate.
- External launcher/scheduler/writer ownership remains unresolved beyond the
  observed container restart policy.

In the receipt, a `false` field means that the corresponding live property was
not established; it does not assert the opposite property. Independently, the
source contract remains `BLOCKED_RUNTIME_SEAM` because safe input, provider, and
overlay runtime seams are still unverified.

G2 activation and G3a S016 remain unauthorized and were not run.
