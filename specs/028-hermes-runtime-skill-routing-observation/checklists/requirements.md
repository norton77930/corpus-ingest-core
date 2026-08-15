# Requirements Checklist

- [x] Manifest identity matches all pinned repository, release, tag, commit, hooks-path, and blob identifiers, with exact top-level/schema/requirement keysets; unknown, missing, or schema drift fails closed.
- [x] Actual manifest has only bounded missing capability states and terminal `blocked_capability`.
- [x] Six-present synthetic coverage yields `PASS_CANONICAL_COVERAGE`.
- [x] Missing, ambiguous, invalid, malformed, non-enum, non-Boolean, and malformed-source inputs fail closed.
- [x] Safe evidence keys are exact and contain no raw material; fixed identity/terminal keys and bounded missing count are present, and forged well-typed cross-field evaluations become `INVALID_EVIDENCE` with `ok=false`.
- [x] CLI accepts only `capability` and `synthetic`; invalid argv is never echoed.
