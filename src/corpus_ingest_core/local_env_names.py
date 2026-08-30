"""Environment-variable names, with the pre-rename spellings still honoured.

The package was renamed from ``podcast_ingest_core`` to ``corpus_ingest_core``
in 0.2.0, and its four ``PODCAST_INGEST_*`` variables were renamed with it.
An operator who set the old name on a machine that predates the rename should
not have their setup silently stop taking effect -- a data root that quietly
reverts to ``data/`` is the kind of failure that looks like corruption rather
than configuration. So the old spelling still works, and the new one wins when
both are set.

Deprecated aliases are scheduled for removal in 0.3.0.
"""

from __future__ import annotations

import os

CONFIG_ENV = "CORPUS_INGEST_CONFIG"
DATA_DIR_ENV = "CORPUS_INGEST_DATA_DIR"
STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH_ENV = "CORPUS_INGEST_STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH"
MCP_PORT_ENV = "CORPUS_INGEST_MCP_PORT"

DEPRECATED_ALIASES = {
    CONFIG_ENV: "PODCAST_INGEST_CONFIG",
    DATA_DIR_ENV: "PODCAST_INGEST_DATA_DIR",
    STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH_ENV: ("PODCAST_INGEST_STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH"),
    MCP_PORT_ENV: "PODCAST_INGEST_MCP_PORT",
}


def read_env(name: str) -> str | None:
    """Return ``name``'s value, falling back to its deprecated spelling."""

    value = os.environ.get(name)
    if value is not None:
        return value
    alias = DEPRECATED_ALIASES.get(name)
    return os.environ.get(alias) if alias else None


def env_is_set(name: str) -> bool:
    """True when ``name`` or its deprecated spelling is present at all."""

    if name in os.environ:
        return True
    alias = DEPRECATED_ALIASES.get(name)
    return alias is not None and alias in os.environ


def names_for(name: str) -> tuple[str, ...]:
    """``name`` plus its deprecated spelling, for messages and test cleanup."""

    alias = DEPRECATED_ALIASES.get(name)
    return (name, alias) if alias else (name,)
