# Contributing

Thanks for looking. This is a working research project, not a product with a
support team, so the most useful thing this document can do is tell you where
the tripwires are before you hit one.

Read [`AGENTS.md`](AGENTS.md) too. Its Engineering Rules are authoritative and
apply to humans and agents alike; everything here is compatible with it.

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
`ModuleNotFoundError: No module named 'podcast_ingest_core'`, and the cause is
not obvious from the message.

Video ingestion needs two more things that are easy to miss:

- **`ffmpeg` on `PATH`**, for YouTube only. yt-dlp has to merge YouTube's
  separate video and audio streams; X serves pre-muxed MP4 and never needs it.
- **A recent `yt-dlp`.** YouTube breaks older releases, and the failure is
  confusing: metadata resolves fine and then the media URL returns `HTTP 403`.
  `pip install -U yt-dlp` before a live run.

Full setup and porting notes, including GPU transcription, are in
[`docs/install-and-porting.md`](docs/install-and-porting.md).

## Verifying a change

```powershell
python -m pytest
python -m compileall src scripts
git diff --check
```

`python -m pytest` should be **fully green**. If it is not, look at your
environment before you look at your change: `test_spec_029_offline`,
`test_mcp_http_transport`, and `test_hermes_runtime_capability` are deliberately
kept in the default run precisely because they go red when the environment does
not match what `pyproject.toml` declares.

Run the targeted tests for your change type first —
[`docs/verification-matrix.md`](docs/verification-matrix.md) maps change types to
the guard tests that cover them.

The blocked Hermes 030–034 doc chain is excluded from the default run. Those
tests are expected to fail, for reasons recorded next to the exclusion list in
`pyproject.toml`. Naming a path explicitly still runs one.

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
  `podcast_ingest_core`. Logic does not live in `scripts/`.
- **TDD for new behavior**, and keep the change surgical.

## Traps specific to this repository

This repo carries audit records that bind file contents by hash. Editing the
wrong file does not just break a test — it falsifies a record.

- **`specs/033-*/upstream/` and `specs/034-*/upstream/`** are byte-pinned
  snapshots of third-party source, tied to digests in each spec's
  `contracts/source-bundle-manifest.json`. Do not edit, add to, or reformat
  anything under those directories. See
  [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).
- **The `contracts/reviewed-artifact-manifest.json` files** in specs 032, 033,
  and 034 pin roughly thirty files under `tests/` and `scripts/` by hash.
  If a test in the blocked chain is wrong, you cannot simply mark it `xfail`.
- **Several blocked-chain tests pin the byte length** of `README.md`,
  `docs/roadmap.md`, `specs/README.md`, and `pyproject.toml` to the snapshot
  taken when that spec was reviewed. This is why those tests are excluded by
  default rather than repaired.
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
