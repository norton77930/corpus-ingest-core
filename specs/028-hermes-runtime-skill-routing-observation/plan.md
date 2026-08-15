# Implementation Plan: Spec 028 Offline Capability Gate

## Scope

Add an offline enum/frozen-dataclass core, a fixed-mode thin CLI, one pinned local manifest, safe evidence, focused tests, and governed-document status pointers. The core is outside the MCP, workflow, router, and integration graphs.

## Delivery slices

1. RED: source identity, total fail-closed evaluator, fixed evidence, offline boundary, and CLI tests.
2. GREEN: minimal pinned-manifest loader, bounded evaluator, and `capability|synthetic` CLI.
3. RED: Spec package and governed-document guard.
4. GREEN: contracts, checklists, successor pointers, and status synchronization.

## Evidence and constraints

Only targeted tests are run. The final verification, full suite, C6 validator, Docker, Hermes, hooks, collector, inference, network, and live configuration are excluded. `ok=true` means the offline gate completed, never that live actions are authorized. Every successful gate output fixes `live_actions_authorized=false`, `hermes_runtime_observation=not_run`, and `c6_status=pass_current_not_rerun`.

Any future work involving Hermes upgrade, Skill sync, hooks/plugin/collector, Docker/MCP/network, live config/session access, inference, or runtime observation must establish and receive separate approval for a new R2 successor spec; Spec 028 does not automatically authorize it.
