# Data model

No persisted entities or schema migration.

## Conversation checkpoint (host only)

Explicit source IDs; pinned64 version; original action/query/time window; validated page limits; verbatim next_cursor from last successful page (empty before first read); accumulated ordinals/chunks; remaining call/character budgets; recovery_used flag. Current conversation only, never a repository session file.

Transitions: inspected -> reading -> eligible_error -> recovering_inspect -> same_version_retry -> reading. Second error/recovery failure/version or identity drift/malformed reply/budget exhaustion -> stopped_partial. Complete requires all requested chunks without gaps; search is not full-source understanding.

## Query error and notes

Existing reason plus optional finite validation diagnosis in Core exception; wrapper only maps known pairs to fixed messages. No raw parameter/evidence values. Notes preserve source issues/reasoning/concrete examples/replay timestamps, scope/completeness and separate labeled optional AI additions. Unknown gender uses 講者 or confirmed name; user request controls optional sections.