"""Pure bounded source-preparation policy and lazy runtime observation."""
from __future__ import annotations

from dataclasses import dataclass
import importlib

MODELS = frozenset({"tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large-v3", "turbo"})
PRECISIONS = {"cpu": frozenset({"int8", "float32"}), "cuda": frozenset({"int8", "float16", "float32"})}


class InvalidTranscriptionSettings(ValueError):
    def __init__(self):
        super().__init__("invalid_transcription_settings")


@dataclass(frozen=True)
class TranscriptionSettings:
    model: str = "tiny"
    device: str = "cpu"
    compute_type: str = "int8"

    def as_dict(self) -> dict:
        return dict(model=self.model, device=self.device, compute_type=self.compute_type, vad_filter=True)


def parse(value, *, language: str | None = None, recorded: bool = False) -> TranscriptionSettings:
    keys = {"model", "device", "compute_type"} | ({"vad_filter"} if recorded else set())
    if not isinstance(value, dict) or set(value) != keys:
        raise InvalidTranscriptionSettings()
    if any(type(value[k]) is not str for k in ("model", "device", "compute_type")):
        raise InvalidTranscriptionSettings()
    if value["model"] not in MODELS or value["device"] not in PRECISIONS or value["compute_type"] not in PRECISIONS[value["device"]]:
        raise InvalidTranscriptionSettings()
    if (language is not None and value["model"].endswith(".en") and language != "en") or (recorded and value["vad_filter"] is not True):
        raise InvalidTranscriptionSettings()
    return TranscriptionSettings(**{k: value[k] for k in ("model", "device", "compute_type")})


def resolve(profile) -> TranscriptionSettings:
    return profile.preparation_transcription or TranscriptionSettings()


def actual(payload) -> dict | None:
    """Only complete recorded evidence; never fill gaps from current policy."""
    try:
        return parse({k: payload[k] for k in ("model", "device", "compute_type", "vad_filter")}, recorded=True).as_dict()
    except (KeyError, TypeError, InvalidTranscriptionSettings):
        return None


def runtime_available(settings: TranscriptionSettings) -> bool:
    """Observe CUDA capability only; no model loading/cache probing/download."""
    if settings.device == "cpu":
        return True
    try:
        runtime = importlib.import_module("ctranslate2")
        return runtime.get_cuda_device_count() > 0 and settings.compute_type in runtime.get_supported_compute_types("cuda")
    except Exception:
        return False
