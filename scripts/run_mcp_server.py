from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core.mcp_server import run

if __name__ == "__main__":
    run()
