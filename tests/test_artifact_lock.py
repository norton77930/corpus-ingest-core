"""Cross-process regression coverage for persistent artifact claims."""

from __future__ import annotations

import multiprocessing
from multiprocessing.synchronize import Event
from pathlib import Path

import pytest

# Liveness budget for the spawned worker, not a correctness bound. The child
# has to start a fresh interpreter, import a 39k-line package, and take an OS
# lock before it can signal. Ten seconds was enough on an idle laptop; under
# `pytest --cov` on a two-core shared CI runner it is not, and this test went
# red once for exactly that reason with nothing wrong in the lock.
#
# What the test actually proves is untouched by this number: the parent still
# asserts that a second claim on the same episode raises TimeoutError with
# timeout_seconds=0.1 while the child holds it. A generous startup budget only
# removes a false failure -- if the lock genuinely broke, the parent's claim
# would succeed and the assertion would fail no matter how long we waited.
WORKER_STARTUP_TIMEOUT_SECONDS = 60.0


def _hold_artifact_claim(lock_path: str, acquired: Event, release: Event) -> None:
    """Spawn-safe worker that holds a claim until the parent releases it."""

    from corpus_ingest_core.artifact_lock import exclusive_artifact_claim

    with exclusive_artifact_claim(Path(lock_path), timeout_seconds=10.0):
        acquired.set()
        release.wait(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)


def _hold_episode_writer_claim(corpus_dir: str, acquired: Event, release: Event) -> None:
    """Spawn-safe worker for the podcast-and-episode shared claim key."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.episode_claim import episode_writer_claim

    storage.CORPUS_DIR = Path(corpus_dir)
    with episode_writer_claim("gooaye", "EP700", timeout_seconds=10.0):
        acquired.set()
        release.wait(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)


def test_spawned_process_blocks_same_episode_writer_claim(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Same episode blocks cross-process despite disparate fixed output paths."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.episode_claim import episode_writer_claim

    monkeypatch.setattr(storage, "CORPUS_DIR", tmp_path / "corpus")
    context = multiprocessing.get_context("spawn")
    acquired = context.Event()
    release = context.Event()
    worker = context.Process(
        target=_hold_episode_writer_claim,
        args=(str(storage.CORPUS_DIR), acquired, release),
    )
    worker.start()
    try:
        assert acquired.wait(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
        with pytest.raises(TimeoutError, match="artifact claim timed out"):
            with episode_writer_claim("gooaye", "EP700", timeout_seconds=0.1):
                pytest.fail("same episode claim must remain exclusive")
    finally:
        release.set()
        worker.join(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
    assert worker.exitcode == 0


def test_spawned_process_blocks_same_artifact_claim(tmp_path: Path) -> None:
    """Windows/POSIX OS lock remains authoritative beyond process-local mutexes."""

    from corpus_ingest_core.artifact_lock import exclusive_artifact_claim

    context = multiprocessing.get_context("spawn")
    acquired = context.Event()
    release = context.Event()
    lock_path = tmp_path / ".EP700.checkpoint.workflow.claim"
    worker = context.Process(
        target=_hold_artifact_claim,
        args=(str(lock_path), acquired, release),
    )
    worker.start()
    try:
        assert acquired.wait(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
        with pytest.raises(TimeoutError, match="artifact claim timed out"):
            with exclusive_artifact_claim(lock_path, timeout_seconds=0.1):
                pytest.fail("same artifact claim must remain exclusive")
    finally:
        release.set()
        worker.join(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=WORKER_STARTUP_TIMEOUT_SECONDS)
    assert worker.exitcode == 0


@pytest.mark.parametrize(
    ("podcast_id", "episode_ref"),
    [
        ("../escape", "EP700"),
        ("gooaye", "../EP700"),
        ("C:\\escape", "EP700"),
        ("gooaye", "EP/700"),
        ("CON", "EP700"),
        ("gooaye", "NUL"),
    ],
)
def test_red_episode_claim_rejects_unsafe_identity_before_any_mkdir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    podcast_id: str,
    episode_ref: str,
) -> None:
    """Claim addressing must never turn untrusted identifiers into directories."""

    from corpus_ingest_core import storage
    from corpus_ingest_core.episode_claim import episode_writer_claim

    corpus_dir = tmp_path / "corpus"
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus_dir)

    with pytest.raises(ValueError, match="episode writer claim identity is invalid"):
        with episode_writer_claim(podcast_id, episode_ref):
            pytest.fail("unsafe episode identity must not be claimable")

    assert not corpus_dir.exists()
