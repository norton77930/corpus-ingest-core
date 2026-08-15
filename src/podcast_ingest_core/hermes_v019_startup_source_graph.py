"""Static-only Spec034 Hermes v0.19 startup-source graph audit.

Bundled upstream files are handled only as canonical bytes.  Nothing in this
module imports, compiles, or executes Hermes source.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import weakref

SPEC_ID = "034-hermes-v019-pinned-startup-source-graph"
SPEC_ROOT = Path(__file__).resolve().parents[2] / "specs" / SPEC_ID
BUNDLE_ROOT = SPEC_ROOT / "upstream" / "NousResearch-hermes-agent-b7a05b6"
SOURCE_MANIFEST_PATH = SPEC_ROOT / "contracts" / "source-bundle-manifest.json"
H1_INVENTORY_PATH = SPEC_ROOT / "contracts" / "h1-source-inventory-proposal.json"
PREDECESSOR_BOUNDARY_PATH = SPEC_ROOT / "contracts" / "predecessor-boundary.json"
PUBLICATION_LOCK_PATH = SPEC_ROOT / "contracts" / ".spec034-source-publication.lock"
PINNED_H1_INVENTORY_SHA256 = "90ba45ccf11bbcbf446f7d16904964073e84837a04aaaa0c6f4887d3ea75109d"
REPOSITORY = "NousResearch/hermes-agent"
PINNED_COMMIT = "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
PINNED_TREE_SHA = "3ae46c7c1576f9a3450a64729be314ba8e853eac"
_PUBLICATION_LOCK_SCHEMA = "spec034-publication-lock-v2"
_PUBLICATION_LOCK_PHASES = frozenset({"staging_created", "bundle_renamed", "manifest_written", "validated"})

# H2 literal authority; it is not derived from H1 or a mutable manifest.
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
CLAIM_ORDER = ("startup_source_ordering", "credential_provider_boundary", "security_guidance_plugin")
_ALLOWED_STATUSES = frozenset({"SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED", "BLOCKED_SOURCE_GRAPH"})


@dataclass(frozen=True, slots=True)
class RequiredH2Edge:
    """One exact H1 inventory proof edge, including its owner-local predicate."""

    edge_id: str
    claim: str
    source: str
    owner: str
    target: str
    pattern: str
    required_bytes: bytes
    replacement_bytes: bytes


# These are the 8 + 6 H1-required edges that must each independently block their
# claim when missing.  Generic loader naming never substitutes for a fixed edge.
REQUIRED_H2_EDGES = (
    RequiredH2Edge("startup.run_agent.env_loader", "startup_source_ordering", "run_agent.py", "module", "hermes_cli/env_loader.py", "literal_import", b"from hermes_cli.env_loader import load_hermes_dotenv", b"from hermes_cli.env_loader import load_removed"),
    RequiredH2Edge("startup.run_agent.process_bootstrap", "startup_source_ordering", "run_agent.py", "module", "agent/process_bootstrap.py", "literal_import", b"from agent.process_bootstrap import (", b"from agent.removed_bootstrap import ("),
    RequiredH2Edge("startup.run_agent.model_tools", "startup_source_ordering", "run_agent.py", "module", "model_tools.py", "literal_import", b"from model_tools import (", b"from missing_tools import ("),
    RequiredH2Edge("startup.main.env_loader", "startup_source_ordering", "hermes_cli/main.py", "module", "hermes_cli/env_loader.py", "literal_import", b"from hermes_cli.env_loader import load_hermes_dotenv", b"from hermes_cli.env_loader import load_removed"),
    RequiredH2Edge("startup.main.config", "startup_source_ordering", "hermes_cli/main.py", "_prepare_agent_startup", "hermes_cli/config.py", "literal_import", b"    try:\n        from hermes_cli.config import load_config\n        from agent.shell_hooks", b"    try:\n        from hermes_cli.config import load_removed\n        from agent.shell_hooks"),
    RequiredH2Edge("startup.main.plugins", "startup_source_ordering", "hermes_cli/main.py", "_prepare_agent_startup", "hermes_cli/plugins.py", "literal_import", b"    _accept_hooks = bool(getattr(args, \"accept_hooks\", False))\n    try:\n        from hermes_cli.plugins import discover_plugins\n\n        discover_plugins()", b"    _accept_hooks = bool(getattr(args, \"accept_hooks\", False))\n    try:\n        from hermes_cli.plugins import discover_removed\n\n        discover_removed()"),
    RequiredH2Edge("startup.main.shell_hooks", "startup_source_ordering", "hermes_cli/main.py", "_prepare_agent_startup", "agent/shell_hooks.py", "literal_import", b"from agent.shell_hooks import register_from_config\n\n        register_from_config", b"from agent.shell_hooks import register_removed\n\n        register_removed"),
    RequiredH2Edge("startup.model_tools.plugins", "startup_source_ordering", "model_tools.py", "module", "hermes_cli/plugins.py", "literal_import_and_call", b"from hermes_cli.plugins import discover_plugins\n    discover_plugins()", b"from hermes_cli.plugins import discover_removed\n    discover_removed()"),
    RequiredH2Edge("plugin.main.plugins", "security_guidance_plugin", "hermes_cli/main.py", "_prepare_agent_startup", "hermes_cli/plugins.py", "literal_import", b"from hermes_cli.plugins import discover_plugins\n\n        discover_plugins()", b"from hermes_cli.plugins import discover_removed\n\n        discover_removed()"),
    RequiredH2Edge("plugin.oneshot.plugins", "security_guidance_plugin", "hermes_cli/oneshot.py", "_validate_explicit_toolsets", "hermes_cli/plugins.py", "literal_import_and_call", b"from hermes_cli.plugins import discover_plugins\n\n            discover_plugins()", b"from hermes_cli.plugins import discover_removed\n\n            discover_removed()"),
    RequiredH2Edge("plugin.model_tools.plugins", "security_guidance_plugin", "model_tools.py", "module", "hermes_cli/plugins.py", "literal_import_and_call", b"from hermes_cli.plugins import discover_plugins\n    discover_plugins()", b"from hermes_cli.plugins import discover_removed\n    discover_removed()"),
    RequiredH2Edge("plugin.bundled_selection", "security_guidance_plugin", "hermes_cli/plugins.py", "PluginManager._load_plugin", "plugins/security-guidance/__init__.py", "bundled_selection", b'manifest.source in {"user", "project", "bundled"}', b'manifest.source in {"user", "project"}'),
    RequiredH2Edge("plugin.manifest_entrypoint", "security_guidance_plugin", "plugins/security-guidance/plugin.yaml", "manifest", "plugins/security-guidance/__init__.py", "manifest_entrypoint", b"name: security-guidance", b"name: another-plugin"),
    RequiredH2Edge("plugin.patterns_import", "security_guidance_plugin", "plugins/security-guidance/__init__.py", "module", "plugins/security-guidance/patterns.py", "literal_import", b"from . import patterns as _patterns", b"from . import missing_patterns as _patterns"),
)


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class SourceCatalogDecision:
    status: str; bundle_valid: bool; reason: str; runtime_status: str; live_actions_authorized: bool; _factory_token: object
    def __init__(self, *_args: object, **_kwargs: object) -> None: raise TypeError("SourceCatalogDecision is factory-issued only")


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class StartupGraphDecision:
    status: str; claim_graph_status: str; claim_statuses: tuple[str, str, str]
    claim_details: tuple[tuple[str, bool, str, tuple[str, ...]], ...]
    whole_program_source_graph_closed: bool; startup_order_status: str; config_status: str; credential_status: str; provider_status: str; runtime_status: str; live_actions_authorized: bool; _factory_token: object
    def __init__(self, *_args: object, **_kwargs: object) -> None: raise TypeError("StartupGraphDecision is factory-issued only")


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class BundledPluginDecision:
    status: str; registration_status: str; actual_activation_observed: bool; dynamic_plugin_status: str; runtime_status: str; live_actions_authorized: bool; _factory_token: object
    def __init__(self, *_args: object, **_kwargs: object) -> None: raise TypeError("BundledPluginDecision is factory-issued only")


def _make_authority():
    issued: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]] = weakref.WeakKeyDictionary()
    fields = ("status", "bundle_valid", "reason", "runtime_status", "live_actions_authorized")
    reasons = frozenset({"publication_recovery_pending", "source_bundle_unavailable", "source_bundle_nonregular_entry", "bundle_filesystem_allowlist_mismatch", "bundle_identity_mismatch", "source_manifest_mismatch", "source_integrity_mismatch", "inventory_digest_mismatch", "predecessor_identity_mismatch", "validated"})
    def issue(status: str, valid: bool, reason: str) -> SourceCatalogDecision:
        if status not in _ALLOWED_STATUSES or type(valid) is not bool or reason not in reasons or valid != (status == "SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED") or (valid != (reason == "validated")): raise TypeError("invalid source catalog facts")
        value = object.__new__(SourceCatalogDecision); token = object(); facts = (status, valid, reason, "not_run", False)
        for field, fact in zip(fields, facts, strict=True): object.__setattr__(value, field, fact)
        object.__setattr__(value, "_factory_token", token); issued[value] = (token, facts); return value
    def valid(value: object) -> bool:
        try: token, facts = issued[value]; return type(value) is SourceCatalogDecision and object.__getattribute__(value, "_factory_token") is token and facts == tuple(object.__getattribute__(value, x) for x in fields)
        except (KeyError, TypeError, AttributeError): return False
    return issue, valid


def _make_graph_authority():
    issued: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]] = weakref.WeakKeyDictionary(); pairs: weakref.WeakKeyDictionary[object, object] = weakref.WeakKeyDictionary(); graph_bundles: weakref.WeakKeyDictionary[object, object] = weakref.WeakKeyDictionary(); graph_fingerprints: weakref.WeakKeyDictionary[object, str | None] = weakref.WeakKeyDictionary()
    graph_fields = ("status", "claim_graph_status", "claim_statuses", "claim_details", "whole_program_source_graph_closed", "startup_order_status", "config_status", "credential_status", "provider_status", "runtime_status", "live_actions_authorized")
    plugin_fields = ("status", "registration_status", "actual_activation_observed", "dynamic_plugin_status", "runtime_status", "live_actions_authorized")
    def issue(cls: type, fields: tuple[str, ...], facts: tuple[object, ...], parent: object | None = None):
        if type(facts[0]) is not str or facts[0] not in _ALLOWED_STATUSES or facts[-2:] != ("not_run", False): raise TypeError("invalid static graph facts")
        value = object.__new__(cls); token = object()
        for field, fact in zip(fields, facts, strict=True): object.__setattr__(value, field, fact)
        object.__setattr__(value, "_factory_token", token); issued[value] = (token, facts)
        if parent is not None: pairs[value] = parent
        return value
    def current(value: object, cls: type, fields: tuple[str, ...]) -> bool:
        try: token, facts = issued[value]; return type(value) is cls and object.__getattribute__(value, "_factory_token") is token and facts == tuple(object.__getattribute__(value, field) for field in fields)
        except (KeyError, TypeError, AttributeError): return False
    def graph(parent: SourceCatalogDecision) -> StartupGraphDecision:
        """Issue only facts recomputed from the current canonical source."""
        source = _validated_bytes() if _DECISION_AUTHORITY.catalog_issued(parent) and parent.bundle_valid else None
        details = (
            _claim_details(source)
            if source is not None
            else tuple((name, False, "BLOCKED_SOURCE_GRAPH", ("canonical_evidence_unavailable",)) for name in CLAIM_ORDER)
        )
        statuses = tuple(item[2] for item in details)
        complete = all(item[1] for item in details)
        facts = (
            "SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED" if complete else "BLOCKED_SOURCE_GRAPH",
            "STATIC_SOURCE_GRAPH_CLOSED" if complete else "BLOCKED_SOURCE_GRAPH",
            statuses, details, False,
            "bounded_source_order_verified" if details[0][1] else "blocked",
            "source_level_only",
            "source_level_only" if details[1][1] else "blocked",
            "source_level_only" if details[1][1] else "blocked", "not_run", False,
        )
        value = issue(StartupGraphDecision, graph_fields, facts)
        graph_bundles[value] = parent
        graph_fingerprints[value] = _evidence_fingerprint()
        return value
    def plugin(bundle: SourceCatalogDecision, parent: StartupGraphDecision) -> BundledPluginDecision:
        """Issue plugin facts only after current provenance revalidation."""
        try:
            require(bundle, parent)
        except TypeError:
            return issue(BundledPluginDecision, plugin_fields, ("BLOCKED_SOURCE_GRAPH", "blocked", False, "BLOCKED_DYNAMIC_PLUGIN_TARGET", "not_run", False), parent)
        plugin_detail = next(item for item in parent.claim_details if item[0] == "security_guidance_plugin")
        return issue(BundledPluginDecision, plugin_fields, (
            "SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED" if plugin_detail[1] else "BLOCKED_SOURCE_GRAPH",
            "conditional_registration_path_verified" if plugin_detail[1] else "blocked",
            False, "BLOCKED_DYNAMIC_PLUGIN_TARGET", "not_run", False,
        ), parent)
    def require(bundle: object, graph: object, plugin: object | None = None) -> None:
        if not _DECISION_AUTHORITY.catalog_issued(bundle) or not current(graph, StartupGraphDecision, graph_fields) or graph_bundles.get(graph) is not bundle or graph_fingerprints.get(graph) != _evidence_fingerprint(): raise TypeError("factory-issued decisions required")
        if plugin is not None and (not current(plugin, BundledPluginDecision, plugin_fields) or pairs.get(plugin) is not graph): raise TypeError("decision provenance mismatch")
    return graph, plugin, require


class _DecisionAuthority:
    """Module-private issuer facade; public functions cannot inject its seams."""

    __slots__ = ("catalog_issue", "catalog_issued", "graph_issue", "plugin_issue", "require_pair")

    def __init__(self) -> None:
        self.catalog_issue, self.catalog_issued = _make_authority()
        self.graph_issue, self.plugin_issue, self.require_pair = _make_graph_authority()


_DECISION_AUTHORITY = _DecisionAuthority()
del _make_authority, _make_graph_authority


def _git_blob_sha(data: bytes) -> str: return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
def _is_reparse_point(info: os.stat_result) -> bool: return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
def _entry_is_regular_no_link(path: Path) -> bool:
    try:
        info = path.lstat(); return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not _is_reparse_point(info)
    except OSError: return False
def _directory_is_no_link(path: Path) -> bool:
    try:
        info = path.lstat(); return stat.S_ISDIR(info.st_mode) and not path.is_symlink() and not _is_reparse_point(info)
    except OSError: return False

def _canonical_path_under(path: Path, expected_root: Path) -> bool:
    """Reject every linked/reparse ancestor from a trusted lexical root to leaf."""
    try:
        root = expected_root.absolute()
        candidate = path.absolute()
        relative = candidate.relative_to(root)
        current = root
        if not _directory_is_no_link(current):
            return False
        for part in relative.parts[:-1]:
            current /= part
            if not _directory_is_no_link(current):
                return False
        return _entry_is_regular_no_link(candidate)
    except (OSError, ValueError):
        return False

def _read_regular_bytes(path: Path, *, expected_root: Path | None = None) -> bytes | None:
    """Read once only if link/reparse/type/identity remains canonical across it."""
    try:
        if expected_root is not None and not _canonical_path_under(path, expected_root):
            return None
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or path.is_symlink() or _is_reparse_point(before):
            return None
        data = path.read_bytes(); after = path.lstat()
        if expected_root is not None and not _canonical_path_under(path, expected_root):
            return None
        if not stat.S_ISREG(after.st_mode) or path.is_symlink() or _is_reparse_point(after):
            return None
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns): return None
        return data
    except OSError: return None

def _manifest_matches(data: bytes | None = None) -> bool:
    try:
        raw = data if data is not None else _read_regular_bytes(SOURCE_MANIFEST_PATH)
        if raw is None: return False
        manifest = json.loads(raw.decode("utf-8")); records = manifest.get("files")
        expected = [(p, b, d, l) for p, b, d, l in AUTHORITATIVE_PATH_BLOBS]
        actual = [(x.get("path"), x.get("git_blob_sha"), x.get("sha256"), x.get("byte_length")) for x in records] if type(records) is list else []
        return manifest.get("schema_version") == "spec034-pinned-source-bundle-v1" and manifest.get("repository") == REPOSITORY and manifest.get("pinned_commit") == PINNED_COMMIT and manifest.get("tree_sha") == PINNED_TREE_SHA and manifest.get("h1_inventory_sha256") == PINNED_H1_INVENTORY_SHA256 and actual == expected
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError): return False

def _sha(path: Path) -> str | None:
    raw = _read_regular_bytes(path, expected_root=SPEC_ROOT.parent.parent); return hashlib.sha256(raw).hexdigest() if raw is not None else None

def _predecessor_boundary_matches() -> bool:
    workspace_root = SPEC_ROOT.parent.parent
    paths = {
        "spec033_review_root_sha256": SPEC_ROOT.parent / "033-hermes-v019-pinned-source-loader-audit/contracts/review-root.json",
        "spec033_reviewed_artifact_manifest_sha256": SPEC_ROOT.parent / "033-hermes-v019-pinned-source-loader-audit/contracts/reviewed-artifact-manifest.json",
        "spec033_source_manifest_sha256": SPEC_ROOT.parent / "033-hermes-v019-pinned-source-loader-audit/contracts/source-bundle-manifest.json",
    }
    try:
        raw = _read_regular_bytes(PREDECESSOR_BOUNDARY_PATH, expected_root=workspace_root)
        if raw is None: return False
        boundary = json.loads(raw.decode("utf-8"))
        expected = {key: _sha(path) for key, path in paths.items()}
        return all(value is not None for value in expected.values()) and boundary == {"schema_version": "spec034-predecessor-boundary-v2", "predecessor_spec": "033-hermes-v019-pinned-source-loader-audit", "h1_inventory_sha256": PINNED_H1_INVENTORY_SHA256, **expected, "runtime_status": "not_run", "live_actions_authorized": False}
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError): return False

def _protocol_owned_validation_lock(expected_phase: str, expected_nonce: str, expected_bundle: Path, expected_manifest: Path) -> bool:
    """Recognize only the caller's current protocol journal, never an ambient lock."""
    if expected_phase not in _PUBLICATION_LOCK_PHASES or not isinstance(expected_nonce, str) or len(expected_nonce) != 32:
        return False
    if expected_bundle != BUNDLE_ROOT or expected_manifest != SOURCE_MANIFEST_PATH:
        return False
    raw = _read_regular_bytes(PUBLICATION_LOCK_PATH, expected_root=SPEC_ROOT.parent.parent)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, dict)
        and set(payload) == {"schema_version", "phase", "staging_basename", "protocol_nonce"}
        and payload.get("schema_version") == _PUBLICATION_LOCK_SCHEMA
        and payload.get("phase") == expected_phase
        and payload.get("protocol_nonce") == expected_nonce
        and payload.get("staging_basename") == f".{BUNDLE_ROOT.name}.stage-{expected_nonce}"
    )


