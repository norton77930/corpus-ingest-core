"""Durable admission and read-only observation with owned stores."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest


def plan(source="123456789", binding="a" * 64):
    return dict(source_type="x-video", canonical_url=f"https://x.com/demo/status/{source}",
                podcast_id="x-demo", episode_ref=source, title="Demo", plan_id=binding,
                context_digest="b" * 64, status="action_available", stages=["downloading", "transcribing", "validating"],
                reads=[], writes=[], reuses=[], artifact_state=[])


def ledger():
    from corpus_ingest_core import source_preparation_jobs
    return source_preparation_jobs


def test_missing_store_is_observed_without_creation(tmp_data_dirs):
    jobs = ledger()
    assert jobs.load("a" * 32) is None
    assert jobs.active_job() is None
    assert not (tmp_data_dirs / "preparation-jobs").exists()


def test_empty_initialization_reservation_coalesces_across_processes(tmp_data_dirs):
    import os,subprocess,sys
    from pathlib import Path
    directory=tmp_data_dirs/"preparation-jobs"
    directory.mkdir()
    # This is the exact O_EXCL reservation another first writer can observe.
    (directory/"jobs.sqlite3").write_bytes(b"")
    script=tmp_data_dirs/"owned_admission.py"
    script.write_text("import json\nfrom corpus_ingest_core import source_preparation_jobs as j\np="+repr(plan())+"\njob,created=j.admit(p)\nprint(json.dumps(dict(job_id=job['job_id'],created=created)))\n",encoding="utf-8")
    environment=os.environ.copy()
    environment["CORPUS_INGEST_DATA_DIR"]=str(tmp_data_dirs)
    environment["PYTHONPATH"]=str(Path(__file__).resolve().parents[1]/"src")
    processes=[subprocess.Popen([sys.executable,str(script)],env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
    results=[]
    for process in processes:
        stdout,stderr=process.communicate(timeout=20)
        assert process.returncode==0,stderr
        results.append(json.loads(stdout))
    assert len({r["job_id"] for r in results})==1
    assert sum(r["created"] for r in results)==1


def test_atomic_duplicate_admission_and_other_source_busy(tmp_data_dirs):
    jobs = ledger()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: jobs.admit(plan()), range(8)))
    assert len({job["job_id"] for job, _ in results}) == 1
    assert sum(created for _, created in results) == 1
    with pytest.raises(jobs.PreparationError, match="busy"):
        jobs.admit(plan("987654321"))
    with pytest.raises(jobs.PreparationError, match="plan_changed"):
        jobs.admit(plan(binding="c" * 64))


@pytest.mark.parametrize("job_id", ["../jobs", "a" * 33, "A" * 32, "", None, 123])
def test_hostile_job_refs_do_not_open_or_create_store(tmp_data_dirs, job_id):
    jobs = ledger()
    with pytest.raises(jobs.PreparationError, match="invalid_request"):
        jobs.load(job_id)
    assert not (tmp_data_dirs / "preparation-jobs").exists()


def test_store_directory_file_and_sidecar_are_refused(tmp_data_dirs):
    jobs = ledger()
    directory = tmp_data_dirs / "preparation-jobs"
    directory.mkdir()
    db = directory / "jobs.sqlite3"
    db.mkdir()
    with pytest.raises(jobs.PreparationError, match="store_unavailable"):
        jobs.load("a" * 32)
    db.rmdir()
    job, _ = jobs.admit(plan())
    sidecar = directory / "jobs.sqlite3-wal"
    sidecar.mkdir()
    with pytest.raises(jobs.PreparationError, match="store_unavailable"):
        jobs.load(job["job_id"])


def test_readonly_status_refuses_noncanonical_wal_store(tmp_data_dirs):
    jobs=ledger()
    job,_=jobs.admit(plan())
    path=tmp_data_dirs/"preparation-jobs/jobs.sqlite3"
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]=="wal"
    before={p.name:p.read_bytes() for p in path.parent.iterdir() if p.is_file()}
    result=jobs.inspect(job["job_id"])
    assert result["status"]=="attention_required" and result["reason"]=="store_unavailable"
    assert {p.name:p.read_bytes() for p in path.parent.iterdir() if p.is_file()}==before


def test_capacity_retains_history_without_purge(tmp_data_dirs, monkeypatch):
    jobs = ledger()
    monkeypatch.setattr(jobs, "MAX_JOBS", 1)
    job, _ = jobs.admit(plan())
    jobs.refuse_launch(job["job_id"])
    with pytest.raises(jobs.PreparationError, match="capacity_exceeded"):
        jobs.admit(plan("987654321"))
    assert jobs.load(job["job_id"])["reason"] == "launch_failed"


def test_only_one_claim_and_owner_can_update(tmp_data_dirs):
    jobs = ledger()
    job, _ = jobs.admit(plan())
    owned = jobs.claim(job["job_id"])
    with pytest.raises(jobs.PreparationError, match="owner_unavailable"):
        jobs.claim(job["job_id"])
    with pytest.raises(jobs.PreparationError, match="owner_unavailable"):
        jobs.update(job["job_id"], "wrong", status="transcribing")
    jobs.update(job["job_id"], owned["owner_token"], status="transcribing")
    assert jobs.load(job["job_id"])["slot_state"] == "active"


def test_unknown_launch_retains_slot_and_record(tmp_data_dirs):
    jobs = ledger()
    job, _ = jobs.admit(plan())
    jobs.uncertain_launch(job["job_id"])
    assert jobs.load(job["job_id"])["status"] == "attention_required"
    with pytest.raises(jobs.PreparationError, match="busy"):
        jobs.admit(plan("987654321"))


def test_corrupt_schema_and_record_are_not_absence(tmp_data_dirs):
    jobs = ledger()
    job, _ = jobs.admit(plan())
    with sqlite3.connect(tmp_data_dirs / "preparation-jobs/jobs.sqlite3") as connection:
        connection.execute("UPDATE jobs SET payload = ?", (json.dumps({"job_id": job["job_id"]}),))
    with pytest.raises(jobs.PreparationError, match="store_unavailable"):
        jobs.load(job["job_id"])


def test_status_is_offline_readonly_and_stale_does_not_release(tmp_data_dirs, monkeypatch):
    jobs = ledger()
    job, _ = jobs.admit(plan())
    now = datetime.now(UTC)
    monkeypatch.setattr(jobs, "utc_now", lambda: now + timedelta(seconds=121))
    db = tmp_data_dirs / "preparation-jobs/jobs.sqlite3"
    before = db.read_bytes()
    status = jobs.inspect(job["job_id"])
    assert status["status"] == "attention_required"
    assert status["reason"] == "worker_unconfirmed"
    assert status["read_only"] is True and status["network_access"] is False
    assert status["study_guide_ready"] is False
    assert db.read_bytes() == before
    assert jobs.active_job()["slot_state"] == "reserved"
    assert jobs.inspect("f" * 32)["reason"] == "not_found"


def test_injected_reparse_store_is_rejected(tmp_data_dirs, monkeypatch):
    jobs = ledger()
    job, _ = jobs.admit(plan())
    monkeypatch.setattr(jobs, "is_redirect", lambda info: True)
    with pytest.raises(jobs.PreparationError, match="store_unavailable"):
        jobs.load(job["job_id"])


@pytest.mark.parametrize("mutation", [{"schema_version":True}, {"status":"transcript_ready","readiness_verified_at":"2026-10-01T00:00:00+00:00"}])
def test_malformed_terminal_metadata_never_claims_ready(tmp_data_dirs, mutation):
    jobs=ledger()
    job,_=jobs.admit(plan())
    job.update(mutation)
    with sqlite3.connect(tmp_data_dirs / "preparation-jobs/jobs.sqlite3") as connection:
        connection.execute("UPDATE jobs SET payload=?",(json.dumps(job),))
    with pytest.raises(jobs.PreparationError,match="store_unavailable"):
        jobs.load(job["job_id"])


def test_status_store_failure_is_bounded_attention_without_writes(tmp_data_dirs):
    jobs=ledger()
    directory=tmp_data_dirs / "preparation-jobs"
    directory.mkdir()
    db=directory / "jobs.sqlite3"
    db.write_bytes(b"not a database")
    before=db.read_bytes()
    status=jobs.inspect("a"*32)
    assert status["status"]=="attention_required" and status["reason"]=="store_unavailable"
    assert status["read_only"] and not status["network_access"]
    assert db.read_bytes()==before


def test_clock_ambiguity_also_blocks_terminal_readiness(tmp_data_dirs,monkeypatch):
    jobs=ledger()
    job,_=jobs.admit(plan())
    owned=jobs.claim(job["job_id"])
    jobs.update(job["job_id"],owned["owner_token"],status="validating")
    jobs.update(job["job_id"],owned["owner_token"],status="transcript_ready",release=True)
    monkeypatch.setattr(jobs,"utc_now",lambda:datetime.fromisoformat(job["created_at"])-timedelta(seconds=1))
    status=jobs.inspect(job["job_id"])
    assert status["status"]=="attention_required" and not status["transcript_ready"]
