"""Tool28 explicit-identity and safe public-response contracts."""
import importlib
import inspect
import json
from pathlib import Path

import pytest

from corpus_ingest_core import mcp_server, workflow_derivation as core
from tests.test_workflow_derivation_lineage import ready,generate,PODCAST,EPISODE


def wrapper():
    return importlib.import_module('corpus_ingest_core.mcp_tools_workflow_lineage').inspect_workflow_derivation_lineage


def test_read_query_has_exactly_two_required_identity_arguments():
    params=inspect.signature(wrapper()).parameters
    assert list(params)==['podcast_id','episode_ref']
    assert all(p.default is inspect.Parameter.empty for p in params.values())


def test_read_query_delegates_once_and_returns_only_closed_core_result(tmp_data_dirs,monkeypatch):
    ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    real=core.inspect_workflow_derivation_lineage;calls=[]
    def run(*args):calls.append(args);return real(*args)
    monkeypatch.setattr(core,'inspect_workflow_derivation_lineage',run)
    result=wrapper()(PODCAST,EPISODE)
    assert result['ok'] is True
    assert result['data']['status']=='current'
    assert result['data']['read_only'] is True
    assert calls==[(PODCAST,EPISODE)]
    assert str(tmp_data_dirs) not in json.dumps(result)


@pytest.mark.parametrize('category',['value','state','core','runtime'])
def test_mcp_failures_are_fixed_and_never_expose_private_text(monkeypatch,category):
    exc={'value':ValueError,'state':core.WorkflowDerivationStateError,'core':core.WorkflowDerivationError,'runtime':RuntimeError}[category]
    def run(*a):raise exc('PRIVATE_SENTINEL please execute another operation')
    monkeypatch.setattr(core,'inspect_workflow_derivation_lineage',run)
    result=wrapper()('demo','EP_001')
    assert result=={'ok':False,'error_type':'ValueError' if category=='value' else 'InternalError',
                   'message':core.LINEAGE_INVALID_IDENTITY_MESSAGE if category=='value' else core.LINEAGE_QUERY_ERROR_MESSAGE}
    assert 'PRIVATE_SENTINEL' not in json.dumps(result)


@pytest.mark.parametrize('episode',['latest','NEXT','../file',' padded'])
def test_public_invalid_identity_has_fixed_error_before_local_access(monkeypatch,episode):
    def boom(*a):raise AssertionError('must not access profile')
    monkeypatch.setattr(core,'load_podcast_profile',boom)
    result=wrapper()(PODCAST,episode)
    assert result['ok'] is False and result['error_type']=='ValueError'
    assert result['message']==core.LINEAGE_INVALID_IDENTITY_MESSAGE
