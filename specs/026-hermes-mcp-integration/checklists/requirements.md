# Specification Quality Checklist: Hermes MCP Integration

**Created**: 2026-08-09  
**Feature**: [spec.md](../spec.md)

- [x] R2 cross-repo/runtime scope and exact prohibited surfaces are explicit.
- [x] Single FastMCP, stdio, and 21-tool freeze are testable requirements.
- [x] Network topology is fixed to host-network plus loopback; no SSE/port publication.
- [x] Config merge and Skill sync define no-op, backup, pre-mutation manifest, recoverable staged replacement, redaction, collision, and digest-verified rollback; uninterrupted atomic directory exchange is not claimed.
- [x] Spec 017 Skill exception is recorded without changing its contract.
- [x] Live smoke distinguishes direct protocol evidence, bounded inference, protected-surface before/after endpoint equality, and normal Hermes state writes; it does not claim the absence of transient mutation between snapshots.
- [x] Migration/upgrade/rollback and absence of artifact schema migration are explicit.
- [x] Out-of-scope items prevent market/advice/Discord/multi-source/provider-secret expansion.