def _validate_spec034_source_bundle_internal(*, journal_phase: str, journal_nonce: str, bundle_root: Path, manifest_path: Path) -> SourceCatalogDecision:
    """Validate only while holding the exact protocol-owned journal identity."""
    if not _protocol_owned_validation_lock(journal_phase, journal_nonce, bundle_root, manifest_path):
        return _blocked("publication_recovery_pending")
    return _validate_spec034_source_bundle(lock_permitted=True)


def validate_spec034_source_bundle() -> SourceCatalogDecision:
    """Public validation always fails closed while any publication lock exists."""
    return _validate_spec034_source_bundle(lock_permitted=False)


def _validate_spec034_source_bundle(*, lock_permitted: bool) -> SourceCatalogDecision:
    """Validate the H2-frozen 20-file bundle and all canonical authorities."""
    workspace_root = SPEC_ROOT.parent.parent
    if PUBLICATION_LOCK_PATH.exists() and not lock_permitted:
        return _blocked("publication_recovery_pending")
    inventory = _read_regular_bytes(H1_INVENTORY_PATH, expected_root=workspace_root)
    if inventory is None or hashlib.sha256(inventory).hexdigest() != PINNED_H1_INVENTORY_SHA256: return _blocked("inventory_digest_mismatch")
    if not _predecessor_boundary_matches(): return _blocked("predecessor_identity_mismatch")
    if not _directory_is_no_link(BUNDLE_ROOT) or not _entry_is_regular_no_link(SOURCE_MANIFEST_PATH) or not _canonical_path_under(BUNDLE_ROOT / ALLOWLIST[0], workspace_root) or not _canonical_path_under(SOURCE_MANIFEST_PATH, workspace_root): return _blocked("source_bundle_unavailable")
    try:
        actual: list[str] = []
        for directory, dirs, files in os.walk(BUNDLE_ROOT, followlinks=False):
            parent = Path(directory)
            if not _directory_is_no_link(parent) or any(not _directory_is_no_link(parent / name) for name in dirs) or any(not _entry_is_regular_no_link(parent / name) for name in files): return _blocked("source_bundle_nonregular_entry")
            actual.extend((parent / name).relative_to(BUNDLE_ROOT).as_posix() for name in files)
    except OSError: return _blocked("source_bundle_nonregular_entry")
    if tuple(sorted(actual)) != ALLOWLIST: return _blocked("bundle_filesystem_allowlist_mismatch")
    manifest = _read_regular_bytes(SOURCE_MANIFEST_PATH)
    if not _manifest_matches(manifest): return _blocked("source_manifest_mismatch")
    for path, blob, digest, length in AUTHORITATIVE_PATH_BLOBS:
        data = _read_regular_bytes(BUNDLE_ROOT / path, expected_root=workspace_root)
        if data is None or len(data) != length or _git_blob_sha(data) != blob or hashlib.sha256(data).hexdigest() != digest: return _blocked("source_integrity_mismatch")
    # A second authoritative read closes pathname replacement between checks.
    if _read_regular_bytes(H1_INVENTORY_PATH, expected_root=workspace_root) != inventory or _read_regular_bytes(SOURCE_MANIFEST_PATH, expected_root=workspace_root) != manifest: return _blocked("source_integrity_mismatch")
    return _DECISION_AUTHORITY.catalog_issue("SPEC034_STATIC_SOURCE_GRAPH_AUDIT_IMPLEMENTED", True, "validated")

