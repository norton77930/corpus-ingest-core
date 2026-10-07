"""046: observable refusal, preservation and publication-state contracts."""
from pathlib import Path
import json
import stat
from types import SimpleNamespace

import pytest

from corpus_ingest_core import errors, storage, workflow_derivation as core
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from tests.test_workflow_derivation import (
    PODCAST, EPISODE, TITLE, LECTURE, _ready_lecture, _context,
    _write_existing_pair, _FakeProvider, _valid_payload,
)


def state_error():
    assert hasattr(errors, "WorkflowDerivationStateError")
    return errors.WorkflowDerivationStateError


def test_finite_state_error_is_compatible_and_unknown_reason_is_safe():
    cls = state_error()
    exc = cls("recovery_required")
    assert isinstance(exc, errors.WorkflowDerivationError)
    assert exc.reason_code == "recovery_required"
    assert str(exc) == "Existing study-guide or derivation staging/backup entries require operator review; no automatic recovery was attempted."
    assert "PRIVATE_SENTINEL" not in str(cls("PRIVATE_SENTINEL"))


def ready(root, monkeypatch, *, reuse=False):
    _ready_lecture(root)
    context = _context(root, ["Claude Code", "Codex"])
    monkeypatch.setattr(core, "DEFAULT_CONTEXT_PATH", context)
    if reuse:
        _write_existing_pair(root)
    return storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir


def no_provider(*args, **kwargs):
    pytest.fail("refusal/reuse/preview must not construct a provider")


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def run(**kwargs):
    return core.run_workflow_derivation(PODCAST, EPISODE, **kwargs)


def assert_reason(reason, call):
    with pytest.raises(state_error()) as caught:
        call()
    assert caught.value.reason_code == reason


@pytest.mark.parametrize("podcast,episode", [("", EPISODE), (" demo", EPISODE), (PODCAST, "latest"), (PODCAST, "NeXt"), (PODCAST, " EP_1"), (PODCAST, "a/b"), (PODCAST, None)])
@pytest.mark.parametrize("confirm", [False, True])
def test_invalid_identity_precedes_profile_and_context(monkeypatch, podcast, episode, confirm):
    monkeypatch.setattr(core, "load_podcast_profile", no_provider)
    monkeypatch.setattr(core, "create_provider", no_provider)
    assert_reason("invalid_identity", lambda: core.run_workflow_derivation(podcast, episode, confirm=confirm))


@pytest.mark.parametrize("kind", ["podcast", "episode", "title", "json"])
def test_canonical_metadata_identity_is_validated(tmp_data_dirs, monkeypatch, kind):
    ready(tmp_data_dirs, monkeypatch)
    monkeypatch.setattr(core, "create_provider", no_provider)
    path = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE).json_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if kind == "podcast": payload["podcast_id"] = "other"
    elif kind == "episode": payload["episode_ref"] = "other"
    elif kind == "title": payload["title"] = " "
    path.write_text("{" if kind == "json" else json.dumps(payload), encoding="utf-8")
    before = snapshot(tmp_data_dirs)
    assert_reason("invalid_identity", run)
    assert snapshot(tmp_data_dirs) == before


@pytest.mark.parametrize("suffix", [".part", ".old", ".wfderive.part", ".wfderive.old"])
@pytest.mark.parametrize("confirm", [False, True])
@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("reuse", [False, True])
@pytest.mark.parametrize("entry_type", ["file", "directory"])
def test_recovery_refuses_every_mode_without_mutation(tmp_data_dirs, monkeypatch, suffix, confirm, force, reuse, entry_type):
    dest = ready(tmp_data_dirs, monkeypatch, reuse=reuse)
    remnant = dest.with_name(dest.name + suffix)
    if entry_type == "directory":
        remnant.mkdir()
        (remnant / "evidence.bin").write_bytes(b"retained")
    else:
        remnant.write_bytes(b"retained")
    before = snapshot(tmp_data_dirs)
    monkeypatch.setattr(core, "create_provider", no_provider)
    monkeypatch.setattr(core, "_write_run_report", no_provider)
    assert_reason("recovery_required", lambda: run(confirm=confirm, force=force, api_cost_ack=SEMANTIC_API_COST_ACK))
    assert snapshot(tmp_data_dirs) == before


