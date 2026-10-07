"""Operator learning acceptance; metadata-only stdout, no installation or repair."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from corpus_ingest_core.learning_mcp_acceptance import inventory_learning_skills, verify_learning_connection


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('inventory', help='Check complete repository Skill resources, without installing')
    verify = commands.add_parser('verify', help='Verify one prepared time range through MCP')
    connection = verify.add_mutually_exclusive_group(required=True)
    connection.add_argument('--data-dir', type=Path, help='Explicit owned local corpus for a separate stdio SDK check')
    connection.add_argument('--mcp-url', help='Already managed numeric-loopback HTTP endpoint')
    verify.add_argument('--podcast', required=True)
    verify.add_argument('--episode', required=True)
    verify.add_argument('--start', type=float, required=True)
    verify.add_argument('--end', type=float, required=True)
    verify.add_argument('--max-calls', type=int, default=20)
    verify.add_argument('--max-total-chars', type=int, default=60000)
    verify.add_argument('--timeout', type=float, default=60)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.action == 'inventory':
        result = inventory_learning_skills(Path(__file__).resolve().parents[1] / '.agents/skills')
    else:
        result = asyncio.run(verify_learning_connection(data_dir=args.data_dir, mcp_url=args.mcp_url,
            timeout_seconds=args.timeout, podcast_id=args.podcast, episode_ref=args.episode,
            start_seconds=args.start, end_seconds=args.end, max_calls=args.max_calls,
            max_total_chars=args.max_total_chars))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
