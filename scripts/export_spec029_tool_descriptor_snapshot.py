"""Export the sole FastMCP registry's read-only Spec029 descriptor snapshot."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from podcast_ingest_core import mcp_server


OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "deploy"
    / "hermes"
    / "spec029"
    / "contracts"
    / "mcp-tool-descriptor-snapshot.json"
)


def build_snapshot() -> dict[str, object]:
    """Read the one existing registry; never invoke a tool or start transport."""
    tools = asyncio.run(mcp_server.mcp.list_tools())
    return {
        "schema_version": "spec029-mcp-tool-descriptor-snapshot-v1",
        "tools": [tool.model_dump(mode="json", exclude_none=True) for tool in tools],
    }


def main() -> int:
    snapshot = build_snapshot()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # newline="" so the bytes are LF on every platform. This file is -text
    # pinned and its SHA-256 is published in docs/install-and-porting.md, so a
    # Windows text-mode default would silently change the digest and make the
    # artifact platform-dependent -- exactly what it exists not to be.
    with open(OUTPUT, "w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
