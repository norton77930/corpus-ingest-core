"""Dry-run-first study-guide bundle runner.

Reads an existing learning-notes semantic summary and writes 00/03/04/07.
Never sends transcript text to a provider.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from . import storage, study_guide_lineage as lineage
from .canonical_transcript import (
    CanonicalTranscriptResolutionError,
    resolve_canonical_transcript_asset_paths,
)
from .config import load_podcast_profile
from .errors import PodcastIngestCoreError, StudyGuideBundleError, StudyGuideBundleStateError
from .llm_provider import create_provider, require_exact_api_cost_ack
from .models import StudyGuideBundleResult
from .report_safety import matched_investment_advice_guard
from .run_report_io import write_part_staged_report_pair
from .secure_local_snapshot import secure_read_bytes
from .semantic_summary_identity import canonical_semantic_summary_path_for_title
from .study_guide_profiles import (
    BUNDLE_KEYS,
    COVER_FILENAME,
    FINANCE_HEADINGS,
    GUIDE_FILENAME,
    NOTES_FILENAME,
    STUDY_GUIDE_PROFILE,
    SUMMARY_FILENAME,
    WORKFLOW_MARKERS,
)
from .summary_profiles import LEARNING_NOTES

CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. This workflow never rebuilds it automatically."
)
_CHUNK_SPLIT = re.compile(r"(?im)^##\s+Chunk Summaries\s*$")
_HEADING = re.compile(r"(?im)^#{1,3}\s*(?:\d+\.\s*)?(.+?)\s*$")
_TIMESTAMP = re.compile(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]")
_CLOCK = re.compile(r"\b\d{2}:\d{2}:\d{2}\b")
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
_MAX_TRANSCRIPT_JSON_BYTES = 64 * 1024 * 1024
_RESERVED_EPISODE_REFS = frozenset({"latest", "next"})
_MISSING_SUMMARY = (
    "canonical learning-notes semantic summary is missing; "
    "generate it first — this runner does not create summaries"
)
REQUIRED_PROFILE = LEARNING_NOTES


def run_study_guide_bundle(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
) -> StudyGuideBundleResult:
    """Plan or write one study-guide bundle for a learning-notes episode."""

    _require_explicit_identity(podcast_id, episode_ref)
    profile = load_podcast_profile(podcast_id)
    if profile.summary_profile != REQUIRED_PROFILE:
        raise StudyGuideBundleError(
            f"study-guide bundle requires summary_profile={REQUIRED_PROFILE}; got {profile.summary_profile!r}"
        )

    source_path, identity_path = _resolve_source_path(podcast_id, episode_ref)
    _require_operation_paths(podcast_id, episode_ref, source_path)
    source_text = _read_source_text(source_path)
    if _is_finance_shaped(source_text):
        raise StudyGuideBundleError(
            "source semantic summary is finance-shaped; refusing to generate a study-guide bundle"
        )

    title = _episode_title(podcast_id, episode_ref, source_path)
    stem = source_path.name.removesuffix(".semantic.md")
    paths = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    file_map = _file_map(paths)
    existing_readable = {label for label, path in file_map.items() if path.is_file() and _is_readable(path)}
    lecture_complete = {"03", "04", "07"} <= existing_readable
    complete = existing_readable == {"00", "03", "04", "07"}
    reuse_all = complete and not force
    cover_only = lecture_complete and "00" not in existing_readable and not force
    if existing_readable and not reuse_all and not cover_only and not force:
        raise StudyGuideBundleError("incomplete study-guide bundle; pass force=true to replace the whole set")
    if not reuse_all and not cover_only and _has_derivation(paths.bundle_dir):
        raise StudyGuideBundleStateError("derivation_conflict")

    receipt_path = paths.bundle_dir / lineage.RECEIPT_FILENAME
    generating = not reuse_all and not cover_only
    metadata_writes = [str(receipt_path)] if generating else []
    if generating:
        _preflight_record(receipt_path, podcast_id, episode_ref, stem)

    planned_reads = [str(source_path), str(identity_path)]
    if generating and _lstat(receipt_path) is not None:
        planned_reads.append(str(receipt_path))
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)
    _require_optional_file(storage.CORPUS_DIR, seed_path)
    if seed_path.is_file():
        planned_reads.append(str(seed_path))
    audio_path = _find_audio(podcast_id, episode_ref)
    if audio_path is not None:
        planned_reads.append(str(audio_path))

    if reuse_all:
        planned_writes: list[str] = []
        planned_reuses = [str(path) for path in file_map.values()]
    elif cover_only:
        planned_writes = [str(file_map["00"])]
        planned_reuses = [str(file_map[label]) for label in ("03", "04", "07")]
    else:
        planned_writes = [str(path) for path in file_map.values()]
        planned_reuses = []

    if not confirm:
        return _result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            source_summary_path=str(source_path),
            bundle_dir=str(paths.bundle_dir),
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            planned_reuses=planned_reuses,
            metadata_writes=metadata_writes,
            output_paths={},
            report_json_path=None,
            report_markdown_path=None,
            reused=reuse_all,
            warnings=[CACHE_STALE_WARNING] if planned_writes else [],
        )

    generated = {
        "00": _render_cover(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            seed_path=seed_path,
            audio_path=audio_path,
        )
    }
    bodies: dict[str, str] | None = None
    record: dict[str, Any] | None = None
    if not reuse_all and not cover_only:
        require_exact_api_cost_ack(api_cost_ack)
        messages = _build_messages(source_text)
        record = lineage.generation_record(podcast_id, episode_ref, stem, source_text, messages)
        llm = create_provider(
            provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            api_cost_ack=api_cost_ack,
        )
        raw = llm.complete(messages)
        parsed = _parse_bundle_payload(raw)
        _validate_generated(parsed, source_text)
        bodies = {
            "03": parsed["03_full_summary"],
            "04": parsed["04_learning_notes"],
            "07": parsed["07_final_study_guide"],
        }

    if not reuse_all:
        overlay = {COVER_FILENAME: generated["00"]}
        if bodies is not None:
            overlay[SUMMARY_FILENAME] = bodies["03"]
            overlay[NOTES_FILENAME] = bodies["04"]
            overlay[GUIDE_FILENAME] = bodies["07"]
        _atomic_write_bundle(paths, overlay, record=record)

    report_paths = storage.study_guide_run_asset_paths(podcast_id, episode_ref)
    result = _result(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=True,
        source_summary_path=str(source_path),
        bundle_dir=str(paths.bundle_dir),
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        planned_reuses=planned_reuses,
        metadata_writes=metadata_writes,
        output_paths={label: str(path) for label, path in file_map.items()},
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        reused=reuse_all,
        warnings=[CACHE_STALE_WARNING],
    )
    try:
        _write_run_report(result)
    except OSError as exc:
        reason = "reused_report_failed" if reuse_all else "published_report_failed"
        raise StudyGuideBundleStateError(reason) from exc
    return result


LINEAGE_INVALID_IDENTITY_MESSAGE = "Invalid explicit episode identity."
LINEAGE_QUERY_ERROR_MESSAGE = "Study-guide lineage could not be inspected safely."


def inspect_study_guide_lineage(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Observe lecture versus recorded summary; never generate, backfill or repair."""
    try:
        _require_explicit_identity(podcast_id, episode_ref)
    except StudyGuideBundleStateError:
        raise ValueError(LINEAGE_INVALID_IDENTITY_MESSAGE) from None

    def result(status: str, reason: str, changed: list[str] | None = None) -> dict[str, Any]:
        return {"podcast_id": podcast_id, "episode_ref": episode_ref, "status": status, "reason": reason,
                "changed_roles": changed or [], "scope": "study_guide_inputs_outputs",
                "read_only": True, "network_access": False,
                "warnings": ["study_guide_scope_only", "non_atomic_observation"]}

    try:
        profile = load_podcast_profile(podcast_id)
    except (PodcastIngestCoreError, ValueError, KeyError, OSError, yaml.YAMLError):
        return result("blocked", "identity_unavailable")
    if profile.summary_profile != REQUIRED_PROFILE:
        return result("blocked", "identity_unavailable")
    try:
        source, _ = _resolve_source_path(podcast_id, episode_ref)
        stem = source.name.removesuffix(".semantic.md")
        paths = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
        _require_bundle_entries(paths.bundle_dir)
        _require_no_recovery_remnants(paths.bundle_dir)
        _require_optional_file(storage.SUMMARIES_DIR, source)
        output_paths = (paths.summary_path, paths.notes_path, paths.guide_path)
        present = [_lstat(path) is not None for path in output_paths]
        receipt_path = paths.bundle_dir / lineage.RECEIPT_FILENAME
        has_receipt = _lstat(receipt_path) is not None
    except StudyGuideBundleStateError as exc:
        reason = exc.reason_code if exc.reason_code in {"unsafe_path", "recovery_required"} else "identity_unavailable"
        return result("blocked", reason)
    except (StudyGuideBundleError, ValueError, UnicodeError, RecursionError):
        return result("blocked", "identity_unavailable")
    if not any(present) and not has_receipt:
        return result("not_generated", "no_study_guide")
    if not all(present):
        return result("blocked", "incomplete_lecture")
    if not has_receipt:
        return result("untracked", "no_record")
    try:
        record = _read_record(receipt_path)
    except lineage.RecordError as exc:
        return result("blocked", exc.reason)
    except StudyGuideBundleStateError:
        return result("blocked", "unsafe_path")
    if not _record_identity_matches(record, podcast_id, episode_ref, stem):
        return result("blocked", "identity_mismatch")
    raw = secure_read_bytes(storage.SUMMARIES_DIR, source, max_bytes=_MAX_SOURCE_BYTES)
    if raw is None:
        return result("blocked", "inputs_unavailable")
    try:
        text = raw.decode("utf-8")
        if _is_finance_shaped(text):
            return result("blocked", "inputs_unavailable")
        observed_request = lineage.canonical_digest(_build_messages(text))
    except (StudyGuideBundleError, UnicodeError):
        return result("blocked", "inputs_unavailable")
    observed_outputs = {}
    for role, path in zip(lineage.OUTPUT_ROLES, output_paths):
        output = secure_read_bytes(storage.STUDY_GUIDES_DIR, path, max_bytes=lineage.MAX_OUTPUT_BYTES)
        if output is None:
            return result("blocked", "outputs_unavailable")
        observed_outputs[role] = lineage.bytes_digest(output)
    changed = []
    if lineage.bytes_digest(raw) != record["input_sha256"]["semantic_summary"]:
        changed.append("semantic_summary")
    if lineage.RECIPE_VERSION != record["recipe_version"]:
        changed.append("recipe")
    if observed_request != record["request_sha256"]:
        changed.append("request")
    changed.extend(role for role in lineage.OUTPUT_ROLES if observed_outputs[role] != record["output_sha256"][role])
    return result("stale", "observed_changes", changed) if changed else result("current", "matches_record")