def test_recovery_stat_failure_is_not_absence(tmp_data_dirs, monkeypatch):
    dest = ready(tmp_data_dirs, monkeypatch)
    target = dest.with_name(dest.name + ".old")
    real = Path.lstat
    def denied(path, *args, **kwargs):
        if path == target: raise PermissionError("fixture")
        return real(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", denied)
    assert_reason("unsafe_path", run)


@pytest.mark.parametrize("kind", ["directory", "special", "reparse", "stat", "listing", "disappeared"])
@pytest.mark.parametrize("confirm", [False, True])
def test_unsafe_extra_entries_fail_closed(tmp_data_dirs, monkeypatch, kind, confirm):
    dest = ready(tmp_data_dirs, monkeypatch)
    extra = dest / "extra.bin"
    if kind == "directory": extra.mkdir()
    else: extra.write_bytes(b"unchanged")
    real = Path.lstat
    def metadata(path, *args, **kwargs):
        if path == extra:
            if kind == "stat": raise PermissionError("fixture")
            if kind == "disappeared": raise FileNotFoundError("fixture")
            if kind in {"special", "reparse"}:
                return SimpleNamespace(st_mode=stat.S_IFIFO if kind == "special" else stat.S_IFREG,
                                       st_file_attributes=0x400 if kind == "reparse" else 0)
        return real(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", metadata)
    real_iter = Path.iterdir
    def listing(path):
        if path == dest and kind == "listing": raise PermissionError("fixture")
        return real_iter(path)
    monkeypatch.setattr(Path, "iterdir", listing)
    monkeypatch.setattr(core, "create_provider", no_provider)
    assert_reason("unsafe_path", lambda: run(confirm=confirm, api_cost_ack=SEMANTIC_API_COST_ACK))


@pytest.mark.parametrize("location", ["summary", "lecture", "pair", "context", "report", "report-part", "bundle", "summary-parent", "transcript-parent"])
@pytest.mark.parametrize("confirm", [False, True])
def test_reparse_paths_are_refused(tmp_data_dirs, monkeypatch, location, confirm):
    dest = ready(tmp_data_dirs, monkeypatch, reuse=True)
    report = storage.workflow_derivation_run_asset_paths(PODCAST, EPISODE).json_path
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_bytes(b"old report")
    part = report.with_suffix(report.suffix + ".part")
    part.write_bytes(b"old staging")
    targets = {
        "summary": storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE),
        "lecture": dest / "03_full_summary.md", "pair": dest / "05_prompt_examples.md",
        "context": core.DEFAULT_CONTEXT_PATH, "report": report, "report-part": part,
        "bundle": dest, "summary-parent": storage.SUMMARIES_DIR / PODCAST,
        "transcript-parent": storage.TRANSCRIPTS_DIR / PODCAST,
    }
    target = targets[location]
    real = Path.lstat
    def metadata(path, *args, **kwargs):
        info = real(path, *args, **kwargs)
        if path == target:
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400, st_size=info.st_size)
        return info
    monkeypatch.setattr(Path, "lstat", metadata)
    monkeypatch.setattr(core, "create_provider", no_provider)
    assert_reason("unsafe_path", lambda: run(confirm=confirm, api_cost_ack=SEMANTIC_API_COST_ACK))


@pytest.mark.parametrize("context", ["../context.yaml", "a/../context.yaml", "C:context.yaml", r"\\server\share\context.yaml", r"\\?\C:\context.yaml"])
def test_context_rejects_unsafe_raw_paths(tmp_data_dirs, monkeypatch, context):
    ready(tmp_data_dirs, monkeypatch)
    assert_reason("unsafe_path", lambda: run(workflow_context=context))


def test_context_has_bounded_read(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch)
    core.DEFAULT_CONTEXT_PATH.write_bytes(b"allowed_tools: [Codex]\n#" + b"x" * (2 * 1024 * 1024))
    with pytest.raises(errors.WorkflowDerivationError, match="size cap"):
        run()


@pytest.mark.parametrize("suffix", [".part", ".old", ".wfderive.part", ".wfderive.old"])
def test_broken_recovery_link_is_present(tmp_data_dirs, monkeypatch, suffix):
    dest = ready(tmp_data_dirs, monkeypatch)
    link = dest.with_name(dest.name + suffix)
    try: link.symlink_to(tmp_data_dirs / "absent")
    except OSError: pytest.skip("native symlink unavailable: OSError")
    assert_reason("recovery_required", run)
    assert link.is_symlink()


