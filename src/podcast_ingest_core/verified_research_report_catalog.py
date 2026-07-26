"""Read-only, bounded catalog for verified research report bundles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any
import unicodedata

from . import storage
from .errors import VerifiedResearchReportCatalogInputError
from .models import (
    VerifiedResearchReportCatalogInspection,
    VerifiedResearchReportCatalogItem,
    VerifiedResearchReportCatalogPage,
)
from .verified_research_report import REPORT_SCHEMA_VERSION


_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100
_ENTRY_CAP = 1_000
_MAX_MANIFEST_BYTES = 1_048_576
_MAX_REPORT_BYTES = 16 * 1_024 * 1_024
_MAX_QUERY_LENGTH = 256
_BUNDLE_FILENAMES = frozenset({"manifest.json", "report.json", "report.md"})
_RESERVED_EPISODE_REFS = frozenset({"latest", "next"})
_VERSION_PATTERN = re.compile(r"^v1-([a-f0-9]{64})$")


@dataclass(frozen=True)
class _PathIdentity:
    device: int
    inode: int
    mode: int


@dataclass(frozen=True)
class _CatalogRoot:
    path: Path
    identity: _PathIdentity


@dataclass(frozen=True)
class _SecureSnapshot:
    raw: bytes
    identity: _PathIdentity


def list_verified_research_reports(
    *,
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> VerifiedResearchReportCatalogPage:
    """List bounded, manifest-derived summaries of canonical local bundles."""

    normalized_podcast_id = _validate_optional_identifier(podcast_id, "podcast_id")
    normalized_episode_ref = _validate_optional_identifier(episode_ref, "episode_ref")
    normalized_limit = _validate_limit(limit)
    root, root_status = _catalog_root()
    if root is None:
        traversal_status = "complete" if root_status == "missing" else "incomplete_catalog_root"
        return _page([], normalized_limit, root_status, traversal_status)

    summaries, traversal_status = _discover_summaries(
        root,
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
    )
    if traversal_status != "complete":
        summaries = []
    summaries.sort(key=lambda item: (item.podcast_id, item.episode_ref, item.report_version))
    return _page(summaries[:normalized_limit], normalized_limit, root_status, traversal_status)


def search_verified_research_reports(
    query: str,
    *,
    podcast_id: str | None = None,
    episode_ref: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> VerifiedResearchReportCatalogPage:
    """Search only normalized safe locator metadata from eligible manifests."""

    normalized_query = _normalize_query(query)
    normalized_podcast_id = _validate_optional_identifier(podcast_id, "podcast_id")
    normalized_episode_ref = _validate_optional_identifier(episode_ref, "episode_ref")
    normalized_limit = _validate_limit(limit)
    root, root_status = _catalog_root()
    if root is None:
        traversal_status = "complete" if root_status == "missing" else "incomplete_catalog_root"
        return _page([], normalized_limit, root_status, traversal_status)

    summaries, traversal_status = _discover_summaries(
        root,
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
    )
    if traversal_status != "complete":
        summaries = []
    matches = [item for item in summaries if _matches_query(item, normalized_query)]
    matches.sort(key=lambda item: (item.podcast_id, item.episode_ref, item.report_version))
    return _page(matches[:normalized_limit], normalized_limit, root_status, traversal_status)


def inspect_verified_research_report(
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportCatalogInspection:
    """Inspect one exact bundle's local self-consistency, never source freshness."""

    normalized_podcast_id = _validate_required_identifier(podcast_id, "podcast_id")
    normalized_episode_ref = _validate_required_identifier(episode_ref, "episode_ref")
    normalized_digest = _validate_source_digest(source_digest)
    locator = {
        "podcast_id": normalized_podcast_id,
        "episode_ref": normalized_episode_ref,
        "source_digest": normalized_digest,
    }
    checks = _inspection_checks()
    root, root_status = _catalog_root()
    if root is None:
        return _inspection(locator, "not_found" if root_status == "missing" else "invalid", checks)

    podcast_dir, podcast_state = _exact_directory_child(root.path, normalized_podcast_id)
    if podcast_dir is None:
        return _inspection(locator, "not_found" if podcast_state == "missing" else "invalid", checks)
    if not _safe_directory(root, podcast_dir):
        return _inspection(locator, "invalid", checks)
    episode_dir, episode_state = _exact_directory_child(podcast_dir, normalized_episode_ref)
    if episode_dir is None:
        return _inspection(locator, "not_found" if episode_state == "missing" else "invalid", checks)
    if not _safe_directory(root, episode_dir):
        return _inspection(locator, "invalid", checks)
    expected_version = f"v1-{normalized_digest}"
    bundle_dir, version_state = _exact_directory_child(episode_dir, expected_version)
    if bundle_dir is None:
        return _inspection(locator, "not_found" if version_state == "missing" else "invalid", checks)
    if not _safe_directory(root, bundle_dir):
        return _inspection(locator, "invalid", checks)
    checks["containment"] = True
    checks["canonical_version"] = bundle_dir.name == expected_version

    entries = _exact_bundle_entries(root, bundle_dir)
    if entries is None:
        return _inspection(locator, "invalid", checks)
    checks["exact_file_set"] = True

    manifest_snapshot = _secure_snapshot(
        root,
        bundle_dir / "manifest.json",
        entries["manifest.json"],
        max_bytes=_MAX_MANIFEST_BYTES,
    )
    manifest = _manifest_from_snapshot(manifest_snapshot)
    if manifest is None:
        return _inspection(locator, "invalid", checks)
    checks["manifest_schema"] = manifest.get("schema_version") == REPORT_SCHEMA_VERSION
    checks["identity"] = _manifest_identity_is_consistent(manifest, locator)
    summary = _safe_projection(
        manifest,
        podcast_id=normalized_podcast_id,
        episode_ref=normalized_episode_ref,
        source_digest=normalized_digest,
    )

    report_json_snapshot = _secure_snapshot(
        root,
        bundle_dir / "report.json",
        entries["report.json"],
        max_bytes=_MAX_REPORT_BYTES,
    )
    report_markdown_snapshot = _secure_snapshot(
        root,
        bundle_dir / "report.md",
        entries["report.md"],
        max_bytes=_MAX_REPORT_BYTES,
    )
    checks["report_json_integrity"] = _report_json_is_consistent(
        report_json_snapshot.raw if report_json_snapshot is not None else None,
        manifest,
        locator,
    )
    checks["report_markdown_integrity"] = _file_matches_manifest(
        report_markdown_snapshot.raw if report_markdown_snapshot is not None else None,
        manifest,
        "report.md",
    )
    if not _exact_bundle_entries_match(root, bundle_dir, entries):
        checks["exact_file_set"] = False
    status = "valid" if all(checks.values()) else "invalid"
    return _inspection(locator, status, checks, summary)


