"""Bounded per-profile transcription policy; no model loading or media."""
import pytest

from corpus_ingest_core.config import load_podcast_profile


def profile(tmp_path, mapping="", language="en"):
    path = tmp_path / "profiles.yaml"
    path.write_text("podcasts:\n  demo:\n    display_name: Demo\n    source_type: x-video\n    language: " + language + "\n" + mapping, encoding="utf-8")
    return load_podcast_profile("demo", path)


def test_omission_retains_legacy_defaults(tmp_path):
    from corpus_ingest_core.preparation_transcription import resolve
    value = profile(tmp_path)
    assert value.preparation_transcription is None
    assert resolve(value).as_dict() == dict(model="tiny", device="cpu", compute_type="int8", vad_filter=True)


@pytest.mark.parametrize("model,device,precision", [("medium","cuda","float16"), ("small","cpu","float32"), ("turbo","cuda","int8"), ("base.en","cpu","int8")])
def test_explicit_settings_are_frozen_and_valid(tmp_path, model, device, precision):
    from corpus_ingest_core.preparation_transcription import resolve
    value = profile(tmp_path, f"    preparation_transcription:\n      model: {model}\n      device: {device}\n      compute_type: {precision}\n")
    assert resolve(value).as_dict() == dict(model=model, device=device, compute_type=precision, vad_filter=True)


@pytest.mark.parametrize("mapping,language", [
    ("null", "en"), ("{}", "en"), ("{model: medium}", "en"),
    ("{model: medium, device: cpu, compute_type: float16}", "en"),
    ("{model: medium, device: auto, compute_type: int8}", "en"),
    ("{model: ../model, device: cpu, compute_type: int8}", "en"),
    ("{model: medium, device: cpu, compute_type: int8, vad_filter: false}", "en"),
    ("{model: true, device: cpu, compute_type: int8}", "en"),
    ("{model: ' medium', device: cpu, compute_type: int8}", "en"),
    ("{model: tiny.en, device: cpu, compute_type: int8}", "zh"),
])
def test_invalid_explicit_mapping_never_silently_defaults(tmp_path, mapping, language):
    with pytest.raises(ValueError, match="invalid_transcription_settings"):
        profile(tmp_path, "    preparation_transcription: " + mapping + "\n", language)


@pytest.mark.parametrize("count,precisions,expected", [(1,{"float16"},True), (0,{"float16"},False), (1,{"int8"},False)])
def test_cuda_capability_observation_only(monkeypatch, count, precisions, expected):
    from types import SimpleNamespace
    from corpus_ingest_core import preparation_transcription as settings
    calls = []
    runtime = SimpleNamespace(get_cuda_device_count=lambda: count, get_supported_compute_types=lambda device: calls.append(device) or precisions)
    monkeypatch.setattr(settings.importlib, "import_module", lambda name: runtime if name == "ctranslate2" else pytest.fail("unexpected model import"))
    assert settings.runtime_available(settings.TranscriptionSettings("medium", "cuda", "float16")) is expected
    assert calls == ([] if not count else ["cuda"])


def test_cpu_preview_never_imports_runtime_and_cuda_import_failure_is_finite(monkeypatch):
    from corpus_ingest_core import preparation_transcription as settings
    def unavailable(name):
        raise ImportError("private backend details")
    monkeypatch.setattr(settings.importlib, "import_module", unavailable)
    assert settings.runtime_available(settings.TranscriptionSettings())
    assert not settings.runtime_available(settings.TranscriptionSettings("medium", "cuda", "float16"))
