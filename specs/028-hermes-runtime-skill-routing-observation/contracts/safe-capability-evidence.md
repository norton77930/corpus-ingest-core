# Safe Capability Evidence Contract

`build_capability_evidence(...)` has a fixed safe schema with a schema version, `spec_id`, derived `terminal_status`, fixed `runtime_target`, fixed `release_tag`, bounded `missing_requirement_count` integer (`0..6`), gate completion Boolean, bounded mode/verdict/failure, source-identity Boolean, coverage Boolean, six named requirement states, fixed no-live-action fields, C6 status, and fixed synthetic-check Booleans.

`terminal_status` is derived only from the bounded verdict (`pass_canonical_coverage`, `blocked_capability`, or `invalid_evidence`), so it cannot contradict `verdict`. The evidence must always state `live_actions_authorized=false`, `hermes_runtime_observation=not_run`, and `c6_status=pass_current_not_rerun`. `ok=true` for `BLOCKED_CAPABILITY` says only that the gate terminated correctly. It is not a runtime pass, observation, or authorization.

The builder rejects forged well-typed cross-field combinations. PASS requires verified source, complete coverage, six `present` states, and failure `none`; synthetic PASS additionally requires every synthetic check. BLOCKED requires verified source, incomplete coverage, only present, missing, or ambiguous states with at least one missing or ambiguous state, and failure `blocked_capability`. INVALID and rejected modes require consistent bounded invalid failures and invalid states. Any contradiction is projected as `INVALID_EVIDENCE` with `ok=false`.

No raw official page, hook payload, example prompt, arguments or results, caller argv, URL, source text, session, endpoint, configuration value, or exception can enter this schema.
