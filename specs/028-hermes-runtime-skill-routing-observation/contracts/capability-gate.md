# Capability Gate Contract

The internal manifest loader has no path, URL, endpoint, configuration, or session override. It accepts only the exact top-level key set, exact `hermes-v2026.8.3-source-manifest-v1`, and exact six-key requirement object; unknown, missing, or schema drift fails closed before source identity or observations are loaded. `evaluate_hermes_capability(observations, source_identity)` is total over arbitrary inputs and returns only bounded verdict/failure combinations.

The six required capability observations are canonical Skill identity, Skill-to-tool linkage, fallback used, fallback not-used, guaranteed Skill/tool correlation, and official no-side-effect positive control. All six must be `present` with exact `official_source=True` to yield `PASS_CANONICAL_COVERAGE`. Missing or ambiguous observations yield `BLOCKED_CAPABILITY`; invalid state, malformed observation, non-enum, non-Boolean, duplicate, or malformed source identity yields invalid evidence.

The actual manifest is terminal `blocked_capability`. A valid blocked result completes the gate but never authorizes a live action. Any future work involving Hermes upgrade, Skill sync, hooks/plugin/collector, Docker/MCP/network, live config/session access, inference, or runtime observation must establish and receive separate approval for a new R2 successor spec; Spec 028 does not automatically authorize it.
