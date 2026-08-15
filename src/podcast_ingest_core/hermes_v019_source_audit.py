"""Fail-closed, static-only audit for the pinned Hermes v0.19 source bundle.

This module reads bytes as data.  It neither imports nor executes upstream Hermes.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import tomllib
import weakref

SPEC_ROOT = Path(__file__).resolve().parents[2] / "specs/033-hermes-v019-pinned-source-loader-audit"
BUNDLE_ROOT = SPEC_ROOT / "upstream/NousResearch-hermes-agent-b7a05b6"
SOURCE_MANIFEST_PATH = SPEC_ROOT / "contracts/source-bundle-manifest.json"
PINNED_COMMIT = "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
REPOSITORY = "NousResearch/hermes-agent"
PINNED_TREE_SHA = "3ae46c7c1576f9a3450a64729be314ba8e853eac"
ALLOWLIST = (
    "LICENSE", "pyproject.toml", "run_agent.py", "hermes_cli/main.py",
    "hermes_cli/oneshot.py", "hermes_cli/plugins.py", "hermes_cli/plugins_cmd.py",
    "hermes_cli/subcommands/plugins.py", "hermes_cli/runtime_provider.py",
    "hermes_cli/config.py", "hermes_cli/env_loader.py", "hermes_cli/hooks.py",
    "agent/agent_init.py", "agent/tool_executor.py", "model_tools.py",
    "providers/__init__.py", "providers/base.py",
)
_ALLOWED_TERMINALS = frozenset({"BLOCKED_SOURCE_GRAPH", "BLOCKED_CREDENTIAL_SEAM", "SPEC033_SOURCE_PROOF_READY_FOR_H4_REVIEW"})
_BUNDLE_REASONS = frozenset({
    "pinned_source_bundle_unavailable", "source_bundle_nonregular_entry",
    "source_bundle_unreadable", "bundle_filesystem_allowlist_mismatch",
    "bundle_identity_mismatch", "allowlist_mismatch",
    "authoritative_blob_identity_mismatch", "bundle_record_schema_invalid",
    "source_file_missing_or_nonregular", "source_file_unreadable",
    "source_integrity_mismatch", "license_provenance_mismatch",
    "project_provenance_unavailable", "cli_entrypoint_provenance_mismatch",
    "loader_audit_pending", "invalid_bundle",
})
_LOADER_REASONS = frozenset({
    "invalid_bundle", "bundle_revalidation_failed", "loader_edge_unproved",
    "force_propagation_unproved", "import_time_caller_unproved",
    "call_time_caller_unproved", "plugins_list_classification_unproved",
    "plugin_context_hook_api_unproved", "plugin_module_dynamic_execution_unresolved",
})
_IMPORT_TIME_CALLERS = ("model_tools.py",)
_CALL_TIME_CALLERS = ("hermes_cli/main.py", "hermes_cli/oneshot.py")
_ALL_CALLERS = _IMPORT_TIME_CALLERS + _CALL_TIME_CALLERS
AUTHORITATIVE_PATH_BLOBS = (
    ("LICENSE", "75410e73319c72cd3e991a501c5455eb78f38375"),
    ("pyproject.toml", "a2a1d6c0ee240044de98b55bf93f7092f6ecef7d"),
    ("run_agent.py", "75846d5bec81f8daaabb742e33642ee97990b425"),
    ("hermes_cli/main.py", "fcca52b8851ebd40ea82ad812e3dc9c3a3233e01"),
    ("hermes_cli/oneshot.py", "320c61c8cc12e3d7041215ab37a93b0e5b60c7e9"),
    ("hermes_cli/plugins.py", "6ca393fca53c1fd2b3479bed72180fedcc848c88"),
    ("hermes_cli/plugins_cmd.py", "f5c57bb88f2bc91b7cbf43abaf7437efa033730a"),
    ("hermes_cli/subcommands/plugins.py", "5355fbec3429ccd6db06babbc80bf964248c44d1"),
    ("hermes_cli/runtime_provider.py", "7a17fc83943f7b058d6feabf838c60d7c1864a99"),
    ("hermes_cli/config.py", "640c184f0cc0874644ad21a0cdf51a4e52ea5d9b"),
    ("hermes_cli/env_loader.py", "e91c12adf7ebf8dde6cd794775110c8c61100cd6"),
    ("hermes_cli/hooks.py", "d3f86bd00e80254b42ea9440cdcede4ab9a0c68b"),
    ("agent/agent_init.py", "e239c48cfbd9d5f3a6f08c3d05852025cb08c218"),
    ("agent/tool_executor.py", "d235de36c03dd668bfb10377ef51c7074368c6b9"),
    ("model_tools.py", "32394a69eec64f3d676bedb1659a6f4e94887a74"),
    ("providers/__init__.py", "a394e74b335ae25c8344c025a500eebb97d47b2d"),
    ("providers/base.py", "554e01e4f7c77c3f32604a36fe6f94581b9dea27"),
)
@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class SourceBundleDecision:
    status: str
    runtime_status: str
    live_actions_authorized: bool
    reason: str
    bundle_valid: bool
    project_name: str | None
    project_version: str | None
    cli_entrypoints: tuple[str, ...]
    _factory_token: object

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("SourceBundleDecision is factory-issued only")


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class LoaderAuditDecision:
    status: str
    runtime_status: str
    live_actions_authorized: bool
    loader_path_verified: bool
    bounded_loader_edges_verified: bool
    force_propagation_verified: bool
    plugin_context_hook_api_verified: bool
    required_hook_registration_verified: bool
    import_time_status: str
    call_time_status: str
    dynamic_execution_status: str
    official_callers: tuple[str, ...]
    import_time_callers: tuple[str, ...]
    call_time_callers: tuple[str, ...]
    unresolved_entrypoints: tuple[str, ...]
    plugins_list_status: str
    reason: str
    _factory_token: object

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("LoaderAuditDecision is factory-issued only")


def _make_decision_authority() -> tuple[object, object, object, object]:
    """Keep issuance tokens and weak registries lexical, not module-readable."""
    issued_bundles: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]] = weakref.WeakKeyDictionary()
    issued_loaders: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]] = weakref.WeakKeyDictionary()
    loader_bundles: weakref.WeakKeyDictionary[object, object] = weakref.WeakKeyDictionary()
    bundle_fields = ("status", "runtime_status", "live_actions_authorized", "reason", "bundle_valid", "project_name", "project_version", "cli_entrypoints")
    loader_fields = ("status", "runtime_status", "live_actions_authorized", "loader_path_verified", "bounded_loader_edges_verified", "force_propagation_verified", "plugin_context_hook_api_verified", "required_hook_registration_verified", "import_time_status", "call_time_status", "dynamic_execution_status", "official_callers", "import_time_callers", "call_time_callers", "unresolved_entrypoints", "plugins_list_status", "reason")

    def seal(value: object) -> object | None:
        if type(value) is str:
            return ("str", value)
        if type(value) is bool:
            return ("bool", value)
        if value is None:
            return ("none",)
        if type(value) is tuple:
            items = tuple(seal(item) for item in value)
            return None if any(item is None for item in items) else ("tuple", items)
        return None

    def matches(value: object, sealed: object) -> bool:
        if type(sealed) is not tuple or not sealed:
            return False
        if sealed[0] == "str":
            return type(value) is str and value == sealed[1]
        if sealed[0] == "bool":
            return type(value) is bool and value is sealed[1]
        if sealed[0] == "none":
            return value is None
        if sealed[0] == "tuple":
            return type(value) is tuple and len(value) == len(sealed[1]) and all(matches(item, item_seal) for item, item_seal in zip(value, sealed[1], strict=True))
        return False

    def issue(cls: type, registry: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]], fields: tuple[str, ...], values: tuple[object, ...]) -> object:
        sealed = tuple(seal(value) for value in values)
        if len(values) != len(fields) or any(item is None for item in sealed):
            raise TypeError("invalid factory state")
        state = dict(zip(fields, values, strict=True))
        if state.get("status") not in _ALLOWED_TERMINALS or state.get("runtime_status") != "not_run" or state.get("live_actions_authorized") is not False:
            raise TypeError("invalid decision status")
        if cls is SourceBundleDecision:
            if state.get("reason") not in _BUNDLE_REASONS:
                raise TypeError("invalid bundle reason")
            if state.get("bundle_valid") is True and (
                state.get("status") != "BLOCKED_SOURCE_GRAPH"
                or state.get("reason") != "loader_audit_pending"
                or state.get("project_name") != "hermes-agent"
                or state.get("project_version") != "0.19.0"
                or state.get("cli_entrypoints") != ("hermes", "hermes-acp", "hermes-agent")
            ):
                raise TypeError("invalid valid-bundle facts")
            if state.get("bundle_valid") is not True and any(
                state.get(name) not in (None, ())
                for name in ("project_name", "project_version", "cli_entrypoints")
            ):
                raise TypeError("invalid blocked-bundle facts")
        elif cls is LoaderAuditDecision:
            if state.get("reason") not in _LOADER_REASONS:
                raise TypeError("invalid loader reason")
            complete = state.get("reason") == "plugin_module_dynamic_execution_unresolved"
            expected_true = (
                state.get("status") == "BLOCKED_SOURCE_GRAPH"
                and state.get("loader_path_verified") is False
                and state.get("bounded_loader_edges_verified") is True
                and state.get("force_propagation_verified") is True
                and state.get("plugin_context_hook_api_verified") is True
                and state.get("required_hook_registration_verified") is False
                and state.get("import_time_status") == "BLOCKED_SOURCE_GRAPH"
                and state.get("call_time_status") == "BLOCKED_SOURCE_GRAPH"
                and state.get("dynamic_execution_status") == "unresolved"
                and state.get("official_callers") == _ALL_CALLERS
                and state.get("import_time_callers") == _IMPORT_TIME_CALLERS
                and state.get("call_time_callers") == _CALL_TIME_CALLERS
                and state.get("unresolved_entrypoints") == ("run_agent.py",)
                and state.get("plugins_list_status") == "manifest_only_not_loader_proof"
            )
            if complete is not expected_true:
                raise TypeError("invalid loader facts")
        else:
            raise TypeError("invalid decision class")
        decision = object.__new__(cls)
        token = object()
        for name, value in zip(fields, values, strict=True):
            object.__setattr__(decision, name, value)
        object.__setattr__(decision, "_factory_token", token)
        registry[decision] = (token, sealed)
        return decision

    def issued(value: object, cls: type, registry: weakref.WeakKeyDictionary[object, tuple[object, tuple[object, ...]]], fields: tuple[str, ...]) -> bool:
        if type(value) is not cls:
            return False
        try:
            entry = registry.get(value)
            token = object.__getattribute__(value, "_factory_token")
            values = tuple(object.__getattribute__(value, field) for field in fields)
        except BaseException:
            return False
        return bool(entry is not None and token is entry[0] and len(values) == len(entry[1]) and all(matches(item, item_seal) for item, item_seal in zip(values, entry[1], strict=True)))

    def issue_bundle(status: str, reason: str, **kwargs: object) -> SourceBundleDecision:
        return issue(SourceBundleDecision, issued_bundles, bundle_fields, (status, "not_run", False, reason, kwargs.get("bundle_valid", False), kwargs.get("project_name"), kwargs.get("project_version"), kwargs.get("cli_entrypoints", ())))

    def issue_loader(bundle: SourceBundleDecision, status: str, loader_path_verified: bool, import_time_status: str, call_time_status: str, reason: str, **kwargs: object) -> LoaderAuditDecision:
        decision = issue(LoaderAuditDecision, issued_loaders, loader_fields, (status, "not_run", False, loader_path_verified, kwargs.get("bounded_loader_edges_verified", False), kwargs.get("force_propagation_verified", False), kwargs.get("plugin_context_hook_api_verified", False), kwargs.get("required_hook_registration_verified", False), import_time_status, call_time_status, kwargs.get("dynamic_execution_status", "unresolved"), kwargs.get("official_callers", ()), kwargs.get("import_time_callers", ()), kwargs.get("call_time_callers", ()), kwargs.get("unresolved_entrypoints", ()), kwargs.get("plugins_list_status", "not_modeled"), reason))
        loader_bundles[decision] = bundle
        return decision

    def bundle_issued(value: object) -> bool:
        return issued(value, SourceBundleDecision, issued_bundles, bundle_fields)

    def require_pair(bundle: object, loader: object) -> None:
        if not bundle_issued(bundle) or not issued(loader, LoaderAuditDecision, issued_loaders, loader_fields):
            raise TypeError("factory-issued decisions required")
        if loader_bundles.get(loader) is not bundle:
            raise TypeError("decision provenance mismatch")

    return issue_bundle, issue_loader, bundle_issued, require_pair


_ISSUE_BUNDLE, _ISSUE_LOADER, _BUNDLE_ISSUED, _REQUIRE_DECISION_PAIR = _make_decision_authority()
del _make_decision_authority


def _blocked(reason: str, _issue_bundle: object = _ISSUE_BUNDLE) -> SourceBundleDecision:
    return _issue_bundle("BLOCKED_SOURCE_GRAPH", reason)


def _safe_manifest() -> dict[str, object] | None:
    try:
        loaded = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
        return loaded if type(loaded) is dict else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _bundle_files(manifest: dict[str, object]) -> dict[str, dict[str, object]] | None:
    files = manifest.get("files")
    if type(files) is not list:
        return None
    result: dict[str, dict[str, object]] = {}
    for item in files:
        if type(item) is not dict or type(item.get("path")) is not str:
            return None
        result[item["path"]] = item
    return result if tuple(result) == ALLOWLIST and len(result) == len(ALLOWLIST) else None


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _project_provenance(data: bytes) -> tuple[str, str, tuple[str, ...]] | None:
    try:
        decoded = tomllib.loads(data.decode("utf-8"))
        project = decoded.get("project")
        scripts = project.get("scripts") if type(project) is dict else None
        if type(project) is not dict or type(scripts) is not dict:
            return None
        name, version = project.get("name"), project.get("version")
        if name != "hermes-agent" or version != "0.19.0":
            return None
        entrypoints = tuple(sorted(key for key, value in scripts.items() if type(key) is str and type(value) is str))
        return name, version, entrypoints
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, TypeError):
        return None


def validate_hermes_v019_source_bundle(_issue_bundle: object = _ISSUE_BUNDLE) -> SourceBundleDecision:
    """Revalidate the saved immutable bytes, without importing upstream code."""
    manifest = _safe_manifest()
    if not BUNDLE_ROOT.is_dir() or manifest is None:
        return _blocked("pinned_source_bundle_unavailable")
    try:
        saved_paths: list[str] = []
        for directory, dirnames, filenames in os.walk(BUNDLE_ROOT, followlinks=False):
            parent = Path(directory)
            if any((parent / name).is_symlink() for name in dirnames):
                return _blocked("source_bundle_nonregular_entry")
            for name in filenames:
                candidate = parent / name
                mode = candidate.lstat().st_mode
                if not stat.S_ISREG(mode) or candidate.is_symlink():
                    return _blocked("source_bundle_nonregular_entry")
                saved_paths.append(candidate.relative_to(BUNDLE_ROOT).as_posix())
    except OSError:
        return _blocked("source_bundle_unreadable")
    if tuple(sorted(saved_paths)) != tuple(sorted(ALLOWLIST)):
        return _blocked("bundle_filesystem_allowlist_mismatch")
    if manifest.get("schema_version") != "spec033-pinned-source-bundle-v1" or manifest.get("repository") != REPOSITORY or manifest.get("pinned_commit") != PINNED_COMMIT or manifest.get("tree_sha") != PINNED_TREE_SHA:
        return _blocked("bundle_identity_mismatch")
    files = _bundle_files(manifest)
    if files is None:
        return _blocked("allowlist_mismatch")
    if tuple((path, files[path].get("git_blob_sha")) for path in ALLOWLIST) != AUTHORITATIVE_PATH_BLOBS:
        return _blocked("authoritative_blob_identity_mismatch")
    source: dict[str, bytes] = {}
    for path, record in files.items():
        if set(record) != {"path", "git_blob_sha", "sha256", "byte_length"} or type(record["git_blob_sha"]) is not str or type(record["sha256"]) is not str or type(record["byte_length"]) is not int:
            return _blocked("bundle_record_schema_invalid")
        candidate = BUNDLE_ROOT / path
        try:
            mode = candidate.lstat().st_mode
            if not stat.S_ISREG(mode) or candidate.is_symlink():
                return _blocked("source_file_missing_or_nonregular")
            data = candidate.read_bytes()
        except OSError:
            return _blocked("source_file_unreadable")
        git_sha = _git_blob_sha(data)
        if len(data) != record["byte_length"] or hashlib.sha256(data).hexdigest() != record["sha256"] or git_sha != record["git_blob_sha"]:
            return _blocked("source_integrity_mismatch")
        source[path] = data
    license_record = manifest.get("license")
    if type(license_record) is not dict or license_record != files["LICENSE"]:
        return _blocked("license_provenance_mismatch")
    provenance = _project_provenance(source["pyproject.toml"])
    if provenance is None:
        return _blocked("project_provenance_unavailable")
    name, version, entrypoints = provenance
    if entrypoints != ("hermes", "hermes-acp", "hermes-agent"):
        return _blocked("cli_entrypoint_provenance_mismatch")
    return _issue_bundle("BLOCKED_SOURCE_GRAPH", "loader_audit_pending", bundle_valid=True, project_name=name, project_version=version, cli_entrypoints=entrypoints)


def _read_validated_sources() -> dict[str, bytes] | None:
    decision = validate_hermes_v019_source_bundle()
    if not decision.bundle_valid:
        return None
    manifest = _safe_manifest()
    if (
        manifest is None
        or manifest.get("schema_version") != "spec033-pinned-source-bundle-v1"
        or manifest.get("repository") != REPOSITORY
        or manifest.get("pinned_commit") != PINNED_COMMIT
        or manifest.get("tree_sha") != PINNED_TREE_SHA
    ):
        return None
    files = _bundle_files(manifest)
    if files is None or tuple((path, files[path].get("git_blob_sha")) for path in ALLOWLIST) != AUTHORITATIVE_PATH_BLOBS:
        return None
    source: dict[str, bytes] = {}
    try:
        for path in ALLOWLIST:
            candidate = BUNDLE_ROOT / path
            mode = candidate.lstat().st_mode
            if not stat.S_ISREG(mode) or candidate.is_symlink():
                return None
            data = candidate.read_bytes()
            record = files[path]
            if (
                len(data) != record.get("byte_length")
                or hashlib.sha256(data).hexdigest() != record.get("sha256")
                or _git_blob_sha(data) != record.get("git_blob_sha")
            ):
                return None
            source[path] = data
    except (OSError, KeyError):
        return None
    return source


def _module_top_level_calls(source: bytes, function_name: str) -> bool:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError):
        return False
    def walk_top_level(node: ast.AST) -> bool:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return False
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == function_name:
            return True
        return any(walk_top_level(child) for child in ast.iter_child_nodes(node))
    return any(walk_top_level(node) for node in tree.body)


def _function_has_call(source: bytes, function_name: str, callee: str) -> bool:
    try:
        tree = ast.parse(source.decode("utf-8"))
        function = next(node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name)
    except (UnicodeDecodeError, SyntaxError, StopIteration):
        return False
    def owns_call(node: ast.AST) -> bool:
        if node is not function and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return False
        if isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id == callee) or (isinstance(node.func, ast.Attribute) and node.func.attr == callee)):
            return True
        return any(owns_call(child) for child in ast.iter_child_nodes(node))

    return owns_call(function)


def _owned_function(source: bytes, class_name: str | None, function_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError):
        return None
    owner: ast.AST = tree
    if class_name is not None:
        owner = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name), tree)
        if owner is tree:
            return None
    return next((node for node in getattr(owner, "body", ()) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name), None)


def _owned_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.Call, ...]:
    calls: list[ast.Call] = []
    def collect(node: ast.AST) -> None:
        if node is not function and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(node, ast.Call):
            calls.append(node)
        for child in ast.iter_child_nodes(node):
            collect(child)
    collect(function)
    return tuple(calls)


def _function_edges(source: bytes, class_name: str | None, function_name: str) -> set[str] | None:
    function = _owned_function(source, class_name, function_name)
    if function is None:
        return None
    edges: set[str] = set()
    for node in _owned_calls(function):
        if isinstance(node.func, ast.Name):
            edges.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            edges.add(node.func.attr)
    return edges


def _function_has_keyword_call(source: bytes, class_name: str | None, function_name: str, callee: str, keyword: str, argument_name: str) -> bool:
    function = _owned_function(source, class_name, function_name)
    return bool(function is not None and any(
        ((isinstance(node.func, ast.Name) and node.func.id == callee) or (isinstance(node.func, ast.Attribute) and node.func.attr == callee))
        and any(item.arg == keyword and isinstance(item.value, ast.Name) and item.value.id == argument_name for item in node.keywords)
        for node in _owned_calls(function)
    ))


def audit_hermes_v019_loader_order(
    bundle: SourceBundleDecision,
    _issue_loader: object = _ISSUE_LOADER,
    _bundle_issued: object = _BUNDLE_ISSUED,
) -> LoaderAuditDecision:
    """Audit bounded AST call edges and fail closed at unknown source graph edges."""
    if type(bundle) is not SourceBundleDecision or not _bundle_issued(bundle) or not bundle.bundle_valid:
        return _issue_loader(_blocked("invalid_bundle"), "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "invalid_bundle")
    source = _read_validated_sources()
    if source is None:
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "bundle_revalidation_failed")
    plugin = source["hermes_cli/plugins.py"]
    required = (
        (None, "discover_plugins", {"get_plugin_manager", "discover_and_load"}),
        (None, "get_plugin_manager", {"PluginManager"}),
        ("PluginManager", "discover_and_load", {"_discover_and_load_inner"}),
        ("PluginManager", "_discover_and_load_inner", {"_load_plugin"}),
        ("PluginManager", "_load_plugin", {"_load_directory_module", "_load_entrypoint_module", "PluginContext", "register_fn"}),
    )
    for owner, function, required_edges in required:
        edges = _function_edges(plugin, owner, function)
        if edges is None or not required_edges <= edges:
            return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "loader_edge_unproved")
    force_propagated = _function_has_keyword_call(
        plugin,
        None,
        "discover_plugins",
        "discover_and_load",
        "force",
        "force",
    )
    if not force_propagated:
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "force_propagation_unproved")
    import_time_callers = ("model_tools.py",)
    call_time_callers = ("hermes_cli/main.py", "hermes_cli/oneshot.py")
    if not _module_top_level_calls(source["model_tools.py"], "discover_plugins"):
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "import_time_caller_unproved")
    # CLI caller ownership is established by AST-owned call expressions, while
    # ordering remains blocked because their transitive dependencies are absent.
    if not _function_has_call(source["hermes_cli/main.py"], "main", "discover_plugins") or not _function_has_call(source["hermes_cli/oneshot.py"], "_validate_explicit_toolsets", "discover_plugins"):
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "call_time_caller_unproved")
    callers = import_time_callers + call_time_callers
    # `plugins list` uses _discover_all_plugins()/manifest inspection and is not
    # a register/load proof; retain that distinction even though other commands
    # in the same module can call discovery.
    list_edges = _function_edges(source["hermes_cli/plugins_cmd.py"], None, "cmd_list")
    if list_edges is None or "_discover_all_plugins" not in list_edges or "discover_plugins" in list_edges:
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "plugins_list_classification_unproved")
    hook_edges = _function_edges(plugin, "PluginContext", "register_hook")
    if hook_edges is None or "append" not in hook_edges:
        return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "blocked", "blocked", "plugin_context_hook_api_unproved")
    # Both module-loading alternatives execute arbitrary third-party/plugin top-level code.
    # Their target bytes and all direct dependencies are outside the fixed allowlist.
    return _issue_loader(bundle, "BLOCKED_SOURCE_GRAPH", False, "BLOCKED_SOURCE_GRAPH", "BLOCKED_SOURCE_GRAPH", "plugin_module_dynamic_execution_unresolved", bounded_loader_edges_verified=True, force_propagation_verified=True, plugin_context_hook_api_verified=True, required_hook_registration_verified=False, official_callers=callers, import_time_callers=import_time_callers, call_time_callers=call_time_callers, unresolved_entrypoints=("run_agent.py",), plugins_list_status="manifest_only_not_loader_proof")


def project_hermes_v019_source_audit_receipt(
    bundle: SourceBundleDecision,
    loader: LoaderAuditDecision,
    _require_decision_pair: object = _REQUIRE_DECISION_PAIR,
) -> dict[str, object]:
    """Return the fixed, source-free projection of current canonical evidence."""
    _require_decision_pair(bundle, loader)
    current_bundle = validate_hermes_v019_source_bundle()
    current_loader = audit_hermes_v019_loader_order(current_bundle)
    bundle_fields = ("status", "runtime_status", "live_actions_authorized", "reason", "bundle_valid", "project_name", "project_version", "cli_entrypoints")
    loader_fields = ("status", "runtime_status", "live_actions_authorized", "loader_path_verified", "bounded_loader_edges_verified", "force_propagation_verified", "plugin_context_hook_api_verified", "required_hook_registration_verified", "import_time_status", "call_time_status", "dynamic_execution_status", "official_callers", "import_time_callers", "call_time_callers", "unresolved_entrypoints", "plugins_list_status", "reason")
    if any(object.__getattribute__(bundle, name) != object.__getattribute__(current_bundle, name) for name in bundle_fields) or any(object.__getattribute__(loader, name) != object.__getattribute__(current_loader, name) for name in loader_fields):
        raise TypeError("decisions do not match current source evidence")
    return {
        "spec_id": "033-hermes-v019-pinned-source-loader-audit",
        "status": current_loader.status,
        "terminal_status": current_loader.status,
        "bundle_valid": current_bundle.bundle_valid,
        "project_version": current_bundle.project_version,
        "pinned_commit": PINNED_COMMIT,
        "loader_path_verified": current_loader.loader_path_verified,
        "import_time_plugin_discovery_present": bool(current_loader.import_time_callers),
        "call_time_plugin_discovery_present": bool(current_loader.call_time_callers),
        "import_time_status": current_loader.import_time_status,
        "call_time_status": current_loader.call_time_status,
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }


# Issuance helpers remain module-private implementation details. Even if a caller
# introspects them, the authority validates an exact closed vocabulary of facts;
# arbitrary receipt-bearing strings cannot be issued.
