# Research: Hermes MCP and Portable Skills Integration

## Evidence Base (2026-08-09)

- Hermes Agent v0.19.0 runs inside the OpenAB Docker container `openab-demo-hermes` under WSL UbuntuProd.
- Official Hermes Agent v0.20.0 release tag `v2026.8.3` and its version-pinned hooks documentation describe per-call `pre_tool_call`/`post_tool_call` events with tool names and arguments/results. They do not document a canonical fallback indicator, and raw hook payloads may contain sensitive values; this is candidate capability only and was not installed or runtime-tested.
- The Hermes container uses `network_mode=host`; its persistent home is mounted at `/home/agent/.hermes`.
- Hermes supports URL-based MCP configuration plus `hermes mcp list/test/add`; its Skills live under the persistent Hermes home and support external directories.
- The current MCP server is stdio-only at `scripts/run_mcp_server.py`, but the installed MCP Python SDK supports `mcp.run(transport="streamable-http")`.
- In the installed SDK, HTTP host/port/path/security are server settings rather than arguments accepted directly by `FastMCP.run()`.
- Spec 025 guarantees one `FastMCP` object, 21 frozen tools, facade import-order registration, and public monkeypatch aliases.
- Existing OpenAB `_patch_hermes_mcp.py` reconstructs a whole trailing `mcp_servers` block and is unsuitable for incremental preservation.
- Existing portable Skills: corpus episode completion, latest deterministic processing, latest verified report, explicit-episode verified report.

## Decisions

1. Reuse the existing `mcp_runtime.mcp`; add a validated settings seam before Streamable HTTP startup.
2. Retain stdio unchanged and add a separate thin HTTP script.
3. Match current OpenAB topology: both containers use host networking; bind MCP to loopback only.
4. Fix the service port at 8767 and stop on collision.
5. Use structured YAML merge and manifest-bound backups; never use textual tail replacement.
6. Synchronize exactly four complete Skill directories with SHA-256 manifests and fail on local shadowing.
7. Use Specs 016/018/019 for preview-safe smoke; preserve Spec 017's existing one-confirm contract without invoking it live.
8. Never reuse the Hermes `.env` for the sidecar. LLM-dependent confirmed paths remain unconfigured until a later secret-provisioning decision.
9. Gather bounded live-safety evidence through direct protocol/application results and boolean-only protected-surface equality; never inspect session dumps. The v2 validator may hash protected bytes only as opaque in-memory input and must not emit protected digests, paths, or values. Both reviewers and the one authorized live v2 run passed; C6 is PASS-current and is not rerun.
10. Treat Hermes v0.20.0 `v2026.8.3` hooks as a C7 research candidate only. Any upgrade, hook enablement, or safe projection collector requires a separate R2 plan; current runtime validation remains not evaluated.

## Rejected

- stdio subprocess launched from the Hermes container: requires mounting source and installing project dependencies into the Hermes image, couples upgrades, and is poor for migration.
- New SSE server: legacy transport superseded by Streamable HTTP.
- Binding `0.0.0.0` or publishing a host port: unnecessary under the approved host-network topology.
- Second `FastMCP` instance: risks duplicate/ordered registration drift and violates Spec 025.
- Rebuilding the entire `mcp_servers` block: can erase unrelated servers.
- Copying all Skills or the whole Hermes `.env`: violates least privilege and the approved scope.
- Reading Hermes request dumps to prove behavior: prohibited sensitive surface.

## Preflight Results

- Port 8767 was unoccupied during preflight; it is now held by the healthy `podcast-ingest-core-mcp` sidecar.
- Installed `mcp` is 1.28.1. `FastMCP.run()` accepts `transport`/`mount_path`; public settings expose `host`, `port`, `streamable_http_path`, and enabled `TransportSecuritySettings` with loopback allowlists.
- Hermes v0.19.0 reads external Skills from `skills.external_dirs`; relative paths resolve under `HERMES_HOME`, nonexistent paths are skipped, and the local `~/.hermes/skills` root is excluded.
- Hermes URL entries default to Streamable HTTP; `transport: sse` is only for legacy SSE and must be omitted for this server.
- `hermes mcp add` is interactive for existing entries/auth and is unsuitable for deterministic unattended merge. The tested helper is the portable plan/apply/rollback route; on this machine the live credential-bearing config was not parsed by the session, so official `hermes config set` applied only the approved leaves after an exact byte backup.
- `hermes mcp test NAME` is non-interactive.
- `hermes chat` supports one-shot `-q`, explicit `-t/--toolsets`, explicit `-s/--skills`, `--max-turns`, and verbose/quiet output. The smoke will restrict toolsets to `podcast-ingest-core`, which removes terminal/shell tools from the available set; final filtered metadata capability remains a C7 runtime gate.
- `openab/demo-local/run.sh` regenerates `hermes-data/config.yaml` from `hermes/config.yaml.template` on every start. The user explicitly approved adding that template to the R2 scope so the managed MCP/Skills entries persist.
- The repository `.agents/skills` root also contains Spec Kit and other Skills. The sync contract therefore selects exactly the four managed names and ignores all other source directories; requiring the whole source root to equal the allowlist was rejected by live preflight.
- The live config may contain credential-shaped values and is not parsed by this session. Runtime leaf updates use official `hermes config set`; the exact live file is copied byte-for-byte to the authorized rollback bundle without displaying content.
