"""Pytest plugin used only by the Spec032 final verifier's five test targets."""
from __future__ import annotations
import builtins
import importlib
import os
import subprocess

_ORIGINAL_IMPORT = builtins.__import__
_ORIGINAL_IMPORT_MODULE = importlib.import_module
_BLOCKED_MODULES = frozenset({
    "docker",
    "hermes",
    "podcast_ingest_core.hermes_g2_docker_driver",
    "scripts.run_spec_032_g2_once",
})


def _blocked(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("Spec032 offline sentinel blocked a runtime capability")


def _module_allowed(name: object) -> bool:
    if type(name) is not str:
        return False
    if name.split(".", 1)[0] in {"docker", "hermes"}:
        return False
    return not any(name == blocked or name.startswith(f"{blocked}.") for blocked in _BLOCKED_MODULES)


def _absolute_import_name(name: object, globals: object, level: object) -> str | None:
    if type(name) is not str or type(level) is not int or level < 0:
        return None
    if level == 0:
        return name
    if type(globals) is not dict:
        return None
    package = globals.get("__package__")
    if type(package) is not str or not package:
        return None
    try:
        return importlib.util.resolve_name(f"{'.' * level}{name}", package)
    except (ImportError, ValueError, AttributeError):
        return None


def _guarded_import(
    name: object,
    globals: object = None,
    locals: object = None,
    fromlist: object = (),
    level: object = 0,
) -> object:
    absolute_name = _absolute_import_name(name, globals, level)
    if not _module_allowed(absolute_name):
        return _blocked()
    children = () if fromlist is None else fromlist
    if type(children) not in (tuple, list):
        return _blocked()
    if any(
        type(child) is not str or not _module_allowed(f"{absolute_name}.{child}")
        for child in children
    ):
        return _blocked()
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


def _guarded_import_module(name: object, package: object = None) -> object:
    if type(name) is not str or type(package) not in (str, type(None)):
        return _blocked()
    try:
        absolute_name = importlib.util.resolve_name(name, package) if name.startswith(".") else name
    except (ImportError, ValueError, AttributeError):
        return _blocked()
    if not _module_allowed(absolute_name):
        return _blocked()
    return _ORIGINAL_IMPORT_MODULE(name, package)


def pytest_sessionstart(session: object) -> None:
    """Block process, Docker/Hermes, and future-concrete capability edges."""
    del session
    subprocess.run = _blocked  # type: ignore[assignment]
    subprocess.Popen = _blocked  # type: ignore[assignment]
    subprocess.check_call = _blocked  # type: ignore[assignment]
    subprocess.check_output = _blocked  # type: ignore[assignment]
    os.system = _blocked  # type: ignore[assignment]
    os.popen = _blocked  # type: ignore[assignment]
    builtins.__import__ = _guarded_import  # type: ignore[assignment]
    importlib.import_module = _guarded_import_module  # type: ignore[assignment]
