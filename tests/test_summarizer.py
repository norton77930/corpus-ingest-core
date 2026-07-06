from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")


def _write_transcript(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    segments=None,
    segment_count=None,
    completed=None,
):
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 0.0, "end": 12.0, "text": "第一段文字"},
            {"id": 2, "start": 305.0, "end": 330.0, "text": "第二段比較長的文字"},
            {"id": 3, "start": 610.0, "end": 640.0, "text": "第三段文字"},
        ]
    if segment_count is None:
        segment_count = len(segments)

    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text(
        "\n".join(segment["text"] for segment in segments), encoding="utf-8"
    )
    paths.srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:12,000\n第一段文字\n" if segments else "",
        encoding="utf-8",
    )
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "language": "zh",
        "text_path": str(paths.text_path),
        "srt_path": str(paths.srt_path),
        "json_path": str(paths.json_path),
        "segment_count": segment_count,
        "segments": segments,
    }
    if completed is not None:
        payload["completed"] = completed
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return paths


def test_summarize_episode_generates_markdown_from_transcript(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer

    _write_transcript(monkeypatch, tmp_path)

    asset = summarizer.summarize_episode("gooaye", "EP672")

    content = asset.summary_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.summary_mode == "extractive-template"
    assert asset.segment_count == 3
    assert "# Gooaye 股癌 - EP672 摘要" in content
    assert "## Metadata" in content
    assert "deterministic extractive-template summarizer" in content


def test_summarize_episode_raises_when_transcript_missing(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.errors import TranscriptMissingError

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    with pytest.raises(TranscriptMissingError):
        summarizer.summarize_episode("gooaye", "EP999")


def test_summarize_episode_raises_when_transcript_json_invalid(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.errors import TranscriptParseError
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", "EP672 title")
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("文字", encoding="utf-8")
    paths.srt_path.write_text("字幕", encoding="utf-8")
    paths.json_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(TranscriptParseError):
        summarizer.summarize_episode("gooaye", "EP672")


def test_summarize_episode_generates_empty_segment_summary(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer

    _write_transcript(
        monkeypatch,
        tmp_path,
        episode_ref="smoke-test",
        title="smoke-test",
        segments=[],
        segment_count=0,
    )

    asset = summarizer.summarize_episode("gooaye", "smoke-test")

    content = asset.summary_path.read_text(encoding="utf-8")
    assert asset.segment_count == 0
    assert "此 transcript 沒有可摘要的語音 segments。" in content


def test_summarize_episode_generates_timeline_and_quotes(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer

    _write_transcript(monkeypatch, tmp_path)

    asset = summarizer.summarize_episode(
        "gooaye", "EP672", max_quotes=2, window_seconds=300
    )

    content = asset.summary_path.read_text(encoding="utf-8")
    assert "## 時間軸摘要" in content
    assert "### 00:00:00 - 00:05:00" in content
    assert "### 00:05:00 - 00:10:00" in content
    assert "## 可引用片段" in content
    assert "1. `[00:00:00 - 00:00:12]` 第一段文字" in content
    assert "2. `[00:05:05 - 00:05:30]` 第二段比較長的文字" in content


def test_summarize_episode_skips_existing_summary_without_force(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.storage import summary_asset_path

    _write_transcript(monkeypatch, tmp_path)
    path = summary_asset_path("gooaye", "EP672", "EP672 title")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("existing", encoding="utf-8")

    asset = summarizer.summarize_episode("gooaye", "EP672", force=False)

    assert path.read_text(encoding="utf-8") == "existing"
    assert asset.generated is False
    assert asset.already_exists is True


def test_summarize_episode_force_regenerates_existing_summary(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.storage import summary_asset_path

    _write_transcript(monkeypatch, tmp_path)
    path = summary_asset_path("gooaye", "EP672", "EP672 title")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("existing", encoding="utf-8")

    asset = summarizer.summarize_episode("gooaye", "EP672", force=True)

    assert "existing" not in path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.already_exists is False


def test_summarize_episode_rejects_partial_by_default(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.errors import TranscriptParseError

    _write_transcript(monkeypatch, tmp_path, completed=False)

    with pytest.raises(TranscriptParseError, match="partial"):
        summarizer.summarize_episode("gooaye", "EP672")


def test_summarize_episode_allows_partial_when_requested(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer

    _write_transcript(monkeypatch, tmp_path, completed=False)

    asset = summarizer.summarize_episode("gooaye", "EP672", allow_partial=True)

    content = asset.summary_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert "Validation status: partial" in content


def test_summary_path_removes_illegal_characters_and_emoji():
    from podcast_ingest_core.storage import summary_asset_path

    path = summary_asset_path("gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok ')

    assert not any(character in path.name for character in '<>:"/\\|?*')
    assert "🐣" not in path.name
    assert path.name == "EP672__bad_title_ok.md"


def test_summarize_episode_cleans_part_file_on_write_failure(monkeypatch, tmp_path):
    import podcast_ingest_core.summarizer as summarizer
    from podcast_ingest_core.errors import SummaryFailedError
    from podcast_ingest_core.storage import summary_asset_path

    _write_transcript(monkeypatch, tmp_path)
    path = summary_asset_path("gooaye", "EP672", "EP672 title")
    original_write_text = Path.write_text

    def fail_part_write(self, *args, **kwargs):
        if self.name.endswith(".part"):
            raise OSError("disk full")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_part_write)

    with pytest.raises(SummaryFailedError):
        summarizer.summarize_episode("gooaye", "EP672")

    assert not path.exists()
    assert not list(path.parent.glob("*.part"))


def test_summarize_cli_parses_options_and_outputs_json(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import SummaryAsset
    from scripts import summarize_episode

    asset = SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        summary_path=tmp_path / "summary.md",
        transcript_json_path=tmp_path / "transcript.json",
        transcript_text_path=tmp_path / "transcript.txt",
        segment_count=2,
        summary_mode="extractive-template",
        generated=True,
        already_exists=False,
    )
    captured = {}

    def fake_summarize(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(summarize_episode, "summarize_episode", fake_summarize)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_episode.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--force",
            "--max-quotes",
            "5",
            "--window-seconds",
            "600",
            "--allow-partial",
        ],
    )

    summarize_episode.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["podcast_id"] == "gooaye"
    assert payload["summary_mode"] == "extractive-template"
    assert payload["generated"] is True
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "force": True,
        "max_quotes": 5,
        "window_seconds": 600,
        "allow_partial": True,
    }
