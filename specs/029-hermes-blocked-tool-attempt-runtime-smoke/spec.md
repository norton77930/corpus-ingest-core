# Spec 029 — Hermes v0.19 G0 offline refactor

**Status: v0.19 G0 Offline Refactor; G1 `BLOCKED_CONTROL_PLANE`.** G1 read-only preflight completed with a blocked receipt. G2 and G3a remain unauthorized and were not run.

The package pins Hermes v0.19.0 (2026.7.20) clean source identity, models a
baseline v0.19 disposable overlay, trusted-clock atomic offline lease, and
rollback quarantine, and provides an all-block v0.19 plugin plus a deny-only
MCP low-level adapter. Its S016 projection accepts only strict `confirm=false`
and `action=next`. The only narrow
future S016 claim, if separately approved and evidenced, is: **observed expected high-level MCP tool-call attempt, then policy-blocked before MCP dispatch**. It does not claim internal Skill selection, Skill causality,
fallback use, `019 PreviewOutcome.BLOCKED`, or Core execution.

The manifest records source pre/post hook capability, while the plugin registers
only the pre-tool block hook through exact `register(ctx)` and `register_hook`.
It also requires block-before-execution and callback-exception fail-open facts. Any
missing, extra, or drifted fact fails closed. Safe input, provider, and overlay
seams are unverified, so the terminal source status remains
`BLOCKED_RUNTIME_SEAM` and cannot authorize live activation.

The adapter exposes an immutable snapshot of the existing exact-21 MCP
descriptors for `tools/list`; every `tools/call` is denied and tripwired. It
neither binds a listener nor imports Core dispatch code.
