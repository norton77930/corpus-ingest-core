# v0.19 G0 offline plan

G0 pins the Hermes v0.19.0 source contract, derives an exact-21 read-only MCP
descriptor snapshot from the sole FastMCP registry, and supplies pure baseline
v0.19 disposable-overlay, lease, rollback, plugin, and deny-adapter models.
Every model is fail-closed and has no Docker, listener, inference, or live
activation transition. The separately approved G1 read-only preflight completed
as `BLOCKED_CONTROL_PLANE`; G2/G3a remain unauthorized. Only a future S016 narrow
policy-block claim is in scope for later work.
