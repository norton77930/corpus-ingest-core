from __future__ import annotations

from pathlib import Path
import re

from corpus_ingest_core import storage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "corpus_ingest_core"

_OLD_ALPHABETS = (
    r"^[A-Za-z0-9][A-Za-z0-9-]*$",
    r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$",
    r"[A-Za-z0-9][A-Za-z0-9-]{0,127}",
    r"[A-Za-z0-9][A-Za-z0-9-]*",
)


def test_is_safe_episode_ref_accepts_youtube_ids_and_existing_refs() -> None:
    assert storage.is_safe_episode_ref("dQw4w9WgXcQ") is True
    assert storage.is_safe_episode_ref("abc_def-12") is True
    assert storage.is_safe_episode_ref("EP678") is True
    assert storage.is_safe_episode_ref("2071290493581840707") is True


def test_is_safe_episode_ref_rejects_separators_and_spaces() -> None:
    assert storage.is_safe_episode_ref("ab.cd") is False
    assert storage.is_safe_episode_ref("ab/cd") is False
    assert storage.is_safe_episode_ref("ab cd") is False
    assert storage.is_safe_episode_ref("") is False
    assert storage.is_safe_episode_ref(None) is False


def test_safe_episode_ref_error_mentions_underscore() -> None:
    try:
        storage._safe_episode_ref("bad.id")
    except ValueError as exc:
        assert "_" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_no_second_old_episode_ref_alphabet_in_src() -> None:
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        if path.name == "storage.py":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in _OLD_ALPHABETS:
            if pattern in text:
                offenders.append(f"{path.relative_to(ROOT)}:{pattern}")
    assert offenders == []


def test_verified_report_identifier_accepts_underscore() -> None:
    from corpus_ingest_core.verified_research_report import _validate_identifier

    _validate_identifier("abc_def-hij", "episode_ref")
    try:
        _validate_identifier("bad.id", "episode_ref")
    except Exception as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("expected invalid episode_ref")
