# Spec034 Main-only final invocation authority

Current terminal: **startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**. This is static/offline only: no live action, secret, upstream import/exec, predecessor verifier, commit, or H2 upstream expansion is authorized.

This v8 trust contract is sealed in the reviewed artifact tuple. The reviewed artifact manifest and detached root exclude themselves only to prevent a hash self-cycle; external root/bootstrap authority validates their detached identities. Fresh reviewers must approve the externally recorded root, launcher-contract, bootstrap, final-verifier, isolated-runner, and `python-test-capability-manifest.json` identities plus the literal approved distribution set. All pre-Task #80 roots, including `2503bef6` and `6b15c7df`, are not approval evidence.

## One unique Main command — do not execute before both re-reviews PASS

Main runs this exact PowerShell command once, with the reviewer-approved literals substituted. It clears `PYTHONOPTIMIZE`; Python's `-I -S` also ignores `PYTHON*` startup configuration, omits `site`, ignores user site/customize behavior, and ignores ambient `PYTHONPATH`. Every check is explicit `if`/`SystemExit`, never `assert`.

```powershell
Remove-Item Env:PYTHONOPTIMIZE -ErrorAction SilentlyContinue
@'
import hashlib
import os
from pathlib import Path
import stat
import sys

if os.environ.get("PYTHONOPTIMIZE") is not None:
    raise SystemExit("PYTHONOPTIMIZE must be cleared")
if len(sys.argv) != 7 or sys.argv[1] != "--approved-bootstrap-sha256" or sys.argv[3] != "--bootstrap-length" or sys.argv[5] != "--review-root-sha256":
    raise SystemExit("invalid Spec034 launcher arguments")

def reparse(info):
    return bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))

def regular_under(path, root):
    try:
        relative = path.absolute().relative_to(root)
        current = root
        root_info = current.lstat()
        if not stat.S_ISDIR(root_info.st_mode) or current.is_symlink() or reparse(root_info):
            return False
        for part in relative.parts:
            current /= part
            info = current.lstat()
            if current == path:
                if not stat.S_ISREG(info.st_mode):
                    return False
            elif not stat.S_ISDIR(info.st_mode):
                return False
            if current.is_symlink() or reparse(info):
                return False
        return True
    except (OSError, ValueError):
        return False

root = Path.cwd().absolute()
bootstrap = root / "scripts" / "run_spec_034_final_once.py"
if not regular_under(bootstrap, root):
    raise SystemExit("untrusted bootstrap path")
before = bootstrap.lstat()
bootstrap_bytes = bootstrap.read_bytes()
after = bootstrap.lstat()
if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
    raise SystemExit("bootstrap changed while read")
if not regular_under(bootstrap, root):
    raise SystemExit("bootstrap path changed while read")
if len(bootstrap_bytes) != int(sys.argv[4]):
    raise SystemExit("bootstrap length is not approved")
if hashlib.sha256(bootstrap_bytes).hexdigest() != sys.argv[2]:
    raise SystemExit("bootstrap digest is not approved")
trusted_globals = {
    "__name__": "__main__",
    "__file__": "spec034-approved/run_spec_034_final_once.py",
    "__package__": None,
    "__builtins__": __builtins__,
}
sys.argv = ["run_spec_034_final_once.py", "--review-root-sha256", sys.argv[6]]
exec(compile(bootstrap_bytes, "spec034-approved/run_spec_034_final_once.py", "exec"), trusted_globals, trusted_globals)
'@ | python -I -S - --approved-bootstrap-sha256 <H4-approved-bootstrap-sha256> --bootstrap-length <H4-approved-bootstrap-byte-length> --review-root-sha256 <H4-approved-review-root-bytes-sha256>
```

