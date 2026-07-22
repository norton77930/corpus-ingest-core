"""Cross-process regression coverage for persistent artifact claims."""

from __future__ import annotations

from multiprocessing.synchronize import Event
from pathlib import Path

import multiprocessing

import pytest


def _hold_artifact_claim(lock_path: str, acquired: Event, release: Event) -> None:
    """Spawn-safe worker that holds a claim until the parent releases it."""

    from podcast_ingest_core.artifact_lock import exclusive_artifact_claim

    with exclusive_artifact_claim(Path(lock_path), timeout_seconds=10.0):
        acquired.set()
        release.wait(timeout=10.0)


def _hold_episode_writer_claim(
    corpus_dir: str, acquired: Event, release: Event
) -> None:
    """Spawn-safe worker for the podcast-and-episode shared claim key."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.episode_claim import episode_writer_claim

    storage.CORPUS_DIR = Path(corpus_dir)
    with episode_writer_claim("gooaye", "EP700", timeout_seconds=10.0):
        acquired.set()
        release.wait(timeout=10.0)


def test_spawned_process_blocks_same_episode_writer_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same episode blocks cross-process despite disparate fixed output paths."""

    from podcast_ingest_core import storage
    from podcast_ingest_core.episode_claim import episode_writer_claim

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
        assert acquired.wait(timeout=10.0)
        with pytest.raises(TimeoutError, match="artifact claim timed out"):
            with episode_writer_claim("gooaye", "EP700", timeout_seconds=0.1):
                pytest.fail("same episode claim must remain exclusive")
    finally:
        release.set()
        worker.join(timeout=10.0)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=10.0)
    assert worker.exitcode == 0


def test_spawned_process_blocks_same_artifact_claim(tmp_path: Path) -> None:
    """Windows/POSIX OS lock remains authoritative beyond process-local mutexes."""

    from podcast_ingest_core.artifact_lock import exclusive_artifact_claim

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
        assert acquired.wait(timeout=10.0)
        with pytest.raises(TimeoutError, match="artifact claim timed out"):
            with exclusive_artifact_claim(lock_path, timeout_seconds=0.1):
                pytest.fail("same artifact claim must remain exclusive")
    finally:
        release.set()
        worker.join(timeout=10.0)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=10.0)
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

    from podcast_ingest_core import storage
    from podcast_ingest_core.episode_claim import episode_writer_claim

    corpus_dir = tmp_path / "corpus"
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus_dir)

    with pytest.raises(ValueError, match="episode writer claim identity is invalid"):
        with episode_writer_claim(podcast_id, episode_ref):
            pytest.fail("unsafe episode identity must not be claimable")

    assert not corpus_dir.exists()
