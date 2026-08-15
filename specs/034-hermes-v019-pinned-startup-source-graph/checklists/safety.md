# Spec034 H1 Safety Checklist

- [x] Official repository, commit, and tree are exact literals.
- [x] Discovery ceilings are fixed and cannot expand automatically; claim closure does not authorize whole-program expansion.
- [x] Fixed bundled plugin is `plugins/security-guidance`.
- [x] No upstream source is imported or executed; Spec033 is read only for its manifest and frozen source identity.
- [x] No `.env`, local config values, credential/provider values, session, log, prompt, or raw response is read.
- [x] Receipt excludes source bytes, absolute paths, URLs, exception dumps, and credential/provider values.
- [x] No Docker, Hermes, WSL, MCP, provider, inference, C6, or predecessor verifier is run.
- [x] H1 cannot authorize H2 implementation or any live action; H2 remains pending and unapproved.
- [x] H3 is offline static-only: no Hermes import/exec, `.env`, local config/credential/provider values, session/log/prompt/raw response, Docker/Compose/WSL/MCP transport/provider/inference/C6, clone/archive/floating ref, or predecessor verifier.
- [x] H3 final verifier was created but not run; sentinel blocks socket/subprocess/upstream imports for final-test startup.
- [x] Task #75 did not execute the final verifier, Spec033 verifier, upstream source, provider, Docker, WSL, MCP, or live action.
- [x] Sentinel claims only upstream import/socket/subprocess blocking, not universal filesystem/environment blocking.
- [x] Manifest/root and H4 review authority have no self-approval cycle.
- [x] Task #80 current terminal is **startup/plugin closed; credential_provider BLOCKED; overall BLOCKED**; isolated launcher/bootstrap/final remain unrun pending fresh re-reviews. The `-I -S` pytest child receives verified runner/sentinel bytes and the exact typed reviewed/detached/H2/predecessor execution snapshot, imports only protocol-owned execution/capability snapshot bytes, and never adds original purelib or ambient site-packages to `sys.path`.
- [x] Task #80 final child runs only the dedicated C0–C7 acceptance suite that has no subprocess/socket/network import or call; sentinel guards remain installed and unsuppressed. Runner/journal/trust meta-tests are non-final only.
- [x] Task #80 capability-manifest generation read only installed package metadata/file bytes, used no network or credentials, includes only the finite reviewer-approved purelib distribution files, and makes no portable-runtime claim.
- [x] Task #81 retains all final launcher/bootstrap/verifier entrypoints unrun. C6 is sentinel-safe and has no subprocess/socket/network import/call; its provider/external/market fail-if-called guards install before fixture construction.
- [x] Task #81 child setup retains only required system environment variables, clears all ambient `PYTEST_*` and startup/test-affecting `PYTHON*` controls, and accepts success only after exact final C0–C7 passed-call reports.
- [x] Task #82 keeps parent final cwd at repository root while requiring child payload cwd to be an exact regular/no-link/reparse-free project snapshot root and changing there before sentinel/import/test startup; original workspace config replacement cannot affect C6 snapshot reads. Final launcher/bootstrap/verifier remain unrun.
- [x] Task #82 retains H2's exact 20-file authority and the blocked terminal; journal rename durability has an explicit Windows best-effort fsync fallback without relaxing manifest/unknown recovery failure closure.

