# Design decisions

Status: Approved design implemented locally; local verification complete and actual operator/real-host acceptance pending.

## Compact continuation

**Decision**: Versioned stateless 57-character cursor; preserve full version/scope binding and character offset, with an integrity digest covering positions. Accept legacy cursors under existing checks.

**Rationale**: Current Core serializes a 64-hex binding plus positions as JSON/Base64, producing about96-99 characters in the synthetic reproduction. Deleting a substring gives invalid_cursor; repeating it fails again, while copying the successful response's original succeeds. A compact binary representation reduces model-copy burden. Protecting positions detects a typo that would otherwise be a different valid in-range continuation.

**Alternatives**: Ordinal-only continuation loses partial-text offsets and is not inherently action/query/window bound. Opaque server handles need session persistence or lifecycle management. Full machine-managed reading could remove model copying but adds an orchestrator beyond this repair scope. Shortening source_version or truncating digest strength is rejected.

## Discovery and local entry

**Decision**: Normalize all repository Skill descriptions to at most60 characters; entry purpose/local priority must remain visible. Only descriptions change for unrelated workflows.

**Rationale**: The repository has23 current Skills with descriptions longer than60; entry is294 characters and its local direction is late. Hermes's [official extraction](https://github.com/NousResearch/hermes-agent/blob/main/agent/skill_utils.py) uses the first57 characters plus an ellipsis for overlong descriptions. Tests must reproduce that host seam. Full-file keyword checks did not cover discovery truncation.

**Alternatives**: Editing Hermes configuration/provider is excluded. Adding more rules after the truncated text does not improve discovery. Repository descriptions improve selection but cannot enforce arbitrary host tool choices.

## Foreground evidence and accurate progress

**Decision**: No delegate_task/background AI for source-learning evidence retrieval; preserve existing server-managed preparation jobs and approvals.

**Rationale**: Entry already says no background AI continuation but lacks explicit delegation prohibition across main Skills. Hermes has an [ACP background-delivery issue](https://github.com/NousResearch/hermes-agent/issues/62548); it supports the reported failure class, not a universal claim about every installed Hermes revision. Main-conversation reading avoids dependence on that delivery rail. Recorded job acceptance remains distinguishable from active/completed notes.

**Alternatives**: Repairing Hermes ACP or disabling delegation host-wide would materially expand scope and affect unrelated work. No such host changes are planned.

## Grounded answer quality

**Decision**: Strengthen visible evidence-before-answer rules, concrete neutral-speaker examples and pre-answer checks of source examples, while retaining one conditional notes template.

**Rationale**: SPEC059 already forbids gender inference, dropped key examples and mixed AI additions. The new report indicates host noncompliance, not absent original requirements. Explicit concept-question applicability and short actionable checks improve instruction clarity. String guards establish instructions exist; they do not establish real model compliance.

**Alternatives**: A new notes generator/provider or rigid template for every short answer is unnecessary and outside scope. Never fabricate source examples to satisfy a template.

## Verification boundary

**Decision**: Separate planning checks, deterministic runtime/SDK tests and actual Hermes observation. Default-budget full-source verification also checks selected/delivered counts equal inspected source count.

**Rationale**: scope_complete=true only proves delivery of the requested selection. Inventory reports resource availability, not host loading. The current verifier already supports an explicit range and120000 characters; no new CLI mode, retry rule or budget default is needed. An upper bound strictly beyond inspect end_seconds includes final zero-duration segments.

**Alternatives**: Declaring model correctness after pytest, or publishing host/session/source logs in the open-source repository, is rejected. Missing host/data access remains a disclosed operator acceptance dependency.
