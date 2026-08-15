"""Pre-pytest runtime sentinel for Spec034's sealed isolated child.

The isolated runner executes these verified bytes and calls :func:`install`
before it imports pytest.  No repo-local plugin import participates in startup.
"""
from __future__ import annotations

import builtins
from pathlib import Path
import socket
import subprocess
import sys
import types
import urllib.request

_BLOCKED_ROOTS = frozenset(("agent", "hermes_cli", "run_agent", "providers", "model_tools", "plugins"))
_ORIGINAL_IMPORT = builtins.__import__
GUARDS_INSTALLED = False


def _blocked_import(name: str, *args: object, **kwargs: object):
    if name.split(".", 1)[0] in _BLOCKED_ROOTS:
        raise ImportError("Spec034 upstream import blocked")
    return _ORIGINAL_IMPORT(name, *args, **kwargs)


def _blocked(*_args: object, **_kwargs: object):
    raise RuntimeError("Spec034 offline runtime capability blocked")


def install(root: Path) -> None:
    """Install guards before pytest and target-test imports occur."""
    global GUARDS_INSTALLED
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValueError("sealed root is required")
    package_root = root / "src" / "podcast_ingest_core"
    try:
        package_info = package_root.lstat()
        if not package_root.is_relative_to(root) or not package_root.is_dir() or package_root.is_symlink() or bool(getattr(package_info, "st_file_attributes", 0) & 0x400):
            raise ValueError("sealed project package root is required")
    except OSError as error:
        raise ValueError("sealed project package root is required") from error
    if "podcast_ingest_core" not in sys.modules:
        package = types.ModuleType("podcast_ingest_core")
        package.__path__ = [str(package_root)]
        package.__package__ = "podcast_ingest_core"
        sys.modules["podcast_ingest_core"] = package
    builtins.__import__ = _blocked_import
    socket.socket = _blocked  # type: ignore[assignment]
    subprocess.run = _blocked  # type: ignore[assignment]
    subprocess.Popen = _blocked  # type: ignore[assignment]
    urllib.request.urlopen = _blocked  # type: ignore[assignment]
    GUARDS_INSTALLED = True


def pytest_configure() -> None:
    """Compatibility hook; isolated execution installs guards earlier."""
    if not GUARDS_INSTALLED:
        install(Path.cwd().absolute())
