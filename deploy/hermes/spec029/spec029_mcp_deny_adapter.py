"""Spec029 deny-only MCP low-level transport surface; it binds nothing."""
from __future__ import annotations

import json
from pathlib import Path
import threading

from mcp import types
from mcp.server.lowlevel import Server


_SNAPSHOT = Path(__file__).with_name("contracts") / "mcp-tool-descriptor-snapshot.json"
_LOCK = threading.Lock()
_TRIPWIRE_COUNT = 0


def _descriptor_json() -> tuple[str, ...]:
    """Load one immutable, exact-22 descriptor snapshot or refuse import."""
    try:
        raw = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError("Spec029 descriptor snapshot unavailable") from error
    if (
        not isinstance(raw, dict)
        or set(raw) != {"schema_version", "tools"}
        or raw.get("schema_version") != "spec029-mcp-tool-descriptor-snapshot-v1"
        or not isinstance(raw["tools"], list)
        or len(raw["tools"]) != 22
        or not all(isinstance(item, dict) for item in raw["tools"])
    ):
        raise RuntimeError("Spec029 descriptor snapshot invalid")
    descriptors = tuple(json.dumps(item, sort_keys=True, separators=(",", ":")) for item in raw["tools"])
    tools = tuple(types.Tool.model_validate_json(item) for item in descriptors)
    if len({tool.name for tool in tools}) != 22:
        raise RuntimeError("Spec029 descriptor snapshot invalid")
    return descriptors


_DESCRIPTOR_JSON = _descriptor_json()
server = Server("spec029-deny-adapter", version="0.19.0")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Return fresh models recreated only from the immutable snapshot."""
    return [types.Tool.model_validate_json(item) for item in _DESCRIPTOR_JSON]


async def deny_tool_call(_tool_name: object, _args: object) -> types.CallToolResult:
    """Deny every call without examining or retaining call material."""
    global _TRIPWIRE_COUNT
    with _LOCK:
        _TRIPWIRE_COUNT = min(_TRIPWIRE_COUNT + 1, 2)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="SPEC029_POLICY_DENIED")],
        isError=True,
    )


@server.call_tool(validate_input=False)
async def _call_tool(tool_name: str, args: dict[str, object]) -> types.CallToolResult:
    return await deny_tool_call(tool_name, args)


def tripwire_count() -> int:
    """Return the bounded in-memory call count for offline assertions."""
    with _LOCK:
        return _TRIPWIRE_COUNT
