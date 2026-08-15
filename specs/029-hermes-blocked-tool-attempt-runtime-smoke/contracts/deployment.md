# Baseline v0.19 disposable-overlay deployment contract

G0 models an immutable baseline v0.19 image and a disposable isolated overlay;
it has no image replacement, Docker command, listener, or activation function.
A factory-issued offline controller lease is opaque, owner-bound, TTL-limited,
and one-use; it cannot authorize live activation. The module-private monotonic
clock supplies time, no caller supplies it, and issue/consume state transitions
are lock-atomic so only one concurrent consume can succeed. Expiry irrevocably
revokes the lease even if a later clock value moves backward. Forgery, owner
mismatch, replay, malformed evidence, and all unverified runtime seams fail
closed.

Safe input, provider, and overlay runtime seams remain unverified, therefore
preflight always fixes `activation_authorized=false` and terminates at
`BLOCKED_RUNTIME_SEAM` even when offline controller facts are complete.

Rollback requires every exact restoration fact: overlay deactivated and
removed, baseline retained, controls restored, and offline controller lease
revoked. Any missing
or non-true fact returns `FAILED_QUARANTINED`, with
`writers_may_resume=false`. No Docker command is executed.
