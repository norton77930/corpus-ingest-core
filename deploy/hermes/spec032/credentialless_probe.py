"""Definition-only future probe contract; intentionally does not invoke Hermes."""
from __future__ import annotations

# An official-loader probe may only be implemented after actual pinned source
# bytes prove the loader call path.  No fake credential, direct registration,
# provider, query, prompt, inference, MCP, tool-call, or Core path is present.


def main() -> int:
    return 3  # blocked_unknown; no stdout/stderr contract surface


if __name__ == "__main__":
    raise SystemExit(main())
