"""Planned sealing verifier for later approved closure; not run in G0."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    return subprocess.run([sys.executable, "-m", "pytest", "tests/test_spec_029_offline.py", "tests/test_hermes_skill_protocol.py", "tests/test_mcp_tool_registry_contract.py", "-q"], cwd=ROOT, check=False).returncode
if __name__ == "__main__": raise SystemExit(main())
