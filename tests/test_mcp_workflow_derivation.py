"""Spec 043: `derive_workflow_bundle` as append-only Tool 25.

The tool wraps Spec 042 Core, which calls an LLM. That makes its envelope
different from Tools 23 and 24 in two ways worth stating up front: preview here
constructs no provider, so it declares ``network_read=false`` where those two
declare ``true``; and the exact ``api_cost_ack`` gate lives in Core, so these
tests assert the tool forwards it rather than checking it a second time.

Fixtures come from ``tests.test_workflow_derivation`` so the preconditions a
derivation actually needs -- a learning-notes profile, a complete lecture, a
workflow-context file -- stay defined in one place.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from podcast_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_workflow_derivation import (
    EPISODE,
    PODCAST,
    _context,
    _FakeProvider,
    _ready_lecture,
    _tree,
    _valid_payload,
)


def _default_context(monkeypatch, tmp_data_dirs: Path) -> None:
    """Point Core's default context at the fixture, since MCP takes no override."""
    from podcast_ingest_core import workflow_derivation

    monkeypatch.setattr(
        workflow_derivation,
        "DEFAULT_CONTEXT_PATH",
        _context(tmp_data_dirs, ["Claude Code", "Codex"]),
    )


def _refuse_provider(monkeypatch) -> None:
    """Patch the name Core actually calls.

    ``workflow_derivation`` value-binds ``create_provider`` at import
    (workflow_derivation.py:21), so patching ``llm_provider.create_provider``
    leaves the bound reference untouched and the tripwire never fires.
    """

    def refuse(*_args, **_kwargs):
        raise AssertionError("no provider may be constructed on this path")

    monkeypatch.setattr(
        "podcast_ingest_core.workflow_derivation.create_provider", refuse
    )


def test_preview_is_zero_write_and_declares_zero_network(monkeypatch, tmp_data_dirs):
    from podcast_ingest_core import mcp_server

    _ready_lecture(tmp_data_dirs)
    _default_context(monkeypatch, tmp_data_dirs)
    _refuse_provider(monkeypatch)
    before = _tree(tmp_data_dirs)

    result = mcp_server.derive_workflow_bundle(PODCAST, EPISODE)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["run_mode"] == "preview"
    assert result["network_read"] is False
    assert result["not_investment_advice"] is True
    assert result["writes"], "preview must still name what it would write"
    assert any(
        "operator_workflow" in read for read in result["reads"]
    ), "preview must name the operator policy file the agent cannot choose"
    assert _tree(tmp_data_dirs) == before


def test_preview_needs_no_api_cost_ack(monkeypatch, tmp_data_dirs):
    from podcast_ingest_core import mcp_server

    _ready_lecture(tmp_data_dirs)
    _default_context(monkeypatch, tmp_data_dirs)
    _refuse_provider(monkeypatch)

    result = mcp_server.derive_workflow_bundle(PODCAST, EPISODE, api_cost_ack="")

    assert result["ok"] is True


def test_confirm_without_the_exact_ack_fails_before_any_provider(
    monkeypatch, tmp_data_dirs
):
    from podcast_ingest_core import mcp_server

    _ready_lecture(tmp_data_dirs)
    _default_context(monkeypatch, tmp_data_dirs)
    _refuse_provider(monkeypatch)
    before = _tree(tmp_data_dirs)

    result = mcp_server.derive_workflow_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack="close-enough"
    )

    assert result["ok"] is False
    assert "error_type" in result and "message" in result
    assert _tree(tmp_data_dirs) == before


def test_confirm_writes_the_pair_and_returns_metadata_only(monkeypatch, tmp_data_dirs):
    from podcast_ingest_core import mcp_server

    _ready_lecture(tmp_data_dirs)
    _default_context(monkeypatch, tmp_data_dirs)
    payload = _valid_payload()
    monkeypatch.setattr(
        "podcast_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(payload, []),
    )

    result = mcp_server.derive_workflow_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result["ok"] is True
    data = result["data"]
    assert data["prompt_examples_path"] and data["apply_path"]
    blob = repr(result)
    for body in payload.values():
        assert body not in blob, "the response must not carry derived body text"


def test_tool_takes_no_provider_endpoint_credential_or_context_path():
    from podcast_ingest_core import mcp_server

    parameters = inspect.signature(mcp_server.derive_workflow_bundle).parameters
    assert list(parameters) == [
        "podcast_id",
        "episode_ref",
        "confirm",
        "force",
        "api_cost_ack",
    ]


@pytest.mark.parametrize(
    "forbidden",
    [
        "provider",
        "model",
        "base_url",
        "api_key_env",
        "reasoning_effort",
        "read_timeout_seconds",
        "workflow_context",
    ],
)
def test_core_parameter_stays_off_the_mcp_surface(forbidden):
    from podcast_ingest_core import mcp_server, workflow_derivation

    assert forbidden in inspect.signature(
        workflow_derivation.run_workflow_derivation
    ).parameters, "guarding a Core parameter that no longer exists"
    assert (
        forbidden
        not in inspect.signature(mcp_server.derive_workflow_bundle).parameters
    )


def test_live_registry_appends_workflow_derivation_as_tool_25():
    import asyncio

    from podcast_ingest_core import mcp_server

    names = [tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())]
    assert len(names) == 25
    assert names[-1] == "derive_workflow_bundle"
    assert names[-2] == "ingest_youtube_video"
    assert names[-3] == "ingest_x_video"
