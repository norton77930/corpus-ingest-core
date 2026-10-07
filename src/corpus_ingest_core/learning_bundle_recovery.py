"""Read-only, bounded learning-bundle recovery diagnosis (SPEC050)."""
from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any
import yaml

from . import storage, study_guide_lineage, workflow_derivation_lineage
from .canonical_transcript import resolve_canonical_transcript_asset_paths
from .config import load_podcast_profile
from .errors import PodcastIngestCoreError
from .secure_local_snapshot import secure_directory_names, secure_read_bytes
from .summary_profiles import LEARNING_NOTES

INVALID_IDENTITY_MESSAGE = "Invalid explicit episode identity."
QUERY_ERROR_MESSAGE = "Learning bundle recovery could not be inspected safely."
MAX_IDENTITY_BYTES = 64 * 1024 * 1024
MAX_RECORD_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_DIRECTORY_ENTRIES = 256
LOCATIONS = (("public", ""), ("lecture_part", ".part"), ("lecture_old", ".old"),
             ("derivation_part", ".wfderive.part"), ("derivation_old", ".wfderive.old"))
ROLE_FILES = {"00": "00_video_info.md", "03": "03_full_summary.md", "04": "04_learning_notes.md",
              "05": "05_prompt_examples.md", "06": "06_apply_to_my_workflow.md", "07": "07_final_study_guide.md"}
RECORD_CODECS = {"study_guide": study_guide_lineage, "workflow_derivation": workflow_derivation_lineage}


class _ObservationError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _require_identity(podcast_id: object, episode_ref: object) -> None:
    if (not isinstance(podcast_id, str) or not isinstance(episode_ref, str)
            or episode_ref.casefold() in {"latest", "next"} or not storage.is_safe_episode_ref(episode_ref)):
        raise ValueError(INVALID_IDENTITY_MESSAGE)
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "identity")
    except (TypeError, ValueError):
        raise ValueError(INVALID_IDENTITY_MESSAGE) from None


def _canonical_bundle(podcast_id: str, episode_ref: str) -> Path:
    try:
        profile = load_podcast_profile(podcast_id)
    except (AttributeError, TypeError):
        raise _ObservationError("identity_unavailable") from None
    if profile.summary_profile != LEARNING_NOTES:
        raise _ObservationError("identity_unavailable")
    identity = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if identity is None:
        raise _ObservationError("identity_unavailable")
    raw = secure_read_bytes(storage.TRANSCRIPTS_DIR, identity.json_path, max_bytes=MAX_IDENTITY_BYTES)
    if raw is None:
        raise _ObservationError("identity_unavailable")
    payload = json.loads(raw.decode("utf-8"))
    if (not isinstance(payload, dict) or payload.get("podcast_id") != podcast_id
            or payload.get("episode_ref") != episode_ref or not isinstance(payload.get("title"), str)
            or not payload["title"].strip()):
        raise _ObservationError("identity_unavailable")
    expected = storage.transcript_asset_paths(podcast_id, episode_ref, payload["title"])
    if identity.json_path != expected.json_path:
        raise _ObservationError("identity_unavailable")
    bundle = storage.study_guide_bundle_paths(podcast_id, episode_ref, payload["title"]).bundle_dir
    bundle.name.encode("utf-8")
    return bundle


