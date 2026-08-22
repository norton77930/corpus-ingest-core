from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://127.0.0.1:8767/mcp"
READONLY_TOOL = "list_episodes"
PREVIEW_TOOL = "run_corpus_episode_completion_workflow"
EXPECTED_TOOL_ORDER = [
    "list_episodes",
    "get_episode",
    "validate_transcript",
    "search_transcripts",
    "search_mentions",
    "rebuild_cache",
    "download_audio",
    "summarize_episode_extractive",
    "extract_mentions",
    "transcribe_episode",
    "semantic_summarize_episode",
    "run_research_workflow",
    "run_corpus_episode_completion_workflow",
    "run_corpus_latest_episode_deterministic_workflow",
    "run_latest_episode_verified_research_report_workflow",
    "run_episode_verified_research_report_workflow",
    "query_verified_research_report_catalog",
    "revalidate_verified_research_report_sources",
    "query_verified_research_report_coverage",
    "suggest_historical_verified_report_next_step",
    "list_verified_report_gap_backlog",
    "generate_stock_lens_report",
    "ingest_x_video",
    "ingest_youtube_video",
    "derive_workflow_bundle",
]
SURFACE_NAMES = (
    "podcast_data",
    "hermes_config",
    "managed_skills",
)


class _BoundedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError("invalid command line")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _BoundedArgumentParser(
        description="驗證 Hermes sidecar 的 direct MCP readiness 與 protected surfaces。"
    )
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--config-path", type=Path, required=True)
    parser.add_argument("--skills-path", type=Path, required=True)
    parser.add_argument("--podcast", default="gooaye")
    return parser.parse_args(argv)


_SNAPSHOT_ERROR = "protected content snapshot failed"


def _protected_content_access_supported() -> bool:
    """Return whether descriptor-only, no-follow traversal is available."""

    return (
        os.name == "posix"
        and bool(getattr(os, "O_NOFOLLOW", 0))
        and bool(getattr(os, "O_DIRECTORY", 0))
        and os.open in getattr(os, "supports_dir_fd", ())
        and os.scandir in getattr(os, "supports_fd", ())
    )


def _require_protected_content_access_support() -> None:
    if not _protected_content_access_supported():
        raise ValueError(_SNAPSHOT_ERROR)


