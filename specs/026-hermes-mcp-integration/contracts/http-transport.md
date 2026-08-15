# Contract: Streamable HTTP Transport

```text
StreamableHttpConfig(host="127.0.0.1", port=8767, path="/mcp")
run_streamable_http(config) -> None
```

- Uses the existing `mcp_runtime.mcp` object; no second `FastMCP` construction.
- `mcp_runtime.run()` remains stdio and unchanged.
- Only `streamable-http`; SSE is forbidden.
- Host must be loopback, path must be `/mcp`, port must be a valid explicitly configured integer.
- Transport security remains enabled; no private SDK member access.
- Direct readiness contract: initialize, exact ordered tools/list, one read-only call, one `confirm=false` call.