def _lstat(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        raise _ObservationError("inspection_unavailable") from None


def _is_reparse(info) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        (getattr(info, "st_file_attributes", 0) or 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _safe_parents(root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        raise _ObservationError("unsafe_path") from None
    # Check lexical ancestors before treating a missing managed root as absence.
    for ancestor in reversed(root.absolute().parents):
        info = _lstat(ancestor)
        if info is None:
            return False
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise _ObservationError("unsafe_path")
    current = root
    for part in (None, *parts[:-1]):
        if part is not None:
            current = current / part
        info = _lstat(current)
        if info is None:
            return False
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise _ObservationError("unsafe_path")
    return True


def _record_result(status: str, output_status: str = "not_evaluated",
                   changed_roles: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "output_status": output_status, "changed_roles": changed_roles or []}


def _location_result(tag: str, status: str, reason: str) -> dict[str, Any]:
    unknown = status == "blocked"
    return {"location": tag, "status": status, "reason": reason,
            "roles": {role: None if unknown else False for role in ROLE_FILES},
            "lecture_state": "unknown" if unknown else "absent",
            "derivation_state": "unknown" if unknown else "absent", "extra_files": None if unknown else 0,
            "records": {family: _record_result("not_evaluated" if unknown else "absent") for family in RECORD_CODECS}}


def _group_state(roles: dict[str, bool], keys: tuple[str, ...]) -> str:
    count = sum(roles[k] for k in keys)
    return "complete" if count == len(keys) else "partial" if count else "absent"


def _observe_record(directory: Path, names: tuple[str, ...], codec,
                    podcast_id: str, episode_ref: str, stem: str) -> dict[str, Any]:
    if codec.RECEIPT_FILENAME not in names:
        return _record_result("absent")
    raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, directory / codec.RECEIPT_FILENAME,
                            max_bytes=MAX_RECORD_BYTES)
    if raw is None:
        return _record_result("record_unreadable")
    try:
        record = codec.decode_record(raw)
    except codec.RecordError as exc:
        return _record_result(exc.reason)
    if (record["podcast_id"] != podcast_id or record["episode_ref"] != episode_ref
            or record["identity_stem_sha256"] != codec.bytes_digest(stem.encode("utf-8"))):
        return _record_result("identity_mismatch")
    if any(ROLE_FILES[role[-2:]] not in names for role in codec.OUTPUT_ROLES):
        return _record_result("valid", "missing")
    changed = []
    for role in codec.OUTPUT_ROLES:
        output = secure_read_bytes(storage.STUDY_GUIDES_DIR, directory / ROLE_FILES[role[-2:]],
                                   max_bytes=MAX_OUTPUT_BYTES)
        if output is None:
            return _record_result("valid", "unavailable")
        if codec.bytes_digest(output) != record["output_sha256"][role]:
            changed.append(role)
    return _record_result("valid", "mismatch" if changed else "match", changed)


def _observe_location(tag: str, directory: Path, podcast_id: str, episode_ref: str, stem: str) -> dict[str, Any]:
    try:
        if not _safe_parents(storage.STUDY_GUIDES_DIR, directory):
            return _location_result(tag, "absent", "missing")
        info = _lstat(directory)
        if info is None:
            return _location_result(tag, "absent", "missing")
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise _ObservationError("unsafe_path")
        names = secure_directory_names(storage.STUDY_GUIDES_DIR, directory, max_entries=MAX_DIRECTORY_ENTRIES)
        if names is None:
            raise _ObservationError("inspection_unavailable")
        for name in names:
            child = _lstat(directory / name)
            if child is None:
                raise _ObservationError("inspection_unavailable")
            if _is_reparse(child) or not stat.S_ISREG(child.st_mode):
                raise _ObservationError("unsafe_path")
    except _ObservationError as exc:
        return _location_result(tag, "blocked", exc.reason)
    row = _location_result(tag, "observed", "observed")
    row["roles"] = {role: name in names for role, name in ROLE_FILES.items()}
    row["lecture_state"] = _group_state(row["roles"], ("00", "03", "04", "07"))
    row["derivation_state"] = _group_state(row["roles"], ("05", "06"))
    known = set(ROLE_FILES.values()) | {c.RECEIPT_FILENAME for c in RECORD_CODECS.values()}
    row["extra_files"] = sum(name not in known for name in names)
    for family, codec in RECORD_CODECS.items():
        row["records"][family] = _observe_record(directory, names, codec, podcast_id, episode_ref, stem)
    return row


def _has_anomaly(row: dict[str, Any]) -> bool:
    if "partial" in (row["lecture_state"], row["derivation_state"]):
        return True
    return any(record["status"] not in {"absent", "valid"}
               or (record["status"] == "valid" and record["output_status"] != "match")
               for record in row["records"].values())


def inspect_learning_bundle_recovery(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Observe fixed locations and owned receipt consistency, never repair or select a winner."""
    _require_identity(podcast_id, episode_ref)

    def result(status: str, reason: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {"podcast_id": podcast_id, "episode_ref": episode_ref, "status": status, "reason": reason,
                "manual_review_required": status != "clear", "locations": rows,
                "scope": "learning_bundle_recovery", "read_only": True, "network_access": False,
                "warnings": ["diagnostic_scope_only", "non_atomic_observation", "publication_outcome_not_proven"]}

    try:
        directory = _canonical_bundle(podcast_id, episode_ref)
    except (PodcastIngestCoreError, _ObservationError, ValueError, KeyError, OSError, yaml.YAMLError, RecursionError):
        return result("blocked", "identity_unavailable", [])
    rows = [_observe_location(tag, directory.with_name(directory.name + suffix), podcast_id, episode_ref, directory.name)
            for tag, suffix in LOCATIONS]
    blocked = [row["reason"] for row in rows if row["status"] == "blocked"]
    if blocked:
        return result("blocked", "unsafe_path" if "unsafe_path" in blocked else "inspection_unavailable", rows)
    if any(row["status"] == "observed" for row in rows[1:]):
        return result("recovery_present", "recovery_entries_present", rows)
    if any(_has_anomaly(row) for row in rows):
        return result("blocked", "manual_review_required", rows)
    return result("clear", "no_recovery_entries", rows)
