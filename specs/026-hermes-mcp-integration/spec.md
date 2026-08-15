# Feature Specification: Hermes MCP and Portable Skills Integration

**Feature Branch**: `feat/corpus-semantic-completion-workflows`  
**Created**: 2026-08-09  
**Status**: Blocked — repository implementation, sidecar deployment, config/Skill integration, recovery runbook, and FR-010/C6 reviewer-approved live endpoint-equality evidence are present and PASS-current. FR-011/C7 remains unproved. Hermes v0.20.0 tag `v2026.8.3` hooks are a promising but insufficient candidate evidence path, not runtime evidence.

**Input**: Expose the existing exact 21-tool MCP registry to the local Docker-hosted Hermes Agent through a persistent Streamable HTTP sidecar, install the four existing portable Skills without changing their contracts, validate one bounded natural-language preview, and document migration to another always-on computer.

## Clarifications

### Session 2026-08-09

- Architecture: one existing `FastMCP` instance, existing stdio preserved, one additional Streamable HTTP runner, no SSE.
- Deployment: `podcast-ingest-core-mcp` sidecar and Hermes both use host networking; the MCP server binds `127.0.0.1` and is not published externally.
- Registry freeze: no Tool 22; names, registration order, signatures, defaults, envelopes, and existing stdio behavior remain unchanged.
- Runtime integration is an approved R2 cross-repository/config change limited to the paths listed in the approved implementation plan; no commit or push.
- Configuration: structured incremental YAML merge with backup/rollback; the historical tail-replacement patch script is not reused. Because OpenAB `run.sh` regenerates live config, the approved scope also updates `hermes/config.yaml.template` with the same non-secret managed entries.
- Secrets: `.env`, credentials, tokens, provider values, private endpoints, and Hermes session dumps are never read or emitted.
- Skills: the four repository Skills are synchronized byte-for-byte. Specs 016/018/019 keep preview→approval→confirm. Spec 017 keeps its existing one-request/one-confirm contract and is excluded from the preview smoke.
- Live validation: direct read-only/`confirm=false` calls plus exactly one bounded Hermes inference; no confirmed content-processing action.

### Validation outcome 2026-08-09

- Built image `sha256:c8ca1182966a3dc710df96a72017d5760cf5c068f1f52d3bbe9f56bdab263b6e` with `mcp==1.28.1`, non-root user `podcast`, and the HTTP runner as entrypoint.
- Both Compose definitions validated; the sidecar became healthy; direct MCP and `hermes mcp test podcast-ingest-core` reported the exact 21-tool registry with order digest `e71b93866a86503155967cc1648cbc83ce1407815fb6d1724c32712fc305076d`.
- Historical v1 evidence covered metadata only. After both required reviewers passed, exactly one explicitly authorized `hermes-direct-smoke-v2` run exited 0 with `ok=true`, exact 21-tool order/digest, one read-only call, one `confirm=false` preview, `dry_run=true`, `requires_confirmation=true`, and all three protected surfaces reporting both metadata and content endpoint equality. C6 is PASS-current; no protected digest, token, path, content, or value was emitted or persisted, and the run is not repeated.
- One bounded Hermes inference exited successfully with protected-surface metadata unchanged and no safe-output shell/terminal marker. Hermes v0.19.0 safe CLI output did not expose unambiguous structured tool-call count or actual `confirm` arguments, so FR-011/C7 remains blocked. Official Hermes v0.20.0 tag `v2026.8.3` documents per-call `pre_tool_call`/`post_tool_call` hooks with tool names and arguments, but no canonical fallback indicator or approved safe projection collector; this is candidate capability only, with runtime validation not evaluated. No session dump, raw response, prompt, config value, endpoint, or credential was inspected or persisted.

## Spec 027 amendment pointer

Spec 027 adds an offline assurance-only contract layer for closed Skill routing, bounded event reducers, and safe evidence. It neither changes nor reopens C6: C6 is PASS-current only for its existing direct endpoint-equality evidence. Spec 027 contract layer is complete (offline assurance only); actual Hermes runtime routing is BLOCKED/not_evaluated and is not a runtime PASS.

## Spec 028 successor pointer

Spec 028 is the successor offline capability gate for the specific unresolved runtime-observation evidence question. It does not modify, invoke, or reopen C6: C6 is PASS-current only for its existing direct endpoint-equality evidence. Spec 028 capability gate is complete and correctly terminates at BLOCKED_CAPABILITY for Hermes v0.20.0 tag v2026.8.3; no upgrade, Skill sync, hooks, collector, inference, or runtime observation was performed. C6 remains PASS-current and was not rerun; actual Hermes Skill routing remains BLOCKED/not_run. Spec 029 successor pointer: its offline implementation adds no runtime evidence; live preflight not run, G2-G3 not authorized, and its pinned source contract is `BLOCKED_RUNTIME_SEAM`.

## User Scenarios & Testing

### User Story 1 — Hermes can discover and safely call the existing MCP (P1)

An operator starts the sidecar and Hermes discovers exactly the existing 21 tools. A natural-language request can invoke one preview-safe Skill and stop after one `confirm=false` call.

**Independent Test**: direct Streamable HTTP `initialize`/`tools/list`, one read-only call, one preview call, then one fresh-session Hermes inference with filtered tool-call evidence.

### User Story 2 — Existing interfaces do not regress (P1)

Current stdio clients continue to launch the server exactly as before, and the registry contract remains byte-for-byte compatible at its public surface.

