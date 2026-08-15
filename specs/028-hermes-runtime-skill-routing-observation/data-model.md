# Data Model

`CapabilityRequirement`, `ObservationState`, `CapabilityVerdict`, `FailureCode`, and `CapabilityMode` are closed `str` enums. `SourceIdentity`, `RequirementObservation`, `SyntheticChecks`, `CapabilityEvaluation`, and `PinnedSourceManifest` are frozen dataclasses.

`RequirementObservation` has only a closed requirement enum, a closed state enum, and an exact Boolean official-source flag. The evaluator accepts no raw runtime event. It validates the exact source identity and the non-duplicated six-requirement set; incomplete observations normalize absent requirements to `missing` and fail closed. The zero-argument pinned loader accepts only the exact top-level key set, exact `hermes-v2026.8.3-source-manifest-v1`, and exact requirement keyset; unknown, missing, or schema drift fields produce no loaded identity or observations.

`build_capability_evidence(...)` emits a fixed safe schema: bounded status strings, Booleans, and only the bounded `missing_requirement_count` integer. Its fixed identity keys are `spec_id`, `runtime_target`, and `release_tag`; its derived `terminal_status` is consistent with the verdict. It rejects forged well-typed `CapabilityEvaluation` cross-field combinations before projection. It emits no source page, hook payload, prompt, argument, result, URL, path input, session, endpoint, or exception text.
