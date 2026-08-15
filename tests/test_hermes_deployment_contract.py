from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = ROOT / "deploy" / "hermes"
DOCKERFILE = DEPLOY_DIR / "Dockerfile"
COMPOSE_FILE = DEPLOY_DIR / "docker-compose.sidecar.yml"
DOCKERIGNORE = ROOT / ".dockerignore"


def test_sidecar_dockerfile_is_non_root_explicit_and_http_only():
    text = DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.11-slim-bookworm" in text
    assert "COPY ." not in text
    assert "COPY pyproject.toml README.md" in text
    assert "COPY src" in text
    assert "COPY config" in text
    assert "COPY scripts/run_mcp_http_server.py" in text
    assert "PODCAST_INGEST_DATA_DIR=/var/lib/podcast-ingest-core/data" in text
    assert "PODCAST_INGEST_MCP_PORT=8767" in text
    assert "ARG MCP_VERSION=1.28.1" in text
    assert '"mcp[cli]==${MCP_VERSION}"' in text
    assert "USER podcast" in text
    assert "HEALTHCHECK" in text
    assert "run_mcp_http_server.py" in text
    assert "run_mcp_server.py" not in text


def test_docker_build_context_excludes_secret_and_runtime_surfaces():
    entries = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {".env", ".env.*", "data/", "evals/", ".git/", ".venv/"} <= entries


def test_sidecar_compose_is_host_network_loopback_only_and_persistent():
    payload = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    service = payload["services"]["podcast-ingest-core-mcp"]

    assert service["image"] == "podcast-ingest-core-mcp:local"
    assert service["container_name"] == "podcast-ingest-core-mcp"
    assert service["network_mode"] == "host"
    assert service["restart"] == "unless-stopped"
    assert "ports" not in service
    assert "env_file" not in service
    assert service["environment"] == {
        "PODCAST_INGEST_DATA_DIR": "/var/lib/podcast-ingest-core/data",
        "PODCAST_INGEST_MCP_PORT": "8767",
    }
    assert service["volumes"] == [
        "${PODCAST_INGEST_HOST_DATA_DIR:-../../data}:/var/lib/podcast-ingest-core/data"
    ]


def test_build_script_stages_only_the_explicit_sidecar_context():
    script = ROOT / "scripts" / "build_hermes_sidecar.sh"
    text = script.read_text(encoding="utf-8")

    assert "mktemp -d" in text
    assert 'cp "$ROOT/pyproject.toml" "$ROOT/README.md"' in text
    assert 'cp -R "$ROOT/src" "$ROOT/config"' in text
    assert 'cp "$ROOT/scripts/run_mcp_http_server.py"' in text
    assert 'cp "$ROOT/deploy/hermes/Dockerfile"' in text
    assert 'cp -R "$ROOT/"' not in text
    assert ".env" not in text


def test_deployment_bundle_never_configures_legacy_sse():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (DOCKERFILE, COMPOSE_FILE, DEPLOY_DIR / "README.md")
    ).lower()

    assert "transport: sse" not in text
    assert "/sse" not in text
