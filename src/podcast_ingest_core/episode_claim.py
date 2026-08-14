"""Shared reentrant episode writer/cost claims.

A claim key is the podcast plus canonical episode reference, not a report path.
Consequently all direct and orchestration entry points serialize provider
construction, exists checks, and writers for one episode while unrelated
episodes remain concurrent.  The underlying descriptor lock is also the
cross-process authority.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
import inspect
import re
from typing import Any, Callable, Iterator, ParamSpec, TypeVar

from . import storage
from .artifact_lock import exclusive_artifact_claim


@dataclass
class _HeldEpisodeClaim:
    manager: Any
    depth: int = 1


_CONTROLLED_REGENERATION_CAPABILITY_NONCE = object()


@dataclass
class _ControlledRegenerationCapability:
    """Opaque, one-shot authority tied to one held episode writer claim."""

    podcast_id: str
    episode_ref: str
    _nonce: object = field(repr=False, default=None)
    _used: bool = False


_CURRENT_EPISODE_CLAIMS: ContextVar[dict[str, _HeldEpisodeClaim] | None] = ContextVar(
    "episode_writer_claims", default=None
)

P = ParamSpec("P")
T = TypeVar("T")
_SAFE_PODCAST_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_SAFE_EPISODE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def validate_episode_writer_claim_identity(podcast_id: object, episode_ref: object) -> tuple[str, str]:
    """Reject unsafe claim components before a lock path can create a directory."""

    if (
        not isinstance(podcast_id, str)
        or not isinstance(episode_ref, str)
        or not _SAFE_PODCAST_ID.fullmatch(podcast_id)
        or not _SAFE_EPISODE_REF.fullmatch(episode_ref)
        or podcast_id.upper() in _WINDOWS_RESERVED
        or episode_ref.upper() in _WINDOWS_RESERVED
    ):
        raise ValueError("episode writer claim identity is invalid")
    return podcast_id, episode_ref


def _episode_writer_claim_is_held(podcast_id: object, episode_ref: object) -> bool:
    """Return whether this context currently owns the exact writer claim."""

    try:
        podcast_id, episode_ref = validate_episode_writer_claim_identity(
            podcast_id, episode_ref
        )
    except ValueError:
        return False
    held_claims = _CURRENT_EPISODE_CLAIMS.get()
    held = (
        held_claims.get(f"{podcast_id}\x00{episode_ref}")
        if held_claims is not None
        else None
    )
    return held is not None and held.depth > 0


def _mint_controlled_regeneration_capability(
    podcast_id: str, episode_ref: str
) -> _ControlledRegenerationCapability:
    """Mint one package-private overwrite authority only beneath a writer claim."""

    podcast_id, episode_ref = validate_episode_writer_claim_identity(
        podcast_id, episode_ref
    )
    if not _episode_writer_claim_is_held(podcast_id, episode_ref):
        raise ValueError("controlled regeneration writer claim is not held")
    return _ControlledRegenerationCapability(
        podcast_id, episode_ref, _CONTROLLED_REGENERATION_CAPABILITY_NONCE
    )


def _validate_controlled_regeneration_capability(
    capability: object, podcast_id: str, episode_ref: str
) -> None:
    """Fail closed unless an unused authority matches the currently held claim."""

    if (
        not isinstance(capability, _ControlledRegenerationCapability)
        or capability.podcast_id != podcast_id
        or capability.episode_ref != episode_ref
        or capability._nonce is not _CONTROLLED_REGENERATION_CAPABILITY_NONCE
        or capability._used
        or not _episode_writer_claim_is_held(podcast_id, episode_ref)
    ):
        raise ValueError("controlled regeneration authority is invalid")


def _consume_controlled_regeneration_capability(
    capability: object, podcast_id: str, episode_ref: str
) -> None:
    """Consume authority exactly once immediately before the forced writer."""

    _validate_controlled_regeneration_capability(capability, podcast_id, episode_ref)
    assert isinstance(capability, _ControlledRegenerationCapability)
    capability._used = True


@contextmanager
def episode_writer_claim(
    podcast_id: str,
    episode_ref: str,
    *,
    timeout_seconds: float = 15.0,
) -> Iterator[None]:
    """Acquire one reentrant local/cross-process writer and cost claim."""

    podcast_id, episode_ref = validate_episode_writer_claim_identity(
        podcast_id, episode_ref
    )
    key = f"{podcast_id}\x00{episode_ref}"
    held_claims = _CURRENT_EPISODE_CLAIMS.get()
    held = held_claims.get(key) if held_claims is not None else None
    if held is not None:
        held.depth += 1
        try:
            yield
        finally:
            held.depth -= 1
        return

    claim_path = (
        storage.CORPUS_DIR
        / podcast_id
        / ".episode-claims"
        / f"{episode_ref}.writer.claim"
    )
    manager = exclusive_artifact_claim(claim_path, timeout_seconds=timeout_seconds)
    manager.__enter__()
    new_claims = dict(held_claims or {})
    new_held = _HeldEpisodeClaim(manager=manager)
    new_claims[key] = new_held
    token = _CURRENT_EPISODE_CLAIMS.set(new_claims)
    try:
        yield
    finally:
        # An exception in a child cannot abandon the OS descriptor lock.  Nested
        # calls have reduced their depth before this outer frame exits.
        _CURRENT_EPISODE_CLAIMS.reset(token)
        manager.__exit__(None, None, None)


def episode_writer_claimed(function: Callable[P, T]) -> Callable[P, T]:
    """Decorate a ``(podcast_id, episode_ref, ...)`` writer without API change."""

    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            bound = signature.bind_partial(*args, **kwargs)
        except TypeError:
            # Preserve the public function's own argument error without a claim.
            return function(*args, **kwargs)
        podcast_id = bound.arguments.get("podcast_id")
        episode_ref = bound.arguments.get("episode_ref")
        if podcast_id is None or episode_ref is None:
            return function(*args, **kwargs)
        podcast_id, episode_ref = validate_episode_writer_claim_identity(
            podcast_id, episode_ref
        )
        with episode_writer_claim(podcast_id, episode_ref):
            return function(*args, **kwargs)

    return wrapped
