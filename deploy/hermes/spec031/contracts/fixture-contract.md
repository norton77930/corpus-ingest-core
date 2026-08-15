# Spec031 fixture contract

This directory is a blocked static fixture definition only, not an activation-ready fixture. `Dockerfile` uses `FROM scratch`; `fixture_build_authorized=false`, `official_loader_verified=false`, and `provider_materialization_status=blocked_unknown`. No build, image, container, network, runtime, or inspection action is authorized. `probe_contract.py` returns `BLOCKED_CREDENTIAL_SEAM` until a separately approved source proof can establish the official loader without provider construction. No raw output is retained.
