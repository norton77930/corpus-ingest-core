# Data Model: Core Consolidation

No new persisted artifact schemas. New internal seams only:

## path_safety (module)

| Symbol | Kind | Notes |
| --- | --- | --- |
| `URI_SCHEME_PATTERN` | `re.Pattern` | `^[A-Za-z][A-Za-z0-9+.-]*://` (single source) |
| `SAFE_FILENAME_PATTERN` | `re.Pattern` | single source |
| `SAFE_PATH_COMPONENT_PATTERN` | `re.Pattern` | single source |
| `is_safe_local_path_structure(value, *, allow_absolute, require_separator=True)` | fn → bool | shared skeleton; `allow_absolute=True` = A/B/C profile; `allow_absolute=False, require_separator=False` = D profile (017 accepts bare filenames — empirically pinned) |

## run_report_io (module)

| Symbol | Kind | Notes |
| --- | --- | --- |
| `write_part_staged_report_pair(json_path, markdown_path, payload, markdown)` | fn → None | byte-equivalent weak protocol; raises raw `OSError` |

## mcp_runtime / mcp_tools_* (modules)

| Symbol | Kind | Notes |
| --- | --- | --- |
| `mcp_runtime.mcp` | `FastMCP` | the only instance in `src` |
| `mcp_runtime.tool_success / tool_error / tool_action_plan` | fns | envelopes unchanged |
| `mcp_tools_read` | module | Tools 1–6 |
| `mcp_tools_side_effect` | module | Tools 7–12 |
| `mcp_tools_corpus_workflows` | module | Tools 13–16 |
| `mcp_tools_verified_report_queries` | module | Tools 17–21 |
| `mcp_server` | facade | re-exports tools, envelopes, dependency aliases; import order = registration order |

## corpus_episode_completion_workflow_runner (addition)

| Symbol | Kind | Notes |
| --- | --- | --- |
| `confirmed_request_rejection_reason(selector, action, api_cost_ack)` | fn → `str \| None` | canonical rejection messages, single source |

## storage (change)

| Symbol | Change |
| --- | --- |
| `DATA_DIR` | `Path(os.environ.get("PODCAST_INGEST_DATA_DIR") or "data")` — identical default |
