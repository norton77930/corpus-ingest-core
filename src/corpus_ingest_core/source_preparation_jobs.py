"""Bounded operational jobs; never the transcript search cache."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
import json
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
import uuid

from . import storage
from . import preparation_transcription as transcription
from .errors import PodcastIngestCoreError

MAX_JOBS = 1024
MAX_RECORD_BYTES = 64 * 1024
MAX_STORE_BYTES = 80 * 1024 * 1024
HEARTBEAT_SECONDS = 30
STALE_SECONDS = 120
ACTIVE = frozenset({"queued", "downloading", "transcribing", "validating"})
STATES = ACTIVE | {"transcript_ready", "failed", "attention_required"}
REASONS = frozenset({"accepted", "processing", "validated", "launch_failed", "outcome_unconfirmed",
                     "worker_unconfirmed", "execution_failed", "validation_failed", "plan_changed", "transcription_runtime_unavailable"})
_WRITE_LOCK = threading.RLock()
_PLAN_KEYS = ("source_type", "canonical_url", "podcast_id", "episode_ref", "title", "plan_id",
              "context_digest", "stages", "reads", "writes", "reuses", "artifact_state")
_JOB_KEYS = {"job_id", "schema_version", "plan", "source_type", "canonical_url", "podcast_id", "episode_ref",
             "approved_plan_id", "context_digest", "created_at", "updated_at", "heartbeat_at", "readiness_verified_at",
             "owner_token", "worker_pid", "status", "stage", "reason", "slot_state"}


def plan_digest(plan: dict) -> str:
    keys = ("source_type", "canonical_url", "podcast_id", "episode_ref", "title", "context_digest", "stages", "writes", "reuses", "artifact_state")
    if "transcription" in plan:
        keys += ("transcription",)
    return hashlib.sha256(json.dumps({key: plan[key] for key in keys}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class PreparationError(PodcastIngestCoreError):
    """Only a finite public reason; exception details never enter responses."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def utc_now() -> datetime:
    return datetime.now(UTC)


def _time() -> str:
    return utc_now().isoformat()


def validate_job_id(value) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
        raise PreparationError("invalid_request")
    return value


def is_redirect(info) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def safe_path(path: Path, *, directory: bool = False) -> os.stat_result | None:
    """Check every lexical ancestor, including missing managed directories."""
    root = Path(os.path.abspath(storage.DATA_DIR))
    target = Path(os.path.abspath(path))
    if not target.is_relative_to(root):
        raise PreparationError("unsafe_path")
    try:
        for parent in reversed(target.parents):
            try:
                info = parent.lstat()
            except FileNotFoundError:
                continue
            if is_redirect(info) or not stat.S_ISDIR(info.st_mode):
                raise PreparationError("unsafe_path")
        try:
            info = target.lstat()
        except FileNotFoundError:
            return None
        if is_redirect(info) or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
            raise PreparationError("unsafe_path")
        if not directory and info.st_nlink != 1:
            raise PreparationError("unsafe_path")
        return info
    except OSError:
        raise PreparationError("inspection_unavailable") from None


def _store_path() -> Path:
    path = storage.PREPARATION_JOBS_DIR / "jobs.sqlite3"
    try:
        safe_path(storage.PREPARATION_JOBS_DIR, directory=True)
        for suffix in ("", "-journal", "-wal", "-shm"):
            info = safe_path(Path(str(path) + suffix))
            if info and info.st_size > MAX_STORE_BYTES:
                raise PreparationError("store_unavailable")
            if info is not None and suffix in {"-wal","-shm"}:
                raise PreparationError("store_unavailable")
            if info is not None and suffix=="" and info.st_size:
                descriptor=os.open(path,os.O_RDONLY | getattr(os,"O_BINARY",0) | getattr(os,"O_NOFOLLOW",0))
                try:
                    opened=os.fstat(descriptor)
                    if is_redirect(opened) or not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or (opened.st_dev,opened.st_ino)!=(info.st_dev,info.st_ino):
                        raise PreparationError("store_unavailable")
                    header=os.read(descriptor,20)
                    if header.startswith(b"SQLite format 3\x00") and header[18:20]!=b"\x01\x01":
                        # WAL readers may create shared-memory sidecars even in
                        # mode=ro. Our ledger uses rollback journaling only.
                        raise PreparationError("store_unavailable")
                finally:
                    os.close(descriptor)
    except (PreparationError,OSError):
        raise PreparationError("store_unavailable") from None
    return path


