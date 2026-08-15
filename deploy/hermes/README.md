# Hermes Sidecar Deployment

This bundle runs the existing exact 21-tool registry as a loopback-only Streamable HTTP service for a Hermes container that shares the Docker host network. The repository implementation and direct MCP path are operational; C6 endpoint equality is PASS-current after both reviewers and the single live v2 run. Spec 026 remains **Blocked** because C7 is unproved. Hermes v0.20.0 tag `v2026.8.3` hooks are only a promising, uninstalled candidate evidence path. Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS.

## Build and Pin

Use the staged-context wrapper as the canonical build route. It copies only package metadata, `src/`, `config/`, the HTTP runner, and the Dockerfile into a temporary WSL build context.

```powershell
wsl.exe -d UbuntuProd -u root bash scripts/build_hermes_sidecar.sh podcast-ingest-core-mcp:local
wsl.exe -d UbuntuProd -u root docker image inspect --format "{{.Id}}" podcast-ingest-core-mcp:local
```

Record the immutable image ID before deployment. The approved local build used `mcp==1.28.1`; do not silently rebuild against another SDK version. Neither `.env`, runtime data, eval evidence, repository metadata, tests, nor local agent state belongs in the image.

## Validate and Start

Set `PODCAST_INGEST_HOST_DATA_DIR` when the artifact directory is not at the Compose default. The service binds `127.0.0.1:8767`, uses host networking, publishes no port mapping, runs as the non-root `podcast` user, and restarts unless stopped.

```powershell
docker compose -f deploy/hermes/docker-compose.sidecar.yml config --quiet
docker compose -f deploy/hermes/docker-compose.sidecar.yml up -d
docker inspect --format "{{.State.Health.Status}}" podcast-ingest-core-mcp
```

Do not pass the Hermes `.env` into this container. Read-only and preview operations work without provider secrets; separately approved confirmed LLM operations require a future least-privilege secret setup.

## Config and Managed Skills

Use explicit paths and preserve the returned manifest path. The helper changes only the managed MCP entry and `skills.external_dirs`, synchronizes the allowlisted Skills, and emits no config values or endpoint values. Two allowlists are deliberately distinct: `MANAGED_SKILLS` stays the four Spec 027 contracted single-tool Skills and remains that layer's drift anchor, while `SYNCED_SKILLS` is what actually ships and additionally carries Spec 023's `historical-episode-verified-report-path` orchestrator, which names four registry tools by design and therefore cannot satisfy the Spec 027 one-tool contract. That Skill keeps its own Spec 023 contract tests. The manifest is bound to the exact `--config-path` and `--skills-target` supplied to `apply`.

```powershell
$IntegrationArgs = @(
  "--config-path", "<hermes-data>/config.yaml",
  "--skills-source", ".agents/skills",
  "--skills-target", "<hermes-data>/podcast-ingest-core-skills",
  "--local-skills-root", "<hermes-data>/skills",
  "--backup-root", "<hermes-data>/integration-backups"
)
python scripts/manage_hermes_integration.py plan @IntegrationArgs
python scripts/manage_hermes_integration.py apply @IntegrationArgs
```

If the OpenAB launcher renders live config from `hermes/config.yaml.template`, use that template as the helper's config target. Treat the credential-bearing live config as a separate protected surface: back it up byte-for-byte and apply only approved leaves through the official Hermes CLI without parsing or emitting its values. A template-bound helper manifest cannot roll back the live config bytes.

## Direct Readiness

The approved current machine already consumed its single C6 validator invocation after both reviewers passed; do not rerun it. The command below is the portable shape for a future separately authorized install. Run only in a POSIX WSL/Docker environment that can reach host loopback and has MCP 1.28.1; native Windows intentionally fails before protected path access because it lacks the required descriptor-only no-follow primitives. Mount the validator and all three protected surfaces read-only. The v2 validator performs exactly one read-only call and one `confirm=false` preview, requires MCP protocol plus application-envelope `ok=true`, checks exact tool order, and compares before/after metadata with opaque in-memory content tokens. It emits equality booleans only and fails closed on unsupported platforms, missing/malformed surfaces, `.env`/`.env.*`, symlink/reparse, and special entries. Endpoint equality does not assert that no transient mutation occurred between snapshots. It does **not** run Hermes inference and cannot satisfy C7.

```bash
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

Also verify Hermes discovery after restart:

```powershell
docker exec openab-demo-hermes hermes mcp test podcast-ingest-core
docker exec openab-demo-hermes hermes skills list --source local --enabled-only
```

## Move to Another Always-on Computer

1. Stop all artifact writers.
2. Install Linux or WSL Docker and clone OpenAB plus `podcast-ingest-core`, preferably as sibling directories.
3. Restore podcast artifacts into the persistent bind mount. Keep data, Hermes config/credentials, managed Skills, and image artifacts as separate backup units.
4. Build or load the pinned sidecar image and record its immutable image ID.
5. Validate both Compose files, then run integration `plan` and inspect only its redacted metadata.
6. Run `apply`, preserve its backup/manifest path, start the sidecar, wait for health, and restart Hermes.
7. Run direct readiness, `hermes mcp test`, and Skill discovery.
8. Keep `restart: unless-stopped` and record image ID plus data/config/Skill manifest digests.
9. C6 has reviewer-approved live v2 evidence and is PASS-current. Do not promote Spec 026 to Implemented until C7 has separately approved safe runtime evidence; v0.20.0 hooks documentation alone is insufficient.

## Upgrade and Rollback

Before an upgrade, stop writers and record the current image ID, Compose validation result, protected-surface manifests, and integration manifest path. This feature performs no artifact schema migration.

If readiness fails:

```powershell
# Restore the previous image tag/digest using the local image-management procedure.
python scripts/manage_hermes_integration.py rollback `
  --manifest "<backup-root>/<bundle>/manifest.json" `
  --config-path "<exact-manifest-bound-config-path>" `
  --skills-target "<exact-manifest-bound-skills-target>"
docker restart podcast-ingest-core-mcp
docker restart openab-demo-hermes
```

Never substitute another config path: target binding, backup digests, and post-restore digests are fail-closed. For the approved current machine, the retained helper manifest is template-bound while the exact pre-apply bundle separately holds Compose/template/live-config bytes; follow the two-path procedure in `specs/026-hermes-mcp-integration/quickstart.md`.

After rollback, compare the config/Skill digests with the manifest and wait for sidecar health. A direct validator rerun is not authorized by the current one-run C6 closure; any later readiness rerun requires a new explicit scope. Restore podcast data only from an operator-created backup while all writers are stopped. Historical v1 smoke observed metadata stability only; the single v2 live run later passed endpoint metadata/content equality. A future artifact migration requires a separate dry-run, version marker, backup, acceptance check, and reverse procedure.