@pytest.mark.parametrize("mode", ["generate", "force", "partial-force", "reuse"])
def test_pair_preserves_all_unowned_bytes(tmp_data_dirs, monkeypatch, mode):
    dest = ready(tmp_data_dirs, monkeypatch, reuse=mode != "generate")
    if mode == "partial-force": (dest / "06_apply_to_my_workflow.md").unlink()
    (dest / "extra.bin").write_bytes(bytes(range(256)) * 12289)
    (dest / "00_video_info.md").write_bytes(b"\xef\xbb\xbf# cover\r\nend\n")
    before = {p.name: p.read_bytes() for p in dest.iterdir()}
    calls = []
    monkeypatch.setattr(core, "create_provider", no_provider if mode == "reuse" else lambda *a, **k: _FakeProvider(_valid_payload(), calls))
    result = run(confirm=True, force=mode in {"force", "partial-force"}, api_cost_ack="" if mode == "reuse" else SEMANTIC_API_COST_ACK)
    for name, body in before.items():
        if mode == "reuse" or name not in {"05_prompt_examples.md", "06_apply_to_my_workflow.md"}:
            assert (dest / name).read_bytes() == body
    assert (dest / "05_prompt_examples.md").is_file() and (dest / "06_apply_to_my_workflow.md").is_file()
    assert result.reused is (mode == "reuse")
    assert len(calls) == (0 if mode == "reuse" else 1)
    assert result.report_json_path.is_file() and result.report_markdown_path.is_file()


def test_partial_pair_without_force_is_unchanged(tmp_data_dirs, monkeypatch):
    dest = ready(tmp_data_dirs, monkeypatch, reuse=True)
    (dest / "06_apply_to_my_workflow.md").unlink()
    before = snapshot(tmp_data_dirs)
    monkeypatch.setattr(core, "create_provider", no_provider)
    with pytest.raises(errors.WorkflowDerivationError, match="incomplete"):
        run(confirm=True)
    assert snapshot(tmp_data_dirs) == before


@pytest.mark.parametrize("fault", ["copy", "write", "backup", "publish", "rollback", "collision"])
def test_publication_faults_preserve_or_retain_evidence(tmp_data_dirs, monkeypatch, fault):
    dest = ready(tmp_data_dirs, monkeypatch, reuse=True)
    (dest / "extra.bin").write_bytes(b"original binary")
    part = dest.with_name(dest.name + ".wfderive.part")
    old = dest.with_name(dest.name + ".wfderive.old")
    before = snapshot(tmp_data_dirs)
    monkeypatch.setattr(core, "create_provider", lambda *a, **k: _FakeProvider(_valid_payload(), []))
    real_rename, real_write, real_mkdir = Path.rename, Path.write_text, Path.mkdir
    def rename(path, target):
        if (fault == "backup" and path == dest) or (fault in {"publish", "rollback"} and path == part) or (fault == "rollback" and path == old):
            raise OSError("fixture publication failure")
        return real_rename(path, target)
    def write(path, *args, **kwargs):
        if fault == "write" and path == part / "06_apply_to_my_workflow.md": raise OSError("fixture write failure")
        return real_write(path, *args, **kwargs)
    def mkdir(path, *args, **kwargs):
        if fault == "collision" and path == part:
            real_mkdir(path)
            (path / "foreign.bin").write_bytes(b"not owned")
            raise FileExistsError("fixture collision")
        return real_mkdir(path, *args, **kwargs)
    def bad_copy(*a, **k): raise OSError("fixture copy failure")
    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.setattr(Path, "write_text", write)
    monkeypatch.setattr(Path, "mkdir", mkdir)
    if fault == "copy": monkeypatch.setattr(core, "_stream_copy", bad_copy, raising=False)
    reason = "rollback_failed" if fault == "rollback" else "recovery_required" if fault == "collision" else "publish_failed"
    assert_reason(reason, lambda: run(confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK))
    if fault == "rollback":
        assert not dest.exists() and old.is_dir() and part.is_dir()
        assert (old / "extra.bin").read_bytes() == b"original binary"
        assert_reason("recovery_required", run)
    elif fault == "collision":
        assert (part / "foreign.bin").read_bytes() == b"not owned"
        assert (dest / "extra.bin").read_bytes() == b"original binary"
    else:
        assert snapshot(tmp_data_dirs) == before
        assert not old.exists() and not part.exists()


