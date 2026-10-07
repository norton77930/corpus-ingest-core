"""050 offline recovery observations; no actual corpus operations."""
import importlib
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace
import pytest
from corpus_ingest_core import storage
from tests.test_study_guide_bundle import PODCAST,EPISODE,TITLE,_ready_episode,_generated_bundle
from tests.test_study_guide_lineage import snapshot,tripwire
TAGS=['public','lecture_part','lecture_old','derivation_part','derivation_old']
SUFFIXES=['','.part','.old','.wfderive.part','.wfderive.old']
NAMES={'00':'00_video_info.md','03':'03_full_summary.md','04':'04_learning_notes.md','05':'05_prompt_examples.md','06':'06_apply_to_my_workflow.md','07':'07_final_study_guide.md'}
RECEIPTS={'study_guide':'study_guide.lineage.json','workflow_derivation':'workflow_derivation.lineage.json'}
def core():return importlib.import_module('corpus_ingest_core.learning_bundle_recovery')
def query():return core().inspect_learning_bundle_recovery(PODCAST,EPISODE)
def bundle():return storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir
def location(i):return bundle().with_name(bundle().name+SUFFIXES[i])
def add_roles(dest,roles):
    dest.mkdir(parents=True,exist_ok=True)
    for role in roles:(dest/NAMES[role]).write_bytes(b'fixture\r\n')

def test_empty_observation_has_fixed_five_rows_and_no_side_effects(tmp_data_dirs):
    _ready_episode(tmp_data_dirs);before=snapshot(tmp_data_dirs);result=query()
    assert (result['status'],result['reason'],result['manual_review_required'])==('clear','no_recovery_entries',False)
    assert [r['location'] for r in result['locations']]==TAGS
    assert all(r['status']=='absent' and r['lecture_state']=='absent' and r['derivation_state']=='absent' for r in result['locations'])
    assert result['read_only'] is True and result['network_access'] is False
    assert result['scope']=='learning_bundle_recovery'
    assert result['warnings']==['diagnostic_scope_only','non_atomic_observation','publication_outcome_not_proven']
    assert set(result)=={'podcast_id','episode_ref','status','reason','manual_review_required','locations','scope','read_only','network_access','warnings'}
    assert before==snapshot(tmp_data_dirs)

@pytest.mark.parametrize('index',[1,2,3,4])
def test_each_fixed_recovery_directory_requires_manual_review(tmp_data_dirs,index):
    _ready_episode(tmp_data_dirs);add_roles(location(index),['00','03','04','07'])
    result=query()
    assert result['status']=='recovery_present' and result['reason']=='recovery_entries_present' and result['manual_review_required'] is True
    row=result['locations'][index]
    assert row['location']==TAGS[index] and row['status']=='observed' and row['lecture_state']=='complete'
    assert row['derivation_state']=='absent' and row['extra_files']==0
    assert row['roles']=={k:k in {'00','03','04','07'} for k in NAMES}
    assert str(tmp_data_dirs) not in json.dumps(result)

def test_all_recovery_locations_are_observed_without_ranking(tmp_data_dirs):
    _ready_episode(tmp_data_dirs)
    for i in range(5):add_roles(location(i),list(NAMES))
    result=query();assert result['status']=='recovery_present'
    assert all(r['lecture_state']=='complete' and r['derivation_state']=='complete' for r in result['locations'])
    assert not any(k in json.dumps(result) for k in ['winner','latest_candidate','delete_command'])

@pytest.mark.parametrize('role',['00','03','04','07','05','06'])
def test_partial_public_groups_are_manual_review(tmp_data_dirs,role):
    _ready_episode(tmp_data_dirs);add_roles(bundle(),[role])
    result=query()
    assert (result['status'],result['reason'],result['manual_review_required'])==('blocked','manual_review_required',True)

def test_legacy_complete_public_lecture_is_clear_but_not_proven_current(tmp_data_dirs):
    _ready_episode(tmp_data_dirs);add_roles(bundle(),['00','03','04','07']);(bundle()/'PRIVATE_EXTRA_NAME.bin').write_bytes(b'PRIVATE_BODY')
    result=query();row=result['locations'][0]
    assert result['status']=='clear' and row['extra_files']==1
    assert row['records']['study_guide']=={'status':'absent','output_status':'not_evaluated','changed_roles':[]}
    assert 'PRIVATE_' not in json.dumps(result)

