"""Invocation-scoped controlled child-commit notifications for SPEC 018."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator


@dataclass(frozen=True)
class ChildArtifactCommit:
    """A writer's post-commit event; it contains no artifact body."""

    role: str
    path: Path
    generated: bool
    metadata: dict[str, Any]


ChildCommitCallback = Callable[[ChildArtifactCommit], None]
_CURRENT_CALLBACK: ContextVar[ChildCommitCallback | None] = ContextVar(
    "latest_episode_verified_research_child_commit_callback", default=None
)


@contextmanager
def controlled_child_commit_scope(callback: ChildCommitCallback) -> Iterator[None]:
    """Deliver writer commits synchronously to the owning 018 invocation only."""

    token = _CURRENT_CALLBACK.set(callback)
    try:
        yield
    finally:
        _CURRENT_CALLBACK.reset(token)


def notify_child_artifact_committed(
    role: str,
    path: Path,
    *,
    generated: bool,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Notify a controlled parent after a writer atomically commits an artifact."""

    callback = _CURRENT_CALLBACK.get()
    if callback is None:
        return
    callback(
        ChildArtifactCommit(
            role=role,
            path=Path(path),
            generated=generated,
            metadata=dict(metadata or {}),
        )
    )