def _blocked(reason: str) -> SourceCatalogDecision: return _DECISION_AUTHORITY.catalog_issue("BLOCKED_SOURCE_GRAPH", False, reason)

def _validated_bytes() -> dict[str, bytes] | None:
    if not validate_spec034_source_bundle().bundle_valid: return None
    source: dict[str, bytes] = {}
    workspace_root = SPEC_ROOT.parent.parent
    for path, blob, digest, length in AUTHORITATIVE_PATH_BLOBS:
        data = _read_regular_bytes(BUNDLE_ROOT / path, expected_root=workspace_root)
        if data is None or len(data) != length or _git_blob_sha(data) != blob or hashlib.sha256(data).hexdigest() != digest: return None
        source[path] = data
    if not validate_spec034_source_bundle().bundle_valid: return None
    return source

def _evidence_fingerprint() -> str | None:
    source = _validated_bytes()
    if source is None: return None
    workspace_root = SPEC_ROOT.parent.parent
    parts = [_read_regular_bytes(H1_INVENTORY_PATH, expected_root=workspace_root), _read_regular_bytes(SOURCE_MANIFEST_PATH, expected_root=workspace_root), _read_regular_bytes(PREDECESSOR_BOUNDARY_PATH, expected_root=workspace_root), *[source[path] for path in ALLOWLIST]]
    return None if any(item is None for item in parts) else hashlib.sha256(b"".join(hashlib.sha256(item).digest() for item in parts if item is not None)).hexdigest()

