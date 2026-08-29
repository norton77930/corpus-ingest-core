"""Canonical semantic-summary identity resolved from transcript metadata."""

from __future__ import annotations

import json
from pathlib import Path

from . import storage
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    resolve_canonical_transcript_asset_paths,
)


def canonical_semantic_summary_path(
    podcast_id: str,
    episode_ref: str,
) -> Path | None:
    """Return only the summary path named by the canonical transcript title.

    A same-episode glob can contain stale summaries after a title correction.  Those
    candidates are deliberately not interchangeable with the title-bearing
    transcript artifact that anchors semantic-review and report identity.
    """

    try:
        transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    except CanonicalTranscriptResolutionError:
        return None
    if transcript_paths is None:
        return None
    try:
        payload = json.loads(transcript_paths.json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != episode_ref:
        return None
    title = payload.get("title")
    return canonical_semantic_summary_path_for_title(podcast_id, episode_ref, title)


def canonical_semantic_summary_path_for_title(
    podcast_id: str,
    episode_ref: str,
    title: object,
) -> Path | None:
    """Build a canonical summary path from an already immutable transcript title."""

    if not isinstance(title, str) or not title.strip():
        return None
    try:
        return storage.semantic_summary_asset_path(podcast_id, episode_ref, title)
    except (TypeError, ValueError):
        return None
