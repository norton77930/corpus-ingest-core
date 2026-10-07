"""Source readiness and consent using public-metadata fakes and owned artifacts."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

URL = "https://x.com/demo/status/123456789"
YT_URL = "https://youtu.be/abc_def-hij"


@pytest.fixture
def configured_source(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import config, x_video_ingest, youtube_video_ingest
    registry = tmp_data_dirs / "profiles.yaml"
    registry.write_text("podcasts:\n  x-demo:\n    display_name: Demo\n    source_type: x-video\n    language: en\n  yt-demo:\n    display_name: Demo\n    source_type: yt-video\n    language: en\n", encoding="utf-8")
    monkeypatch.setattr(config, "DEFAULT_CONFIG_PATH", registry)
    info = {"title": "Demo", "uploader_id": "@demo", "upload_date": "20261001", "duration": 1}
    monkeypatch.setattr(x_video_ingest, "_resolve_metadata", lambda _: dict(info))
    monkeypatch.setattr(youtube_video_ingest, "_resolve_metadata", lambda _: dict(info))
    for module in (x_video_ingest, youtube_video_ingest):
        monkeypatch.setattr(module, "load_podcast_profile", lambda podcast_id: config.load_podcast_profile(podcast_id, config.DEFAULT_CONFIG_PATH))
        monkeypatch.setattr(module, "_acquire_audio", lambda *_: pytest.fail("preview must not download"))
    return tmp_data_dirs


def transcript(*, podcast_id="x-demo", episode_ref="123456789", title="Demo", completed=True):
    from corpus_ingest_core import storage
    paths = storage.transcript_asset_paths(podcast_id, episode_ref, title)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text("owned fixture", encoding="utf-8")
    paths.srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nowned fixture\n", encoding="utf-8")
    paths.json_path.write_text(json.dumps(dict(podcast_id=podcast_id, episode_ref=episode_ref, title=title,
        completed=completed, segment_count=1, segments=[dict(id=0,start=0,end=1,text="owned fixture")])), encoding="utf-8")
    return paths


def core():
    from corpus_ingest_core import source_preparation
    return source_preparation


@pytest.mark.parametrize("url,podcast_id", [(URL,"x-demo"),(YT_URL,"yt-demo")])
def test_preview_is_zero_write_and_declares_effects(configured_source, url, podcast_id):
    before = sorted((p.as_posix(), p.read_bytes()) for p in configured_source.rglob("*") if p.is_file())
    result = core().prepare_learning_source(url)
    assert result["status"] == "action_available" and result["podcast_id"] == podcast_id
    assert len(result["plan_id"]) == 64 and result["requires_confirmation"] is True
    assert result["requires_llm"] is False and result["requires_api_cost_ack"] is False
    assert result["network_read"] is True and "validating" in result["stages"]
    assert any("preparation-jobs" in p for p in result["writes"])
    assert sorted((p.as_posix(), p.read_bytes()) for p in configured_source.rglob("*") if p.is_file()) == before


@pytest.mark.parametrize("url", ["https://example.com/video", "file:///tmp/video", "https://x.com/demo/status/123evil", "https://user@x.com/demo/status/123", "https://x.com:99/demo/status/123", "https://x.com/demo/status/123#secret", "x"*2049, None])
def test_unsupported_urls_stop_before_network(configured_source, monkeypatch, url):
    from corpus_ingest_core import x_video_ingest, youtube_video_ingest
    for module in (x_video_ingest, youtube_video_ingest):
        monkeypatch.setattr(module, "_resolve_metadata", lambda _: pytest.fail("invalid URL contacted source"))
    assert core().prepare_learning_source(url)["reason"] == "unsupported_source"


def test_profile_missing_and_type_mismatch_are_specific(configured_source):
    registry = configured_source / "profiles.yaml"
    registry.write_text("podcasts: {}\n", encoding="utf-8")
    assert core().prepare_learning_source(URL)["reason"] == "profile_missing"
    registry.write_text("podcasts:\n  x-demo:\n    display_name: Demo\n    source_type: yt-video\n    language: en\n", encoding="utf-8")
    assert core().prepare_learning_source(URL)["reason"] == "source_type_mismatch"


def test_complete_transcript_is_ready_even_without_learning_profile(configured_source):
    transcript()
    result = core().prepare_learning_source(URL)
    assert result["status"] == "transcript_ready" and result["plan_id"] is None
    assert result["readiness_verified_at"] and result["study_guide_ready"] is False
    assert not (configured_source / "preparation-jobs").exists()


@pytest.mark.parametrize("defect", ["missing_srt","partial","wrong_identity","malformed","part","old","directory"])
def test_partial_recovery_and_unsafe_artifacts_block(configured_source, defect):
    paths = transcript()
    if defect == "missing_srt":
        paths.srt_path.unlink()
    elif defect == "partial":
        transcript(completed=False)
    elif defect == "wrong_identity":
        payload = json.loads(paths.json_path.read_text())
        payload["podcast_id"] = "x-other"
        paths.json_path.write_text(json.dumps(payload))
    elif defect == "malformed":
        paths.json_path.write_text("[]")
    elif defect in {"part","old"}:
        paths.text_path.with_suffix(".txt." + defect).write_bytes(b"preserve")
    elif defect == "directory":
        paths.text_path.unlink()
        paths.text_path.mkdir()
    result = core().prepare_learning_source(URL)
    assert result["status"] == "blocked" and result["plan_id"] is None


def test_existing_audio_reuses_and_drift_changes_binding(configured_source):
    from corpus_ingest_core import storage
    audio = storage.audio_asset_path("x-demo", "123456789", "Demo", ".wav")
    first = core().prepare_learning_source(URL)
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"owned audio")
    second = core().prepare_learning_source(URL)
    assert second["stages"] == ["transcribing","validating"]
    assert str(audio) in second["reuses"] and first["plan_id"] != second["plan_id"]


def test_confirm_requires_binding_and_recomputes_before_admission(configured_source, monkeypatch):
    source = core()
    monkeypatch.setattr(source, "launch_worker", lambda _: pytest.fail("must not launch"))
    with pytest.raises(source.PreparationError, match="invalid_request"):
        source.prepare_learning_source(URL, confirm=True)
    plan = source.prepare_learning_source(URL)
    (configured_source / "profiles.yaml").write_text("podcasts: {}\n", encoding="utf-8")
    with pytest.raises(source.PreparationError, match="plan_changed"):
        source.prepare_learning_source(URL, confirm=True, expected_plan_id=plan["plan_id"])
    assert not (configured_source / "preparation-jobs").exists()


def test_one_submit_returns_quick_job_and_duplicate_does_not_spawn(configured_source, monkeypatch):
    source = core()
    called = []
    monkeypatch.setattr(source, "launch_worker", lambda job: called.append(job["job_id"]))
    plan = source.prepare_learning_source(URL)
    first = source.prepare_learning_source(URL, confirm=True, expected_plan_id=plan["plan_id"])
    second = source.prepare_learning_source(URL, confirm=True, expected_plan_id=plan["plan_id"])
    assert first["job_id"] == second["job_id"] and second["submission"] == "reused"
    assert called == [first["job_id"]] and first["transcript_ready"] is False
    assert source.prepare_learning_source(URL)["status"] == "in_progress"
    assert source.prepare_learning_source("https://x.com/demo/status/987654321")["status"] == "busy"


def test_submission_tolerates_an_empty_first_writer_reservation(configured_source,monkeypatch):
    source=core()
    monkeypatch.setattr(source,"launch_worker",lambda job:None)
    plan=source.prepare_learning_source(URL)
    directory=configured_source/"preparation-jobs"
    directory.mkdir()
    (directory/"jobs.sqlite3").write_bytes(b"")
    result=source.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"])
    assert result["status"]=="accepted"


@pytest.mark.skipif(os.name!="nt",reason="Windows stdio host restriction")
def test_matching_active_http_job_can_be_coalesced_without_stdio_spawn(configured_source,monkeypatch):
    source=core()
    launched=[]
    monkeypatch.setattr(source,"launch_worker",lambda job:launched.append(job["job_id"]))
    plan=source.prepare_learning_source(URL,host_transport="streamable-http")
    first=source.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"],host_transport="streamable-http")
    second=source.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"],host_transport="stdio")
    assert second["job_id"]==first["job_id"] and second["submission"]=="reused"
    assert launched==[first["job_id"]]


def test_metadata_failure_and_unsafe_inspection_never_mean_missing(configured_source, monkeypatch):
    from corpus_ingest_core import x_video_ingest
    monkeypatch.setattr(x_video_ingest, "_resolve_metadata", lambda _: (_ for _ in ()).throw(RuntimeError("private diagnostic")))
    result = core().prepare_learning_source(URL)
    assert result["reason"] == "metadata_unavailable" and "private diagnostic" not in json.dumps(result)


def test_overlimit_directory_is_not_empty(configured_source, monkeypatch):
    source = core()
    monkeypatch.setattr(source, "MAX_DIRECTORY_ENTRIES", 1)
    transcript()
    assert source.prepare_learning_source(URL)["status"] == "blocked"


def test_ready_transcript_does_not_hide_unsafe_declared_audio(configured_source):
    from corpus_ingest_core import storage
    transcript()
    storage.audio_asset_path("x-demo", "123456789", "Demo", ".wav").mkdir(parents=True)
    assert core().prepare_learning_source(URL)["reason"] == "unsafe_path"


def test_equivalent_relative_and_absolute_context_keeps_binding(configured_source, monkeypatch):
    from corpus_ingest_core import storage
    names = [name for name,value in vars(storage).items() if name.isupper() and name.endswith("_DIR") and isinstance(value,Path)]
    absolute = {name:Path(os.path.abspath(getattr(storage,name))) for name in names}
    for name,value in absolute.items():
        monkeypatch.setattr(storage,name,Path(os.path.relpath(value,Path.cwd())))
    relative_plan = core().prepare_learning_source(URL)
    for name,value in absolute.items():
        monkeypatch.setattr(storage,name,value)
    absolute_plan = core().prepare_learning_source(URL)
    assert relative_plan["plan_id"] == absolute_plan["plan_id"]


def test_metadata_uses_canonical_single_video_url(configured_source, monkeypatch):
    from corpus_ingest_core import youtube_video_ingest
    seen=[]
    def resolve(url):
        seen.append(url)
        return dict(title="Demo",uploader_id="@demo")
    monkeypatch.setattr(youtube_video_ingest,"_resolve_metadata",resolve)
    assert core().prepare_learning_source(YT_URL + "?list=ignored")["status"] == "action_available"
    assert seen == ["https://www.youtube.com/watch?v=abc_def-hij"]


@pytest.mark.parametrize("name",[".env",".ENV",".Env.local"])
def test_selected_env_file_is_never_opened_as_registry(configured_source, monkeypatch,name):
    from corpus_ingest_core import config
    monkeypatch.setattr(config,"DEFAULT_CONFIG_PATH",configured_source / name)
    (configured_source/name).write_text("owned no-secret fixture",encoding="utf-8")
    called=[]
    monkeypatch.setattr(config,"load_podcast_profile",lambda *a: called.append(a) or SimpleNamespace(source_type="x-video",podcast_id="x-demo",language="en",summary_profile="finance"))
    assert core().prepare_learning_source(URL)["reason"] == "inspection_unavailable"
    assert called == []


def test_ready_requires_inspection_of_all_artifact_directories(configured_source,monkeypatch):
    from corpus_ingest_core import storage
    paths=transcript()
    source=core()
    visited=[]
    original=source._names
    monkeypatch.setattr(source,"_names",lambda directory: visited.append(directory) or original(directory))
    assert source.prepare_learning_source(URL)["transcript_ready"]
    reports=storage.x_video_ingest_run_asset_paths("x-demo","123456789")
    expected={paths.json_path.parent,storage.audio_asset_path("x-demo","123456789","Demo",".wav").parent,
              storage.corpus_episode_seed_asset_path("x-demo","123456789").parent,reports.json_path.parent}
    assert expected<=set(visited)


def test_finance_profile_disclosed_without_blocking_transcript(configured_source,monkeypatch):
    source=core()
    monkeypatch.setattr(source,"launch_worker",lambda job:None)
    plan=source.prepare_learning_source(URL)
    assert plan["status"]=="action_available"
    assert "learning_profile_incompatible" in plan["warnings"]
    result=source.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"])
    assert "learning_profile_incompatible" in result["warnings"]
    assert "learning_profile_incompatible" in source.inspect_source_preparation_job(result["job_id"])["warnings"]
