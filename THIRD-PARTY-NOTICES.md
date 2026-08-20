# Third-Party Notices

This repository is licensed under the MIT License (see [LICENSE](LICENSE)), and
that copyright covers the first-party work only. The directories listed below
contain third-party source code that is redistributed here verbatim under its
own license. Nothing in this repository's `LICENSE` alters or supersedes the
terms below.

## NousResearch/hermes-agent

Two spec packages vendor an exact, byte-pinned snapshot of the upstream
`NousResearch/hermes-agent` repository so that a source audit can be reproduced
without fetching from the network:

| Path | Files | Pinned commit |
| --- | --- | --- |
| `specs/033-hermes-v019-pinned-source-loader-audit/upstream/NousResearch-hermes-agent-b7a05b6/` | 17 | `b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6` |
| `specs/034-hermes-v019-pinned-startup-source-graph/upstream/NousResearch-hermes-agent-b7a05b6/` | 20 | `b7a05b6b6f509d14f708a2fe7b7c1d3559396ef6` |

Both snapshots come from upstream tree `3ae46c7c1576f9a3450a64729be314ba8e853eac`.
Each file's SHA-256 is recorded in the corresponding
`contracts/source-bundle-manifest.json`, and
`tests/test_repository_secret_boundary.py` fails if any vendored byte drifts
from its pinned digest. The two file lists differ because each spec pinned the
subset its own audit needed; neither snapshot has been modified.

These files are static audit inputs. They are read for source analysis and are
never imported or executed by this project (`runtime_status=not_run`,
`live_actions_authorized=false` in the spec 034 manifest).

Upstream project: <https://github.com/NousResearch/hermes-agent>

### License

The upstream `LICENSE` is preserved verbatim at
`specs/033-hermes-v019-pinned-source-loader-audit/upstream/NousResearch-hermes-agent-b7a05b6/LICENSE`
and is reproduced in full here so that the notice travels with every copy of
this repository, as its terms require.

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
