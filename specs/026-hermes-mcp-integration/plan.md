# Implementation Plan: Hermes MCP and Portable Skills Integration

**Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

## Summary

Add a Streamable HTTP startup seam around the existing single FastMCP object, package it as a loopback-only host-network sidecar, incrementally merge one Hermes MCP entry and one managed Skills directory with rollback, perform safe live validation, and document migration to another Linux/WSL Docker host.

## Constitution Check

No amendment. Stable core contracts are protected by the unmodified 21-tool registry test. Side effects remain preview-first where their existing specs require it. No secret, cache rebuild, market-data, or investment-advice surface is added.

## Approved Runtime Topology

```text
Hermes container (network_mode: host)
        |
        | http://127.0.0.1:8767/mcp
        v
podcast-ingest-core-mcp sidecar (network_mode: host)
        |
        v
persistent host podcast data mount
```

The port is fixed at 8767 unless preflight proves it occupied; collision stops implementation and requires an approved plan amendment rather than automatic fallback.

## Batches

| Batch | Content |
| --- | --- |
| B0 | Spec/contracts/checklists/tasks and read-only Hermes/SDK preflight |
| B1 | RED tests then single-instance Streamable HTTP configuration/runner; stdio and registry freeze |
| B2 | Sidecar Dockerfile, host-network Compose bundle, deployment contract tests |
| B3 | RED tests then structured Hermes config merge and four-Skill manifest sync/rollback |
| B4 | Backup, incremental OpenAB Compose/config/Skill apply, image build/start, direct MCP readiness |
| B5 | Direct safe smoke plus exactly one bounded Hermes natural-language preview |
| B6 | Portable operations docs, converge, code/architecture review, one final verification invocation |

## Project Structure

```text
specs/026-hermes-mcp-integration/
src/podcast_ingest_core/mcp_runtime.py
src/podcast_ingest_core/mcp_server.py
src/podcast_ingest_core/hermes_integration.py          (new)
scripts/run_mcp_http_server.py                         (new)
scripts/manage_hermes_integration.py                   (new)
scripts/validate_hermes_integration.py                 (new)
deploy/hermes/Dockerfile                               (new)
deploy/hermes/docker-compose.sidecar.yml               (new)
deploy/hermes/README.md                                (new)
tests/test_mcp_http_transport.py                       (new)
tests/test_hermes_integration.py                       (new)
tests/test_hermes_deployment_contract.py               (new)
```

External approved target:

```text
../openab/demo-local/docker-compose.yml
../openab/demo-local/hermes/config.yaml.template
../openab/demo-local/hermes-data/config.yaml
../openab/demo-local/hermes-data/podcast-ingest-core-skills/
../openab/demo-local/hermes-data/integration-backups/
```

## Reused Existing Boundaries

- `mcp_runtime.mcp` remains the sole server object and registry owner.
- `mcp_server` remains the public facade and re-export boundary.
- `PODCAST_INGEST_DATA_DIR` remains the single data-root override.
- PyYAML is reused for structured config handling; no dependency is added.
- The four `.agents/skills/*` directories remain the source of truth and are copied without semantic edits.

## TDD Seams

1. stdio `mcp_runtime.run()` public behavior.
2. new `run_streamable_http(config)` startup boundary and object identity.
3. `manage_hermes_integration` plan/apply/rollback JSON-safe result envelope.
4. sidecar Docker/Compose static contract.
5. direct MCP HTTP protocol validation.
6. one fresh-session Hermes natural-language preview.

## Risks

- SDK settings drift inside `mcp>=1.27,<2`: use only verified public attributes and fail closed on unsupported API.
- Host-network port collision: fixed preflight; no fallback.
- YAML clobber/secret output: synthetic preservation and redaction tests plus atomic backup.
- Skill shadowing: path-existence fail-closed before copy.
- Data mount error: verify path identity and before/after manifest.
- Hermes trace insufficiency: C7 remains blocked; v0.20.0 tag `v2026.8.3` hooks are candidate capability only because fallback evidence and an approved safe projection are absent. No upgrade, hook enablement, inference rerun, or session-dump workaround occurs in this plan.

## Verification

Per batch: targeted RED/GREEN tests only. The C6 live validator is a separate reviewer-gated invocation and may run at most once; it is not the feature final verification. After every required claim including C7 passes and both reviewers pass, one final command invocation runs the full pytest suite, compileall, both Compose validations, both-repo `git diff --check`, and secret/SSE/second-FastMCP guards. C7 is expected to remain blocked in this batch, so final-verification invocation count remains zero and live inference is not repeated.
