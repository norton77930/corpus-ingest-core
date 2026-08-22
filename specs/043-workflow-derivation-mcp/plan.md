# Implementation Plan: Workflow Derivation MCP Tool

**Branch**: `043-workflow-derivation-mcp` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

## Summary

Append Tool 25 `derive_workflow_bundle`, a thin wrapper over Spec 042's
`run_workflow_derivation`. Preview plans paths and writes nothing. Confirm
forwards the operator's `api_cost_ack` to Core's gate and writes the `05`/`06`
pair plus a metadata-only report. Registry 24 → 25.

## Constitution Check

No amendment. Thin MCP, confirm-gated preview, exact `api_cost_ack` unchanged,
no `.env`, no live market API, no auto cache rebuild, no investment advice.

## Design Decisions

1. Last-imported `mcp_tools_workflow_derivation.py`, so Tools 1–24 keep their slots.
2. **Not** the Spec 040/041 envelope. Those tools resolve public video metadata and
   therefore declare `network_read=true`; preview here returns before constructing a
   provider, so it declares `network_read=false`. Copying 041 verbatim would state
   the opposite of what the code does.
3. Provider plumbing stays off the MCP surface: no `provider`, `model`, `base_url`,
   `api_key_env`, `reasoning_effort`, or `read_timeout_seconds`. Same reasoning as
   Spec 041 FR-011 — these name credentials and endpoints owned by the operator.
4. `workflow_context` stays off the MCP surface too, and this one is a boundary
   rather than a tidiness choice: Core reads that file and folds it into an LLM
   prompt, so an agent-supplied path would make Tool 25 a read-any-file-and-send-it
   primitive. The tool always uses `DEFAULT_CONTEXT_PATH`.
5. The ack gate is not re-implemented. `run_workflow_derivation` calls
   `llm_provider.require_exact_api_cost_ack` on the confirm path, and only when it
   is actually going to call a provider — a confirmed reuse legitimately needs no
   ack. The tool forwards the value and adds no check of its own, so the two can
   never drift apart.
6. No model change. `WorkflowDerivationResult` already carries `run_mode`,
   `not_investment_advice`, and both report paths, unlike Spec 041's Tool 24 which
   had to extend its result first.
7. Descriptor snapshot regenerated with the official script, as Specs 035, 040, and
   041 each did.

## Files

```text
src/podcast_ingest_core/mcp_tools_workflow_derivation.py   (new, imported last)
src/podcast_ingest_core/mcp_server.py                      (facade wiring)
src/podcast_ingest_core/hermes_skill_protocol.py           (AST source list + size)
deploy/hermes/spec029/spec029_mcp_deny_adapter.py          (exact-24 -> exact-25)
deploy/hermes/spec029/contracts/mcp-tool-descriptor-snapshot.json  (regenerated)
scripts/validate_mcp_setup.py                              (registry check)
tests/test_mcp_workflow_derivation.py                      (new)
tests/  (count assertions: registry contract, server, setup validation,
        docs consistency, hermes skill protocol, hermes live smoke, spec029 offline)
docs/api.md, docs/mcp-usage.md, README.md, README.zh-TW.md,
docs/agent-handoff.md, docs/ai-development-framework.md,
specs/README.md, docs/roadmap.md
```

## Verification

```powershell
python -m pytest tests/test_mcp_workflow_derivation.py tests/test_workflow_derivation.py tests/test_mcp_tool_registry_contract.py tests/test_docs_registry_count_consistency.py tests/test_mcp_server_facade_boundary.py tests/test_llm_ack_guard_contracts.py -q
python -m pytest
python -m compileall src scripts
```
