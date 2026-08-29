"""Focused safety contracts for Core-owned local immutable snapshots."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_secure_reader_rejects_out_of_root_symlink_before_body_read(tmp_path: Path) -> None:
    from corpus_ingest_core.secure_local_snapshot import secure_read_bytes

    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("OUTSIDE-BODY-SENTINEL", encoding="utf-8")
    linked = root / "linked.txt"
    try:
        linked.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc.__class__.__name__}")

    assert secure_read_bytes(root, linked, max_bytes=1024) is None


def test_secure_reader_returns_core_derived_regular_file_bytes(tmp_path: Path) -> None:
    from corpus_ingest_core.secure_local_snapshot import secure_read_bytes

    root = tmp_path / "root"
    root.mkdir()
    expected = root / "source.json"
    expected.write_bytes(b'{"stable": true}')

    assert secure_read_bytes(root, expected, max_bytes=1024) == b'{"stable": true}'


def test_secure_reader_rejects_mocked_windows_reparse_before_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.secure_local_snapshot as snapshots

    root = tmp_path / "root"
    root.mkdir()
    expected = root / "source.json"
    expected.write_text("REPARSE-BODY-SENTINEL", encoding="utf-8")
    target_inode = expected.lstat().st_ino
    original = snapshots._is_reparse
    monkeypatch.setattr(
        snapshots,
        "_is_reparse",
        lambda value: value.st_ino == target_inode or original(value),
    )

    assert snapshots.secure_read_bytes(root, expected, max_bytes=1024) is None


def test_secure_reader_rejects_opened_handle_identity_race(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import os
    import corpus_ingest_core.secure_local_snapshot as snapshots

    root = tmp_path / "root"
    root.mkdir()
    expected = root / "source.json"
    expected.write_text("RACE-BODY-SENTINEL", encoding="utf-8")
    original_fstat = os.fstat
    calls = 0

    def raced_fstat(descriptor: int):
        nonlocal calls
        calls += 1
        value = original_fstat(descriptor)
        if calls == 2:
            return SimpleNamespace(
                st_dev=value.st_dev,
                st_ino=value.st_ino + 1,
                st_mode=value.st_mode,
                st_size=value.st_size,
            )
        return value

    monkeypatch.setattr(snapshots.os, "fstat", raced_fstat)

    assert snapshots.secure_read_bytes(root, expected, max_bytes=1024) is None


def test_secure_directory_listing_rejects_out_of_root_directory_symlink(
    tmp_path: Path,
) -> None:
    from corpus_ingest_core.secure_local_snapshot import secure_directory_names

    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "EXTERNAL-ENUMERATION-SENTINEL.json").write_text("sentinel", encoding="utf-8")
    linked = root / "podcast"
    try:
        linked.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation is unavailable: {exc.__class__.__name__}")

    assert secure_directory_names(root, linked, max_entries=10) is None


def test_secure_reader_rejects_mocked_reparse_in_root_ancestor_chain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corpus_ingest_core.secure_local_snapshot as snapshots

    root = tmp_path / "root"
    root.mkdir()
    expected = root / "source.json"
    expected.write_text("ANCESTOR-SENTINEL", encoding="utf-8")
    parent_inode = root.parent.lstat().st_ino
    original = snapshots._is_reparse
    monkeypatch.setattr(
        snapshots,
        "_is_reparse",
        lambda value: value.st_ino == parent_inode or original(value),
    )

    assert snapshots.secure_read_bytes(root, expected, max_bytes=1024) is None


def test_canonical_and_review_discovery_reject_directory_symlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core import storage
    from corpus_ingest_core.canonical_transcript import resolve_canonical_transcript_asset_paths
    from corpus_ingest_core.semantic_review_artifact import semantic_review_candidates

    transcript_root = tmp_path / "transcripts"
    transcript_root.mkdir()
    review_root = tmp_path / "reviews"
    review_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "EP1__Outside.json").write_text("EXTERNAL-TRANSCRIPT-SENTINEL", encoding="utf-8")
    (outside / "20260101-000000__show__EP1.semantic-review.json").write_text(
        "EXTERNAL-REVIEW-SENTINEL", encoding="utf-8"
    )
    transcript_link = transcript_root / "show"
    review_link = review_root / "linked"
    try:
        transcript_link.symlink_to(outside, target_is_directory=True)
        review_link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation is unavailable: {exc.__class__.__name__}")
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", transcript_root)

    assert resolve_canonical_transcript_asset_paths("show", "EP1") is None
    assert semantic_review_candidates(review_link, "show", "EP1") == ([], [])


def test_secure_directory_listing_rejects_mocked_reparse_and_identity_race(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import os
    import corpus_ingest_core.secure_local_snapshot as snapshots

    root = tmp_path / "root"
    directory = root / "podcast"
    directory.mkdir(parents=True)
    (directory / "entry.json").write_text("DIRECTORY-SENTINEL", encoding="utf-8")
    target_inode = directory.lstat().st_ino
    original_is_reparse = snapshots._is_reparse
    monkeypatch.setattr(
        snapshots,
        "_is_reparse",
        lambda value: value.st_ino == target_inode or original_is_reparse(value),
    )
    assert snapshots.secure_directory_names(root, directory, max_entries=10) is None

    monkeypatch.undo()
    original_fstat = os.fstat
    calls = 0

    def raced_fstat(descriptor: int):
        nonlocal calls
        calls += 1
        value = original_fstat(descriptor)
        if calls == 2:
            return SimpleNamespace(
                st_dev=value.st_dev,
                st_ino=value.st_ino + 1,
                st_mode=value.st_mode,
                st_size=value.st_size,
            )
        return value

    monkeypatch.setattr(snapshots.os, "fstat", raced_fstat)
    assert snapshots.secure_directory_names(root, directory, max_entries=10) is None


def test_directory_listing_rejects_names_absent_after_enumeration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Post-validation rejects an enumerator result absent from the checked directory."""
    import corpus_ingest_core.secure_local_snapshot as snapshots

    root = tmp_path / "root"
    directory = root / "podcast"
    directory.mkdir(parents=True)
    (directory / "safe.json").write_text("safe", encoding="utf-8")
    original_listdir = snapshots.os.listdir

    def swapped_names(path: object) -> list[str]:
        if path == directory:
            return ["HOSTILE-SWAP-RESTORE-SENTINEL.json"]
        return original_listdir(path)

    monkeypatch.setattr(snapshots.os, "name", "nt")
    monkeypatch.setattr(snapshots, "_open_directory_descriptor", lambda path: 0)
    monkeypatch.setattr(snapshots.os, "fstat", lambda descriptor: directory.lstat())
    monkeypatch.setattr(snapshots, "_opened_handle_is_contained", lambda root, descriptor: True)
    monkeypatch.setattr(snapshots.os, "listdir", swapped_names)
    monkeypatch.setattr(snapshots.os, "close", lambda descriptor: None)

    assert snapshots.secure_directory_names(root, directory, max_entries=10) is None


