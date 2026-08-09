# Contract: Core Consolidation Internal Boundaries

## path_safety

```text
is_safe_local_path_structure(value: object, *, allow_absolute: bool) -> bool
```

- Only module allowed to define the structural regex constants.
- Runner `_is_safe_local_path` wrappers keep their names and per-module round-trip conjuncts.

## run_report_io

```text
write_part_staged_report_pair(json_path: Path, markdown_path: Path, payload: dict, markdown: str) -> None
```

- Byte-equivalent to the historical weak protocol; raises raw `OSError`; callers map exceptions.
- Only legitimate `.part` report-path constructors: this module (+ `downloader.py` for audio).

## MCP facade

- `mcp_runtime` owns the single `FastMCP` instance and the response envelopes.
- Registration order = facade import order: `mcp_tools_read` → `mcp_tools_side_effect` → `mcp_tools_corpus_workflows` → `mcp_tools_verified_report_queries`.
- `mcp_server` re-exports: `run`, envelopes, all 21 tool functions, and every dependency-module alias tests patch through.
- Group modules import `mcp_runtime` only; importing `mcp_server` from them is banned.

## completion rejection reasons

```text
confirmed_request_rejection_reason(selector, action, api_cost_ack) -> str | None
```

- Canonical messages: "confirmed action must be explicit" / "confirmed episode_ref must be canonical" / "semantic_summary requires exact api_cost_ack" — defined once in core; MCP normalizes then delegates; CLI imports the constants.

## docs count claims

- Governed set: `README.md`, `docs/*.md`, `specs/README.md`.
- Current-marked claims must equal live-registry N; historical-marked exempt; unmarked claims fail the suite.
