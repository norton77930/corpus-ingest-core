"""Approval, history and worker evidence for configured transcription."""
import json
import sqlite3
from types import SimpleNamespace

import pytest

from tests.test_source_preparation import configured_source, transcript, URL, YT_URL, core
from tests.test_source_preparation_worker import fake_media, submit, worker
from tests.test_source_preparation_jobs import plan as legacy_plan

DEFAULT = dict(model="tiny", device="cpu", compute_type="int8", vad_filter=True)
MEDIUM = dict(model="medium", device="cpu", compute_type="float32", vad_filter=True)


def configure(root, **options):
    import yaml
    path = root / "profiles.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for profile in data["podcasts"].values():
        profile["preparation_transcription"] = {k: options.get(k, MEDIUM[k]) for k in ("model", "device", "compute_type")}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_preview_discloses_default_without_writes(configured_source):
    before = snapshot(configured_source)
    result = core().prepare_learning_source(URL)
    assert result["transcription"] == DEFAULT and result["actual_transcription"] is None
    assert "model_download_possible" in result["warnings"]
    assert snapshot(configured_source) == before


def test_invalid_settings_are_finite_and_do_not_admit(configured_source):
    configure(configured_source, model="private/model")
    result = core().prepare_learning_source(URL)
    assert result["reason"] == "invalid_transcription_settings" and result["plan_id"] is None
    assert "private/model" not in json.dumps(result)
    assert not (configured_source / "preparation-jobs").exists()


def test_cuda_observation_blocks_without_model_loading_or_writes(configured_source, monkeypatch):
    from corpus_ingest_core import preparation_transcription as settings
    configure(configured_source, device="cuda", compute_type="float16")
    monkeypatch.setattr(settings.importlib, "import_module", lambda _: SimpleNamespace(get_cuda_device_count=lambda: 0))
    before = snapshot(configured_source)
    result = core().prepare_learning_source(URL)
    assert result["reason"] == "transcription_runtime_unavailable" and result["transcription"]["model"] == "medium"
    assert result["plan_id"] is None and snapshot(configured_source) == before


@pytest.mark.parametrize("metadata,title", [(None,"Demo"),(DEFAULT,"Old title"),(MEDIUM,"Demo")])
def test_existing_transcript_uses_recorded_selected_metadata_without_gpu_probe(configured_source, monkeypatch, metadata, title):
    from corpus_ingest_core import preparation_transcription as settings
    configure(configured_source, device="cuda", compute_type="float16")
    monkeypatch.setattr(settings, "runtime_available", lambda _: pytest.fail("ready transcript must not probe hardware"))
    paths = transcript(title=title)
    if metadata:
        payload = json.loads(paths.json_path.read_text())
        paths.json_path.write_text(json.dumps({**payload, **metadata}))
    before = snapshot(configured_source)
    result = core().prepare_learning_source(URL)
    assert result["transcript_ready"] and result["plan_id"] is None and result["actual_transcription"] == metadata
    assert ("existing_transcription_unknown" if metadata is None else "existing_transcription_differs") in result["warnings"]
    assert snapshot(configured_source) == before


@pytest.mark.parametrize("options", [dict(model="base"),dict(device="cuda",compute_type="int8"),dict(compute_type="float32")])
@pytest.mark.parametrize("admitted", [False,True])
def test_settings_drift_invalidates_confirm_and_active_reuse(configured_source, monkeypatch, options, admitted):
    from corpus_ingest_core import preparation_transcription as settings
    monkeypatch.setattr(settings, "runtime_available", lambda _: True)
    source = core()
    launches = []
    monkeypatch.setattr(source, "launch_worker", lambda job: launches.append(job["job_id"]))
    original = source.prepare_learning_source(URL)
    if admitted:
        source.prepare_learning_source(URL, confirm=True, expected_plan_id=original["plan_id"])
    configure(configured_source, **{**DEFAULT, **options})
    before = snapshot(configured_source)
    with pytest.raises(source.PreparationError, match="plan_changed"):
        source.prepare_learning_source(URL, confirm=True, expected_plan_id=original["plan_id"])
    assert snapshot(configured_source) == before and len(launches) == int(admitted)


