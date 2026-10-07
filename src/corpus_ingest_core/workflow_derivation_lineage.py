"""Pure codec and fingerprints for workflow derivation lineage (SPEC048)."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

RECEIPT_FILENAME = "workflow_derivation.lineage.json"
SCHEMA_VERSION = 1
RECIPE_VERSION = 1
MAX_RECORD_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
INPUT_ROLES = ("lecture_03", "lecture_04", "lecture_07", "effective_context")
OUTPUT_ROLES = ("output_05", "output_06")
CHANGED_ROLES = (*INPUT_ROLES, "recipe", "request", *OUTPUT_ROLES)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = {"schema_version", "recipe_version", "family", "podcast_id", "episode_ref",
           "identity_stem_sha256", "context_origin", "input_sha256", "request_sha256", "output_sha256"}


class RecordError(ValueError):
    """A finite receipt validation outcome; never carries record content."""
    def __init__(self, reason: str = "invalid_record") -> None:
        self.reason = reason
        super().__init__(reason)


def bytes_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return bytes_digest(canonical_bytes(value))


def input_digests(lecture_text: dict[str, str], allowed_tools: list[str]) -> dict[str, str]:
    return {**{f"lecture_{role}": bytes_digest(lecture_text[role].encode("utf-8")) for role in ("03", "04", "07")},
            "effective_context": canonical_digest(allowed_tools)}


def generation_record(podcast_id: str, episode_ref: str, stem: str, context_origin: str,
                      lecture_text: dict[str, str], allowed_tools: list[str], messages: list[dict[str, str]]) -> dict[str, Any]:
    """Capture inputs before provider execution; outputs are filled during staging."""
    return {"schema_version": SCHEMA_VERSION, "recipe_version": RECIPE_VERSION,
            "family": "workflow_derivation", "podcast_id": podcast_id, "episode_ref": episode_ref,
            "identity_stem_sha256": bytes_digest(stem.encode("utf-8")), "context_origin": context_origin,
            "input_sha256": input_digests(lecture_text, allowed_tools),
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
    if record["family"] != "workflow_derivation" or record["context_origin"] not in ("default", "custom"):
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
