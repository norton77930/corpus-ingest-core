"""Pure codec and fingerprints for study-guide lineage (SPEC049)."""
from __future__ import annotations

import json
import re
from typing import Any

from .workflow_derivation_lineage import bytes_digest, canonical_bytes, canonical_digest

RECEIPT_FILENAME = "study_guide.lineage.json"
SCHEMA_VERSION = 1
RECIPE_VERSION = 1
MAX_RECORD_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
INPUT_ROLES = ("semantic_summary",)
OUTPUT_ROLES = ("output_03", "output_04", "output_07")
CHANGED_ROLES = (*INPUT_ROLES, "recipe", "request", *OUTPUT_ROLES)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = {"schema_version", "recipe_version", "family", "podcast_id", "episode_ref",
           "identity_stem_sha256", "input_sha256", "request_sha256", "output_sha256"}


class RecordError(ValueError):
    """A finite receipt validation outcome; never carries record content."""
    def __init__(self, reason: str = "invalid_record") -> None:
        self.reason = reason
        super().__init__(reason)


def generation_record(podcast_id: str, episode_ref: str, stem: str,
                      source_text: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    """Capture exactly consumed summary/request before provider execution."""
    return {"schema_version": SCHEMA_VERSION, "recipe_version": RECIPE_VERSION,
            "family": "study_guide", "podcast_id": podcast_id, "episode_ref": episode_ref,
            "identity_stem_sha256": bytes_digest(stem.encode("utf-8")),
            "input_sha256": {"semantic_summary": bytes_digest(source_text.encode("utf-8"))},
            "request_sha256": canonical_digest(messages), "output_sha256": {}}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecordError()
        result[key] = value
    return result


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _validate(record: Any) -> None:
    if not isinstance(record, dict) or set(record) != _FIELDS:
        raise RecordError()
    if type(record["schema_version"]) is not int:
        raise RecordError()
    if record["schema_version"] != SCHEMA_VERSION:
        raise RecordError("unsupported_schema")
    if type(record["recipe_version"]) is not int or record["recipe_version"] < 1:
        raise RecordError()
    if record["family"] != "study_guide":
        raise RecordError()
    podcast, episode = record["podcast_id"], record["episode_ref"]
    if (not isinstance(podcast, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", podcast)
            or not isinstance(episode, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", episode)
            or episode.casefold() in {"latest", "next"}):
        raise RecordError()
    if not _is_digest(record["identity_stem_sha256"]) or not _is_digest(record["request_sha256"]):
        raise RecordError()
    for field, roles in (("input_sha256", INPUT_ROLES), ("output_sha256", OUTPUT_ROLES)):
        value = record[field]
        if not isinstance(value, dict) or set(value) != set(roles) or not all(_is_digest(v) for v in value.values()):
            raise RecordError()


def decode_record(payload: bytes) -> dict[str, Any]:
    if len(payload) > MAX_RECORD_BYTES:
        raise RecordError("record_unreadable")
    try:
        record = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs)
        _validate(record)
        return record
    except RecordError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise RecordError() from None


def encode_record(record: dict[str, Any]) -> bytes:
    _validate(record)
    payload = canonical_bytes(record) + b"\n"
    if len(payload) > MAX_RECORD_BYTES:
        raise RecordError("record_unreadable")
    return payload