def test_new_job_persists_settings_and_readonly_status(configured_source, monkeypatch):
    from corpus_ingest_core import source_preparation_jobs as jobs
    configure(configured_source)
    accepted = submit(monkeypatch)
    job = jobs.load(accepted["job_id"])
    assert job["schema_version"] == 2 and job["plan"]["transcription"] == MEDIUM
    assert job["actual_transcription"] is None and accepted["transcription"] == MEDIUM
    before = snapshot(configured_source)
    assert jobs.inspect(job["job_id"])["transcription"] == MEDIUM
    assert snapshot(configured_source) == before
    with sqlite3.connect(configured_source / "preparation-jobs/jobs.sqlite3") as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1


@pytest.mark.parametrize("url,module_name", [(URL,"x_video_ingest"),(YT_URL,"youtube_video_ingest")])
def test_both_workers_forward_persisted_settings_and_record_actual(configured_source, monkeypatch, url, module_name):
    from corpus_ingest_core import source_preparation_jobs as jobs
    configure(configured_source)
    module = __import__("corpus_ingest_core." + module_name, fromlist=[module_name])
    accepted = submit(monkeypatch, url)
    calls = fake_media(monkeypatch, module)
    recorded = []
    def transcribe(podcast_id, episode_ref, **options):
        recorded.append({k: options[k] for k in ("model","device","compute_type","vad_filter")})
        paths = transcript(podcast_id=podcast_id, episode_ref=episode_ref, title=options["title"])
        payload = json.loads(paths.json_path.read_text())
        paths.json_path.write_text(json.dumps({**payload, **recorded[-1]}))
        return SimpleNamespace(json_path=paths.json_path)
    monkeypatch.setattr(module, "transcribe_episode", transcribe)
    assert worker().run_worker(accepted["job_id"]) == 0
    assert recorded == [MEDIUM] and calls == ["download"]
    result = jobs.inspect(accepted["job_id"])
    assert result["actual_transcription"] == MEDIUM and result["transcription"] == MEDIUM and result["transcript_ready"]


@pytest.mark.parametrize("defect", ["model", "device", "compute_type", "vad_filter", "missing"])
def test_worker_cannot_claim_ready_for_wrong_or_unknown_actual_settings(configured_source, monkeypatch, defect):
    from corpus_ingest_core import x_video_ingest, source_preparation_jobs as jobs
    configure(configured_source)
    accepted = submit(monkeypatch)
    fake_media(monkeypatch, x_video_ingest)
    def transcribe(podcast_id, episode_ref, **options):
        paths = transcript(podcast_id=podcast_id, episode_ref=episode_ref, title=options["title"])
        metadata = dict(MEDIUM)
        if defect == "missing":
            metadata = {}
        else:
            metadata[defect] = {"model":"tiny", "device":"cuda", "compute_type":"int8", "vad_filter":False}[defect]
        paths.json_path.write_text(json.dumps({**json.loads(paths.json_path.read_text()), **metadata}))
        return SimpleNamespace(json_path=paths.json_path)
    monkeypatch.setattr(x_video_ingest, "transcribe_episode", transcribe)
    assert worker().run_worker(accepted["job_id"]) == 1
    result = jobs.inspect(accepted["job_id"])
    assert result["reason"] == "validation_failed" and not result["transcript_ready"]
    assert result["actual_transcription"] is None and jobs.active_job() is not None


def test_worker_hardware_loss_refuses_before_media(configured_source, monkeypatch):
    from corpus_ingest_core import preparation_transcription as settings, x_video_ingest, source_preparation_jobs as jobs
    configure(configured_source, device="cuda", compute_type="float16")
    monkeypatch.setattr(settings,"runtime_available",lambda _: True)
    accepted = submit(monkeypatch)
    monkeypatch.setattr(settings,"runtime_available",lambda _: False)
    calls = fake_media(monkeypatch,x_video_ingest)
    assert worker().run_worker(accepted["job_id"]) == 1
    assert calls == [] and jobs.active_job() is None
    assert jobs.inspect(accepted["job_id"])["reason"] == "transcription_runtime_unavailable"


def test_legacy_inspection_keeps_unknown_metadata_and_original_bytes(tmp_data_dirs):
    from corpus_ingest_core import source_preparation_jobs as jobs
    job, _ = jobs.admit(legacy_plan())
    before = snapshot(tmp_data_dirs)
    result = jobs.inspect(job["job_id"])
    assert result["transcription"] is None and result["actual_transcription"] is None
    assert jobs.load(job["job_id"])["schema_version"] == 1 and snapshot(tmp_data_dirs) == before