def _protected_descriptor_flags() -> int:
    return (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _descriptor_kind(info: os.stat_result) -> bytes:
    if _is_reparse_or_symlink(info):
        raise ValueError(_SNAPSHOT_ERROR)
    if stat.S_ISREG(info.st_mode):
        return b"F"
    if stat.S_ISDIR(info.st_mode):
        return b"D"
    raise ValueError(_SNAPSHOT_ERROR)


def _open_protected_root_descriptor(path: Path) -> int:
    parts = path.parts[1:] if path.is_absolute() else path.parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(_SNAPSHOT_ERROR)

    base = path.anchor if path.is_absolute() else "."
    descriptor = os.open(
        base,
        _protected_descriptor_flags() | os.O_DIRECTORY,
    )
    try:
        if _descriptor_kind(os.fstat(descriptor)) != b"D":
            raise ValueError(_SNAPSHOT_ERROR)
        for index, part in enumerate(parts):
            child_fd = os.open(
                part,
                _protected_descriptor_flags(),
                dir_fd=descriptor,
            )
            try:
                child_kind = _descriptor_kind(os.fstat(child_fd))
                if index < len(parts) - 1 and child_kind != b"D":
                    raise ValueError(_SNAPSHOT_ERROR)
            except Exception:
                os.close(child_fd)
                raise
            os.close(descriptor)
            descriptor = child_fd
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _open_protected_descriptor(
    path: Path | str,
    *,
    directory_fd: int | None = None,
) -> int:
    if directory_fd is None:
        return _open_protected_root_descriptor(Path(path))
    return os.open(path, _protected_descriptor_flags(), dir_fd=directory_fd)


def _descriptor_entry_names(directory_fd: int) -> list[str]:
    with os.scandir(directory_fd) as entries:
        return sorted(entry.name for entry in entries)


def metadata_manifest(root: Path) -> dict[str, Any]:
    """Hash metadata through no-follow descriptors without returning values."""

    try:
        _require_protected_content_access_support()
        root_fd = _open_protected_descriptor(root)
        try:
            digest = hashlib.sha256()
            entry_count = _update_metadata_manifest(digest, root_fd, ())
        finally:
            os.close(root_fd)
        return {
            "entry_count": entry_count,
            "sha256": digest.hexdigest(),
        }
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(_SNAPSHOT_ERROR) from exc


def _update_metadata_manifest(
    digest: Any,
    descriptor: int,
    relative_parts: tuple[str, ...],
) -> int:
    before = os.fstat(descriptor)
    kind = _descriptor_kind(before)
    relative = "." if not relative_parts else "/".join(relative_parts)
    record = [
        relative,
        kind.decode("ascii"),
        stat.S_IMODE(before.st_mode),
        before.st_size,
        before.st_mtime_ns,
    ]
    digest.update(json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\0")

    entry_count = 1
    if kind == b"D":
        for name in _descriptor_entry_names(descriptor):
            child_fd = _open_protected_descriptor(name, directory_fd=descriptor)
            try:
                entry_count += _update_metadata_manifest(
                    digest,
                    child_fd,
                    (*relative_parts, name),
                )
            finally:
                os.close(child_fd)
        if _stable_directory_identity(before) != _stable_directory_identity(
            os.fstat(descriptor)
        ):
            raise ValueError(_SNAPSHOT_ERROR)
    return entry_count


def _content_token(root: Path) -> bytes:
    try:
        if _is_prohibited_content_name(root.name):
            raise ValueError(_SNAPSHOT_ERROR)
        _require_protected_content_access_support()
        root_fd = _open_protected_descriptor(root)
        try:
            root_info = os.fstat(root_fd)
            root_kind = _descriptor_kind(root_info)
            digest = hashlib.sha256()
            digest.update(b"hermes-protected-content-v1\0")
            if root_kind == b"F":
                _update_content_file(digest, root_fd, b".")
            else:
                _update_content_frame(digest, b"D", b".")
                _update_content_directory(digest, root_fd, ())
            return digest.digest()
        finally:
            os.close(root_fd)
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(_SNAPSHOT_ERROR) from exc


def _update_content_directory(
    digest: Any,
    directory_fd: int,
    relative_parts: tuple[str, ...],
) -> None:
    before = os.fstat(directory_fd)
    if _descriptor_kind(before) != b"D":
        raise ValueError(_SNAPSHOT_ERROR)

    for name in _descriptor_entry_names(directory_fd):
        if _is_prohibited_content_name(name):
            raise ValueError(_SNAPSHOT_ERROR)
        child_fd = _open_protected_descriptor(name, directory_fd=directory_fd)
        try:
            info = os.fstat(child_fd)
            kind = _descriptor_kind(info)
            relative = "/".join((*relative_parts, name)).encode("utf-8")
            if kind == b"D":
                _update_content_frame(digest, b"D", relative)
                _update_content_directory(
                    digest,
                    child_fd,
                    (*relative_parts, name),
                )
            else:
                _update_content_file(digest, child_fd, relative)
        finally:
            os.close(child_fd)

    if _stable_directory_identity(before) != _stable_directory_identity(
        os.fstat(directory_fd)
    ):
        raise ValueError(_SNAPSHOT_ERROR)


def _update_content_file(
    digest: Any,
    descriptor: int,
    relative: bytes,
) -> None:
    before = os.fstat(descriptor)
    if _descriptor_kind(before) != b"F":
        raise ValueError(_SNAPSHOT_ERROR)
    _update_content_frame(digest, b"F", relative)
    digest.update(before.st_size.to_bytes(8, "big"))
    while chunk := os.read(descriptor, 1024 * 1024):
        digest.update(chunk)
    if _stable_file_identity(before) != _stable_file_identity(os.fstat(descriptor)):
        raise ValueError(_SNAPSHOT_ERROR)


def _update_content_frame(digest: Any, kind: bytes, relative: bytes) -> None:
    digest.update(kind)
    digest.update(len(relative).to_bytes(8, "big"))
    digest.update(relative)


def _is_prohibited_content_name(name: str) -> bool:
    normalized = name.casefold()
    return normalized == ".env" or normalized.startswith(".env.")


def _is_reparse_or_symlink(info: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    file_attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(info.st_mode) or bool(file_attributes & reparse_flag)


def _stable_file_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
    )


def _stable_directory_identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_mtime_ns,
    )


def protected_surface_snapshot(
    *,
    data_path: Path,
    config_path: Path,
    skills_path: Path,
) -> dict[str, dict[str, Any]]:
    return {
        "podcast_data": _protected_surface_state(data_path),
        "hermes_config": _protected_surface_state(config_path),
        "managed_skills": _protected_surface_state(skills_path),
    }


def _protected_surface_state(path: Path) -> dict[str, Any]:
    metadata_before = metadata_manifest(path)
    content_token = _content_token(path)
    metadata_after = metadata_manifest(path)
    if metadata_before != metadata_after:
        raise ValueError("protected content snapshot failed")
    return {
        "metadata": metadata_after,
        "content_token": content_token,
    }


def _surface_manifest_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"entry_count", "sha256"}:
        return False
    entry_count = value["entry_count"]
    digest = value["sha256"]
    return (
        type(entry_count) is int
        and entry_count >= 1
        and isinstance(digest, str)
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def _surface_snapshot_valid(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"metadata", "content_token"}
        and _surface_manifest_valid(value["metadata"])
        and isinstance(value["content_token"], bytes)
        and len(value["content_token"]) == hashlib.sha256().digest_size
    )


