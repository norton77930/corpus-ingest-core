"""Thin fixed one-job process entry; admitted job metadata is the authority."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))
from corpus_ingest_core.source_preparation_worker import run_worker


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Process one already admitted source job.")
    parser.add_argument("job_id")
    args = parser.parse_args(argv)
    return run_worker(args.job_id)


if __name__ == "__main__":
    raise SystemExit(main())