@pytest.mark.parametrize("fault", ["cleanup-stat", "cleanup-type", "cleanup-delete", "report-new", "report-reuse"])
def test_postcommit_failure_never_rolls_back(tmp_data_dirs, monkeypatch, fault):
    reuse = fault == "report-reuse"
    dest = ready(tmp_data_dirs, monkeypatch, reuse=reuse)
    (dest / "extra.bin").write_bytes(b"keep")
    old = dest.with_name(dest.name + ".wfderive.old")
    monkeypatch.setattr(core, "create_provider", no_provider if reuse else lambda *a, **k: _FakeProvider(_valid_payload(), []))
    real_stat, real_remove, real_write = Path.lstat, core.shutil.rmtree, Path.write_text
    committed = lambda: old.exists() and (dest / "06_apply_to_my_workflow.md").is_file()
    def metadata(path, *args, **kwargs):
        info = real_stat(path, *args, **kwargs)
        if path == old and committed():
            if fault == "cleanup-stat": raise PermissionError("fixture")
            if fault == "cleanup-type": return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0)
        return info
    def remove(path, *args, **kwargs):
        if Path(path) == old and fault == "cleanup-delete": raise OSError("fixture")
        return real_remove(path, *args, **kwargs)
    report = storage.workflow_derivation_run_asset_paths(PODCAST, EPISODE).markdown_path
    def write(path, *args, **kwargs):
        if fault.startswith("report") and path == report.with_name(report.name + ".part"):
            raise OSError("fixture actual report writer")
        return real_write(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", metadata)
    monkeypatch.setattr(core.shutil, "rmtree", remove)
    monkeypatch.setattr(Path, "write_text", write)
    reason = "published_cleanup_failed" if fault.startswith("cleanup") else "reused_report_failed" if reuse else "published_report_failed"
    assert_reason(reason, lambda: run(confirm=True, api_cost_ack="" if reuse else SEMANTIC_API_COST_ACK))
    assert (dest / "05_prompt_examples.md").is_file() and (dest / "06_apply_to_my_workflow.md").is_file()
    assert (dest / "extra.bin").read_bytes() == b"keep"



def test_unsafe_bundle_ancestor_is_not_followed_for_recovery(tmp_data_dirs, monkeypatch):
    dest = ready(tmp_data_dirs, monkeypatch)
    real = Path.lstat
    def metadata(path, *args, **kwargs):
        if path.parent == dest.parent and path.name.endswith(".part"):
            pytest.fail("recovery inspection followed an unsafe ancestor")
        info = real(path, *args, **kwargs)
        if path == dest.parent:
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
        return info
    monkeypatch.setattr(Path, "lstat", metadata)
    assert_reason("unsafe_path", run)


def test_transcript_listing_failure_is_unsafe_not_missing(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch)
    directory = storage.TRANSCRIPTS_DIR / PODCAST
    real = Path.iterdir
    def listing(path):
        if path == directory: raise PermissionError("fixture")
        return real(path)
    monkeypatch.setattr(Path, "iterdir", listing)
    assert_reason("unsafe_path", run)


@pytest.mark.parametrize("location", ["source", "lecture", "extra", "context", "report"])
def test_native_file_links_are_refused(tmp_data_dirs, monkeypatch, location):
    dest = ready(tmp_data_dirs, monkeypatch)
    target = {"source": storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE),
              "lecture": dest / "04_learning_notes.md", "extra": dest / "extra.bin",
              "context": core.DEFAULT_CONTEXT_PATH,
              "report": storage.workflow_derivation_run_asset_paths(PODCAST, EPISODE).json_path}[location]
    outside = tmp_data_dirs / "outside.bin"
    outside.write_bytes(b"not followed")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Determine platform support without changing the source fixture first.
    probe = tmp_data_dirs / "link-probe"
    try: probe.symlink_to(outside)
    except OSError: pytest.skip("native symlink unavailable: OSError")
    probe.unlink()
    target.unlink(missing_ok=True)
    target.symlink_to(outside)
    assert_reason("unsafe_path", run)
    assert outside.read_bytes() == b"not followed"