def _module_name(path: str) -> str: return path.removesuffix("/__init__.py").removesuffix(".py").replace("/", ".").replace("security-guidance", "security_guidance")
def _owner(tree: ast.Module, owner: str) -> ast.AST | None:
    if owner == "module": return tree
    return next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == owner), None)
def _class_owner(tree: ast.Module, klass: str, method: str) -> ast.AST | None:
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass), None)
    return next((n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method), None) if cls else None
def _walk_owned(node: ast.AST, root: ast.AST):
    if node is not root and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)): return
    yield node
    for child in ast.iter_child_nodes(node): yield from _walk_owned(child, root)
def _call_name(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None
def _owned_calls(source: bytes, function_name: str) -> set[str]:
    try: owner = _owner(ast.parse(source.decode("utf-8")), function_name)
    except (UnicodeDecodeError, SyntaxError): return set()
    return {_call_name(node) for node in _walk_owned(owner, owner) if isinstance(node, ast.Call) and _call_name(node) is not None} if owner else set()
def _class_owned_calls(source: bytes, class_name: str, function_name: str) -> set[str]:
    try: owner = _class_owner(ast.parse(source.decode("utf-8")), class_name, function_name)
    except (UnicodeDecodeError, SyntaxError): return set()
    return {_call_name(node) for node in _walk_owned(owner, owner) if isinstance(node, ast.Call) and _call_name(node) is not None} if owner else set()

def _required_edge_reasons(source: bytes, owner_name: str, target: str) -> tuple[str, ...]:
    """Accept one direct literal import only; required dynamic/wildcard edges block."""
    try: owner = _owner(ast.parse(source.decode("utf-8")), owner_name)
    except (UnicodeDecodeError, SyntaxError): return ("required_edge_parse_failure",)
    if owner is None: return ("required_edge_owner_missing",)
    wanted = _module_name(target); found = False; suspect: list[str] = []
    for node in _walk_owned(owner, owner):
        if isinstance(node, ast.Import):
            found |= any(alias.name == wanted for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            wildcard = any(alias.name == "*" for alias in node.names)
            if node.level or not base: suspect.append("required_edge_path_escape")
            if wildcard: suspect.append("required_edge_wildcard")
            found |= not wildcard and (base == wanted or any(f"{base}.{alias.name}" == wanted for alias in node.names))
        elif isinstance(node, ast.Call) and _call_name(node) in {"__import__", "import_module"}: suspect.append("required_edge_dynamic_import")
        elif isinstance(node, ast.Attribute) and node.attr == "path" and isinstance(node.value, ast.Name) and node.value.id == "sys": suspect.append("required_edge_sys_path")
    if found: return ()
    return tuple(dict.fromkeys(suspect or ("required_literal_edge_missing",)))

def _has_call_before(owner: ast.AST, first: str, second: str) -> bool:
    calls = [(node.lineno, _call_name(node)) for node in _walk_owned(owner, owner) if isinstance(node, ast.Call)]
    return any(name == first and line < min((other for other, value in calls if value == second), default=-1) for line, name in calls)

def _static_statement_calls_name(statement: ast.stmt, name: str) -> bool:
    """Match startup calls in a top-level statement, pruning nested owners.

    Module-level ``if``/``try``/``with`` bodies remain startup-owned; function,
    async-function, class, and lambda scopes never contribute their calls.
    """
    def visits(node: ast.AST) -> bool:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return False
        if isinstance(node, ast.Call) and _call_name(node) == name:
            return True
        return any(visits(child) for child in ast.iter_child_nodes(node))
    return visits(statement)

def _run_agent_dotenv_before_model_tools(source: bytes) -> bool:
    """Prove the actual module-startup dotenv call precedes model_tools import.

    This deliberately uses AST top-level statement ownership/order rather than
    substring indexes, where a missing substring can falsely sort before one.
    """
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError):
        return False
    dotenv_import_index: int | None = None
    dotenv_call_index: int | None = None
    model_tools_import_index: int | None = None
    for index, statement in enumerate(tree.body):
        if isinstance(statement, ast.ImportFrom):
            if statement.module == "hermes_cli.env_loader" and any(alias.name == "load_hermes_dotenv" for alias in statement.names):
                dotenv_import_index = index
            if statement.module == "model_tools":
                if model_tools_import_index is None:
                    model_tools_import_index = index
        if _static_statement_calls_name(statement, "load_hermes_dotenv"):
            dotenv_call_index = index
    return (
        dotenv_import_index is not None
        and dotenv_call_index is not None
        and model_tools_import_index is not None
        and dotenv_import_index < dotenv_call_index < model_tools_import_index
    )

def _startup_plugin_then_hooks(source: bytes) -> bool:
    try: owner = _owner(ast.parse(source.decode("utf-8")), "_prepare_agent_startup")
    except (UnicodeDecodeError, SyntaxError): return False
    return owner is not None and _has_call_before(owner, "discover_plugins", "register_from_config") and "load_config" in _owned_calls(source, "_prepare_agent_startup")
def _name_assignment(statement: ast.stmt, name: str) -> ast.Call | None:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return None
    if not isinstance(statement.targets[0], ast.Name) or statement.targets[0].id != name:
        return None
    return statement.value if isinstance(statement.value, ast.Call) else None


def _exact_call(call: ast.Call | None, dotted: str, arguments: tuple[str, ...]) -> bool:
    if call is None or ".".join(_attribute_parts(call.func)) != dotted:
        return False
    return len(call.args) == len(arguments) and not call.keywords and all(
        isinstance(value, ast.Name) and value.id == expected
        for value, expected in zip(call.args, arguments, strict=True)
    )


def _attribute_parts(value: ast.AST) -> tuple[str, ...]:
    if isinstance(value, ast.Name):
        return (value.id,)
    if isinstance(value, ast.Attribute):
        return (*_attribute_parts(value.value), value.attr)
    return ()


def _exact_directory_spec(call: ast.Call | None) -> bool:
    if call is None or ".".join(_attribute_parts(call.func)) != "importlib.util.spec_from_file_location":
        return False
    if len(call.args) != 2 or not all(isinstance(value, ast.Name) for value in call.args):
        return False
    if tuple(value.id for value in call.args) != ("module_name", "init_file") or len(call.keywords) != 1:
        return False
    keyword = call.keywords[0]
    return (
        keyword.arg == "submodule_search_locations"
        and isinstance(keyword.value, ast.List)
        and len(keyword.value.elts) == 1
        and isinstance(keyword.value.elts[0], ast.Call)
        and _exact_call(keyword.value.elts[0], "str", ("plugin_dir",))
    )


def _spec_loader_guard(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.If) or statement.orelse or not statement.body:
        return False
    checks = tuple(node for node in ast.walk(statement.test) if isinstance(node, ast.Compare))
    has_spec_none = any(
        isinstance(check.left, ast.Name) and check.left.id == "spec"
        and any(isinstance(value, ast.Constant) and value.value is None for value in check.comparators)
        for check in checks
    )
    has_loader_none = any(
        isinstance(check.left, ast.Attribute)
        and isinstance(check.left.value, ast.Name)
        and check.left.value.id == "spec"
        and check.left.attr == "loader"
        and any(isinstance(value, ast.Constant) and value.value is None for value in check.comparators)
        for check in checks
    )
    return has_spec_none and has_loader_none and any(isinstance(node, ast.Raise) for node in statement.body)


def _same_spec_directory_flow(owner: ast.AST) -> bool:
    """Fail closed unless one direct statement path owns every loader value."""
    statements = tuple(owner.body) if isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)) else ()
    spec_indexes = [index for index, statement in enumerate(statements) if _exact_directory_spec(_name_assignment(statement, "spec"))]
    module_indexes = [index for index, statement in enumerate(statements) if _exact_call(_name_assignment(statement, "module"), "importlib.util.module_from_spec", ("spec",))]
    if len(spec_indexes) != 1 or len(module_indexes) != 1:
        return False
    spec_index, module_index = spec_indexes[0], module_indexes[0]
    if not spec_index < module_index:
        return False
    guard_indexes = [index for index, statement in enumerate(statements) if _spec_loader_guard(statement)]
    if len(guard_indexes) != 1 or not spec_index < guard_indexes[0] < module_index:
        return False
    # Any branch over the value-carrying interval is ambiguous except the exact
    # rejecting guard.  Nested scopes cannot contribute to this direct path.
    if any(
        isinstance(statement, (ast.If, ast.Try, ast.Match, ast.For, ast.While, ast.With, ast.AsyncWith))
        and index != guard_indexes[0]
        for index, statement in enumerate(statements[spec_index + 1 :], start=spec_index + 1)
    ):
        return False
    # A value-bearing direct assignment other than the approved module setup is
    # an ambiguous alias/substitution attempt, even if it is presently unused.
    approved_assignments = {"module", "module.__package__", "module.__path__", "sys.modules[module_name]"}
    for statement in statements[module_index + 1 :]:
        if isinstance(statement, ast.Assign):
            targets = {ast.unparse(target) for target in statement.targets}
            if not targets <= approved_assignments:
                return False
    for statement in statements[spec_index + 1 : module_index]:
        if isinstance(statement, ast.Assign):
            return False
    exec_indexes = [
        index for index, statement in enumerate(statements)
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and ".".join(_attribute_parts(statement.value.func)) == "spec.loader.exec_module"
        and len(statement.value.args) == 1
        and isinstance(statement.value.args[0], ast.Name)
        and statement.value.args[0].id == "module"
        and not statement.value.keywords
    ]
    return_indexes = [index for index, statement in enumerate(statements) if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Name) and statement.value.id == "module"]
    return len(exec_indexes) == 1 and len(return_indexes) == 1 and module_index < exec_indexes[0] < return_indexes[0]


