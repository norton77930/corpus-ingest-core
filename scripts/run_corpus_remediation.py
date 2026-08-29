from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus_ingest_core import PodcastIngestCoreError, run_corpus_remediation
from corpus_ingest_core.corpus_remediation_runner import result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview or run deterministic corpus remediation actions."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--episode", dest="episode_ref")
    parser.add_argument("--action-family", dest="action_family")
    parser.add_argument("--max-actions", type=int, dest="max_actions")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-partial", action="store_true", dest="allow_partial")
    args = parser.parse_args(argv)

    try:
        result = run_corpus_remediation(
            args.podcast_id,
            confirm=args.confirm,
            episode_ref=args.episode_ref,
            action_family=args.action_family,
            max_actions=args.max_actions,
            force=args.force,
            allow_partial=args.allow_partial,
        )
    except (PodcastIngestCoreError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
