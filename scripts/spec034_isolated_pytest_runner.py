"""Stdlib-only isolated pytest runner for Spec034's sealed final child.

It accepts only protocol-owned project/capability snapshots whose exact records
were already verified against reviewer-approved manifest bytes by the parent.
"""
from __future__ import annotations
import base64
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import io
import json
import importlib.resources.abc
import os
from pathlib import Path
import stat
import subprocess
import sys

APPROVED_TOP_LEVEL_CAPABILITY_NAMES = frozenset()


def _clear_pytest_ambient() -> None:
    """Keep only the protocol-owned pytest autoload disablement."""
    for name in tuple(os.environ):
        if name.startswith("PYTEST_"):
            del os.environ[name]
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


def _minimal_child_env() -> dict[str, str]:
    """Pass only Windows process prerequisites to the isolated interpreter."""
    allowed = (
        "COMSPEC", "HOMEDRIVE", "HOMEPATH", "LOCALAPPDATA", "PATH",
        "PATHEXT", "SystemRoot", "TEMP", "TMP", "USERPROFILE", "WINDIR",
    )
    env = {name: os.environ[name] for name in allowed if name in os.environ}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


class _ExactPassedCalls:
    """In-memory proof that exactly the approved tests made passed calls."""

    def __init__(self, expected: tuple[str, ...]) -> None:
        self.expected = expected
        self.collected: tuple[str, ...] = ()
        self.passed_calls: tuple[str, ...] = ()
        self.invalid = False

    def pytest_collection_finish(self, session: object) -> None:
        items = getattr(session, "items", ())
        self.collected = tuple(getattr(item, "nodeid", "") for item in items)
        self.invalid = self.invalid or self.collected != self.expected

    def pytest_runtest_logreport(self, report: object) -> None:
        when, outcome, nodeid = (getattr(report, name, None) for name in ("when", "outcome", "nodeid"))
        if when == "call" and outcome == "passed" and not getattr(report, "wasxfail", False) and isinstance(nodeid, str):
            self.passed_calls += (nodeid,)
        elif outcome != "passed" or bool(getattr(report, "wasxfail", False)):
            self.invalid = True

    @property
    def complete(self) -> bool:
        return not self.invalid and self.collected == self.expected and self.passed_calls == self.expected
def _reparse(info: os.stat_result) -> bool: return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
def _safe_relative(value: object) -> bool: return isinstance(value, str) and value and "\\" not in value and not Path(value).is_absolute() and all(x not in ("", ".", "..") for x in value.split("/"))
def _regular_under(path: Path, root: Path) -> bool:
    try:
        root, path = root.absolute(), path.absolute(); relative = path.relative_to(root); current = root
        info = current.lstat()
        if not stat.S_ISDIR(info.st_mode) or current.is_symlink() or _reparse(info): return False
        for part in relative.parts:
            current /= part; info = current.lstat()
            if current == path:
                if not stat.S_ISREG(info.st_mode): return False
            elif not stat.S_ISDIR(info.st_mode): return False
            if current.is_symlink() or _reparse(info): return False
        return True
    except (OSError, ValueError): return False
def _read_verified(path: Path, root: Path, digest: str, length: int) -> bytes | None:
    try:
        if not _regular_under(path, root): return None
        before = path.lstat(); data = path.read_bytes(); after = path.lstat()
        stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        return data if stable and _regular_under(path, root) and len(data) == length and hashlib.sha256(data).hexdigest() == digest else None
    except OSError: return None
def _snapshot_records(root: Path, records: object) -> tuple[str, ...] | None:
    if not root.is_absolute() or not isinstance(records, list): return None
    expected: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "byte_length"}: return None
        path, digest, length = record["path"], record["sha256"], record["byte_length"]
        if not _safe_relative(path) or path in expected or not isinstance(digest, str) or not isinstance(length, int): return None
        if _read_verified(root / path, root, digest, length) is None: return None
        expected.add(path)
    actual: set[str] = set()
    try:
        for directory, dirs, files in os.walk(root, followlinks=False):
            parent = Path(directory)
            if parent.is_symlink() or _reparse(parent.lstat()) or any((parent / d).is_symlink() or _reparse((parent / d).lstat()) for d in dirs): return None
            for name in files:
                candidate = parent / name
                if not _regular_under(candidate, root): return None
                actual.add(candidate.relative_to(root).as_posix())
    except OSError: return None
    return tuple(sorted(expected)) if actual == expected else None
def _project_snapshot_valid(root: Path, records: object) -> bool:
    sealed = _snapshot_records(root, records)
    if sealed is None or "pyproject.toml" not in sealed: return False
    tops = APPROVED_TOP_LEVEL_CAPABILITY_NAMES
    for top in tops:
        if f"{top}.py" in sealed or f"{top}/__init__.py" in sealed: return False
    return True