@contextmanager
def _connection(*, write: bool = False):
    connection = None
    try:
        path = _store_path()
        created = False
        if not path.exists():
            if not write:
                yield None
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            _store_path()
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                os.close(descriptor)
                created = True
        before = path.lstat()
        connection = sqlite3.connect(path.absolute().as_uri() + ("?mode=rw" if write else "?mode=ro"),
                                     uri=True, timeout=1.0)
        connection.execute("PRAGMA trusted_schema=OFF")
        if write:
            connection.execute("BEGIN IMMEDIATE")
        else:
            connection.execute("PRAGMA query_only=ON")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if not write and version==0 and before.st_size==0:
            # An empty O_EXCL reservation has no recorded jobs yet. Observation
            # never initializes it; approved admission serializes initialization.
            yield None
            return
        if version == 0 and write and (created or before.st_size == 0):
            if connection.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]:
                raise PreparationError("store_unavailable")
            connection.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, source_key TEXT NOT NULL, "
                               "plan_id TEXT NOT NULL, context_digest TEXT NOT NULL, payload TEXT NOT NULL, slot INTEGER UNIQUE)")
            connection.execute("PRAGMA user_version=1")
        elif version != 1:
            raise PreparationError("store_unavailable")
        if [row[1] for row in connection.execute("PRAGMA table_info(jobs)")] != ["job_id","source_key","plan_id","context_digest","payload","slot"]:
            raise PreparationError("store_unavailable")
        if connection.execute("SELECT count(*) FROM sqlite_master WHERE type IN ('trigger','view')").fetchone()[0]:
            raise PreparationError("store_unavailable")
        after = _store_path().lstat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise PreparationError("store_unavailable")
        yield connection
        _store_path()
        if write:
            connection.commit()
    except (OSError, sqlite3.Error, ValueError, TypeError):
        raise PreparationError("store_unavailable") from None
    finally:
        if connection is not None:
            connection.close()


def _validate_plan(plan: dict, *, version: int | None = None) -> dict:
    try:
        version = version if version is not None else (2 if "transcription" in plan else 1)
        if ("transcription" in plan) != (version == 2):
            raise ValueError
        result = {key: plan[key] for key in _PLAN_KEYS}
        if version == 2:
            result["transcription"] = transcription.parse(plan["transcription"], recorded=True).as_dict()
        result["warnings"]=plan.get("warnings",[])
        if not isinstance(result["warnings"],list) or len(result["warnings"])>4 or any(type(w) is not str or w not in {"manual_cache","learning_documents_not_evaluated","learning_profile_incompatible","model_download_possible","existing_transcription_unknown","existing_transcription_differs"} for w in result["warnings"]):
            raise ValueError
        storage._safe_slug(result["podcast_id"], "podcast_id")
        storage._safe_episode_ref(result["episode_ref"])
        if result["source_type"] not in {"yt-video", "x-video"}:
            raise ValueError
        for key in ("plan_id", "context_digest"):
            if not isinstance(result[key], str) or not re.fullmatch(r"[a-f0-9]{64}", result[key]):
                raise ValueError
        if version == 2 and result["plan_id"] != plan_digest(result):
            raise ValueError
        if not isinstance(result["title"], str) or not 1 <= len(result["title"]) <= 512:
            raise ValueError
        if not isinstance(result["canonical_url"], str) or not result["canonical_url"].startswith("https://") or len(result["canonical_url"]) > 2048:
            raise ValueError
        for key in ("reads", "writes", "reuses"):
            if not isinstance(result[key], list) or len(result[key]) > 32 or any(not isinstance(s, str) or len(s) > 1024 for s in result[key]):
                raise ValueError
        if result["stages"] not in (["downloading", "transcribing", "validating"], ["transcribing", "validating"]):
            raise ValueError
        if not isinstance(result["artifact_state"], list) or len(result["artifact_state"]) > 32:
            raise ValueError
        if len(json.dumps(result).encode()) > MAX_RECORD_BYTES - 2048:
            raise ValueError
        return result
    except (KeyError, ValueError, TypeError, AttributeError, RecursionError):
        raise PreparationError("invalid_request") from None


