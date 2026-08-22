# Safety Checklist: Workflow Derivation MCP

- [ ] Preview zero-write and zero-network
- [ ] Exact `api_cost_ack` forwarded to Core's gate, never re-implemented or defaulted
- [ ] No provider / model / endpoint / credential parameter on the MCP surface
- [ ] No `workflow_context` override — the file reaches an LLM prompt
- [ ] Response carries paths and counts, never derived body text or prompts
- [ ] No `.env` / cache rebuild / live market API / advice
- [ ] No Hermes live
