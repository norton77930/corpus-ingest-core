# Spec 031 — Hermes G2 credentialless activation gate

## Purpose

Define an offline-only, fail-closed activation boundary for a future one-shot Hermes G2 attempt. G2 has no API key, credential channel, provider configuration, or runtime payload. This specification does not authorize or perform a live activation.

## Approved scope

- Factory-sealed observation facts, evaluations, rollback ownership, and safe receipts.
- A closed, zero-side-effect runtime boundary that evaluates current gates before the fixed marker helper or any caller-supplied driver can be reached.
- Static deployment fixtures and a probe contract which never impersonates the official plugin loader by calling `plugin.register()`.
- An offline feasibility CLI, static offline verifier, future static-only live runner, and focused tests.

## Explicit non-goals

- No Docker, Compose, container, image, network, Hermes runtime, listener, MCP transport, Core dispatch, inference, tools, query, chat, or prompt execution.
- No environment, credential, session, log, endpoint, or live configuration access.
- No change to Spec029 immutable plugin/adapter/snapshot artifacts, Spec030 artifacts, C6 artifacts, or their narratives.
- No assertion that G2 is live-ready or that an activation succeeded.

## Claims and evidence

| Claim | Offline evidence |
| --- | --- |
| Credentialless G2 facts are exact-class, factory-issued, and mutation/forgery/copy/subclass fail closed. | `tests/test_hermes_g2_activation_observation.py` |
| The pinned source contract can only report credential feasibility when it can prove official loader behavior without provider construction; otherwise it reports `BLOCKED_CREDENTIAL_SEAM`. | Source-manifest fixture, observation receipt, focused test |
| The current plan admits only fixed operation vocabulary; arbitrary command/env/map/path/prompt/credential input is absent. | `tests/test_hermes_g2_activation_runtime.py` and AST guard |
| Current calls to `run_g2_activation_once` stop before marker or driver access with zero attempts and retries. | Focused runtime test and static verifier |
| Fixture probe does not call `plugin.register()` and terminal feasibility remains blocked when the official loader cannot be established offline. | Fixture contract and docs test |

## State model

`UNKNOWN` observations fail closed. Before any live-start observation they produce a blocked receipt; after live-start they produce `QUARANTINED`. `BLOCKED_CREDENTIAL_SEAM` is the required terminal result when repository-pinned source cannot prove that the official loader avoids provider construction. Offline leases are not live tokens. A live lease and exact approval acknowledgement are necessary but never sufficient evidence for activation success.

Future live lease, driver, metadata inspection, and rollback execution are not implemented by this offline closure.

## Verification boundary

Focused public-seam tests and required Spec029/030 predecessor tests may run. H3 may run `scripts/verify_spec_031_offline.py` exactly once as the planned final verification; that verifier must remain static/offline and must not import or call the live executor. `run_spec_031_g2_once.py` is not run by this closure.
