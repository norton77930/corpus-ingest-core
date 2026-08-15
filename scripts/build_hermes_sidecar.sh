#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${1:-podcast-ingest-core-mcp:local}"
CONTEXT="$(mktemp -d /tmp/podcast-mcp-build.XXXXXX)"

cleanup() {
  rm -rf "$CONTEXT"
}
trap cleanup EXIT

cp "$ROOT/pyproject.toml" "$ROOT/README.md" "$CONTEXT/"
cp -R "$ROOT/src" "$ROOT/config" "$CONTEXT/"
mkdir -p "$CONTEXT/scripts"
cp "$ROOT/scripts/run_mcp_http_server.py" "$CONTEXT/scripts/"
cp "$ROOT/deploy/hermes/Dockerfile" "$CONTEXT/Dockerfile"

docker build -f "$CONTEXT/Dockerfile" -t "$IMAGE" "$CONTEXT"
docker image inspect --format '{{.Id}}' "$IMAGE"
