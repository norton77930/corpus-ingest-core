"""Dry-run-first 05/06 workflow derivation runner.

Reads an available Spec 038 lecture plus operator context. Never sends
transcript text to a provider. Never rewrites the lecture four.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from dataclasses import asdict
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml

from . import storage, workflow_derivation_lineage as lineage
from .config import load_podcast_profile
from .errors import PodcastIngestCoreError, WorkflowDerivationError, WorkflowDerivationStateError
from .llm_provider import create_provider, require_exact_api_cost_ack
from .models import WorkflowDerivationResult
from .report_safety import matched_investment_advice_guard
from .run_report_io import write_part_staged_report_pair
from .canonical_transcript import CanonicalTranscriptResolutionError, resolve_canonical_transcript_asset_paths
from .secure_local_snapshot import secure_read_bytes
from .semantic_summary_identity import canonical_semantic_summary_path_for_title
from .study_guide_profiles import WORKFLOW_MARKERS
from .summary_profiles import LEARNING_NOTES
from .workflow_derivation_profiles import (
    APPLY_FILENAME,
    APPLY_HEADINGS,
    APPLY_KEY,
    BUNDLE_KEYS,
    PROMPT_EXAMPLES_FILENAME,
    PROMPT_EXAMPLES_HEADINGS,
    PROMPT_EXAMPLES_KEY,
    WORKFLOW_DERIVATION_PROFILE,
)

CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. This workflow never rebuilds it automatically."
)
DEFAULT_CONTEXT_PATH = Path(__file__).resolve().parents[2] / "config" / "operator_workflow.yaml"
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
REQUIRED_PROFILE = LEARNING_NOTES


def run_workflow_derivation(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
    workflow_context: str | Path | None = None,
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
) -> WorkflowDerivationResult:
    """Plan or write 05/06 for one learning-notes lecture."""

    _require_explicit_identity(podcast_id, episode_ref)
    profile = load_podcast_profile(podcast_id)
    if profile.summary_profile != REQUIRED_PROFILE:
        raise WorkflowDerivationError(
            f"workflow derivation requires summary_profile={REQUIRED_PROFILE}; got {profile.summary_profile!r}"
        )

    context_path = Path(workflow_context) if workflow_context else DEFAULT_CONTEXT_PATH
    allowed_tools = _load_context(context_path)

    source_path = _resolve_source_path(podcast_id, episode_ref)
    if source_path is None or not _require_optional_file(storage.SUMMARIES_DIR, source_path):
        raise WorkflowDerivationError("canonical learning-notes semantic summary is missing")
    stem = source_path.name.removesuffix(".semantic.md")
    lecture = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    _require_no_recovery_remnants(lecture.bundle_dir)
    _require_bundle_entries(lecture.bundle_dir)
    _require_report_paths(podcast_id, episode_ref)
    _require_lecture(lecture)

    paths = storage.workflow_derivation_paths_from_stem(podcast_id, stem)
    existing = [path for path in (paths.prompt_examples_path, paths.apply_path) if path.is_file()]
    complete = len(existing) == 2
    if existing and not complete and not force:
        raise WorkflowDerivationError("incomplete workflow derivation pair; pass force=true to replace")
    reuse_all = complete and not force
    receipt_path = paths.bundle_dir / lineage.RECEIPT_FILENAME
    if not reuse_all:
        _preflight_record(receipt_path, podcast_id, episode_ref, stem)

    planned_reads = [
        str(lecture.summary_path),
        str(lecture.notes_path),
        str(lecture.guide_path),
        str(context_path),
    ]
    if not reuse_all and receipt_path.is_file():
        planned_reads.append(str(receipt_path))
    if reuse_all:
        planned_writes: list[str] = []
        planned_reuses = [str(paths.prompt_examples_path), str(paths.apply_path)]
    else:
        planned_writes = [str(paths.prompt_examples_path), str(paths.apply_path)]
        planned_reuses = []

    metadata_writes = [] if reuse_all else [str(paths.bundle_dir / lineage.RECEIPT_FILENAME)]

    if not confirm:
        return _result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            lecture_dir=str(paths.bundle_dir),
            context_path=str(context_path),
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            planned_reuses=planned_reuses,
            metadata_writes=metadata_writes,
            prompt_examples_path=None,
            apply_path=None,
            report_json_path=None,
            report_markdown_path=None,
            reused=reuse_all,
            warnings=[CACHE_STALE_WARNING] if planned_writes else [],
        )

    if not reuse_all:
        require_exact_api_cost_ack(api_cost_ack)
        lecture_text = {
            "03": _read_capped(lecture.summary_path),
            "04": _read_capped(lecture.notes_path),
            "07": _read_capped(lecture.guide_path),
        }
        messages = _build_messages(lecture_text, allowed_tools)
        record = lineage.generation_record(
            podcast_id, episode_ref, stem, "custom" if workflow_context else "default",
            lecture_text, allowed_tools, messages,
        )
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
        bodies = _parse_payload(raw)
        _validate_generated(bodies, allowed_tools)
        _atomic_write_pair(paths, bodies, record)

    report_paths = storage.workflow_derivation_run_asset_paths(podcast_id, episode_ref)
    result = _result(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=True,
        lecture_dir=str(paths.bundle_dir),
        context_path=str(context_path),
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        planned_reuses=planned_reuses,
        metadata_writes=metadata_writes,
        prompt_examples_path=str(paths.prompt_examples_path),
        apply_path=str(paths.apply_path),
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        reused=reuse_all,
        warnings=[CACHE_STALE_WARNING] if planned_writes else [],
    )
    _write_run_report(result)
    return result


LINEAGE_INVALID_IDENTITY_MESSAGE = "Invalid explicit episode identity."
LINEAGE_QUERY_ERROR_MESSAGE = "Workflow derivation lineage could not be inspected safely."


def _inspection_result(podcast_id: str, episode_ref: str, status: str, reason: str,
                       changed_roles: list[str] | None = None) -> dict[str, Any]:
    return {"podcast_id": podcast_id, "episode_ref": episode_ref, "status": status, "reason": reason,
            "changed_roles": changed_roles or [], "scope": "workflow_derivation_inputs_outputs",
            "read_only": True, "network_access": False,
            "warnings": ["derivation_scope_only", "non_atomic_observation"]}


def inspect_workflow_derivation_lineage(podcast_id: str, episode_ref: str) -> dict[str, Any]:
    """Observe one derivation's recorded inputs/outputs; never generate or repair."""
    try:
        _require_explicit_identity(podcast_id, episode_ref)
    except WorkflowDerivationStateError:
        raise ValueError(LINEAGE_INVALID_IDENTITY_MESSAGE) from None

    def result(status: str, reason: str, changed: list[str] | None = None) -> dict[str, Any]:
        return _inspection_result(podcast_id, episode_ref, status, reason, changed)

    try:
        profile = load_podcast_profile(podcast_id)
    except (PodcastIngestCoreError, ValueError, KeyError, OSError, yaml.YAMLError):
        return result("blocked", "identity_unavailable")
    if profile.summary_profile != REQUIRED_PROFILE:
        return result("blocked", "identity_unavailable")
    try:
        source = _resolve_source_path(podcast_id, episode_ref)
        if source is None:
            return result("blocked", "identity_unavailable")
        _require_optional_file(storage.SUMMARIES_DIR, source)
        stem = source.name.removesuffix(".semantic.md")
        paths = storage.workflow_derivation_paths_from_stem(podcast_id, stem)
        _require_bundle_entries(paths.bundle_dir)
        _require_no_recovery_remnants(paths.bundle_dir)
        pair = [_require_optional_file(storage.STUDY_GUIDES_DIR, p)
                for p in (paths.prompt_examples_path, paths.apply_path)]
        receipt_path = paths.bundle_dir / lineage.RECEIPT_FILENAME
        has_receipt = _require_optional_file(storage.STUDY_GUIDES_DIR, receipt_path)
    except WorkflowDerivationStateError as exc:
        reason = exc.reason_code if exc.reason_code in {"unsafe_path", "recovery_required"} else "identity_unavailable"
        return result("blocked", reason)
    if not any(pair) and not has_receipt:
        return result("not_generated", "no_derivation")
    if not all(pair):
        return result("blocked", "incomplete_pair")
    if not has_receipt:
        return result("untracked", "no_record")
    try:
        record = _read_record(receipt_path)
    except lineage.RecordError as exc:
        return result("blocked", exc.reason)
    except WorkflowDerivationStateError:
        return result("blocked", "unsafe_path")
    if not _record_identity_matches(record, podcast_id, episode_ref, stem):
        return result("blocked", "identity_mismatch")
    if record["context_origin"] == "custom":
        return result("not_evaluated", "custom_context")
    lecture = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    try:
        text = {"03": _observe_lecture(lecture.summary_path), "04": _observe_lecture(lecture.notes_path),
                "07": _observe_lecture(lecture.guide_path)}
        tools = _load_context(DEFAULT_CONTEXT_PATH)
        observed_inputs = lineage.input_digests(text, tools)
        observed_request = lineage.canonical_digest(_build_messages(text, tools))
    except WorkflowDerivationStateError as exc:
        return result("blocked", "unsafe_path" if exc.reason_code == "unsafe_path" else "inputs_unavailable")
    except (WorkflowDerivationError, UnicodeError):
        return result("blocked", "inputs_unavailable")
    output_digests = {}
    for role, path in zip(lineage.OUTPUT_ROLES, (paths.prompt_examples_path, paths.apply_path)):
        raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, path, max_bytes=lineage.MAX_OUTPUT_BYTES)
        if raw is None:
            return result("blocked", "outputs_unavailable")
        output_digests[role] = lineage.bytes_digest(raw)
    changed = [role for role in lineage.INPUT_ROLES if observed_inputs[role] != record["input_sha256"][role]]
    if record["recipe_version"] != lineage.RECIPE_VERSION:
        changed.append("recipe")
    if observed_request != record["request_sha256"]:
        changed.append("request")
    changed.extend(role for role in lineage.OUTPUT_ROLES if output_digests[role] != record["output_sha256"][role])
    return result("stale", "observed_changes", changed) if changed else result("current", "matches_record")


