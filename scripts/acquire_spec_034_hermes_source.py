"""Acquire only Spec034's H2-frozen immutable 20-file source bundle.

No upstream Hermes module is imported or executed. This is not a downloader for
an arbitrary tree: each approved literal blob is fetched by identity.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import re
import secrets
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC_ID = "034-hermes-v019-pinned-startup-source-graph"
SPEC_ROOT = ROOT / "specs" / SPEC_ID
BUNDLE_ROOT = SPEC_ROOT / "upstream" / "NousResearch-hermes-agent-b7a05b6"
MANIFEST_PATH = SPEC_ROOT / "contracts" / "source-bundle-manifest.json"
PUBLICATION_LOCK_PATH = SPEC_ROOT / "contracts" / ".spec034-source-publication.lock"
REPOSITORY = "NousResearch/hermes-agent"
COMMIT = "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
TREE_SHA = "3ae46c7c1576f9a3450a64729be314ba8e853eac"
H1_INVENTORY_SHA256 = "90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d"
API_BASE = "https://api.github.com/repos/NousResearch/hermes-agent/git"
RAW_PREFIX = f"https://raw.githubusercontent.com/NousResearch/hermes-agent/{COMMIT}/"
MAX_FILE_BYTES = 1_000_000

# H2 literal authority, independent from every mutable inventory artifact.
AUTHORITATIVE_PATH_BLOBS = (
    ("agent/agent_init.py", "e239c48cfbd9d5f3a6f08c3d05852025cb08c218", "d43d38208ca3cec807c91d668b91218a6c2b263c255f5e91105fbf675d720424", 131629),
    ("agent/credential_pool.py", "d5d652ad7414c0fc270a4ff5cf837dcb382bb427", "bae44a6559dc32aedcfc5a6c4b3650982f7fa014eaa76243f2173ddaa49162d8", 125241),
    ("agent/process_bootstrap.py", "89b6278a8c258f49f9fda3c8ed35d9eba3117b96", "aad759120134df961c27a71db2e1b6a9c2cd725b54d03c1ab2835c4a347f08ea", 7497),
    ("agent/secret_scope.py", "8b376d5fceff347de8dce40ae0f917b82f3586b5", "414d314d35a458abf3fd70ab7130244a023e2015c944027a27554b27c9a6c94e", 10095),
    ("agent/shell_hooks.py", "c1cec81df3332b3f9b85238635cdf914af007193", "851c1b800c6e6c2c76b45eeb6cae02f1b96f63c30cd50615cfac198f983b2e47", 33689),
    ("hermes_cli/auth.py", "011cf817aebd88b915a32ba090628d19e8fb360b", "3dd63df2c06aa5fdea9e3d020bbbcd10156e1ef820156b2bbe4c768af076150a", 357982),
    ("hermes_cli/config.py", "640c184f0cc0874644ad21a0cdf51a4e52ea5d9b", "f4f5c41ca42a2b855e437eca00ea7c8906b8b8bc56a53aa3c49782c3f25550b1", 438401),
    ("hermes_cli/env_loader.py", "e91c12adf7ebf8dde6cd794775110c8c61100cd6", "223122b50dad39b2b97f8aa06464a400115250fbfa617b56d692b65666e79f09", 22239),
    ("hermes_cli/main.py", "fcca52b8851ebd40ea82ad812e3dc9c3a3233e01", "402557604c530bc4f8a143d921244d38fde210460c6811cba91b10e3a92a5690", 670990),
    ("hermes_cli/oneshot.py", "320c61c8cc12e3d7041215ab37a93b0e5b60c7e9", "70d0b5abda1565cdc0db88d0f54c37890a75212b96a58650c2c6146574d462e5", 20852),
    ("hermes_cli/plugins.py", "6ca393fca53c1fd2b3479bed72180fedcc848c88", "0f6c28614bebb7444392625a63c2b3186039f04238fe6ca79ad62d4849b0551c", 102530),
    ("hermes_cli/runtime_provider.py", "7a17fc83943f7b058d6feabf838c60d7c1864a99", "8c1dd09ec4216b43acec739062b35ec6943b2bee0aca405f2a9dec1b57dc7a9b", 98052),
    ("model_tools.py", "32394a69eec64f3d676bedb1659a6f4e94887a74", "db74ee29c8d335d80f3c18cc31f8c441956af956b2ed08e5113ced249fad32b4", 65159),
    ("plugins/security-guidance/__init__.py", "99cc6f725ee750f9283db76ba741227f06ef9487", "4522fb7c315456c3cb062adc310e19ab17d38706a4ee6d36eac432fe53ff6a82", 9739),
    ("plugins/security-guidance/patterns.py", "6980888733c2714a6db3339d47595ce96b4a2ee4", "94fcf9eacea3dbe36dd203e7f4b78191225afc34e06fd0dc3a24cb33ca0da4b4", 18580),
    ("plugins/security-guidance/plugin.yaml", "97567299954b578b15f8508588c7c29cd9f8dd99", "c5832c5fe4c25d0d1dc136622056cef16c3356704d45b59cab63671ae657c557", 626),
    ("providers/__init__.py", "a394e74b335ae25c8344c025a500eebb97d47b2d", "f489370bc5467be9370315b766881081748b72a6356743f38b5adcd5ec3e29e8", 6780),
    ("providers/base.py", "554e01e4f7c77c3f32604a36fe6f94581b9dea27", "90010fe0e5a79349d7f46d399949876649885ab73faa24835c91612aea838801", 9927),
    ("pyproject.toml", "a2a1d6c0ee240044de98b55bf93f7092f6ecef7d", "35462080afc8177258babd430dcdc2ac654fdf69332cc4370fec555295f7eaba", 19582),
    ("run_agent.py", "75846d5bec81f8daaabb742e33642ee97990b425", "f9642ba60a0652f54fecf65d14849a12ca58eedff11926a16ce2215873fa677a", 312947),
)
ALLOWLIST = tuple(item[0] for item in AUTHORITATIVE_PATH_BLOBS)
_LOCK_SCHEMA = "spec034-publication-lock-v2"
_LOCK_PHASES = frozenset({"staging_created", "bundle_renamed", "manifest_written", "validated"})
_STAGE_BASENAME_RE = re.compile(r"^\.[A-Za-z0-9_-]+\.stage-[a-f0-9]{32}$")
_NONCE_RE = re.compile(r"^[a-f0-9]{32}$")


class PublicationCleanupError(RuntimeError):
    """Publication failed and its lock remains for deterministic recovery."""


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _is_reparse_point(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _regular(path: Path) -> bool:
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not _is_reparse_point(info)
    except OSError:
        return False


def _publication_lock_payload(phase: str, staging_basename: str | None = None, protocol_nonce: str | None = None) -> dict[str, str]:
    if phase not in _LOCK_PHASES:
        raise ValueError("unknown_publication_phase")
    nonce = protocol_nonce or secrets.token_hex(16)
    staging = staging_basename or f".{BUNDLE_ROOT.name}.stage-{nonce}"
    if not _NONCE_RE.fullmatch(nonce) or not _STAGE_BASENAME_RE.fullmatch(staging) or Path(staging).name != staging:
        raise ValueError("invalid_publication_lock_identity")
    return {"schema_version": _LOCK_SCHEMA, "phase": phase, "staging_basename": staging, "protocol_nonce": nonce}


def _valid_lock_payload(payload: object) -> bool:
    return (
        isinstance(payload, dict)
        and set(payload) == {"schema_version", "phase", "staging_basename", "protocol_nonce"}
        and payload.get("schema_version") == _LOCK_SCHEMA
        and payload.get("phase") in _LOCK_PHASES
        and isinstance(payload.get("staging_basename"), str)
        and isinstance(payload.get("protocol_nonce"), str)
        and _NONCE_RE.fullmatch(payload["protocol_nonce"]) is not None
        and payload["staging_basename"] == f".{BUNDLE_ROOT.name}.stage-{payload['protocol_nonce']}"
        and _STAGE_BASENAME_RE.fullmatch(payload["staging_basename"]) is not None
    )


def _fsync_parent_best_effort(path: Path) -> None:
    """Persist a replacement's directory entry when this platform permits it."""
    try:
        descriptor = os.open(str(path.parent), getattr(os, "O_DIRECTORY", os.O_RDONLY))
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _write_journal(phase: str, staging_basename: str, protocol_nonce: str, *, exclusive: bool = False) -> None:
    """Commit protocol state by exclusive creation or same-parent atomic replace."""
    payload = (json.dumps(_publication_lock_payload(phase, staging_basename, protocol_nonce), sort_keys=True) + "\n").encode("utf-8")
    if exclusive:
        with PUBLICATION_LOCK_PATH.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
        return
    descriptor, temporary_name = tempfile.mkstemp(
        dir=PUBLICATION_LOCK_PATH.parent,
        prefix=f".{PUBLICATION_LOCK_PATH.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, PUBLICATION_LOCK_PATH)
        _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
    finally:
        temporary.unlink(missing_ok=True)


# Backwards-compatible internal spelling for the initial Task #76 tests.
def _write_lock(phase: str, staging_basename: str, protocol_nonce: str, *, exclusive: bool = False) -> None:
    _write_journal(phase, staging_basename, protocol_nonce, exclusive=exclusive)


def _partial_bundle_is_authoritative() -> bool:
    """Recognize only this protocol's incomplete directory, never an unknown target."""
    try:
        if not BUNDLE_ROOT.is_dir() or BUNDLE_ROOT.is_symlink() or _is_reparse_point(BUNDLE_ROOT.lstat()):
            return False
        found: list[str] = []
        for directory, dirs, files in os.walk(BUNDLE_ROOT, followlinks=False):
            parent = Path(directory)
            if any(not _regular(parent / name) for name in files) or any((parent / name).is_symlink() or _is_reparse_point((parent / name).lstat()) for name in dirs):
                return False
            found.extend((parent / name).relative_to(BUNDLE_ROOT).as_posix() for name in files)
        return tuple(sorted(found)) == ALLOWLIST
    except OSError:
        return False


def _manifest_is_complete(phase: str, nonce: str) -> bool:
    """Use the private validator only for this journal's exact identity."""
    try:
        from podcast_ingest_core.hermes_v019_startup_source_graph import _validate_spec034_source_bundle_internal
        return _validate_spec034_source_bundle_internal(
            journal_phase=phase,
            journal_nonce=nonce,
            bundle_root=BUNDLE_ROOT,
            manifest_path=MANIFEST_PATH,
        ).bundle_valid is True
    except Exception:
        return False


def _owned_staging_directory(staging: Path) -> bool:
    """Accept only a nonce-owned staging tree with no unknown/link entries."""
    try:
        if not (
            staging.parent == BUNDLE_ROOT.parent
            and staging.name.startswith(f".{BUNDLE_ROOT.name}.stage-")
            and staging.is_dir()
            and not staging.is_symlink()
            and not _is_reparse_point(staging.lstat())
        ):
            return False
        found: list[str] = []
        for directory, dirs, files in os.walk(staging, followlinks=False):
            parent = Path(directory)
            if parent.is_symlink() or _is_reparse_point(parent.lstat()):
                return False
            for name in dirs:
                child = parent / name
                if child.is_symlink() or _is_reparse_point(child.lstat()):
                    return False
            for name in files:
                child = parent / name
                if not _regular(child):
                    return False
                found.append(child.relative_to(staging).as_posix())
        return len(found) == len(set(found)) and set(found) <= set(ALLOWLIST)
    except OSError:
        return False


def _remove_owned_directory(directory: Path) -> bool:
    if not _owned_staging_directory(directory) and directory != BUNDLE_ROOT:
        return False
    try:
        shutil.rmtree(directory)
        return True
    except OSError:
        return False


def recover_interrupted_publication() -> bool:
    """Safely finalize or roll back every protocol-owned adjacent crash state.

    A valid journal may lag the actual rename/write state.  Recovery recognizes
    only the nonce-owned staging directory, the exact 20-file bundle, and a
    complete validated manifest.  Any extra, malformed, or ambiguous target is
    retained with its journal so consumers remain blocked.
    """
    if not PUBLICATION_LOCK_PATH.exists():
        return True
    try:
        if not _regular(PUBLICATION_LOCK_PATH):
            return False
        payload = json.loads(PUBLICATION_LOCK_PATH.read_text(encoding="utf-8"))
        if not _valid_lock_payload(payload):
            return False
        staging = BUNDLE_ROOT.parent / payload["staging_basename"]
        if staging.parent != BUNDLE_ROOT.parent:
            return False
        phase = payload["phase"]
        staging_exists = staging.exists()
        bundle_exists = BUNDLE_ROOT.exists()
        manifest_exists = MANIFEST_PATH.exists()
        bundle_owned = bundle_exists and _partial_bundle_is_authoritative()
        manifest_complete = manifest_exists and _manifest_is_complete(phase, payload["protocol_nonce"])

        # Finalize any proven complete publication, even if its journal lags.
        if bundle_owned and manifest_complete and not staging_exists:
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        # Before staging mkdir, exclusive journal only: safe no-op cleanup.
        if phase == "staging_created" and not staging_exists and not bundle_exists and not manifest_exists:
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        # Staging can be partial or complete, but may not coexist with targets.
        if staging_exists and not bundle_exists and not manifest_exists and _owned_staging_directory(staging):
            if not _remove_owned_directory(staging):
                return False
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        # A durable rename journal can survive filesystem metadata loss.  It is
        # retry-safe only for this exact nonce-owned target with neither output;
        # any manifest or ambiguous state remains fail-closed.
        if phase == "bundle_renamed" and not bundle_exists and not staging_exists and not manifest_exists:
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        # Rename can happen while the marker still says staging_created.  The
        # only rollback-able target is the protocol's exact 20-file bundle with
        # no manifest, never a directory that merely resembles it.
        if bundle_owned and not manifest_exists and not staging_exists and phase in {"staging_created", "bundle_renamed"}:
            if not _remove_owned_directory(BUNDLE_ROOT):
                return False
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        # An invalid/partial manifest after rename is safe only to remove with
        # the exact owned bundle, and only when the journal identifies rename.
        if bundle_owned and manifest_exists and not manifest_complete and not staging_exists and phase in {"bundle_renamed", "manifest_written"}:
            if not _regular(MANIFEST_PATH) or not _remove_owned_directory(BUNDLE_ROOT):
                return False
            MANIFEST_PATH.unlink()
            _fsync_parent_best_effort(MANIFEST_PATH)
            PUBLICATION_LOCK_PATH.unlink()
            _fsync_parent_best_effort(PUBLICATION_LOCK_PATH)
            return True
        return False
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return False


def _fetch_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "spec034-static-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200 or response.geturl() != url: raise ValueError("immutable_identity_request_rejected")
        payload = response.read(MAX_FILE_BYTES + 1)
    value = json.loads(payload.decode("utf-8"))
    if type(value) is not dict: raise ValueError("immutable_identity_payload_invalid")
    return value


def _fetch_blob(path: str) -> bytes:
    request = urllib.request.Request(RAW_PREFIX + path, headers={"User-Agent": "spec034-static-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200 or response.geturl() != request.full_url: raise ValueError("immutable_blob_request_rejected")
        data = response.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES: raise ValueError("source_blob_oversized")
    return data


def _acquire() -> dict[str, object]:
    commit = _fetch_json(f"{API_BASE}/commits/{COMMIT}"); tree = commit.get("tree")
    if commit.get("sha") != COMMIT or type(tree) is not dict or tree.get("sha") != TREE_SHA: raise ValueError("commit_tree_identity_mismatch")
    staged: list[tuple[str, bytes]] = []; records: list[dict[str, object]] = []
    for path, blob, digest, length in AUTHORITATIVE_PATH_BLOBS:
        data = _fetch_blob(path)
        if _git_blob_sha(data) != blob or hashlib.sha256(data).hexdigest() != digest or len(data) != length: raise ValueError("immutable_blob_identity_mismatch")
        staged.append((path, data)); records.append({"path": path, "git_blob_sha": blob, "sha256": digest, "byte_length": length})
    return {"schema_version": "spec034-pinned-source-bundle-v1", "repository": REPOSITORY, "pinned_commit": COMMIT, "tree_sha": TREE_SHA, "h1_inventory_sha256": H1_INVENTORY_SHA256, "files": records, "_staged": staged}


def _write_file(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())


def _post_publication_valid(nonce: str) -> bool:
    """Validate the just-written bundle through the journal-bound internal seam."""
    return _manifest_is_complete("manifest_written", nonce)


def _write(bundle: dict[str, object]) -> None:
    staged = bundle.get("_staged")
    BUNDLE_ROOT.parent.mkdir(parents=True, exist_ok=True); MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    nonce = secrets.token_hex(16); staging_name = f".{BUNDLE_ROOT.name}.stage-{nonce}"
    staging = BUNDLE_ROOT.parent / staging_name
    completed = False
    try:
        _write_lock("staging_created", staging_name, nonce, exclusive=True)
        if BUNDLE_ROOT.exists() or MANIFEST_PATH.exists() or staging.exists() or type(staged) is not list or len(staged) != len(ALLOWLIST): raise ValueError("published_target_not_fresh")
        staging.mkdir(exist_ok=False)
        for path, data in staged:
            if path not in ALLOWLIST or type(data) is not bytes: raise ValueError("invalid_staged_entry")
            target = staging / path; target.parent.mkdir(parents=True, exist_ok=True); _write_file(target, data)
        if tuple(sorted(item.relative_to(staging).as_posix() for item in staging.rglob("*") if item.is_file())) != ALLOWLIST: raise ValueError("staging_validation_failed")
        os.rename(staging, BUNDLE_ROOT)
        # Directory rename durability precedes the journal claim.  On Windows a
        # directory fsync may be unavailable; the best-effort helper records
        # that platform fallback while retaining journal ordering.
        _fsync_parent_best_effort(BUNDLE_ROOT)
        _write_lock("bundle_renamed", staging_name, nonce)
        sanitized = {key: value for key, value in bundle.items() if key != "_staged"}
        _write_file(MANIFEST_PATH, (json.dumps(sanitized, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        _write_lock("manifest_written", staging_name, nonce)
        if not _post_publication_valid(nonce): raise ValueError("published_bundle_validation_failed")
        _write_lock("validated", staging_name, nonce)
        completed = True
    finally:
        if completed:
            PUBLICATION_LOCK_PATH.unlink(missing_ok=True)
        elif not recover_interrupted_publication():
            raise PublicationCleanupError("publication_cleanup_failed")


def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if args != ("--write",):
        print(json.dumps({"status": "rejected", "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 2
    try:
        if not recover_interrupted_publication() or BUNDLE_ROOT.exists() or MANIFEST_PATH.exists(): raise ValueError("published_target_not_fresh")
        _write(_acquire()); print(json.dumps({"status": "published", "file_count": len(ALLOWLIST), "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 0
    except Exception:
        print(json.dumps({"status": "BLOCKED_SOURCE_GRAPH", "runtime_status": "not_run", "live_actions_authorized": False}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
