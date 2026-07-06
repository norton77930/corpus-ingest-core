from __future__ import annotations

import os

import pytest


def test_load_local_env_loads_simple_values(monkeypatch, tmp_path):
    from podcast_ingest_core.local_env import load_local_env

    env_path = tmp_path / ".env"
    env_path.write_text(
        "API_KEY=secret-value\nMODEL=GB10\nBASE_URL=https://api.example.com/v1\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)

    result = load_local_env(env_path)

    assert result.loaded is True
    assert result.path == env_path
    assert result.loaded_env_var_names == ["API_KEY", "MODEL", "BASE_URL"]
    assert os.environ["API_KEY"] == "secret-value"
    assert os.environ["MODEL"] == "GB10"
    assert os.environ["BASE_URL"] == "https://api.example.com/v1"


def test_load_local_env_supports_comments_quotes_and_export(monkeypatch, tmp_path):
    from podcast_ingest_core.local_env import load_local_env

    env_path = tmp_path / ".env"
    env_path.write_text(
        """
# local LLM config
export API_KEY='secret-value'
MODEL="GB10"

BASE_URL=https://api.example.com/v1
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)

    result = load_local_env(env_path)

    assert result.loaded is True
    assert result.loaded_env_var_names == ["API_KEY", "MODEL", "BASE_URL"]
    assert os.environ["API_KEY"] == "secret-value"
    assert os.environ["MODEL"] == "GB10"


def test_load_local_env_missing_file_is_not_failure(tmp_path):
    from podcast_ingest_core.local_env import load_local_env

    result = load_local_env(tmp_path / ".env")

    assert result.loaded is False
    assert result.loaded_env_var_names == []


def test_load_local_env_does_not_overwrite_existing_env(monkeypatch, tmp_path):
    from podcast_ingest_core.local_env import load_local_env

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=file-secret\nMODEL=GB10\n", encoding="utf-8")
    monkeypatch.setenv("API_KEY", "session-secret")
    monkeypatch.delenv("MODEL", raising=False)

    result = load_local_env(env_path)

    assert os.environ["API_KEY"] == "session-secret"
    assert os.environ["MODEL"] == "GB10"
    assert result.loaded_env_var_names == ["MODEL"]
    assert result.skipped_env_var_names == ["API_KEY"]


def test_load_local_env_rejects_malformed_line_without_secret_value(tmp_path):
    from podcast_ingest_core.errors import LLMProviderConfigError
    from podcast_ingest_core.local_env import load_local_env

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nnot a valid line\n", encoding="utf-8")

    with pytest.raises(LLMProviderConfigError) as exc_info:
        load_local_env(env_path)

    message = str(exc_info.value)
    assert "line 2" in message
    assert "secret-value" not in message


def test_local_env_result_metadata_does_not_include_secret_values(monkeypatch, tmp_path):
    from podcast_ingest_core.local_env import load_local_env, local_env_metadata

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=GB10\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)

    metadata = local_env_metadata(load_local_env(env_path))

    assert metadata == {
        "env_file_loaded": True,
        "env_file_path": str(env_path),
        "loaded_env_var_names": ["API_KEY", "MODEL"],
        "skipped_env_var_names": [],
    }
    assert "secret-value" not in str(metadata)
