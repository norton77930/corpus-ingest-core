from pathlib import Path
from types import SimpleNamespace
import importlib
import json
import sys

import pytest

from podcast_ingest_core.models import AudioAsset


class FakeSegment:
    def __init__(self, segment_id, start, end, text):
        self.id = segment_id
        self.start = start
        self.end = end
        self.text = text


class FakeWhisperModel:
    constructors = []
    calls = []

    def __init__(self, model_name, device="cpu", compute_type="int8"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.__class__.constructors.append(
            {
                "model_name": model_name,
                "device": device,
                "compute_type": compute_type,
            }
        )

    def transcribe(self, audio_path, language=None, beam_size=5, vad_filter=False):
        self.__class__.calls.append(
            {
                "audio_path": audio_path,
                "language": language,
                "beam_size": beam_size,
                "model_name": self.model_name,
                "vad_filter": vad_filter,
            }
        )
        segments = (
            segment
            for segment in [
                FakeSegment(1, 0.0, 1.25, "第一段"),
                FakeSegment(2, 65.123, 66.5, "第二段"),
            ]
        )
        return segments, SimpleNamespace(language=language)


def _audio_asset(tmp_path, *, exists=True, title="EP672 | 🐣"):
    audio_path = tmp_path / "audio.mp3"
    if exists:
        audio_path.write_bytes(b"audio")
    return AudioAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title=title,
        source_url="https://example.com/audio.mp3",
        local_path=audio_path,
        content_type="audio/mpeg",
        size_bytes=audio_path.stat().st_size if audio_path.exists() else None,
        downloaded=False,
        already_exists=True,
    )


