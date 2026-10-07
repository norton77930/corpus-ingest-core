# Feature Specification: Learning MCP acceptance and Hermes handoff

**Feature directory**: `specs/058-learning-mcp-acceptance`
**Created**: 2026-10-08
**Status**: Developer implementation and local verification complete; live operational gates pending
**Input**: The user approved local operating acceptance, source preparation verification, source-grounded note checks, and a later Hermes migration on the Grok bot VM.

## User Scenarios & Testing

### User Story 1 — Verify the selected source connection (P1)

An operator checks that the selected server exposes the learning tools and can deliver a specified prepared source/time range, without changing server settings or moving data.

**Independent test**: A readable source returns a bounded, metadata-only acceptance receipt; the wrong data root returns a fixed missing-source diagnosis.

**Acceptance scenarios**:
1. Given a prepared source and complete learning tool surface, verification reports its identity, version, recorded transcription settings and accumulated range coverage.
2. Given missing tools/source, contradictory identity/version, broken pagination or exhausted budget, verification stops and cannot claim complete coverage.
3. Given text containing instructions or secrets, verification treats it only as evidence and emits no transcript, title, cursor, remote error text or settings file contents.

### User Story 2 — Repeat content-quality acceptance (P2)

An operator uses the existing video questions to distinguish evidence retrieval, AI answer quality and human replay checking.

**Independent test**: The acceptance guide defines TDD, intent clarification and Michelin-kitchen questions, their replay windows, required source/AI labels, and explicit unchecked human outcomes.

**Acceptance scenarios**:
1. Given local source retrieval, a receipt proves delivery only, without claiming ASR accuracy, model reasoning quality or Hermes behavior.
2. Given an answer, the reviewer can check explanation, speaker reasoning, original examples, AI additions and time references; project application is omitted unless requested.

### User Story 3 — Prepare a complete Hermes handoff (P2)

An operator checks and copies the three complete existing Skill folders and follows a staged same-server operating guide on an already configured host.

**Independent test**: Missing referenced Skill resources are reported; an intact inventory is ready for operator copying. No installation occurs automatically.

**Acceptance scenarios**:
1. Given the repository Skill set, inventory covers entry, preparation, QA and all their references, including the single editable notes template.
2. Given no live host/new-source consent, the guide and task records keep those operational outcomes pending.
3. Given an available compatible host and freshly approved preparation preview, an operator records submission, one status observation and explicit learning continuation with matched identity/job; no automatic polling or follow-on action is introduced.

### Edge cases

Empty time selection; split segment text; repeated/noncontiguous ordinals; repeated cursor; source drift; transport timeout/failure; missing companion resources; filtered registry; unavailable CUDA; Windows stdio preparation incompatibility; endpoint redirects or credentials; another source's active job.

### Safety and Data Boundaries

Verification reads already prepared evidence through the existing tool only. It never prepares/repairs a source, reads `.env`, calls a repository LLM, downloads media/models, rebuilds cache or changes host configuration. Receipts are stdout metadata; saving them is an explicit operator redirection to a new owned path. Owned local stdio verification and connection to an existing loopback server are distinct from actual Hermes inference. Preparation remains preview/fresh approval/one confirmation/stop. No investment advice or live market API. Existing 35 tools and Skill behavior remain unchanged.

## Requirements

- **FR-001**: Require one explicit source identity and finite ordered time range before contacting a server.
- **FR-002**: Support an explicitly selected owned local data root or an existing credential-free loopback connection; never silently select/copy another corpus or launch an HTTP service.
- **FR-003**: Check availability of the three existing learning tools and report missing capabilities without calling side-effect tools.
- **FR-004**: Freshly inspect the exact source and pin every read to one valid source version.
- **FR-005**: Verify ordered segment/chunk continuity and stable selection coverage across pages; reject contradictory/repeated paging.
- **FR-006**: Bound tool calls, delivered characters and elapsed verification; insufficient budgets yield incomplete status, not success.
- **FR-007**: Emit only finite safe metadata and fixed diagnoses, including truthful recorded transcription settings; do not expose source text, titles, cursors, credentials or arbitrary exceptions.
- **FR-008**: Inventory all three Skill folders and their referenced resources without reading host settings or installing anything.
- **FR-009**: Document three source-grounded content checks with independent human replay/quality outcomes.
- **FR-010**: Provide repeatable local and VM handoff instructions covering data-root choice, transport, model/device disclosure, complete resources and one-action preparation/continuation.
- **FR-011**: Separate repository tests, local SDK delivery, existing-server checks, live preparation and actual Hermes acceptance. Preserve pending SPEC057 T017/T018 until real host evidence exists.
- **FR-012**: Preserve corpus files/history and existing tool order/contracts; introduce no new tool, automatic retry, repair, polling, model downgrade or deployment.

### Key Entities

- Verification request: selected connection, source identity, time window and budgets.
- Delivery receipt: safe identity/version/settings, call trace and accumulated coverage; never a quality certificate.
- Skill inventory: required installed-name folders and repository-relative resource availability.
- Operational acceptance record: independent evidence level, outcome and missing operator prerequisites.

## Success Criteria

- **SC-001**: A prepared selected range produces a complete delivery receipt; wrong-source and paging/budget failures never produce a success receipt.
- **SC-002**: All required resources of the three Skills appear in a reusable inventory; a missing reference prevents resource readiness.
- **SC-003**: Three film questions each have a replay range and explicit criteria separating speaker content from AI additions.
- **SC-004**: A second operator can follow the handoff without guessing a source, copying hidden settings, silently selecting a model or mistaking local checks for remote acceptance.

## Assumptions and scope clarification

2026-10-08: Existing source x-natewiki/2106893534980685927 is the local read-only pilot, not a shipped corpus. No remote host access has been provided. A live new-source download/transcription requires its own fresh disclosed-plan approval; this approval authorizes building the verification and handoff, not confirming an undisclosed job. No high-impact scope question remains. Actual host/preparation evidence stays an operational gate; developer tooling can be implemented now.