**Independent Test**: `tests/test_mcp_tool_registry_contract.py` remains unmodified and green; a new identity/transport test proves stdio and HTTP use the same `mcp` object.

### User Story 3 — Configuration and Skills are recoverable (P1)

An operator can plan, apply, no-op, and roll back the Hermes config and four managed Skills without overwriting unrelated settings or local Skills.

**Independent Test**: synthetic YAML/directory tests cover preserve-existing, no-op, pre-mutation recovery manifest, recoverable staged replacement, failure injection, redacted output, manifest/backup integrity, shadow collision, post-rollback digest verification, and rollback.

### User Story 4 — The deployment can move to another computer (P2)

An operator can restore data, config, Skills, and the pinned image independently on another Linux/WSL Docker host, verify readiness, and roll back an upgrade.

**Independent Test**: deployment contract tests plus a runbook tabletop using actual path/image/config/Skill digests without secret values.

## Safety and Data Boundaries

- The HTTP listener MUST remain loopback-only under the approved host-network topology.
- No legacy SSE transport, host port publication, disabled DNS rebinding protection, or automatic port fallback.
- Live smoke MUST NOT run download, transcription, extraction, semantic summary, report publication, or any request with `confirm=true`.
- Protected-surface before/after evidence MUST fail closed on missing/invalid surfaces. The authorized v2 path may read protected bytes only as opaque input to in-memory SHA-256 tokens through POSIX descriptor-only, `O_NOFOLLOW` traversal; unsupported platforms, including native Windows, MUST fail before protected path access. It MUST reject `.env`/`.env.*`, symlink/reparse, and special entries before content access, and MUST emit no protected content, path, or digest. Both reviewers and the single live run passed; C6 is PASS-current and must not be rerun under this closure.
- Hermes may normally write its own state/log/session data; those files are neither inspected nor included in the protected-surface claim.
- No investment advice, live market API, cache rebuild, credential access, or secret propagation is introduced.

## Requirements

- **FR-001**: Keep exactly one `FastMCP` construction and reuse that object for stdio and Streamable HTTP.
- **FR-002**: Keep `scripts/run_mcp_server.py` and `mcp_runtime.run()` stdio behavior unchanged.
- **FR-003**: Add a validated HTTP startup seam restricted to host `127.0.0.1`, path `/mcp`, configured fixed port, and transport `streamable-http`.
- **FR-004**: Keep all 21 tool names/order/signatures/defaults/envelopes unchanged; the existing registry contract test MUST not be edited.
- **FR-005**: Provide a non-root sidecar image that explicitly copies only required source/config files, uses persistent `PODCAST_INGEST_DATA_DIR`, and includes no `.env`, runtime data, repository metadata, or Hermes state.
- **FR-006**: Provide host-network Compose configuration with loopback binding, `restart: unless-stopped`, bounded healthcheck, no `ports`, and no SSE.
- **FR-007**: Structured config merge MUST modify only the managed MCP entry and external Skills directory, preserve unknown/existing entries, no-op without writes, backup before apply, validate staged YAML, atomically replace, preserve permissions, redact values, and support manifest-bound rollback.
- **FR-008**: Skill sync MUST allow exactly four named Skills, copy complete directories byte-for-byte, use SHA-256 manifests, no-op identical content, persist a pre-mutation recovery manifest, use crash-recoverable staged replacement, fail on local-name shadowing, and support digest-verified rollback. It does not claim an uninterrupted atomic directory exchange.
- **FR-009**: External OpenAB Compose/config/Skill changes MUST occur only after targeted tests and preflight pass; any failure stops and rolls back the same integration bundle.
- **FR-010**: Direct live validation MUST prove HTTP readiness, exact registry, one read-only call, one `confirm=false` preview, and protected-surface metadata/content endpoint equality. This is a before/after claim and does not assert that no transient mutation occurred between snapshots.
- **FR-011**: One bounded Hermes inference MUST prove one podcast MCP call, non-confirmed invocation, no second action, and no shell/terminal fallback using safe structured/filtered evidence; if unavailable, the feature remains blocked rather than inspecting session dumps.
- **FR-012**: The runbook MUST cover build/pin, restore, startup, readiness, safe smoke, backup, upgrade, rollback, and the explicit absence of an artifact schema migration.
- **FR-013**: No file or output may expose `.env` content, credentials, tokens, headers, provider values, private endpoints, raw Hermes session data, or raw natural-language smoke responses.

## Success Criteria

- Direct Streamable HTTP reports the exact frozen 21-tool registry and safely handles one read-only plus one preview call.
- Existing stdio and registry tests remain green without registry-test edits.
- Config/Skill helpers pass failure/rollback/redaction tests and apply idempotently to the approved local Hermes target.
- C6 endpoint equality is PASS-current from the single reviewer-approved v2 live run. The earlier bounded Hermes inference still lacks safe structured C7 proof, and v0.20.0 hooks remain an unvalidated candidate path; C7 and the feature remain blocked.
- The sidecar restarts persistently and the migration runbook can restore by image/config/Skill/data digests.

## Out of Scope

- Tool 22 or any existing tool/Skill workflow redesign.
- Spec 017 preview unification.
- Confirmed download/transcription/summary/report actions.
- Provider credential provisioning, market data, investment recommendations, Discord/OpenClaw, multi-user authorization, YouTube/X ingestion, and artifact schema migration.