def _use_tmp_transcripts_dir(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    transcript_dir = tmp_path / "transcripts"
    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", transcript_dir)
    return transcript_dir


def _install_fake_faster_whisper(monkeypatch, model_class=FakeWhisperModel):
    import podcast_ingest_core.transcriber as transcriber

    if hasattr(model_class, "constructors"):
        model_class.constructors.clear()
    if hasattr(model_class, "calls"):
        model_class.calls.clear()
    monkeypatch.setattr(transcriber, "_load_whisper_model_class", lambda: model_class)


def test_transcribe_episode_downloads_audio_asset(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    requested = []
    monkeypatch.setattr(
        transcriber,
        "download_audio",
        lambda podcast_id, episode_ref: requested.append((podcast_id, episode_ref))
        or _audio_asset(tmp_path),
    )
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode("gooaye", "EP672", model="small")

    assert requested == [("gooaye", "EP672")]
    assert asset.transcribed is True
    assert asset.segment_count == 2


def test_transcribe_episode_defaults_to_tiny_cpu_int8(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: _audio_asset(tmp_path))
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode("gooaye", "EP672")

    assert FakeWhisperModel.constructors == [
        {"model_name": "tiny", "device": "cpu", "compute_type": "int8"}
    ]
    assert asset.model == "tiny"
    assert asset.device == "cpu"
    assert asset.compute_type == "int8"
    assert asset.vad_filter is False


def test_transcribe_episode_passes_runtime_options_to_whisper(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: _audio_asset(tmp_path))
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode(
        "gooaye",
        "EP672",
        model="base",
        device="cuda",
        compute_type="float16",
        vad_filter=True,
    )

    assert FakeWhisperModel.constructors == [
        {"model_name": "base", "device": "cuda", "compute_type": "float16"}
    ]
    assert FakeWhisperModel.calls[-1]["vad_filter"] is True
    assert asset.device == "cuda"
    assert asset.compute_type == "float16"
    assert asset.vad_filter is True


def test_transcribe_episode_raises_when_audio_file_missing(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.errors import AudioFileMissingError

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(
        transcriber,
        "download_audio",
        lambda *_args: _audio_asset(tmp_path, exists=False),
    )

    with pytest.raises(AudioFileMissingError, match="audio.mp3"):
        transcriber.transcribe_episode("gooaye", "EP672")


def test_transcribe_episode_raises_dependency_error(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.errors import TranscriptionDependencyError

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: _audio_asset(tmp_path))

    def fail_import():
        raise TranscriptionDependencyError("faster-whisper 未安裝。")

    monkeypatch.setattr(transcriber, "_load_whisper_model_class", fail_import)

    with pytest.raises(TranscriptionDependencyError):
        transcriber.transcribe_episode("gooaye", "EP672")


def test_transcribe_episode_writes_txt_srt_and_json(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: _audio_asset(tmp_path))
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode("gooaye", "EP672", model="small")

    assert asset.text_path.read_text(encoding="utf-8") == "第一段\n第二段\n"
    assert "00:00:00,000 --> 00:00:01,250" in asset.srt_path.read_text(
        encoding="utf-8"
    )
    payload = json.loads(asset.json_path.read_text(encoding="utf-8"))
    assert payload["podcast_id"] == "gooaye"
    assert payload["episode_ref"] == "EP672"
    assert payload["model"] == "small"
    assert payload["language"] == "zh"
    assert payload["generated_at"].endswith("Z")
    assert payload["source_audio_path"] == str(asset.audio_path)
    assert payload["source_audio_size_bytes"] == 5
    assert payload["segment_count"] == 2
    assert payload["last_segment_end_seconds"] == 66.5
    assert payload["completed"] is True
    assert payload["segments"][1]["text"] == "第二段"


def test_transcribe_episode_reports_progress_callback(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: _audio_asset(tmp_path))
    _install_fake_faster_whisper(monkeypatch)
    progress = []

    transcriber.transcribe_episode(
        "gooaye",
        "EP672",
        model="tiny",
        progress_callback=lambda count, last_end: progress.append((count, last_end)),
    )

    assert progress[-1] == (2, 66.5)


def test_transcribe_episode_skips_when_all_outputs_exist(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    audio_asset = _audio_asset(tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", audio_asset.title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("existing", encoding="utf-8")
    paths.srt_path.write_text("existing", encoding="utf-8")
    paths.json_path.write_text(
        json.dumps(
            {
                "podcast_id": "gooaye",
                "episode_ref": "EP672",
                "title": audio_asset.title,
                "segment_count": 1,
                "segments": [{"id": 1, "start": 0.0, "end": 1.0, "text": "existing"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: audio_asset)

    def fail_load_model():
        raise AssertionError("model should not be loaded when transcript exists")

    monkeypatch.setattr(transcriber, "_load_whisper_model_class", fail_load_model)

    asset = transcriber.transcribe_episode("gooaye", "EP672", model="small", force=False)

    assert asset.segment_count == 1
    assert asset.already_exists is True
    assert asset.transcribed is False


def test_transcribe_episode_force_retranscribes_existing_outputs(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    audio_asset = _audio_asset(tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", audio_asset.title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("existing", encoding="utf-8")
    paths.srt_path.write_text("existing", encoding="utf-8")
    paths.json_path.write_text('{"segment_count": 7}', encoding="utf-8")
    stale_part = paths.json_path.with_name(f"{paths.json_path.name}.part")
    stale_part.write_text("stale", encoding="utf-8")
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: audio_asset)
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode("gooaye", "EP672", model="tiny", force=True)

    assert asset.transcribed is True
    assert asset.already_exists is False
    assert asset.segment_count == 2
    assert paths.text_path.read_text(encoding="utf-8") == "第一段\n第二段\n"
    assert not stale_part.exists()


def test_transcribe_episode_rejects_bad_existing_outputs_without_force(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.errors import TranscriptionFailedError
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    audio_asset = _audio_asset(tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", audio_asset.title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("existing", encoding="utf-8")
    paths.srt_path.write_text("existing", encoding="utf-8")
    paths.json_path.write_text(
        '{"podcast_id":"gooaye","episode_ref":"EP672","title":"EP672 | 🐣","segment_count":99,"segments":[]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: audio_asset)

    with pytest.raises(TranscriptionFailedError, match="--force"):
        transcriber.transcribe_episode("gooaye", "EP672", model="tiny", force=False)


def test_transcribe_episode_uses_audio_path_without_downloading(monkeypatch, tmp_path):
    import podcast_ingest_core.transcriber as transcriber

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    sample_audio_path = tmp_path / "sample.mp3"
    sample_audio_path.write_bytes(b"audio")

    def fail_download(*_args):
        raise AssertionError("audio_path smoke test should not download")

    monkeypatch.setattr(transcriber, "download_audio", fail_download)
    _install_fake_faster_whisper(monkeypatch)

    asset = transcriber.transcribe_episode(
        "gooaye", "smoke-test", audio_path=sample_audio_path
    )

    assert asset.episode_ref == "smoke-test"
    assert asset.title == "smoke-test"
    assert asset.audio_path == sample_audio_path
    assert asset.transcribed is True


def test_transcribe_episode_removes_part_files_and_preserves_no_half_outputs(
    monkeypatch, tmp_path
):
    import podcast_ingest_core.transcriber as transcriber
    from podcast_ingest_core.errors import TranscriptionFailedError
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_transcripts_dir(monkeypatch, tmp_path)
    audio_asset = _audio_asset(tmp_path)
    paths = transcript_asset_paths("gooaye", "EP672", audio_asset.title)
    monkeypatch.setattr(transcriber, "download_audio", lambda *_args: audio_asset)
    _install_fake_faster_whisper(monkeypatch)
    original_write_text = Path.write_text

    def fail_srt_write(self, *args, **kwargs):
        if self.suffix == ".srt" or self.name.endswith(".srt.part"):
            raise OSError("disk full")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_srt_write)

    with pytest.raises(TranscriptionFailedError):
        transcriber.transcribe_episode("gooaye", "EP672", model="tiny")

    assert not paths.text_path.exists()
    assert not paths.srt_path.exists()
    assert not paths.json_path.exists()
    assert not list(paths.text_path.parent.glob("*.part"))


def test_transcript_paths_remove_illegal_characters_and_emoji():
    from podcast_ingest_core.storage import transcript_asset_paths

    paths = transcript_asset_paths("gooaye", "EP672", ' bad <title> 🐣 : / \\ | ? * ok ')

    assert not any(character in paths.text_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.text_path.name
    assert paths.text_path.name == "EP672__bad_title_ok.txt"


def test_format_srt_timestamp():
    from podcast_ingest_core.transcriber import _format_srt_timestamp

    assert _format_srt_timestamp(0.0) == "00:00:00,000"
    assert _format_srt_timestamp(65.123) == "00:01:05,123"
    assert _format_srt_timestamp(3661.5) == "01:01:01,500"


def test_transcribe_cli_parses_podcast_episode_and_model(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import TranscriptAsset
    from scripts import transcribe_episode

    asset = TranscriptAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        audio_path=tmp_path / "audio.mp3",
        text_path=tmp_path / "out.txt",
        srt_path=tmp_path / "out.srt",
        json_path=tmp_path / "out.json",
        model="small",
        language="zh",
        segment_count=2,
        device="cuda",
        compute_type="float16",
        vad_filter=True,
        transcribed=True,
        already_exists=False,
    )
    captured = {}

    def fake_transcribe(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(transcribe_episode, "transcribe_episode", fake_transcribe)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "transcribe_episode.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--model",
            "small",
            "--device",
            "cuda",
            "--compute-type",
            "float16",
            "--vad-filter",
            "--force",
            "--audio-path",
            str(tmp_path / "sample.mp3"),
        ],
    )

    transcribe_episode.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["podcast_id"] == "gooaye"
    assert payload["model"] == "small"
    assert payload["device"] == "cuda"
    assert payload["compute_type"] == "float16"
    assert payload["vad_filter"] is True
    assert payload["segment_count"] == 2
    assert captured["args"] == ("gooaye", "EP672")
    progress_callback = captured["kwargs"].pop("progress_callback")
    assert callable(progress_callback)
    assert captured["kwargs"] == {
        "model": "small",
        "device": "cuda",
        "compute_type": "float16",
        "vad_filter": True,
        "force": True,
        "audio_path": tmp_path / "sample.mp3",
    }
