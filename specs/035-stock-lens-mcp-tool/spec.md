# Feature Specification: Stock Lens MCP Tool

**Feature Branch**: `035-stock-lens-mcp-tool`  
**Created**: 2026-08-15  
**Status**: Implemented

**Input**: Expose the existing deterministic stock lens report over MCP as append-only Tool 22, completing Spec 001 User Story 3 for agents. The Core capability and CLI already exist; no tool reached them, so an agent could not answer "analyse this stock through the podcast's lens" without a terminal.

## Clarifications

### Session 2026-08-15

- Q: Is this new capability or exposure only? → A: **Exposure only** — `stock_lens.generate_stock_lens_report` is unchanged; the tool is a thin wrapper.
- Q: Read-query or side-effect? → A: **Side-effect** — it writes a report, so it follows the dry-run-first `confirm` gate like Tools 7–12.
- Q: Does it need `api_cost_ack`? → A: **No** — no LLM, no network, no external market API. Only local mapping and boundary artifacts are read.
- Q: Which registration slot? → A: **Tool 22**, appended last via a new `mcp_tools_stock_lens.py` group imported after the existing four, so Tools 1–21 keep their order.
- Q: Does this conflict with "不做股票分析或投資建議"? → A: **No** — the red line forbids buy/sell/hold, target prices and guaranteed returns. This ships an evidence framework and refuses advice, which is exactly User Story 3.
- Q: Stock lens synthesis (`generate_stock_lens_synthesis_report`) too? → A: **No** — out of scope for v1; it has a different input contract.

## User Scenarios & Testing

### User Story 1 — Analyse a Stock Through the Podcast Lens (Priority: P1)

An operator names a stock and receives a deterministic report separating what the podcast explicitly said from what was inferred from industry-chain relations, plus the lens dimensions, the external checks still needed, and an explicit no-advice boundary.

**Why this priority**: Spec 001 marked User Story 3 as the capability closest to the user's long-term goal. Core and CLI shipped it; without a tool an agent cannot use it, so the user-facing goal stayed unmet.

**Independent Test**: For a stock the transcripts name explicitly, the report lists direct evidence with timestamps. For a stock reachable only through an industry-chain node, it appears under inferred leads with `needs_verification`. For a stock with neither, the report states the absence instead of inventing a link.

**Acceptance Scenarios**:

1. **Given** a stock named in transcripts, **When** the tool runs confirmed, **Then** the report lists `evidence_status=podcast_explicit` rows with timestamp evidence.
2. **Given** a stock reachable only by industry-chain inference, **When** the tool runs, **Then** it appears only as an inferred lead with `verification_status=needs_verification`.
3. **Given** a request for buy/sell guidance, **When** the report is produced, **Then** it carries the no-advice boundary and contains no recommendation, target price, or guaranteed return.

### User Story 2 — Dry-run First (Priority: P1)

The default call writes nothing and returns the plan: inputs, planned writes, and risks.

**Acceptance Scenarios**:

1. `confirm=false` returns an action plan, writes no file, and names `data/stock-lens/{podcast_id}/` as the planned write.
2. The plan states that the run reads only local artifacts and makes no live market API, network, or LLM call.
3. `confirm=true` executes exactly once and returns the report asset metadata.

### User Story 3 — Append-only Registry (Priority: P1)

Tool 22 appends after unchanged Tools 1–21.

**Acceptance Scenarios**:

1. The registry exposes exactly 22 tools; the first 21 keep their names, order, signatures, and defaults.
2. The AST-derived registry projection and the Spec 029 descriptor snapshot both resolve to 22.
3. Governed docs state 22, or mark an older count as historical.

## Safety and Data Boundaries

- Side-effect and dry-run-first: no write without `confirm=true`.
- No LLM, no `api_cost_ack`, no network, no live market API, no external data provider.
- Reads only local industry-mapping and external-data-boundary artifacts; accepts no arbitrary local path.
- A partial-draft external boundary is refused unless `allow_partial=true`.
- Does not rebuild the SQLite cache; the response carries the stale-cache warning.
- Direct podcast evidence and inferred industry leads stay separated; inferred rows keep `needs_verification`.
- No investment advice: no buy/sell/hold, target price, or guaranteed return.

## Requirements

- **FR-001**: MCP MUST expose `generate_stock_lens_report(podcast_id, stock_query, confirm, force, allow_partial, max_evidence_items)` as append-only Tool 22.
- **FR-002**: The tool MUST be a thin wrapper over the existing `stock_lens.generate_stock_lens_report`; Core behaviour is unchanged.
- **FR-003**: `confirm=false` MUST return an action plan and perform zero writes.
- **FR-004**: `max_evidence_items` MUST be clamped to `1..50`.
- **FR-005**: The confirmed response MUST carry the stale-cache warning and the no-advice statement.
- **FR-006**: Registration MUST occur in a dedicated `mcp_tools_stock_lens.py` group imported last, so Tools 1–21 keep their positions.
- **FR-007**: The facade MUST re-export the tool and its bounded constants.
- **FR-008**: The AST-derived registry projection MUST include the new group module and resolve to exactly 22 names.
- **FR-009**: The Spec 029 descriptor snapshot MUST be regenerated with the official export script, not hand-edited.
- **FR-010**: Governed docs MUST state the live count or mark an older count as historical, enforced by the registry-derived consistency check.
- **FR-011**: No new runtime dependency; no Skill is added in v1.

## Success Criteria

- An agent can produce a stock lens report through MCP without a terminal fallback.
- Registry is exactly 22 tools with Tools 1–21 unchanged in name, order, signature, and defaults.
- A stock with no podcast evidence yields an explicit absence rather than a fabricated link.
- Full repository regression shows no new failure outside the pre-existing Spec 026–034 blocked chain.

## Assumptions

1. Mapping and external-boundary artifacts already exist; the tool does not generate them.
2. Operators run `rebuild_cache` manually when they want the new artifact indexed.
3. The evidence/inference separation is produced by Core and is not re-derived here.

## Out of Scope (v1)

- `generate_stock_lens_synthesis_report` exposure
- A portable Skill for this tool
- External market data fetching or verification
- Batch or multi-stock requests, scheduler, auto-remediation
