"""Build the bounded, claim-scoped Spec034 H1 source inventory.

This program parses source statically and never imports or executes Hermes.  It
reads only identity-checked Spec033 frozen roots plus the explicitly named,
commit-addressed files needed for the three H1 claims.  It intentionally does
not enumerate the repository or recursively close ordinary imports.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any

OWNER = "NousResearch"
REPOSITORY = "hermes-agent"
PINNED_COMMIT = "b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6"
PINNED_TREE = "3ae46c7c1576f9a3450a64729be314ba8e853eac"
MAX_FILES = 96
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_INTERNAL_DEPTH = 16

ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "specs" / "034-hermes-v019-pinned-startup-source-graph"
INVENTORY_PATH = SPEC_ROOT / "contracts" / "h1-source-inventory-proposal.json"
RECEIPT_PATH = SPEC_ROOT / "contracts" / "h1-discovery-receipt.json"
SPEC033_ROOT = ROOT / "specs" / "033-hermes-v019-pinned-source-loader-audit"
SPEC033_MANIFEST_PATH = SPEC033_ROOT / "contracts" / "source-bundle-manifest.json"
SPEC033_SOURCE_ROOT = SPEC033_ROOT / "upstream" / "NousResearch-hermes-agent-b7a05b6"
RAW_PREFIX = f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{PINNED_COMMIT}/"

SPEC033_ROOTS = (
    "LICENSE", "pyproject.toml", "run_agent.py", "hermes_cli/main.py",
    "hermes_cli/oneshot.py", "hermes_cli/plugins.py", "hermes_cli/plugins_cmd.py",
    "hermes_cli/subcommands/plugins.py", "hermes_cli/runtime_provider.py",
    "hermes_cli/config.py", "hermes_cli/env_loader.py", "hermes_cli/hooks.py",
    "agent/agent_init.py", "agent/tool_executor.py", "model_tools.py",
    "providers/__init__.py", "providers/base.py",
)
FIXED_PLUGIN_PATHS = (
    "plugins/security-guidance/plugin.yaml",
    "plugins/security-guidance/__init__.py",
    "plugins/security-guidance/patterns.py",
)
FORBIDDEN_BASENAMES = {".env", ".envrc", "cli-config.yaml", "config.yaml"}
FORBIDDEN_SUFFIXES = (".log", ".session")
INTERNAL_TOP_LEVEL = {
    "agent", "hermes_cli", "providers", "plugins", "tools", "model_tools",
    "hermes_constants", "utils", "run_agent",
}
CLAIM_ORDER = (
    "startup_source_ordering",
    "credential_provider_boundary",
    "security_guidance_plugin",
)

# Only the direct source relationships required to interpret the named claim
# predicates appear here.  Any other Hermes import in a listed source is a
# typed out-of-claim leaf and is deliberately not fetched or expanded.
CLAIMS: dict[str, dict[str, Any]] = {
    "startup_source_ordering": {
        "roots": ("pyproject.toml", "run_agent.py", "hermes_cli/main.py"),
        "edges": (
            ("run_agent.py", "hermes_cli/env_loader.py", "literal_import"),
            ("run_agent.py", "agent/process_bootstrap.py", "literal_import"),
            ("run_agent.py", "model_tools.py", "literal_import"),
            ("hermes_cli/main.py", "hermes_cli/env_loader.py", "literal_import"),
            ("hermes_cli/main.py", "hermes_cli/config.py", "literal_import"),
            ("hermes_cli/main.py", "hermes_cli/plugins.py", "literal_import"),
            ("hermes_cli/main.py", "agent/shell_hooks.py", "literal_import"),
            ("model_tools.py", "hermes_cli/plugins.py", "literal_import"),
        ),
        "predicates": ("cli_entrypoint", "dotenv_before_model_tools", "startup_plugin_then_shell_hook"),
    },
    "credential_provider_boundary": {
        "roots": ("hermes_cli/runtime_provider.py", "agent/agent_init.py"),
        "edges": (
            ("hermes_cli/runtime_provider.py", "hermes_cli/config.py", "literal_import"),
            ("hermes_cli/runtime_provider.py", "hermes_cli/auth.py", "literal_import"),
            ("hermes_cli/runtime_provider.py", "agent/credential_pool.py", "literal_import"),
            ("hermes_cli/runtime_provider.py", "agent/secret_scope.py", "literal_import"),
            ("agent/agent_init.py", "agent/credential_pool.py", "literal_import"),
            ("agent/agent_init.py", "providers/__init__.py", "literal_import"),
            ("providers/__init__.py", "providers/base.py", "literal_import"),
        ),
        "predicates": ("requested_provider_selection", "provider_credential_resolution", "post_detection_pool_validation", "agent_construction_boundary"),
    },
    "security_guidance_plugin": {
        "roots": (
            "plugins/security-guidance/plugin.yaml", "hermes_cli/plugins.py",
            "model_tools.py", "hermes_cli/main.py", "hermes_cli/oneshot.py",
        ),
        "edges": (
            ("hermes_cli/main.py", "hermes_cli/plugins.py", "literal_import"),
            ("hermes_cli/oneshot.py", "hermes_cli/plugins.py", "literal_import"),
            ("model_tools.py", "hermes_cli/plugins.py", "literal_import"),
            ("hermes_cli/plugins.py", "plugins/security-guidance/__init__.py", "conditional_fixed_plugin_loader_candidate"),
            ("plugins/security-guidance/plugin.yaml", "plugins/security-guidance/__init__.py", "fixed_manifest_entrypoint"),
            ("plugins/security-guidance/__init__.py", "plugins/security-guidance/patterns.py", "literal_import"),
        ),
        "predicates": ("conditional_loader_register_candidate", "literal_hook_registration", "plugin_context_mutation_candidate"),
    },
}


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _safe_repo_path(path: str) -> str:
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or "\\" in path or any(part in {"", ".", ".."} for part in pure.parts):
        raise RuntimeError("unsafe_repository_path")
    basename = pure.name.lower()
    if basename in FORBIDDEN_BASENAMES or basename.startswith(".env.") or basename.endswith(FORBIDDEN_SUFFIXES):
        raise RuntimeError("forbidden_repository_path")
    return pure.as_posix()


def _load_spec033_sources() -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    manifest = json.loads(SPEC033_MANIFEST_PATH.read_text(encoding="utf-8"))
    if (manifest.get("repository"), manifest.get("pinned_commit"), manifest.get("tree_sha")) != (f"{OWNER}/{REPOSITORY}", PINNED_COMMIT, PINNED_TREE):
        raise RuntimeError("spec033_authority_identity_mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, list) or tuple(entry.get("path") for entry in entries) != SPEC033_ROOTS:
        raise RuntimeError("spec033_manifest_root_order_mismatch")
    by_path = {entry["path"]: entry for entry in entries if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
    sources: dict[str, bytes] = {}
    for path in SPEC033_ROOTS:
        entry = by_path.get(path)
        if entry is None:
            raise RuntimeError("spec033_manifest_root_missing")
        data = SPEC033_SOURCE_ROOT.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(data) != entry.get("byte_length") or hashlib.sha256(data).hexdigest() != entry.get("sha256") or _git_blob_sha(data) != entry.get("git_blob_sha"):
            raise RuntimeError("spec033_frozen_source_identity_mismatch")
        sources[path] = data
    return sources, by_path


class ImmutableFileReader:
    def __init__(self, frozen_sources: dict[str, bytes]) -> None:
        self._frozen_sources = frozen_sources
        self._cache: dict[str, bytes] = {}
        self.official_file_retrieval_count = 0

    def read_required(self, path: str) -> bytes:
        path = _safe_repo_path(path)
        if path in self._cache:
            return self._cache[path]
        if path in self._frozen_sources:
            data = self._frozen_sources[path]
        else:
            request = urllib.request.Request(RAW_PREFIX + path, headers={"User-Agent": "podcast-ingest-core-spec034-h1"})
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status != 200:
                        raise RuntimeError("official_immutable_file_status")
                    data = response.read(MAX_TOTAL_BYTES + 1)
            except urllib.error.HTTPError as exc:
                raise RuntimeError("required_immutable_file_unavailable") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError("official_immutable_file_request_failed") from exc
            if len(data) > MAX_TOTAL_BYTES:
                raise RuntimeError("individual_source_exceeds_byte_ceiling")
            self.official_file_retrieval_count += 1
        self._cache[path] = data
        return data


def _path_to_module(path: str) -> str:
    pure = PurePosixPath(path)
    if path == "plugins/security-guidance/__init__.py":
        return "plugins.security_guidance"
    if path == "plugins/security-guidance/patterns.py":
        return "plugins.security_guidance.patterns"
    if pure.name == "__init__.py":
        return ".".join(pure.parent.parts)
    return ".".join(pure.with_suffix("").parts)


def _direct_internal_modules(path: str, data: bytes, module_paths: dict[str, str]) -> tuple[set[str], list[dict[str, str]]]:
    """Return directly imported internal modules and nonliteral/dynamic leaves."""
    try:
        tree = ast.parse(data.decode("utf-8"), filename=path)
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise RuntimeError("claim_source_parse_error") from exc
    current = _path_to_module(path)
    package = current.split(".") if path.endswith("/__init__.py") else current.split(".")[:-1]
    modules: set[str] = set()
    dynamic_leaves: list[dict[str, str]] = []

    def add_module(module: str) -> None:
        if module.split(".", 1)[0] in INTERNAL_TOP_LEVEL:
            modules.add(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_module(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                levels_up = node.level - 1
                if levels_up > len(package):
                    dynamic_leaves.append({"source": path, "kind": "relative_import_path_escape"})
                    continue
                base_parts = package[: len(package) - levels_up]
                if node.module:
                    base_parts.extend(node.module.split("."))
                base = ".".join(base_parts)
            else:
                base = node.module or ""
            if any(alias.name == "*" for alias in node.names):
                dynamic_leaves.append({"source": path, "kind": "wildcard_import", "target_module": base})
            if base:
                add_module(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidate = f"{base}.{alias.name}" if base else alias.name
                if candidate in module_paths:
                    add_module(candidate)
        elif isinstance(node, ast.Call):
            mechanism = ""
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                mechanism = "__import__"
            elif isinstance(node.func, ast.Attribute) and node.func.attr in {"import_module", "spec_from_file_location", "exec_module", "load_module"}:
                mechanism = node.func.attr
            if mechanism:
                if mechanism in {"__import__", "import_module"} and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    add_module(node.args[0].value)
                else:
                    dynamic_leaves.append({"source": path, "kind": "nonliteral_or_dynamic_loader", "mechanism": mechanism})
    return modules, dynamic_leaves


def _has_static_edge(source: str, target: str, direct_modules: dict[str, set[str]]) -> bool:
    return _path_to_module(target) in direct_modules.get(source, set())


def _plugin_predicates(plugin_source: bytes, loader_source: bytes) -> tuple[dict[str, object], list[str]]:
    tree = ast.parse(plugin_source.decode("utf-8"), filename=FIXED_PLUGIN_PATHS[1])
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    register = functions.get("register")
    hooks: list[str] = []
    if register is not None:
        for node in ast.walk(register):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "register_hook" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                hooks.append(node.args[0].value)
    env_names = {
        child.args[0].value
        for child in ast.walk(tree)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "get"
        and isinstance(child.func.value, ast.Attribute) and child.func.value.attr == "environ"
        and isinstance(child.func.value.value, ast.Name) and child.func.value.value.id == "os"
        and child.args and isinstance(child.args[0], ast.Constant) and isinstance(child.args[0].value, str)
    }
    blocks: list[str] = []
    if hooks != ["pre_tool_call", "transform_tool_result"]:
        blocks.append("plugin_literal_hook_mismatch")
    if env_names != {"SECURITY_GUIDANCE_BLOCK", "SECURITY_GUIDANCE_DISABLE"}:
        blocks.append("plugin_environment_predicate_mismatch")
    loader_tree = ast.parse(loader_source.decode("utf-8"), filename="hermes_cli/plugins.py")
    loader_names = {node.name for node in ast.walk(loader_tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    loader_calls = {node.func.attr for node in ast.walk(loader_tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    if "_load_plugin" not in loader_names or "spec_from_file_location" not in loader_calls:
        blocks.append("conditional_plugin_loader_predicate_unresolved")
    return {
        "identity": "security-guidance",
        "paths": list(FIXED_PLUGIN_PATHS),
        "literal_hooks": hooks,
        "call_time_environment_predicates": ["SECURITY_GUIDANCE_BLOCK", "SECURITY_GUIDANCE_DISABLE"],
        "registration_claim": "conditional_registration_path_candidate",
        "context_mutation_claim": "plugin_context_hook_registration_candidate",
        "actual_activation_observed": False,
    }, blocks


def _claim_reachable(claim: dict[str, Any]) -> tuple[dict[str, str], dict[str, int]]:
    parents: dict[str, str] = {path: "root" for path in claim["roots"]}
    depths: dict[str, int] = {path: 0 for path in claim["roots"]}
    by_source: dict[str, list[str]] = {}
    for source, target, _kind in claim["edges"]:
        by_source.setdefault(source, []).append(target)
    queue = deque(claim["roots"])
    while queue:
        source = queue.popleft()
        for target in by_source.get(source, []):
            proposed_depth = depths[source] + 1
            if target not in depths or proposed_depth < depths[target]:
                depths[target] = proposed_depth
                parents[target] = source
                queue.append(target)
    return parents, depths


def _build_inventory() -> tuple[dict[str, object], dict[str, object]]:
    frozen_sources, frozen_manifest = _load_spec033_sources()
    reader = ImmutableFileReader(frozen_sources)
    membership: dict[str, set[str]] = {}
    introduced_by: dict[str, dict[str, str]] = {}
    depths: dict[str, dict[str, int]] = {}
    all_paths: set[str] = set()
    for claim_id in CLAIM_ORDER:
        parents, claim_depths = _claim_reachable(CLAIMS[claim_id])
        for path, parent in parents.items():
            all_paths.add(path)
            membership.setdefault(path, set()).add(claim_id)
            introduced_by.setdefault(path, {})[claim_id] = f"root:{claim_id}" if parent == "root" else parent
            depths.setdefault(path, {})[claim_id] = claim_depths[path]
    sources = {path: reader.read_required(path) for path in sorted(all_paths)}
    total_bytes = sum(len(data) for data in sources.values())
    if len(sources) > MAX_FILES or total_bytes > MAX_TOTAL_BYTES:
        raise RuntimeError("claim_inventory_ceiling_exceeded")
    module_paths = {_path_to_module(path): path for path in sources if path.endswith(".py")}
    direct_modules: dict[str, set[str]] = {}
    dynamic_by_source: dict[str, list[dict[str, str]]] = {}
    for path, data in sources.items():
        if path.endswith(".py"):
            direct_modules[path], dynamic_by_source[path] = _direct_internal_modules(path, data, module_paths)

    plugin_predicates, plugin_blocks = _plugin_predicates(sources[FIXED_PLUGIN_PATHS[1]], sources["hermes_cli/plugins.py"])
    # The fixed manifest is source-owned evidence paired with the fixed plugin
    # entrypoint.  Its schema is intentionally not reinterpreted as a runtime
    # loader proof; loader activation remains only a conditional candidate.
    plugin_manifest_ok = bool(sources[FIXED_PLUGIN_PATHS[0]])
    claim_records: dict[str, object] = {}
    all_out_of_claim: list[dict[str, str]] = []
    all_dynamic_leaves: list[dict[str, str]] = []
    for claim_id in CLAIM_ORDER:
        claim = CLAIMS[claim_id]
        required_edges: list[dict[str, str]] = []
        blocked_reasons: list[str] = []
        required_pairs = {(source, _path_to_module(target)) for source, target, _kind in claim["edges"]}
        for source, target, kind in claim["edges"]:
            resolved = True
            if kind == "literal_import":
                resolved = _has_static_edge(source, target, direct_modules)
            elif kind == "fixed_manifest_entrypoint":
                resolved = plugin_manifest_ok
            elif kind == "conditional_fixed_plugin_loader_candidate":
                resolved = "conditional_plugin_loader_predicate_unresolved" not in plugin_blocks
            if not resolved:
                blocked_reasons.append(f"claim_required_edge_unresolved:{source}->{target}")
            required_edges.append({"source": source, "target": target, "edge_kind": kind, "resolved": resolved})
        if claim_id == "security_guidance_plugin":
            blocked_reasons.extend(plugin_blocks)
        claim_paths = {path for path, claims in membership.items() if claim_id in claims}
        out_of_claim: list[dict[str, str]] = []
        dynamic_leaves: list[dict[str, str]] = []
        for source in sorted(claim_paths):
            for module in sorted(direct_modules.get(source, set())):
                if (source, module) not in required_pairs:
                    leaf = {"source": source, "target_module": module, "leaf_type": "out_of_claim_internal_leaf"}
                    out_of_claim.append(leaf)
                    all_out_of_claim.append({"claim": claim_id, **leaf})
            for leaf in dynamic_by_source.get(source, []):
                # The fixed security-guidance target is separately resolved by its
                # manifest and remains only a conditional, not observed, path.
                dynamic_leaf = {"leaf_type": "out_of_claim_dynamic_leaf", **leaf}
                dynamic_leaves.append(dynamic_leaf)
                all_dynamic_leaves.append({"claim": claim_id, **dynamic_leaf})
        blocked_reasons = sorted(set(blocked_reasons))
        claim_records[claim_id] = {
            "roots": list(claim["roots"]),
            "required_internal_edges": required_edges,
            "required_source_predicates": list(claim["predicates"]),
            "out_of_claim_internal_leaves": sorted(out_of_claim, key=lambda item: (item["source"], item["target_module"])),
            "out_of_claim_dynamic_leaves": sorted(dynamic_leaves, key=lambda item: (item["source"], item["kind"], item.get("mechanism", ""))),
            "blocked_reasons": blocked_reasons,
            "verdict": "PASS_CLAIM_SCOPED_SOURCE_CLOSURE" if not blocked_reasons else "BLOCKED_CLAIM_SOURCE_CLOSURE",
        }

    records: list[dict[str, object]] = []
    for path in sorted(sources):
        data = sources[path]
        claims = sorted(membership[path])
        roles = {claim_id: ("claim_root" if path in CLAIMS[claim_id]["roots"] else "required_claim_dependency") for claim_id in claims}
        record: dict[str, object] = {
            "path": path,
            "git_blob_sha": _git_blob_sha(data),
            "byte_length": len(data),
            "graph_role": "shared_claim_path" if len(claims) > 1 else roles[claims[0]],
            "claim_membership": claims,
            "claim_roles": roles,
            "introduced_by": {claim_id: introduced_by[path][claim_id] for claim_id in claims},
            "depth": {claim_id: depths[path][claim_id] for claim_id in claims},
        }
        if path in frozen_manifest and record["git_blob_sha"] != frozen_manifest[path].get("git_blob_sha"):
            raise RuntimeError("spec033_record_blob_mismatch")
        records.append(record)
    all_claims_pass = all(record["verdict"] == "PASS_CLAIM_SCOPED_SOURCE_CLOSURE" for record in claim_records.values())
    max_depth = max((depth for values in depths.values() for depth in values.values()), default=0)
    union = {
        "files": len(records),
        "total_bytes": total_bytes,
        "max_observed_depth": max_depth,
        "required_internal_edges": sum(len(CLAIMS[claim_id]["edges"]) for claim_id in CLAIM_ORDER),
        "out_of_claim_internal_leaves": len(all_out_of_claim),
        "out_of_claim_dynamic_leaves": len(all_dynamic_leaves),
    }
    status = "SPEC034_H1_INVENTORY_PROPOSED" if all_claims_pass else "BLOCKED_SOURCE_GRAPH"
    inventory: dict[str, object] = {
        "schema_version": "spec034-h1-claim-scoped-inventory-v2",
        "spec_id": "034-hermes-v019-pinned-startup-source-graph",
        "status": status,
        "authority": {
            "repository": f"{OWNER}/{REPOSITORY}", "pinned_commit": PINNED_COMMIT,
            "tree_sha": PINNED_TREE,
            "retrieval_policy": "identity-checked Spec033 frozen roots plus explicitly named official immutable files; no repository enumeration",
        },
        "ceilings": {"max_files": MAX_FILES, "max_total_bytes": MAX_TOTAL_BYTES, "max_internal_depth": MAX_INTERNAL_DEPTH},
        "whole_program_source_graph_closed": False,
        "claim_order": list(CLAIM_ORDER),
        "claims": claim_records,
        "files": records,
        "union": union,
        "fixed_plugin": plugin_predicates,
        "h2_inventory_approved": False,
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }
    inventory_bytes = (json.dumps(inventory, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt: dict[str, object] = {
        "schema_version": "spec034-h1-claim-scoped-discovery-receipt-v2",
        "spec_id": "034-hermes-v019-pinned-startup-source-graph",
        "status": status,
        "whole_program_source_graph_closed": False,
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "union": union,
        "claim_verdicts": {claim_id: claim_records[claim_id]["verdict"] for claim_id in CLAIM_ORDER},
        "claim_blocked_reason_counts": {claim_id: len(claim_records[claim_id]["blocked_reasons"]) for claim_id in CLAIM_ORDER},
        "fixed_plugin_identity": "security-guidance",
        "fixed_plugin_literal_hooks": plugin_predicates["literal_hooks"],
        "fixed_plugin_call_time_environment_names": plugin_predicates["call_time_environment_predicates"],
        "fixed_plugin_registration_claim": "conditional_registration_path_candidate",
        "actual_activation_observed": False,
        "official_immutable_file_retrieval_count": reader.official_file_retrieval_count,
        "spec033_frozen_root_count": len(frozen_sources),
        "source_bytes_in_receipt": False,
        "h2_inventory_approved": False,
        "runtime_status": "not_run",
        "live_actions_authorized": False,
    }
    return inventory, receipt


def _assert_final_self_check(inventory: dict[str, object], receipt: dict[str, object], inventory_bytes: bytes) -> None:
    assert inventory["schema_version"] == "spec034-h1-claim-scoped-inventory-v2"
    assert inventory["whole_program_source_graph_closed"] is False
    assert receipt["whole_program_source_graph_closed"] is False
    assert inventory["claim_order"] == list(CLAIM_ORDER)
    assert receipt["inventory_sha256"] == hashlib.sha256(inventory_bytes).hexdigest()
    files = inventory["files"]
    assert isinstance(files, list)
    paths = [record["path"] for record in files]
    assert paths == sorted(paths) and len(paths) == len(set(paths))
    union = inventory["union"]
    assert union["files"] == len(files) <= MAX_FILES
    assert union["total_bytes"] == sum(record["byte_length"] for record in files) <= MAX_TOTAL_BYTES
    assert union["max_observed_depth"] <= MAX_INTERNAL_DEPTH
    file_paths = set(paths)
    expected_status = "SPEC034_H1_INVENTORY_PROPOSED"
    for claim_id in CLAIM_ORDER:
        claim = inventory["claims"][claim_id]
        assert all(path in file_paths for path in claim["roots"])
        assert all(edge["resolved"] and edge["source"] in file_paths and edge["target"] in file_paths for edge in claim["required_internal_edges"])
        assert all(leaf["leaf_type"] == "out_of_claim_internal_leaf" for leaf in claim["out_of_claim_internal_leaves"])
        assert all(leaf["leaf_type"] == "out_of_claim_dynamic_leaf" for leaf in claim["out_of_claim_dynamic_leaves"])
        if claim["blocked_reasons"] or claim["verdict"] != "PASS_CLAIM_SCOPED_SOURCE_CLOSURE":
            expected_status = "BLOCKED_SOURCE_GRAPH"
    assert inventory["status"] == expected_status == receipt["status"]
    plugin = inventory["fixed_plugin"]
    assert plugin["literal_hooks"] == ["pre_tool_call", "transform_tool_result"]
    assert plugin["call_time_environment_predicates"] == ["SECURITY_GUIDANCE_BLOCK", "SECURITY_GUIDANCE_DISABLE"]
    assert plugin["registration_claim"] == "conditional_registration_path_candidate"
    assert plugin["actual_activation_observed"] is False
    assert inventory["h2_inventory_approved"] is False and receipt["h2_inventory_approved"] is False
    assert inventory["runtime_status"] == receipt["runtime_status"] == "not_run"
    assert inventory["live_actions_authorized"] is receipt["live_actions_authorized"] is False
    assert receipt["source_bytes_in_receipt"] is False
    receipt_text = json.dumps(receipt, ensure_ascii=True, sort_keys=True).lower()
    assert not any(marker in receipt_text for marker in ("http://", "https://", "traceback", "\\\\", "/sourcecode/", "exception"))


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        inventory_bytes = INVENTORY_PATH.read_bytes()
        inventory = json.loads(inventory_bytes)
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        _assert_final_self_check(inventory, receipt, inventory_bytes)
        print("SPEC034_H1_R_SELF_CHECK_PASS")
        return 0
    if len(sys.argv) > 1:
        raise SystemExit("usage: discover_spec_034_h1_inventory.py [--self-check]")
    inventory, receipt = _build_inventory()
    inventory_bytes = (json.dumps(inventory, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_bytes(inventory_bytes)
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "inventory_sha256": receipt["inventory_sha256"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
