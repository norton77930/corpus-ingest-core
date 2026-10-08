"""SPEC056 public offline read behavior; real files, bounded synthetic inputs."""
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from corpus_ingest_core import storage


def core():
    assert importlib.util.find_spec('corpus_ingest_core.source_content_query') is not None, 'offline source reader is missing'
    return importlib.import_module('corpus_ingest_core.source_content_query')


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root = tmp_path / 'transcripts'
    root.mkdir()
    monkeypatch.setattr(storage, 'TRANSCRIPTS_DIR', root)
    def write(podcast='show', episode='EP1', title='Evidence', segments=None, **updates):
        paths = storage.transcript_asset_paths(podcast, episode, title)
        paths.json_path.parent.mkdir(exist_ok=True)
        payload = dict(podcast_id=podcast, episode_ref=episode, title=title, language='en', completed=True,
                       segments=segments if segments is not None else [
                           dict(id=17,start=0,end=12,text='Verification first.'),
                           dict(id=17,start=10,end=15,text='CLI tools are deterministic.'),
                           dict(id={'hostile':'id'},start=20,end=30,text='Skills preserve lessons.')])
        payload['segment_count'] = len(payload['segments'])
        payload.update(updates)
        paths.json_path.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
        paths.text_path.write_text('Source text',encoding='utf-8')
        paths.srt_path.write_text('1\n00:00:00,000 --> 00:00:12,000\nVerification first.',encoding='utf-8')
        return paths,payload
    return root,write


def inspect(podcast='show',episode='EP1'):
    return core().query_source_content(podcast,episode)


def read(version,**kwargs):
    return core().query_source_content('show','EP1',action='read',expected_source_version=version,**kwargs)


def reason(expected, function):
    with pytest.raises(core().SourceContentError) as error:
        function()
    assert error.value.reason == expected


@pytest.mark.parametrize('podcast,episode',[('show','EP1'),('yt-example','Ab_Cd-12345'),('x-example','2106893534980685927')])
def test_prepared_sources_read_without_index(prepared,podcast,episode):
    root,write = prepared
    paths,payload = write(podcast,episode)
    metadata = inspect(podcast,episode)
    assert metadata['source_version'] == hashlib.sha256(paths.json_path.read_bytes()).hexdigest()
    assert metadata['segment_count'] == 3 and metadata['end_seconds'] == 30
    assert metadata['actual_transcription'] is None and 'segments' not in metadata
    page = core().query_source_content(podcast,episode,action='read',expected_source_version=metadata['source_version'])
    assert [s['ordinal'] for s in page['segments']] == [0,1,2]
    assert [s['segment_id'] for s in page['segments']] == [17,17,None]
    assert page['coverage']['complete'] and page['next_cursor'] is None
    assert not list(root.parent.rglob('*.sqlite3'))


def test_long_text_reconstructs_with_pinned_pages(prepared):
    _,write=prepared
    text='verification ' * 3000
    write(segments=[dict(id='same',start=0,end=30,text=text),dict(id='same',start=30,end=40,text='tail')])
    version=inspect()['source_version']
    cursor=''; chunks=[]; offsets=[]; pages=[]
    for _ in range(1000):
        page=read(version,cursor=cursor,max_chars=97,limit=1)
        pages.append(page)
        assert sum(len(s['text']) for s in page['segments']) <=97
        for segment in page['segments']:
            if segment['ordinal']==0: chunks.append(segment['text']);offsets.append(segment['text_offset'])
        cursor=page['next_cursor']
        if cursor is None:break
    else:pytest.fail('pagination did not progress')
    assert ''.join(chunks)==text
    assert offsets==list(range(0,len(text),97))
    assert pages[-1]['coverage']['scope_exhausted'] and not pages[-1]['coverage']['complete']
    assert pages[0]['coverage']['truncated']


def test_range_overlap_and_literal_search_scope(prepared):
    _,write=prepared;write()
    version=inspect()['source_version']
    page=read(version,start_seconds=11,end_seconds=20)
    assert [s['ordinal'] for s in page['segments']]==[0,1]
    assert page['coverage']['scope']=='time_range'
    found=core().query_source_content('show','EP1',action='search',expected_source_version=version,query='VERIFICATION')
    assert [s['ordinal'] for s in found['segments']]==[0]
    assert found['search']['total_matches']==1 and found['search']['scanned_segments']==3
    absent=core().query_source_content('show','EP1',action='search',expected_source_version=version,query='驗證')
    assert absent['segments']==[] and absent['search']['total_matches']==0
    assert absent['search']['mode']=='literal_keyword'