def _capability_snapshot_valid(root: Path, records: object, approved_tops: object) -> bool:
    if not isinstance(approved_tops, list) or not approved_tops or not all(isinstance(name, str) and name.isidentifier() for name in approved_tops): return False
    return _snapshot_records(root, records) is not None

def _execution_records_match(execution: object, project_records: object) -> bool:
    """Require the child's snapshot union to retain its parent-issued category."""
    if not isinstance(execution, list) or not isinstance(project_records, list): return False
    expected: dict[str, tuple[str, int]] = {}
    categories: list[str] = []
    for record in execution:
        if not isinstance(record, dict) or set(record) != {"category", "path", "sha256", "byte_length"}: return False
        category, path, digest, length = record["category"], record["path"], record["sha256"], record["byte_length"]
        if category not in {"reviewed", "detached", "upstream", "predecessor"} or not _safe_relative(path) or not isinstance(digest, str) or not isinstance(length, int) or path in expected: return False
        expected[path] = (digest, length); categories.append(category)
    actual = {record.get("path"): (record.get("sha256"), record.get("byte_length")) for record in project_records if isinstance(record, dict)}
    return len(actual) == len(project_records) and actual == expected and categories.count("detached") == 2 and categories.count("upstream") == 20 and categories.count("predecessor") == 3 and categories.count("reviewed") > 0

def _imported_capabilities_are_snapshot_owned(capability: Path, approved_tops: object) -> bool:
    if not isinstance(approved_tops, list): return False
    try:
        for top in approved_tops:
            module = sys.modules.get(top)
            if module is None: continue
            origin = getattr(module, "__file__", None)
            if not isinstance(origin, str) or not Path(origin).absolute().is_relative_to(capability.absolute()): return False
        return True
    except (OSError, ValueError): return False