def build_evidence(
    *,
    protocol_version: str,
    server_version: str,
    tool_names: list[str],
    readonly_ok: bool,
    preview_ok: bool,
    preview_dry_run: bool,
    preview_requires_confirmation: bool,
    before: Any,
    after: Any,
) -> dict[str, Any]:
    registry_matches = tool_names == EXPECTED_TOOL_ORDER
    surfaces: dict[str, dict[str, bool]] = {}
    for name in SURFACE_NAMES:
        before_surface = before.get(name) if isinstance(before, dict) else None
        after_surface = after.get(name) if isinstance(after, dict) else None
        valid = _surface_snapshot_valid(before_surface) and _surface_snapshot_valid(
            after_surface
        )
        metadata_unchanged = bool(
            valid
            and before_surface["metadata"] == after_surface["metadata"]
        )
        content_unchanged = bool(
            valid
            and hmac.compare_digest(
                before_surface["content_token"],
                after_surface["content_token"],
            )
        )
        surfaces[name] = {
            "metadata_unchanged": metadata_unchanged,
            "content_unchanged": content_unchanged,
        }

    ok = (
        registry_matches
        and readonly_ok
        and preview_ok
        and preview_dry_run
        and preview_requires_confirmation
        and all(
            all(surface_results.values())
            for surface_results in surfaces.values()
        )
    )
    return {
        "schema_version": "hermes-direct-smoke-v2",
        "ok": ok,
        "protocol_version": protocol_version,
        "server_version": server_version,
        "tool_count": len(tool_names),
        "tool_names": tool_names,
        "tool_order_sha256": hashlib.sha256(
            "\n".join(tool_names).encode("utf-8")
        ).hexdigest(),
        "tool_registry_matches": registry_matches,
        "readonly_call_count": 1,
        "readonly_ok": readonly_ok,
        "preview_call_count": 1,
        "preview_ok": preview_ok,
        "preview_confirm": False,
        "preview_dry_run": preview_dry_run,
        "preview_requires_confirmation": preview_requires_confirmation,
        "protected_surface_evidence_scope": "metadata_and_content_equality",
        "protected_surfaces": surfaces,
        "hermes_natural_language_claim": "not_evaluated",
    }


def tool_result_ok(result: Any) -> bool:
    structured = _structured_content(result)
    return (
        not bool(result.isError)
        and isinstance(structured, dict)
        and structured.get("ok") is True
    )


def tool_result_flag(result: Any, name: str) -> bool:
    structured = _structured_content(result)
    return isinstance(structured, dict) and structured.get(name) is True


def _structured_content(result: Any) -> Any:
    return getattr(result, "structuredContent", None) or getattr(
        result,
        "structured_content",
        None,
    )


def run_validation(
    *,
    data_path: Path,
    config_path: Path,
    skills_path: Path,
    podcast_id: str = "gooaye",
) -> dict[str, Any]:
    before = protected_surface_snapshot(
        data_path=data_path,
        config_path=config_path,
        skills_path=skills_path,
    )
    direct = asyncio.run(_run_direct_smoke(podcast_id=podcast_id))
    after = protected_surface_snapshot(
        data_path=data_path,
        config_path=config_path,
        skills_path=skills_path,
    )
    return build_evidence(before=before, after=after, **direct)


async def _run_direct_smoke(*, podcast_id: str) -> dict[str, Any]:
    async with streamablehttp_client(MCP_URL, timeout=20) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            readonly = await session.call_tool(
                READONLY_TOOL,
                {"podcast_id": podcast_id, "limit": 1},
            )
            preview = await session.call_tool(
                PREVIEW_TOOL,
                {
                    "podcast_id": podcast_id,
                    "episode_ref": "latest",
                    "action": "next",
                    "confirm": False,
                },
            )

    return {
        "protocol_version": initialized.protocolVersion,
        "server_version": initialized.serverInfo.version,
        "tool_names": [tool.name for tool in listed.tools],
        "readonly_ok": tool_result_ok(readonly),
        "preview_ok": tool_result_ok(preview),
        "preview_dry_run": tool_result_flag(preview, "dry_run"),
        "preview_requires_confirmation": tool_result_flag(
            preview,
            "requires_confirmation",
        ),
    }


def _failure_result() -> dict[str, Any]:
    return {
        "schema_version": "hermes-direct-smoke-v2",
        "ok": False,
        "error": "direct_validation_failed",
        "hermes_natural_language_claim": "not_evaluated",
    }


def main() -> None:
    try:
        args = parse_args()
        result = run_validation(
            data_path=args.data_path,
            config_path=args.config_path,
            skills_path=args.skills_path,
            podcast_id=args.podcast,
        )
    except Exception:
        result = _failure_result()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
