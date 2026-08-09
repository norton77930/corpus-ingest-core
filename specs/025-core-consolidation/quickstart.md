# Quickstart: Core Consolidation

Nothing operator-facing changes. Maintainer touchpoints after the epic:

```powershell
# add a new MCP tool (Tool 22 playbook):
#   1. implement in the matching mcp_tools_* group module
#   2. append its name to the facade re-export list in mcp_server.py
#   3. deliberately update tests/test_mcp_tool_registry_contract.py (count/order/signature)
#   4. docs count claims: current-marked lines auto-checked against the live registry

# new tests: use the shared fixture instead of copying _use_tmp_data_dirs
#   def test_x(tmp_data_dirs): ...

# optional data-root override (inert when unset):
$env:PODCAST_INGEST_DATA_DIR = "D:\\alt-data-root"
```

Guard tests that lock the consolidation: `tests/test_path_safety_boundary.py`, `tests/test_run_report_io_boundary.py`, `tests/test_mcp_server_facade_boundary.py`, `tests/test_docs_registry_count_consistency.py`, `tests/test_data_dir_fixture_contract.py`.
