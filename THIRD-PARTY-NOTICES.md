# Third-Party Notices

This repository is licensed under the MIT License (see [LICENSE](LICENSE)), and
that copyright covers the first-party work only.

**No third-party source is vendored on `main`.** Everything under `src/`,
`tests/`, `scripts/`, and `specs/` on this branch is first-party work. The
project's runtime dependencies are declared in `pyproject.toml` and installed
from PyPI; they are not redistributed here.

## NousResearch/hermes-agent (archived, still reachable by tag)

Spec packages 026-034 vendored an exact, byte-pinned snapshot of the upstream
`NousResearch/hermes-agent` repository so that a source audit could be
reproduced without fetching from the network. That audit chain terminated
BLOCKED and was removed from `main`; the complete history, including both
snapshots, is preserved at the tag `archive/hermes-audit-chain`.

A `git clone` fetches tags, so those bytes still travel with every copy of this
repository. The upstream notice is therefore reproduced below, as its terms
require.

| Archived path (at `archive/hermes-audit-chain`) | Files | Pinned commit |
| --- | --- | --- |
| `specs/033-hermes-v019-pinned-source-loader-audit/upstream/NousResearch-hermes-agent-b7a05b6/` | 17 | `b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6` |
| `specs/034-hermes-v019-pinned-startup-source-graph/upstream/NousResearch-hermes-agent-b7a05b6/` | 20 | `b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6` |

Both snapshots come from upstream tree `3ae46c7c1576f9a3450a64729be314ba8e853eac`.
They were static audit inputs: read for source analysis, never imported or
executed by this project, and never modified.

Upstream project: <https://github.com/NousResearch/hermes-agent>

### License

```
MIT License

Copyright (c) 2025 Nous Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
