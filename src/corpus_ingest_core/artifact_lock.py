"""Cross-process exclusive claims for local artifact critical sections."""

from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
import time
from threading import Lock
from typing import Iterator


_PROCESS_CLAIMS_GUARD = Lock()
_PROCESS_CLAIMS: dict[str, Lock] = {}


@contextmanager
def exclusive_artifact_claim(
    claim_path: Path,
    *,
    timeout_seconds: float = 15.0,
) -> Iterator[None]:
    """Hold a process-lifetime OS lock at a persistent local lockfile path.

    The process-local lock closes a same-process thread hole on platforms whose
    advisory OS locks permit re-entry by a process.  The descriptor lock remains
    the cross-process authority.  A lockfile is only an address for that lock,
    not evidence that a process is alive; it is intentionally retained after
    release/crash and never reclaimed by mtime.
    """

    deadline = time.monotonic() + timeout_seconds
    with _in_process_claim(claim_path, timeout_seconds=timeout_seconds):
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(str(claim_path), os.O_CREAT | os.O_RDWR)
        locked = False
        try:
            _ensure_lock_byte(descriptor)
            while not locked:
                try:
                    _lock_descriptor(descriptor)
                    locked = True
                except OSError as exc:
                    if not _is_lock_contention(exc):
                        raise
                    if time.monotonic() >= deadline:
                        raise TimeoutError("artifact claim timed out") from exc
                    time.sleep(0.01)
            yield
        finally:
            try:
                if locked:
                    _unlock_descriptor(descriptor)
            finally:
                os.close(descriptor)


@contextmanager
def _in_process_claim(claim_path: Path, *, timeout_seconds: float) -> Iterator[None]:
    key = str(claim_path.resolve(strict=False))
    with _PROCESS_CLAIMS_GUARD:
        claim = _PROCESS_CLAIMS.setdefault(key, Lock())
    if not claim.acquire(timeout=timeout_seconds):
        raise TimeoutError("artifact claim timed out")
    try:
        yield
    finally:
        claim.release()


def _ensure_lock_byte(descriptor: int) -> None:
    """Ensure Windows byte-range locking has a stable first byte to lock.

    Concurrent creators can race between the empty-size check and the seed write.
    Once another process has seeded (and possibly locked) byte zero, a failed
    write is acceptable if the file is non-empty; callers then contend on the
    advisory lock rather than failing claim acquisition outright.
    """

    if os.fstat(descriptor).st_size == 0:
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            os.write(descriptor, b"\0")
        except OSError:
            if os.fstat(descriptor).st_size == 0:
                raise
    os.lseek(descriptor, 0, os.SEEK_SET)


def _lock_descriptor(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_descriptor(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


def _is_lock_contention(exc: OSError) -> bool:
    """Recognize nonblocking advisory-lock conflict on Windows and POSIX."""

    return exc.errno in {errno.EACCES, errno.EAGAIN} or getattr(exc, "winerror", None) in {
        32,  # ERROR_SHARING_VIOLATION
        33,  # ERROR_LOCK_VIOLATION
    }