def test_lineage_sidecar_source_and_config_reads_only_use_secure_snapshot_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corpus_ingest_core import storage
    import corpus_ingest_core.verified_research_lineage as lineage

    corpus = tmp_path / "corpus"
    source = tmp_path / "transcripts" / "show" / "EP1.json"
    source.parent.mkdir(parents=True)
    source.write_text("SOURCE-BODY-SENTINEL", encoding="utf-8")
    config = tmp_path / "config.yaml"
    config.write_text("CONFIG-BODY-SENTINEL", encoding="utf-8")
    monkeypatch.setattr(storage, "CORPUS_DIR", corpus)
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    calls: list[tuple[Path, Path]] = []

    def deny_snapshot(root: Path, path: Path, *, max_bytes: int) -> None:
        calls.append((root, path))
        return None

    monkeypatch.setattr(lineage, "secure_read_bytes", deny_snapshot)

    sidecar = lineage.lineage_path("show", "EP1")
    assert lineage._load_existing_sidecar(sidecar, "show", "EP1") is None
    with pytest.raises(lineage.VerifiedResearchReportInputError):
        lineage._read_bytes(source, "transcript")
    assert lineage._config_identity(config)["sha256"] is None
    assert (corpus, sidecar) in calls
    assert (tmp_path / "transcripts", source) in calls
    assert (config.parent, config) in calls
