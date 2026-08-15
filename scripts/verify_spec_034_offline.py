"""Unique byte-verified Spec034 final verifier; Main invokes it only after review.

The verifier reads the reviewer-rooted manifest once, verifies each current
artifact against that manifest, and runs only protocol-owned byte snapshots.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/034-hermes-v019-pinned-startup-source-graph"
CAPABILITY_MANIFEST_PATH = SPEC / "contracts/python-test-capability-manifest.json"
REVIEWED_ARTIFACT_PATHS = (
    "src/podcast_ingest_core/hermes_v019_startup_source_graph.py", "src/podcast_ingest_core/artifact_lock.py", "src/podcast_ingest_core/canonical_transcript.py", "src/podcast_ingest_core/config.py", "src/podcast_ingest_core/llm_provider.py", "src/podcast_ingest_core/stock_lens.py", "src/podcast_ingest_core/episode_claim.py", "src/podcast_ingest_core/errors.py", "src/podcast_ingest_core/external_data_boundary.py", "src/podcast_ingest_core/external_data_verification.py", "src/podcast_ingest_core/generation_proof.py", "src/podcast_ingest_core/gooaye_lens.py", "src/podcast_ingest_core/industry_mapping.py", "src/podcast_ingest_core/models.py", "src/podcast_ingest_core/report_safety.py", "src/podcast_ingest_core/secure_local_snapshot.py", "src/podcast_ingest_core/semantic_review_artifact.py", "src/podcast_ingest_core/semantic_summary_identity.py", "src/podcast_ingest_core/semantic_summary_smoke_review.py", "src/podcast_ingest_core/storage.py", "src/podcast_ingest_core/verified_research_lineage.py", "src/podcast_ingest_core/verified_research_report.py",
    "scripts/acquire_spec_034_hermes_source.py", "scripts/validate_spec_034_source_graph.py", "scripts/spec034_offline_runtime_sentinel.py", "scripts/spec034_isolated_pytest_runner.py", "scripts/spec034_trust_launcher.py", "scripts/run_spec_034_final_once.py", "scripts/verify_spec_034_offline.py",
    "tests/__init__.py", "tests/test_hermes_v019_startup_source_graph.py", "tests/test_spec_034_h1_inventory.py", "tests/test_spec_034_h4_repair.py", "tests/test_spec_034_source_graph_docs.py", "tests/spec034_final_c6_support.py", "tests/test_spec_034_verified_report_public_seam_regression.py", "tests/test_spec_034_final_acceptance.py",
    "specs/034-hermes-v019-pinned-startup-source-graph/proposal.md", "specs/034-hermes-v019-pinned-startup-source-graph/spec.md", "specs/034-hermes-v019-pinned-startup-source-graph/plan.md", "specs/034-hermes-v019-pinned-startup-source-graph/tasks.md", "specs/034-hermes-v019-pinned-startup-source-graph/checklists/requirements.md", "specs/034-hermes-v019-pinned-startup-source-graph/checklists/safety.md", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/h1-source-inventory-proposal.json", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/h1-discovery-receipt.json", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/source-bundle-manifest.json", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/predecessor-boundary.json", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/python-test-capability-manifest.json", "specs/034-hermes-v019-pinned-startup-source-graph/contracts/final-invocation.md",
    "config/industry_chain_mappings.yaml", "config/external_data_boundary.yaml", "config/gooaye_lens.yaml", "README.md", "docs/roadmap.md", "docs/verification-matrix.md", "specs/README.md", "pyproject.toml",
)
TARGETS = ("tests/test_spec_034_final_acceptance.py",)
EXPECTED_FINAL_NODE_IDS = (
    "tests/test_spec_034_final_acceptance.py::test_c0_reviewed_artifacts_and_detached_authority_are_current",
    "tests/test_spec_034_final_acceptance.py::test_c1_h2_bundle_is_exactly_twenty_current_literal_records",
    "tests/test_spec_034_final_acceptance.py::test_c2_predecessor_boundary_pins_all_three_current_records",
    "tests/test_spec_034_final_acceptance.py::test_c3_static_receipt_is_closed_only_for_startup_and_plugin",
    "tests/test_spec_034_final_acceptance.py::test_c4_sentinel_and_final_target_are_static_and_closed",
    "tests/test_spec_034_final_acceptance.py::test_c5_public_product_seams_remain_available_without_external_execution",
    "tests/test_spec_034_final_acceptance.py::test_c6_current_docs_preserve_blocked_terminal_and_no_live_claim",
    "tests/test_spec_034_final_acceptance.py::test_c7_final_acceptance_is_the_only_final_child_target",
)
# Forwarded by the verified runner; retained here as final-verifier contract.
PYTEST_ARGUMENTS = ("--noconftest", "-p", "no:cacheprovider")
STATIC_ONLY = ("src/podcast_ingest_core/hermes_v019_startup_source_graph.py", "scripts/acquire_spec_034_hermes_source.py", "scripts/validate_spec_034_source_graph.py", "scripts/spec034_offline_runtime_sentinel.py", "scripts/spec034_isolated_pytest_runner.py", "scripts/spec034_trust_launcher.py", "scripts/verify_spec_034_offline.py")
ROOT_SCHEMA = "spec034-detached-review-root-v8"
MANIFEST_SCHEMA = "spec034-reviewed-artifact-manifest-v8"
CAPABILITY_SCHEMA = "spec034-python-test-capability-manifest-v1"
# Review-approved local verifier capability; this is deliberately not a
# portable runtime dependency declaration.
EXPECTED_CAPABILITY_MANIFEST_SHA256 = "5185a9b618dabdbd9bf815a344037b988d8290aef81666a536c838123bbb3173"
CAPABILITY_DISTRIBUTIONS = ("pytest", "pluggy", "iniconfig", "packaging", "pygments", "colorama", "requests", "urllib3", "certifi", "charset-normalizer", "idna", "pyyaml")
CAPABILITY_TOP_LEVELS = {"pytest": ("pytest",), "pluggy": ("pluggy",), "iniconfig": ("iniconfig",), "packaging": ("packaging",), "pygments": ("pygments",), "colorama": ("colorama",), "requests": ("requests",), "urllib3": ("urllib3",), "certifi": ("certifi",), "charset-normalizer": ("charset_normalizer",), "idna": ("idna",), "pyyaml": ("yaml",)}
SOURCE_BUNDLE_PATH = SPEC / "contracts/source-bundle-manifest.json"
PREDECESSOR_BOUNDARY_PATH = SPEC / "contracts/predecessor-boundary.json"
SPEC033_CONTRACTS = ROOT / "specs/033-hermes-v019-pinned-source-loader-audit/contracts"
EXECUTION_RECORD_CATEGORIES = ("reviewed", "detached", "upstream", "predecessor")
# H2 literal authority is deliberately independent of the mutable source-bundle
# manifest.  The snapshot accepts precisely this 20-file path/blob/SHA/length
# tuple and verifies the manifest agrees before it reads the upstream bytes.
H2_PATH_BLOB_SHA_LENGTH = (
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


@dataclass(frozen=True, slots=True)
class ManifestAuthority:
    """One stable-read detached authority transaction; never self-signed later."""

    records: tuple[dict[str, object], ...]
    capability: dict[str, object]
    root_bytes: bytes
    manifest_bytes: bytes
    approved_root_sha256: str
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """One sealed input copied into the child-owned execution snapshot."""

    category: str
    path: str
    sha256: str
    byte_length: int
    source: Path
    approved_bytes: bytes | None = None


CHILD_ENV_ALLOWLIST = ("COMSPEC", "HOMEDRIVE", "HOMEPATH", "LOCALAPPDATA", "PATH", "PATHEXT", "SystemRoot", "TEMP", "TMP", "USERPROFILE", "WINDIR")


def _minimal_child_env() -> dict[str, str]:
    """Build child startup state from required system variables only."""
    env = {name: os.environ[name] for name in CHILD_ENV_ALLOWLIST if name in os.environ}
    for name in tuple(env):
        if name.startswith("PYTEST_") or name.startswith("PYTHON"):
            del env[name]
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _reparse(info: os.stat_result) -> bool: return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _valid_sha256(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
def _safe_relative(value: object) -> bool:
    return isinstance(value, str) and value and "\\" not in value and not Path(value).is_absolute() and all(part not in ("", ".", "..") for part in value.split("/"))

def _directory_under(path: Path, root: Path) -> bool:
    try:
        root, path = root.absolute(), path.absolute(); relative = path.relative_to(root); current = root
        for part in ("", *relative.parts):
            if part: current /= part
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode) or current.is_symlink() or _reparse(info): return False
        return True
    except (OSError, ValueError): return False

def _is_regular_no_link(path: Path) -> bool:
    """Single leaf seam used by all detached-manifest and snapshot reads."""
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not _reparse(info)
    except OSError:
        return False

def _regular_under(path: Path, root: Path) -> bool:
    try:
        root, path = root.absolute(), path.absolute(); relative = path.relative_to(root); current = root
        root_info = root.lstat()
        if not stat.S_ISDIR(root_info.st_mode) or root.is_symlink() or _reparse(root_info): return False
        for part in relative.parts:
            current /= part; info = current.lstat()
            if current == path:
                return _is_regular_no_link(current)
            if not stat.S_ISDIR(info.st_mode) or current.is_symlink() or _reparse(info): return False
        return False
    except (OSError, ValueError): return False

def _read_under(path: Path, root: Path) -> bytes | None:
    try:
        if not _regular_under(path, root): return None
        before = path.lstat(); data = path.read_bytes(); after = path.lstat()
        stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        return data if stable and _regular_under(path, root) else None
    except OSError: return None

def _read(path: Path) -> bytes | None: return _read_under(path, ROOT)

def _records_valid(records: object, expected_paths: tuple[str, ...] | None = None) -> tuple[dict[str, object], ...] | None:
    if not isinstance(records, list): return None
    result: list[dict[str, object]] = []
    for item in records:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "byte_length"}: return None
        if not _safe_relative(item["path"]) or not _valid_sha256(item["sha256"]) or not isinstance(item["byte_length"], int) or item["byte_length"] < 0: return None
        result.append(item)
    paths = tuple(item["path"] for item in result)
    if len(paths) != len(set(paths)) or (expected_paths is not None and paths != expected_paths): return None
    return tuple(result)

def _capability_manifest_valid(manifest: object) -> bool:
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "distributions"} or manifest.get("schema_version") != CAPABILITY_SCHEMA: return False
    distributions = manifest.get("distributions")
    if not isinstance(distributions, list): return False
    names: list[str] = []
    for distribution in distributions:
        if not isinstance(distribution, dict) or set(distribution) != {"canonical_name", "version", "record", "files", "top_level_modules"}: return False
        name, version, record, files, tops = (distribution[key] for key in ("canonical_name", "version", "record", "files", "top_level_modules"))
        if not isinstance(name, str) or not isinstance(version, str) or not isinstance(record, dict) or not isinstance(tops, list): return False
        if tuple(tops) != CAPABILITY_TOP_LEVELS.get(name, ()) or not all(isinstance(top, str) and top.isidentifier() for top in tops): return False
        if _records_valid(files) is None or set(record) != {"path", "sha256", "byte_length"} or record not in files: return False
        names.append(name)
    return tuple(names) == CAPABILITY_DISTRIBUTIONS

def _manifest_authority(required_root_sha256: str) -> ManifestAuthority | None:
    if not _valid_sha256(required_root_sha256): return None
    manifest_bytes, root_bytes, contract_bytes = (_read(SPEC / "contracts/reviewed-artifact-manifest.json"), _read(SPEC / "contracts/review-root.json"), _read(SPEC / "contracts/final-invocation.md"))
    if manifest_bytes is None or root_bytes is None or contract_bytes is None or _sha(root_bytes) != required_root_sha256: return None
    try:
        manifest, root = json.loads(manifest_bytes.decode("utf-8")), json.loads(root_bytes.decode("utf-8"))
        records = _records_valid(manifest.get("artifacts"), REVIEWED_ARTIFACT_PATHS)
        capability_bytes = _read(CAPABILITY_MANIFEST_PATH)
        capability = json.loads(capability_bytes.decode("utf-8")) if capability_bytes is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError): return None
    if records is None or not _capability_manifest_valid(capability): return None
    if EXPECTED_CAPABILITY_MANIFEST_SHA256 != _sha(capability_bytes): return None
    expected_root = {"schema_version": ROOT_SCHEMA, "reviewed_manifest_sha256": _sha(manifest_bytes), "launcher_contract_sha256": _sha(contract_bytes), "capability_manifest_sha256": _sha(capability_bytes), "capability_distributions": list(CAPABILITY_DISTRIBUTIONS), "bootstrap": next({"sha256": r["sha256"], "byte_length": r["byte_length"]} for r in records if r["path"] == "scripts/run_spec_034_final_once.py"), "final_verifier": next({"sha256": r["sha256"], "byte_length": r["byte_length"]} for r in records if r["path"] == "scripts/verify_spec_034_offline.py"), "isolated_pytest_runner": next({"sha256": r["sha256"], "byte_length": r["byte_length"]} for r in records if r["path"] == "scripts/spec034_isolated_pytest_runner.py")}
    if root != expected_root or manifest.get("schema_version") != MANIFEST_SCHEMA or manifest.get("live_actions_authorized") is not False or manifest.get("review_evidence_included") is not False: return None
    return ManifestAuthority(records, capability, root_bytes, manifest_bytes, required_root_sha256, _sha(manifest_bytes))

def _verified_project_bytes(records: tuple[dict[str, object], ...]) -> tuple[tuple[dict[str, object], bytes], ...] | None:
    verified = []
    for record in records:
        data = _read(ROOT / str(record["path"]))
        if data is None or len(data) != record["byte_length"] or _sha(data) != record["sha256"]: return None
        verified.append((record, data))
    return tuple(verified)

def _execution_record(category: str, path: str, digest: str, length: int, source: Path, approved_bytes: bytes | None = None) -> ExecutionRecord | None:
    if category not in EXECUTION_RECORD_CATEGORIES or not _safe_relative(path) or not _valid_sha256(digest) or not isinstance(length, int) or length < 0:
        return None
    if approved_bytes is not None and (len(approved_bytes) != length or _sha(approved_bytes) != digest): return None
    return ExecutionRecord(category, path, digest, length, source, approved_bytes)


def _execution_records(authority: ManifestAuthority) -> tuple[ExecutionRecord, ...] | None:
    """Build child authority from one detached stable-read transaction."""
    if not _capability_manifest_valid(authority.capability): return None
    reviewed, root_bytes, manifest_bytes = authority.records, authority.root_bytes, authority.manifest_bytes
    source_manifest_bytes = _read(SOURCE_BUNDLE_PATH)
    boundary_bytes = _read(PREDECESSOR_BOUNDARY_PATH)
    if any(data is None for data in (root_bytes, manifest_bytes, source_manifest_bytes, boundary_bytes)):
        return None
    try:
        source_manifest = json.loads(source_manifest_bytes.decode("utf-8"))
        boundary = json.loads(boundary_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    required_source_manifest = {
        "schema_version": "spec034-pinned-source-bundle-v1",
        "repository": "NousResearch/hermes-agent",
        "pinned_commit": "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6",
        "tree_sha": "3ae46c7c1576f9a3450a64729be314ba8e853eac",
        "h1_inventory_sha256": "90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d",
        "runtime_status": "not_run",
        "live_actions_authorized": False,
        "whole_program_source_graph_closed": False,
    }
    files = source_manifest.get("files") if isinstance(source_manifest, dict) else None
    source_tuple = tuple((record.get("path"), record.get("git_blob_sha"), record.get("sha256"), record.get("byte_length")) for record in files) if isinstance(files, list) else ()
    if source_tuple != H2_PATH_BLOB_SHA_LENGTH or any(source_manifest.get(key) != value for key, value in required_source_manifest.items()):
        return None
    predecessor_paths = {
        "spec033_review_root_sha256": "review-root.json",
        "spec033_reviewed_artifact_manifest_sha256": "reviewed-artifact-manifest.json",
        "spec033_source_manifest_sha256": "source-bundle-manifest.json",
    }
    expected_boundary = {
        "schema_version": "spec034-predecessor-boundary-v2",
        "predecessor_spec": "033-hermes-v019-pinned-source-loader-audit",
        "h1_inventory_sha256": required_source_manifest["h1_inventory_sha256"],
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }
    if not isinstance(boundary, dict) or any(boundary.get(key) != value for key, value in expected_boundary.items()) or set(boundary) != set(expected_boundary) | set(predecessor_paths):
        return None
    entries: list[ExecutionRecord] = []
    for record in reviewed:
        source = ROOT / str(record["path"])
        data = _read(source)
        entry = _execution_record("reviewed", str(record["path"]), str(record["sha256"]), int(record["byte_length"]), source, data)
        if entry is None: return None
        entries.append(entry)
    for path, data, source in (
        ("specs/034-hermes-v019-pinned-startup-source-graph/contracts/reviewed-artifact-manifest.json", manifest_bytes, SPEC / "contracts/reviewed-artifact-manifest.json"),
        ("specs/034-hermes-v019-pinned-startup-source-graph/contracts/review-root.json", root_bytes, SPEC / "contracts/review-root.json"),
    ):
        entry = _execution_record("detached", path, _sha(data), len(data), source, data)
        if entry is None: return None
        entries.append(entry)
    for record in files:
        if not isinstance(record, dict) or set(record) != {"path", "git_blob_sha", "sha256", "byte_length"}: return None
        path = str(record["path"]); data = _read(SPEC / "upstream/NousResearch-hermes-agent-b7a05b6" / path)
        blob = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest() if data is not None else None
        if data is None or blob != record["git_blob_sha"]: return None
        entry = _execution_record("upstream", f"specs/034-hermes-v019-pinned-startup-source-graph/upstream/NousResearch-hermes-agent-b7a05b6/{path}", str(record["sha256"]), int(record["byte_length"]), SPEC / "upstream/NousResearch-hermes-agent-b7a05b6" / path, data)
        if entry is None: return None
        entries.append(entry)
    for key, filename in predecessor_paths.items():
        source = SPEC033_CONTRACTS / filename; data = _read(source)
        if data is None or _sha(data) != boundary.get(key): return None
        entry = _execution_record("predecessor", f"specs/033-hermes-v019-pinned-source-loader-audit/contracts/{filename}", _sha(data), len(data), source, data)
        if entry is None: return None
        entries.append(entry)
    paths = tuple(record.path for record in entries)
    return tuple(entries) if len(paths) == len(set(paths)) else None


def _verified_execution_bytes(records: tuple[ExecutionRecord, ...]) -> tuple[tuple[dict[str, object], bytes], ...] | None:
    entries: list[tuple[dict[str, object], bytes]] = []
    for record in records:
        data = record.approved_bytes if record.approved_bytes is not None else _read(record.source)
        if data is None or len(data) != record.byte_length or _sha(data) != record.sha256: return None
        entries.append(({"path": record.path, "sha256": record.sha256, "byte_length": record.byte_length}, data))
    return tuple(entries)


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle: os.fsync(handle.fileno())

def _write_snapshot_file(root: Path, relative: str, data: bytes) -> None:
    destination = root.joinpath(*relative.split("/")); parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    if not _directory_under(parent, root): raise OSError("unsafe snapshot directory")
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
    except BaseException:
        try: destination.unlink()
        except OSError: pass
        raise

def _create_snapshot(prefix: str, entries: tuple[tuple[dict[str, object], bytes], ...]) -> Path:
    root = Path(tempfile.mkdtemp(prefix=prefix, dir=ROOT.parent))
    try:
        for record, data in entries: _write_snapshot_file(root, str(record["path"]), data)
        records = tuple(record for record, _data in entries)
        if not _snapshot_exact(root, records): raise OSError("snapshot verification failed")
        return root
    except BaseException:
        _remove_snapshot(root); raise

def _create_project_snapshot(records: tuple[dict[str, object], ...]) -> Path:
    verified = _verified_project_bytes(records)
    if verified is None: raise OSError("project artifact verification failed")
    return _create_snapshot(".spec034-project-", verified)


def _create_execution_snapshot(records: tuple[ExecutionRecord, ...]) -> Path:
    verified = _verified_execution_bytes(records)
    if verified is None: raise OSError("execution authority verification failed")
    return _create_snapshot(".spec034-execution-", verified)


def _execution_snapshot_exact(root: Path, records: tuple[ExecutionRecord, ...]) -> bool:
    projected = tuple({"path": record.path, "sha256": record.sha256, "byte_length": record.byte_length} for record in records)
    return _snapshot_exact(root, projected)

def _snapshot_exact(root: Path, records: tuple[dict[str, object], ...]) -> bool:
    expected = {str(item["path"]) for item in records}
    if not _directory_under(root, root): return False
    actual: set[str] = set()
    try:
        for directory, dirs, files in os.walk(root, followlinks=False):
            parent = Path(directory)
            if not _directory_under(parent, root) or any(not _directory_under(parent / name, root) for name in dirs): return False
            for name in files:
                path = parent / name
                if not _regular_under(path, root): return False
                actual.add(path.relative_to(root).as_posix())
    except OSError: return False
    if actual != expected: return False
    for record in records:
        data = _read_under(root / str(record["path"]), root)
        if data is None or len(data) != record["byte_length"] or _sha(data) != record["sha256"]: return False
    return True

def _remove_snapshot(path: Path) -> bool:
    try:
        if path.exists(): shutil.rmtree(path)
        return not path.exists()
    except OSError: return False

def _approved_capability_bytes(capability: dict[str, object]) -> tuple[tuple[dict[str, object], bytes], ...] | None:
    purelib = Path(sysconfig.get_paths()["purelib"])
    if not _directory_under(purelib, purelib): return None
    entries: list[tuple[dict[str, object], bytes]] = []
    for distribution in capability["distributions"]:
        for record in distribution["files"]:
            data = _read_under(purelib / record["path"], purelib)
            if data is None or len(data) != record["byte_length"] or _sha(data) != record["sha256"]: return None
            entries.append((record, data))
    paths = [str(record["path"]) for record, _data in entries]
    return tuple(entries) if len(paths) == len(set(paths)) else None

def _create_capability_snapshot(capability: dict[str, object]) -> tuple[Path, tuple[dict[str, object], ...]]:
    entries = _approved_capability_bytes(capability)
    if entries is None: raise OSError("approved Python capability unavailable or drifted")
    return _create_snapshot(".spec034-capability-", entries), tuple(record for record, _data in entries)

def _seal_valid(required_review_root_sha256: str) -> bool:
    authority = _manifest_authority(required_review_root_sha256)
    if authority is None or tuple(path for path in REVIEWED_ARTIFACT_PATHS if path in STATIC_ONLY) != STATIC_ONLY: return False
    return _verified_project_bytes(authority.records) is not None


def _post_child_current_authority_valid(authority: ManifestAuthority) -> bool:
    """Reject permanent post-child drift; snapshots alone never authorize success."""
    current = _manifest_authority(authority.approved_root_sha256)
    if current is None or current != authority: return False
    execution_records = _execution_records(current)
    return _verified_project_bytes(authority.records) is not None and execution_records is not None and _verified_execution_bytes(execution_records) is not None and _approved_capability_bytes(authority.capability) is not None

def _isolated_pytest_payload(project: Path, execution_records: tuple[ExecutionRecord, ...], capability: Path, capability_records: tuple[dict[str, object], ...], runner: bytes, sentinel: bytes) -> bytes:
    project_records = tuple({"path": record.path, "sha256": record.sha256, "byte_length": record.byte_length} for record in execution_records)
    payload = {"project_snapshot": str(project), "project_records": list(project_records), "execution_records": [{"category": record.category, "path": record.path, "sha256": record.sha256, "byte_length": record.byte_length} for record in execution_records], "capability_snapshot": str(capability), "capability_records": list(capability_records), "targets": list(TARGETS), "expected_node_ids": list(EXPECTED_FINAL_NODE_IDS), "cwd": str(project), "sentinel": {"module": "spec034_sealed_sentinel", "bytes_b64": base64.b64encode(sentinel).decode("ascii"), "sha256": _sha(sentinel), "byte_length": len(sentinel)}, "approved_top_levels": sorted({top for names in CAPABILITY_TOP_LEVELS.values() for top in names})}
    return json.dumps({"runner_b64": base64.b64encode(runner).decode("ascii"), "payload": payload}, sort_keys=True).encode("utf-8")

_ISOLATED_CHILD_EXEC_RUNNER = """
import base64, hashlib, json, sys
packet = json.loads(sys.stdin.buffer.read().decode('utf-8'))
runner = base64.b64decode(packet['runner_b64'].encode('ascii'), validate=True)
if len(runner) != int(sys.argv[2]) or hashlib.sha256(runner).hexdigest() != sys.argv[1]: raise SystemExit('unapproved isolated pytest runner bytes')
globals_dict = {'__name__': '__main__', '__file__': 'spec034-approved/spec034_isolated_pytest_runner.py', '__package__': None, '__builtins__': __builtins__}
exec(compile(runner, globals_dict['__file__'], 'exec'), globals_dict, globals_dict)
raise SystemExit(globals_dict['run'](packet['payload']))
"""
def _sealed_pytest_command(runner: bytes) -> tuple[str, ...]: return (sys.executable, "-I", "-S", "-c", _ISOLATED_CHILD_EXEC_RUNNER, _sha(runner), str(len(runner)))

def main(argv: object = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if os.environ.get("PYTHONOPTIMIZE") is not None or len(args) != 2 or args[0] != "--review-root-sha256": return 2
    authority = _manifest_authority(args[1])
    if authority is None: return 1
    capability_manifest = authority.capability
    snapshots: list[Path] = []
    try:
        # Read each workspace artifact once against its detached-manifest record.
        # All executable/importable bytes below come from this verified cache or
        # the exact project snapshot, never an unverified current pathname read.
        execution_records = _execution_records(authority)
        if execution_records is None: return 1
        project = _create_execution_snapshot(execution_records); snapshots.append(project)
        capability, capability_records = _create_capability_snapshot(capability_manifest); snapshots.append(capability)
        runner_record = next(record for record in execution_records if record.path == "scripts/spec034_isolated_pytest_runner.py")
        sentinel_record = next(record for record in execution_records if record.path == "scripts/spec034_offline_runtime_sentinel.py")
        runner = _read_under(project / runner_record.path, project)
        if runner is None or len(runner) != runner_record.byte_length or _sha(runner) != runner_record.sha256: return 1
        if not _execution_snapshot_exact(project, execution_records) or not _snapshot_exact(capability, capability_records): return 1
        sentinel = _read_under(project / sentinel_record.path, project)
        if sentinel is None or len(sentinel) != sentinel_record.byte_length or _sha(sentinel) != sentinel_record.sha256: return 1
        completed = subprocess.run(_sealed_pytest_command(runner), cwd=ROOT, env=_minimal_child_env(), input=_isolated_pytest_payload(project, execution_records, capability, capability_records, runner, sentinel), check=False)
        return 0 if completed.returncode == 0 and _post_child_current_authority_valid(authority) and _execution_snapshot_exact(project, execution_records) and _snapshot_exact(capability, capability_records) else 1
    except (OSError, StopIteration): return 1
    finally:
        if any(not _remove_snapshot(snapshot) for snapshot in snapshots): return 1

if __name__ == "__main__": raise SystemExit(main())
