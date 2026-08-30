# Contributing

Thanks for looking. This is a working research project, not a product with a
support team, so the most useful thing this document can do is tell you where
the tripwires are before you hit one.

Read [`AGENTS.md`](AGENTS.md) too. Its Engineering Rules are authoritative and
apply to humans and agents alike; everything here is compatible with it.

Participation is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Setting up

```powershell
git clone https://github.com/norton77930/corpus-ingest-core.git
cd corpus-ingest-core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Python 3.11 or newer. **Do not skip `pip install -e .`** — several tests spawn
subprocesses, and `pythonpath = ["src"]` in `pyproject.toml` covers pytest
itself but nothing it spawns. Without the install those tests fail with
`ModuleNotFoundError: No module named 'corpus_ingest_core'`, and the cause is
not obvious from the message.

Video ingestion has one extra setup detail that is easy to miss:

- **A recent `yt-dlp`.** YouTube breaks older releases, and the failure is
  confusing: metadata resolves fine and then the media URL returns `HTTP 403`.
  `pip install -U yt-dlp` before a live run.

The current X and YouTube ingest path does not require an `ffmpeg` executable
on `PATH`. It asks yt-dlp for `bestaudio/best`, so no selector branch merges
streams; PyAV converts the selected source media to the corpus WAV.

Full setup and porting notes, including GPU transcription, are in
[`docs/install-and-porting.md`](docs/install-and-porting.md).
Cutting a release is in [`docs/releasing.md`](docs/releasing.md).

## Verifying a change

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

`python -m pytest` should be **fully green** — there is no `--ignore` list and
no expected-failure set. If it is not green, look at your environment before you
look at your change: `test_mcp_http_transport` spawns a subprocess, so it goes
red whenever the environment does not match what `pyproject.toml` declares
(most often because `pip install -e .` was skipped).

Run the targeted tests for your change type first —
[`docs/verification-matrix.md`](docs/verification-matrix.md) maps change types to
the guard tests that cover them.

## Rules that are not up for discussion

These are product boundaries, not style preferences. A change that crosses one
will not be merged regardless of how good the code is.

- **No investment advice.** No buy/sell/hold, no target prices, no guaranteed
  returns, nothing personalized. The project produces research artifacts, and
  that line is the reason it can.
- **No live market API** unless a future approved phase explicitly adds one.
- **`.env` stays local.** Never read, print, commit, or paste it.
- **Side-effect workflows are dry-run first.** A tool that writes takes
  `confirm=true`; without it the run must plan and write nothing.
- **Never auto-rebuild the SQLite cache** after a side-effect tool. Warn that
  the cache may be stale and let the operator rebuild.
- **Thin CLI, thick core.** Scripts parse arguments and call
  `corpus_ingest_core`. Logic does not live in `scripts/`.
- **TDD for new behavior**, and keep the change surgical.

## Traps specific to this repository

- **`README.md` is a contract surface.** More than a dozen test files assert on
  its content. Check before you reword a heading. `README.zh-TW.md` is a
  translation and must not drift from it.
- **`config/podcasts.yaml` has an exact-set assertion** in
  `tests/test_contracts.py`. Adding a profile for a local run turns that test
  red until you remove it again. This is deliberate: it stops an operator's
  personal profile from being committed by accident.
- **`data/` is entirely gitignored** and must stay that way. It holds
  third-party audio, transcripts, and derived reports. Nothing under it belongs
  in a commit, an issue, or a pull request.
- **Windows only, in practice.** PowerShell is the default shell, and pytest is
  configured with a repo-local basetemp because long temp paths hit the 260-char
  `MAX_PATH` limit. Run pytest from the repo root.

## Feature work

New features go through Spec Kit before implementation, not after:

```text
constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge
```

Packages live in `specs/<nnn>-<name>/`; [`specs/README.md`](specs/README.md) is
the registry and explains how to select one. Set `SPECIFY_FEATURE_DIRECTORY`
explicitly — the repo does not pin a single active feature.

For a bug fix or a small correction, skip all of that and open a pull request.

## Pull requests

Say what changed, why, and how you verified it. If verification was partial or
you skipped something, say so plainly — that is more useful than a clean-looking
report that hides a gap.

Commit messages here explain reasoning rather than restating the diff. Recent
history is a reasonable guide to the expected shape.

## Security

Do not open a public issue for a vulnerability. See
[`SECURITY.md`](SECURITY.md).