def describe_study_guide_plan(result: StudyGuideBundleResult) -> dict[str, Any]:
    """Project MCP preview metadata from an existing plan. No filesystem or provider access."""

    bundle_dir = Path(result.bundle_dir)
    lecture_writes = {
        str(bundle_dir / name)
        for name in ("03_full_summary.md", "04_learning_notes.md", "07_final_study_guide.md")
    }
    reports = storage.study_guide_run_asset_paths(result.podcast_id, result.episode_ref)
    return {
        "requires_llm": bool(lecture_writes.intersection(result.planned_writes)),
        "report_writes": [str(reports.json_path), str(reports.markdown_path)],
    }


def result_to_dict(result: StudyGuideBundleResult) -> dict[str, Any]:
    """Serialize a bundle result to metadata-only JSON."""

    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    payload["dry_run"] = not result.confirm
    return payload


def _result(**kwargs: Any) -> StudyGuideBundleResult:
    confirm = bool(kwargs["confirm"])
    return StudyGuideBundleResult(
        run_mode="confirmed" if confirm else "dry-run",
        not_investment_advice=True,
        **kwargs,
    )


def _require_explicit_identity(podcast_id: object, episode_ref: object) -> None:
    if (
        not isinstance(podcast_id, str)
        or not isinstance(episode_ref, str)
        or episode_ref.casefold() in _RESERVED_EPISODE_REFS
        or not storage.is_safe_episode_ref(episode_ref)
    ):
        raise StudyGuideBundleStateError("invalid_identity")
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "title")
    except (TypeError, ValueError) as exc:
        raise StudyGuideBundleStateError("invalid_identity") from exc