def test_relative_context_and_valid_underscore_identity(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch)
    profile = core.load_podcast_profile(PODCAST)
    monkeypatch.setattr(core, "load_podcast_profile", lambda *_: profile)
    monkeypatch.chdir(tmp_data_dirs)
    result = run(workflow_context="operator_workflow.yaml")
    assert result.run_mode == "preview"
    core._require_explicit_identity("demo", "EP_A1")


@pytest.mark.parametrize("payload", [b"\xff", b"[unclosed", b"- list", b"allowed_tools: []", b"allowed_tools: [1]"])
def test_invalid_context_remains_refused(tmp_data_dirs, monkeypatch, payload):
    ready(tmp_data_dirs, monkeypatch)
    core.DEFAULT_CONTEXT_PATH.write_bytes(payload)
    monkeypatch.setattr(core, "create_provider", no_provider)
    with pytest.raises(errors.WorkflowDerivationError): run(confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)


def test_report_regular_parts_keep_existing_overwrite_protocol(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch, reuse=True)
    paths = storage.workflow_derivation_run_asset_paths(PODCAST, EPISODE)
    for p in (paths.json_path, paths.markdown_path):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.with_name(p.name + ".part").write_bytes(b"ordinary old report staging")
    monkeypatch.setattr(core, "create_provider", no_provider)
    result = run(confirm=True)
    assert result.reused
    assert json.loads(paths.json_path.read_text(encoding="utf-8"))["reused"] is True
    assert not paths.markdown_path.with_name(paths.markdown_path.name + ".part").exists()


@pytest.mark.parametrize("key", ["05_prompt_examples", "06_apply_to_my_workflow"])
def test_unencodable_output_is_refused_before_staging(tmp_data_dirs, monkeypatch, key):
    dest = ready(tmp_data_dirs, monkeypatch)
    payload = _valid_payload()
    payload[key] += chr(0xD800)
    monkeypatch.setattr(core, "create_provider", lambda *a, **k: _FakeProvider(payload, []))
    before = snapshot(tmp_data_dirs)
    with pytest.raises(errors.WorkflowDerivationError):
        run(confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert snapshot(tmp_data_dirs) == before
    assert not dest.with_name(dest.name + ".wfderive.part").exists()


def test_stale_title_neighbor_cannot_replace_canonical_summary(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch)
    canonical = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE)
    canonical.unlink()
    stale = storage.semantic_summary_asset_path(PODCAST, EPISODE, "Stale title")
    stale.write_text("old summary", encoding="utf-8")
    old_lecture = storage.study_guide_bundle_paths(PODCAST, EPISODE, "Stale title")
    old_lecture.bundle_dir.mkdir()
    for name in LECTURE: (old_lecture.bundle_dir / name).write_text("old lecture", encoding="utf-8")
    monkeypatch.setattr(core, "create_provider", no_provider)
    before = snapshot(tmp_data_dirs)
    with pytest.raises(errors.WorkflowDerivationError, match="canonical.*missing"):
        run(confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert snapshot(tmp_data_dirs) == before


def test_transcript_metadata_cap_refuses_before_provider(tmp_data_dirs, monkeypatch):
    ready(tmp_data_dirs, monkeypatch)
    metadata = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE).json_path
    with metadata.open("wb") as stream:
        stream.seek(64 * 1024 * 1024)
        stream.write(b"x")
    before = snapshot(tmp_data_dirs)
    monkeypatch.setattr(core, "create_provider", no_provider)
    assert_reason("unsafe_path", lambda: run(confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK))
    assert snapshot(tmp_data_dirs) == before


@pytest.mark.parametrize("payload", [b"\xff", b"x" * (2 * 1024 * 1024 + 1)], ids=["utf8", "oversized"])
def test_invalid_lecture_encoding_or_size_refuses_before_provider(tmp_data_dirs, monkeypatch, payload):
    dest = ready(tmp_data_dirs, monkeypatch)
    (dest / "03_full_summary.md").write_bytes(payload)
    before = snapshot(tmp_data_dirs)
    monkeypatch.setattr(core, "create_provider", no_provider)
    with pytest.raises(errors.WorkflowDerivationError):
        run(confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert snapshot(tmp_data_dirs) == before