def _observe_lecture(path: Path) -> str:
    """Classify safe-but-unreadable observations without changing runner errors."""
    if not _require_optional_file(storage.STUDY_GUIDES_DIR, path):
        raise WorkflowDerivationError("Comparison input unavailable.")
    raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, path, max_bytes=_MAX_SOURCE_BYTES)
    if raw is None:
        raise WorkflowDerivationError("Comparison input unavailable.")
    try:
        return raw.decode("utf-8")
    except UnicodeError:
        raise WorkflowDerivationError("Comparison input unavailable.") from None


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
    if not _require_optional_file(storage.STUDY_GUIDES_DIR, path):
        return
    try:
        record = _read_record(path)
        if not _record_identity_matches(record, podcast_id, episode_ref, stem):
            raise lineage.RecordError("identity_mismatch")
    except lineage.RecordError as exc:
        raise WorkflowDerivationError("Unrecognized reserved lineage record; operator review is required.") from exc


def _lstat(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise WorkflowDerivationStateError("unsafe_path") from exc


def _is_reparse(info) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _require_ancestor_chain(root: Path, leaf: Path) -> None:
    try:
        relative = leaf.relative_to(root)
    except ValueError as exc:
        raise WorkflowDerivationStateError("unsafe_path") from exc
    current = root
    for part in (None, *relative.parts[:-1]):
        if part is not None:
            current = current / part
        info = _lstat(current)
        if info is None:
            return
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise WorkflowDerivationStateError("unsafe_path")


def _require_optional_file(root: Path, path: Path) -> bool:
    _require_ancestor_chain(root, path)
    info = _lstat(path)
    if info is None:
        return False
    if _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise WorkflowDerivationStateError("unsafe_path")
    return True


def _require_bundle_entries(dest: Path) -> list[str]:
    _require_ancestor_chain(storage.STUDY_GUIDES_DIR, dest)
    info = _lstat(dest)
    if info is None:
        return []
    if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
        raise WorkflowDerivationStateError("unsafe_path")
    try:
        children = list(dest.iterdir())
    except OSError as exc:
        raise WorkflowDerivationStateError("unsafe_path") from exc
    for child in children:
        if not _require_optional_file(storage.STUDY_GUIDES_DIR, child):
            raise WorkflowDerivationStateError("unsafe_path")
    return [child.name for child in children]


def _require_report_paths(podcast_id: str, episode_ref: str) -> None:
    paths = storage.workflow_derivation_run_asset_paths(podcast_id, episode_ref)
    for path in (paths.json_path, paths.markdown_path):
        _require_optional_file(storage.CORPUS_DIR, path)
        _require_optional_file(storage.CORPUS_DIR, path.with_name(path.name + ".part"))


def _context_file(path: Path) -> Path:
    raw = str(path)
    windows = PureWindowsPath(raw)
    if (".." in raw.replace(chr(92), "/").split("/")
            or raw.startswith(("//", chr(92) * 2))
            or (windows.drive and not windows.root)):
        raise WorkflowDerivationStateError("unsafe_path")
    absolute = Path(os.path.abspath(path))
    if not _require_optional_file(Path(absolute.anchor), absolute):
        raise WorkflowDerivationError(f"operator workflow context is missing: {path}")
    return absolute


def _require_no_recovery_remnants(dest: Path) -> None:
    _require_ancestor_chain(storage.STUDY_GUIDES_DIR, dest)
    for suffix in (".part", ".old", ".wfderive.part", ".wfderive.old"):
        if _lstat(dest.with_name(dest.name + suffix)) is not None:
            raise WorkflowDerivationStateError("recovery_required")


def _require_explicit_identity(podcast_id: object, episode_ref: object) -> None:
    if (not isinstance(podcast_id, str) or not podcast_id or podcast_id != podcast_id.strip()
            or not isinstance(episode_ref, str) or episode_ref != episode_ref.strip()
            or episode_ref.casefold() in {"latest", "next"}
            or not storage.is_safe_episode_ref(episode_ref)):
        raise WorkflowDerivationStateError("invalid_identity")
    try:
        storage.study_guide_bundle_paths(podcast_id, episode_ref, "title")
    except (TypeError, ValueError) as exc:
        raise WorkflowDerivationStateError("invalid_identity") from exc


def _resolve_source_path(podcast_id: str, episode_ref: str) -> Path | None:
    directory = storage.TRANSCRIPTS_DIR / podcast_id
    _require_ancestor_chain(storage.TRANSCRIPTS_DIR, directory / "metadata.json")
    if _lstat(directory) is None:
        return None
    try:
        candidates = list(directory.iterdir())
    except OSError as exc:
        raise WorkflowDerivationStateError("unsafe_path") from exc
    for candidate in candidates:
        if candidate.name.startswith(episode_ref + "__") and candidate.suffix == ".json":
            if not _require_optional_file(storage.TRANSCRIPTS_DIR, candidate):
                raise WorkflowDerivationStateError("unsafe_path")
    try:
        paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    except CanonicalTranscriptResolutionError as exc:
        raise WorkflowDerivationStateError("invalid_identity") from exc
    if paths is None:
        return None
    raw = secure_read_bytes(storage.TRANSCRIPTS_DIR, paths.json_path, max_bytes=64 * 1024 * 1024)
    if raw is None:
        raise WorkflowDerivationStateError("unsafe_path")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise WorkflowDerivationStateError("invalid_identity") from exc
    if (not isinstance(payload, dict) or payload.get("podcast_id") != podcast_id
            or payload.get("episode_ref") != episode_ref
            or not isinstance(payload.get("title"), str) or not payload["title"].strip()):
        raise WorkflowDerivationStateError("invalid_identity")
    return canonical_semantic_summary_path_for_title(podcast_id, episode_ref, payload["title"])


def result_to_dict(result: WorkflowDerivationResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    payload["dry_run"] = not result.confirm
    return payload


def _result(**kwargs: Any) -> WorkflowDerivationResult:
    confirm = bool(kwargs["confirm"])
    return WorkflowDerivationResult(
        run_mode="confirmed" if confirm else "preview",
        not_investment_advice=True,
        **kwargs,
    )


def _load_context(path: Path) -> list[str]:
    checked = _context_file(path)
    try:
        with checked.open("rb") as stream:
            payload = stream.read(_MAX_SOURCE_BYTES + 1)
        if len(payload) > _MAX_SOURCE_BYTES:
            raise WorkflowDerivationError("operator workflow context exceeded the read size cap")
        raw = yaml.safe_load(payload.decode("utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise WorkflowDerivationError(f"operator workflow context is unreadable: {path}") from exc
    if not isinstance(raw, dict):
        raise WorkflowDerivationError("operator workflow context must be a mapping")
    tools = raw.get("allowed_tools")
    if not isinstance(tools, list) or not tools or not all(isinstance(item, str) and item.strip() for item in tools):
        raise WorkflowDerivationError("operator workflow context requires a non-empty allowed_tools list")
    return [item.strip() for item in tools]


def _require_lecture(lecture: storage.StudyGuideBundlePaths) -> None:
    files = (
        lecture.cover_path,
        lecture.summary_path,
        lecture.notes_path,
        lecture.guide_path,
    )
    existing = [path for path in files if path.is_file()]
    if len(existing) < 4:
        raise WorkflowDerivationError("study-guide lecture is missing or partial; generate Spec 038 first")
    for path in files:
        _read_capped(path)


def _read_capped(path: Path) -> str:
    if not _require_optional_file(storage.STUDY_GUIDES_DIR, path):
        raise WorkflowDerivationError(f"unreadable: {path}")
    info = _lstat(path)
    if info is None:
        raise WorkflowDerivationStateError("unsafe_path")
    if info.st_size > _MAX_SOURCE_BYTES:
        raise WorkflowDerivationError(f"exceeded read size cap: {path}")
    payload = secure_read_bytes(storage.STUDY_GUIDES_DIR, path, max_bytes=_MAX_SOURCE_BYTES)
    if payload is None:
        raise WorkflowDerivationStateError("unsafe_path")
    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise WorkflowDerivationError(f"not UTF-8: {path}") from exc


def _build_messages(lecture_text: dict[str, str], allowed_tools: list[str]) -> list[dict[str, str]]:
    tools = ", ".join(allowed_tools)
    user = (
        f"{WORKFLOW_DERIVATION_PROFILE.user_instructions}\n\n"
        f"allowed_tools: {tools}\n\n"
        f"## 03\n{lecture_text['03']}\n\n"
        f"## 04\n{lecture_text['04']}\n\n"
        f"## 07\n{lecture_text['07']}\n"
    )
    return [
        {"role": "system", "content": WORKFLOW_DERIVATION_PROFILE.system_message},
        {"role": "user", "content": user},
    ]


def _parse_payload(raw: str) -> dict[str, str]:
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkflowDerivationError("workflow derivation output is not JSON") from exc
    if not isinstance(parsed, dict):
        raise WorkflowDerivationError("workflow derivation output is not an object")
    if set(parsed) != set(BUNDLE_KEYS):
        raise WorkflowDerivationError("workflow derivation output keys are wrong")
    bodies: dict[str, str] = {}
    for key in BUNDLE_KEYS:
        value = parsed[key]
        if not isinstance(value, str) or not value.strip():
            raise WorkflowDerivationError(f"workflow derivation output {key} is empty")
        bodies[key] = value
    return bodies


def _validate_generated(bodies: dict[str, str], allowed_tools: list[str]) -> None:
    for key, headings in (
        (PROMPT_EXAMPLES_KEY, PROMPT_EXAMPLES_HEADINGS),
        (APPLY_KEY, APPLY_HEADINGS),
    ):
        text = bodies[key]
        try:
            text.encode("utf-8")
        except UnicodeError as exc:
            raise WorkflowDerivationError("workflow derivation output is not encodable UTF-8") from exc
        for heading in headings:
            if heading not in text:
                raise WorkflowDerivationError(f"{key} missing heading {heading}")
        if matched_investment_advice_guard(text) is not None:
            raise WorkflowDerivationError(f"{key} failed prohibited_advice")
        forbidden_tools = []
        for marker in (*WORKFLOW_MARKERS, "spec-kit"):
            if marker in text and marker not in allowed_tools:
                forbidden_tools.append(marker)
        if forbidden_tools:
            raise WorkflowDerivationError(f"{key} advises tools absent from context: {forbidden_tools}")


def _stream_copy(source: Path, target: Path) -> None:
    with source.open("rb") as reader, target.open("wb") as writer:
        shutil.copyfileobj(reader, writer, length=1024 * 1024)


def _discard_owned_staging(part: Path) -> None:
    # Best effort only for a positively inspected directory created by this call.
    try:
        info = _lstat(part)
        if info is None or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            return
        _require_bundle_entries(part)
        shutil.rmtree(part)
    except (OSError, WorkflowDerivationStateError):
        return


def _restore_owned_backup(old: Path, dest: Path) -> bool:
    try:
        if _lstat(dest) is not None:
            return False
        old.rename(dest)
    except (OSError, WorkflowDerivationStateError):
        return False
    return True


def _cleanup_committed_backup(old: Path) -> None:
    try:
        info = _lstat(old)
        if info is None:
            return
        if _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise WorkflowDerivationStateError("published_cleanup_failed")
        _require_bundle_entries(old)
        shutil.rmtree(old)
    except (OSError, WorkflowDerivationStateError) as exc:
        raise WorkflowDerivationStateError("published_cleanup_failed") from exc


def _atomic_write_pair(paths: storage.WorkflowDerivationPaths, bodies: dict[str, str],
                       record: dict[str, Any]) -> None:
    """Replace 05/06 and its owned lineage receipt in one directory publication.

    Writers are externally serialized. The second rename is the commit point;
    neither continuous availability nor power-loss durability is promised.
    """
    dest = paths.bundle_dir
    _require_no_recovery_remnants(dest)
    names = _require_bundle_entries(dest)
    _preflight_record(dest / lineage.RECEIPT_FILENAME, record["podcast_id"], record["episode_ref"], dest.name)
    if _lstat(dest) is None:
        raise WorkflowDerivationStateError("unsafe_path")
    part = dest.with_name(dest.name + ".wfderive.part")
    old = dest.with_name(dest.name + ".wfderive.old")
    mapping = {
        PROMPT_EXAMPLES_FILENAME: bodies[PROMPT_EXAMPLES_KEY],
        APPLY_FILENAME: bodies[APPLY_KEY],
    }
    created_staging = moved = committed = False
    try:
        try:
            part.mkdir()
        except FileExistsError as exc:
            raise WorkflowDerivationStateError("recovery_required") from exc
        created_staging = True
        for name in names:
            child = dest / name
            if not _require_optional_file(storage.STUDY_GUIDES_DIR, child):
                raise WorkflowDerivationStateError("unsafe_path")
            if name not in mapping and name != lineage.RECEIPT_FILENAME:
                _stream_copy(child, part / name)
        for name, content in mapping.items():
            (part / name).write_text(content, encoding="utf-8")
        outputs = {}
        for role, name in zip(lineage.OUTPUT_ROLES, (PROMPT_EXAMPLES_FILENAME, APPLY_FILENAME)):
            raw = secure_read_bytes(storage.STUDY_GUIDES_DIR, part / name, max_bytes=lineage.MAX_OUTPUT_BYTES)
            if raw is None:
                raise WorkflowDerivationStateError("publish_failed")
            outputs[role] = lineage.bytes_digest(raw)
        staged_record = {**record, "output_sha256": outputs}
        (part / lineage.RECEIPT_FILENAME).write_bytes(lineage.encode_record(staged_record))
        dest.rename(old)
        moved = True
        part.rename(dest)
        committed = True
    except (OSError, lineage.RecordError, WorkflowDerivationStateError) as exc:
        if committed:
            raise WorkflowDerivationStateError("published_cleanup_failed") from exc
        if moved:
            if not _restore_owned_backup(old, dest):
                raise WorkflowDerivationStateError("rollback_failed") from exc
            if created_staging:
                _discard_owned_staging(part)
            raise WorkflowDerivationStateError("publish_failed") from exc
        if created_staging:
            _discard_owned_staging(part)
        if isinstance(exc, WorkflowDerivationStateError):
            raise
        raise WorkflowDerivationStateError("publish_failed") from exc
    _cleanup_committed_backup(old)


def _write_run_report(result: WorkflowDerivationResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    markdown = "\n".join(
        [
            f"# Workflow derivation run — {result.podcast_id} / {result.episode_ref}",
            "",
            f"- run_mode: {result.run_mode}",
            f"- reused: {result.reused}",
            f"- context: {result.context_path}",
            "",
        ]
    )
    try:
        _require_report_paths(result.podcast_id, result.episode_ref)
        write_part_staged_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            result_to_dict(result),
            markdown,
        )
    except (OSError, WorkflowDerivationError) as exc:
        reason = "reused_report_failed" if result.reused else "published_report_failed"
        raise WorkflowDerivationStateError(reason) from exc


def _path_or_none(path: Path | None) -> str | None:
    return None if path is None else str(path)
