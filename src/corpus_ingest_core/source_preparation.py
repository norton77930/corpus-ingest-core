"""Preview, bind and submit one source; media processing belongs to one worker."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import stat
import sys
from urllib.parse import urlparse

from . import config, storage, x_video_ingest, youtube_video_ingest
from . import source_preparation_jobs as jobs
from . import preparation_transcription as transcription
from .secure_local_snapshot import secure_directory_names, secure_read_bytes
from .validator import _normalize_segments

PreparationError = jobs.PreparationError
MAX_DIRECTORY_ENTRIES = 256
MAX_TRANSCRIPT_BYTES = 64 * 1024 * 1024
WARNINGS = ["manual_cache", "learning_documents_not_evaluated"]
_BLOCKERS = {"unsupported_source", "metadata_unavailable", "profile_missing", "source_type_mismatch", "unsafe_path",
             "inspection_unavailable", "partial_artifacts", "previous_outcome_unconfirmed", "store_unavailable", "capacity_exceeded", "worker_host_incompatible", "invalid_transcription_settings", "transcription_runtime_unavailable"}


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _absolute(path) -> Path:
    return Path(os.path.abspath(path))


def _source(url):
    if not isinstance(url, str) or not 1 <= len(url) <= 2048 or any(ord(c) < 32 for c in url):
        raise PreparationError("unsupported_source")
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password or parsed.port or parsed.fragment:
        raise PreparationError("unsupported_source")
    host = parsed.netloc.lower()
    if host in youtube_video_ingest._YOUTUBE_HOSTS:
        youtube_video_ingest.parse_youtube_video_id(url)
        return "yt-video", youtube_video_ingest
    if host in x_video_ingest._X_HOSTS and re.fullmatch(r"/[A-Za-z0-9_]{1,15}/status/[0-9]{1,30}/?", parsed.path):
        x_video_ingest.derive_identity(url)
        return "x-video", x_video_ingest
    raise PreparationError("unsupported_source")


def _resolve(url):
    try:
        source_type, module = _source(url)
    except (PreparationError, ValueError, TypeError):
        raise PreparationError("unsupported_source") from None
    try:
        canonical = module.canonical_watch_url(module.parse_youtube_video_id(url)) if source_type == "yt-video" else module.derive_identity(url).canonical_url
        info = module._resolve_metadata(canonical)
        if not isinstance(info, dict):
            raise ValueError
        identity = module.derive_youtube_identity(url, info) if source_type == "yt-video" else module.derive_identity(url)
        if source_type == "x-video":
            identity = module.derive_identity(identity.canonical_url.replace(identity.handle, identity.handle.lower(), 1))
        seed = module.build_seed(identity, info)
        if not isinstance(seed.title, str) or not 1 <= len(seed.title) <= 512:
            raise ValueError
        storage._safe_slug(identity.podcast_id, "podcast_id")
        storage._safe_episode_ref(identity.episode_ref)
        return source_type, module, identity, seed.title
    except Exception:
        raise PreparationError("metadata_unavailable") from None


def context_digest(profile, *, legacy=False) -> str:
    """Selected context only; no provider or full settings snapshot."""
    context = dict(registry=str(_absolute(config.DEFAULT_CONFIG_PATH)),
        data=str(_absolute(storage.DATA_DIR)), roots={name:str(_absolute(getattr(storage,name))) for name in
        ("AUDIO_DIR", "TRANSCRIPTS_DIR", "CORPUS_DIR", "REPORTS_DIR", "PREPARATION_JOBS_DIR")},
        profile={name:getattr(profile,name) for name in ("podcast_id", "source_type", "language", "summary_profile")})
    if not legacy:
        context["transcription"] = transcription.resolve(profile).as_dict()
    return _digest(context)


def job_context_matches(job, profile) -> bool:
    legacy = job["schema_version"] == 1
    return not (legacy and profile.preparation_transcription is not None) and job["context_digest"] == context_digest(profile, legacy=legacy)


def _profile(identity, source_type):
    try:
        registry = _absolute(config.DEFAULT_CONFIG_PATH)
        if registry.name.casefold().startswith(".env"):
            raise PreparationError("inspection_unavailable")
        for parent in registry.parents:
            info = parent.lstat()
            if jobs.is_redirect(info) or not stat.S_ISDIR(info.st_mode):
                raise PreparationError("inspection_unavailable")
        info = registry.lstat()
        if jobs.is_redirect(info) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise PreparationError("inspection_unavailable")
        profile = config.load_podcast_profile(identity.podcast_id, config.DEFAULT_CONFIG_PATH)
    except transcription.InvalidTranscriptionSettings:
        raise PreparationError("invalid_transcription_settings") from None
    except KeyError:
        raise PreparationError("profile_missing") from None
    except Exception:
        raise PreparationError("inspection_unavailable") from None
    if profile.source_type != source_type:
        raise PreparationError("source_type_mismatch")
    return profile


def _names(directory):
    if jobs.safe_path(directory, directory=True) is None:
        return ()
    names = secure_directory_names(storage.DATA_DIR, directory, max_entries=MAX_DIRECTORY_ENTRIES)
    if names is None:
        raise PreparationError("inspection_unavailable")
    return names


def _snapshot(path, *, maximum=MAX_TRANSCRIPT_BYTES):
    raw = secure_read_bytes(storage.DATA_DIR, path, max_bytes=maximum)
    if raw is None:
        raise PreparationError("inspection_unavailable")
    return raw


def validate_transcript_ready(podcast_id, episode_ref, paths, *, expected_title=None, payload_sink=None) -> bool:
    """Validate bounded immutable reads, identity, completeness and real timestamps."""
    try:
        for path in (paths.text_path, paths.srt_path, paths.json_path):
            info = jobs.safe_path(path)
            if info is None or info.st_size > MAX_TRANSCRIPT_BYTES:
                return False
        text = _snapshot(paths.text_path).decode("utf-8")
        srt = _snapshot(paths.srt_path).decode("utf-8")
        payload = json.loads(_snapshot(paths.json_path).decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != episode_ref:
            return False
        title = payload.get("title")
        if not isinstance(title, str) or not 1 <= len(title) <= 512 or (expected_title is not None and title != expected_title):
            return False
        expected = storage.transcript_asset_paths(podcast_id, episode_ref, title)
        if tuple(_absolute(p) for p in (expected.text_path,expected.srt_path,expected.json_path)) != tuple(_absolute(p) for p in (paths.text_path,paths.srt_path,paths.json_path)) or payload.get("completed") is not True:
            return False
        segments = payload.get("segments")
        if not isinstance(segments, list) or type(payload.get("segment_count")) is not int or payload["segment_count"] != len(segments):
            return False
        problems = []
        normalized = _normalize_segments(segments, problems)
        if problems or len(normalized) != len(segments) or any(not math.isfinite(s["start"]) or not math.isfinite(s["end"]) for s in normalized):
            return False
        if segments and (not text.strip() or not srt.strip()):
            return False
        if payload_sink is not None:
            payload_sink.append(payload)
        return True
    except (PreparationError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return False


def _artifacts(identity, title, module, *, payload_sink=None):
    podcast_id, ref = identity.podcast_id, identity.episode_ref
    audio = _absolute(storage.audio_asset_path(podcast_id, ref, title, ".wav"))
    seed = _absolute(storage.corpus_episode_seed_asset_path(podcast_id, ref))
    raw_paths = storage.transcript_asset_paths(podcast_id, ref, title)
    paths = storage.TranscriptAssetPaths(*(_absolute(p) for p in (raw_paths.text_path,raw_paths.srt_path,raw_paths.json_path)))
    reports = (storage.youtube_video_ingest_run_asset_paths if module is youtube_video_ingest else storage.x_video_ingest_run_asset_paths)(podcast_id, ref)
    reports = type(reports)(_absolute(reports.json_path),_absolute(reports.markdown_path))
    roles = [audio, seed, paths.text_path, paths.srt_path, paths.json_path, reports.json_path, reports.markdown_path]
    for path in roles:
        jobs.safe_path(path)
    ready=False
    selected_payloads = []
    audio_names = []
    for directory in {p.parent for p in roles}:
        names = _names(directory)
        relevant = [n for n in names if n.startswith(ref + "__") or n.startswith(ref + ".")]
        if any(".part" in n or ".old" in n or ".wfderive." in n for n in relevant):
            raise PreparationError("partial_artifacts")
        if directory == paths.json_path.parent:
            candidates = [n for n in relevant if n.endswith((".json", ".txt", ".srt"))]
            if candidates:
                json_names = [n for n in candidates if n.endswith(".json")]
                if len(json_names) != 1:
                    raise PreparationError("partial_artifacts")
                existing = directory / json_names[0]
                selected = storage.TranscriptAssetPaths(existing.with_suffix(".txt"), existing.with_suffix(".srt"), existing)
                if set(candidates) != {p.name for p in (selected.text_path, selected.srt_path, selected.json_path)}:
                    raise PreparationError("partial_artifacts")
                if not validate_transcript_ready(podcast_id, ref, selected, payload_sink=selected_payloads):
                    raise PreparationError("partial_artifacts")
                ready=True
        elif directory == audio.parent:
            audio_names = relevant
    allowed_audio = {audio.name}
    if ready:
        allowed_audio.add(storage.audio_asset_path(podcast_id, ref, selected_payloads[0]["title"], ".wav").name)
    for name in audio_names:
        jobs.safe_path(audio.parent / name)
        if name not in allowed_audio:
            raise PreparationError("partial_artifacts")
    if ready:
        if payload_sink is not None:
            payload_sink.extend(selected_payloads)
        return True, [], [], [], []
    observations = []
    for path in roles:
        info = jobs.safe_path(path)
        observations.append(dict(path=str(path), exists=info is not None,
            identity=None if info is None else [info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns]))
    audio_info = jobs.safe_path(audio)
    if audio_info is not None and audio_info.st_size == 0:
        raise PreparationError("partial_artifacts")
    if jobs.safe_path(reports.json_path) is not None or jobs.safe_path(reports.markdown_path) is not None:
        raise PreparationError("previous_outcome_unconfirmed")
    if jobs.safe_path(seed) is not None:
        try:
            payload = json.loads(_snapshot(seed, maximum=64*1024).decode("utf-8"))
            if not isinstance(payload,dict) or payload.get("podcast_id") != podcast_id or payload.get("episode_ref") != ref or payload.get("title") != title:
                raise ValueError
        except (ValueError, UnicodeError, RecursionError):
            raise PreparationError("partial_artifacts") from None
    reuse = [str(audio)] if audio_info is not None else []
    return False, [str(p) for p in roles if str(p) not in reuse], reuse, observations, ["transcribing","validating"] if reuse else ["downloading","transcribing","validating"]


def _empty(reason="unsupported_source", *, network=False):
    return dict(source_type=None,canonical_url=None,podcast_id=None,episode_ref=None,title=None,status="blocked",reason=reason,
        plan_id=None,context_digest=None,stages=[],reads=[],writes=[],reuses=[],artifact_state=[],job_id=None,
        requires_confirmation=False,requires_llm=False,requires_api_cost_ack=False,network_read=network,
        transcript_ready=False,study_guide_ready=False,readiness_verified_at=None,warnings=list(WARNINGS),transcription=None,actual_transcription=None)


def _preview(url, *, ignore_job_id=None,host_transport=None,legacy=False):
    result = _empty()
    try:
        source_type, module, identity, title = _resolve(url)
        result.update(source_type=source_type,canonical_url=identity.canonical_url,podcast_id=identity.podcast_id,
                      episode_ref=identity.episode_ref,title=title,network_read=True)
        profile = _profile(identity, source_type)
        if legacy and profile.preparation_transcription is not None:
            raise PreparationError("inspection_unavailable")
        settings = transcription.resolve(profile)
        result["transcription"] = settings.as_dict()
        if profile.summary_profile != "learning-notes":
            result["warnings"].append("learning_profile_incompatible")
        result["context_digest"] = context_digest(profile, legacy=legacy)
        active = jobs.active_job()
        if active is not None and active["job_id"] != ignore_job_id:
            result.update(status="in_progress" if active["canonical_url"] == identity.canonical_url and job_context_matches(active, profile) else "busy",
                          reason="processing" if active["status"] in jobs.ACTIVE else "previous_outcome_unconfirmed",job_id=active["job_id"])
            if active["status"] not in jobs.ACTIVE:
                result["status"] = "blocked"
            return result
        previous = jobs.source_history(source_type + ":" + identity.canonical_url)
        if previous and previous["status"] in {"failed","attention_required"} and previous["reason"] != "launch_failed":
            raise PreparationError("previous_outcome_unconfirmed")
        payloads = []
        ready,writes,reuses,state,stages = _artifacts(identity, title, module, payload_sink=payloads)
        if ready:
            actual = transcription.actual(payloads[0])
            result["actual_transcription"] = actual
            if actual is None:
                result["warnings"].append("existing_transcription_unknown")
            elif actual != result["transcription"]:
                result["warnings"].append("existing_transcription_differs")
            result.update(status="transcript_ready",reason="validated",transcript_ready=True,readiness_verified_at=jobs.utc_now().isoformat())
            return result
        if not transcription.runtime_available(settings):
            raise PreparationError("transcription_runtime_unavailable")
        # Windows venv redirectors can add nested jobs, so the immediate job's
        # policy cannot prove stdio client-tree independence. Refuse stdio before
        # admission; independently managed HTTP hosting has separate lifetime.
        if os.name=="nt" and host_transport=="stdio":
            raise PreparationError("worker_host_incompatible")
        # A claimed worker rechecks its plan without admitting another worker.
        # Its own child-launch policy is unrelated to finishing this job.
        if ignore_job_id is None:
            _worker_flags()
        store = _absolute(storage.PREPARATION_JOBS_DIR / "jobs.sqlite3")
        writes += [str(store), str(store) + "-journal"]
        result.update(status="action_available",reason="preparation_needed",requires_confirmation=True,reads=["selected_source_registry", *reuses],
                      writes=writes,reuses=reuses,artifact_state=state,stages=stages)
        result["warnings"].append("model_download_possible")
        result["plan_id"] = jobs.plan_digest({key:value for key,value in result.items() if not (legacy and key == "transcription")})
    except PreparationError as error:
        result.update(status="blocked",reason=error.reason if error.reason in _BLOCKERS else "inspection_unavailable")
        result["network_read"] = result["network_read"] or error.reason == "metadata_unavailable"
    return result


def _windows_job_limits():
    """Read current host policy; never change a job or its permissions."""
    import ctypes
    from ctypes import wintypes
    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time",ctypes.c_int64),("job_time",ctypes.c_int64),
                    ("flags",wintypes.DWORD),("minimum",ctypes.c_size_t),("maximum",ctypes.c_size_t),
                    ("active_processes",wintypes.DWORD),("affinity",ctypes.c_size_t),
                    ("priority",wintypes.DWORD),("scheduling",wintypes.DWORD)]
    try:
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
        kernel.IsProcessInJob.restype=wintypes.BOOL
        kernel.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p]
        kernel.QueryInformationJobObject.restype=wintypes.BOOL
        bound=wintypes.BOOL()
        if not kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(bound)):
            raise OSError
        if not bound.value:
            return None
        limits=BasicLimits()
        if not kernel.QueryInformationJobObject(None,2,ctypes.byref(limits),ctypes.sizeof(limits),None):
            raise OSError
        return limits.flags
    except (AttributeError,OSError):
        raise PreparationError("worker_host_incompatible") from None


def _windows_worker_flags():
    limits=_windows_job_limits()
    flags=0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    if limits is None or limits & 0x1000:  # silent breakaway already permitted
        return flags
    if limits & 0x800:  # explicit breakaway permitted by the host
        return flags | 0x01000000
    raise PreparationError("worker_host_incompatible")


def _worker_flags():
    return _windows_worker_flags() if os.name == "nt" else 0


def launch_worker(job):
    """Start one hidden, independent process with fixed code and selected context."""
    from .local_env_names import DATA_DIR_ENV, CONFIG_ENV
    jobs.validate_job_id(job["job_id"])
    script = Path(__file__).resolve().parents[2] / "scripts" / "run_source_preparation_worker.py"
    environment = os.environ.copy()
    environment[DATA_DIR_ENV] = str(_absolute(storage.DATA_DIR))
    environment[CONFIG_ENV] = str(_absolute(config.DEFAULT_CONFIG_PATH))
    try:
        for name, leaf in (("AUDIO_DIR","audio"),("TRANSCRIPTS_DIR","transcripts"),("CORPUS_DIR","corpus"),
                           ("REPORTS_DIR","reports"),("PREPARATION_JOBS_DIR","preparation-jobs")):
            if _absolute(getattr(storage,name)) != _absolute(storage.DATA_DIR / leaf):
                raise OSError
        flags = _worker_flags()
        process = subprocess.Popen([sys.executable,str(script),job["job_id"]], env=environment,
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            close_fds=True,creationflags=flags,start_new_session=os.name != "nt")
        if type(process.pid) is not int or process.pid < 1:
            raise RuntimeError
    except (OSError,PreparationError) as error:
        try:
            jobs.refuse_launch(job["job_id"])
        except PreparationError:
            raise PreparationError("outcome_unconfirmed") from None
        reason="worker_host_incompatible" if isinstance(error,PreparationError) and error.reason=="worker_host_incompatible" else "launch_failed"
        raise PreparationError(reason) from None
    except Exception:
        try:
            jobs.uncertain_launch(job["job_id"])
        except PreparationError:
            pass
        raise PreparationError("outcome_unconfirmed") from None


def _accepted(job, created):
    return {**{key:job[key] for key in ("job_id","source_type","canonical_url","podcast_id","episode_ref")},
            "status":"accepted","job_state":job["status"],"submission":"created" if created else "reused",
            "transcript_ready":False,"study_guide_ready":False,"requires_llm":False,"requires_api_cost_ack":False,"warnings":list(job["plan"].get("warnings",WARNINGS)),
            "transcription":job["plan"].get("transcription"),"actual_transcription":job.get("actual_transcription")}


def prepare_learning_source(url: str, *, confirm: bool = False, expected_plan_id: str = "",host_transport: str | None = None) -> dict:
    if type(confirm) is not bool or not isinstance(expected_plan_id,str) or (not confirm and expected_plan_id) or (confirm and not re.fullmatch(r"[a-f0-9]{64}",expected_plan_id)):
        raise PreparationError("invalid_request")
    if not confirm:
        return _preview(url,host_transport=host_transport)
    source_type, module, identity, title = _resolve(url)
    try:
        profile = _profile(identity, source_type)
    except PreparationError:
        raise PreparationError("plan_changed") from None
    active = jobs.active_job()
    if active is not None:
        if active["canonical_url"] != identity.canonical_url:
            raise PreparationError("busy")
        if active["approved_plan_id"] != expected_plan_id or not job_context_matches(active,profile) or active["plan"]["title"] != title:
            raise PreparationError("plan_changed")
        if active["status"] not in jobs.ACTIVE:
            raise PreparationError("outcome_unconfirmed")
        return _accepted(active, False)
    if os.name=="nt" and host_transport=="stdio":
        raise PreparationError("worker_host_incompatible")
    plan = _preview(url,host_transport=host_transport)
    if plan["status"] != "action_available" or plan["plan_id"] != expected_plan_id:
        raise PreparationError("plan_changed")
    job, created = jobs.admit(plan)
    if created:
        try:
            launch_worker(job)
        except PreparationError as error:
            error.job_id=job["job_id"]
            raise
    return _accepted(job, created)


def inspect_source_preparation_job(job_id: str) -> dict:
    return jobs.inspect(job_id)