def _is_bundled_manifest_branch(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.If) or not isinstance(statement.test, ast.Compare):
        return False
    left = statement.test.left
    return (
        isinstance(left, ast.Attribute)
        and isinstance(left.value, ast.Name)
        and left.value.id == "manifest"
        and left.attr == "source"
        and any(isinstance(value, (ast.Set, ast.Tuple, ast.List)) and any(isinstance(item, ast.Constant) and item.value == "bundled" for item in value.elts) for value in statement.test.comparators)
    )


def _same_manifest_plugin_flow(owner: ast.AST) -> bool:
    """Prove bundled directory load then register/context on one reachable path."""
    if not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    tries = [statement for statement in owner.body if isinstance(statement, ast.Try)]
    if len(tries) != 1:
        return False
    statements = tuple(tries[0].body)
    branches = [(index, statement) for index, statement in enumerate(statements) if _is_bundled_manifest_branch(statement)]
    if len(branches) != 1:
        return False
    branch_index, branch = branches[0]
    direct_loads = [
        statement for statement in branch.body
        if _exact_call(_name_assignment(statement, "module"), "self._load_directory_module", ("manifest",))
    ]
    if len(direct_loads) != 1 or any(isinstance(statement, (ast.If, ast.Try, ast.Match)) for statement in branch.body):
        return False
    loaded_index = next((index for index, statement in enumerate(statements) if index > branch_index and isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Name) and statement.value.id == "module" and any(isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "loaded" and target.attr == "module" for target in statement.targets)), None)
    register_index = next((
        index
        for index, statement in enumerate(statements)
        if index > (loaded_index if loaded_index is not None else -1)
        and isinstance(_name_assignment(statement, "register_fn"), ast.Call)
        and _call_name(_name_assignment(statement, "register_fn")) == "getattr"
        and len(_name_assignment(statement, "register_fn").args) == 3  # type: ignore[union-attr]
        and isinstance(_name_assignment(statement, "register_fn").args[0], ast.Name)  # type: ignore[union-attr]
        and _name_assignment(statement, "register_fn").args[0].id == "module"  # type: ignore[union-attr]
        and isinstance(_name_assignment(statement, "register_fn").args[1], ast.Constant)  # type: ignore[union-attr]
        and _name_assignment(statement, "register_fn").args[1].value == "register"  # type: ignore[union-attr]
        and isinstance(_name_assignment(statement, "register_fn").args[2], ast.Constant)  # type: ignore[union-attr]
        and _name_assignment(statement, "register_fn").args[2].value is None  # type: ignore[union-attr]
        and not _name_assignment(statement, "register_fn").keywords  # type: ignore[union-attr]
    ), None)
    if loaded_index is None or register_index is None:
        return False
    guards = [statement for statement in statements[register_index + 1 :] if isinstance(statement, ast.If) and statement.orelse]
    if len(guards) != 1:
        return False
    continuation = guards[0].orelse
    context_indexes = [index for index, statement in enumerate(continuation) if _exact_call(_name_assignment(statement, "ctx"), "PluginContext", ("manifest", "self"))]
    invoke_indexes = [index for index, statement in enumerate(continuation) if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Name) and statement.value.func.id == "register_fn" and len(statement.value.args) == 1 and isinstance(statement.value.args[0], ast.Name) and statement.value.args[0].id == "ctx" and not statement.value.keywords]
    return len(context_indexes) == 1 and len(invoke_indexes) == 1 and context_indexes[0] < invoke_indexes[0]


