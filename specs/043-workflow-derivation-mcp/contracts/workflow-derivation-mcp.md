# Contract: derive_workflow_bundle (Tool 25)

```text
derive_workflow_bundle(
    podcast_id: str,
    episode_ref: str,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
) -> dict
```

No other parameter is accepted. `provider`, `model`, `base_url`, `api_key_env`,
`reasoning_effort`, and `read_timeout_seconds` name the operator's credentials and
endpoints; `workflow_context` names a file whose contents reach an LLM prompt.
Core takes all seven, and this surface deliberately takes none of them.

**Preview** (`confirm=false`): standard `tool_action_plan` plus `run_mode=preview`,
`network_read=false`, `not_investment_advice=true`. Plans reads, writes, and
reuses. Constructs no provider, so it needs no `api_cost_ack` and makes no
network call. Zero writes.

**Confirm** (`confirm=true`): `{"ok": true, "data": ...}` from Core
`WorkflowDerivationResult`, carrying paths, `reused`, and warnings — never the
derived body text or the prompt.

`api_cost_ack` is forwarded verbatim. Core gates it in
`llm_provider.require_exact_api_cost_ack`, and only on the path that actually calls
a provider: confirming a complete existing pair without `force` reuses the files and
needs no ack. The tool adds no check of its own.

**Errors**: `{"ok": false, "error_type": "...", "message": "..."}` — for a wrong or
missing `api_cost_ack`, a `summary_profile` that is not `learning-notes`, a missing
lecture, a missing workflow-context file, or an incomplete pair without `force`.