@pytest.mark.parametrize('podcast,episode',[(None,EPISODE),(PODCAST,None),('',EPISODE),('bad/path',EPISODE),(PODCAST,'latest'),(PODCAST,'NEXT'),(PODCAST,' padded'),(PODCAST,'../file')])
def test_invalid_identity_precedes_profile(monkeypatch,podcast,episode):
    monkeypatch.setattr(core(),'load_podcast_profile',tripwire)
    with pytest.raises(ValueError,match='Invalid explicit episode identity'):
        core().inspect_learning_bundle_recovery(podcast,episode)

def test_missing_identity_and_finance_profile_are_closed(tmp_data_dirs):
    assert query()['reason']=='identity_unavailable' and query()['locations']==[]
    assert core().inspect_learning_bundle_recovery('gooaye','EP678')['reason']=='identity_unavailable'

@pytest.mark.parametrize('problem',['directory','file-leaf','reparse-leaf','reparse-child','reparse-parent','special-child'])
def test_unsafe_location_is_not_read_and_outranks_safe_recovery(tmp_data_dirs,monkeypatch,problem):
    _ready_episode(tmp_data_dirs);bad=location(1);safe=location(2);add_roles(safe,[])
    if problem=='file-leaf':bad.write_bytes(b'not directory')
    else:add_roles(bad,['03'])
    if problem=='directory':(bad/'nested').mkdir()
    real=Path.lstat
    if problem.startswith('reparse') or problem=='special-child':
        target=bad if problem=='reparse-leaf' else bad.parent if problem=='reparse-parent' else bad/NAMES['03']
        def lstat(path,*a,**k):
            info=real(path,*a,**k)
            if path==target:return SimpleNamespace(st_mode=stat.S_IFIFO if problem=='special-child' else info.st_mode,st_size=info.st_size,st_file_attributes=0 if problem=='special-child' else 0x400)
            return info
        monkeypatch.setattr(Path,'lstat',lstat)
    real_read=core().secure_read_bytes;reads=[]
    def read(root,path,**kwargs):
        reads.append(path);return real_read(root,path,**kwargs)
    monkeypatch.setattr(core(),'secure_read_bytes',read)
    result=query()
    assert result['status']=='blocked' and result['reason']=='unsafe_path'
    assert not any(p.parent==bad for p in reads)

@pytest.mark.parametrize('failure',['lstat','listing','cap'])
def test_unknown_location_is_not_absence(tmp_data_dirs,monkeypatch,failure):
    _ready_episode(tmp_data_dirs);dest=location(1);add_roles(dest,[])
    if failure=='lstat':
        real=Path.lstat
        def lstat(path,*a,**k):
            if path==dest:raise PermissionError('PRIVATE_EXCEPTION')
            return real(path,*a,**k)
        monkeypatch.setattr(Path,'lstat',lstat)
    elif failure=='listing':
        real=core().secure_directory_names
        monkeypatch.setattr(core(),'secure_directory_names',lambda root,path,**k:None if path==dest else real(root,path,**k))
    else:
        for i in range(257):(dest/f'extra{i}.bin').write_bytes(b'')
    result=query();row=result['locations'][1]
    assert result['status']=='blocked' and result['reason']=='inspection_unavailable'
    assert row['status']=='blocked' and row['roles']=={k:None for k in NAMES} and row['extra_files'] is None
    assert 'PRIVATE_' not in json.dumps(result)


def test_deep_malformed_identity_is_finite(tmp_data_dirs):
    _ready_episode(tmp_data_dirs)
    storage.transcript_asset_paths(PODCAST,EPISODE,TITLE).json_path.write_bytes(b'['*5000+b'0'+b']'*5000)
    assert query()['reason']=='identity_unavailable'


def test_source_summary_is_not_opened_or_compared(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);add_roles(bundle(),['00','03','04','07'])
    real=core().secure_read_bytes
    def read(root,path,**kwargs):
        assert root!=storage.SUMMARIES_DIR
        return real(root,path,**kwargs)
    monkeypatch.setattr(core(),'secure_read_bytes',read)
    storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE).unlink()
    assert query()['status']=='clear'


def receipt(dest, family, stem=None):
    codec=core().RECORD_CODECS[family]
    if family=='study_guide':
        value=codec.generation_record(PODCAST,EPISODE,stem or bundle().name,'PRIVATE_SOURCE',[])
    else:
        value=codec.generation_record(PODCAST,EPISODE,stem or bundle().name,'custom',dict.fromkeys(['03','04','07'],'PRIVATE_SOURCE'),[],[])
    value['output_sha256']={role:codec.bytes_digest((dest/NAMES[role[-2:]]).read_bytes()) for role in codec.OUTPUT_ROLES}
    (dest/codec.RECEIPT_FILENAME).write_bytes(codec.encode_record(value))
    return value