def _decode(row) -> dict | None:
    if row is None:
        return None
    try:
        if len(row[4].encode()) > MAX_RECORD_BYTES:
            raise ValueError
        job = json.loads(row[4])
        if type(job.get("schema_version")) is not int or job["schema_version"] not in {1,2}:
            raise ValueError
        version = job["schema_version"]
        if set(job) != _JOB_KEYS | ({"actual_transcription"} if version == 2 else set()):
            raise ValueError
        if set(job["plan"]) != set(_PLAN_KEYS) | {"warnings"} | ({"transcription"} if version == 2 else set()):
            raise ValueError
        validate_job_id(job["job_id"])
        validate_job_id(job["owner_token"])
        plan = _validate_plan(job["plan"], version=version)
        if version == 2:
            if job["status"] == "transcript_ready":
                if transcription.parse(job["actual_transcription"], recorded=True).as_dict() != plan["transcription"]:
                    raise ValueError
            elif job["actual_transcription"] is not None:
                raise ValueError
        for key in ("source_type", "canonical_url", "podcast_id", "episode_ref", "context_digest"):
            if job[key] != plan[key]:
                raise ValueError
        if (job["job_id"], plan["source_type"] + ":" + plan["canonical_url"], plan["plan_id"], plan["context_digest"]) != tuple(row[:4]):
            raise ValueError
        if job["approved_plan_id"] != plan["plan_id"] or job["status"] not in STATES or job["stage"] not in ACTIVE or job["reason"] not in REASONS:
            raise ValueError
        if job["slot_state"] not in {"reserved", "active", "released"} or (row[5] == 1) != (job["slot_state"] != "released"):
            raise ValueError
        for key in ("created_at", "updated_at", "heartbeat_at", "readiness_verified_at"):
            if job[key] is None and key == "readiness_verified_at":
                continue
            if not isinstance(job[key], str) or len(job[key]) > 64 or datetime.fromisoformat(job[key]).utcoffset() is None:
                raise ValueError
        if (job["status"] == "transcript_ready") != (job["readiness_verified_at"] is not None):
            raise ValueError
        if job["status"] == "transcript_ready" and (job["stage"] != "validating" or job["slot_state"] != "released" or job["reason"] != "validated"):
            raise ValueError
        if job["worker_pid"] is not None and (type(job["worker_pid"]) is not int or job["worker_pid"] < 1):
            raise ValueError
        return job
    except (PreparationError, KeyError, ValueError, TypeError, AttributeError, RecursionError, IndexError):
        raise PreparationError("store_unavailable") from None


def _save(connection, job):
    raw = json.dumps(job, ensure_ascii=True, separators=(",", ":"))
    if len(raw.encode()) > MAX_RECORD_BYTES:
        raise PreparationError("store_unavailable")
    connection.execute("UPDATE jobs SET payload=?, slot=? WHERE job_id=?",
                       (raw, 1 if job["slot_state"] != "released" else None, job["job_id"]))


def load(job_id: str) -> dict | None:
    validate_job_id(job_id)
    with _connection() as connection:
        return None if connection is None else _decode(connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())


def active_job() -> dict | None:
    with _connection() as connection:
        return None if connection is None else _decode(connection.execute("SELECT * FROM jobs WHERE slot=1").fetchone())


def source_history(source_key: str) -> dict | None:
    with _connection() as connection:
        return None if connection is None else _decode(connection.execute("SELECT * FROM jobs WHERE source_key=? ORDER BY rowid DESC LIMIT 1", (source_key,)).fetchone())


def admit(plan: dict) -> tuple[dict, bool]:
    plan = _validate_plan(plan)
    source_key = plan["source_type"] + ":" + plan["canonical_url"]
    with _WRITE_LOCK, _connection(write=True) as connection:
        active = _decode(connection.execute("SELECT * FROM jobs WHERE slot=1").fetchone())
        if active is not None:
            if active["source_type"] + ":" + active["canonical_url"] != source_key:
                raise PreparationError("busy")
            if active["approved_plan_id"] != plan["plan_id"] or active["context_digest"] != plan["context_digest"]:
                raise PreparationError("plan_changed")
            if active["status"] not in ACTIVE:
                raise PreparationError("outcome_unconfirmed")
            return active, False
        if connection.execute("SELECT count(*) FROM jobs").fetchone()[0] >= MAX_JOBS:
            raise PreparationError("capacity_exceeded")
        timestamp = _time()
        job = dict(job_id=uuid.uuid4().hex, schema_version=2 if "transcription" in plan else 1, plan=plan, **{key: plan[key] for key in
                   ("source_type", "canonical_url", "podcast_id", "episode_ref", "context_digest")},
                   approved_plan_id=plan["plan_id"], created_at=timestamp, updated_at=timestamp, heartbeat_at=timestamp,
                   readiness_verified_at=None, owner_token=uuid.uuid4().hex, worker_pid=None, status="queued", stage="queued",
                   reason="accepted", slot_state="reserved")
        if job["schema_version"] == 2:
            job["actual_transcription"] = None
        connection.execute("INSERT INTO jobs VALUES (?,?,?,?,?,1)",
                           (job["job_id"], source_key, plan["plan_id"], plan["context_digest"], json.dumps(job)))
        return job, True


