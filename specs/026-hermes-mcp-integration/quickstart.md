# Quickstart: Hermes MCP Sidecar

> Never source, print, copy into evidence, or commit either repository's `.env`, provider values, private endpoints, live config values, or Hermes session data.

## Current Computer

```powershell
# 1. Build from the narrow staged context and record the immutable image ID.
wsl.exe -d UbuntuProd -u root bash scripts/build_hermes_sidecar.sh podcast-ingest-core-mcp:local
wsl.exe -d UbuntuProd -u root docker image inspect --format "{{.Id}}" podcast-ingest-core-mcp:local

# 2. Validate both Compose definitions before changing runtime state.
docker compose -f deploy/hermes/docker-compose.sidecar.yml config --quiet
docker compose -f <openab>/demo-local/docker-compose.yml config --quiet

# 3. Plan and apply only the managed template/Skill transaction.
# On the approved OpenAB installation, run.sh renders the live config from this template.
$IntegrationArgs = @(
  "--config-path", "<openab>/demo-local/hermes/config.yaml.template",
  "--skills-source", ".agents/skills",
  "--skills-target", "<openab>/demo-local/hermes-data/podcast-ingest-core-skills",
  "--local-skills-root", "<openab>/demo-local/hermes-data/skills",
  "--backup-root", "<openab>/demo-local/hermes-data/integration-backups"
)
python scripts/manage_hermes_integration.py plan @IntegrationArgs
python scripts/manage_hermes_integration.py apply @IntegrationArgs

# The credential-bearing live config is a separate surface. On the approved machine it
# was backed up byte-for-byte and only approved leaves were set through Hermes CLI;
# this session did not parse or emit its values.

# 4. Start sidecar, wait for health, restart Hermes, and verify discovery.
docker compose -f <openab>/demo-local/docker-compose.yml up -d podcast-ingest-core-mcp
docker inspect --format "{{.State.Health.Status}}" podcast-ingest-core-mcp
docker restart openab-demo-hermes
docker exec openab-demo-hermes hermes mcp test podcast-ingest-core
docker exec openab-demo-hermes hermes skills list --source local --enabled-only

# 5. Portable command shape for a future separately authorized install.
# The approved current machine already consumed its one C6 invocation; do not rerun it.
# Use a POSIX WSL/Docker shell; native Windows fails before protected path access.
docker run --rm --network host --entrypoint python \
  --mount type=bind,src="<repo>/scripts/validate_hermes_integration.py",dst=/work/validate_hermes_integration.py,readonly \
  --mount type=bind,src="<podcast-data>",dst=/protected/podcast-data,readonly \
  --mount type=bind,src="<hermes-data>/config.yaml",dst=/protected/config.yaml,readonly \
  --mount type=bind,src="<hermes-data>/podcast-ingest-core-skills",dst=/protected/skills,readonly \
  podcast-ingest-core-mcp:local /work/validate_hermes_integration.py \
  --data-path /protected/podcast-data \
  --config-path /protected/config.yaml \
  --skills-path /protected/skills
```

The `hermes-direct-smoke-v2` validator emits only protocol/server versions, exact tool names/count/order digest, fixed call counts, protocol-plus-application success booleans, preview safety booleans, and per-surface before/after metadata/content equality booleans. Protected bytes are opaque in-memory hash input only; protected digest, token, path, content, config value, MCP URL, raw response, prompt, and session data are never emitted or persisted. POSIX descriptor-only traversal rejects missing/malformed surfaces, `.env`/`.env.*`, symlink/reparse, and special entries before content access; unsupported platforms fail before protected path access. Endpoint equality does not assert absence of transient mutation between snapshots. For the approved current machine, both reviews and the single live run passed, so C6 is PASS-current; the command above is retained as a portable procedure but must not be rerun under the current closure.

## Natural-language Gate

A fresh-session Hermes request may be attempted only with one preview-safe Skill, only the `podcast-ingest-core` toolset, bounded turns, and no `confirm=true`, second action, shell/terminal fallback, download, transcription, summary, or publication.

Hermes v0.19.0 completed the bounded request with protected-surface metadata unchanged. The later reviewer-approved v2 direct run established before/after metadata/content endpoint equality, so C6 is **PASS-current**. v0.19.0 safe CLI output still did not prove the C7 one-call and argument facts. Official v0.20.0 tag `v2026.8.3` hooks are promising but insufficient because no canonical fallback indicator or approved safe projection collector exists; the candidate was not installed or runtime-tested, so C7 remains **BLOCKED/FAIL**. Do not rerun the validator or inference, inspect session dumps, save raw responses, upgrade Hermes, enable hooks, or mark the feature Implemented under this plan. Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS.

## Another Always-on Computer

1. Stop all artifact writers.
2. Install Linux or WSL Docker and clone OpenAB plus `podcast-ingest-core` as sibling directories.
3. Restore podcast artifacts to the persistent bind mount. Restore Hermes credentials separately from config and managed Skills; never place `.env` in either repository.
4. Build or load the pinned sidecar image and record its immutable ID.
5. Validate both Compose files, run helper `plan`, then `apply`; preserve the returned integration manifest.
6. Start the sidecar and Hermes; run health, direct readiness, MCP discovery, and Skill discovery.
7. Keep `restart: unless-stopped`; record image, data, config-metadata, and Skill-manifest digests.
8. C6 is PASS-current from the one reviewer-approved live v2 run. Keep the feature blocked until C7 has separately approved safe structured runtime evidence; v0.20.0 hooks documentation alone is insufficient.

## Upgrade and Rollback

- Stop writers and create separate data/config/Skills backups before an upgrade.
- Record the previous image ID, integration manifest path, Compose validation result, and protected-surface metadata digests.
- Start the new image and run direct-safe validation.
- A helper manifest is bound to the exact config and Skill targets recorded when `apply` ran. Rollback MUST pass those same paths; never substitute a live config path for a template-bound manifest.

### Current approved machine

The retained helper manifest is:

```text
<openab>/demo-local/hermes-data/integration-backups/20260809T124217Z-12375d1c/manifest.json
```

It is bound to `hermes/config.yaml.template` plus `hermes-data/podcast-ingest-core-skills`; its config transaction was a no-op and its Skill transaction was the first install. Use it only for that exact transaction:

```powershell
python scripts/manage_hermes_integration.py rollback `
  --manifest "<openab>/demo-local/hermes-data/integration-backups/20260809T124217Z-12375d1c/manifest.json" `
  --config-path "<openab>/demo-local/hermes/config.yaml.template" `
  --skills-target "<openab>/demo-local/hermes-data/podcast-ingest-core-skills"
```

A full machine-level reversion is a separate byte-backup route. The authorized pre-apply bundle is `<openab>/demo-local/hermes-data/integration-backups/spec026-preapply-20260809-01/` and contains the prior OpenAB Compose file, template, and credential-bearing live config bytes. With writers and both containers stopped, restore each file byte-for-byte to its original matching path; do not parse, print, diff, or substitute its contents. The bundle has no prior managed-Skills backup because that target did not exist; the exact helper rollback above removes the first-installed target.

### Future portable installs

Preserve each returned manifest with its exact target paths. On failure, restore the previous image, invoke helper rollback with those exact paths, restart sidecar/Hermes, verify health/discovery, and compare the restored config/Skill digests with the manifest. Restore podcast data only from an operator-created backup while writers remain stopped.

This feature performs no artifact schema migration. Any future migration requires its own dry-run, version marker, backup, acceptance check, and reverse procedure.
