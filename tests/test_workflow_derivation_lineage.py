"""048 offline provenance codec, generation and read-observation contracts."""
import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from corpus_ingest_core import storage, workflow_derivation as core
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_workflow_derivation import PODCAST, EPISODE, TITLE, _ready_lecture, _context, _valid_payload, _FakeProvider

RECEIPT = 'workflow_derivation.lineage.json'


def codec():
    return importlib.import_module('corpus_ingest_core.workflow_derivation_lineage')


def record():
    return {'schema_version':1, 'recipe_version':1, 'family':'workflow_derivation',
            'podcast_id':PODCAST, 'episode_ref':EPISODE, 'identity_stem_sha256':'a'*64,
            'context_origin':'default',
            'input_sha256':{r:'b'*64 for r in ('lecture_03','lecture_04','lecture_07','effective_context')},
            'request_sha256':'c'*64, 'output_sha256':{'output_05':'d'*64,'output_06':'e'*64}}


def test_strict_receipt_round_trip_is_deterministic_and_bounded():
    c=codec(); payload=record()
    wire=c.encode_record(payload)
    assert c.decode_record(wire)==payload
    assert c.encode_record(dict(reversed(list(payload.items()))))==wire
    assert len(wire)<=65536
    assert c.bytes_digest(b'abc')==hashlib.sha256(b'abc').hexdigest()
    assert c.canonical_digest(['Codex','Codex'])!=c.canonical_digest(['Codex'])
    assert c.canonical_digest(['A','B'])!=c.canonical_digest(['B','A'])


@pytest.mark.parametrize('field,value',[
    ('schema_version',True),('schema_version',2),('recipe_version',True),('recipe_version',0),
    ('family','other'),('podcast_id',[]),('podcast_id','../bad'),('episode_ref','latest'),
    ('context_origin','unknown'),('identity_stem_sha256','A'*64),('request_sha256','x'),
    ('input_sha256',{'lecture_03':'b'*64}),('output_sha256',{'output_05':'d'*64}),
])
def test_receipt_refuses_invalid_schema(field,value):
    payload=record();payload[field]=value
    with pytest.raises(codec().RecordError): codec().decode_record(json.dumps(payload).encode())


@pytest.mark.parametrize('wire',[
    b'{}',b'[]',b'null',b'{',b'\xff', b'{"schema_version":1,"schema_version":1}',
    b' '*65537, json.dumps(dict(record(),extra='unrecognized')).encode(),
], ids=['empty','array','null','truncated','encoding','duplicate','oversized','extra'])
def test_receipt_refuses_invalid_or_unbounded_wire(wire):
    with pytest.raises(codec().RecordError): codec().decode_record(wire)


def test_unknown_schema_has_distinct_reason_and_recipe_is_comparable():
    payload=record();payload['schema_version']=2
    with pytest.raises(codec().RecordError) as exc: codec().decode_record(json.dumps(payload).encode())
    assert exc.value.reason=='unsupported_schema'
    payload=record();payload['recipe_version']=2
    assert codec().decode_record(json.dumps(payload).encode())['recipe_version']==2


