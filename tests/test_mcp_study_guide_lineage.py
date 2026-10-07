import importlib
import inspect
import json
import pytest
from corpus_ingest_core import study_guide_bundle as core,mcp_server
from tests.test_study_guide_lineage import PODCAST,EPISODE,_ready_episode,generate,snapshot,tripwire

def wrapper():return importlib.import_module('corpus_ingest_core.mcp_tools_study_guide_lineage').inspect_study_guide_lineage

def test_query_has_two_required_parameters():
    params=inspect.signature(wrapper()).parameters
    assert list(params)==['podcast_id','episode_ref'] and all(p.default is inspect.Parameter.empty for p in params.values())

def test_query_calls_core_once_and_has_safe_payload(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);generate(monkeypatch);real=core.inspect_study_guide_lineage;calls=[]
    def query(*a):calls.append(a);return real(*a)
    monkeypatch.setattr(core,'inspect_study_guide_lineage',query);monkeypatch.setattr(core,'create_provider',tripwire)
    before=snapshot(tmp_data_dirs);result=wrapper()(PODCAST,EPISODE)
    assert result['ok'] is True and result['data']['status']=='current' and calls==[(PODCAST,EPISODE)]
    assert str(tmp_data_dirs) not in json.dumps(result) and before==snapshot(tmp_data_dirs)

@pytest.mark.parametrize('error',[ValueError('PRIVATE_SENTINEL'),RuntimeError('PRIVATE_SENTINEL'),core.StudyGuideBundleError('PRIVATE_SENTINEL')])
def test_errors_are_fixed(monkeypatch,error):
    def fail(*a):raise error
    monkeypatch.setattr(core,'inspect_study_guide_lineage',fail)
    result=wrapper()(PODCAST,EPISODE)
    assert result=={'ok':False,'error_type':'ValueError' if isinstance(error,ValueError) else 'InternalError','message':core.LINEAGE_INVALID_IDENTITY_MESSAGE if isinstance(error,ValueError) else core.LINEAGE_QUERY_ERROR_MESSAGE}
    assert 'PRIVATE_SENTINEL' not in json.dumps(result)

@pytest.mark.parametrize('episode',['latest','NEXT','../bad',' padded'])
def test_bad_identity_does_not_load_profile(monkeypatch,episode):
    monkeypatch.setattr(core,'load_podcast_profile',tripwire)
    result=wrapper()(PODCAST,episode)
    assert result=={'ok':False,'error_type':'ValueError','message':core.LINEAGE_INVALID_IDENTITY_MESSAGE}

@pytest.mark.parametrize('branch',['generate','reuse','cover-only'])
def test_real_tool26_preview_discloses_metadata(tmp_data_dirs,monkeypatch,branch):
    from tests.test_study_guide_lineage import paths,RECEIPT
    _ready_episode(tmp_data_dirs)
    if branch!='generate':generate(monkeypatch)
    if branch=='cover-only':paths().cover_path.unlink()
    monkeypatch.setattr(core,'create_provider',tripwire)
    result=mcp_server.generate_study_guide_bundle(PODCAST,EPISODE)
    assert result['metadata_writes']==([str(paths().bundle_dir/RECEIPT)] if branch=='generate' else [])
