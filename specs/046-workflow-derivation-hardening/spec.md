# Feature Specification: Workflow Derivation Publication Hardening

**Feature Directory**: `specs/046-workflow-derivation-hardening`
**Created**: 2026-10-03
**Status**: Implemented and offline-verified on 2026-10-03
**Branch**: none created
**Input**: User requested planning after045, then explicitly authorized implementation of this written scope.

## Scope and Clarifications

Make the existing derivation operation safe to retry only after operator review, preserve all unrelated lecture-directory bytes, and distinguish refusal from failures after publication. This closes the backend limitations documented by 045. Keep the two operations independent.

Included: explicit identity and local-path checks, refusal of pre-existing recovery entries, byte-preserving pair publication, finite failure outcomes, safe MCP errors, focused regressions and current operator guidance. Excluded: new tools or signatures, one-click pipelines, source-version/digest tracking, automatic repair, stronger report transactions, scheduling, new providers, installation and live evaluation. Runtime implementation was explicitly authorized after planning; live provider/host evaluation remains unperformed.

Clarification assumptions: complete pairs still reuse without cost acknowledgement; a partial pair remains replaceable only with explicit force, preserving existing behavior. Force never overrides unsafe paths or recovery refusal. Successful-operation schemas remain unchanged. CLI/Core context overrides remain supported; MCP cannot choose a context path. Writers remain externally serialized. These compatibility decisions were documented in the plan subsequently approved for implementation.

## User Scenarios & Testing

### User Story 1 - Refuse unsafe or unresolved local state (Priority: P1)

An operator previews one named episode and learns that manual review is required before any generation or mutation when its local paths or recovery state are unsafe.

**Why this priority**: The current publisher can silently remove or restore old staging/backup entries.
**Independent Test**: Call preview and confirm with synthetic recovery/path cases; snapshot all files and forbid provider/report/publisher calls.

**Acceptance Scenarios**:
1. **Given** a staging or backup remnant for either lecture or derivation, **When** preview or confirm is called with either force value, **Then** refuse without changing any entry or constructing a provider.
2. **Given** an invalid target or linked, reparse, special, nested or unreadable protected path, **When** either mode runs, **Then** fail closed without following that path or treating unreadable state as absence.
3. **Given** a valid complete lecture and ordinary extra files, **When** preview runs, **Then** return the compatible zero-write, zero-network plan.

### User Story 2 - Preserve lecture bytes while publishing a complete pair (Priority: P1)

An operator generates or explicitly replaces 05/06 without losing lecture files or unrelated regular files, including binary files and mixed line endings.

**Why this priority**: Publishing a whole directory must not discard entries outside the pair's ownership.
**Independent Test**: Generate/force with fixtures and inject publication-stage failures; compare byte snapshots and both pair members.

**Acceptance Scenarios**:
1. **Given** a valid lecture, extra binary files and no pair, **When** confirmed generation succeeds, **Then** 05/06 appear together and every other file retains identical bytes.
2. **Given** a complete pair, **When** confirmed without force, **Then** reuse every artifact unchanged, skip the provider and write run reports; with explicit force and exact acknowledgement replace only 05/06.
3. **Given** a publish failure before the directory swap commits, **When** rollback succeeds, **Then** restore the previous public directory; if rollback fails preserve recovery evidence and report that different outcome.
4. **Given** publication committed but cleanup or reports fail, **When** the operation returns an error, **Then** retain the new pair and report published-but-incomplete, without regenerating or rolling it back.

### User Story 3 - Receive bounded, truthful operation errors (Priority: P1)

An operator or agent receives a fixed safe failure message without raw provider text, local file bodies, configuration fragments or exception-derived instructions.

**Why this priority**: Skill instructions cannot sanitize raw text before it reaches the agent.
**Independent Test**: Inject each known state, arbitrary exception types and synthetic sensitive markers through both MCP branches; assert exact bounded envelopes and no markers.

**Acceptance Scenarios**:
1. **Given** a known refusal or publication state, **When** either MCP branch reports it, **Then** use a fixed type/message pair; unknown states produce generic uncertainty.
2. **Given** provider, configuration or arbitrary errors with injected text, **When** returned over MCP, **Then** no raw text or dynamic exception class escapes.
3. **Given** the updated Skill and current docs, **When** interpreting errors, **Then** distinguish published/reused report failure from unknown state while retaining one preview, fresh consent, one confirm and stop.

### Edge Cases