def _resolve_source_path(podcast_id: str, episode_ref: str) -> tuple[Path, Path]:
    try:
        transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    except CanonicalTranscriptResolutionError as exc:
        raise StudyGuideBundleStateError("invalid_identity") from exc
    if transcript_paths is None:
        raise StudyGuideBundleError(_MISSING_SUMMARY)
    raw = secure_read_bytes(
        storage.TRANSCRIPTS_DIR,
        transcript_paths.json_path,
        max_bytes=_MAX_TRANSCRIPT_JSON_BYTES,
    )
    if raw is None:
        raise StudyGuideBundleStateError("unsafe_path")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StudyGuideBundleStateError("invalid_identity") from exc
    if not isinstance(payload, dict):
        raise StudyGuideBundleStateError("invalid_identity")
    title = payload.get("title")
    if (
        payload.get("podcast_id") != podcast_id
        or payload.get("episode_ref") != episode_ref
        or not isinstance(title, str)
        or not title.strip()
    ):
        raise StudyGuideBundleStateError("invalid_identity")
    source = canonical_semantic_summary_path_for_title(podcast_id, episode_ref, title)
    if source is None:
        raise StudyGuideBundleError(_MISSING_SUMMARY)
    return source, transcript_paths.json_path


def _is_reparse(value: Any) -> bool:
    attributes = getattr(value, "st_file_attributes", 0) or 0
    return stat.S_ISLNK(value.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _read_record(path: Path) -> dict[str, Any]:
    info = _lstat(path)
    if info is None or info.st_size > lineage.MAX_RECORD_BYTES:
        raise lineage.RecordError("record_unreadable")
    raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, path, max_bytes=lineage.MAX_RECORD_BYTES)
    if raw is None:
        raise lineage.RecordError("record_unreadable")
    return lineage.decode_record(raw)