def test_source_change_and_scope_cursor_mismatch(prepared):
    _,write=prepared;paths,payload=write()
    version=inspect()['source_version'];page=read(version,limit=1)
    reason('invalid_cursor',lambda:read(version,cursor=page['next_cursor'],start_seconds=1))
    reason('invalid_cursor',lambda:read(version,cursor='hostile cursor'))
    payload['segments'][0]['text']='replacement'
    paths.json_path.write_text(json.dumps(payload),encoding='utf-8')
    reason('source_changed',lambda:read(version,cursor=page['next_cursor']))


@pytest.mark.parametrize('kwargs',[{'episode_ref':'../private'},{'podcast_id':'../private'},{'episode_ref':'latest'},
 {'action':'run'},{'limit':True},{'max_chars':0},{'start_seconds':float('nan')},{'end_seconds':True},
 {'start_seconds':10,'end_seconds':5},{'action':'read'},{'action':'read','expected_source_version':'private'},
 {'action':'search','query':''},{'query':'not relevant'},{'limit':1000}])
def test_invalid_request_is_finite(prepared,kwargs):
    prepared[1]()
    args=dict(podcast_id='show',episode_ref='EP1');args.update(kwargs)
    reason('invalid_request',lambda:core().query_source_content(**args))


@pytest.mark.parametrize('mutation,expected',[
 ('empty','source_empty'),('incomplete','source_incomplete'),('identity','source_invalid'),('title','source_invalid'),
 ('nan','source_invalid'),('bool_time','source_invalid'),('nontext','source_invalid'),('count','source_invalid'),
 ('order','source_invalid'),('blank','source_invalid')])
def test_invalid_transcripts_do_not_expose_text(prepared,mutation,expected):
    _,write=prepared;paths,p=write()
    if mutation=='empty':p['segments']=[];p['segment_count']=0
    elif mutation=='incomplete':p['completed']=False
    elif mutation=='identity':p['episode_ref']='EP2'
    elif mutation=='title':p['title']='Different'
    elif mutation=='nan':p['segments'][0]['end']=float('inf')
    elif mutation=='bool_time':p['segments'][0]['start']=True
    elif mutation=='nontext':p['segments'][0]['text']={'private':'value'}
    elif mutation=='count':p['segment_count']=999
    elif mutation=='order':p['segments'][1]['start']=0;p['segments'][0]['start']=1
    elif mutation=='blank':p['segments'][0]['text']=' '
    paths.json_path.write_text(json.dumps(p),encoding='utf-8')
    reason(expected,inspect)


def test_legacy_completion_unknown_and_recorded_model(prepared):
    _,write=prepared;paths,p=write(model='medium',device='cuda',compute_type='float16',vad_filter=True)
    p.pop('completed');paths.json_path.write_text(json.dumps(p),encoding='utf-8')
    result=inspect()
    assert 'legacy_completion_unknown' in result['warnings']
    assert result['actual_transcription']['model']=='medium'


@pytest.mark.parametrize('suffix',['.json.part','.txt.old','.json.wfderive.backup'])
def test_recovery_markers_block_without_cleanup(prepared,suffix):
    _,write=prepared;paths,_=write()
    marker=paths.json_path.with_suffix(suffix);marker.write_text('private',encoding='utf-8')
    reason('source_incomplete',inspect)
    assert marker.read_text()=='private'


def test_ambiguity_and_missing_companion_fail(prepared):
    _,write=prepared;paths,_=write()
    paths.text_path.unlink()
    reason('source_incomplete',inspect)
    write();write(title='Other')
    reason('source_ambiguous',inspect)


def test_missing_source_does_not_create_directories(prepared):
    root,_=prepared
    reason('source_missing',inspect)
    assert list(root.iterdir())==[]


@pytest.mark.parametrize('suffix',['.json','.txt','.srt'])
def test_hardlinks_rejected_before_body_read(prepared,monkeypatch,suffix):
    import corpus_ingest_core.secure_local_snapshot as snapshots
    _,write=prepared;paths,_=write()
    target=paths.json_path.with_suffix(suffix)
    alias=target.parent.parent/'private-copy'
    os.link(target,alias)
    original=snapshots._read_descriptor_once
    def guarded(fd,size):
        assert os.fstat(fd).st_ino != target.stat().st_ino, 'hardlink body was read'
        return original(fd,size)
    monkeypatch.setattr(snapshots,'_read_descriptor_once',guarded)
    reason('unsafe_source',inspect)


