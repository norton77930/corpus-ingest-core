# Safe Contract Evidence Contract

## Input boundary

`build_contract_evidence(...)` accepts only a `SkillRoute`, `ArtifactValidation`, and `SequenceVerification`. It accepts no raw natural language, source text, raw event data, prompts, responses, arguments, result objects, paths, endpoints, config values, or sessions. Success requires the route Skill, verified sequence Skill, and call budget to bind to the same canonical Skill; a cross-Skill substitution or wrong budget yields bounded invalid evidence.

## Output schema

The stable evidence schema is `hermes-skill-protocol-evidence-v1`:

```json
{"schema_version":"hermes-skill-protocol-evidence-v1","ok":true,"route":"route","skill":"corpus-episode-completion","artifact_ok":true,"managed_allowlist_ok":true,"sequence_ok":true,"failure_code":"none","call_count":2,"hermes_runtime_observation":"not_evaluated"}
```

Only closed enum values, exact booleans, `null` for no Skill, and a capped integer count may occur. Failure uses a bounded code and never an exception message.

## CLI

`validate_hermes_skill_protocol.py` accepts exactly one mode: `contracts` or `synthetic`. `contracts` obtains artifact paths from `MANAGED_SKILLS`, emits `managed_allowlist_ok`, and carries `hermes_runtime_observation="not_evaluated"` both at top level and in each evidence projection. `synthetic` additionally emits `synthetic_protocols_pass`, `unknown_event_fail_closed`, and `non_boolean_fail_closed` after executing its finite positive and hostile bounded projections. Invalid invocation emits fixed keys with `mode="rejected"`, `failure_code="invalid_mode"`, and an empty evidence list. It never echoes argv. Both modes are offline and leave actual Hermes runtime routing `not_evaluated`.