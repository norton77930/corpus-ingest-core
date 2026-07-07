"""LLM api_cost_ack guard consistency contracts (Batch 2, B2-T4; audit F-03).

Invariants protected:
- Every wrapper that can reach a confirmed LLM call (CLI / MCP / workflow)
  requires the exact acknowledgement text before provider construction.
- The acknowledgement text has a single source of truth (defined in
  ``llm_provider.SEMANTIC_API_COST_ACK``, re-exported as
  ``semantic_summarizer.SEMANTIC_API_COST_ACK``); wrappers must reuse that
  constant instead of pasting their own copy.
- F-03 resolved (Batch 3A): the exact ack is also enforced at the core LLM
  execution boundary — ``semantic_summarize_episode`` validates it at entry,
  and ``llm_provider.create_provider`` refuses to construct any provider
  without it. Wrappers stay as the first line of defense, but are no longer
  the only one.
- Dry-run remains a wrapper concern: the semantic core deliberately has no
  ``confirm`` parameter. If a future change alters these signatures, these
  tests must fail so the change is reviewed.
- Dry-run / rejected paths never expose API key values.
"""

from __future__ import annotations

import inspect
import json
import sys

import pytest


def test_semantic_core_signature_requires_ack_no_confirm_f03_resolved():
    from podcast_ingest_core.semantic_summarizer import semantic_summarize_episode

    parameters = inspect.signature(semantic_summarize_episode).parameters
    # Audit F-03 resolved in Batch 3A: the core function now enforces the
    # exact-ack gate itself (keyword-only ``api_cost_ack``). ``confirm`` stays
    # out on purpose — dry-run planning remains a wrapper responsibility.
    # Changing this signature is a public-API and safety-boundary change that
    # needs explicit approval.
    assert "api_cost_ack" in parameters
    assert parameters["api_cost_ack"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "confirm" not in parameters


@pytest.mark.parametrize("bad_ack", ["", "wrong ack text"])
def test_create_provider_requires_exact_ack_before_provider_construction(
    monkeypatch, bad_ack
):
    from podcast_ingest_core import llm_provider
    from podcast_ingest_core.errors import LLMProviderConfigError

    monkeypatch.setattr(
        llm_provider,
        "OpenAICompatibleProvider",
        lambda **kwargs: pytest.fail(
            "provider must not be constructed without the exact api_cost_ack"
        ),
    )

    with pytest.raises(LLMProviderConfigError, match="api_cost_ack"):
        llm_provider.create_provider("openai-compatible", api_cost_ack=bad_ack)


def test_create_provider_with_exact_ack_constructs_provider(monkeypatch):
    from podcast_ingest_core import llm_provider

    sentinel = object()
    monkeypatch.setattr(
        llm_provider, "OpenAICompatibleProvider", lambda **kwargs: sentinel
    )

    provider = llm_provider.create_provider(
        "openai-compatible",
        api_cost_ack=llm_provider.SEMANTIC_API_COST_ACK,
    )

    assert provider is sentinel


@pytest.mark.parametrize("bad_ack_kwargs", [{}, {"api_cost_ack": "wrong ack text"}])
def test_semantic_core_rejects_wrong_ack_before_any_work(
    monkeypatch, bad_ack_kwargs
):
    from podcast_ingest_core import semantic_summarizer
    from podcast_ingest_core.errors import LLMProviderConfigError

    # The entry-level guard must fire before profile loading, transcript
    # access, or provider construction — no fixtures are needed because none
    # of those collaborators may run.
    monkeypatch.setattr(
        semantic_summarizer,
        "load_podcast_profile",
        lambda *args, **kwargs: pytest.fail(
            "profile must not load without the exact api_cost_ack"
        ),
    )
    monkeypatch.setattr(
        semantic_summarizer,
        "_build_provider",
        lambda **kwargs: pytest.fail(
            "provider must not be built without the exact api_cost_ack"
        ),
    )

    with pytest.raises(LLMProviderConfigError, match="api_cost_ack"):
        semantic_summarizer.semantic_summarize_episode(
            "gooaye", "EP672", **bad_ack_kwargs
        )


def test_synthesis_core_signature_keeps_ack_guard():
    from podcast_ingest_core.stock_lens_synthesis import (
        generate_stock_lens_synthesis_report,
    )

    parameters = inspect.signature(generate_stock_lens_synthesis_report).parameters
    assert "api_cost_ack" in parameters
    assert "confirm" in parameters


def test_ack_constant_has_single_source_of_truth():
    from podcast_ingest_core import (
        llm_provider,
        mcp_server,
        research_workflow,
        semantic_summarizer,
        stock_lens_synthesis,
    )
    from scripts import (
        run_research_llm_smoke,
        run_semantic_summary_smoke,
        summarize_episode,
    )

    canonical = semantic_summarizer.SEMANTIC_API_COST_ACK
    assert llm_provider.SEMANTIC_API_COST_ACK is canonical
    assert mcp_server.SEMANTIC_API_COST_ACK is canonical
    assert research_workflow.SEMANTIC_API_COST_ACK is canonical
    assert stock_lens_synthesis.SEMANTIC_API_COST_ACK is canonical
    assert run_research_llm_smoke.SEMANTIC_API_COST_ACK is canonical
    assert run_semantic_summary_smoke.SEMANTIC_API_COST_ACK is canonical
    assert summarize_episode.SEMANTIC_API_COST_ACK is canonical


@pytest.mark.parametrize("bad_ack_argv", [[], ["--api-cost-ack", "wrong ack text"]])
def test_summarize_cli_semantic_requires_exact_ack_before_core(
    monkeypatch, capsys, bad_ack_argv
):
    from scripts import summarize_episode as cli

    monkeypatch.setenv("API_KEY", "fake-key-value")
    monkeypatch.setattr(
        cli,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail(
            "semantic core must not run without the exact api_cost_ack"
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_episode.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--mode",
            "semantic",
            "--no-env-file",
            *bad_ack_argv,
        ],
    )

    with pytest.raises(SystemExit) as excinfo:
        cli.main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "api_cost_ack" in captured.err
    combined_output = captured.out + captured.err
    assert "fake-key-value" not in combined_output


def test_mcp_semantic_dry_run_reports_env_name_only_never_value(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import TranscriptValidationResult

    monkeypatch.setenv("FAKE_LLM_KEY", "fake-key-value")
    monkeypatch.setattr(
        mcp_server.validator,
        "validate_transcript",
        lambda *args, **kwargs: TranscriptValidationResult(
            podcast_id="gooaye",
            episode_ref="EP672",
            valid=True,
            status="valid",
            segment_count=2,
            last_segment_end_seconds=120.0,
            transcript_text_length=500,
            problems=[],
            warnings=[],
            paths={"json": "data/transcripts/gooaye/EP672__title.json"},
        ),
    )

    response = mcp_server.semantic_summarize_episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
        api_key_env="FAKE_LLM_KEY",
    )

    assert response["dry_run"] is True
    assert response["inputs"]["api_key_env"] == "FAKE_LLM_KEY"
    assert response["inputs"]["api_key_env_configured"] is True
    serialized = json.dumps(response, ensure_ascii=False, default=str)
    assert "fake-key-value" not in serialized
