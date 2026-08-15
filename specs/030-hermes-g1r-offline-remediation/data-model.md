# Static Data Model

Closed vocabulary: six `TmpfsRole` values (`RAW_INPUT`, `RAW_OUTPUT`, `SESSION_STATE`, `PROFILE_STATE`, `DATABASE_STATE`, `TEMPORARY_WORK`); ordered `ControllerOperation`; `InputMode.ONE_SHOT_STDIN`; `LogSink.NONE`; and `CredentialBindingKind.READ_ONLY_REFERENCE`.

`G1ROwnerLedger` is a Spec030-owned factory-only opaque identity. Its factory validates a non-empty owner string but does not retain that owner in an object field, repr, or evidence. Plan/reference/assessments share one exact ledger identity; copies, subclass or `__class__` changes, token/field/extra mutation fail closed. It is not a Spec029 ledger or runtime evidence.

`G1RBaselineRollbackIntentFacts` and `G1RRollbackPlanFacts` are independent static intents. `rollback_plan_complete` means only all destruction/revocation intents are supplied; it does not mean a rollback was performed, runtime surfaces were destroyed, or writers may resume. G1R neither emits nor authorizes `writers_may_resume`.

Safe evidence has no owner, values, paths, endpoints, or runtime identifiers. It fixes `runtime_observation_status=not_run`, all credential value read/copy/project/log fields false, and `raw_persisted=false` only with `raw_persisted_scope=safe_evidence_projection_only`.