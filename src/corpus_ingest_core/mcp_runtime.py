"""MCP server runtime: the single FastMCP instance and shared envelopes.

specs/025-core-consolidation FR-005: this module owns the only ``FastMCP``
construction in ``src`` plus the response envelopes and generic helpers shared
by every tool group. Tool functions live in the ``mcp_tools_*`` group modules,
which register on import; ``mcp_server`` (the facade) imports the groups in
registration order and re-exports the public surface.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import semantic_summarizer
from .errors import PodcastIngestCoreError, SearchError
from .local_env_names import MCP_PORT_ENV, read_env
from .serialization import to_jsonable

MAX_LIMIT = 50
MAX_CONTEXT_SEGMENTS = 5
SEMANTIC_API_COST_ACK = semantic_summarizer.SEMANTIC_API_COST_ACK

mcp = FastMCP("corpus-ingest-core")


DEFAULT_STREAMABLE_HTTP_PORT = 8767


def _port_from_env() -> int:
    raw = (read_env(MCP_PORT_ENV) or "").strip()
    if not raw:
        return DEFAULT_STREAMABLE_HTTP_PORT
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{MCP_PORT_ENV} must be an integer") from exc


@dataclass(frozen=True)
class StreamableHttpConfig:
    """Loopback-only Streamable HTTP listener configuration.

    Host and path are fixed, not defaults. This transport exposes every
    side-effect tool in the registry, so binding it anywhere but the loopback
    interface would put a download/transcribe/spend surface on the network. The
    constraint originally came from spec 026's sidecar deployment, which has
    since been archived; it stays because the reason for it never depended on
    that deployment. Invalid values fail before the shared server settings are
    touched. Widening it should be an explicit, reviewed opt-in, not a default.

    The port is the one part that legitimately varies, so it reads
    ``CORPUS_INGEST_MCP_PORT`` when nothing is passed. Without that the
    installed ``corpus-ingest-mcp-http`` command would ignore a variable that
    ``scripts/run_mcp_http_server.py`` honours -- the same setting behaving
    differently depending on how you started the server.
    """

    host: str = "127.0.0.1"
    port: int = field(default_factory=lambda: _port_from_env())
    path: str = "/mcp"

    def __post_init__(self) -> None:
        if self.host != "127.0.0.1":
            raise ValueError("host must be 127.0.0.1")
        if self.path != "/mcp":
            raise ValueError("path must be /mcp")
        if type(self.port) is not int:
            raise ValueError("port must be an integer")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")


def tool_success(data: Any, warnings: list[str] | None = None) -> dict[str, Any]:
    """回傳 MCP tool 成功 envelope。"""

    response = {"ok": True, "data": to_jsonable(data)}
    if warnings:
        response["warnings"] = warnings
    return response


def tool_error(message: str, error_type: str | None = None) -> dict[str, Any]:
    """回傳 MCP tool 錯誤 envelope，不暴露 traceback。"""

    return {
        "ok": False,
        "error_type": error_type,
        "message": message,
    }


def tool_action_plan(
    *,
    tool_name: str,
    action: str,
    inputs: dict[str, Any],
    writes: list[str],
    risks: list[str],
    requires_confirmation: bool = True,
) -> dict[str, Any]:
    """回傳 side-effect tool 的 dry-run action plan。"""

    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": requires_confirmation,
        "tool": tool_name,
        "action": action,
        "inputs": to_jsonable(inputs),
        "writes": writes,
        "risks": risks,
        "next_step": "Call this tool again with confirm=true to execute.",
    }


def run() -> None:
    """以 FastMCP 預設 stdio transport 啟動 server。"""

    mcp.run()


def run_streamable_http(config: StreamableHttpConfig | None = None) -> None:
    """以核准的 loopback Streamable HTTP transport 啟動同一個 server。"""

    resolved = config or StreamableHttpConfig()
    mcp.settings.host = resolved.host
    mcp.settings.port = resolved.port
    mcp.settings.streamable_http_path = resolved.path
    mcp.run(transport="streamable-http")


def _tool_call(operation: Callable[[], Any], warnings: list[str] | None = None) -> dict[str, Any]:
    try:
        return tool_success(operation(), warnings=warnings)
    except PodcastIngestCoreError as exc:
        return tool_error(_safe_error_message(exc), type(exc).__name__)
    except ValueError as exc:
        return tool_error(str(exc), "ValueError")
    except Exception as exc:
        return tool_error(str(exc), type(exc).__name__)


def _safe_error_message(exc: PodcastIngestCoreError) -> str:
    message = str(exc)
    if isinstance(exc, SearchError) and "SQLite cache 不存在" in message and "rebuild_cache" not in message:
        return f"{message}。請先執行 rebuild_cache maintenance tool。"
    return message


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _clamp_context_segments(context_segments: int) -> int:
    return max(0, min(int(context_segments), MAX_CONTEXT_SEGMENTS))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(value), maximum))


def _redact_text(message: str, sensitive_value: str | None) -> str:
    if sensitive_value:
        return message.replace(sensitive_value, "[redacted-base-url]")
    return message


def _redact_many(message: str, sensitive_values: list[str | None]) -> str:
    redacted = message
    for sensitive_value in sensitive_values:
        redacted = _redact_text(redacted, sensitive_value)
    return redacted