def test_nonregular_candidate_refused(prepared):
    _,write=prepared;paths,_=write()
    paths.json_path.unlink();paths.json_path.mkdir()
    reason('unsafe_source',inspect)


def test_snapshot_opt_in_rejects_handle_link_race(prepared,monkeypatch):
    import corpus_ingest_core.secure_local_snapshot as snapshots
    root,write=prepared;paths,_=write()
    assert 'require_single_link' in __import__('inspect').signature(snapshots.secure_snapshot).parameters
    original=os.fstat
    def raced(fd):
        result=original(fd)
        if result.st_ino==paths.json_path.stat().st_ino:
            return SimpleNamespace(**{name:getattr(result,name) for name in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')},st_nlink=2)
        return result
    monkeypatch.setattr(snapshots.os,'fstat',raced)
    assert snapshots.secure_snapshot(root,paths.json_path,max_bytes=999999,require_single_link=True) is None


def test_query_preserves_all_owned_bytes_and_avoids_external_work(prepared,monkeypatch):
    import socket,sqlite3
    from corpus_ingest_core import cache,feed_reader,downloader,transcriber,llm_provider
    root,write=prepared;write()
    before={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def forbidden(*args,**kwargs):pytest.fail('query performed unauthorized external work')
    monkeypatch.setattr(socket,'create_connection',forbidden)
    monkeypatch.setattr(sqlite3,'connect',forbidden)
    for module,name in [(cache,'rebuild_cache'),(feed_reader,'get_episode'),(downloader,'download_audio'),(transcriber,'transcribe_episode'),(llm_provider,'create_provider')]:
        monkeypatch.setattr(module,name,forbidden)
    version=inspect()['source_version'];read(version)
    assert before=={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}

def test_huge_integer_request_has_finite_reason(prepared):
    prepared[1]()
    reason('invalid_request',lambda:core().query_source_content('show','EP1',start_seconds=10**400))


def test_huge_integer_timestamp_has_finite_reason(prepared):
    _,write=prepared;write(segments=[dict(id=0,start=0,end=10**400,text='source')])
    reason('source_invalid',inspect)


def test_distinct_large_integer_time_windows_do_not_share_cursor(prepared):
    lower=2**53
    prepared[1](segments=[dict(id=i,start=lower+i*2,end=lower+i*2,text=str(i)) for i in range(3)])
    version=inspect()['source_version']
    page=read(version,start_seconds=lower,limit=1)
    reason('invalid_cursor',lambda:read(version,start_seconds=lower+1,cursor=page['next_cursor']))


def test_snapshot_parent_redirect_rejected_before_read(prepared,monkeypatch):
    import corpus_ingest_core.secure_local_snapshot as snapshots
    root,write=prepared;paths,_=write()
    original=snapshots._safe_parent_chain
    checks=0
    def redirected(checked_root,path):
        nonlocal checks
        checks+=1
        return original(checked_root,path) if checks==1 else False
    reads=[]
    original_read=snapshots._read_descriptor_once
    def observed(fd,size):
        reads.append(fd)
        return original_read(fd,size)
    monkeypatch.setattr(snapshots,'_safe_parent_chain',redirected)
    monkeypatch.setattr(snapshots,'_read_descriptor_once',observed)
    assert snapshots.secure_snapshot(root,paths.json_path,max_bytes=999999,require_single_link=True) is None
    assert reads==[], 'parent redirect body read before refusal'


@pytest.mark.parametrize('index,offset',[(True,0),(-1,0),(999,0),(0,True),(0,-1),(0,999)])
def test_tampered_cursor_positions_refused(prepared,index,offset):
    import base64
    prepared[1]();metadata=inspect();version=metadata['source_version']
    # Characterize legacy input independently of the current emitted format.
    value=[core()._binding(metadata,'read','',None,None),index,offset]
    cursor=base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
    reason('invalid_cursor',lambda:read(version,cursor=cursor))


def test_zero_duration_boundary_and_max_extent(prepared):
    prepared[1](segments=[dict(id=0,start=0,end=100,text='overlap'),dict(id=1,start=10,end=10,text='point'),dict(id=2,start=20,end=20,text='last point')])
    metadata=inspect();assert metadata['end_seconds']==100
    page=read(metadata['source_version'],start_seconds=10,end_seconds=20)
    assert [s['ordinal'] for s in page['segments']]==[0,1]


def test_byte_cap_exact_and_one_over(prepared,monkeypatch):
    paths,_=prepared[1]();size=paths.json_path.stat().st_size
    monkeypatch.setattr(core(),'_MAX_BYTES',size)
    assert inspect()['segment_count']==3
    paths.json_path.write_bytes(paths.json_path.read_bytes()+b' ')
    reason('unsafe_source',inspect)


def test_segment_query_and_page_caps(prepared,monkeypatch):
    _,write=prepared;write()
    monkeypatch.setattr(core(),'_MAX_SEGMENTS',3)
    version=inspect()['source_version']
    assert read(version,limit=100,max_chars=12000)['coverage']['complete']
    reason('invalid_request',lambda:read(version,limit=101))
    reason('invalid_request',lambda:read(version,max_chars=12001))
    assert core().query_source_content('show','EP1',action='search',expected_source_version=version,query='a'*256)['search']['total_matches']==0
    reason('invalid_request',lambda:core().query_source_content('show','EP1',action='search',expected_source_version=version,query='a'*257))
    write(segments=[dict(start=i,end=i+1,text='x') for i in range(4)])
    reason('source_invalid',inspect)


def test_candidate_cap_refuses_before_read(prepared,monkeypatch):
    root,_=prepared;folder=root/'show';folder.mkdir()
    for i in range(9):(folder/f'EP1__candidate{i}.json').write_text('private',encoding='utf-8')
    def forbidden(*a,**k):pytest.fail('over-cap candidate body read')
    monkeypatch.setattr(core(),'secure_read_bytes',forbidden)
    reason('unsafe_source',inspect)


def test_directory_entry_cap_refuses_before_source_read(prepared):
    root,_=prepared;folder=root/'show';folder.mkdir()
    for i in range(4097):(folder/f'entry{i}').touch()
    reason('unsafe_source',inspect)


def test_json_replacement_during_invocation_refused(prepared,monkeypatch):
    _,write=prepared;paths,payload=write()
    original=core().secure_read_bytes
    replaced=False
    def observed(root,path,**kwargs):
        nonlocal replaced
        raw=original(root,path,**kwargs)
        if path==paths.text_path and not replaced:
            replaced=True;payload['segments'][0]['text']='New evidence'
            paths.json_path.write_text(json.dumps(payload),encoding='utf-8')
        return raw
    monkeypatch.setattr(core(),'secure_read_bytes',observed)
    reason('source_changed',inspect)


def test_same_inode_modification_during_snapshot_refused(prepared,monkeypatch):
    import corpus_ingest_core.secure_local_snapshot as snapshots
    root,write=prepared;paths,_=write()
    original=snapshots._read_descriptor_once
    def mutated(fd,size):
        raw=original(fd,size)
        paths.json_path.write_bytes(raw.replace(b'first.',b'later.'))
        value=paths.json_path.stat()
        os.utime(paths.json_path,ns=(value.st_atime_ns,value.st_mtime_ns+1_000_000))
        return raw
    monkeypatch.setattr(snapshots,'_read_descriptor_once',mutated)
    assert snapshots.secure_snapshot(root,paths.json_path,max_bytes=999999,require_single_link=True) is None


def test_simulated_reparse_candidate_refused_before_read(prepared,monkeypatch):
    import corpus_ingest_core.secure_local_snapshot as snapshots
    _,write=prepared;paths,_=write();inode=paths.json_path.stat().st_ino
    original=snapshots._is_reparse
    monkeypatch.setattr(snapshots,'_is_reparse',lambda value:value.st_ino==inode or original(value))
    reason('unsafe_source',inspect)


def test_leaf_reparse_swap_after_open_refused_before_read(prepared,monkeypatch):
    import stat
    import corpus_ingest_core.secure_local_snapshot as snapshots
    root,write=prepared;paths,_=write()
    original_lstat=Path.lstat
    leaf_calls=0
    def swapped(path,*args,**kwargs):
        nonlocal leaf_calls
        value=original_lstat(path,*args,**kwargs)
        if path==paths.json_path:
            leaf_calls+=1
            if leaf_calls>=2:
                return SimpleNamespace(st_mode=stat.S_IFLNK|0o777,st_dev=value.st_dev,st_ino=value.st_ino,
                    st_size=value.st_size,st_nlink=1,st_mtime_ns=value.st_mtime_ns,st_ctime_ns=value.st_ctime_ns)
        return value
    reads=[];original_read=snapshots._read_descriptor_once
    def observed(fd,size):
        reads.append(fd);return original_read(fd,size)
    monkeypatch.setattr(Path,'lstat',swapped)
    monkeypatch.setattr(snapshots,'_read_descriptor_once',observed)
    assert snapshots.secure_snapshot(root,paths.json_path,max_bytes=999999,require_single_link=True) is None
    assert reads==[], 'leaf reparse body was read before refusal'
