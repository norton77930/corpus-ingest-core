"""Provider factory boundary guards (Batch 3B, B3B-T2).

Invariants protected:
- ``llm_provider.create_provider`` is the ONLY sanctioned construction site for
  an LLM provider, because it enforces the exact ``api_cost_ack`` gate
  (``require_exact_api_cost_ack``) before the provider is built. Application
  code must go through the factory; constructing ``OpenAICompatibleProvider``
  directly bypasses that gate.
- No ``src/`` core module and no ``scripts/`` entry point constructs
  ``OpenAICompatibleProvider(...)`` directly. Only ``llm_provider.py`` (the
  factory's own module) may. Unit tests may still construct the provider class
  directly to exercise it in isolation, so ``tests/`` is intentionally not
  scanned.
- ``create_provider`` keeps ``api_cost_ack`` as a keyword-only parameter that
  fails closed (empty default), so a caller can never accidentally skip the
  gate by passing arguments positionally.

Runtime refusal behaviour (missing / wrong ack raises before construction) is
covered by ``tests/test_llm_ack_guard_contracts.py``; this module locks the
static call-site boundary and the factory signature so a future ``src/`` change
cannot silently reintroduce a direct-construction bypass.

No download / transcription / LLM call / market API access happens here: the
tests only read source files and introspect a signature.
"""

from __future__ import annotations

import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PROVIDER_CONSTRUCTOR = "OpenAICompatibleProvider("
# Only the factory's own module may construct the provider directly.
FACTORY_MODULE = "llm_provider.py"


def _app_python_files():
    """Application code that must reach the provider through the factory.

    ``src/podcast_ingest_core/*.py`` core modules plus ``scripts/*.py`` entry
    points (both are flat directories). ``tests/`` is excluded on purpose:
    unit tests legitimately construct the provider class directly to exercise
    it in isolation.
    """

    core_dir = ROOT / "src" / "podcast_ingest_core"
    scripts_dir = ROOT / "scripts"
    return sorted(core_dir.glob("*.py")) + sorted(scripts_dir.glob("*.py"))


def test_provider_constructed_only_in_factory_module():
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
    from podcast_ingest_core.llm_provider import create_provider

    parameters = inspect.signature(create_provider).parameters
    # The exact-ack gate depends on api_cost_ack staying keyword-only and
    # failing closed (empty default). Relaxing this signature is a safety-
    # boundary change that must be reviewed, so pin it here.
    assert "api_cost_ack" in parameters
    assert parameters["api_cost_ack"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["api_cost_ack"].default == ""
