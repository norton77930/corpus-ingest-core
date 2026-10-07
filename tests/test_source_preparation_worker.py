"""One-job lifecycle; actual media/provider calls are replaced by owned fakes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from tests.test_source_preparation import configured_source, transcript, URL, YT_URL


def worker():
    from corpus_ingest_core import source_preparation_worker
    return source_preparation_worker


def submit(monkeypatch, url=URL):
    from corpus_ingest_core import source_preparation as core
    monkeypatch.setattr(core, "launch_worker", lambda _: None)
    plan = core.prepare_learning_source(url)
    return core.prepare_learning_source(url, confirm=True, expected_plan_id=plan["plan_id"])


def fake_media(monkeypatch, module, *, fail_report=False):
    called = []
    def acquire(_url, target, _work_dir):
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b"owned audio")
        called.append("download")
    def transcribe(podcast_id, episode_ref, **kwargs):
        assert kwargs["force"] is False
        paths = transcript(podcast_id=podcast_id,episode_ref=episode_ref,title=kwargs["title"])
        payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
        paths.json_path.write_text(json.dumps({**payload, **{key: kwargs[key] for key in ("model", "device", "compute_type", "vad_filter")}}), encoding="utf-8")
        called.append("transcribe")
        return SimpleNamespace(json_path=paths.json_path)
    monkeypatch.setattr(module,"_acquire_audio",acquire)
    monkeypatch.setattr(module,"transcribe_episode",transcribe)
    if fail_report:
        def report(result):
            path = Path(result.report_json_path + ".part")
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b"preserve partial report")
            raise OSError("private diagnostic must not leak")
        monkeypatch.setattr(module,"_write_run_report",report)
    return called


@pytest.mark.parametrize("url,module_name", [(URL,"x_video_ingest"),(YT_URL,"youtube_video_ingest")])
def test_one_owned_worker_validates_transcript_and_stops(configured_source, monkeypatch, url, module_name):
    from corpus_ingest_core import source_preparation_jobs as jobs
    import corpus_ingest_core
    module = __import__("corpus_ingest_core." + module_name,fromlist=[module_name])
    job = submit(monkeypatch,url)
    calls = fake_media(monkeypatch,module)
    assert worker().run_worker(job["job_id"]) == 0
    status = jobs.inspect(job["job_id"])
    assert status["transcript_ready"] is True and status["study_guide_ready"] is False
    assert status["stage"] == "validating" and jobs.active_job() is None
    assert calls == ["download","transcribe"]
    assert worker().run_worker(job["job_id"]) == 1
    assert calls == ["download","transcribe"]


@pytest.mark.parametrize("url,module_name", [(URL,"x_video_ingest"),(YT_URL,"youtube_video_ingest")])
def test_running_worker_does_not_require_permission_to_launch_another_worker(configured_source, monkeypatch, url, module_name):
    from corpus_ingest_core import source_preparation as core, source_preparation_jobs as jobs
    module = __import__("corpus_ingest_core." + module_name, fromlist=[module_name])
    job = submit(monkeypatch, url)
    calls = fake_media(monkeypatch, module)

    def refused_launch():
        raise core.PreparationError("worker_host_incompatible")

    monkeypatch.setattr(core, "_worker_flags", refused_launch)
    assert worker().run_worker(job["job_id"]) == 0
    status = jobs.inspect(job["job_id"])
    assert status["transcript_ready"] is True
    assert jobs.active_job() is None
    assert calls == ["download", "transcribe"]


def test_unknown_worker_job_has_no_effects(tmp_data_dirs):
    assert worker().run_worker("f"*32) == 1
    assert worker().run_worker("../other") == 1
    assert not (tmp_data_dirs/"preparation-jobs").exists()


def test_worker_drift_refuses_before_media_and_preserves_partial(configured_source, monkeypatch):
    from corpus_ingest_core import storage, x_video_ingest
    from corpus_ingest_core import source_preparation_jobs as jobs
    job = submit(monkeypatch)
    partial = storage.transcript_asset_paths("x-demo","123456789","Demo").json_path.with_suffix(".json.part")
    partial.parent.mkdir(parents=True,exist_ok=True)
    partial.write_bytes(b"preserve")
    calls = fake_media(monkeypatch,x_video_ingest)
    assert worker().run_worker(job["job_id"]) == 1
    assert calls == [] and partial.read_bytes() == b"preserve"
    assert jobs.inspect(job["job_id"])["reason"] == "plan_changed"


def test_report_failure_preserves_outputs_and_occupied_slot(configured_source, monkeypatch):
    from corpus_ingest_core import x_video_ingest, storage
    from corpus_ingest_core import source_preparation_jobs as jobs
    job = submit(monkeypatch)
    fake_media(monkeypatch,x_video_ingest,fail_report=True)
    assert worker().run_worker(job["job_id"]) == 1
    status = jobs.inspect(job["job_id"])
    assert status["status"] == "attention_required" and status["transcript_ready"] is False
    assert "private diagnostic" not in json.dumps(jobs.load(job["job_id"]))
    assert jobs.active_job()["job_id"] == job["job_id"]
    assert storage.transcript_asset_paths("x-demo","123456789","Demo").json_path.is_file()
    assert list(storage.CORPUS_DIR.rglob("*.part"))


def test_worker_rechecks_executor_identity_before_first_write(configured_source, monkeypatch):
    from corpus_ingest_core import x_video_ingest
    from corpus_ingest_core import source_preparation_jobs as jobs
    job = submit(monkeypatch)
    calls = []
    def changed(_url, **kwargs):
        kwargs["progress_callback"]("downloading",dict(podcast_id="x-other",episode_ref="123456789",canonical_url=URL))
        calls.append("unsafe effect")
    monkeypatch.setattr(x_video_ingest,"run_x_video_ingest",changed)
    assert worker().run_worker(job["job_id"]) == 1
    assert calls == [] and jobs.inspect(job["job_id"])["reason"] == "plan_changed"


def test_validation_failure_cannot_become_ready(configured_source, monkeypatch):
    from corpus_ingest_core import x_video_ingest
    from corpus_ingest_core import source_preparation_jobs as jobs
    job = submit(monkeypatch)
    fake_media(monkeypatch,x_video_ingest)
    monkeypatch.setattr(x_video_ingest,"transcribe_episode",lambda *a,**kw: SimpleNamespace(json_path="unused"))
    assert worker().run_worker(job["job_id"]) == 1
    status = jobs.inspect(job["job_id"])
    assert status["reason"] == "validation_failed" and not status["transcript_ready"]


def test_launcher_uses_only_fixed_command_context_and_hidden_window(configured_source, monkeypatch):
    from corpus_ingest_core import source_preparation as core
    from corpus_ingest_core.local_env_names import DATA_DIR_ENV, CONFIG_ENV
    captured=[]
    monkeypatch.setattr(core.subprocess,"Popen",lambda command,**kwargs: captured.append((command,kwargs)) or SimpleNamespace(pid=123))
    plan=core.prepare_learning_source(URL)
    start=time.monotonic()
    response=core.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"])
    assert time.monotonic()-start < 2
    command,options=captured[0]
    assert command[0]==sys.executable and command[-1]==response["job_id"] and len(command)==3
    assert options["env"][DATA_DIR_ENV]==str(configured_source.absolute())
    assert options["env"][CONFIG_ENV]==str((configured_source/"profiles.yaml").absolute())
    assert options["stdin"]==options["stdout"]==options["stderr"]==subprocess.DEVNULL
    assert options["close_fds"] is True
    if os.name == "nt":
        assert options["creationflags"] & subprocess.CREATE_NO_WINDOW
    else:
        assert options["start_new_session"] is True


@pytest.mark.parametrize("policy,expected",[(None,0),(0x1000,0),(0x800,0x01000000),(0,None)])
def test_windows_worker_flags_respect_host_policy(monkeypatch,policy,expected):
    from corpus_ingest_core import source_preparation as core
    monkeypatch.setattr(core,"_windows_job_limits",lambda:policy,raising=False)
    if expected is None:
        with pytest.raises(core.PreparationError,match="worker_host_incompatible"):
            core._windows_worker_flags()
    else:
        flags=core._windows_worker_flags()
        assert flags & 0x01000000 == expected


def test_restrictive_host_preview_has_no_writes_or_admission(configured_source,monkeypatch):
    from corpus_ingest_core import source_preparation as core
    def incompatible():raise core.PreparationError("worker_host_incompatible")
    monkeypatch.setattr(core,"_worker_flags",incompatible,raising=False)
    plan=core.prepare_learning_source(URL)
    assert plan["status"]=="blocked" and plan["reason"]=="worker_host_incompatible"
    assert plan["writes"]==[] and not plan["requires_confirmation"]
    assert not (configured_source/"preparation-jobs").exists()


@pytest.mark.parametrize("failure,expected", [(OSError,"failed"),(RuntimeError,"attention_required")])
def test_known_and_uncertain_launch_outcomes_are_recorded(configured_source, monkeypatch, failure, expected):
    from corpus_ingest_core import source_preparation as core
    from corpus_ingest_core import source_preparation_jobs as jobs
    monkeypatch.setattr(core.subprocess,"Popen",lambda *a,**k: (_ for _ in ()).throw(failure("private diagnostic")))
    plan=core.prepare_learning_source(URL)
    with pytest.raises(core.PreparationError):
        core.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"])
    previous=jobs.source_history("x-video:"+URL)
    assert previous["status"]==expected
    assert (jobs.active_job() is not None)==(expected=="attention_required")
    assert "private diagnostic" not in json.dumps(previous)


def test_worker_heartbeat_store_failure_never_reports_ready(configured_source, monkeypatch):
    from corpus_ingest_core import x_video_ingest
    from corpus_ingest_core import source_preparation_jobs as jobs
    job=submit(monkeypatch)
    fake_media(monkeypatch,x_video_ingest)
    original=jobs.update
    def unavailable(*args,**kwargs):
        if kwargs.get("status")=="transcript_ready":
            raise jobs.PreparationError("store_unavailable")
        return original(*args,**kwargs)
    monkeypatch.setattr(jobs,"update",unavailable)
    assert worker().run_worker(job["job_id"])==1
    assert not jobs.inspect(job["job_id"])["transcript_ready"]
    assert jobs.active_job() is not None


@pytest.mark.parametrize("module_name,url,podcast_id,episode_ref",[("x_video_ingest",URL,"x-demo","123456789"),("youtube_video_ingest",YT_URL,"yt-demo","abc_def-hij")])
def test_real_acquisition_failure_preserves_managed_partial(configured_source,monkeypatch,module_name,url,podcast_id,episode_ref):
    import importlib
    from corpus_ingest_core import storage,source_preparation_jobs as jobs
    module=importlib.import_module("corpus_ingest_core."+module_name)
    monkeypatch.undo()
    # Reinstall only owned metadata/configuration; retain the real acquisition.
    from corpus_ingest_core import config
    monkeypatch.setattr(config,"DEFAULT_CONFIG_PATH",configured_source/"profiles.yaml")
    for name,value in vars(storage).copy().items():
        if name=="DATA_DIR":monkeypatch.setattr(storage,name,configured_source)
        elif name.isupper() and name.endswith("_DIR") and isinstance(value,Path):
            monkeypatch.setattr(storage,name,configured_source/value.name)
    monkeypatch.setattr(module,"_resolve_metadata",lambda _:dict(title="Demo",uploader_id="@demo",upload_date="20261001"))
    monkeypatch.setattr(module,"load_podcast_profile",lambda pod:config.load_podcast_profile(pod,config.DEFAULT_CONFIG_PATH))
    job=submit(monkeypatch,url)
    monkeypatch.setattr(module,"_download_video",lambda *args:configured_source/"owned-video")
    def failed_extract(video,partial):
        partial.write_bytes(b"owned partial audio")
        raise OSError("owned extraction failure")
    monkeypatch.setattr(module,"_extract_audio",failed_extract)
    assert worker().run_worker(job["job_id"])==1
    audio=storage.audio_asset_path(podcast_id,episode_ref,"Demo",".wav")
    assert audio.with_suffix(".wav.part").read_bytes()==b"owned partial audio"
    assert jobs.inspect(job["job_id"])["status"]=="attention_required"


@pytest.mark.parametrize("role",["seed","transcript","report"])
def test_actual_publication_failure_keeps_remaining_staging(configured_source,monkeypatch,role):
    from corpus_ingest_core import storage,x_video_ingest,transcriber,source_preparation_jobs as jobs
    job=submit(monkeypatch)
    fake_media(monkeypatch,x_video_ingest)
    seed=storage.corpus_episode_seed_asset_path("x-demo","123456789")
    transcript_paths=storage.transcript_asset_paths("x-demo","123456789","Demo")
    reports=storage.x_video_ingest_run_asset_paths("x-demo","123456789")
    failure_target={"seed":seed,"transcript":transcript_paths.text_path,"report":reports.markdown_path}[role]
    if role=="transcript":
        def real_publication(podcast_id,episode_ref,**kwargs):
            audio=SimpleNamespace(podcast_id=podcast_id,episode_ref=episode_ref,title="Demo",local_path=Path(kwargs["audio_path"]))
            transcriber._write_transcript_outputs(paths=transcript_paths,audio_asset=audio,model_name="owned",language="en",device="cpu",compute_type="int8",vad_filter=False,segments=[dict(start=0,end=1,text="owned")],completed=True)
        monkeypatch.setattr(x_video_ingest,"transcribe_episode",real_publication)
    original=Path.replace
    def refused(path,target):
        if Path(target)==failure_target:raise OSError("owned publication failure")
        return original(path,target)
    monkeypatch.setattr(Path,"replace",refused)
    assert worker().run_worker(job["job_id"])==1
    assert failure_target.with_name(failure_target.name+".part").is_file()
    assert jobs.inspect(job["job_id"])["status"]=="attention_required"


def process_helpers(root):
    """Owned test programs; production exposes no fake mode or executable input."""
    worker_script = root / "owned_worker.py"
    worker_script.write_text('''import json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
from corpus_ingest_core import storage,x_video_ingest,youtube_video_ingest
from corpus_ingest_core.source_preparation_worker import run_worker
root=storage.DATA_DIR
for module in (x_video_ingest,youtube_video_ingest):
    module._resolve_metadata=lambda _:dict(title="Demo",uploader_id="@demo",upload_date="20261001")
def acquire(url,target,work_dir):
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(b"owned audio")
    (root/"worker-entered").write_text(json.dumps(dict(pid=os.getpid(),job_id=sys.argv[1])))
    deadline=time.monotonic()+30
    while not (root/"worker-gate").exists():
        if time.monotonic()>deadline:raise RuntimeError("owned gate expired")
        time.sleep(.02)
def transcribe(podcast_id,episode_ref,**kwargs):
    assert kwargs["force"] is False
    paths=storage.transcript_asset_paths(podcast_id,episode_ref,kwargs["title"])
    paths.json_path.parent.mkdir(parents=True,exist_ok=True)
    paths.text_path.write_text("owned fixture",encoding="utf-8")
    paths.srt_path.write_text("1\\n00:00:00,000 --> 00:00:01,000\\nowned fixture\\n",encoding="utf-8")
    paths.json_path.write_text(json.dumps(dict(podcast_id=podcast_id,episode_ref=episode_ref,title=kwargs["title"],completed=True,segment_count=1,segments=[dict(id=0,start=0,end=1,text="owned fixture")],**{key:kwargs[key] for key in ("model","device","compute_type","vad_filter")})),encoding="utf-8")
    return SimpleNamespace(json_path=paths.json_path)
for module in (x_video_ingest,youtube_video_ingest):
    module._acquire_audio=acquire
    module.transcribe_episode=transcribe
raise SystemExit(run_worker(sys.argv[1]))
''',encoding="utf-8")
    setup = '''import json,sys
from pathlib import Path
from corpus_ingest_core import storage,x_video_ingest,youtube_video_ingest,source_preparation as core
for module in (x_video_ingest,youtube_video_ingest):
    module._resolve_metadata=lambda _:dict(title="Demo",uploader_id="@demo",upload_date="20261001")
real_popen=core.subprocess.Popen
def owned_popen(command,**kwargs):
    command=[command[0],str(storage.DATA_DIR/"owned_worker.py"),command[2]]
    with (storage.DATA_DIR/"owned-worker-errors.txt").open("ab") as diagnostics:
        kwargs["stderr"]=diagnostics
        return real_popen(command,**kwargs)
core.subprocess.Popen=owned_popen
'''
    client_script=root/"owned_client.py"
    client_script.write_text(setup+'''url="https://x.com/demo/status/123456789"
plan=core.prepare_learning_source(url)
response=core.prepare_learning_source(url,confirm=True,expected_plan_id=plan["plan_id"])
print(json.dumps(dict(job_id=response["job_id"])))
''',encoding="utf-8")
    server_script=root/"owned_server.py"
    server_script.write_text('from corpus_ingest_core import mcp_server\n'+setup+'''
original_flags=core._worker_flags
def observed_flags():
    (storage.DATA_DIR/"owned-policy.json").write_text(json.dumps(dict(limits=core._windows_job_limits() if sys.platform=="win32" else None)))
    return original_flags()
core._worker_flags=observed_flags
mcp_server.run()
''',encoding="utf-8")
    environment=os.environ.copy()
    environment.update(CORPUS_INGEST_DATA_DIR=str(root.absolute()),CORPUS_INGEST_CONFIG=str((root/"profiles.yaml").absolute()),
                       PYTHONPATH=str(Path(__file__).resolve().parents[1]/"src"))
    return client_script,server_script,environment


def wait_for_entered(root,timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        path=root/"worker-entered"
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (ValueError,OSError):
                pass
        time.sleep(.02)
    pytest.fail("owned worker never entered acquisition")


def test_real_owned_worker_survives_submitter_exit(configured_source):
    from corpus_ingest_core import source_preparation_jobs as jobs
    client,_,environment=process_helpers(configured_source)
    try:
        submitted=subprocess.run([sys.executable,str(client)],env=environment,capture_output=True,text=True,timeout=20)
        assert submitted.returncode==0,submitted.stderr
        job_id=json.loads(submitted.stdout)["job_id"]
        entered=wait_for_entered(configured_source)
        assert entered["job_id"]==job_id
        assert jobs.inspect(job_id)["status"]=="downloading"
        assert jobs.load(job_id)["worker_pid"]==entered["pid"]
        (configured_source/"worker-gate").write_text("continue")
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and jobs.inspect(job_id)["status"] in jobs.ACTIVE:
            time.sleep(.02)
        assert jobs.inspect(job_id)["transcript_ready"] is True
        assert jobs.active_job() is None
    finally:
        (configured_source/"worker-gate").write_text("stop waiting")


def test_owned_worker_interruption_retains_artifacts_and_slot(configured_source,monkeypatch):
    import signal
    from datetime import datetime,timedelta
    from corpus_ingest_core import storage,source_preparation_jobs as jobs
    client,_,environment=process_helpers(configured_source)
    try:
        submitted=subprocess.run([sys.executable,str(client)],env=environment,capture_output=True,text=True,timeout=20)
        assert submitted.returncode==0,submitted.stderr
        job_id=json.loads(submitted.stdout)["job_id"]
        entered=wait_for_entered(configured_source)
        job=jobs.load(job_id)
        assert job["worker_pid"]==entered["pid"] and entered["job_id"]==job_id
        os.kill(entered["pid"],signal.SIGTERM)
        monkeypatch.setattr(jobs,"utc_now",lambda:datetime.fromisoformat(job["heartbeat_at"])+timedelta(seconds=121))
        status=jobs.inspect(job_id)
        assert status["status"]=="attention_required" and status["reason"]=="worker_unconfirmed"
        assert jobs.active_job()["job_id"]==job_id
        assert storage.audio_asset_path("x-demo","123456789","Demo",".wav").read_bytes()==b"owned audio"
    finally:
        (configured_source/"worker-gate").write_text("stop waiting")


@pytest.mark.parametrize("url,module_name", [(URL,"x_video_ingest"),(YT_URL,"youtube_video_ingest")])
def test_executor_title_drift_preserves_approved_artifact_names(configured_source,monkeypatch,url,module_name):
    from corpus_ingest_core import source_preparation_jobs as jobs
    module=__import__("corpus_ingest_core."+module_name,fromlist=[module_name])
    job=submit(monkeypatch,url)
    calls=fake_media(monkeypatch,module)
    resolved=[]
    def metadata(_):
        resolved.append(True)
        return dict(title="Demo" if len(resolved)==1 else "Changed title",uploader_id="@demo",upload_date="20261001",duration=1)
    monkeypatch.setattr(module,"_resolve_metadata",metadata)
    assert worker().run_worker(job["job_id"])==0
    assert len(resolved)==2 and calls==["download","transcribe"]
    status=jobs.inspect(job["job_id"])
    assert status["transcript_ready"] and status["reason"]=="validated"
    assert jobs.active_job() is None
    from corpus_ingest_core import storage
    record=jobs.load(job["job_id"])
    paths=storage.transcript_asset_paths(record["podcast_id"],record["episode_ref"],"Demo")
    assert all(path.is_file() for path in (paths.text_path,paths.srt_path,paths.json_path))
    assert json.loads(paths.json_path.read_text(encoding="utf-8"))["title"]=="Demo"
    for role in ("audio","corpus","transcripts","reports"):
        for artifact in (configured_source/role).rglob("*"):
            if artifact.is_file():
                assert str(artifact) in record["plan"]["writes"]