@pytest.mark.parametrize("defect", ["tuple", "valid_tuple_mutation", "actual", "version"])
def test_v2_corruption_is_unavailable_and_not_repaired(configured_source, monkeypatch, defect):
    from corpus_ingest_core import source_preparation_jobs as jobs
    accepted = submit(monkeypatch)
    path = configured_source / "preparation-jobs/jobs.sqlite3"
    with sqlite3.connect(path) as db:
        job = json.loads(db.execute("SELECT payload FROM jobs").fetchone()[0])
        if defect == "tuple":
            job["plan"].pop("transcription")
        elif defect == "valid_tuple_mutation":
            job["plan"]["transcription"]["model"] = "medium"
        elif defect == "actual":
            job["actual_transcription"] = DEFAULT
        else:
            job["schema_version"] = 1
        db.execute("UPDATE jobs SET payload=?", (json.dumps(job),))
    before = snapshot(configured_source)
    assert jobs.inspect(accepted["job_id"])["reason"] == "store_unavailable"
    assert snapshot(configured_source) == before


@pytest.mark.parametrize("options", [dict(model="base"),dict(device="cuda",compute_type="int8"),dict(compute_type="float32")])
def test_worker_settings_drift_after_admission_has_no_media(configured_source, monkeypatch, options):
    from corpus_ingest_core import preparation_transcription as settings, x_video_ingest, source_preparation_jobs as jobs
    monkeypatch.setattr(settings,"runtime_available",lambda _: True)
    accepted = submit(monkeypatch)
    configure(configured_source, **{**DEFAULT, **options})
    calls = fake_media(monkeypatch,x_video_ingest)
    assert worker().run_worker(accepted["job_id"]) == 1 and calls == []
    assert jobs.inspect(accepted["job_id"])["reason"] == "plan_changed"


@pytest.mark.parametrize("configured", [False, True])
def test_legacy_queued_worker_is_allowed_only_without_new_mapping(configured_source, monkeypatch, configured):
    from corpus_ingest_core import source_preparation_jobs as jobs, x_video_ingest
    source = core()
    old = source._preview(URL, legacy=True)
    old.pop("transcription")
    job, _ = jobs.admit(old)
    assert job["schema_version"] == 1
    if configured:
        configure(configured_source)
    calls = fake_media(monkeypatch, x_video_ingest)
    assert worker().run_worker(job["job_id"]) == int(configured)
    status = jobs.inspect(job["job_id"])
    assert status["transcription"] is None and status["actual_transcription"] is None
    assert calls == ([] if configured else ["download", "transcribe"])
    assert status["reason"] == ("plan_changed" if configured else "validated")


def test_model_load_failure_retains_failure_without_downgrade_or_retry(configured_source, monkeypatch):
    from corpus_ingest_core import source_preparation_jobs as jobs, x_video_ingest
    configure(configured_source)
    job = submit(monkeypatch)
    fake_media(monkeypatch, x_video_ingest)
    calls = []
    def refused(*args, **options):
        calls.append({k: options[k] for k in ("model", "device", "compute_type", "vad_filter")})
        raise RuntimeError("private GPU diagnostic")
    monkeypatch.setattr(x_video_ingest, "transcribe_episode", refused)
    assert worker().run_worker(job["job_id"]) == 1 and calls == [MEDIUM]
    result = jobs.inspect(job["job_id"])
    assert result["status"] == "attention_required" and not result["transcript_ready"]
    assert jobs.active_job() is not None and "private GPU" not in json.dumps(result)


def test_ready_old_title_transcript_and_retained_audio_stay_reusable(configured_source):
    from corpus_ingest_core import storage
    configure(configured_source)
    paths = transcript(title="Old title")
    paths.json_path.write_text(json.dumps({**json.loads(paths.json_path.read_text()), **DEFAULT}))
    audio = storage.audio_asset_path("x-demo", "123456789", "Old title", ".wav")
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"retained owned WAV")
    before = snapshot(configured_source)
    result = core().prepare_learning_source(URL)
    assert result["status"] == "transcript_ready" and result["actual_transcription"] == DEFAULT
    assert result["writes"] == [] and snapshot(configured_source) == before
