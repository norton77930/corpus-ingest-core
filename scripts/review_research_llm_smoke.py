from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import review_research_llm_smoke
from corpus_ingest_core.serialization import to_jsonable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic Research LLM smoke review report.")
    parser.add_argument("podcast_id", nargs="?")
    parser.add_argument("episode_ref", nargs="?")
    parser.add_argument("stock_query", nargs="?")
    parser.add_argument("--podcast", dest="podcast_option")
    parser.add_argument("--episode", dest="episode_option")
    parser.add_argument("--stock", dest="stock_option")
    parser.add_argument("--workflow-stdout-path", type=Path)
    parser.add_argument("--raw-output-path", type=Path)
    args = parser.parse_args(argv)

    podcast_id = args.podcast_option or args.podcast_id
    episode_ref = args.episode_option or args.episode_ref
    stock_query = args.stock_option or args.stock_query
    if podcast_id is None or episode_ref is None or stock_query is None:
        parser.error("Provide --podcast, --episode, and --stock, or positional podcast_id episode_ref stock_query.")

    result = review_research_llm_smoke(
        podcast_id,
        episode_ref,
        stock_query,
        workflow_stdout_path=args.workflow_stdout_path,
        raw_output_path=args.raw_output_path,
    )
    print(json.dumps(to_jsonable(asdict(result)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
