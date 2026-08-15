FROM python:3.11-slim-bookworm

ARG MCP_VERSION=1.28.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PODCAST_INGEST_DATA_DIR=/var/lib/podcast-ingest-core/data \
    PODCAST_INGEST_MCP_PORT=8767

WORKDIR /app

RUN useradd --create-home --uid 10001 podcast

COPY pyproject.toml README.md ./
COPY src ./src
# Preinstall the shared numeric dependency to avoid resolver backtracking across
# the faster-whisper/ctranslate2 wheel matrix in minimal images.
RUN python -m pip install --no-cache-dir \
        "numpy>=1.23,<3" \
        "mcp[cli]==${MCP_VERSION}" \
    && python -m pip install --no-cache-dir .

COPY config ./config
COPY scripts/run_mcp_http_server.py ./scripts/run_mcp_http_server.py

RUN mkdir -p /var/lib/podcast-ingest-core/data \
    && chown -R podcast:podcast /var/lib/podcast-ingest-core /app

USER podcast

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=4 \
    CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1',int(os.environ['PODCAST_INGEST_MCP_PORT'])),2); s.close()"

ENTRYPOINT ["python", "scripts/run_mcp_http_server.py"]