def _bundled_security_guidance_identity_proven(source: dict[str, bytes]) -> bool:
    """Prove one manifest object's bundled path through module and register.

    This is deliberately an owner-sensitive data-flow proof, not a generic
    loader-name check: the same ``manifest`` parameter must reach the directory
    loader, its ``manifest.path`` must form the package directory and
    ``__init__.py`` spec, and that same object must form the register context.
    """
    try:
        manifest = source["plugins/security-guidance/plugin.yaml"].decode("utf-8")
        loader_tree = ast.parse(source["hermes_cli/plugins.py"].decode("utf-8"))
        plugin_tree = ast.parse(source["plugins/security-guidance/__init__.py"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, SyntaxError):
        return False
    manifest_lines = manifest.splitlines()
    if "name: security-guidance" not in manifest_lines or any(line.lstrip().startswith("entrypoint:") for line in manifest_lines):
        return False
    directory_loader = _class_owner(loader_tree, "PluginManager", "_load_directory_module")
    load_plugin = _class_owner(loader_tree, "PluginManager", "_load_plugin")
    discovery = _class_owner(loader_tree, "PluginManager", "_discover_and_load_inner")
    if directory_loader is None or load_plugin is None or discovery is None:
        return False

    directory_statements = tuple(directory_loader.body)
    has_manifest_path = any(
        _exact_call(_name_assignment(statement, "plugin_dir"), "Path", ("manifest",))
        for statement in directory_statements
    )
    # ``Path(manifest.path)`` is a qualified attribute rather than a bare name.
    has_manifest_path = has_manifest_path or any(
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "plugin_dir"
        and isinstance(statement.value, ast.Call)
        and _call_name(statement.value) == "Path"
        and len(statement.value.args) == 1
        and isinstance(statement.value.args[0], ast.Attribute)
        and isinstance(statement.value.args[0].value, ast.Name)
        and statement.value.args[0].value.id == "manifest"
        and statement.value.args[0].attr == "path"
        and not statement.value.keywords
        for statement in directory_statements
    )
    has_init_mapping = any(
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "init_file"
        and isinstance(statement.value, ast.BinOp)
        and isinstance(statement.value.op, ast.Div)
        and isinstance(statement.value.left, ast.Name)
        and statement.value.left.id == "plugin_dir"
        and isinstance(statement.value.right, ast.Constant)
        and statement.value.right.value == "__init__.py"
        for statement in directory_statements
    )
    bundled_source_path = any(
        isinstance(node, ast.Call)
        and _call_name(node) == "_scan_directory"
        and any(keyword.arg == "source" and isinstance(keyword.value, ast.Constant) and keyword.value.value == "bundled" for keyword in node.keywords)
        for node in _walk_owned(discovery, discovery)
    )
    patterns_relative_import = any(
        isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module is None
        and any(alias.name == "patterns" for alias in node.names)
        for node in plugin_tree.body
    )
    return all((
        bundled_source_path,
        has_manifest_path,
        has_init_mapping,
        _same_spec_directory_flow(directory_loader),
        _same_manifest_plugin_flow(load_plugin),
        patterns_relative_import,
    ))

def _plugin_hooks(source: bytes) -> tuple[str, ...]:
    try: owner = _owner(ast.parse(source.decode("utf-8")), "register")
    except (UnicodeDecodeError, SyntaxError): return ()
    return tuple(node.args[0].value for node in _walk_owned(owner, owner) if isinstance(node, ast.Call) and _call_name(node) == "register_hook" and node.args and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is str) if owner else ()
def _plugin_loader_context(source: bytes) -> bool:
    try: owner = _class_owner(ast.parse(source.decode("utf-8")), "PluginManager", "_load_plugin")
    except (UnicodeDecodeError, SyntaxError): return False
    if owner is None: return False
    calls = list(_walk_owned(owner, owner)); has_fn = any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "register_fn" for t in n.targets) and isinstance(n.value, ast.Call) and _call_name(n.value) == "getattr" for n in calls); has_ctx = any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ctx" for t in n.targets) and isinstance(n.value, ast.Call) and _call_name(n.value) == "PluginContext" for n in calls); invokes = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "register_fn" and len(n.args) == 1 and isinstance(n.args[0], ast.Name) and n.args[0].id == "ctx" for n in calls)
    return has_fn and has_ctx and invokes
