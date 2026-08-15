"""Pytest sentinel for Spec033 static-only targets."""
from __future__ import annotations
import builtins
import importlib
import os
import socket
import subprocess
import urllib.request  # preload sealed stdlib acquisition dependencies before socket blocking

_ORIGINAL_IMPORT = builtins.__import__
_ORIGINAL_IMPORT_MODULE = importlib.import_module
_BLOCKED_ROOTS = frozenset({"agent", "docker", "hermes", "hermes_cli", "model_tools", "providers", "run_agent"})
_BLOCKED_MODULES = frozenset({"scripts.run_spec_032_g2_once", "podcast_ingest_core.hermes_g2_docker_driver"})


def _blocked(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("Spec033 offline sentinel blocked a runtime capability")


def _allowed(name: object) -> bool:
    return type(name) is str and name.split(".", 1)[0] not in _BLOCKED_ROOTS and not any(name == item or name.startswith(f"{item}.") for item in _BLOCKED_MODULES)


def _guarded_import(name: object, globals: object = None, locals: object = None, fromlist: object = (), level: object = 0) -> object:
    if not _allowed(name):
        return _blocked()
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


def _guarded_import_module(name: object, package: object = None) -> object:
    if not _allowed(name):
        return _blocked()
    return _ORIGINAL_IMPORT_MODULE(name, package)


def pytest_sessionstart(session: object) -> None:
    del session
    subprocess.run = _blocked  # type: ignore[assignment]
    subprocess.Popen = _blocked  # type: ignore[assignment]
    subprocess.check_call = _blocked  # type: ignore[assignment]
    subprocess.check_output = _blocked  # type: ignore[assignment]
    os.system = _blocked  # type: ignore[assignment]
    os.popen = _blocked  # type: ignore[assignment]
    socket.socket = _blocked  # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    builtins.__import__ = _guarded_import  # type: ignore[assignment]
    importlib.import_module = _guarded_import_module  # type: ignore[assignment]