def _discover_summaries(
    root: _CatalogRoot,
    *,
    podcast_id: str | None,
    episode_ref: str | None,
) -> tuple[list[VerifiedResearchReportCatalogItem], str]:
    summaries: list[VerifiedResearchReportCatalogItem] = []
    podcast_dirs, capped = _bounded_children(root.path)
    if capped:
        return summaries, "incomplete_entry_cap"
    if podcast_dirs is None:
        return summaries, "incomplete_directory_read"

    for podcast_dir in podcast_dirs:
        if not _safe_directory(root, podcast_dir) or not _is_safe_podcast_id(podcast_dir.name):
            continue
        if podcast_id is not None and podcast_dir.name != podcast_id:
            continue
        episode_dirs, capped = _bounded_children(podcast_dir)
        if capped:
            return summaries, "incomplete_entry_cap"
        if episode_dirs is None:
            return summaries, "incomplete_directory_read"
        for episode_dir in episode_dirs:
            if not _safe_directory(root, episode_dir) or not _is_safe_episode_ref(episode_dir.name):
                continue
            if episode_ref is not None and episode_dir.name != episode_ref:
                continue
            version_dirs, capped = _bounded_children(episode_dir)
            if capped:
                return summaries, "incomplete_entry_cap"
            if version_dirs is None:
                return summaries, "incomplete_directory_read"
            for version_dir in version_dirs:
                if not _safe_directory(root, version_dir):
                    continue
                version_match = _VERSION_PATTERN.fullmatch(version_dir.name)
                if version_match is None:
                    continue
                summary = _summary_from_manifest(
                    root,
                    version_dir,
                    podcast_id=podcast_dir.name,
                    episode_ref=episode_dir.name,
                    source_digest=version_match.group(1),
                )
                if summary is not None:
                    summaries.append(summary)
    return summaries, "complete"


