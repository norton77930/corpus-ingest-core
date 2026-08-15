"""Acquire only Spec033's fixed public Hermes source allowlist.

No upstream module is imported or executed. GitHub data is downloaded only during
acquisition; publication is an atomic, fail-closed local operation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "specs/033-hermes-v019-pinned-source-loader-audit"
BUNDLE_ROOT = SPEC_ROOT / "upstream/NousResearch-hermes-agent-b7a05b6"
MANIFEST_PATH = SPEC_ROOT / "contracts/source-bundle-manifest.json"
PUBLICATION_LOCK_PATH = SPEC_ROOT / "contracts/.spec033-source-publication.lock"
REPOSITORY = "NousResearch/hermes-agent"
COMMIT = "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
TREE_SHA = "3ae46c7c1576f9a3450a64729be314ba8e853eac"
ALLOWLIST = (
    "LICENSE", "pyproject.toml", "run_agent.py", "hermes_cli/main.py",
    "hermes_cli/oneshot.py", "hermes_cli/plugins.py", "hermes_cli/plugins_cmd.py",
    "hermes_cli/subcommands/plugins.py", "hermes_cli/runtime_provider.py",
    "hermes_cli/config.py", "hermes_cli/env_loader.py", "hermes_cli/hooks.py",
    "agent/agent_init.py", "agent/tool_executor.py", "model_tools.py",
    "providers/__init__.py", "providers/base.py",
)
AUTHORITATIVE_PATH_BLOBS = (
    ("LICENSE", "75410e73319c72cd3e991a501c5455eb78f38375"), ("pyproject.toml", "a2a1d6c0ee240044de98b55bf93f7092f6ecef7d"),
    ("run_agent.py", "75846d5bec81f8daaabb742e33642ee97990b425"), ("hermes_cli/main.py", "fcca52b8851ebd40ea82ad812e3dc9c3a3233e01"),
    ("hermes_cli/oneshot.py", "320c61c8cc12e3d7041215ab37a93b0e5b60c7e9"), ("hermes_cli/plugins.py", "6ca393fca53c1fd2b3479bed72180fedcc848c88"),
    ("hermes_cli/plugins_cmd.py", "f5c57bb88f2bc91b7cbf43abaf7437efa033730a"), ("hermes_cli/subcommands/plugins.py", "5355fbec3429ccd6db06babbc80bf964248c44d1"),
    ("hermes_cli/runtime_provider.py", "7a17fc83943f7b058d6feabf838c60d7c1864a99"), ("hermes_cli/config.py", "640c184f0cc0874644ad21a0cdf51a4e52ea5d9b"),
    ("hermes_cli/env_loader.py", "e91c12adf7ebf8dde6cd794775110c8c61100cd6"), ("hermes_cli/hooks.py", "d3f86bd00e80254b42ea9440cdcede4ab9a0c68b"),
    ("agent/agent_init.py", "e239c48cfbd9d5f3a6f08c3d05852025cb08c218"), ("agent/tool_executor.py", "d235de36c03dd668bfb10377ef51c7074368c6b9"),
    ("model_tools.py", "32394a69eec64f3d676bedb1659a6f4e94887a74"), ("providers/__init__.py", "a394e74b335ae25c8344c025a500eebb97d47b2d"),
    ("providers/base.py", "554e01e4f7c77c3f32604a36fe6f94581b9dea27"),
)
MAX_FILE_BYTES = 1_000_000
_API_BASE = "https://api.github.com/repos/NousResearch/hermes-agent/git"


class PublicationCleanupError(RuntimeError):
    """Publication failed and one or more residual paths could not be removed."""

    def __init__(self, residual_paths: tuple[Path, ...]) -> None:
        super().__init__("publication_cleanup_failed")
        self.residual_paths = residual_paths


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: object, **_kwargs: object) -> object:
        raise urllib.error.HTTPError("", 302, "redirect rejected", {}, None)


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _fetch_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "spec033-static-audit"})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=20) as response:
        size = response.headers.get("Content-Length")
        if response.status != 200 or response.geturl() != url or (size is not None and (not size.isdecimal() or int(size) > MAX_FILE_BYTES * 4)):
            raise ValueError("immutable_github_identity_request_rejected")
        payload = response.read(MAX_FILE_BYTES * 4 + 1)
    if len(payload) > MAX_FILE_BYTES * 4:
        raise ValueError("identity_payload_oversized")
    parsed = json.loads(payload.decode("utf-8"))
    if type(parsed) is not dict:
        raise ValueError("identity_payload_not_object")
    return parsed


def _fetch_blob(blob_sha: str) -> bytes:
    url = f"{_API_BASE}/blobs/{blob_sha}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github.raw", "User-Agent": "spec033-static-audit"})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=20) as response:
        size = response.headers.get("Content-Length")
        if response.status != 200 or response.geturl() != url or (size is not None and (not size.isdecimal() or int(size) > MAX_FILE_BYTES)):
            raise ValueError("immutable_github_blob_request_rejected")
        data = response.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("source_blob_oversized")
    return data


def _acquire() -> dict[str, object]:
    commit = _fetch_json(f"{_API_BASE}/commits/{COMMIT}")
    tree = commit.get("tree")
    if commit.get("sha") != COMMIT or type(tree) is not dict or tree.get("sha") != TREE_SHA:
        raise ValueError("commit_tree_identity_mismatch")
    payload = _fetch_json(f"{_API_BASE}/trees/{TREE_SHA}?recursive=1")
    entries = payload.get("tree")
    if type(entries) is not list or payload.get("truncated") is not False:
        raise ValueError("source_tree_unavailable_or_truncated")
    by_path = {entry.get("path"): entry for entry in entries if type(entry) is dict and type(entry.get("path")) is str}
    records: list[dict[str, object]] = []
    staged: list[tuple[str, bytes]] = []
    for path, expected_blob in AUTHORITATIVE_PATH_BLOBS:
        entry = by_path.get(path)
        if type(entry) is not dict or entry.get("type") != "blob" or entry.get("mode") not in {"100644", "100755"} or entry.get("sha") != expected_blob:
            raise ValueError("authoritative_tree_blob_mismatch")
        data = _fetch_blob(expected_blob)
        if _git_blob_sha(data) != expected_blob:
            raise ValueError("git_blob_identity_mismatch")
        staged.append((path, data))
        records.append({"path": path, "git_blob_sha": expected_blob, "sha256": hashlib.sha256(data).hexdigest(), "byte_length": len(data)})
    license_record = records[0]
    return {"schema_version": "spec033-pinned-source-bundle-v1", "repository": REPOSITORY, "pinned_commit": COMMIT, "tree_sha": TREE_SHA, "license": dict(license_record), "files": records, "_staged": staged}


def _write_file(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _publish_manifest_exclusive(path: Path, data: bytes) -> None:
    _write_file(path, data)


def _post_publication_valid() -> bool:
    """Validate the published target through the static analyzer seam."""
    try:
        from podcast_ingest_core.hermes_v019_source_audit import validate_hermes_v019_source_bundle
        return validate_hermes_v019_source_bundle().bundle_valid is True
    except ImportError:
        return False


def _staging_valid(staging: Path, bundle: dict[str, object]) -> bool:
    files = bundle.get("files")
    if type(files) is not list or tuple((record.get("path"), record.get("git_blob_sha")) for record in files if type(record) is dict) != AUTHORITATIVE_PATH_BLOBS:
        return False
    try:
        saved = tuple(sorted(item.relative_to(staging).as_posix() for item in staging.rglob("*") if item.is_file()))
        if saved != tuple(sorted(ALLOWLIST)):
            return False
        return all(
            type(record) is dict and (staging / record["path"]).read_bytes() == data and _git_blob_sha(data) == record["git_blob_sha"] and hashlib.sha256(data).hexdigest() == record["sha256"] and len(data) == record["byte_length"]
            for record, (_path, data) in zip(files, bundle.get("_staged", ()), strict=True)
        )
    except (OSError, KeyError, TypeError):
        return False


def _write(bundle: dict[str, object]) -> None:
    staged = bundle.get("_staged")
    BUNDLE_ROOT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_acquired = False
    staging: Path | None = None
    published_bundle = False
    manifest_published = False
    publication_succeeded = False
    try:
        _write_file(PUBLICATION_LOCK_PATH, b"spec033\n")
        lock_acquired = True
        if BUNDLE_ROOT.exists() or MANIFEST_PATH.exists() or type(staged) is not list or len(staged) != len(ALLOWLIST):
            raise ValueError("published_target_not_fresh")
        staging = Path(tempfile.mkdtemp(prefix=f".{BUNDLE_ROOT.name}.stage-", dir=BUNDLE_ROOT.parent))
        for path, data in staged:
            if type(path) is not str or type(data) is not bytes or path not in ALLOWLIST:
                raise ValueError("invalid_staged_entry")
            target = staging / path
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_file(target, data)
        if not _staging_valid(staging, bundle):
            raise ValueError("staging_validation_failed")
        sanitized = {key: value for key, value in bundle.items() if key != "_staged"}
        manifest_bytes = (json.dumps(sanitized, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
        # The exclusive manifest is the publication marker. Readers validate the
        # complete pair and fail closed before this final step becomes visible.
        os.rename(staging, BUNDLE_ROOT)
        published_bundle = True
        _publish_manifest_exclusive(MANIFEST_PATH, manifest_bytes)
        manifest_published = True
        if not _post_publication_valid():
            raise ValueError("published_bundle_validation_failed")
        publication_succeeded = True
    except BaseException as error:
        residuals: list[Path] = []
        if staging is not None and staging.exists():
            try:
                shutil.rmtree(staging)
            except OSError:
                residuals.append(staging)
        if published_bundle and BUNDLE_ROOT.exists():
            try:
                shutil.rmtree(BUNDLE_ROOT)
            except OSError:
                residuals.append(BUNDLE_ROOT)
        if manifest_published and MANIFEST_PATH.exists():
            try:
                MANIFEST_PATH.unlink()
            except OSError:
                residuals.append(MANIFEST_PATH)
        if residuals:
            raise PublicationCleanupError(tuple(residuals)) from error
        raise
    finally:
        if lock_acquired:
            cleanup_incomplete = not publication_succeeded and any(
                path is not None and path.exists()
                for path in (staging, BUNDLE_ROOT if published_bundle else None, MANIFEST_PATH if manifest_published else None)
            )
            if not cleanup_incomplete:
                try:
                    PUBLICATION_LOCK_PATH.unlink(missing_ok=True)
                except OSError as error:
                    raise PublicationCleanupError((PUBLICATION_LOCK_PATH,)) from error


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args not in {(), ("--write",)}:
        print(json.dumps({"status": "rejected", "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 2
    try:
        bundle = _acquire()
        if args == ("--write",):
            _write(bundle)
        print(json.dumps({"status": "acquired" if args else "validated", "file_count": len(ALLOWLIST), "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 0
    except Exception:
        print(json.dumps({"status": "BLOCKED_SOURCE_GRAPH", "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
