from __future__ import annotations

import asyncio
from dataclasses import asdict
import importlib
import inspect
import json

import pytest

from tests.test_learning_workflow_next_step import (
    PODCAST, EPISODE, lecture, derivation, install_previews, query_module,
)


def tool_module():
    from corpus_ingest_core import mcp_server  # Load tools through the ordered facade.
    return importlib.import_module("corpus_ingest_core.mcp_tools_learning_workflow")


@pytest.mark.parametrize("first,second,status", [
    (lecture(), None, "action_available"),
    (lecture("cover"), None, "action_available"),
    (lecture("reuse"), derivation(), "action_available"),
    (lecture("reuse"), derivation("reuse"), "complete"),
    (ValueError("PRIVATE"), None, "blocked"),
])
def test_real_core_projection_through_mcp(monkeypatch, first, second, status):
    tool = tool_module()
    q, calls = install_previews(monkeypatch, first, second)
    result = tool.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert result["ok"] is True and result["data"]["status"] == status
    assert "dry_run" not in result
    assert result["data"]["read_only"] is True
    assert "PRIVATE" not in json.dumps(result)


def test_tool_delegates_once_with_only_exact_identity(monkeypatch):
    tool = tool_module()
    q = query_module()
    observed = []
    result = q._decision(PODCAST, EPISODE, lecture_mode="blocked", blocked_stage="lecture", reason="unsafe_path")
    def fake(*args, **kwargs):
        observed.append((args, kwargs))
        return result
    monkeypatch.setattr(q, "suggest_learning_workflow_next_step", fake)
    response = tool.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert observed == [((PODCAST, EPISODE), {})]
    assert response == {"ok": True, "data": asdict(result)}


@pytest.mark.parametrize("kind,public_type", [
    ("value", "ValueError"), ("query", "LearningWorkflowQueryError"), ("other", "InternalError"),
])
def test_error_mapping_is_fixed(monkeypatch, kind, public_type):
    tool = tool_module()
    q = query_module()
    def fail(*args, **kwargs):
        raise {"value": ValueError, "query": q.LearningWorkflowQueryError, "other": RuntimeError}[kind]("PRIVATE_TEXT")
    monkeypatch.setattr(q, "suggest_learning_workflow_next_step", fail)
    response = tool.suggest_learning_workflow_next_step(PODCAST, EPISODE)
    assert response == {"ok": False, "error_type": public_type, "message":
                        q.INVALID_IDENTITY_MESSAGE if kind == "value" else q.QUERY_ERROR_MESSAGE}


def test_registry_appends_read_query_and_schema_has_no_execution_options():
    from corpus_ingest_core import mcp_server
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert len(tools) == 35
    assert [tool.name for tool in tools[24:27]] == [
        "derive_workflow_bundle", "generate_study_guide_bundle", "suggest_learning_workflow_next_step",
    ]
    schema = tools[26].inputSchema
    assert list(schema["properties"]) == ["podcast_id", "episode_ref"]
    assert set(schema["required"]) == {"podcast_id", "episode_ref"}
    signature = inspect.signature(mcp_server.suggest_learning_workflow_next_step)
    assert list(signature.parameters) == ["podcast_id", "episode_ref"]
    assert all(p.default is inspect.Parameter.empty for p in signature.parameters.values())
