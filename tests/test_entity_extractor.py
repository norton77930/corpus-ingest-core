from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")


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
    write_text=True,
    write_srt=True,
    write_json=True,
    json_text=None,
):
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {
                "id": 1,
                "start": 83.1,
                "end": 90.2,
                "text": "NVIDIA 跟台積電今天都有被提到，利率也很重要。",
            },
            {
                "id": 2,
                "start": 125.0,
                "end": 140.0,
                "text": "NVIDIA 在 AI 和 GPU 這塊還是很強。",
            },
            {
                "id": 3,
                "start": 305.0,
                "end": 312.0,
                "text": "日本跟東京旅遊也聊了一下。",
            },
        ]
    if segment_count is None:
        segment_count = len(segments)

    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    if write_text:
        paths.text_path.write_text(
            "\n".join(segment["text"] for segment in segments), encoding="utf-8"
        )
    if write_srt:
        paths.srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\n字幕\n", encoding="utf-8"
        )
    if write_json:
        if json_text is not None:
            paths.json_path.write_text(json_text, encoding="utf-8")
        else:
            payload = {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "language": "zh",
                "segment_count": segment_count,
                "completed": completed,
                "segments": segments,
            }
            paths.json_path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
    return paths


def test_extract_mentions_generates_json_and_markdown(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor

    _write_transcript(monkeypatch, tmp_path)

    asset = extractor.extract_mentions("gooaye", "EP672")

    payload = json.loads(asset.mentions_json_path.read_text(encoding="utf-8"))
    markdown = asset.mentions_markdown_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.extraction_mode == "deterministic-rules"
    assert asset.mention_count >= 5
    assert payload["extraction_mode"] == "deterministic-rules"
    assert "NVIDIA" in {mention["text"] for mention in payload["mentions"]}
    assert "# Gooaye 股癌 - EP672 Mentions" in markdown
    assert "本檔案不構成投資建議" in markdown


def test_extract_mentions_empty_transcript_generates_zero_mentions(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor

    _write_transcript(
        monkeypatch,
        tmp_path,
        episode_ref="smoke-test",
        title="smoke-test",
        segments=[],
        segment_count=0,
    )

    asset = extractor.extract_mentions("gooaye", "smoke-test")
    payload = json.loads(asset.mentions_json_path.read_text(encoding="utf-8"))

    assert asset.mention_count == 0
    assert payload["mentions"] == []


def test_extract_mentions_rejects_missing_transcript(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.errors import TranscriptMissingError

    _use_tmp_data_dirs(monkeypatch, tmp_path)

    with pytest.raises(TranscriptMissingError):
        extractor.extract_mentions("gooaye", "EP999")


def test_extract_mentions_rejects_corrupt_transcript(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.errors import TranscriptParseError

    _write_transcript(monkeypatch, tmp_path, json_text="{not-json")

    with pytest.raises(TranscriptParseError):
        extractor.extract_mentions("gooaye", "EP672")


def test_extract_mentions_rejects_incomplete_outputs(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.errors import TranscriptMissingError

    _write_transcript(monkeypatch, tmp_path, write_srt=False)

    with pytest.raises(TranscriptMissingError):
        extractor.extract_mentions("gooaye", "EP672")


def test_extract_mentions_rejects_partial_by_default(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.errors import TranscriptParseError

    _write_transcript(monkeypatch, tmp_path, completed=False)

    with pytest.raises(TranscriptParseError, match="partial"):
        extractor.extract_mentions("gooaye", "EP672")


def test_extract_mentions_allows_partial_when_requested(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor

    _write_transcript(monkeypatch, tmp_path, completed=False)

    asset = extractor.extract_mentions("gooaye", "EP672", allow_partial=True)

    assert asset.generated is True
    assert asset.mention_count > 0


def test_extract_mentions_counts_repeated_mentions_and_limits_evidence(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.entity_extractor as extractor

    _write_transcript(monkeypatch, tmp_path)

    asset = extractor.extract_mentions(
        "gooaye", "EP672", max_evidence_per_mention=1
    )
    payload = json.loads(asset.mentions_json_path.read_text(encoding="utf-8"))
    mentions = {mention["text"]: mention for mention in payload["mentions"]}

    assert mentions["NVIDIA"]["count"] == 2
    assert len(mentions["NVIDIA"]["evidence"]) == 1
    assert mentions["台積電"]["type"] == "company"
    assert mentions["利率"]["type"] == "macro_topic"
    assert mentions["NVIDIA"]["evidence"][0]["timestamp"] == "[00:01:23 - 00:01:30]"


def test_extract_mentions_skips_existing_artifacts_without_force(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.storage import mention_asset_paths

    _write_transcript(monkeypatch, tmp_path)
    paths = mention_asset_paths("gooaye", "EP672", "EP672 title")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = extractor.extract_mentions("gooaye", "EP672", force=False)

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == "existing json"


def test_extract_mentions_force_rewrites_existing_artifacts(monkeypatch, tmp_path):
    import podcast_ingest_core.entity_extractor as extractor
    from podcast_ingest_core.storage import mention_asset_paths

    _write_transcript(monkeypatch, tmp_path)
    paths = mention_asset_paths("gooaye", "EP672", "EP672 title")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = extractor.extract_mentions("gooaye", "EP672", force=True)

    assert asset.generated is True
    assert asset.already_exists is False
    assert "existing json" not in paths.json_path.read_text(encoding="utf-8")


def test_mention_path_removes_illegal_characters_and_emoji():
    from podcast_ingest_core.storage import mention_asset_paths

    paths = mention_asset_paths("gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok ')

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "EP672__bad_title_ok.mentions.json"
    assert paths.markdown_path.name == "EP672__bad_title_ok.mentions.md"


def test_extract_mentions_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from podcast_ingest_core.models import MentionExtractionAsset
    from scripts import extract_mentions

    asset = MentionExtractionAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        source_transcript_json_path=tmp_path / "transcript.json",
        mentions_json_path=tmp_path / "mentions.json",
        mentions_markdown_path=tmp_path / "mentions.md",
        mention_count=2,
        segment_count=3,
        extraction_mode="deterministic-rules",
        generated=True,
        already_exists=False,
    )
    captured = {}

    def fake_extract(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(extract_mentions, "extract_mentions", fake_extract)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "extract_mentions.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--force",
            "--allow-partial",
            "--max-evidence-per-mention",
            "3",
        ],
    )

    extract_mentions.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["mention_count"] == 2
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "force": True,
        "allow_partial": True,
        "max_evidence_per_mention": 3,
    }
