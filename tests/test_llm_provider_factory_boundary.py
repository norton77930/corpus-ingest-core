"""Provider factory boundary guards (Batch 3B static + Batch 3C runtime).

Invariants protected:
- ``llm_provider.create_provider`` is the ONLY sanctioned construction site for
  an LLM provider, because it enforces the exact ``api_cost_ack`` gate
  (``require_exact_api_cost_ack``) before the provider is built. Application
  code must go through the factory; constructing ``OpenAICompatibleProvider``
  directly bypasses that gate.
- No ``src/`` core module and no ``scripts/`` entry point constructs
  ``OpenAICompatibleProvider(...)`` directly. Only ``llm_provider.py`` (the
  factory's own module) may. Tests exercise construction via ``create_provider``
  (or by asserting that bare construction is refused).
- ``create_provider`` keeps ``api_cost_ack`` as a keyword-only parameter that
  fails closed (empty default), so a caller can never accidentally skip the
  gate by passing arguments positionally.
- Batch 3C: ``OpenAICompatibleProvider(...)`` refuses direct construction at
  runtime unless the private factory token is supplied by ``create_provider``.
  A wrong or missing token raises ``LLMProviderConfigError`` before env/model
  resolution, so the constructor cannot be used as an ack bypass.

Runtime refusal behaviour for missing / wrong **ack** (before construction)
is covered by ``tests/test_llm_ack_guard_contracts.py``; this module locks the
static call-site boundary, the factory signature, and the constructor token
gate so a future change cannot silently reintroduce a direct-construction
bypass.

No download / transcription / LLM call / market API access happens here
beyond optional env setup for successful factory construction paths.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

PROVIDER_CONSTRUCTOR = "OpenAICompatibleProvider("
# Only the factory's own module may construct the provider directly.
FACTORY_MODULE = "llm_provider.py"


def _app_python_files():
    """Application code that must reach the provider through the factory.

    ``src/corpus_ingest_core/*.py`` core modules plus ``scripts/*.py`` entry
    points (both are flat directories). ``tests/`` is excluded: tests assert the
    runtime ban or go through ``create_provider``.
    """

    core_dir = ROOT / "src" / "corpus_ingest_core"
    scripts_dir = ROOT / "scripts"
    return sorted(core_dir.glob("*.py")) + sorted(scripts_dir.glob("*.py"))


def test_provider_constructed_only_in_factory_module():
    completion_core = (
        ROOT / "src" / "corpus_ingest_core" / "corpus_episode_completion_workflow_runner.py"
    )
    assert completion_core in _app_python_files()

    offenders = sorted(
        path.relative_to(ROOT).as_posix()
        for path in _app_python_files()
        if PROVIDER_CONSTRUCTOR in path.read_text(encoding="utf-8")
        and path.name != FACTORY_MODULE
    )
    assert not offenders, (
        "OpenAICompatibleProvider(...) constructed outside the factory module; "
        "application code must call llm_provider.create_provider so the exact "
        f"api_cost_ack gate is enforced (see ADR-0005): {offenders}"
    )


def test_create_provider_keeps_keyword_only_api_cost_ack():
    from corpus_ingest_core.llm_provider import create_provider

    parameters = inspect.signature(create_provider).parameters
    # The exact-ack gate depends on api_cost_ack staying keyword-only and
    # failing closed (empty default). Relaxing this signature is a safety-
    # boundary change that must be reviewed, so pin it here.
    assert "api_cost_ack" in parameters
    assert parameters["api_cost_ack"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["api_cost_ack"].default == ""


def test_direct_openai_compatible_provider_construction_is_rejected(monkeypatch):
    """Batch 3C: bare constructor must not bypass create_provider + api_cost_ack."""
    from corpus_ingest_core.errors import LLMProviderConfigError
    from corpus_ingest_core.llm_provider import OpenAICompatibleProvider

    # Env would be sufficient for a successful build if the token gate were
    # missing — prove the refusal is about construction path, not config.
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    with pytest.raises(LLMProviderConfigError, match="create_provider"):
        OpenAICompatibleProvider(model="test-model")


def test_direct_construction_rejects_forged_factory_token(monkeypatch):
    from corpus_ingest_core.errors import LLMProviderConfigError
    from corpus_ingest_core.llm_provider import OpenAICompatibleProvider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    with pytest.raises(LLMProviderConfigError, match="create_provider"):
        OpenAICompatibleProvider(model="test-model", _factory_token=object())


def test_create_provider_with_exact_ack_still_builds_provider(monkeypatch):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    provider = create_provider(
        "openai-compatible",
        model="test-model",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.model == "test-model"
    assert provider.provider_name == "openai-compatible"