def claim(job_id: str) -> dict:
    validate_job_id(job_id)
    with _WRITE_LOCK, _connection(write=True) as connection:
        job = _decode(connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())
        if job is None or job["slot_state"] != "reserved" or job["status"] != "queued":
            raise PreparationError("owner_unavailable")
        job.update(slot_state="active", worker_pid=os.getpid(), updated_at=_time(), heartbeat_at=_time())
        _save(connection, job)
        return job


def update(job_id: str, owner_token: str, *, status: str | None = None, reason: str | None = None, release: bool = False, actual_transcription: dict | None = None) -> None:
    validate_job_id(job_id)
    with _WRITE_LOCK, _connection(write=True) as connection:
        job = _decode(connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())
        if job is None or job["owner_token"] != owner_token or job["slot_state"] != "active" or job["status"] not in ACTIVE:
            raise PreparationError("owner_unavailable")
        if job["schema_version"] == 2 and status == "transcript_ready":
            try:
                actual = transcription.parse(actual_transcription, recorded=True).as_dict()
            except transcription.InvalidTranscriptionSettings:
                raise PreparationError("invalid_request") from None
            if actual != job["plan"]["transcription"]:
                raise PreparationError("invalid_request")
            job["actual_transcription"] = actual
        elif actual_transcription is not None:
            raise PreparationError("invalid_request")
        if status is not None:
            order = ["queued", "downloading", "transcribing", "validating"]
            if status not in STATES or (status in ACTIVE and order.index(status) < order.index(job["stage"])):
                raise PreparationError("invalid_request")
            if status == "transcript_ready" and (job["stage"] != "validating" or not release):
                raise PreparationError("invalid_request")
            job["status"] = status
            if status in ACTIVE:
                job["stage"] = status
        if reason is not None and reason not in REASONS:
            raise PreparationError("invalid_request")
        job["reason"] = reason or ("validated" if status == "transcript_ready" else "processing")
        job.update(updated_at=_time(), heartbeat_at=_time())
        if status == "transcript_ready":
            job["readiness_verified_at"] = _time()
        if release:
            if job["status"] not in {"transcript_ready", "failed"}:
                raise PreparationError("invalid_request")
            job["slot_state"] = "released"
        _save(connection, job)


def _launch_outcome(job_id: str, *, uncertain: bool):
    validate_job_id(job_id)
    with _WRITE_LOCK, _connection(write=True) as connection:
        job = _decode(connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone())
        if job is None or job["slot_state"] != "reserved":
            raise PreparationError("outcome_unconfirmed")
        job.update(status="attention_required" if uncertain else "failed",
                   reason="outcome_unconfirmed" if uncertain else "launch_failed",
                   slot_state="reserved" if uncertain else "released", updated_at=_time())
        _save(connection, job)


def refuse_launch(job_id: str):
    _launch_outcome(job_id, uncertain=False)


def uncertain_launch(job_id: str):
    _launch_outcome(job_id, uncertain=True)


def inspect(job_id: str) -> dict:
    validate_job_id(job_id)
    result = dict(job_id=job_id, podcast_id=None, episode_ref=None, status="unknown", reason="not_found",
                  stage=None, created_at=None, last_observed_at=None, readiness_verified_at=None,
                  transcript_ready=False, study_guide_ready=False, read_only=True, network_access=False, warnings=[],transcription=None,actual_transcription=None)
    try:
        job = load(job_id)
    except PreparationError:
        result.update(status="attention_required",reason="store_unavailable")
        return result
    if job is None:
        return result
    result.update({key: job[key] for key in ("podcast_id", "episode_ref", "status", "reason", "stage", "created_at", "readiness_verified_at")})
    result.update(last_observed_at=job["heartbeat_at"], transcript_ready=job["status"] == "transcript_ready")
    result["warnings"]=list(job["plan"].get("warnings",[]))
    result.update(transcription=job["plan"].get("transcription"), actual_transcription=job.get("actual_transcription"))
    now = utc_now()
    age = (now - datetime.fromisoformat(job["heartbeat_at"])).total_seconds()
    ambiguous = any(datetime.fromisoformat(job[key]) > now for key in ("created_at","updated_at","heartbeat_at","readiness_verified_at") if job[key] is not None)
    if ambiguous or (job["status"] in ACTIVE and age > STALE_SECONDS):
        result.update(status="attention_required", reason="worker_unconfirmed",transcript_ready=False)
    return result
