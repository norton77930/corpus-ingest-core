from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HTTP_RUNNER = ROOT / "scripts" / "run_mcp_http_server.py"


def test_streamable_http_reuses_the_facade_mcp_instance():
    from corpus_ingest_core import mcp_runtime, mcp_server

    assert mcp_server.mcp is mcp_runtime.mcp


def test_streamable_http_config_accepts_only_the_approved_listener():
    from corpus_ingest_core.mcp_runtime import StreamableHttpConfig

    assert StreamableHttpConfig() == StreamableHttpConfig(
        host="127.0.0.1",
        port=8767,
        path="/mcp",
    )

    with pytest.raises(ValueError, match="host must be 127.0.0.1"):
        StreamableHttpConfig(host="0.0.0.0")
    with pytest.raises(ValueError, match="path must be /mcp"):
        StreamableHttpConfig(path="/other")
    with pytest.raises(ValueError, match="port must be between 1 and 65535"):
        StreamableHttpConfig(port=0)
    with pytest.raises(ValueError, match="port must be an integer"):
        StreamableHttpConfig(port="8767")


def test_streamable_http_sets_public_settings_and_runs_the_existing_server(monkeypatch):
    from corpus_ingest_core import mcp_runtime

    calls: list[tuple[str, str, int, str]] = []
    security = mcp_runtime.mcp.settings.transport_security

    monkeypatch.setattr(mcp_runtime.mcp.settings, "host", "127.0.0.1")
    monkeypatch.setattr(mcp_runtime.mcp.settings, "port", 8000)
    monkeypatch.setattr(mcp_runtime.mcp.settings, "streamable_http_path", "/mcp")

    def fake_run(*, transport: str = "stdio", mount_path=None):
        del mount_path
        calls.append(
            (
                transport,
                mcp_runtime.mcp.settings.host,
                mcp_runtime.mcp.settings.port,
                mcp_runtime.mcp.settings.streamable_http_path,
            )
        )

    monkeypatch.setattr(mcp_runtime.mcp, "run", fake_run)

    mcp_runtime.run_streamable_http(
        mcp_runtime.StreamableHttpConfig(port=8767)
    )

    assert calls == [("streamable-http", "127.0.0.1", 8767, "/mcp")]
    assert mcp_runtime.mcp.settings.transport_security is security
    assert security.enable_dns_rebinding_protection is True


def test_stdio_run_remains_the_default_transport(monkeypatch):
    from corpus_ingest_core import mcp_runtime

    calls = []
    monkeypatch.setattr(mcp_runtime.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    mcp_runtime.run()

    assert calls == [((), {})]


def test_http_runner_is_a_thin_facade_entrypoint():
    assert HTTP_RUNNER.exists()
    spec = importlib.util.spec_from_file_location("run_mcp_http_server", HTTP_RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.DEFAULT_PORT == 8767
    assert callable(module.parse_args)
    assert callable(module.main)
