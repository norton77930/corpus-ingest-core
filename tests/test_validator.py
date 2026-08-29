from __future__ import annotations

import json
import sys


def _use_tmp_transcripts_dir(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    transcript_dir = tmp_path / "transcripts"
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", transcript_dir)
    return transcript_dir


def _write_transcript(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    segments=None,
    segment_count=None,
    completed=True,
    include_legacy_metadata=False,
):
    from corpus_ingest_core.storage import transcript_asset_paths

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 0.0, "end": 1.25, "text": "第一段"},
            {"id": 2, "start": 65.123, "end": 66.5, "text": "第二段"},
        ]
    if segment_count is None:
        segment_count = len(segments)

    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text(
        "".join(f"{segment['text']}\n" for segment in segments), encoding="utf-8"
    )
    paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,250\n第一段\n" if segments else "",
        encoding="utf-8",
    )
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "model": "tiny",
        "language": "zh",
        "device": "cpu",
        "compute_type": "int8",
        "vad_filter": False,
        "text_path": str(paths.text_path),
        "srt_path": str(paths.srt_path),
        "json_path": str(paths.json_path),
        "segment_count": segment_count,
        "segments": segments,
    }
    if not include_legacy_metadata:
        payload.update(
            {
                "generated_at": "2026-06-21T00:00:00Z",
                "source_audio_path": "data/audio/gooaye/EP672.mp3",
                "source_audio_size_bytes": 1234,
                "last_segment_end_seconds": segments[-1]["end"] if segments else None,
                "completed": completed,
            }
        )
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return paths


def test_validate_transcript_returns_valid_for_complete_outputs(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    paths = _write_transcript(monkeypatch, tmp_path)

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is True
    assert result.status == "valid"
    assert result.segment_count == 2
    assert result.last_segment_end_seconds == 66.5
    assert result.transcript_text_length > 0
    assert result.problems == []
    assert result.paths["json"] == str(paths.json_path)


def test_validate_transcript_missing_when_json_absent(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)

    result = validate_transcript("gooaye", "EP999")

    assert result.valid is False
    assert result.status == "missing"
    assert result.segment_count == 0
    assert result.problems


def test_validate_transcript_incomplete_when_txt_missing(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    paths = _write_transcript(monkeypatch, tmp_path)
    paths.text_path.unlink()

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is False
    assert result.status == "incomplete_outputs"
    assert any("TXT" in problem for problem in result.problems)


def test_validate_transcript_incomplete_when_srt_missing(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    paths = _write_transcript(monkeypatch, tmp_path)
    paths.srt_path.unlink()

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is False
    assert result.status == "incomplete_outputs"
    assert any("SRT" in problem for problem in result.problems)


def test_validate_transcript_corrupt_when_json_invalid(monkeypatch, tmp_path):
    from corpus_ingest_core.storage import transcript_asset_paths
    from corpus_ingest_core.validator import validate_transcript

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", "EP672 title")
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("文字", encoding="utf-8")
    paths.srt_path.write_text("字幕", encoding="utf-8")
    paths.json_path.write_text("{not-json", encoding="utf-8")

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is False
    assert result.status == "corrupt"
    assert any("JSON" in problem for problem in result.problems)


def test_validate_transcript_empty_when_segments_empty(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    _write_transcript(
        monkeypatch,
        tmp_path,
        episode_ref="smoke-test",
        title="smoke-test",
        segments=[],
        segment_count=0,
    )

    result = validate_transcript("gooaye", "smoke-test")

    assert result.valid is True
    assert result.status == "empty"
    assert result.segment_count == 0
    assert result.last_segment_end_seconds is None


def test_validate_transcript_warns_when_part_file_exists(monkeypatch, tmp_path):
    from corpus_ingest_core.validator import validate_transcript

    paths = _write_transcript(monkeypatch, tmp_path)
    paths.json_path.with_name(f"{paths.json_path.name}.part").write_text(
        "partial", encoding="utf-8"
    )

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is True
    assert result.status == "valid"
    assert any(".part" in warning for warning in result.warnings)


def test_validate_transcript_partial_when_segment_count_mismatch(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.validator import validate_transcript

    _write_transcript(monkeypatch, tmp_path, segment_count=99)

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is False
    assert result.status == "partial"
    assert any("segment_count" in problem for problem in result.problems)


def test_validate_transcript_legacy_metadata_warns_but_stays_valid(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.validator import validate_transcript

    _write_transcript(monkeypatch, tmp_path, include_legacy_metadata=True)

    result = validate_transcript("gooaye", "EP672")

    assert result.valid is True
    assert result.status == "valid"
    assert any("legacy" in warning for warning in result.warnings)


def test_validate_transcript_cli_outputs_json(monkeypatch, capsys):
    from corpus_ingest_core.models import TranscriptValidationResult
    from scripts import validate_transcript

    result = TranscriptValidationResult(
        podcast_id="gooaye",
        episode_ref="EP672",
        valid=True,
        status="valid",
        segment_count=2,
        last_segment_end_seconds=66.5,
        transcript_text_length=6,
        problems=[],
        warnings=[],
        paths={"json": "transcript.json"},
    )
    captured = {}

    def fake_validate(*args):
        captured["args"] = args
        return result

    monkeypatch.setattr(validate_transcript, "validate_transcript", fake_validate)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_transcript.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
        ],
    )

    validate_transcript.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["podcast_id"] == "gooaye"
    assert payload["status"] == "valid"
    assert captured["args"] == ("gooaye", "EP672")
