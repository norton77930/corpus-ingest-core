"""Preparation-only failure policy; other callers retain historical cleanup."""
from contextlib import contextmanager
from contextvars import ContextVar

_PRESERVE = ContextVar("preparation_preserve_partial_artifacts",default=False)


def preserve_partial_artifacts() -> bool:
    return _PRESERVE.get()


@contextmanager
def preparation_artifact_preservation():
    token=_PRESERVE.set(True)
    try:
        yield
    finally:
        _PRESERVE.reset(token)