Broken links count as present, not missing. Inspect four exact recovery siblings, including remnants shared with the lecture operation. Refuse subdirectories rather than recursively preserving them. Preserve all regular extras, not just four known lecture files. Missing destination does not authorize restoration of an old backup. Permission/stat/listing failures never imply empty directories. Reject stale title-neighbor fallback. Check state again at confirm and before publication; this is not a promise against hostile concurrent filesystem mutation or power loss. Successful rollback and deletion of only this attempt's temporary files are permitted transaction handling, not recovery of pre-existing state.

### Safety and Data Boundaries

Dry-run remains zero-write and zero-network. Generation requires the exact existing acknowledgement before provider construction; complete-pair reuse does not. Only existing lecture content and allowed-tool context are sent to the provider; no transcript text. No live market API, investment advice, automatic cache rebuild or source preparation. Fixtures only during development. No .env reads during planning/tests or values in errors. Report files remain the existing weaker staged pair, separately written after artifact publication; never describe the whole operation as one atomic report/artifact transaction.

## Requirements

### Functional Requirements

- **FR-001**: Preserve existing tools, order, public signatures, successful result/preview fields and independent operation boundaries; intentional error semantics are explicitly documented.
- **FR-002**: Validate explicit target identity before profile/source/context access; reject empty, padded, separator-bearing and reserved latest/next episode identifiers, preserving valid case and underscores. Bind the lecture location to validated canonical metadata with matching identity and a nonempty title.
- **FR-003**: Refuse linked/reparse/nonregular protected files, nondirectory ancestors, unreadable inspection and any nested/special entry in the lecture directory. Apply bounded reads to metadata, lecture text and context; enforce the context override policy in the contract.
- **FR-004**: Refuse any pre-existing .part, .old, .wfderive.part or .wfderive.old sibling in preview and confirm, including files and broken links; neither force nor reuse may clean or restore them.
- **FR-005**: Keep generation/reuse/partial-pair semantics: complete regular pair plus force=false reuses, partial plus force=false refuses, and generation/replacement requires exact acknowledgement. Force changes only owned pair files and never overrides FR-002/003/004.
- **FR-006**: Stage a complete destination retaining every non-pair regular file byte-for-byte; never silently skip an entry or decode/re-encode preserved data. Publish both pair members as one directory replacement commit.
- **FR-007**: Track this attempt's staging/backup ownership and committed state. Before commit restore the old destination when possible; preserve evidence on rollback failure. After commit do not revert a successfully published pair because cleanup fails.
- **FR-008**: Distinguish refusal, publication failure with unchanged/restored public state, rollback failure, committed cleanup failure, committed report failure and reused report failure; ambiguous failures remain explicitly uncertain.
- **FR-009**: Every successful confirmed operation writes the existing metadata-only reports, including reuse. Keep report paths/formats and manual cache warnings; do not strengthen report atomicity implicitly.
- **FR-010**: Map all MCP errors in both modes through a finite type/message allowlist, never exception text or dynamic class names. Keep the existing error envelope; do not add a reason_code response field.
- **FR-011**: Refresh current derivation Skill guidance, offline oracles and usage docs to the new backend guarantees and limitations while keeping fresh approval, exact generation acknowledgement, empty reuse acknowledgement and no retries/chaining.
- **FR-012**: Supply focused failing checks before changes, fault injection at every transaction phase, real-wrapper contract checks, byte snapshots and existing Tool 26/registry/safety regression coverage. Native symlink skips require non-skipped simulated reparse/special/stat cases.
- **FR-013**: Preserve existing 044/045 and unrelated behavior, runtime boundaries and historical records; document changed failure compatibility and all verification limits.

### Key Entities

Explicit request; canonical source identity; validated lecture/context; destination entry inventory; pre-existing recovery entry; attempt-owned staging/backup; publication state; safe public error.

## Success Criteria

- **SC-001**: Every defined unsafe/recovery fixture is refused in both modes and both force settings without a provider call or filesystem mutation.
- **SC-002**: Every successful generation/force fixture retains the exact bytes of all non-pair files; reuse retains all artifact bytes.
- **SC-003**: Every injected publication/report failure produces the documented outcome and retained/restored state, without automatic regeneration or unowned cleanup.
- **SC-004**: Every public failure fixture excludes injected raw text and uses only fixed documented types/messages; existing successful callers require no argument/schema changes.
- **SC-005**: Targeted and full offline regressions have recorded results/skips; current guidance matches implemented behavior and unperformed live verification is explicit.

## Assumptions

Local writers are serialized by the caller. The managed roots are trusted deployment anchors; path checks reject links from those roots downward, and context ancestors are checked separately. No claim of adversarial race immunity, crash durability, digest-pinned approval, source freshness or uniform hardening of other tools. User explicitly authorized this scoped implementation; no live provider execution was requested.