def ready(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context=_context(tmp_data_dirs,['Claude Code','Codex'])
    monkeypatch.setattr(core,'DEFAULT_CONTEXT_PATH',context)
    return storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir


def snapshot(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def tripwire(*args,**kwargs):
    raise AssertionError('side-effect boundary invoked')


def generate(monkeypatch, **kwargs):
    captured=[]
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:_FakeProvider(_valid_payload(),captured))
    result=core.run_workflow_derivation(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK,**kwargs)
    return result,captured


@pytest.mark.parametrize('branch',['generate','reuse','force'])
def test_preview_metadata_is_separate_and_provider_free(tmp_data_dirs,monkeypatch,branch):
    dest=ready(tmp_data_dirs,monkeypatch)
    if branch!='generate':
        for name in ('05_prompt_examples.md','06_apply_to_my_workflow.md'): (dest/name).write_bytes(b'old')
    monkeypatch.setattr(core,'create_provider',tripwire)
    before=snapshot(tmp_data_dirs)
    result=core.run_workflow_derivation(PODCAST,EPISODE,force=branch=='force')
    assert result.metadata_writes==([] if branch=='reuse' else [str(dest/RECEIPT)])
    assert len(result.planned_writes)==(0 if branch=='reuse' else 2)
    assert snapshot(tmp_data_dirs)==before
    from corpus_ingest_core import mcp_server
    response=mcp_server.derive_workflow_bundle(PODCAST,EPISODE,force=branch=='force')
    assert response['metadata_writes']==result.metadata_writes
    assert response['writes']==result.planned_writes
    assert snapshot(tmp_data_dirs)==before

def test_confirm_records_consumed_inputs_and_actual_staged_bytes(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch)
    (dest/'03_full_summary.md').write_bytes(b'LF\nCRLF\r\n')
    (dest/'extra.bin').write_bytes(bytes(range(256))*100)
    before={p.name:p.read_bytes() for p in dest.iterdir()}
    result,captured=generate(monkeypatch)
    receipt=json.loads((dest/RECEIPT).read_bytes())
    assert result.metadata_writes==[str(dest/RECEIPT)]
    assert receipt['input_sha256']['lecture_03']==hashlib.sha256(before['03_full_summary.md']).hexdigest()
    assert receipt['request_sha256']==hashlib.sha256(json.dumps(captured[0],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert receipt['context_origin']=='default'
    for role,name in [('output_05','05_prompt_examples.md'),('output_06','06_apply_to_my_workflow.md')]:
        assert receipt['output_sha256'][role]==hashlib.sha256((dest/name).read_bytes()).hexdigest()
    for name,payload in before.items(): assert (dest/name).read_bytes()==payload
    assert 'Claude Code' not in json.dumps(receipt)
    assert str(tmp_data_dirs) not in json.dumps(receipt)


def test_provider_time_source_mutation_does_not_rewrite_recorded_inputs(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch); original=(dest/'04_learning_notes.md').read_bytes()
    context_before=core.DEFAULT_CONTEXT_PATH.read_bytes()
    class MutatingProvider:
        def complete(self,messages):
            (dest/'04_learning_notes.md').write_bytes(b'changed during provider call')
            core.DEFAULT_CONTEXT_PATH.write_text('allowed_tools: [Codex]\n',encoding='utf-8')
            return json.dumps(_valid_payload(),ensure_ascii=False)
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:MutatingProvider())
    core.run_workflow_derivation(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    receipt=json.loads((dest/RECEIPT).read_bytes())
    assert receipt['input_sha256']['lecture_04']==hashlib.sha256(original).hexdigest()
    assert receipt['input_sha256']['effective_context']==codec().canonical_digest(['Claude Code','Codex'])
    assert (dest/'04_learning_notes.md').read_bytes()==b'changed during provider call'


@pytest.mark.parametrize('defect',['malformed','unsupported','identity','stem','extra','oversized'])
@pytest.mark.parametrize('confirm',[False,True])
def test_generation_reserved_name_collision_refuses_before_provider(tmp_data_dirs,monkeypatch,defect,confirm):
    dest=ready(tmp_data_dirs,monkeypatch);payload=record()
    payload['identity_stem_sha256']=hashlib.sha256(dest.name.encode()).hexdigest()
    if defect=='unsupported':payload['schema_version']=99
    if defect=='identity':payload['episode_ref']='OTHER'
    if defect=='stem':payload['identity_stem_sha256']='f'*64
    if defect=='extra':payload['extra']='foreign'
    wire=b'{' if defect=='malformed' else b'x'*65537 if defect=='oversized' else json.dumps(payload).encode()
    (dest/RECEIPT).write_bytes(wire);before=snapshot(tmp_data_dirs)
    monkeypatch.setattr(core,'create_provider',tripwire)
    with pytest.raises(core.WorkflowDerivationError):
        core.run_workflow_derivation(PODCAST,EPISODE,force=True,confirm=confirm,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert snapshot(tmp_data_dirs)==before


def test_force_replaces_recognized_record_and_reuse_leaves_it_byte_identical(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    first=(dest/RECEIPT).read_bytes()
    (dest/'03_full_summary.md').write_bytes(b'new source')
    preview=core.run_workflow_derivation(PODCAST,EPISODE,force=True)
    assert str(dest/RECEIPT) in preview.planned_reads
    generate(monkeypatch,force=True)
    assert (dest/RECEIPT).read_bytes()!=first
    # Reuse intentionally does not manufacture or validate lineage.
    (dest/RECEIPT).write_bytes(b'legacy invalid receipt kept on reuse')
    monkeypatch.setattr(core,'create_provider',tripwire)
    reused=core.run_workflow_derivation(PODCAST,EPISODE,confirm=True)
    assert reused.metadata_writes==[]
    assert (dest/RECEIPT).read_bytes()==b'legacy invalid receipt kept on reuse'


@pytest.mark.parametrize('fault',['receipt-write','staged-hash','output-cap','backup','publish','rollback','cleanup','report'])
def test_record_publication_faults_keep_matching_tuple_or_recovery(tmp_data_dirs,monkeypatch,fault):
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    before={p.name:p.read_bytes() for p in dest.iterdir()}
    (dest/'extra.bin').write_bytes(b'preserve');before['extra.bin']=b'preserve'
    part=dest.with_name(dest.name+'.wfderive.part');old=dest.with_name(dest.name+'.wfderive.old')
    real_write=Path.write_bytes;real_rename=Path.rename;real_read=core.secure_read_bytes
    def write(path,payload):
        if fault=='receipt-write' and path==part/RECEIPT:raise OSError('private receipt write failure')
        return real_write(path,payload)
    def rename(path,target):
        if (fault=='backup' and path==dest) or (fault in {'publish','rollback'} and path==part) or (fault=='rollback' and path==old):raise OSError('private rename failure')
        return real_rename(path,target)
    def read(root,path,**kwargs):
        if fault=='staged-hash' and path==part/'05_prompt_examples.md':return None
        return real_read(root,path,**kwargs)
    monkeypatch.setattr(Path,'write_bytes',write);monkeypatch.setattr(Path,'rename',rename);monkeypatch.setattr(core,'secure_read_bytes',read)
    if fault=='output-cap':monkeypatch.setattr(codec(),'MAX_OUTPUT_BYTES',1)
    if fault=='cleanup':monkeypatch.setattr(core,'_cleanup_committed_backup',lambda *a: (_ for _ in ()).throw(core.WorkflowDerivationStateError('published_cleanup_failed')))
    if fault=='report':monkeypatch.setattr(core,'write_part_staged_report_pair',lambda *a: (_ for _ in ()).throw(OSError('private report failure')))
    with pytest.raises(core.WorkflowDerivationStateError) as exc:generate(monkeypatch,force=True)
    expected='rollback_failed' if fault=='rollback' else 'published_cleanup_failed' if fault=='cleanup' else 'published_report_failed' if fault=='report' else 'publish_failed'
    assert exc.value.reason_code==expected
    if fault=='rollback':
        assert not dest.exists() and old.is_dir() and part.is_dir()
        assert {p.name:p.read_bytes() for p in old.iterdir()}==before
        assert codec().decode_record((part/RECEIPT).read_bytes())['output_sha256']['output_05']==hashlib.sha256((part/'05_prompt_examples.md').read_bytes()).hexdigest()
    elif fault in {'cleanup','report'}:
        receipt=codec().decode_record((dest/RECEIPT).read_bytes())
        assert receipt['output_sha256']['output_06']==hashlib.sha256((dest/'06_apply_to_my_workflow.md').read_bytes()).hexdigest()
        assert (dest/'extra.bin').read_bytes()==b'preserve'
    else:
        assert {p.name:p.read_bytes() for p in dest.iterdir()}==before
        assert not part.exists() and not old.exists()

def inspect():
    return core.inspect_workflow_derivation_lineage(PODCAST,EPISODE)


@pytest.mark.parametrize('state',['not_generated','untracked','current','custom','partial','orphan'])
def test_inspection_states_and_zero_side_effects(tmp_data_dirs,monkeypatch,state):
    dest=ready(tmp_data_dirs,monkeypatch)
    if state in {'current','custom','partial','orphan'}:
        generate(monkeypatch,**({'workflow_context':core.DEFAULT_CONTEXT_PATH} if state=='custom' else {}))
        if state in {'partial','orphan'}:(dest/'05_prompt_examples.md').unlink()
        if state=='orphan':(dest/'06_apply_to_my_workflow.md').unlink()
    elif state=='untracked':
        for name in ('05_prompt_examples.md','06_apply_to_my_workflow.md'):(dest/name).write_bytes(b'legacy')
    before=snapshot(tmp_data_dirs)
    monkeypatch.setattr(core,'create_provider',tripwire)
    monkeypatch.setattr(core,'run_workflow_derivation',tripwire)
    from corpus_ingest_core import cache
    monkeypatch.setattr(cache,'rebuild_cache',tripwire)
    for method in ('write_bytes','write_text','mkdir','rename','unlink'):
        monkeypatch.setattr(Path,method,tripwire)
    result=inspect()
    expected={'custom':('not_evaluated','custom_context'),'partial':('blocked','incomplete_pair'),'orphan':('blocked','incomplete_pair'),
              'not_generated':('not_generated','no_derivation'),'untracked':('untracked','no_record'),'current':('current','matches_record')}[state]
    assert (result['status'],result['reason'])==expected
    assert result['changed_roles']==[]
    assert result['scope']=='workflow_derivation_inputs_outputs'
    assert result['read_only'] is True and result['network_access'] is False
    assert result['warnings']==['derivation_scope_only','non_atomic_observation']
    assert snapshot(tmp_data_dirs)==before
    assert set(result)=={'podcast_id','episode_ref','status','reason','changed_roles','scope','read_only','network_access','warnings'}
    assert str(tmp_data_dirs) not in json.dumps(result)


@pytest.mark.parametrize('role',['lecture_03','lecture_04','lecture_07','effective_context','recipe','request','output_05','output_06'])
def test_default_inspection_reports_ordered_actual_changed_roles(tmp_data_dirs,monkeypatch,role):
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    names={'lecture_03':'03_full_summary.md','lecture_04':'04_learning_notes.md','lecture_07':'07_final_study_guide.md',
           'output_05':'05_prompt_examples.md','output_06':'06_apply_to_my_workflow.md'}
    if role in names:(dest/names[role]).write_bytes(b'PRIVATE_BODY_SENTINEL changed bytes')
    elif role=='effective_context':core.DEFAULT_CONTEXT_PATH.write_text('allowed_tools: [Codex, Claude Code, Codex]\n',encoding='utf-8')
    elif role=='recipe':monkeypatch.setattr(codec(),'RECIPE_VERSION',2)
    elif role=='request':
        real=core._build_messages
        monkeypatch.setattr(core,'_build_messages',lambda *a:real(*a)+[{'role':'user','content':'changed recipe layout'}])
    result=inspect()
    assert result['status']=='stale' and result['reason']=='observed_changes'
    assert result['changed_roles']==([role,'request'] if role.startswith('lecture_') or role=='effective_context' else [role])
    assert 'PRIVATE_BODY_SENTINEL' not in json.dumps(result)
    assert str(tmp_data_dirs) not in json.dumps(result)


def test_context_ignores_comments_and_unused_fields_but_preserves_duplicates(tmp_data_dirs,monkeypatch):
    ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    core.DEFAULT_CONTEXT_PATH.write_text('# unused comment\nother: ignored\nallowed_tools: [" Claude Code ", " Codex "]\n',encoding='utf-8')
    assert inspect()['status']=='current'
    core.DEFAULT_CONTEXT_PATH.write_text('allowed_tools: [Claude Code, Codex, Codex]\n',encoding='utf-8')
    assert inspect()['changed_roles']==['effective_context','request']


@pytest.mark.parametrize('defect,reason',[
    ('json','invalid_record'),('duplicate','invalid_record'),('schema','unsupported_schema'),('identity','identity_mismatch'),
    ('stem','identity_mismatch'),('oversized','record_unreadable'),('unreadable','record_unreadable'),
    ('input-missing','inputs_unavailable'),('input-encoding','inputs_unavailable'),('input-cap','inputs_unavailable'),
    ('context-missing','inputs_unavailable'),('context-invalid','inputs_unavailable'),('context-cap','inputs_unavailable'),
    ('output-cap','outputs_unavailable'),('output-unreadable','outputs_unavailable'),
])
def test_inspection_blocks_unverifiable_sources_instead_of_claiming_stale(tmp_data_dirs,monkeypatch,defect,reason):
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    receipt=json.loads((dest/RECEIPT).read_bytes())
    if defect=='json':(dest/RECEIPT).write_bytes(b'{')
    elif defect=='duplicate':(dest/RECEIPT).write_bytes(b'{"schema_version":1,"schema_version":1}')
    elif defect=='schema':receipt['schema_version']=99
    elif defect=='identity':receipt['episode_ref']='DIFFERENT'
    elif defect=='stem':receipt['identity_stem_sha256']='f'*64
    elif defect=='oversized':(dest/RECEIPT).write_bytes(b'x'*65537)
    elif defect=='input-missing':(dest/'03_full_summary.md').unlink()
    elif defect=='input-encoding':(dest/'03_full_summary.md').write_bytes(b'\xff')
    elif defect=='input-cap':monkeypatch.setattr(core,'_MAX_SOURCE_BYTES',1)
    elif defect=='context-missing':core.DEFAULT_CONTEXT_PATH.unlink()
    elif defect=='context-invalid':core.DEFAULT_CONTEXT_PATH.write_text('allowed_tools: []',encoding='utf-8')
    elif defect=='context-cap':core.DEFAULT_CONTEXT_PATH.write_bytes(b'x'*(core._MAX_SOURCE_BYTES+1))
    elif defect=='output-cap':monkeypatch.setattr(codec(),'MAX_OUTPUT_BYTES',1)
    if defect in {'schema','identity','stem'}:(dest/RECEIPT).write_bytes(json.dumps(receipt).encode())
    if defect in {'unreadable','output-unreadable'}:
        real=core.secure_read_bytes;target=dest/(RECEIPT if defect=='unreadable' else '05_prompt_examples.md')
        monkeypatch.setattr(core,'secure_read_bytes',lambda root,path,**k:None if path==target else real(root,path,**k))
    result=inspect()
    assert (result['status'],result['reason'],result['changed_roles'])==('blocked',reason,[])


@pytest.mark.parametrize('suffix',['.part','.old','.wfderive.part','.wfderive.old'])
def test_inspection_recovery_precedes_pair_states(tmp_data_dirs,monkeypatch,suffix):
    dest=ready(tmp_data_dirs,monkeypatch)
    dest.with_name(dest.name+suffix).write_bytes(b'recovery')
    assert inspect()['reason']=='recovery_required'


def test_custom_context_does_not_reopen_path_or_substitute_default(tmp_data_dirs,monkeypatch):
    ready(tmp_data_dirs,monkeypatch);generate(monkeypatch,workflow_context=core.DEFAULT_CONTEXT_PATH)
    monkeypatch.setattr(core,'_load_context',tripwire)
    monkeypatch.setattr(core,'_read_capped',tripwire)
    assert inspect()['reason']=='custom_context'


@pytest.mark.parametrize('podcast,episode',[(None,EPISODE),(PODCAST,None),('bad/path',EPISODE),(PODCAST,' latest'),(PODCAST,'NEXT'),(PODCAST,'../file')])
def test_inspection_invalid_identity_rejected_before_access(monkeypatch,podcast,episode):
    monkeypatch.setattr(core,'load_podcast_profile',tripwire)
    with pytest.raises(ValueError,match='Invalid explicit episode identity'):
        core.inspect_workflow_derivation_lineage(podcast,episode)


def test_query_does_not_fall_back_to_old_title(tmp_data_dirs,monkeypatch):
    ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    metadata=storage.transcript_asset_paths(PODCAST,EPISODE,TITLE).json_path
    payload=json.loads(metadata.read_text(encoding='utf-8'));payload['title']='Changed canonical title'
    metadata.write_text(json.dumps(payload),encoding='utf-8')
    assert inspect()['status']=='not_generated'

@pytest.mark.parametrize('location',['bundle-parent','receipt','output','extra','context'])
def test_query_simulated_reparse_is_refused_without_following_it(tmp_data_dirs,monkeypatch,location):
    from types import SimpleNamespace
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    (dest/'extra.bin').write_bytes(b'keep')
    target={'bundle-parent':dest.parent,'receipt':dest/RECEIPT,'output':dest/'05_prompt_examples.md','extra':dest/'extra.bin','context':core.DEFAULT_CONTEXT_PATH}[location]
    real=Path.lstat
    def metadata(path,*a,**k):
        info=real(path,*a,**k)
        return SimpleNamespace(st_mode=info.st_mode,st_file_attributes=0x400,st_size=info.st_size) if path==target else info
    monkeypatch.setattr(Path,'lstat',metadata)
    result=inspect()
    assert (result['status'],result['reason'])==('blocked','unsafe_path')


def test_query_special_entry_precedes_legacy_reuse(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch)
    for name in ('05_prompt_examples.md','06_apply_to_my_workflow.md'):(dest/name).write_bytes(b'legacy')
    (dest/'nested').mkdir()
    assert inspect()['reason']=='unsafe_path'


def test_mutation_during_generation_is_reported_stale_at_observation(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch)
    class Provider:
        def complete(self,messages):
            (dest/'07_final_study_guide.md').write_bytes(b'changed while generation runs')
            return json.dumps(_valid_payload(),ensure_ascii=False)
    monkeypatch.setattr(core,'create_provider',lambda *a,**k:Provider())
    core.run_workflow_derivation(PODCAST,EPISODE,confirm=True,api_cost_ack=SEMANTIC_API_COST_ACK)
    assert inspect()['changed_roles']==['lecture_07','request']


def test_query_safe_lecture_read_failure_is_inputs_unavailable(tmp_data_dirs,monkeypatch):
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    real=core.secure_read_bytes
    monkeypatch.setattr(core,'secure_read_bytes',lambda root,path,**k:None if path==dest/'03_full_summary.md' else real(root,path,**k))
    result=inspect()
    assert (result['status'],result['reason'],result['changed_roles'])==('blocked','inputs_unavailable',[])


@pytest.mark.parametrize('location',['bundle','output','receipt'])
def test_query_unsafe_entry_precedes_simultaneous_recovery(tmp_data_dirs,monkeypatch,location):
    from types import SimpleNamespace
    dest=ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    dest.with_name(dest.name+'.old').write_bytes(b'recovery evidence')
    target={'bundle':dest,'output':dest/'05_prompt_examples.md','receipt':dest/RECEIPT}[location]
    real=Path.lstat
    def metadata(path,*a,**k):
        info=real(path,*a,**k)
        return SimpleNamespace(st_mode=info.st_mode,st_file_attributes=0x400,st_size=info.st_size) if path==target else info
    monkeypatch.setattr(Path,'lstat',metadata)
    result=inspect()
    assert (result['status'],result['reason'])==('blocked','unsafe_path')


def test_query_unknown_configured_slug_is_identity_unavailable(tmp_data_dirs):
    result=core.inspect_workflow_derivation_lineage('unconfigured-lineage-test','EP_001')
    assert (result['status'],result['reason'])==('blocked','identity_unavailable')


@pytest.mark.parametrize('failure',['missing','unreadable','yaml'])
def test_query_unavailable_profile_is_identity_unavailable(monkeypatch,failure):
    import yaml
    error={'missing':FileNotFoundError,'unreadable':PermissionError,'yaml':yaml.YAMLError}[failure]
    def load(*a):raise error('PRIVATE_PROFILE_SENTINEL')
    monkeypatch.setattr(core,'load_podcast_profile',load)
    result=inspect()
    assert (result['status'],result['reason'])==('blocked','identity_unavailable')
    assert 'PRIVATE_PROFILE_SENTINEL' not in json.dumps(result)


@pytest.mark.parametrize('episode',['_not-canonical','-not-canonical'])
def test_codec_refuses_noncanonical_episode_start(episode):
    payload=record();payload['episode_ref']=episode
    with pytest.raises(codec().RecordError):codec().decode_record(json.dumps(payload).encode())


def test_query_unencodable_yaml_context_is_inputs_unavailable(tmp_data_dirs,monkeypatch):
    ready(tmp_data_dirs,monkeypatch);generate(monkeypatch)
    core.DEFAULT_CONTEXT_PATH.write_bytes(b'allowed_tools: ["'+bytes([92])+b'ud800"]'+bytes([10]))
    result=inspect()
    assert (result['status'],result['reason'],result['changed_roles'])==('blocked','inputs_unavailable',[])


def test_lecture_cover_only_preserves_lineage_and_pair_bytes(tmp_data_dirs,monkeypatch):
    from tests.test_study_guide_bundle import _generated_bundle
    from corpus_ingest_core import study_guide_bundle
    _generated_bundle(tmp_data_dirs,monkeypatch)
    monkeypatch.setattr(core,'DEFAULT_CONTEXT_PATH',_context(tmp_data_dirs,['Claude Code','Codex']))
    dest=storage.study_guide_bundle_paths(PODCAST,EPISODE,TITLE).bundle_dir
    generate(monkeypatch)
    before={p.name:p.read_bytes() for p in dest.iterdir() if p.name!='00_video_info.md'}
    (dest/'00_video_info.md').unlink()
    monkeypatch.setattr(study_guide_bundle,'create_provider',tripwire)
    monkeypatch.setattr(core,'create_provider',tripwire)
    preview=study_guide_bundle.run_study_guide_bundle(PODCAST,EPISODE)
    assert preview.planned_writes==[str(dest/'00_video_info.md')]
    study_guide_bundle.run_study_guide_bundle(PODCAST,EPISODE,confirm=True)
    assert before=={p.name:p.read_bytes() for p in dest.iterdir() if p.name!='00_video_info.md'}
    assert inspect()['status']=='current'
