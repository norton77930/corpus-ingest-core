# Research: Safe Contract Projection

## Decision

Use `str`-backed closed enums and frozen dataclasses. This makes the assurance input explicit, prevents a natural-language routing API, and makes emitted JSON a finite projection.

## Alternatives rejected

- Parsing a request string: rejected because ambiguity, conflicting instructions, and prompt content cannot be safely turned into runtime authorization.
- Observing raw Hermes hooks/events: rejected because those payloads may contain prompts, arguments, responses, session data, or no canonical fallback indicator.
- Connecting the checker to MCP: rejected because this package proves contract conformance, not a runtime call.

## Boundary

Skill source text is read only in the offline `contracts` mode and is discarded after clause validation. `synthetic` mode creates only bounded enum projections. Neither mode reads `.env`, live config values, session dumps, raw prompt/response/args/results, or protected data.

## Runtime status

The result is `not_evaluated` for actual Hermes routing. C6 remains a Spec 026 direct endpoint-equality claim; this package neither reruns nor amends it.