@pytest.mark.parametrize('family',list(RECEIPTS))
@pytest.mark.parametrize('index',range(5))
def test_receipts_use_original_stem_in_all_five_locations(tmp_data_dirs,family,index):
    _ready_episode(tmp_data_dirs);dest=location(index);add_roles(dest,list(NAMES));receipt(dest,family)
    before=snapshot(tmp_data_dirs);result=query()
    assert result['locations'][index]['records'][family]=={'status':'valid','output_status':'match','changed_roles':[]}
    assert result['status']==('clear' if index==0 else 'recovery_present')
    assert snapshot(tmp_data_dirs)==before

@pytest.mark.parametrize('family',list(RECEIPTS))
@pytest.mark.parametrize('problem',['mismatch','missing','unreadable','output-unavailable','invalid','unsupported','identity','stem','deep','duplicate','oversize'])
def test_receipt_failures_are_finite_and_require_review(tmp_data_dirs,monkeypatch,family,problem):
    _ready_episode(tmp_data_dirs);dest=bundle();add_roles(dest,list(NAMES));value=receipt(dest,family)
    codec=core().RECORD_CODECS[family];path=dest/codec.RECEIPT_FILENAME;role=codec.OUTPUT_ROLES[0];output=dest/NAMES[role[-2:]]
    status='valid';out='not_evaluated';changed=[]
    if problem=='mismatch':output.write_bytes(b'PRIVATE_MUTATED');out='mismatch';changed=[role]
    elif problem=='missing':output.unlink();out='missing'
    elif problem in ['unreadable','output-unavailable']:
        real=core().secure_read_bytes;target=path if problem=='unreadable' else output
        monkeypatch.setattr(core(),'secure_read_bytes',lambda root,p,**k:None if p==target else real(root,p,**k))
        if problem=='unreadable':status='record_unreadable'
        else:out='unavailable'
    elif problem=='unsupported':value['schema_version']=2;path.write_text(json.dumps(value));status='unsupported_schema'
    elif problem in ['identity','stem']:
        value['episode_ref']='other' if problem=='identity' else EPISODE
        if problem=='stem':value['identity_stem_sha256']=codec.bytes_digest((bundle().name+'.part').encode())
        path.write_bytes(codec.encode_record(value));status='identity_mismatch'
    else:
        status='record_unreadable' if problem=='oversize' else 'invalid_record'
        path.write_bytes(b'x'*(65536+1) if problem=='oversize' else b'['*5000+b'0'+b']'*5000 if problem=='deep' else b'{"x":1,"x":2}' if problem=='duplicate' else b'PRIVATE_INVALID')
    result=query();observed=result['locations'][0]['records'][family]
    assert observed=={'status':status,'output_status':out,'changed_roles':changed}
    assert result['manual_review_required'] is True
    assert 'PRIVATE_' not in json.dumps(result)

@pytest.mark.parametrize('family',list(RECEIPTS))
def test_receipt_and_output_caps_and_extra_privacy(tmp_data_dirs,monkeypatch,family):
    _ready_episode(tmp_data_dirs);dest=bundle();add_roles(dest,list(NAMES));receipt(dest,family)
    (dest/'PRIVATE_EXTRA.bin').write_bytes(b'PRIVATE_BODY');real=core().secure_read_bytes;reads=[]
    def read(root,path,**kw):
        assert path.name!='PRIVATE_EXTRA.bin'
        reads.append((path.name,kw['max_bytes']));return real(root,path,**kw)
    monkeypatch.setattr(core(),'secure_read_bytes',read)
    result=query();codec=core().RECORD_CODECS[family]
    assert (codec.RECEIPT_FILENAME,65536) in reads
    assert all((NAMES[r[-2:]],64*1024*1024) in reads for r in codec.OUTPUT_ROLES)
    assert result['locations'][0]['extra_files']==1
    assert 'PRIVATE_' not in json.dumps(result)


def test_query_has_no_write_network_generation_or_cache_calls(tmp_data_dirs,monkeypatch):
    import socket
    from corpus_ingest_core import study_guide_bundle,workflow_derivation,cache,local_env,llm_provider
    _ready_episode(tmp_data_dirs);add_roles(bundle(),list(NAMES));receipt(bundle(),'study_guide');receipt(bundle(),'workflow_derivation')
    for name in ['write_bytes','write_text','mkdir','rename','replace','unlink','rmdir']:
        monkeypatch.setattr(Path,name,tripwire)
    monkeypatch.setattr(socket,'create_connection',tripwire)
    monkeypatch.setattr(socket.socket,'connect',tripwire)
    monkeypatch.setattr(local_env,'load_local_env',tripwire)
    for module in [study_guide_bundle,workflow_derivation,cache,llm_provider]:
        for name in ['run_study_guide_bundle','run_workflow_derivation','rebuild_cache','initialize_cache','create_provider','write_part_staged_report_pair']:
            if hasattr(module,name):monkeypatch.setattr(module,name,tripwire)
    assert query()['status']=='clear'


