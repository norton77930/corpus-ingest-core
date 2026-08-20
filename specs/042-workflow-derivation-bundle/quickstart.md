# Quickstart: Workflow Derivation Bundle

## Prerequisites

- Spec 038 lecture available for a `learning-notes` episode
- `config/operator_workflow.yaml` with a non-empty `allowed_tools` list

## Dry-run

```powershell
python scripts/run_workflow_derivation.py --podcast-id x-raytar --episode-ref 2071290493581840707
```

Expect metadata-only JSON, `confirmed=false`, zero new files.

## Confirm (after accepting the plan and the exact ack)

```powershell
python scripts/run_workflow_derivation.py --podcast-id x-raytar --episode-ref 2071290493581840707 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

Note: the ack string is the existing exact constant. This runner still must not send transcript text; it sends lecture Markdown plus operator context.

## Verify

```powershell
python -m pytest tests/test_workflow_derivation.py tests/test_workflow_derivation_profiles.py tests/test_corpus_index.py tests/test_mcp_tool_registry_contract.py tests/test_cache_rebuild_guard.py -q
python -m compileall src scripts
```

Expect: Copilot-omitted context produces no Copilot advice; finance profile refused; registry still 24; lecture four unchanged.
