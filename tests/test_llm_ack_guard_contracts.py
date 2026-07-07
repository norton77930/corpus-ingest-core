"""LLM api_cost_ack guard consistency contracts (Batch 2, B2-T4; audit F-03).

Invariants protected:
- Every wrapper that can reach a confirmed LLM call (CLI / MCP / workflow)
  requires the exact acknowledgement text before provider construction.
- The acknowledgement text has a single source of truth
  (``semantic_summarizer.SEMANTIC_API_COST_ACK``); wrappers must reuse that
  constant instead of pasting their own copy.
- Dry-run / rejected paths never expose API key values.

Characterized known gap (do NOT "fix" silently):
- ``semantic_summarize_episode`` core itself has no ``confirm``/``api_cost_ack``
  parameter; the guard lives only in the CLI/MCP/workflow wrappers. This is
  audit finding F-03 and stays a Batch 3 design decision (e.g. moving the ack
  check into ``llm_provider.create_provider``). If a future change adds or
  removes these parameters, this test must fail so the change is reviewed.
"""

from __future__ import annotations

import inspect
import json
import sys

import pytest


def test_semantic_core_signature_has_no_ack_guard_known_gap_f03():
    from podcast_ingest_core.semantic_summarizer import semantic_summarize_episode

    parameters = inspect.signature(semantic_summarize_episode).parameters
    # Known architectural gap (audit F-03): the core function relies on its
    # wrappers for the confirm + exact-ack gate. Changing this signature is a
    # public-API and safety-boundary change that needs explicit approval.
    assert "api_cost_ack" not in parameters
    assert "confirm" not in parameters


def test_synthesis_core_signature_keeps_ack_guard():
    from podcast_ingest_core.stock_lens_synthesis import (
        generate_stock_lens_synthesis_report,
    )

    parameters = inspect.signature(generate_stock_lens_synthesis_report).parameters
    assert "api_cost_ack" in parameters
    assert "confirm" in parameters


def test_ack_constant_has_single_source_of_truth():
    from podcast_ingest_core import (
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