def _record_identity_matches(record: dict[str, Any], podcast_id: str, episode_ref: str, stem: str) -> bool:
    return (record["podcast_id"] == podcast_id and record["episode_ref"] == episode_ref
            and record["identity_stem_sha256"] == lineage.bytes_digest(stem.encode("utf-8")))


def _preflight_record(path: Path, podcast_id: str, episode_ref: str, stem: str) -> None:
    _require_optional_file(storage.STUDY_GUIDES_DIR, path)
    if _lstat(path) is None:
        return
    try:
        record = _read_record(path)
        if not _record_identity_matches(record, podcast_id, episode_ref, stem):
            raise lineage.RecordError("identity_mismatch")
    except lineage.RecordError as exc:
        raise StudyGuideBundleError("Unrecognized reserved lineage record; operator review is required.") from exc


def _lstat(path: Path):
    """Return no-follow metadata, or None only when this path is absent.

    PermissionError and any other OSError leave the state unknown. Callers must
    not treat that as absence.
    """

    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc


def _require_ancestor_chain(root: Path, leaf: Path) -> None:
    try:
        relative = leaf.relative_to(root)
    except ValueError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc
    current = root
    info = _lstat(current)
    if info is None:
        return
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    for part in relative.parts[:-1]:
        current = current / part
        info = _lstat(current)
        if info is None:
            return
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise StudyGuideBundleStateError("unsafe_path")


def _require_no_recovery_remnants(bundle_dir: Path) -> None:
    for suffix in (".part", ".old", ".wfderive.part", ".wfderive.old"):
        sibling = bundle_dir.with_name(bundle_dir.name + suffix)
        if _lstat(sibling) is not None:
            raise StudyGuideBundleStateError("recovery_required")


def _has_derivation(bundle_dir: Path) -> bool:
    if _lstat(bundle_dir) is None:
        return False
    return any(
        _lstat(bundle_dir / name) is not None
        for name in ("05_prompt_examples.md", "06_apply_to_my_workflow.md")
    )


def _require_bundle_entries(bundle_dir: Path) -> None:
    _require_ancestor_chain(storage.STUDY_GUIDES_DIR, bundle_dir)
    info = _lstat(bundle_dir)
    if info is None:
        return
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    try:
        children = list(bundle_dir.iterdir())
    except OSError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc
    for child in children:
        child_info = _lstat(child)
        if child_info is None or _is_reparse(child_info) or not stat.S_ISREG(child_info.st_mode):
            raise StudyGuideBundleStateError("unsafe_path")


def _require_optional_file(root: Path, path: Path) -> None:
    _require_ancestor_chain(root, path)
    info = _lstat(path)
    if info is None:
        return
    if _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")