The command's positional parser is deliberately exact: `--approved-bootstrap-sha256 <digest> --bootstrap-length <length> --review-root-sha256 <root-digest>`. The inline program validates only verified bootstrap bytes, then uses `compile(bytes, approved_logical_filename, "exec")`; it never uses `runpy`, imports the bootstrap, or reopens its pathname after verification. The bootstrap analogously reads/validates final-verifier bytes and sends those exact bytes to an isolated `python -I -S -c` child for `compile`/`exec`; it never launches the final verifier by pathname. The final verifier builds one typed stable-read authority transaction containing root bytes, manifest bytes, parsed records, required external root digest, and manifest digest. Its execution records retain those approved detached bytes rather than rereading detached pathnames when snapshotting; reviewed, exactly 20 H2 source-bundle/literal blob/SHA/length records, and three predecessor-boundary-pinned Spec033 contracts are also stable-read before exclusive-write/fsync copying into one same-parent execution snapshot. Root/manifest remain external detached authority, never self-cycled manifest entries. It separately requires the exact reviewer-approved local capability manifest digest/schema/distribution list; every approved purelib file is stable-read against that manifest before copying to an exact capability snapshot. Parent child creation uses a minimal system-variable allowlist and no ambient `PYTEST_*` or startup/testing `PYTHON*` controls; it sets only `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. The runner repeats clearing every `PYTEST_*` except that flag, passes `--noconftest -o addopts=`, and uses a sealed in-memory pytest plugin to require the final verifier's literal eight C0–C7 node IDs to collect and complete as passed call reports; collect-only, selection, ignored, skipped, or xfailed runs cannot succeed by return code alone. The child accepts no snapshot extras, links, missing records, category/link mismatch, approved-top-level project shadows, or a cwd that is not the exact regular/no-link project snapshot root; it changes into that snapshot before installing verified guards or importing pytest. It then stable-reads every approved project and capability record once into an in-memory byte map before any Pytest, project, or capability import. A meta-path loader installed before `PathFinder` and Pytest rewriting compiles/executes every approved pure-Python module directly from that map; it exposes logical snapshot `__file__`/`__path__` identities and serves package resource data only from approved map bytes. A preceding snapshot-origin deny finder rejects any attempted `PathFinder` fallback into either snapshot, so `sys.path` cannot shadow or reopen Python source after validation. Native extension records are not bytes-executable and are refused rather than loaded; the final-safe closure imports no native extension. The capability manifest currently includes four native files (`ada92cb5d92a588d1b93__mypyc.cp312-win_amd64.pyd`, `charset_normalizer/cd.cp312-win_amd64.pyd`, `charset_normalizer/md.cp312-win_amd64.pyd`, and `yaml/_yaml.cp312-win_amd64.pyd`) solely as filesystem snapshot records, none as execution authority. It puts only capability snapshot then project snapshot then stdlib on `sys.path`; therefore relative C6 config paths resolve from snapshot-approved bytes, not the parent workspace. Its sole target is `tests/test_spec_034_final_acceptance.py`, a dedicated C0–C7 pure file/AST/public-seam acceptance suite. C6 calls one sealed shared synthetic helper through the public verified-report assemble/publish workflows under pre-fixture provider/external/market fail-if-called guards; the non-final regression reuses that same helper. Runner/journal/trust meta-tests remain review-sealed non-final verification. Original purelib is never added to child paths. After the child, the final verifier rechecks the external root SHA, manifest authority/current reviewed bytes, capability identity/current purelib bytes, H2 identity, predecessor identity, and both snapshots; a permanent current drift fails even where snapshot bytes are unchanged. This is a local offline verifier capability prerequisite, not a portable runtime or third-party review claim. The final verifier rejects ambient `PYTHONOPTIMIZE` and performs no `assert` checks.

Wrong bootstrap/final digest or length, reparse/link/ancestor replacement, byte drift during read, or modified-after-read pathname must fail before executable bytes run. The static focused tests exercise those preflight/byte-exec rules only with inert payloads; this document is authority documentation, not approval or execution evidence.