@pytest.mark.parametrize('family',list(RECEIPTS))
def test_legacy_absence_and_invalid_receipt_never_open_output_bodies(tmp_data_dirs,monkeypatch,family):
    _ready_episode(tmp_data_dirs);dest=bundle();add_roles(dest,list(NAMES));real=core().secure_read_bytes
    def read(root,path,**kwargs):
        assert path.name not in NAMES.values()
        return real(root,path,**kwargs)
    monkeypatch.setattr(core(),'secure_read_bytes',read)
    assert query()['status']=='clear'
    (dest/RECEIPTS[family]).write_bytes(b'PRIVATE_INVALID')
    assert query()['locations'][0]['records'][family]['status']=='invalid_record'

@pytest.mark.parametrize('family',list(RECEIPTS))
def test_reduced_output_cap_is_unavailable_not_match(tmp_data_dirs,monkeypatch,family):
    _ready_episode(tmp_data_dirs);dest=bundle();add_roles(dest,list(NAMES));receipt(dest,family)
    monkeypatch.setattr(core(),'MAX_OUTPUT_BYTES',1)
    result=query()
    assert result['locations'][0]['records'][family]=={'status':'valid','output_status':'unavailable','changed_roles':[]}
    assert result['manual_review_required'] is True

@pytest.mark.parametrize('family',list(RECEIPTS))
def test_all_changed_output_roles_are_ordered(tmp_data_dirs,family):
    _ready_episode(tmp_data_dirs);dest=bundle();add_roles(dest,list(NAMES));receipt(dest,family);codec=core().RECORD_CODECS[family]
    for role in codec.OUTPUT_ROLES:(dest/NAMES[role[-2:]]).write_bytes(b'changed')
    assert query()['locations'][0]['records'][family]['changed_roles']==list(codec.OUTPUT_ROLES)


def test_unknown_location_outranks_safe_recovery(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);add_roles(location(1),[]);add_roles(location(2),[]);real=core().secure_directory_names
    monkeypatch.setattr(core(),'secure_directory_names',lambda root,path,**k:None if path==location(1) else real(root,path,**k))
    result=query()
    assert result['status']=='blocked' and result['reason']=='inspection_unavailable'
    assert result['locations'][2]['status']=='observed'


def test_receipt_anomaly_is_reported_with_safe_recovery_presence(tmp_data_dirs):
    _ready_episode(tmp_data_dirs);add_roles(location(1),list(NAMES));(location(1)/RECEIPTS['study_guide']).write_bytes(b'invalid')
    result=query()
    assert result['status']=='recovery_present' and result['manual_review_required']
    assert result['locations'][1]['records']['study_guide']['status']=='invalid_record'


def test_single_wrong_title_filename_cannot_establish_identity(tmp_data_dirs):
    _ready_episode(tmp_data_dirs)
    expected=storage.transcript_asset_paths(PODCAST,EPISODE,TITLE).json_path
    expected.rename(expected.with_name(EPISODE+'__wrong-title.json'))
    result=query()
    assert result['status']=='blocked' and result['reason']=='identity_unavailable' and result['locations']==[]


def test_reparse_ancestor_above_missing_managed_root_is_unsafe(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);ancestor=tmp_data_dirs/'unsafe-parent';ancestor.mkdir()
    monkeypatch.setattr(storage,'STUDY_GUIDES_DIR',ancestor/'missing-guides');real=Path.lstat
    def lstat(path,*args,**kwargs):
        info=real(path,*args,**kwargs)
        if path==ancestor:return SimpleNamespace(st_mode=info.st_mode,st_size=info.st_size,st_file_attributes=0x400)
        return info
    monkeypatch.setattr(Path,'lstat',lstat)
    result=query()
    assert result['status']=='blocked' and result['reason']=='unsafe_path'
    assert all(row['status']=='blocked' for row in result['locations'])


@pytest.mark.parametrize('payload',['scalar\n','- malformed-profile-root\n'])
def test_malformed_profile_registry_is_finite(tmp_data_dirs,monkeypatch,payload):
    from corpus_ingest_core import config
    _ready_episode(tmp_data_dirs);path=tmp_data_dirs/'bad-profile.yaml';path.write_text(payload)
    monkeypatch.setattr(core(),'load_podcast_profile',lambda podcast:config.load_podcast_profile(podcast,path))
    assert query()['status']=='blocked' and query()['reason']=='identity_unavailable' and query()['locations']==[]
