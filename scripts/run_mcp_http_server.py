from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core.local_env_names import MCP_PORT_ENV as PORT_ENV
from corpus_ingest_core.local_env_names import read_env
from corpus_ingest_core.mcp_server import StreamableHttpConfig, run_streamable_http

DEFAULT_PORT = 8767


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="以 loopback Streamable HTTP 啟動 corpus-ingest-core MCP server。"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_port_from_environment(),
        help=f"Loopback listener port（預設 {DEFAULT_PORT}；可由 {PORT_ENV} 設定）。",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    run_streamable_http(StreamableHttpConfig(port=args.port))


def _port_from_environment() -> int:
    raw = read_env(PORT_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_PORT
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{PORT_ENV} must be an integer") from exc


if __name__ == "__main__":
    main()
