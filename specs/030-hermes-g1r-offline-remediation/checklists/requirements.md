# Requirements Checklist

- [x] static closed operations, six tmpfs roles, input/log/binding enums, and exact bool/int controls.
- [x] Spec030-owned opaque `G1ROwnerLedger` shares one exact sealed identity with plan/reference/assessments; it is not Spec029/runtime evidence.
- [x] independent `G1RBaselineRollbackIntentFacts` plus `G1RRollbackPlanFacts` express only destruction/revocation intents.
- [x] `rollback_plan_complete` is static intent completeness only; it does not claim performed rollback, destroyed runtime surfaces, or writers resume. No `writers_may_resume` output/authorization exists.
- [x] exact PASS_OFFLINE_REMEDIATION safe receipt; runtime observation stays not_run.
- [x] G2/G3a/live actions remain false; Docker/Hermes/network/inference/C6 excluded.
