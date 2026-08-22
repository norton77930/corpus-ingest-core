# Security Policy

## Reporting a vulnerability

Report privately through GitHub, not in a public issue:

**[Open a private security advisory](https://github.com/norton77930/corpus-ingest-core/security/advisories/new)**

That form is visible only to the maintainer. A public issue publishes the
details to everyone, including anyone who would misuse them, before there is a
fix.

Please include what you can: the affected file or tool, what an attacker gains,
and the smallest reproduction you have. A rough report beats a delayed one.

This is a personal research project with a single maintainer, so there is no
response-time guarantee. Reports are read and answered; complicated ones may
take a while.

## Supported versions

Only `main` is supported. There are no releases and no backports.

## Scope

The pipeline runs entirely on your own machine. It has no hosted service, no
account system, no telemetry, and it never sends the corpus anywhere. Most of
the security surface is therefore about what the code does *to the machine
running it*, and what it might leak from that machine.

In scope:

- Anything that writes outside the configured `data/` tree, or that escapes a
  `podcast_id` / `episode_ref` into a path (`tests/test_artifact_lock.py`
  guards this).
- Anything that leaks a secret, a credential, a local absolute path, or a
  private endpoint into committed files, tool output, logs, or an MCP response.
- Anything that makes the video acquisition path carry credentials.
  `video_acquire._assert_guest_options` refuses `cookiefile`,
  `cookiesfrombrowser`, `username`, `password`, and `videopassword`, and forces
  `ignoreconfig` so a user's own yt-dlp config cannot inject them. A way around
  that is a vulnerability.
- Command or code injection through a URL, a feed, a transcript, a profile
  name, or any other untrusted input.
- An MCP tool performing a side effect without `confirm=true`, or a dry-run
  that writes.

Out of scope:

- Vulnerabilities in dependencies themselves. Report those upstream. Do tell us
  if this project uses one in a way that makes it exploitable when it otherwise
  would not be.
- Anything requiring an attacker to already have write access to your machine,
  your `config/`, or your `.env`.
- The absence of authentication on the local MCP server. It is designed to be
  reached over stdio by a local client. If you expose the HTTP transport to a
  network, securing that is your deployment's job.
- Transcription accuracy, summary quality, or anything about the *content* of
  what the pipeline produces.

## Handling secrets in this repository

`.env` is local-only. It is gitignored, and it must never be read, printed,
committed, or pasted into an issue. `.env.example` carries the key names with
obvious placeholders, never real values.

`tests/test_repository_secret_boundary.py` runs on every default `pytest` and
fails the build on API-key-shaped strings and private endpoints in committed
files. It is a guard, not a guarantee: if you find a way past it, that is worth
reporting.

## A note on corpus content

Everything under `data/` — audio, transcripts, summaries, reports — is
gitignored and stays on your machine. Much of it is derived from third-party
material whose rights belong to its publishers. Do not attach corpus content to
a report; describe the shape of the input instead.