def _catalog_root() -> tuple[_CatalogRoot | None, str]:
    root = Path(storage.RESEARCH_REPORTS_DIR)
    try:
        root_stat = root.lstat()
    except FileNotFoundError:
        return None, "missing"
    except OSError:
        return None, "invalid"
    if _is_reparse(root, root_stat) or not stat.S_ISDIR(root_stat.st_mode):
        return None, "invalid"
    try:
        resolved = root.resolve(strict=True)
    except OSError:
        return None, "invalid"
    return _CatalogRoot(resolved, _path_identity(root_stat)), "available"


def _bounded_children(directory: Path) -> tuple[list[Path] | None, bool]:
    try:
        iterator = directory.iterdir()
        children: list[Path] = []
        for entry in iterator:
            if len(children) >= _ENTRY_CAP:
                return [], True
            children.append(entry)
    except OSError:
        return None, False
    return children, False


def _safe_directory(root: _CatalogRoot, candidate: Path) -> bool:
    try:
        candidate_stat = candidate.lstat()
    except OSError:
        return False
    if _is_reparse(candidate, candidate_stat) or not stat.S_ISDIR(candidate_stat.st_mode):
        return False
    return _root_is_stable(root) and _is_contained(root.path, candidate)


def _safe_regular_file(root: _CatalogRoot, candidate: Path) -> bool:
    try:
        candidate_stat = candidate.lstat()
    except OSError:
        return False
    if _is_reparse(candidate, candidate_stat) or not stat.S_ISREG(candidate_stat.st_mode):
        return False
    return _root_is_stable(root) and _is_contained(root.path, candidate)


