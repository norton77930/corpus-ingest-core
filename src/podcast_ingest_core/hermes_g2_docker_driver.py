"""Spec032 pure future-adapter declaration.

This closure deliberately contains no Docker capability: no subprocess import,
no command execution and no constructable adapter.  A real subprocess adapter
belongs to a separately approved future successor, never to Spec032 offline
validation.
"""
from __future__ import annotations


class FutureSpec032DockerDriver:
    """Name-only successor contract; not an executable driver capability."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("real Docker adapter is outside the Spec032 offline closure")

    @staticmethod
    def _unavailable(*_args: object, **_kwargs: object) -> None:
        raise TypeError("real Docker adapter is outside the Spec032 offline closure")

    inspect_metadata = _unavailable
    activate_once = _unavailable
    rollback = _unavailable
