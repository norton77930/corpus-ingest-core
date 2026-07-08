from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from podcast_ingest_core import (
    PodcastIngestCoreError,
    generate_corpus_remediation_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic local corpus remediation plan."
    )
    parser.add_argument("--podcast", required=True, dest="podcast_id")
    args = parser.parse_args(argv)

    try:
        result = generate_corpus_remediation_plan(args.podcast_id)
    except (PodcastIngestCoreError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(_result_to_dict(result), ensure_ascii=False, indent=2))
    return 0


def _result_to_dict(result):
    return {
        "podcast_id": result.podcast_id,
        "plan_json_path": str(result.plan_json_path),
        "plan_markdown_path": str(result.plan_markdown_path),
        "source_corpus_index_json_path": str(result.source_corpus_index_json_path),
        "source_corpus_index_markdown_path": str(
            result.source_corpus_index_markdown_path
        ),
        "episode_count": result.episode_count,
        "warning_count": result.warning_count,
        **asdict(result.action_counts),
    }


if __name__ == "__main__":
    raise SystemExit(main())
