# Spec 032 proposal

Implement an offline-only, credentialless G2 attempt-executor contract as the immutable successor to Spec031. It adds sealed authority, a factory-issued in-memory single-process ledger, fake-driver, command, and receipt seams without Docker, Hermes, C6, live configuration, filesystem writes, or production ledger actions. Any filesystem ledger is future-only.

Current production source proof is intentionally `BLOCKED_CREDENTIAL_SEAM`. Fake-driver success is only `PASS_OFFLINE_EXECUTOR_CONTRACT`; live activation remains unauthorized.