def _plugin_context_mutates_hooks(source: bytes) -> bool:
    try: owner = _class_owner(ast.parse(source.decode("utf-8")), "PluginContext", "register_hook")
    except (UnicodeDecodeError, SyntaxError): return False
    if owner is None: return False
    return any(isinstance(n, ast.Call) and _call_name(n) == "append" and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Call) and _call_name(n.func.value) == "setdefault" for n in _walk_owned(owner, owner))
def _loader_selects_bundled(source: bytes) -> bool:
    try: owner = _class_owner(ast.parse(source.decode("utf-8")), "PluginManager", "_load_plugin")
    except (UnicodeDecodeError, SyntaxError): return False
    return owner is not None and "_load_directory_module" in {_call_name(n) for n in _walk_owned(owner, owner) if isinstance(n, ast.Call)} and any(isinstance(n, ast.Constant) and n.value == "bundled" for n in _walk_owned(owner, owner))

def _claim(complete: bool, *reasons: str) -> tuple[bool, str, tuple[str, ...]]:
    blocked = tuple(reason for reason in reasons if reason)
    return (complete and not blocked, "STATIC_SOURCE_GRAPH_CLOSED" if complete and not blocked else "BLOCKED_SOURCE_GRAPH", blocked)

def _required_h2_edge_reasons(source: dict[str, bytes], edge: RequiredH2Edge) -> tuple[str, ...]:
    data = source.get(edge.source)
    if data is None:
        return (f"{edge.edge_id}:source_missing",)
    if edge.required_bytes not in data:
        return (f"{edge.edge_id}:exact_pattern_missing",)
    if edge.pattern == "manifest_entrypoint":
        try:
            lines = data.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            return (f"{edge.edge_id}:parse_failure",)
        # This manifest's directory entrypoint is the bundled __init__.py;
        # pin its identity and the literal declared hook list rather than
        # assuming a generic loader name proves this specific plugin.
        has_name = "name: security-guidance" in lines
        has_hooks = "hooks:" in lines and "  - transform_tool_result" in lines and "  - pre_tool_call" in lines
        return () if has_name and has_hooks else (f"{edge.edge_id}:manifest_entrypoint_missing",)
    if edge.edge_id == "plugin.patterns_import":
        return () if edge.required_bytes in data else (f"{edge.edge_id}:required_literal_edge_missing",)
    if edge.pattern == "bundled_selection":
        try:
            owner = _class_owner(ast.parse(data.decode("utf-8")), "PluginManager", "_load_plugin")
        except (UnicodeDecodeError, SyntaxError):
            return (f"{edge.edge_id}:parse_failure",)
        selected = owner is not None and any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Attribute)
            and node.left.attr == "source"
            and any(isinstance(value, ast.Constant) and value.value == "bundled" for value in ast.walk(node))
            and any(isinstance(node2, ast.Call) and _call_name(node2) == "_load_directory_module" for node2 in _walk_owned(owner, owner))
            for node in _walk_owned(owner, owner)
        )
        return () if selected else (f"{edge.edge_id}:bundled_selection_missing",)
    reasons = _required_edge_reasons(data, edge.owner, edge.target)
    if reasons:
        return tuple(f"{edge.edge_id}:{reason}" for reason in reasons)
    if edge.pattern == "literal_import_and_call":
        owner_name = edge.owner.split(".")[-1]
        calls = _owned_calls(data, owner_name) if edge.owner != "module" else {
            _call_name(node) for node in ast.walk(ast.parse(data.decode("utf-8"))) if isinstance(node, ast.Call)
        }
        if "discover_plugins" not in calls:
            return (f"{edge.edge_id}:owner_call_missing",)
    return ()

