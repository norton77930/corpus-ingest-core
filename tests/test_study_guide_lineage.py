"""049 fixture-only lecture provenance contracts."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import pytest
from corpus_ingest_core import storage, study_guide_bundle as core
from corpus_ingest_core.errors import StudyGuideBundleError, StudyGuideBundleStateError
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_study_guide_bundle import PODCAST,EPISODE,TITLE,_ready_episode,_generated_bundle,_valid_payload,_FakeProvider
RECEIPT='study_guide.lineage.json'
NAMES={'output_03':'03_full_summary.md','output_04':'04_learning_notes.md','output_07':'07_final_study_guide.md'}
def codec():return importlib.import_module('corpus_ingest_core.study_guide_lineage')
def record():
    return {'schema_version':1,'recipe_version':1,'family':'study_guide','podcast_id':PODCAST,'episode_ref':EPISODE,
            'identity_stem_sha256':'a'*64,'input_sha256':{'semantic_summary':'b'*64},'request_sha256':'c'*64,
            'output_sha256':{r:'d'*64 for r in NAMES}}
def paths():return storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE)
def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
def tripwire(*a,**k):raise AssertionError('forbidden side effect')
def generate(monkeypatch):
    captured=[]
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:_FakeProvider(_valid_payload(),captured))
    return core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK),captured

def test_codec_roundtrip_deterministic():
    c=codec();r=record();wire=c.encode_record(r)
    assert c.decode_record(wire)==r
    assert c.encode_record(dict(reversed(list(r.items()))))==wire
    assert c.bytes_digest(b'abc')==hashlib.sha256(b'abc').hexdigest()
@pytest.mark.parametrize('field,value',[('schema_version',True),('schema_version',2),('recipe_version',False),('recipe_version',0),('family','other'),('podcast_id','../bad'),('episode_ref','latest'),('episode_ref','/bad'),('request_sha256','A'*64),('input_sha256',{}),('output_sha256',{}),('identity_stem_sha256',[])])
def test_codec_rejects_invalid_field(field,value):
    r=record();r[field]=value
    with pytest.raises(codec().RecordError):codec().decode_record(json.dumps(r).encode())
@pytest.mark.parametrize('wire',[b'{}',b'null',b'[]',b'{',b'\xff',b'{"schema_version":1,"schema_version":1}',b' '*65537,json.dumps(dict(record(),extra='unknown')).encode()],ids=['empty','null','list','broken','utf8','duplicate','oversize','extra'])
def test_codec_rejects_invalid_wire(wire):
    with pytest.raises(codec().RecordError):codec().decode_record(wire)

@pytest.mark.parametrize('branch',['generate','reuse','cover-only','force'])
def test_preview_metadata_separate_zero_write(tmp_data_dirs,monkeypatch,branch):
    if branch=='generate':_ready_episode(tmp_data_dirs)
    else:_generated_bundle(tmp_data_dirs,monkeypatch)
    if branch=='cover-only':paths().cover_path.unlink()
    monkeypatch.setattr(core,'create_provider',tripwire)
    before=snapshot(tmp_data_dirs)
    result=core.run_study_guide_bundle(PODCAST,EPISODE,force=branch=='force')
    assert result.metadata_writes==([str(paths().bundle_dir/RECEIPT)] if branch in {'generate','force'} else [])
    assert all(not p.endswith(RECEIPT) for p in result.planned_writes)
    assert set(core.describe_study_guide_plan(result))=={'requires_llm','report_writes'}
    assert snapshot(tmp_data_dirs)==before

def test_generation_records_consumed_source_request_and_staged_bytes(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs)
    source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
    consumed=source.read_bytes();result,captured=generate(monkeypatch)
    r=codec().decode_record((paths().bundle_dir/RECEIPT).read_bytes())
    assert r['input_sha256']=={'semantic_summary':codec().bytes_digest(consumed)}
    assert r['request_sha256']==codec().canonical_digest(captured[0])
    assert r['identity_stem_sha256']==codec().bytes_digest(paths().bundle_dir.name.encode())
    assert r['output_sha256']=={role:codec().bytes_digest((paths().bundle_dir/name).read_bytes()) for role,name in NAMES.items()}
    assert result.metadata_writes==[str(paths().bundle_dir/RECEIPT)]
    assert set(r)==set(record())

@pytest.mark.parametrize('wire',[b'not owned',b'{}',b' '*65537,json.dumps(dict(record(),schema_version=2)).encode(),json.dumps(dict(record(),podcast_id='other')).encode()],ids=['foreign','invalid','oversize','schema','identity'])
@pytest.mark.parametrize('confirm',[False,True])
def test_reserved_collision_blocks_before_provider_even_force(tmp_data_dirs,monkeypatch,wire,confirm):
    _ready_episode(tmp_data_dirs);dest=paths().bundle_dir;dest.mkdir(parents=True);(dest/RECEIPT).write_bytes(wire)
    monkeypatch.setattr(core,'create_provider',tripwire);before=snapshot(tmp_data_dirs)
    with pytest.raises(StudyGuideBundleError):core.run_study_guide_bundle(PODCAST,EPISODE,confirm=confirm,force=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert snapshot(tmp_data_dirs)==before

@pytest.mark.parametrize('branch',['reuse','cover-only'])
@pytest.mark.parametrize('tracked',[False,True])
def test_no_generation_never_backfills_or_changes_receipt(tmp_data_dirs,monkeypatch,branch,tracked):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    if tracked:(dest/RECEIPT).write_bytes(b'unrecognized but preserved')
    else:(dest/RECEIPT).unlink(missing_ok=True)
    (dest/'extra.bin').write_bytes(b'\x00\xff\n')
    (dest/'workflow_derivation.lineage.json').write_bytes(b'derivation metadata')
    if branch=='cover-only':paths().cover_path.unlink()
    before={p.name:p.read_bytes() for p in dest.iterdir() if p.name!='00_video_info.md'}
    monkeypatch.setattr(core,'create_provider',tripwire)
    result=core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True)
    assert result.metadata_writes==[]
    assert {p.name:p.read_bytes() for p in dest.iterdir() if p.name!='00_video_info.md'}==before

def test_force_replaces_only_owned_receipt_and_preserves_extras(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    r=codec().decode_record((dest/RECEIPT).read_bytes());r['recipe_version']=2;(dest/RECEIPT).write_bytes(codec().encode_record(r))
    (dest/'extra.bin').write_bytes(b'\xff\r\n');before=(dest/'extra.bin').read_bytes()
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:_FakeProvider(_valid_payload(),[]))
    core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,force=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert codec().decode_record((dest/RECEIPT).read_bytes())['recipe_version']==1
    assert (dest/'extra.bin').read_bytes()==before


def inspect():return core.inspect_study_guide_lineage(PODCAST,EPISODE)
@pytest.mark.parametrize('state',['not_generated','untracked','current','stale','blocked'])
def test_public_state_matrix_is_read_only(tmp_data_dirs,monkeypatch,state):
    _ready_episode(tmp_data_dirs)
    if state!='not_generated':
        generate(monkeypatch)
        if state=='untracked':(paths().bundle_dir/RECEIPT).unlink()
        elif state=='stale':paths().notes_path.write_bytes(b'changed')
        elif state=='blocked':paths().notes_path.unlink()
    before=snapshot(tmp_data_dirs)
    monkeypatch.setattr(core,'create_provider',tripwire);monkeypatch.setattr(core,'_atomic_write_bundle',tripwire);monkeypatch.setattr(core,'_write_run_report',tripwire)
    result=inspect()
    assert result['status']==state
    assert set(result)=={'podcast_id','episode_ref','status','reason','changed_roles','scope','read_only','network_access','warnings'}
    assert result['scope']=='study_guide_inputs_outputs' and result['read_only'] is True and result['network_access'] is False
    assert result['warnings']==['study_guide_scope_only','non_atomic_observation']
    assert str(tmp_data_dirs) not in json.dumps(result)
    assert before==snapshot(tmp_data_dirs)

@pytest.mark.parametrize('defect,reason',[
    ('json','invalid_record'),('duplicate','invalid_record'),('schema','unsupported_schema'),('identity','identity_mismatch'),('stem','identity_mismatch'),('oversize','record_unreadable'),('receipt-read','record_unreadable'),
    ('source-missing','inputs_unavailable'),('source-utf8','inputs_unavailable'),('source-cap','inputs_unavailable'),('source-finance','inputs_unavailable'),('source-read','inputs_unavailable'),('output-cap','outputs_unavailable'),('output-read','outputs_unavailable')])
def test_unverifiable_states_are_blocked(tmp_data_dirs,monkeypatch,defect,reason):
    _ready_episode(tmp_data_dirs);generate(monkeypatch);dest=paths().bundle_dir;receipt=dest/RECEIPT
    r=codec().decode_record(receipt.read_bytes());source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
    if defect=='json':receipt.write_bytes(b'{')
    elif defect=='duplicate':receipt.write_bytes(b'{"schema_version":1,"schema_version":1}')
    elif defect=='schema':r['schema_version']=2
    elif defect=='identity':r['episode_ref']='different'
    elif defect=='stem':r['identity_stem_sha256']='f'*64
    elif defect=='oversize':receipt.write_bytes(b' '*65537)
    elif defect=='source-missing':source.unlink()
    elif defect=='source-utf8':source.write_bytes(b'\xff')
    elif defect=='source-cap':monkeypatch.setattr(core,'_MAX_SOURCE_BYTES',1)
    elif defect=='source-finance':
        from tests.test_study_guide_bundle import FINANCE_SUMMARY
        source.write_text(FINANCE_SUMMARY,encoding='utf-8')
    elif defect=='output-cap':monkeypatch.setattr(codec(),'MAX_OUTPUT_BYTES',1)
    if defect in {'schema','identity','stem'}:receipt.write_bytes(json.dumps(r).encode())
    if defect.endswith('-read'):
        real=core.secure_read_bytes;target=receipt if defect=='receipt-read' else source if defect=='source-read' else paths().notes_path
        monkeypatch.setattr(core,'secure_read_bytes',lambda root,path,**k:None if path==target else real(root,path,**k))
    result=inspect();assert (result['status'],result['reason'],result['changed_roles'])==('blocked',reason,[])

@pytest.mark.parametrize('suffix',['.part','.old','.wfderive.part','.wfderive.old'])
def test_recovery_precedes_missing_outputs(tmp_data_dirs,suffix):
    _ready_episode(tmp_data_dirs);dest=paths().bundle_dir;dest.parent.mkdir(parents=True)
    dest.with_name(dest.name+suffix).write_bytes(b'recovery')
    assert inspect()['reason']=='recovery_required'

@pytest.mark.parametrize('unsafe',['directory','reparse','parent','bundle'])
def test_unsafe_entries_refused_before_recovery(tmp_data_dirs,monkeypatch,unsafe):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    dest.with_name(dest.name+'.part').mkdir()
    if unsafe=='directory':(dest/'extra').mkdir()
    else:
        import stat
        from types import SimpleNamespace
        real=core._lstat;target=paths().notes_path if unsafe=='reparse' else dest.parent if unsafe=='parent' else dest
        def lstat(path):
            info=real(path)
            if path==target:return SimpleNamespace(st_mode=info.st_mode,st_size=info.st_size,st_file_attributes=0x400)
            return info
        monkeypatch.setattr(core,'_lstat',lstat)
    assert inspect()['reason']=='unsafe_path'

@pytest.mark.parametrize('podcast,episode',[(None,EPISODE),(PODCAST,None),('bad/path',EPISODE),(PODCAST,' latest'),(PODCAST,'NEXT'),(PODCAST,'../file')])
def test_invalid_identity_precedes_profile_access(monkeypatch,podcast,episode):
    monkeypatch.setattr(core,'load_podcast_profile',tripwire)
    with pytest.raises(ValueError,match='Invalid explicit episode identity'):
        core.inspect_study_guide_lineage(podcast,episode)

@pytest.mark.parametrize('error',[KeyError('private'),OSError('private'),ValueError('private')])
def test_unavailable_profile_is_closed_blocker(monkeypatch,error):
    def fail(*a):raise error
    monkeypatch.setattr(core,'load_podcast_profile',fail)
    assert inspect()['reason']=='identity_unavailable'

def test_missing_identity_and_wrong_profile_are_blocked(tmp_data_dirs):
    assert inspect()['reason']=='identity_unavailable'
    assert core.inspect_study_guide_lineage('gooaye','EP678')['reason']=='identity_unavailable'

@pytest.mark.parametrize('role',['semantic_summary','recipe','request','output_03','output_04','output_07'])
def test_changed_roles_have_fixed_order(tmp_data_dirs,monkeypatch,role):
    _ready_episode(tmp_data_dirs);generate(monkeypatch);dest=paths().bundle_dir
    if role=='semantic_summary':
        source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE);source.write_bytes(source.read_bytes()+b'\nchanged chunk appendix')
    elif role=='recipe':monkeypatch.setattr(codec(),'RECIPE_VERSION',2)
    elif role=='request':
        real=core._build_messages
        monkeypatch.setattr(core,'_build_messages',lambda text:[*real(text),{'role':'user','content':'new instruction'}])
    else:(dest/NAMES[role]).write_bytes(b'different output')
    result=inspect();assert result['status']=='stale' and result['changed_roles']==[role]

def test_provider_time_summary_mutation_uses_actual_consumption(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE);before=source.read_bytes()
    class Mutating(_FakeProvider):
        def complete(self,messages):
            source.write_bytes(before+b'\nchanged during provider')
            return super().complete(messages)
    captured=[];monkeypatch.setattr(core,'create_provider',lambda *a,**k:Mutating(_valid_payload(),captured))
    core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    r=codec().decode_record((paths().bundle_dir/RECEIPT).read_bytes())
    assert r['input_sha256']['semantic_summary']==codec().bytes_digest(before)
    assert inspect()['changed_roles']==['semantic_summary']

def test_cover_only_does_not_bless_changed_summary(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
    source.write_bytes(source.read_bytes()+b'\nchanged');paths().cover_path.unlink()
    assert inspect()['status']=='stale'
    before=(paths().bundle_dir/RECEIPT).read_bytes();monkeypatch.setattr(core,'create_provider',tripwire)
    core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True)
    assert (paths().bundle_dir/RECEIPT).read_bytes()==before and inspect()['status']=='stale'

def test_cover_and_derivation_files_do_not_change_scope(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);paths().cover_path.unlink()
    for name in ('05_prompt_examples.md','06_apply_to_my_workflow.md','workflow_derivation.lineage.json'):(paths().bundle_dir/name).write_bytes(b'other stage')
    assert inspect()['status']=='current'

@pytest.mark.parametrize('phase',['receipt-write','output-read','stage-rename','backup-rename'])
def test_publication_faults_preserve_old_bundle(tmp_data_dirs,monkeypatch,phase):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    (dest/'extra.bin').write_bytes(b'preserve');before={p.name:p.read_bytes() for p in dest.iterdir()}
    read=Path.read_bytes;write=Path.write_bytes;rename=Path.rename
    def read_bytes(path):
        if phase=='output-read' and path.parent.name.endswith('.part') and path.name=='03_full_summary.md':raise OSError('injected')
        return read(path)
    def write_bytes(path,data):
        if phase=='receipt-write' and path.parent.name.endswith('.part') and path.name==RECEIPT:raise OSError('injected')
        return write(path,data)
    def rename_path(path,target):
        if (phase=='stage-rename' and path.name.endswith('.part')) or (phase=='backup-rename' and path==dest):raise OSError('injected')
        return rename(path,target)
    monkeypatch.setattr(Path,'read_bytes',read_bytes);monkeypatch.setattr(Path,'write_bytes',write_bytes);monkeypatch.setattr(Path,'rename',rename_path)
    secure=core.secure_read_bytes
    monkeypatch.setattr(core,'secure_read_bytes',lambda root,path,**k:None if phase=='output-read' and path.parent.name.endswith('.part') and path.name=='03_full_summary.md' else secure(root,path,**k))
    with pytest.raises(StudyGuideBundleStateError) as exc:core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,force=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert exc.value.reason_code=='publish_failed'
    assert {p.name:p.read_bytes() for p in dest.iterdir()}==before


def test_orphan_receipt_and_untracked_precedence(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    for name in NAMES.values():(dest/name).unlink()
    assert inspect()['reason']=='incomplete_lecture'
    (dest/RECEIPT).unlink();assert inspect()['status']=='not_generated'
    for name in NAMES.values():(dest/name).write_bytes(b'legacy')
    source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE);source.unlink()
    assert inspect()['status']=='untracked'


def test_all_change_roles_are_ordered(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);dest=paths().bundle_dir
    source=storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE)
    source.write_bytes(b'new source content\n'+source.read_bytes())
    monkeypatch.setattr(codec(),'RECIPE_VERSION',2)
    for name in NAMES.values():(dest/name).write_bytes(b'changed')
    assert inspect()['changed_roles']==['semantic_summary','recipe','request','output_03','output_04','output_07']


def test_collision_introduced_during_provider_is_refused_before_staging(tmp_data_dirs,monkeypatch):
    _ready_episode(tmp_data_dirs);dest=paths().bundle_dir;dest.mkdir(parents=True)
    (dest/'extra.bin').write_bytes(b'keep')
    class Colliding(_FakeProvider):
        def complete(self,messages):
            (dest/RECEIPT).write_bytes(b'unknown new file')
            return super().complete(messages)
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:Colliding(_valid_payload(),[]))
    with pytest.raises(StudyGuideBundleError):core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert (dest/RECEIPT).read_bytes()==b'unknown new file' and (dest/'extra.bin').read_bytes()==b'keep'
    assert not any((dest/name).exists() for name in NAMES.values())
    assert not dest.with_name(dest.name+'.part').exists()


def test_tool25_preserves_lecture_receipt(tmp_data_dirs,monkeypatch):
    from corpus_ingest_core import workflow_derivation
    from tests.test_workflow_derivation import _context,_valid_payload as derivation_payload,_FakeProvider as DerivationProvider
    _generated_bundle(tmp_data_dirs,monkeypatch);receipt=paths().bundle_dir/RECEIPT;before=receipt.read_bytes()
    monkeypatch.setattr(workflow_derivation,'DEFAULT_CONTEXT_PATH',_context(tmp_data_dirs,['Claude Code','Codex']))
    monkeypatch.setattr(workflow_derivation,'create_provider',lambda *a,**k:DerivationProvider(derivation_payload(),[]))
    workflow_derivation.run_workflow_derivation(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert receipt.read_bytes()==before and inspect()['status']=='current'


def test_current_title_does_not_fall_back_to_old_bundle(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch);transcript=storage.transcript_asset_paths(PODCAST,EPISODE,TITLE).json_path
    identity=json.loads(transcript.read_bytes());identity['title']='Revised Talk';transcript.write_text(json.dumps(identity),encoding='utf-8')
    assert inspect()['status']=='not_generated'


def test_summary_missing_required_prompt_section_is_blocked(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch)
    storage.semantic_summary_asset_path(PODCAST,EPISODE,TITLE).write_bytes(b'missing required section')
    result=inspect()
    assert (result['status'],result['reason'],result['changed_roles'])==('blocked','inputs_unavailable',[])


def test_deeply_nested_canonical_identity_is_blocked(tmp_data_dirs,monkeypatch):
    _generated_bundle(tmp_data_dirs,monkeypatch)
    identity=storage.transcript_asset_paths(PODCAST,EPISODE,TITLE).json_path
    identity.write_bytes(b'['*5000+b'0'+b']'*5000)
    result=inspect()
    assert (result['status'],result['reason'],result['changed_roles'])==('blocked','identity_unavailable',[])


@pytest.mark.parametrize('existing',[False,True])
def test_staged_output_cap_refuses_before_publication(tmp_data_dirs,monkeypatch,existing):
    _ready_episode(tmp_data_dirs)
    if existing:generate(monkeypatch)
    dest=paths().bundle_dir
    before={p.name:p.read_bytes() for p in dest.iterdir()} if existing else {}
    monkeypatch.setattr(codec(),'MAX_OUTPUT_BYTES',1)
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:_FakeProvider(_valid_payload(),[]))
    with pytest.raises(StudyGuideBundleStateError) as exc:
        core.run_study_guide_bundle(PODCAST,EPISODE,confirm=True,force=existing,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert exc.value.reason_code=='publish_failed'
    assert ({p.name:p.read_bytes() for p in dest.iterdir()} if dest.exists() else {})==before
    assert not dest.with_name(dest.name+'.part').exists() and not dest.with_name(dest.name+'.old').exists()
