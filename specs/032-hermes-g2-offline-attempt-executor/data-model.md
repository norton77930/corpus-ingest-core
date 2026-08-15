# Data model

- `Spec032GateDecision`: sealed gate status and zero-side-effect counters.
- `Spec032OfflineApproval`: sealed offline scope only; no public identity fields.
- `Spec032AttemptLease`: sealed single-use, trusted-monotonic lease bound by exact identity to its offline approval and scope; abnormal/rollback clock observation permanently revokes it.
- `AttemptLedger`: sealed, factory-issued in-memory ledger. Its lock-protected state is single-process only: claim is absent-only, a pending second claim is indeterminate-quarantined, a terminalized claim is replay-blocked, and only one terminalization wins. It accepts no path, storage, or filesystem capability, creates no files, and has no production ledger factory. A durable/filesystem or cross-process ledger is future-only.
- `OfflineSyntheticDriver`: exact-class, factory-issued offline driver whose inspect observation is the bounded metadata parser result, not an exit code or generic boolean.
- `Spec032ActualResult`: sealed terminal outcome, rollback status, and ledger-terminalization fact projected verbatim to a safe receipt.

No model projects identifiers, paths, commands, environment, credentials, raw output, errors, timestamps, or host data. The current production terminal is `BLOCKED_CREDENTIAL_SEAM`.
