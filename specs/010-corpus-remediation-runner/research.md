# Research: Corpus Remediation Runner

## Decision: Dry-run output is stdout-only

**Rationale**: The project constitution requires dry-run behavior to list planned reads/writes and risks without writing artifacts. A dry-run `corpus-remediation-run.json/.md` would be a write side effect, so v1 returns the planned run report through the command result only.

**Alternatives considered**:

- Dry-run writes report artifacts: rejected because it violates the dry-run no-write gate.
- Optional `--write-report` for dry-run: deferred because it adds a new side-effect mode before the basic runner is proven.

## Decision: v1 executes deterministic actions only

**Rationale**: The safest next step after 009 is to execute local deterministic backlog actions that already have transcript prerequisites. This delivers value without network, transcription, LLM, `.env`, or MCP expansion.

**Alternatives considered**:

- Full ladder including download/transcribe: rejected for v1 because it adds network, long-running IO, and local model execution risks.
- Include gated semantic actions: rejected for v1 because it adds LLM acknowledgement, provider construction, transcript transfer, and secret-boundary risks.

## Decision: Confirmed execution must be filter-bounded

**Rationale**: A corpus-wide confirmed run could unexpectedly write many artifacts. Requiring an episode reference or action family keeps the blast radius explicit while still allowing useful batch work.

**Alternatives considered**:

- Confirm all ready actions by default: rejected because accidental broad execution is too easy.
- Require one exact action only: rejected because it removes useful batch remediation by family.

## Decision: Execute core functions directly

**Rationale**: The repository constitution keeps runtime behavior in core and CLI scripts as thin wrappers. The runner should call existing core functions directly rather than shelling out to scripts, which keeps errors typed and avoids command parsing drift.

**Alternatives considered**:

- Shell out to suggested commands from 009: rejected because suggested commands are advisory text and not a stable execution API.
- Duplicate generator logic in the runner: rejected because it would violate thick-core boundaries and increase drift.

## Decision: Failure containment is per action

**Rationale**: Corpus state can be incomplete. One failed action should be visible but should not hide unrelated ready work. Same-run downstream selected actions that depend on a failed family should be skipped because their prerequisite did not materialize.

**Alternatives considered**:

- Stop on first failure: rejected because it reduces corpus-level usefulness.
- Continue all actions regardless of failed dependency: rejected because it can produce misleading downstream errors.

## Decision: No MCP surface in v1

**Rationale**: 008 and 009 deliberately stayed core + CLI. The runner is a side-effect surface and should first prove its dry-run/confirm contract locally before any MCP exposure is considered.

**Alternatives considered**:

- Add MCP dry-run tool: deferred to a future feature because it changes reviewed tool count and docs/eval surface.
- Add MCP execution tool: rejected for v1 due larger safety blast radius.
