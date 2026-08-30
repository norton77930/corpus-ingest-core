"""Strict, externally selected canonical transcript identity for bound workflow stages.

Only a corpus episode seed may disambiguate identity-valid title variants.  A
verified-report lineage record or report manifest is derived output and can
never establish that root: accepting either would let an 018 artifact select
its own source.  A workflow may pin an immutable identity in a ContextVar so
all of its child writers use the same concrete transcript rather than a legacy
glob result.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from . import storage
from .secure_local_snapshot import secure_directory_names, secure_read_bytes

_MAX_TRANSCRIPT_BYTES = 64 * 1024 * 1024


class CanonicalTranscriptResolutionError(ValueError):
    """Raised when a transcript-bound workflow cannot select one canonical source."""


@dataclass(frozen=True)
class CanonicalTranscriptIdentity:
    """One immutable, identity-valid transcript selected before child execution."""

    podcast_id: str
    episode_ref: str
    title: str
    paths: storage.TranscriptAssetPaths
    json_sha256: str


_CURRENT_CANONICAL_TRANSCRIPT: ContextVar[CanonicalTranscriptIdentity | None] = ContextVar(
    "canonical_transcript_identity", default=None
)


def resolve_canonical_transcript_asset_paths(
    podcast_id: str,
    episode_ref: str,
) -> storage.TranscriptAssetPaths | None:
    """Return one identity-valid transcript or fail closed on title ambiguity.

    A corpus episode seed is the sole externally-originated selector.  No
    timestamp, filename ordering, 018 lineage sidecar, or report manifest may
    choose between identity-valid variants.
    """

    scoped = _CURRENT_CANONICAL_TRANSCRIPT.get()
    if scoped is not None and scoped.podcast_id == podcast_id and scoped.episode_ref == episode_ref:
        _validate_scoped_identity(scoped)
        return scoped.paths

    transcript_dir = storage.TRANSCRIPTS_DIR / podcast_id
    names = secure_directory_names(storage.TRANSCRIPTS_DIR, transcript_dir, max_entries=4_096)
    if names is None:
        return None
    raw_candidates = [transcript_dir / name for name in names if fnmatch.fnmatchcase(name, f"{episode_ref}__*.json")]
    candidates = [
        paths for path in raw_candidates if (paths := _identity_valid_paths(path, podcast_id, episode_ref)) is not None
    ]
    if not candidates:
        # Preserve a precise parser/validator diagnosis for one malformed legacy
        # artifact.  This is not a canonical identity or an ambiguity resolver:
        # no child may proceed until downstream validation rejects it.
        if len(raw_candidates) == 1:
            json_path = raw_candidates[0]
            return storage.TranscriptAssetPaths(
                text_path=json_path.with_suffix(".txt"),
                srt_path=json_path.with_suffix(".srt"),
                json_path=json_path,
            )
        return None
    if len(candidates) == 1:
        return candidates[0]

    selected = _seed_selected_path(candidates, podcast_id, episode_ref)
    if selected is None:
        raise CanonicalTranscriptResolutionError(
            "canonical transcript is ambiguous across identity-valid title variants"
        )
    return selected


def resolve_canonical_transcript_identity(
    podcast_id: str,
    episode_ref: str,
) -> CanonicalTranscriptIdentity | None:
    """Resolve and snapshot the one concrete transcript identity for an invocation."""

    paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if paths is None:
        return None
    raw = secure_read_bytes(storage.TRANSCRIPTS_DIR, paths.json_path, max_bytes=_MAX_TRANSCRIPT_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanonicalTranscriptResolutionError("canonical transcript is unreadable") from exc
    if raw is None:
        raise CanonicalTranscriptResolutionError("canonical transcript is unreadable")
    if not isinstance(payload, dict):
        raise CanonicalTranscriptResolutionError("canonical transcript identity is invalid")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise CanonicalTranscriptResolutionError("canonical transcript title is invalid")
    return CanonicalTranscriptIdentity(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        paths=paths,
        json_sha256=hashlib.sha256(raw).hexdigest(),
    )


@contextmanager
def canonical_transcript_scope(identity: CanonicalTranscriptIdentity) -> Iterator[CanonicalTranscriptIdentity]:
    """Pin one transcript identity for reentrant in-process child execution."""

    _validate_scoped_identity(identity)
    token = _CURRENT_CANONICAL_TRANSCRIPT.set(identity)
    try:
        yield identity
    finally:
        _CURRENT_CANONICAL_TRANSCRIPT.reset(token)


def current_canonical_transcript_identity(
    podcast_id: str,
    episode_ref: str,
) -> CanonicalTranscriptIdentity | None:
    """Return the current scoped identity, or resolve a fresh strict identity."""

    scoped = _CURRENT_CANONICAL_TRANSCRIPT.get()
    if scoped is not None and scoped.podcast_id == podcast_id and scoped.episode_ref == episode_ref:
        _validate_scoped_identity(scoped)
        return scoped
    return resolve_canonical_transcript_identity(podcast_id, episode_ref)


def _identity_valid_paths(
    json_path: Path,
    podcast_id: str,
    episode_ref: str,
) -> storage.TranscriptAssetPaths | None:
    raw = secure_read_bytes(storage.TRANSCRIPTS_DIR, json_path, max_bytes=_MAX_TRANSCRIPT_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    title = payload.get("title")
    if (
        payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or not isinstance(title, str)
        or not title.strip()
    ):
        return None
    try:
        expected = storage.transcript_asset_paths(podcast_id, episode_ref, title)
    except (TypeError, ValueError):
        return None
    # Reject a title/payload pair merely placed at an arbitrary same-episode name.
    if expected.json_path != json_path:
        return None
    return expected


def _seed_selected_path(
    candidates: list[storage.TranscriptAssetPaths],
    podcast_id: str,
    episode_ref: str,
) -> storage.TranscriptAssetPaths | None:
    """Use a valid corpus seed only when it names exactly one valid path."""

    seed_title = _trusted_seed_title(
        storage.corpus_episode_seed_asset_path(podcast_id, episode_ref),
        podcast_id,
        episode_ref,
    )
    if seed_title is None:
        return None
    expected = storage.transcript_asset_paths(podcast_id, episode_ref, seed_title)
    selected = [candidate for candidate in candidates if candidate.json_path == expected.json_path]
    return selected[0] if len(selected) == 1 else None


def _trusted_seed_title(path: Path, podcast_id: str, episode_ref: str) -> str | None:
    raw = secure_read_bytes(storage.CORPUS_DIR, path, max_bytes=_MAX_TRANSCRIPT_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    title = payload.get("title")
    if (
        payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or not isinstance(title, str)
        or not title.strip()
    ):
        return None
    return title


def _validate_scoped_identity(identity: CanonicalTranscriptIdentity) -> None:
    """Fail closed if a scoped source was replaced between child stages."""

    if not _identity_valid_paths(identity.paths.json_path, identity.podcast_id, identity.episode_ref):
        raise CanonicalTranscriptResolutionError("canonical transcript identity is no longer valid")
    raw = secure_read_bytes(storage.TRANSCRIPTS_DIR, identity.paths.json_path, max_bytes=_MAX_TRANSCRIPT_BYTES)
    if raw is None:
        raise CanonicalTranscriptResolutionError("canonical transcript is unreadable")
    current_sha256 = hashlib.sha256(raw).hexdigest()
    if current_sha256 != identity.json_sha256:
        raise CanonicalTranscriptResolutionError("canonical transcript changed during invocation")


def _canonical_path(path: Path) -> str:
    return path.resolve(strict=False).as_posix()
