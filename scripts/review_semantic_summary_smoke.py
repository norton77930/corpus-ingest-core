from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import review_semantic_summary_smoke
from corpus_ingest_core.serialization import to_jsonable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a deterministic semantic summary smoke review report."
    )
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--workflow-stdout-path", type=Path)
    args = parser.parse_args(argv)

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    if podcast_id is None or episode_ref is None:
        parser.error("必須提供 --podcast 與 --episode，或 positional podcast_id episode_ref。")

    result = review_semantic_summary_smoke(
        podcast_id,
        episode_ref,
        workflow_stdout_path=args.workflow_stdout_path,
    )
    print(json.dumps(to_jsonable(asdict(result)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
