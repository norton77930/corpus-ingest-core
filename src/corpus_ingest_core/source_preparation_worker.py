"""One admitted preparation job; no scheduler, retry or recovery cleanup."""
from __future__ import annotations

import threading
from types import SimpleNamespace

from . import config, storage, source_preparation as core
from . import source_preparation_jobs as jobs
from . import preparation_transcription as transcription
from .artifact_preservation import preparation_artifact_preservation


def run_worker(job_id: str) -> int:
    """Return a finite exit code; never print content, settings or exceptions."""
    try:
        if jobs.load(job_id) is None:
            return 1
        job = jobs.claim(job_id)
    except (jobs.PreparationError, ValueError):
        return 1
    stop = threading.Event()
    failed_heartbeat = threading.Event()
    started_effects = False
    events = []

    def heartbeat():
        while not stop.wait(jobs.HEARTBEAT_SECONDS):
            try:
                jobs.update(job_id,job["owner_token"])
            except Exception:
                failed_heartbeat.set()
                return

    beater = threading.Thread(target=heartbeat,daemon=True,name="source-preparation-heartbeat")
    beater.start()
    try:
        profile = core._profile(SimpleNamespace(podcast_id=job["podcast_id"]), job["source_type"])
        if not core.job_context_matches(job, profile):
            raise jobs.PreparationError("plan_changed")
        fresh = core._preview(job["canonical_url"],ignore_job_id=job_id,legacy=job["schema_version"] == 1)
        if fresh["reason"] == "transcription_runtime_unavailable":
            raise jobs.PreparationError("transcription_runtime_unavailable")
        if fresh["status"] != "action_available" or fresh["plan_id"] != job["approved_plan_id"] or (job["schema_version"] == 2 and fresh["transcription"] != job["plan"]["transcription"]):
            raise jobs.PreparationError("plan_changed")
        module = core.youtube_video_ingest if job["source_type"] == "yt-video" else core.x_video_ingest

        def progress(stage, identity):
            nonlocal started_effects
            if failed_heartbeat.is_set():
                raise jobs.PreparationError("store_unavailable")
            if not isinstance(identity,dict) or any(identity.get(key) != job[key] for key in ("podcast_id","episode_ref","canonical_url")):
                raise jobs.PreparationError("plan_changed")
            profile = core._profile(SimpleNamespace(podcast_id=job["podcast_id"]),job["source_type"])
            if not core.job_context_matches(job, profile):
                raise jobs.PreparationError("plan_changed")
            if len(events) >= len(job["plan"]["stages"]) or stage != job["plan"]["stages"][len(events)]:
                raise jobs.PreparationError("plan_changed")
            if not events:
                observed = core._artifacts(SimpleNamespace(**identity),job["plan"]["title"],module)
                if observed[0] or observed[3] != job["plan"]["artifact_state"]:
                    raise jobs.PreparationError("plan_changed")
            jobs.update(job_id,job["owner_token"],status=stage)
            events.append(stage)
            started_effects = True

        executor = module.run_youtube_video_ingest if job["source_type"] == "yt-video" else module.run_x_video_ingest
        options = job["plan"].get("transcription", transcription.TranscriptionSettings().as_dict())
        with preparation_artifact_preservation():
            executor(job["canonical_url"],confirm=True,title=job["plan"]["title"],force=False,progress_callback=progress,
                     **{k: options[k] for k in ("model", "device", "compute_type")})
        if events != job["plan"]["stages"] or failed_heartbeat.is_set():
            raise jobs.PreparationError("execution_failed")
        paths = storage.transcript_asset_paths(job["podcast_id"],job["episode_ref"],job["plan"]["title"])
        payloads = []
        if not core.validate_transcript_ready(job["podcast_id"],job["episode_ref"],paths,expected_title=job["plan"]["title"],payload_sink=payloads):
            raise jobs.PreparationError("validation_failed")
        actual = transcription.actual(payloads[0])
        if job["schema_version"] == 2 and actual != options:
            raise jobs.PreparationError("validation_failed")
        profile = core._profile(SimpleNamespace(podcast_id=job["podcast_id"]),job["source_type"])
        if not core.job_context_matches(job, profile):
            raise jobs.PreparationError("plan_changed")
        stop.set()
        beater.join(timeout=2)
        if failed_heartbeat.is_set():
            raise jobs.PreparationError("store_unavailable")
        jobs.update(job_id,job["owner_token"],status="transcript_ready",reason="validated",release=True,
                    **({"actual_transcription": actual} if job["schema_version"] == 2 else {}))
        return 0
    except BaseException as error:
        reason = "outcome_unconfirmed" if started_effects else "execution_failed"
        if isinstance(error,jobs.PreparationError) and error.reason in {"plan_changed","validation_failed","transcription_runtime_unavailable"}:
            reason = error.reason
        try:
            jobs.update(job_id,job["owner_token"],status="attention_required" if started_effects else "failed",
                        reason=reason,release=not started_effects)
        except Exception:
            # A broken store cannot prove publication or termination. Keep the
            # last observation and slot; read-only inspection will report staleness.
            pass
        return 1
    finally:
        stop.set()
        beater.join(timeout=2)