class _VerifiedBytesImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Execute approved Python source from a stable in-memory record map only.

    Paths remain logical snapshot identities for ``__file__``, packages, and
    resource lookup.  They are never reopened for Python code execution.
    """

    def __init__(self, root: Path, records: dict[str, bytes], *, module_prefix: str = "") -> None:
        self.root = root.absolute()
        self.records = dict(records)
        self._module_records: dict[str, tuple[str, bool]] = {}
        for relative in self.records:
            if not relative.endswith(".py") or (module_prefix and not relative.startswith(module_prefix)):
                continue
            module_relative = relative.removeprefix(module_prefix)
            if module_relative.endswith("/__init__.py"):
                name = module_relative.removesuffix("/__init__.py").replace("/", ".")
                self._module_records[name] = (relative, True)
            else:
                self._module_records[module_relative.removesuffix(".py").replace("/", ".")] = (relative, False)

    def find_spec(self, fullname: str, path: object = None, target: object = None):
        record = self._module_records.get(fullname)
        if record is None:
            return None
        relative, is_package = record
        return importlib.util.spec_from_loader(
            fullname,
            self,
            origin=str(self.root.joinpath(*relative.split("/"))),
            is_package=is_package,
        )

    def create_module(self, spec: object):
        return None

    def load_module(self, fullname: str):
        """Inert-test seam using the exact finder/loader path as import."""
        spec = self.find_spec(fullname)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        self.exec_module(module)
        return module

    def exec_module(self, module: object) -> None:
        spec = getattr(module, "__spec__", None)
        name = getattr(spec, "name", None)
        record = self._module_records.get(name) if isinstance(name, str) else None
        if record is None:
            raise ImportError("unapproved snapshot module")
        relative, is_package = record
        payload = self.records[relative]
        filename = str(self.root.joinpath(*relative.split("/")))
        module_dict = getattr(module, "__dict__")
        module_dict["__file__"] = filename
        module_dict["__loader__"] = self
        if is_package:
            module_dict["__path__"] = [str(self.root.joinpath(*relative.rsplit("/", 1)[0].split("/")))]
        exec(compile(payload, filename, "exec"), module_dict, module_dict)

    def get_filename(self, fullname: str) -> str:
        record = self._module_records.get(fullname)
        if record is None:
            raise ImportError("unapproved snapshot module")
        return str(self.root.joinpath(*record[0].split("/")))

    def get_data(self, path: str) -> bytes:
        try:
            relative = Path(path).absolute().relative_to(self.root).as_posix()
        except (OSError, ValueError) as error:
            raise OSError("unapproved snapshot resource") from error
        payload = self.records.get(relative)
        if payload is None:
            raise OSError("unapproved snapshot resource")
        return payload

    def get_resource_reader(self, fullname: str):
        record = self._module_records.get(fullname)
        return _VerifiedResourceReader(self, record[0].removesuffix("/__init__.py") + "/") if record is not None and record[1] else None


class _VerifiedResourceReader(importlib.resources.abc.ResourceReader):
    """Expose only manifest-approved package resources from the byte map."""

    def __init__(self, importer: _VerifiedBytesImporter, prefix: str) -> None:
        self.importer = importer
        self.prefix = prefix

    def open_resource(self, resource: str):
        return io.BytesIO(self.importer.get_data(str(self.importer.root / (self.prefix + resource))))

    def resource_path(self, resource: str) -> str:
        raise FileNotFoundError("approved resources are memory-backed")

    def is_resource(self, name: str) -> bool:
        return self.prefix + name in self.importer.records

    def contents(self):
        names = set()
        for relative in self.importer.records:
            if relative.startswith(self.prefix):
                remainder = relative.removeprefix(self.prefix)
                if remainder:
                    names.add(remainder.split("/", 1)[0])
        return iter(sorted(names))


class _SnapshotPathFinderBlocker(importlib.abc.MetaPathFinder):
    """Prevent PathFinder from bypassing the in-memory importer in snapshots."""

    def __init__(self, roots: tuple[Path, ...]) -> None:
        self.roots = tuple(root.absolute() for root in roots)

    def find_spec(self, fullname: str, path: object = None, target: object = None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        origin = getattr(spec, "origin", None) if spec is not None else None
        if isinstance(origin, str):
            try:
                if any(Path(origin).absolute().is_relative_to(root) for root in self.roots):
                    raise ImportError(f"unapproved pathname import: {fullname}")
            except OSError:
                raise ImportError(f"unapproved pathname import: {fullname}") from None
        return None


def _verified_record_bytes(root: Path, records: object) -> dict[str, bytes] | None:
    """Stable-read every approved record before a single code import begins."""
    if not isinstance(records, list):
        return None
    payloads: dict[str, bytes] = {}
    for record in records:
        if not isinstance(record, dict):
            return None
        path, digest, length = record.get("path"), record.get("sha256"), record.get("byte_length")
        if not _safe_relative(path) or not isinstance(digest, str) or not isinstance(length, int):
            return None
        data = _read_verified(root / path, root, digest, length)
        if data is None or path in payloads:
            return None
        payloads[path] = data
    return payloads


def _prioritize_snapshot_importers(*importers: importlib.abc.MetaPathFinder) -> None:
    for importer in importers:
        while importer in sys.meta_path:
            sys.meta_path.remove(importer)
    sys.meta_path[:0] = list(importers)


def _snapshot_cwd_valid(value: object, project: Path) -> bool:
    """Bind child-relative configuration to the exact project snapshot root."""
    try:
        cwd = Path(value)
        return isinstance(value, str) and cwd.is_absolute() and cwd.absolute() == project.absolute() and _directory_under_snapshot(cwd)
    except (OSError, ValueError):
        return False

def _directory_under_snapshot(path: Path) -> bool:
    try:
        info = path.lstat()
        return stat.S_ISDIR(info.st_mode) and not path.is_symlink() and not _reparse(info)
    except OSError:
        return False

def run(payload: object) -> int:
    required = {"project_snapshot", "project_records", "capability_snapshot", "capability_records", "targets", "expected_node_ids", "sentinel", "approved_top_levels", "cwd"}
    if not isinstance(payload, dict) or not required <= set(payload) or set(payload) - (required | {"execution_records"}): return 2
    project, capability, targets, tops = Path(payload["project_snapshot"]), Path(payload["capability_snapshot"]), payload["targets"], payload["approved_top_levels"]
    # `root` is deliberately the only project authority passed to the verified
    # sentinel before Pytest loading; it is a protocol-owned snapshot.
    root = project
    global APPROVED_TOP_LEVEL_CAPABILITY_NAMES
    APPROVED_TOP_LEVEL_CAPABILITY_NAMES = frozenset(tops) if isinstance(tops, list) else frozenset()
    execution = payload.get("execution_records")
    if execution is not None and not _execution_records_match(execution, payload["project_records"]): return 21
    if not _project_snapshot_valid(project, payload["project_records"]) or not _capability_snapshot_valid(capability, payload["capability_records"], tops) or not _snapshot_cwd_valid(payload["cwd"], project): return 21
    # Cache every record before importing any project/capability code.  Later
    # filesystem checks detect drift, but cannot be the execution authority.
    project_bytes = _verified_record_bytes(project, payload["project_records"])
    capability_bytes = _verified_record_bytes(capability, payload["capability_records"])
    if project_bytes is None or capability_bytes is None: return 21
    if not isinstance(targets, list) or not all(isinstance(target, str) and target in project_bytes for target in targets): return 21
    sys.dont_write_bytecode = True
    stdlib_paths = tuple(path for path in sys.path if "site-packages" not in path and "dist-packages" not in path)
    sys.path[:] = [str(capability), str(project / "src"), str(project), *stdlib_paths]
    importer = _VerifiedBytesImporter(project, project_bytes, module_prefix="src/")
    test_importer = _VerifiedBytesImporter(project, project_bytes, module_prefix="")
    capability_importer = _VerifiedBytesImporter(capability, capability_bytes)
    blocker = _SnapshotPathFinderBlocker((project, capability))
    # These loaders precede Pytest's rewriter and PathFinder.  Thus neither
    # sys.path nor an assertion-rewrite loader can reopen a Python source path.
    _prioritize_snapshot_importers(importer, test_importer, capability_importer, blocker)
    try:
        os.chdir(project)
    except OSError:
        return 21
    expected_node_ids = payload["expected_node_ids"]
    if not isinstance(expected_node_ids, list) or not expected_node_ids or not all(isinstance(nodeid, str) and "::test_" in nodeid for nodeid in expected_node_ids): return 21
    expected = tuple(expected_node_ids)
    if len(expected) != len(set(expected)): return 21
    sentinel = payload["sentinel"]
    if not isinstance(sentinel, dict) or set(sentinel) != {"module", "bytes_b64", "sha256", "byte_length"}: return 23
    try: sentinel_bytes = base64.b64decode(sentinel["bytes_b64"].encode("ascii"), validate=True)
    except (ValueError, AttributeError): return 2
    if len(sentinel_bytes) != sentinel["byte_length"] or hashlib.sha256(sentinel_bytes).hexdigest() != sentinel["sha256"]: return 2
    import types
    sentinel_module = types.ModuleType(sentinel["module"]); sentinel_module.__file__ = "spec034-approved/spec034_offline_runtime_sentinel.py"; sys.modules[sentinel["module"]] = sentinel_module
    exec(compile(sentinel_bytes, sentinel_module.__file__, "exec"), sentinel_module.__dict__, sentinel_module.__dict__)
    install = getattr(sentinel_module, "install", None)
    if not callable(install): return 2
    install(root)
    if getattr(sentinel_module, "GUARDS_INSTALLED", False) is not True: return 2
    _clear_pytest_ambient()
    # Exact snapshot closure rejects cache artifacts, so imports must not create
    # ambient __pycache__ files in either protocol-owned snapshot.  Snapshot
    # paths and cwd were bound before this sentinel/Pytest import boundary.
    try:
        import pytest
        if not Path(pytest.__file__).absolute().is_relative_to(capability.absolute()): return 2
    except Exception: return 2
    if not _project_snapshot_valid(project, payload["project_records"]) or not _capability_snapshot_valid(capability, payload["capability_records"], tops) or not _imported_capabilities_are_snapshot_owned(capability, tops): return 2
    counter = _ExactPassedCalls(expected)
    args = ("--noconftest", "-p", "no:cacheprovider", "-o", "addopts=", "-c", str(project / "pyproject.toml"), *[str(project / target) for target in targets], "-q")
    result = pytest.main(list(args), plugins=[counter])
    return 0 if result == 0 and counter.complete and _project_snapshot_valid(project, payload["project_records"]) and _capability_snapshot_valid(capability, payload["capability_records"], tops) and _imported_capabilities_are_snapshot_owned(capability, tops) else 1

_CHILD_EXEC_RUNNER = """
import base64, hashlib, json, sys
packet = json.loads(sys.stdin.buffer.read().decode('utf-8')); runner = base64.b64decode(packet['runner_b64'].encode('ascii'), validate=True)
if len(runner) != int(sys.argv[2]) or hashlib.sha256(runner).hexdigest() != sys.argv[1]: raise SystemExit('unapproved isolated pytest runner bytes')
globals_dict = {'__name__': '__main__', '__file__': 'spec034-approved/spec034_isolated_pytest_runner.py', '__package__': None, '__builtins__': __builtins__}
exec(compile(runner, globals_dict['__file__'], 'exec'), globals_dict, globals_dict); raise SystemExit(globals_dict['run'](packet['payload']))
"""
def run_isolated(payload: dict[str, object]) -> int:
    runner = Path(__file__).read_bytes(); packet = json.dumps({"runner_b64": base64.b64encode(runner).decode("ascii"), "payload": payload}, sort_keys=True).encode("utf-8")
    completed = subprocess.run((sys.executable, "-I", "-S", "-c", _CHILD_EXEC_RUNNER, hashlib.sha256(runner).hexdigest(), str(len(runner))), input=packet, check=False, capture_output=True, env=_minimal_child_env())
    if completed.returncode: sys.stderr.buffer.write(completed.stderr)
    return completed.returncode
