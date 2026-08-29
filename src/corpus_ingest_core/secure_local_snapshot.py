"""Fail-closed immutable local-file snapshots for Core-derived paths only."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Any


_MAX_DIRECTORY_ENTRIES = 4_096


@dataclass(frozen=True)
class SecureLocalSnapshot:
    """One immutable byte snapshot proven to be a regular file beneath root."""

    raw: bytes
    device: int
    inode: int
    size_bytes: int


@dataclass(frozen=True)
class _Root:
    lexical_path: Path
    resolved_path: Path
    device: int
    inode: int


def secure_read_bytes(root: Path, path: Path, *, max_bytes: int) -> bytes | None:
    """Read one Core-derived expected file or fail closed without following links.

    ``path`` must be lexically below the Core-derived ``root``.  Neither caller
    may supply a persisted path as the authority for either argument.
    """

    snapshot = secure_snapshot(root, path, max_bytes=max_bytes)
    return snapshot.raw if snapshot is not None else None


def secure_snapshot(root: Path, path: Path, *, max_bytes: int) -> SecureLocalSnapshot | None:
    """Prove stable, regular, in-root bytes across pathname and handle races."""

    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0:
        return None
    checked_root = _checked_root(root)
    if checked_root is None:
        return None
    candidate = _lexically_contained_candidate(checked_root.lexical_path, path)
    if candidate is None or not _safe_parent_chain(checked_root, candidate):
        return None
    try:
        before = candidate.lstat()
    except OSError:
        return None
    if (
        _is_reparse(before)
        or not stat.S_ISREG(before.st_mode)
        or before.st_size > max_bytes
    ):
        return None
    identity = _identity(before)
    descriptor: int | None = None
    try:
        descriptor = os.open(candidate, _open_flags())
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _is_reparse(opened)
            or _identity(opened) != identity
            or opened.st_size > max_bytes
            or not _opened_handle_is_contained(checked_root.resolved_path, descriptor)
        ):
            return None
        raw = _read_descriptor_once(descriptor, opened.st_size)
        after_handle = os.fstat(descriptor)
        if (
            _identity(after_handle) != identity
            or after_handle.st_size != opened.st_size
            or len(raw) != opened.st_size
            or len(raw) > max_bytes
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
        after_path = candidate.lstat()
    except OSError:
        return None
    if (
        _is_reparse(after_path)
        or not stat.S_ISREG(after_path.st_mode)
        or _identity(after_path) != identity
        or not _root_is_stable(checked_root)
        or not _safe_parent_chain(checked_root, candidate)
    ):
        return None
    return SecureLocalSnapshot(raw, identity[0], identity[1], len(raw))


def secure_directory_names(root: Path, directory: Path, *, max_entries: int) -> tuple[str, ...] | None:
    """List direct child names while holding a proven Core-derived directory handle.

    Returned names contain no separators and are suitable only for joining to the
    caller's independently Core-derived directory.  Failure to prove any handle,
    root, identity, or containment property returns ``None``.
    """

    if (
        isinstance(max_entries, bool)
        or not isinstance(max_entries, int)
        or not 0 <= max_entries <= _MAX_DIRECTORY_ENTRIES
    ):
        return None
    checked_root = _checked_root(root)
    if checked_root is None:
        return None
    candidate = _lexically_contained_path(checked_root.lexical_path, directory, allow_root=True)
    if candidate is None or not _safe_directory_chain(checked_root, candidate):
        return None
    try:
        before = candidate.lstat()
    except OSError:
        return None
    if _is_reparse(before) or not stat.S_ISDIR(before.st_mode):
        return None
    identity = _identity(before)
    descriptor: int | None = None
    try:
        descriptor = _open_directory_descriptor(candidate)
        opened = os.fstat(descriptor)
        if (
            _is_reparse(opened)
            or not stat.S_ISDIR(opened.st_mode)
            or _identity(opened) != identity
            or not _opened_handle_is_contained(checked_root.resolved_path, descriptor)
        ):
            return None
        names = _list_directory_while_open(descriptor, candidate)
        if (
            len(names) > max_entries
            or any(not _safe_child_name(name) for name in names)
            or not _directory_names_are_current(candidate, names)
        ):
            return None
        after_handle = os.fstat(descriptor)
        if _identity(after_handle) != identity:
            return None
    except (OSError, TypeError, ValueError):
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
    try:
        after_path = candidate.lstat()
    except OSError:
        return None
    if (
        _is_reparse(after_path)
        or not stat.S_ISDIR(after_path.st_mode)
        or _identity(after_path) != identity
        or not _root_is_stable(checked_root)
        or not _safe_directory_chain(checked_root, candidate)
    ):
        return None
    return tuple(sorted(names))


def _checked_root(root: Path) -> _Root | None:
    lexical = Path(os.path.abspath(str(root)))
    try:
        root_stat = lexical.lstat()
    except OSError:
        return None
    if (
        _is_reparse(root_stat)
        or not stat.S_ISDIR(root_stat.st_mode)
        or not _safe_root_ancestor_chain(lexical)
    ):
        return None
    device, inode, _mode = _identity(root_stat)
    # The complete lexical root chain has been proven non-reparse.  Keep this
    # lexical path as the containment anchor; never resolve a hostile candidate.
    return _Root(lexical, lexical, device, inode)


def _lexically_contained_candidate(root: Path, path: Path) -> Path | None:
    return _lexically_contained_path(root, path, allow_root=False)


def _lexically_contained_path(root: Path, path: Path, *, allow_root: bool) -> Path | None:
    candidate = Path(os.path.abspath(str(path)))
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None
    if not allow_root and not relative.parts:
        return None
    return root.joinpath(relative)


def _safe_root_ancestor_chain(root: Path) -> bool:
    """Reject a reparse point at root itself or at any lexical ancestor."""

    current = root
    while True:
        try:
            value = current.lstat()
        except OSError:
            return False
        if _is_reparse(value) or not stat.S_ISDIR(value.st_mode):
            return False
        parent = current.parent
        if parent == current:
            return True
        current = parent


def _safe_parent_chain(root: _Root, candidate: Path) -> bool:
    try:
        relative = candidate.relative_to(root.lexical_path)
    except ValueError:
        return False
    current = root.lexical_path
    for part in relative.parts[:-1]:
        current = current / part
        try:
            value = current.lstat()
        except OSError:
            return False
        if _is_reparse(value) or not stat.S_ISDIR(value.st_mode):
            return False
    return _root_is_stable(root)


def _safe_directory_chain(root: _Root, directory: Path) -> bool:
    try:
        relative = directory.relative_to(root.lexical_path)
    except ValueError:
        return False
    current = root.lexical_path
    for part in relative.parts:
        current = current / part
        try:
            value = current.lstat()
        except OSError:
            return False
        if _is_reparse(value) or not stat.S_ISDIR(value.st_mode):
            return False
    return _root_is_stable(root)


def _root_is_stable(root: _Root) -> bool:
    try:
        current = root.lexical_path.lstat()
    except OSError:
        return False
    return (
        not _is_reparse(current)
        and stat.S_ISDIR(current.st_mode)
        and _identity(current)[:2] == (root.device, root.inode)
    )


def _identity(value: Any) -> tuple[int, int, int]:
    return value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode)


def _is_reparse(value: Any) -> bool:
    return stat.S_ISLNK(value.st_mode) or bool(
        getattr(value, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _open_flags() -> int:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    if os.name != "nt":
        flags |= getattr(os, "O_NOFOLLOW", 0)
    return flags


def _open_directory_descriptor(directory: Path) -> int:
    if os.name == "nt":
        return _windows_open_directory_descriptor(directory)
    flags = _open_flags() | getattr(os, "O_DIRECTORY", 0)
    return os.open(directory, flags)


def _windows_open_directory_descriptor(directory: Path) -> int:
    """Open a directory without delete sharing, then transfer it to a CRT fd."""

    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    creator = kernel32.CreateFileW
    creator.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    creator.restype = wintypes.HANDLE
    handle = creator(
        str(directory),
        wintypes.DWORD(0x80000000),  # GENERIC_READ
        wintypes.DWORD(0x00000001 | 0x00000002),  # READ|WRITE, never DELETE
        None,
        wintypes.DWORD(3),  # OPEN_EXISTING
        wintypes.DWORD(0x02000000),  # FILE_FLAG_BACKUP_SEMANTICS
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        raise OSError(ctypes.get_last_error(), "CreateFileW failed")
    try:
        return msvcrt.open_osfhandle(handle, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError:
        kernel32.CloseHandle(wintypes.HANDLE(handle))
        raise


def _list_directory_while_open(descriptor: int, directory: Path) -> list[str]:
    # On POSIX, listdir(fd) binds enumeration to the opened directory.  Windows
    # CPython does not accept directory fds; CreateFileW above denied delete
    # sharing, so this path cannot be replaced while its verified handle lives.
    return os.listdir(directory if os.name == "nt" else descriptor)


def _directory_names_are_current(directory: Path, names: list[str]) -> bool:
    """Prove pathname enumeration still names entries in the verified directory.

    Windows retains the directory handle without DELETE sharing while this runs;
    the explicit post-check also fails closed if a mocked or platform-specific
    pathname enumerator reports names from a transient replacement.
    """

    try:
        for name in names:
            (directory / name).lstat()
    except OSError:
        return False
    return True


def _safe_child_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and bool(name)
        and name not in {".", ".."}
        and "/" not in name
        and "\\" not in name
        and Path(name).name == name
    )


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
    return final_path is not None and _text_is_contained(root, final_path)


def _opened_handle_final_path(descriptor: int) -> Path | None:
    if os.name == "nt":
        return _windows_final_path_from_descriptor(descriptor)
    try:
        return Path(os.readlink(Path("/proc/self/fd") / str(descriptor)))
    except OSError:
        return None


def _windows_final_path_from_descriptor(descriptor: int) -> Path | None:
    """Use a pointer-sized, explicitly typed GetFinalPathNameByHandleW ABI."""

    try:
        import ctypes
        from ctypes import wintypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        getter = kernel32.GetFinalPathNameByHandleW
        getter.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        getter.restype = wintypes.DWORD
        raw_handle = msvcrt.get_osfhandle(descriptor)
        if raw_handle == -1:
            return None
        buffer = ctypes.create_unicode_buffer(32_768)
        length = getter(wintypes.HANDLE(raw_handle), buffer, wintypes.DWORD(len(buffer)), wintypes.DWORD(0))
        if length == 0 or length >= len(buffer):
            return None
        normalized = _normalize_windows_final_path(buffer.value)
        return Path(normalized) if normalized is not None else None
    except (AttributeError, ImportError, OSError, TypeError, ValueError, ctypes.ArgumentError):
        return None


def _normalize_windows_final_path(value: str) -> str | None:
    unc_prefix = "\\\\?\\UNC\\"
    dos_prefix = "\\\\?\\"
    if not isinstance(value, str):
        return None
    if value.startswith(unc_prefix):
        suffix = value[len(unc_prefix):]
        pieces = suffix.split("\\")
        if len(pieces) < 2 or not pieces[0] or not pieces[1]:
            return None
        return "\\\\" + suffix
    if value.startswith(dos_prefix):
        suffix = value[len(dos_prefix):]
        if len(suffix) < 3 or suffix[1] != ":" or suffix[2] != "\\" or not suffix[0].isalpha():
            return None
        return suffix
    return None


def _text_is_contained(root: Path, candidate: Path) -> bool:
    try:
        root_text = os.path.normcase(os.path.abspath(str(root)))
        candidate_text = os.path.normcase(os.path.abspath(str(candidate)))
        return os.path.commonpath((root_text, candidate_text)) == root_text
    except (OSError, ValueError):
        return False
