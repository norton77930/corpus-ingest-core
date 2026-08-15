# Spec033 Proposal

Acquire only the fixed 17-file public source allowlist from `NousResearch/hermes-agent` commit `b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6`, then audit those bytes statically. No Hermes import, execution, configuration, credential, network listener, provider, or inference action is within scope.

Current terminal state is `SPEC033_PINNED_SOURCE_AUDIT_IMPLEMENTED` plus `BLOCKED_SOURCE_GRAPH`; `runtime_status=not_run` and `live_actions_authorized=false`.