def _require_operation_paths(podcast_id: str, episode_ref: str, source_path: Path) -> None:
    _require_ancestor_chain(storage.SUMMARIES_DIR, source_path)
    info = _lstat(source_path)
    if info is not None and (_is_reparse(info) or not stat.S_ISREG(info.st_mode)):
        raise StudyGuideBundleStateError("unsafe_path")
    stem = source_path.name.removesuffix(".semantic.md")
    bundle_dir = storage.study_guide_bundle_paths_from_stem(podcast_id, stem).bundle_dir
    _require_no_recovery_remnants(bundle_dir)
    _require_bundle_entries(bundle_dir)
    _require_optional_file(storage.CORPUS_DIR, storage.corpus_episode_seed_asset_path(podcast_id, episode_ref))
    _find_audio(podcast_id, episode_ref)


def _read_source_text(path: Path) -> str:
    info = _lstat(path)
    if info is None:
        raise StudyGuideBundleError(_MISSING_SUMMARY)
    if _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    if info.st_size > _MAX_SOURCE_BYTES:
        raise StudyGuideBundleError("semantic summary exceeded the read size cap")
    raw = secure_read_bytes(storage.SUMMARIES_DIR, path, max_bytes=_MAX_SOURCE_BYTES)
    if raw is None:
        raise StudyGuideBundleStateError("unsafe_path")
    try:
        return raw.decode("utf-8")
    except UnicodeError as exc:
        raise StudyGuideBundleError("semantic summary is not readable UTF-8") from exc


def _file_map(paths: storage.StudyGuideBundlePaths) -> dict[str, Path]:
    return {
        "00": paths.cover_path,
        "03": paths.summary_path,
        "04": paths.notes_path,
        "07": paths.guide_path,
    }


def _episode_title(podcast_id: str, episode_ref: str, source_path: Path) -> str:
    stem = source_path.name.removesuffix(".semantic.md")
    if "__" in stem:
        return stem.split("__", 1)[1].replace("_", " ")
    seed_path = storage.corpus_episode_seed_asset_path(podcast_id, episode_ref)
    if seed_path.is_file():
        try:
            payload = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return episode_ref


def _find_audio(podcast_id: str, episode_ref: str) -> Path | None:
    audio_dir = storage.AUDIO_DIR / podcast_id
    info = _lstat(audio_dir)
    if info is None:
        return None
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    suffix = {".mp3", ".m4a", ".wav", ".aac", ".flac"}
    matches = sorted(path for path in audio_dir.glob(f"{episode_ref}__*") if path.suffix.lower() in suffix)
    for match in matches:
        _require_optional_file(storage.AUDIO_DIR, match)
    return matches[0] if matches else None


