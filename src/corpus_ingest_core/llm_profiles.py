from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import LLMProviderConfigError
from .models import LLMProfile

DEFAULT_LLM_PROFILES_CONFIG_PATH = Path("config/llm_profiles.yaml")
ALLOWED_PROFILE_FIELDS = {"provider", "model", "base_url", "api_key_env", "unavailable"}
SECRET_FIELD_TOKENS = ("api_key", "token", "secret")


def load_llm_profile(profile_id: str, path: str | Path = DEFAULT_LLM_PROFILES_CONFIG_PATH) -> LLMProfile:
    """Load an LLM provider profile without reading API key values."""

    normalized_profile_id = _required_text(profile_id, "profile_id")
    config_path = Path(path)
    if not config_path.exists():
        raise LLMProviderConfigError(f"LLM profile config missing: {config_path}")

    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise LLMProviderConfigError(f"LLM profile config invalid: {config_path}") from exc

    profiles = raw_config.get("profiles")
    if not isinstance(profiles, dict):
        raise LLMProviderConfigError("LLM profile config must contain a profiles mapping.")

    raw_profile = profiles.get(normalized_profile_id)
    if not isinstance(raw_profile, dict):
        raise LLMProviderConfigError(f"LLM profile not found: {normalized_profile_id}")

    _reject_secret_like_fields(raw_profile)
    unsupported_fields = sorted(set(raw_profile) - ALLOWED_PROFILE_FIELDS)
    if unsupported_fields:
        raise LLMProviderConfigError(f"LLM profile has unsupported fields: {', '.join(unsupported_fields)}")

    if _profile_is_unavailable(raw_profile):
        available = sorted(
            name
            for name, body in profiles.items()
            if isinstance(name, str)
            and name != normalized_profile_id
            and isinstance(body, dict)
            and not _profile_is_unavailable(body)
        )
        suffix = f" Available profiles: {', '.join(available)}." if available else ""
        raise LLMProviderConfigError(f"LLM profile unavailable: {normalized_profile_id}.{suffix}")

    provider = _required_text(raw_profile.get("provider"), "provider")
    if provider != "openai-compatible":
        raise LLMProviderConfigError(f"unsupported LLM provider in profile: {provider}")

    return LLMProfile(
        profile_id=normalized_profile_id,
        provider=provider,
        model=_required_text(raw_profile.get("model"), "model"),
        base_url=_optional_text(raw_profile.get("base_url"), "base_url"),
        api_key_env=_required_text(raw_profile.get("api_key_env"), "api_key_env"),
    )


def _profile_is_unavailable(profile: dict[str, Any]) -> bool:
    flag = profile.get("unavailable")
    if flag is None:
        return False
    if isinstance(flag, bool):
        return flag
    raise LLMProviderConfigError("LLM profile field must be boolean: unavailable")


def _reject_secret_like_fields(profile: dict[str, Any]) -> None:
    for field_name in profile:
        normalized = str(field_name).lower()
        if normalized == "api_key_env":
            continue
        if any(token in normalized for token in SECRET_FIELD_TOKENS):
            raise LLMProviderConfigError(f"LLM profile must not contain secret-like field: {field_name}")


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LLMProviderConfigError(f"LLM profile field required: {field_name}")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise LLMProviderConfigError(f"LLM profile field must be text: {field_name}")
    return value.strip()