def _claim_details(source: dict[str, bytes]) -> tuple[tuple[str, bool, str, tuple[str, ...]], ...]:
    edge_reasons = {
        claim: [reason for edge in REQUIRED_H2_EDGES if edge.claim == claim for reason in _required_h2_edge_reasons(source, edge)]
        for claim in CLAIM_ORDER
    }
    startup_complete = _run_agent_dotenv_before_model_tools(source["run_agent.py"]) and _startup_plugin_then_hooks(source["hermes_cli/main.py"])
    startup = _claim(startup_complete, *edge_reasons["startup_source_ordering"], *(() if startup_complete else ("startup_owner_order_unproven",)))
    credential_edges = (("hermes_cli/runtime_provider.py", "resolve_runtime_provider", "hermes_cli/config.py"), ("hermes_cli/runtime_provider.py", "resolve_runtime_provider", "agent/credential_pool.py"), ("agent/agent_init.py", "init_agent", "agent/credential_pool.py"), ("run_agent.py", "module", "agent/agent_init.py"))
    credential_reasons = [reason for origin, owner, target in credential_edges for reason in _required_edge_reasons(source[origin], owner, target)]
    requested = "resolve_requested_provider" in _owned_calls(source["hermes_cli/runtime_provider.py"], "resolve_runtime_provider")
    pool = {"load_pool", "select", "credential_pool_matches_provider"} <= _owned_calls(source["hermes_cli/runtime_provider.py"], "resolve_runtime_provider")
    post_detection = "credential_pool_matches_provider" in _owned_calls(source["agent/agent_init.py"], "init_agent")
    # The frozen 20 files prove local predicates but do not provide a literal
    # data-flow edge from runtime resolution to AIAgent construction. Do not
    # infer that missing boundary from names or source proximity.
    credential = _claim(False, *credential_reasons, *(() if requested else ("requested_provider_selection_unproven",)), *(() if pool else ("credential_resolution_or_pool_validation_unproven",)), *(() if post_detection else ("post_detection_pool_validation_unproven",)), "provider_agent_construction_dataflow_unproven_in_h2_scope")
    plugin_ok = _plugin_hooks(source["plugins/security-guidance/__init__.py"]) == ("pre_tool_call", "transform_tool_result") and _bundled_security_guidance_identity_proven(source) and _plugin_loader_context(source["hermes_cli/plugins.py"]) and _plugin_context_mutates_hooks(source["hermes_cli/plugins.py"]) and _loader_selects_bundled(source["hermes_cli/plugins.py"])
    plugin = _claim(plugin_ok, *edge_reasons["security_guidance_plugin"], *(() if plugin_ok else ("plugin_loader_context_or_hook_mutation_unproven",)))
    return tuple((name, *value) for name, value in zip(CLAIM_ORDER, (startup, credential, plugin), strict=True))

def audit_spec034_startup_source_graph(bundle: SourceCatalogDecision) -> StartupGraphDecision:
    """Project current canonical evidence through the module-private issuer."""
    return _DECISION_AUTHORITY.graph_issue(bundle)

def audit_spec034_bundled_plugin(bundle: SourceCatalogDecision, graph: StartupGraphDecision) -> BundledPluginDecision:
    """Project the current graph provenance to its paired plugin decision."""
    return _DECISION_AUTHORITY.plugin_issue(bundle, graph)

def project_spec034_source_graph_receipt(bundle: SourceCatalogDecision, graph: StartupGraphDecision, plugin: BundledPluginDecision) -> dict[str, object]:
    """Return source-free claim-specific static receipt after evidence revalidation."""
    _DECISION_AUTHORITY.require_pair(bundle, graph, plugin)
    current_bundle = validate_spec034_source_bundle(); current_graph = audit_spec034_startup_source_graph(current_bundle); current_plugin = audit_spec034_bundled_plugin(current_bundle, current_graph)
    if (bundle.status, graph.claim_details, plugin.status, plugin.registration_status) != (current_bundle.status, current_graph.claim_details, current_plugin.status, current_plugin.registration_status): raise TypeError("decisions do not match current canonical evidence")
    details = {name: {"complete": complete, "verdict": verdict, "blocked_reasons": reasons} for name, complete, verdict, reasons in current_graph.claim_details}
    return {"spec_id": SPEC_ID, "status": current_graph.status, "terminal_status": current_graph.claim_graph_status, "claim_statuses": {name: detail["verdict"] for name, detail in details.items()}, "claim_details": details, "bundle_valid": current_bundle.bundle_valid, "whole_program_source_graph_closed": False, "startup_order_status": current_graph.startup_order_status, "config_status": current_graph.config_status, "credential_status": current_graph.credential_status, "provider_status": current_graph.provider_status, "plugin_registration_status": current_plugin.registration_status, "actual_activation_observed": False, "dynamic_plugin_status": "BLOCKED_DYNAMIC_PLUGIN_TARGET", "unknown_external_secret_runtime_edges": "BLOCKED_SOURCE_GRAPH", "runtime_status": "not_run", "live_actions_authorized": False}