def _read_capped_utf8(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise StudyGuideBundleError(f"semantic summary is unreadable: {path}") from exc
    if len(payload) > _MAX_SOURCE_BYTES:
        raise StudyGuideBundleError("semantic summary exceeded the read size cap")
    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise StudyGuideBundleError("semantic summary is not readable UTF-8") from exc


def _is_readable(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc
    if _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    try:
        _read_capped_utf8(path)
    except StudyGuideBundleStateError:
        raise
    except StudyGuideBundleError as exc:
        if isinstance(exc.__cause__, OSError):
            raise StudyGuideBundleStateError("unsafe_path") from exc
        return False
    return True


def _is_finance_shaped(text: str) -> bool:
    headings = _heading_titles(text)
    return any(name in headings for name in FINANCE_HEADINGS)


def _heading_titles(text: str) -> set[str]:
    titles: set[str] = set()
    for match in _HEADING.finditer(text):
        titles.add(match.group(1).strip())
    return titles


def _source_window(source_text: str) -> str:
    if _CHUNK_SPLIT.search(source_text) is None:
        raise StudyGuideBundleError("source semantic summary is missing the Chunk Summaries heading")
    return _CHUNK_SPLIT.split(source_text, maxsplit=1)[0]


def _build_messages(source_text: str) -> list[dict[str, str]]:
    window = _source_window(source_text)
    return [
        {"role": "system", "content": STUDY_GUIDE_PROFILE.system_message},
        {
            "role": "user",
            "content": STUDY_GUIDE_PROFILE.user_instructions + "\n\n" + window,
        },
    ]


def _parse_bundle_payload(raw: str) -> dict[str, str]:
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StudyGuideBundleError("study-guide model output is not JSON") from exc
    if not isinstance(payload, dict):
        raise StudyGuideBundleError("study-guide model output is not an object")
    missing = [key for key in BUNDLE_KEYS if key not in payload]
    if missing:
        raise StudyGuideBundleError(f"study-guide model output missing keys: {', '.join(missing)}")
    parsed: dict[str, str] = {}
    for key in BUNDLE_KEYS:
        value = payload[key]
        if not isinstance(value, str) or not value.strip():
            raise StudyGuideBundleError(f"study-guide model output {key} is empty")
        parsed[key] = value
    return parsed


def _validate_generated(parsed: dict[str, str], source_text: str) -> None:
    required = {
        "03_full_summary": STUDY_GUIDE_PROFILE.summary_headings,
        "04_learning_notes": STUDY_GUIDE_PROFILE.notes_headings,
        "07_final_study_guide": STUDY_GUIDE_PROFILE.guide_headings,
    }
    source_window = _source_window(source_text)
    for key, headings in required.items():
        body = parsed[key]
        titles = _heading_titles(body)
        missing = [heading for heading in headings if not _has_heading(titles, heading) and heading not in body]
        if missing:
            raise StudyGuideBundleError(f"{key} missing required headings: {', '.join(missing)}")
        if any(_has_heading(titles, heading) for heading in FINANCE_HEADINGS):
            raise StudyGuideBundleError(f"{key} contains finance headings")
        for marker in WORKFLOW_MARKERS:
            if marker in body and marker not in source_window:
                raise StudyGuideBundleError(f"{key} invents workflow marker {marker!r}")
        if matched_investment_advice_guard(body) is not None:
            raise StudyGuideBundleError(f"{key} failed prohibited_advice")
        source_clocks = set(_CLOCK.findall(source_window))
        for stamp in _TIMESTAMP.findall(body) + [f"[{clock}]" for clock in _CLOCK.findall(body)]:
            clocks = _CLOCK.findall(stamp)
            if clocks and any(clock not in source_clocks for clock in clocks):
                raise StudyGuideBundleError(f"{key} uses timestamp {stamp} that is not in the source summary")


def _has_heading(titles: set[str], expected: str) -> bool:
    for title in titles:
        if title == expected or title.endswith(expected) or expected in title:
            return True
    return False


def _render_cover(
    *,
    podcast_id: str,
    episode_ref: str,
    title: str,
    seed_path: Path,
    audio_path: Path | None,
) -> str:
    seed: dict[str, Any] = {}
    if seed_path.is_file():
        try:
            loaded = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if isinstance(loaded, dict):
            seed = loaded
    lines = [
        "# Video Info",
        "",
        f"- Podcast ID: `{podcast_id}`",
        f"- Episode: `{episode_ref}`",
        f"- Title: `{title}`",
    ]
    for key, label in (
        ("seed_source", "Source"),
        ("selector", "Selector"),
        ("published_at", "Published"),
        ("duration", "Duration"),
    ):
        value = seed.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(f"- {label}: `{value}`")
    if audio_path is not None and audio_path.is_file():
        size = audio_path.stat().st_size
        lines.append(f"- Audio: `{audio_path.name}` (`{size}` bytes)")
    lines.append("")
    return "\n".join(lines)


def _snapshot_preserved_names(dest: Path) -> tuple[bool, list[str]]:
    """Return whether dest exists and the entry names that must be preserved.

    A missing directory is an empty new bundle. An unreadable directory, a
    non-directory, or a failed listing is refusal — never an empty preserve list.
    """

    info = _lstat(dest)
    if info is None:
        return False, []
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise StudyGuideBundleStateError("unsafe_path")
    try:
        names = [entry.name for entry in os.scandir(dest)]
    except OSError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc
    return True, names


def _rollback_moved_bundle(old: Path, dest: Path) -> bool:
    """Move this attempt's backup back. Success is the rename itself."""

    try:
        old.rename(dest)
    except OSError:
        return False
    return True


def _remove_staging_if_confirmed_safe(part: Path) -> None:
    """Remove staging only when this attempt can confirm it is a normal directory."""

    try:
        info = part.lstat()
    except OSError:
        return
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        return
    try:
        shutil.rmtree(part)
    except OSError:
        return


def _cleanup_committed_backup(old: Path, *, created: bool) -> None:
    """After commit, clean only the backup this attempt created.

    FileNotFoundError confirms absence. Any other stat failure, or a backup this
    attempt did not create, keeps the new directory and reports cleanup failure.
    """

    try:
        info = old.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise StudyGuideBundleStateError("published_cleanup_failed") from exc
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode) or not created:
        raise StudyGuideBundleStateError("published_cleanup_failed")
    try:
        shutil.rmtree(old)
    except OSError as exc:
        raise StudyGuideBundleStateError("published_cleanup_failed") from exc


def _atomic_write_bundle(paths: storage.StudyGuideBundlePaths, files: dict[str, str],
                         *, record: dict[str, Any] | None = None) -> None:
    dest = paths.bundle_dir
    part = dest.with_name(dest.name + ".part")
    old = dest.with_name(dest.name + ".old")
    _require_no_recovery_remnants(dest)
    _require_ancestor_chain(storage.STUDY_GUIDES_DIR, dest)
    if record is not None:
        _preflight_record(dest / lineage.RECEIPT_FILENAME, record["podcast_id"], record["episode_ref"], dest.name)
    dest_existed, preserved = _snapshot_preserved_names(dest)
    # moved/committed record this attempt. Later stat results must not guess them.
    moved = False
    committed = False
    created_staging = False
    try:
        part.mkdir(parents=True)
        created_staging = True
        for name in preserved:
            if record is not None and name == lineage.RECEIPT_FILENAME:
                continue
            child = dest / name
            if not _is_safe_regular_file(child):
                raise StudyGuideBundleStateError("unsafe_path")
            _stream_copy(child, part / name)
        for name, content in files.items():
            (part / name).write_text(content, encoding="utf-8")
        if record is not None:
            completed = dict(record)
            completed["output_sha256"] = {}
            for role, name in zip(lineage.OUTPUT_ROLES, (SUMMARY_FILENAME, NOTES_FILENAME, GUIDE_FILENAME)):
                raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, part / name, max_bytes=lineage.MAX_OUTPUT_BYTES)
                if raw is None:
                    raise StudyGuideBundleStateError("publish_failed")
                completed["output_sha256"][role] = lineage.bytes_digest(raw)
            (part / lineage.RECEIPT_FILENAME).write_bytes(lineage.encode_record(completed))
        if dest_existed:
            dest.rename(old)
            moved = True
        part.rename(dest)
        committed = True
    except StudyGuideBundleStateError:
        if moved and not committed:
            if not _rollback_moved_bundle(old, dest):
                raise StudyGuideBundleStateError("rollback_failed")
            if created_staging:
                _remove_staging_if_confirmed_safe(part)
            raise StudyGuideBundleStateError("publish_failed")
        if created_staging and not committed:
            _remove_staging_if_confirmed_safe(part)
        raise
    except OSError as exc:
        if committed:
            raise StudyGuideBundleStateError("published_cleanup_failed") from exc
        if moved:
            if _rollback_moved_bundle(old, dest):
                if created_staging:
                    _remove_staging_if_confirmed_safe(part)
                raise StudyGuideBundleStateError("publish_failed") from exc
            raise StudyGuideBundleStateError("rollback_failed") from exc
        if created_staging:
            _remove_staging_if_confirmed_safe(part)
        raise StudyGuideBundleStateError("publish_failed") from exc
    _cleanup_committed_backup(old, created=moved)


def _is_safe_regular_file(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError as exc:
        raise StudyGuideBundleStateError("unsafe_path") from exc
    if stat.S_ISLNK(info.st_mode):
        return False
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if attributes & reparse:
        return False
    return stat.S_ISREG(info.st_mode)


def _stream_copy(source: Path, target: Path) -> None:
    with source.open("rb") as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)


def _write_run_report(result: StudyGuideBundleResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = result_to_dict(result)
    markdown = "\n".join(
        [
            f"# Study-guide run — {result.podcast_id} / {result.episode_ref}",
            "",
            f"- run_mode: {result.run_mode}",
            f"- reused: {result.reused}",
            f"- source: {result.source_summary_path}",
            "",
        ]
    )
    write_part_staged_report_pair(
        result.report_json_path,
        result.report_markdown_path,
        payload,
        markdown,
    )


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None
