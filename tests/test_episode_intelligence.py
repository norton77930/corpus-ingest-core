from __future__ import annotations

import json
import sys

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "MENTIONS_DIR", tmp_path / "mentions")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")


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
    from corpus_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {
                "id": 1,
                "start": 83.1,
                "end": 90.2,
                "text": "今天聊到台積電、半導體和 AI 需求。",
            },
            {
                "id": 2,
                "start": 305.0,
                "end": 312.0,
                "text": "利率和通膨對估值還是有影響。",
            },
            {
                "id": 3,
                "start": 620.0,
                "end": 640.0,
                "text": "也提到 GPU 供應鏈的不確定性。",
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
            "1\n00:01:23,000 --> 00:01:30,000\n字幕\n" if segments else "",
            encoding="utf-8",
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
                "generated_at": "2026-06-28T00:00:00Z",
                "source_audio_path": "data/audio/gooaye/EP672__EP672.mp3",
                "source_audio_size_bytes": 123,
                "segments": segments,
            }
            paths.json_path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
    return paths


def _write_mentions(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
):
    from corpus_ingest_core.storage import mention_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = mention_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "extraction_mode": "deterministic-rules",
        "segment_count": 3,
        "mention_count": 3,
        "mentions": [
            {
                "type": "company",
                "text": "台積電",
                "normalized_text": "台積電",
                "count": 1,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            },
            {
                "type": "industry",
                "text": "半導體",
                "normalized_text": "半導體",
                "count": 1,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
            },
            {
                "type": "macro_topic",
                "text": "利率",
                "normalized_text": "利率",
                "count": 1,
                "confidence": "rule",
                "evidence": [
                    {
                        "segment_id": 2,
                        "start": 305.0,
                        "end": 312.0,
                        "timestamp": "[00:05:05 - 00:05:12]",
                        "text": "利率和通膨對估值還是有影響。",
                    }
                ],
            },
        ],
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# mentions", encoding="utf-8")
    return paths


def test_generate_episode_intelligence_report_writes_json_and_markdown(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.episode_intelligence import (
        generate_episode_intelligence_report,
    )

    _write_transcript(monkeypatch, tmp_path)
    _write_mentions(monkeypatch, tmp_path)

    asset = generate_episode_intelligence_report("gooaye", "EP672")

    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))
    markdown = asset.report_markdown_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.already_exists is False
    assert asset.transcript_status == "valid"
    assert asset.segment_count == 3
    assert asset.source_status_warnings == []
    assert payload["report_mode"] == "deterministic-episode-intelligence-v1"
    assert payload["source_status"]["mentions"] == "available"
    assert payload["mentions_by_type"]["company"][0]["text"] == "台積電"
    assert payload["industry_clues"][0]["text"] == "半導體"
    assert payload["macro_variables"][0]["text"] == "利率"
    assert payload["timeline"][0]["evidence"][0]["timestamp"] == "[00:01:23 - 00:01:30]"
    assert "# Gooaye 股癌 - EP672 Episode Intelligence Report" in markdown
    assert "## Explicit Mentions" in markdown
    assert "[00:01:23 - 00:01:30]" in markdown
    assert "本報告不構成投資建議" in markdown


def test_generate_episode_intelligence_report_warns_when_mentions_missing(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.episode_intelligence import (
        generate_episode_intelligence_report,
    )

    _write_transcript(monkeypatch, tmp_path)

    asset = generate_episode_intelligence_report("gooaye", "EP672")
    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))

    assert payload["source_status"]["mentions"] == "missing"
    assert "mentions artifact missing" in asset.source_status_warnings[0]
    assert payload["mentions_by_type"] == {}


def test_generate_episode_intelligence_report_rejects_invalid_transcripts(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.episode_intelligence import (
        generate_episode_intelligence_report,
    )
    from corpus_ingest_core.errors import TranscriptMissingError, TranscriptParseError

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    with pytest.raises(TranscriptMissingError):
        generate_episode_intelligence_report("gooaye", "EP999")

    _write_transcript(monkeypatch, tmp_path, json_text="{not-json")
    with pytest.raises(TranscriptParseError):
        generate_episode_intelligence_report("gooaye", "EP672")

    _write_transcript(monkeypatch, tmp_path, episode_ref="EP673", write_srt=False)
    with pytest.raises(TranscriptMissingError):
        generate_episode_intelligence_report("gooaye", "EP673")


def test_generate_episode_intelligence_report_handles_partial_transcript(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.episode_intelligence import (
        generate_episode_intelligence_report,
    )
    from corpus_ingest_core.errors import TranscriptParseError

    _write_transcript(monkeypatch, tmp_path, completed=False)

    with pytest.raises(TranscriptParseError, match="partial"):
        generate_episode_intelligence_report("gooaye", "EP672")

    asset = generate_episode_intelligence_report(
        "gooaye", "EP672", allow_partial=True
    )
    payload = json.loads(asset.report_json_path.read_text(encoding="utf-8"))

    assert asset.transcript_status == "partial"
    assert payload["report_status"] == "partial-draft"
    assert "partial transcript" in payload["risks_and_uncertainties"][0]


def test_generate_episode_intelligence_report_reuses_existing_without_force(
    monkeypatch, tmp_path
):
    from corpus_ingest_core.episode_intelligence import (
        generate_episode_intelligence_report,
    )
    from corpus_ingest_core.storage import episode_intelligence_report_asset_paths

    _write_transcript(monkeypatch, tmp_path)
    paths = episode_intelligence_report_asset_paths("gooaye", "EP672", "EP672 title")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("existing json", encoding="utf-8")
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")

    asset = generate_episode_intelligence_report("gooaye", "EP672", force=False)

    assert asset.generated is False
    assert asset.already_exists is True
    assert paths.json_path.read_text(encoding="utf-8") == "existing json"

    regenerated = generate_episode_intelligence_report("gooaye", "EP672", force=True)
    assert regenerated.generated is True
    assert "existing json" not in paths.json_path.read_text(encoding="utf-8")


def test_episode_intelligence_report_path_removes_illegal_characters_and_emoji():
    from corpus_ingest_core.storage import episode_intelligence_report_asset_paths

    paths = episode_intelligence_report_asset_paths(
        "gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok '
    )

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "EP672__bad_title_ok.intelligence.json"
    assert paths.markdown_path.name == "EP672__bad_title_ok.intelligence.md"


def test_episode_intelligence_cli_parses_options_and_outputs_json(
    monkeypatch, capsys, tmp_path
):
    from scripts import generate_episode_intelligence_report

    from corpus_ingest_core.models import EpisodeIntelligenceReportAsset

    asset = EpisodeIntelligenceReportAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        report_json_path=tmp_path / "report.json",
        report_markdown_path=tmp_path / "report.md",
        transcript_status="valid",
        segment_count=3,
        generated=True,
        already_exists=False,
        source_status_warnings=[],
    )
    captured = {}

    def fake_generate(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(
        generate_episode_intelligence_report,
        "generate_episode_intelligence_report",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_episode_intelligence_report.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--force",
            "--allow-partial",
            "--window-seconds",
            "600",
            "--max-evidence-per-section",
            "3",
        ],
    )

    generate_episode_intelligence_report.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["report_json_path"] == str(tmp_path / "report.json")
    assert payload["generated"] is True
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "force": True,
        "allow_partial": True,
        "window_seconds": 600,
        "max_evidence_per_section": 3,
    }
