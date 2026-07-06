from __future__ import annotations

import json
import sys

import pytest


def test_load_llm_profile_from_yaml(tmp_path):
    from podcast_ingest_core.llm_profiles import load_llm_profile

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text(
        """
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
""".strip(),
        encoding="utf-8",
    )

    profile = load_llm_profile("gb10", config_path)

    assert profile.profile_id == "gb10"
    assert profile.provider == "openai-compatible"
    assert profile.model == "GB10"
    assert profile.base_url == "https://api.example.com/v1"
    assert profile.api_key_env == "API_KEY"


def test_default_gb10_llm_profile_config_loads():
    from podcast_ingest_core.llm_profiles import load_llm_profile

    profile = load_llm_profile("gb10")

    assert profile.provider == "openai-compatible"
    assert profile.model == "GB10"
    assert profile.base_url is None
    assert profile.api_key_env == "API_KEY"


def test_load_llm_profile_rejects_missing_file_or_profile(tmp_path):
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.llm_profiles import load_llm_profile

    with pytest.raises(LLMProviderConfigError, match="missing"):
        load_llm_profile("gb10", tmp_path / "missing.yaml")

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text("profiles: {}", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError, match="gb10"):
        load_llm_profile("gb10", config_path)


def test_load_llm_profile_rejects_malformed_yaml(tmp_path):
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.llm_profiles import load_llm_profile

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text("profiles: [", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError, match="invalid"):
        load_llm_profile("gb10", config_path)


@pytest.mark.parametrize("field_name", ["api_key", "token", "secret"])
def test_load_llm_profile_rejects_secret_like_fields(tmp_path, field_name):
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.llm_profiles import load_llm_profile

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text(
        f"""
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
    {field_name}: should-not-be-here
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(LLMProviderConfigError, match=field_name):
        load_llm_profile("gb10", config_path)


def test_smoke_cli_profile_values_can_be_overridden(monkeypatch, tmp_path, capsys):
    from scripts import run_research_llm_smoke

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text(
        """
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
""".strip(),
        encoding="utf-8",
    )
    captured = {}

    def fake_workflow(*args, **kwargs):
        from tests.test_research_llm_smoke import _workflow_result

        captured["kwargs"] = kwargs
        return _workflow_result(dry_run=True, confirm=False)

    monkeypatch.setattr(run_research_llm_smoke, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--llm-profile",
            "gb10",
            "--llm-profile-path",
            str(config_path),
            "--model",
            "override-model",
            "--base-url",
            "https://override.test/v1",
            "--api-key-env",
            "OVERRIDE_API_KEY",
        ],
    )

    run_research_llm_smoke.main()

    payload = json.loads(capsys.readouterr().out)
    assert captured["kwargs"]["semantic_model"] == "override-model"
    assert captured["kwargs"]["semantic_base_url"] == "https://override.test/v1"
    assert captured["kwargs"]["semantic_api_key_env"] == "OVERRIDE_API_KEY"
    assert captured["kwargs"]["synthesis_model"] == "override-model"
    assert captured["kwargs"]["synthesis_base_url"] == "https://override.test/v1"
    assert captured["kwargs"]["synthesis_api_key_env"] == "OVERRIDE_API_KEY"
    assert payload["provider_config"]["llm_profile"] == "gb10"
    assert payload["provider_config"]["model"] == "override-model"
    assert payload["provider_config"]["api_key_env"] == "OVERRIDE_API_KEY"
    assert "should-not-be-here" not in capsys.readouterr().out