def _is_reparse(path: Path, path_stat: Any) -> bool:
    del path
    return stat.S_ISLNK(path_stat.st_mode) or bool(
        getattr(path_stat, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _is_contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def _summary_from_manifest(
    root: _CatalogRoot,
    bundle_dir: Path,
    *,
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportCatalogItem | None:
    entries = _exact_bundle_entries(root, bundle_dir)
    if entries is None:
        return None
    manifest_snapshot = _secure_snapshot(
        root,
        bundle_dir / "manifest.json",
        entries["manifest.json"],
        max_bytes=_MAX_MANIFEST_BYTES,
    )
    manifest = _manifest_from_snapshot(manifest_snapshot)
    if manifest is None or not _exact_bundle_entries_match(root, bundle_dir, entries):
        return None
    return _safe_projection(
        manifest,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        source_digest=source_digest,
    )


def _exact_bundle_entries(root: _CatalogRoot, bundle_dir: Path) -> dict[str, _PathIdentity] | None:
    entries, capped = _bounded_children(bundle_dir)
    if capped or entries is None or {entry.name for entry in entries} != _BUNDLE_FILENAMES:
        return None
    identities: dict[str, _PathIdentity] = {}
    for entry in entries:
        if not _safe_regular_file(root, entry):
            return None
        try:
            identities[entry.name] = _path_identity(entry.lstat())
        except OSError:
            return None
    return identities


def _exact_bundle_entries_match(
    root: _CatalogRoot,
    bundle_dir: Path,
    expected: dict[str, _PathIdentity],
) -> bool:
    current = _exact_bundle_entries(root, bundle_dir)
    return current == expected


def _manifest_from_snapshot(snapshot: _SecureSnapshot | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    try:
        payload = json.loads(snapshot.raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _secure_snapshot(
    root: _CatalogRoot,
    path: Path,
    expected_identity: _PathIdentity,
    *,
    max_bytes: int | None = None,
) -> _SecureSnapshot | None:
    """Read one regular in-root file once and reject pathname/handle races."""

    if not _root_is_stable(root):
        return None
    try:
        before = path.lstat()
    except OSError:
        return None
    if (
        _is_reparse(path, before)
        or not stat.S_ISREG(before.st_mode)
        or _path_identity(before) != expected_identity
        or not _is_contained(root.path, path)
    ):
        return None
    if max_bytes is not None and before.st_size > max_bytes:
        return None

    descriptor: int | None = None
    try:
        descriptor = os.open(path, _snapshot_open_flags())
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _is_reparse_stat(opened)
            or _path_identity(opened) != expected_identity
            or (max_bytes is not None and opened.st_size > max_bytes)
            or not _opened_handle_is_contained(root.path, descriptor)
        ):
            return None
        raw = _read_descriptor_once(descriptor, opened.st_size)
        after_handle = os.fstat(descriptor)
        if (
            _path_identity(after_handle) != expected_identity
            or after_handle.st_size != opened.st_size
            or len(raw) != opened.st_size
            or (max_bytes is not None and (after_handle.st_size > max_bytes or len(raw) > max_bytes))
        ):
            return None
    except OSError:
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass

    try:
        after_path = path.lstat()
    except OSError:
        return None
    if (
        _is_reparse(path, after_path)
        or not stat.S_ISREG(after_path.st_mode)
        or _path_identity(after_path) != expected_identity
        or not _root_is_stable(root)
        or not _is_contained(root.path, path)
    ):
        return None
    return _SecureSnapshot(raw=raw, identity=expected_identity)


def _snapshot_open_flags() -> int:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    if os.name != "nt":
        flags |= getattr(os, "O_NOFOLLOW", 0)
    return flags


def _read_descriptor_once(descriptor: int, expected_size: int) -> bytes:
    remaining = expected_size
    chunks: list[bytes] = []
    while remaining:
        chunk = os.read(descriptor, min(remaining, 1_048_576))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _opened_handle_is_contained(root: Path, descriptor: int) -> bool:
    final_path = _opened_handle_final_path(descriptor)
    if final_path is None:
        # A platform without a handle-final-path primitive cannot prove that an
        # opened pathname remained beneath root, so this bounded check fails closed.
        return False
    return _path_text_is_contained(root, final_path)


def _opened_handle_final_path(descriptor: int) -> Path | None:
    if os.name == "nt":
        return _windows_final_path_from_descriptor(descriptor)
    proc_link = Path("/proc/self/fd") / str(descriptor)
    try:
        return Path(os.readlink(proc_link))
    except OSError:
        return None


def _windows_final_path_from_descriptor(descriptor: int) -> Path | None:
    """Return a normalized final DOS/UNC path through an explicitly typed Win32 ABI."""

    try:
        import ctypes
        from ctypes import wintypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_final_path = kernel32.GetFinalPathNameByHandleW
        get_final_path.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        get_final_path.restype = wintypes.DWORD
        raw_handle = msvcrt.get_osfhandle(descriptor)
        if raw_handle == -1:
            return None
        handle = wintypes.HANDLE(raw_handle)
        buffer = ctypes.create_unicode_buffer(32_768)
        length = get_final_path(handle, buffer, wintypes.DWORD(len(buffer)), wintypes.DWORD(0))
        if length == 0 or length >= len(buffer):
            return None
        normalized = _normalize_windows_final_path(buffer.value)
        return Path(normalized) if normalized is not None else None
    except (AttributeError, ImportError, OSError, TypeError, ValueError, ctypes.ArgumentError):
        return None


def _normalize_windows_final_path(value: str) -> str | None:
    """Accept only extended DOS or UNC forms returned by the handle API."""

    unc_prefix = "\\\\?\\UNC\\"
    dos_prefix = "\\\\?\\"
    if not isinstance(value, str):
        return None
    if value.startswith(unc_prefix):
        suffix = value[len(unc_prefix) :]
        server_and_share = suffix.split("\\")
        if len(server_and_share) < 2 or not server_and_share[0] or not server_and_share[1]:
            return None
        return "\\\\" + suffix
    if value.startswith(dos_prefix):
        suffix = value[len(dos_prefix) :]
        if len(suffix) < 3 or suffix[1] != ":" or suffix[2] != "\\" or not suffix[0].isalpha():
            return None
        return suffix
    return None


def _path_text_is_contained(root: Path, candidate: Path) -> bool:
    try:
        root_text = os.path.normcase(os.path.abspath(str(root)))
        candidate_text = os.path.normcase(os.path.abspath(str(candidate)))
        return os.path.commonpath((root_text, candidate_text)) == root_text
    except (OSError, ValueError):
        return False


def _is_reparse_stat(path_stat: Any) -> bool:
    return bool(
        getattr(path_stat, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _path_identity(path_stat: Any) -> _PathIdentity:
    return _PathIdentity(path_stat.st_dev, path_stat.st_ino, stat.S_IFMT(path_stat.st_mode))


def _root_is_stable(root: _CatalogRoot) -> bool:
    try:
        current = root.path.lstat()
    except OSError:
        return False
    return (
        not _is_reparse(root.path, current)
        and stat.S_ISDIR(current.st_mode)
        and _path_identity(current) == root.identity
    )


def _safe_projection(
    manifest: dict[str, Any],
    *,
    podcast_id: str,
    episode_ref: str,
    source_digest: str,
) -> VerifiedResearchReportCatalogItem | None:
    identity = manifest.get("episode_identity")
    assembly_options = manifest.get("assembly_options")
    quality_gates = manifest.get("quality_gates")
    expected_version = f"v1-{source_digest}"
    if (
        manifest.get("schema_version") != REPORT_SCHEMA_VERSION
        or manifest.get("report_version") != expected_version
        or manifest.get("source_digest") != source_digest
        or not isinstance(identity, dict)
        or identity.get("podcast_id") != podcast_id
        or identity.get("episode_ref") != episode_ref
        or not isinstance(assembly_options, dict)
        or not isinstance(assembly_options.get("include_fixture_verification"), bool)
        or not isinstance(quality_gates, dict)
        or quality_gates.get("semantic_review_status") != "passed"
        or quality_gates.get("not_investment_advice") is not True
    ):
        return None
    return VerifiedResearchReportCatalogItem(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        report_version=expected_version,
        source_digest=source_digest,
        schema_version=REPORT_SCHEMA_VERSION,
        include_fixture_verification=assembly_options["include_fixture_verification"],
        stock_query_present=assembly_options.get("stock_query") is not None,
        semantic_review_status="passed",
        not_investment_advice=quality_gates["not_investment_advice"],
    )


def _page(
    items: list[VerifiedResearchReportCatalogItem],
    limit: int,
    catalog_root_status: str,
    traversal_status: str,
) -> VerifiedResearchReportCatalogPage:
    return VerifiedResearchReportCatalogPage(
        items=items,
        limit=limit,
        returned_count=len(items),
        catalog_root_status=catalog_root_status,
        traversal_status=traversal_status,
    )


def _validate_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= _MAX_LIMIT:
        raise VerifiedResearchReportCatalogInputError("catalog limit is invalid")
    return limit


def _inspection_checks() -> dict[str, bool]:
    return {
        "containment": False,
        "canonical_version": False,
        "exact_file_set": False,
        "manifest_schema": False,
        "identity": False,
        "report_json_integrity": False,
        "report_markdown_integrity": False,
    }


def _inspection(
    locator: dict[str, str],
    status: str,
    checks: dict[str, bool],
    safe_metadata: VerifiedResearchReportCatalogItem | None = None,
) -> VerifiedResearchReportCatalogInspection:
    return VerifiedResearchReportCatalogInspection(
        locator=locator,
        bundle_self_consistency_status=status,
        checks=checks,
        source_currentness_status="not_evaluated",
        safe_metadata=safe_metadata,
        not_investment_advice=(
            safe_metadata.not_investment_advice if safe_metadata is not None else None
        ),
    )


def _exact_directory_child(directory: Path, expected_name: str) -> tuple[Path | None, str]:
    children, capped = _bounded_children(directory)
    if capped:
        return None, "entry_cap"
    if children is None:
        return None, "directory_read"
    for child in children:
        if child.name == expected_name:
            return child, "found"
    return None, "missing"


def _manifest_identity_is_consistent(manifest: dict[str, Any], locator: dict[str, str]) -> bool:
    identity = manifest.get("episode_identity")
    return bool(
        isinstance(identity, dict)
        and manifest.get("report_version") == f"v1-{locator['source_digest']}"
        and manifest.get("source_digest") == locator["source_digest"]
        and identity.get("podcast_id") == locator["podcast_id"]
        and identity.get("episode_ref") == locator["episode_ref"]
    )


def _report_json_is_consistent(
    raw: bytes | None,
    manifest: dict[str, Any],
    locator: dict[str, str],
) -> bool:
    if not _file_matches_manifest(raw, manifest, "report.json"):
        return False
    try:
        report = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    identity = report.get("episode_identity") if isinstance(report, dict) else None
    return bool(
        isinstance(identity, dict)
        and report.get("schema_version") == REPORT_SCHEMA_VERSION
        and report.get("report_version") == f"v1-{locator['source_digest']}"
        and report.get("source_digest") == locator["source_digest"]
        and identity.get("podcast_id") == locator["podcast_id"]
        and identity.get("episode_ref") == locator["episode_ref"]
        and report.get("not_investment_advice") is True
    )


def _file_matches_manifest(raw: bytes | None, manifest: dict[str, Any], filename: str) -> bool:
    bundle_files = manifest.get("bundle_files")
    expected = bundle_files.get(filename) if isinstance(bundle_files, dict) else None
    if (
        raw is None
        or not isinstance(expected, dict)
        or not isinstance(expected.get("sha256"), str)
        or not isinstance(expected.get("size_bytes"), int)
        or isinstance(expected.get("size_bytes"), bool)
    ):
        return False
    return (
        expected["size_bytes"] == len(raw)
        and expected["sha256"] == hashlib.sha256(raw).hexdigest()
    )


def _matches_query(item: VerifiedResearchReportCatalogItem, query: str) -> bool:
    return any(
        query in value.casefold()
        for value in (
            item.podcast_id,
            item.episode_ref,
            item.report_version,
            item.source_digest,
        )
    )


def _normalize_query(query: str) -> str:
    if not isinstance(query, str) or len(query) > _MAX_QUERY_LENGTH or any(
        unicodedata.category(character).startswith("C") and not character.isspace()
        for character in query
    ):
        raise VerifiedResearchReportCatalogInputError("catalog query is invalid")
    normalized = " ".join(unicodedata.normalize("NFKC", query).casefold().split())
    if not normalized or len(normalized) > _MAX_QUERY_LENGTH:
        raise VerifiedResearchReportCatalogInputError("catalog query is invalid")
    return normalized


def _is_safe_podcast_id(value: str) -> bool:
    return storage._SAFE_SLUG_PATTERN.fullmatch(value) is not None


def _is_safe_episode_ref(value: str) -> bool:
    return (
        storage._SAFE_EPISODE_REF_PATTERN.fullmatch(value) is not None
        and value.casefold() not in _RESERVED_EPISODE_REFS
    )


def _validate_required_identifier(value: str, field: str) -> str:
    validator = _is_safe_podcast_id if field == "podcast_id" else _is_safe_episode_ref
    if not isinstance(value, str) or not validator(value):
        raise VerifiedResearchReportCatalogInputError(f"catalog {field} is invalid")
    return value


def _validate_source_digest(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise VerifiedResearchReportCatalogInputError("catalog source_digest is invalid")
    return value


def _validate_optional_identifier(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    return _validate_required_identifier(value, field)


def result_to_dict(
    result: VerifiedResearchReportCatalogPage | VerifiedResearchReportCatalogInspection,
) -> dict[str, Any]:
    """Serialize a catalog result without filesystem paths or raw manifest data."""

    return asdict(result)
