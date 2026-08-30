# Releasing

Cutting a release is two commands and one GitHub action. Publishing to PyPI is
automatic once the one-time setup below is done — and it is deliberately not
automatic before that.

## One-time PyPI setup (human only)

This cannot be scripted from inside the repository, and should not be: it
grants a workflow permission to publish under a name that is claimed forever.

1. Sign in to <https://pypi.org> with the account that will own the project.
2. Go to **Your projects → Publishing** → *Add a new pending publisher*.
3. Fill in exactly:

   | Field | Value |
   | --- | --- |
   | PyPI Project Name | `corpus-ingest-core` |
   | Owner | `norton77930` |
   | Repository name | `corpus-ingest-core` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

4. In GitHub: **Settings → Environments → New environment**, named `pypi`.
   Adding yourself as a required reviewer there means every publish waits for a
   click. Recommended: it is the last point at which a mistaken release can be
   stopped.

No API token is created, stored, or rotated. PyPI verifies the workflow's
identity through OIDC, so there is no secret in this repository to leak.

Until step 2 is done the publish job fails at the upload step. Everything
before it — build, version check — still runs, so a release is never silently
half-published.

## Cutting a release

1. Update `CHANGELOG.md`: move `Unreleased` items under the new version with
   today's date, and add the comparison link at the bottom.
2. Bump `version` in `pyproject.toml`.
3. Commit, open a PR, and let CI go green on all four jobs.
4. Merge.
5. Tag the merge commit and push it:

   ```powershell
   git tag -a v0.3.0 -m "v0.3.0 — <one line>"
   git push origin v0.3.0
   ```

6. Publish a GitHub release for that tag. **That is what triggers the upload** —
   pushing the tag alone does not. A tag can be pushed by accident; publishing
   a release is a separate, explicit act, and a version on PyPI can never be
   replaced or re-uploaded.

The workflow refuses to publish if the built version does not match the tag.

## Version numbers

Semantic versioning, with the breaking-change bar set at what a user's setup
depends on: the import path, the distribution name, the MCP server name, the
tool registry order, and the environment variables.

Adding an MCP tool is a MINOR release as long as it is appended last and Tools
1..N keep their slots — that append-only property is the compatibility promise,
and `tests/test_mcp_tool_registry_contract.py` enforces it.

## Pending for 0.3.0

The `PODCAST_INGEST_*` environment variable aliases are removed in 0.3.0.
`CHANGELOG.md` promised that in 0.2.0; `src/corpus_ingest_core/local_env_names.py`
holds the mapping. Removing them is a breaking change and needs its own entry.
