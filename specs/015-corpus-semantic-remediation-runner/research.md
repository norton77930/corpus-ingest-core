# Research: Corpus Semantic Remediation Runner

## Decision: Keep 015 standalone from deterministic remediation and fresh-episode orchestration

**Rationale**: Feature 010 owns deterministic corpus remediation and feature 014 deliberately stops before semantic or LLM work. Semantic summary generation introduces transcript transfer, cost acknowledgement, credential, and provider boundaries that do not belong in either existing workflow. A standalone Core+CLI runner keeps those boundaries explicit and lets an operator preview and confirm one semantic action independently.

**Alternatives considered**:
- Extend 010 with semantic work: rejected because it would mix deterministic remediation with an opt-in, cost-bearing LLM action and weaken 010's established contract.
- Add a semantic stage to 014: rejected because 014 is a no-LLM one-stage fresh-episode workflow and its exact behavior is already guarded.
- Expose 015 through MCP: rejected because v1 is a local operator workflow and changing the exact 12-tool registry would broaden the reviewed remote execution surface.

## Decision: Derive every decision from one in-memory 008/009 snapshot pair

**Rationale**: The private 008 index builder and 009 remediation-plan builder already centralize corpus artifact discovery and planning without requiring persistence. Each 015 invocation builds one index snapshot, passes that exact result and payload into one plan build, and never calls either public generator or persister. This makes preview fresh while preserving strict zero-file behavior and a single internally consistent view of the corpus.

**Implementation boundary**: Snapshot building may read bounded local artifact metadata and the content needed to establish artifact validity, but it must not create directories, allocate report paths, write reports, replace `.part` files, or refresh persisted index/plan artifacts. Existing public 008/009 write order, schemas, result types, and standalone behavior remain unchanged.

**Alternatives considered**:
- Read persisted 008/009 JSON: rejected because it can be stale and would make old sentinels stage truth.
- Call the public 008/009 generators: rejected because they intentionally persist artifacts and therefore violate strict zero-file preview.
- Rescan after execution: rejected because one confirmation must dispatch once and stop; a post-write rebuild would add work and blur the audit boundary.

## Decision: Isolate the canonical episode before semantic classification

**Rationale**: Index and plan snapshots can contain many episodes. The runner must first match the single validated canonical `episode_ref`, then pass only that row's state into semantic classification. Missing, failed, or blocked state from another episode must never influence the requested episode's outcome.

**Alternatives considered**:
- Reduce the complete plan and then filter the selected action: rejected because another episode could contaminate selection or counts.
- Accept a best-effort or title-based selector: rejected because it is ambiguous and can target the wrong transcript.

## Decision: Use a dedicated fail-closed semantic state reducer

**Rationale**: The generic 009 plan correctly treats several missing or unreadable deterministic artifacts as actionable remediation, but 015 has a narrower safety rule. It may select only `semantic_summary` for a valid transcript with no summary, or `semantic_review` for a readable summary with no review. A passed review is complete. An unusable transcript, unreadable summary, or failed, blocked, or unreadable review is terminal `blocked/manual-only`; v1 must not infer that regeneration, overwrite, retry, or fallback is safe.

**State precedence**:
1. Invalid or unusable transcript → `blocked/manual-only`.
2. Missing summary → `semantic_summary`.
3. Unreadable summary → `blocked/manual-only`.
4. Readable summary with no review → `semantic_review`.
5. Latest readable review passed → `completed`.
6. Any latest review state other than exact `passed`, including default `available`, blank, arbitrary, failed, blocked, or unreadable → `blocked/manual-only`.

**Alternatives considered**:
- Reuse 009's action label directly: rejected because its broader remediation semantics can turn unreadable artifacts into automatic work.
- Automatically regenerate a summary after failed review: rejected because v1 has no force contract and one confirmation may not chain actions.
- Automatically rerun review: rejected because the existing terminal review is authoritative until an operator intervenes.

## Decision: Add backward-compatible semantic-summary UTF-8 readability metadata to 008

**Rationale**: Existing summary discovery can mark a semantic Markdown artifact available from its path alone. The 015 reducer must distinguish a readable summary from an unreadable one without calling the semantic executor or exposing semantic content. The 008 build therefore gains additive per-episode `readable` and `readability_status` metadata based on a full UTF-8 decode only when the file is at most 2 MiB. The legacy `status` remains `available` for every discovered summary so existing 008/009 behavior is unchanged; 015 alone fails closed on unreadable or oversized readability metadata. No semantic body is retained or copied into the snapshot, result, report, stdout, or stderr.

**Alternatives considered**:
- Open the summary directly in 015 after planning: rejected because it creates a second source of artifact truth outside the shared snapshot.
- Treat any existing path as readable: rejected because confirmed review could then consume corrupt or undecodable input.
- Treat unreadable as missing and regenerate: rejected because overwrite is not supported and would destroy the fail-closed boundary.

## Decision: Require an exact episode selector and explicit confirmed action

**Rationale**: Every run requires one non-blank canonical episode reference. `latest`, path-like values, URL-like values, traversal, and unsafe components are rejected before corpus evaluation. Dry-run may use `action=next` to discover the safe next state, while confirmed execution accepts only `semantic_summary` or `semantic_review`. Confirmed state is recomputed; if the explicit action no longer matches, the outcome is `rejected` and no alternate action executes.

**Alternatives considered**:
- Support `latest`: rejected because feed ordering and local artifact state can drift between preview and confirmation.
- Allow confirmed `next`: rejected because it would let state drift choose a different side effect than the operator approved.
- Fall back to the newly selected action after drift: rejected because one explicit confirmation authorizes only the named action.

## Decision: Validate acknowledgement before summary configuration or provider resolution

**Rationale**: Confirmed semantic summary is the only cost-bearing action and the only action allowed to transfer transcript content. Both CLI and Core enforce the repository's exact acknowledgement. The CLI performs this check before LLM profile loading, `.env` loading, credential lookup, endpoint resolution, or provider construction; Core repeats the guard for direct callers. Dry-run constructs no provider and reads no local environment values. Confirmed semantic review bypasses all LLM configuration and requires no acknowledgement.

**Alternatives considered**:
- Validate after profile or environment loading: rejected because invalid consent must result in zero secret/configuration access.
- Rely only on CLI validation: rejected because the public Core API can be called directly.
- Require acknowledgement for deterministic review: rejected because review is local, deterministic, and makes no provider call.

## Decision: Dispatch exactly one existing semantic executor and stop

**Rationale**: Confirmed `semantic_summary` calls `semantic_summarize_episode` once; confirmed `semantic_review` calls `review_semantic_summary_smoke` once. These capabilities remain owners of semantic artifact schemas and execution details. The runner maps their bounded result into one outcome, writes its latest report, emits manual stale-metadata warnings, and stops without a second executor, fallback action, post-write snapshot, index/plan refresh, or cache rebuild. If a summary appears after selection, the summary executor's existing reuse outcome is recorded without proceeding to review.

**Alternatives considered**:
- Implement summary or review logic inside 015: rejected because it would duplicate established, tested artifact contracts.
- Chain summary into review: rejected because it would turn one confirmation into multiple writes.
- Retry on provider or review failure: rejected because v1 has no retry policy and must preserve one-attempt auditability.

## Decision: Preserve the existing timestamped semantic-review artifact contract

**Rationale**: The deterministic review capability owns timestamped JSON/Markdown naming, latest-review discovery, path collision handling, and its current pair-write behavior. Feature 015 must not migrate, rename, make atomic, clean up, or otherwise redefine those artifacts. If review writing only partly succeeds or raises, 015 records a bounded category-only failure in its own confirmed-run report and performs no compensating cleanup.

**Alternatives considered**:
- Replace timestamped reports with a latest-only review artifact: rejected because it breaks existing discovery and history.
- Add transactional cleanup in 015: rejected because it would cross executor ownership and could delete valid user artifacts.
- Change review pair atomicity as part of 015: rejected as unrelated behavior outside this feature's contract.

## Decision: Make runner reports confirmed-only, latest, and metadata-only

**Rationale**: A validated confirmed attempt writes `corpus-semantic-remediation-run.json` and `.md` under the podcast root. The report records the requested and selected action, safe local paths, counts, warnings, risk/acknowledgement flags, provider/model identifiers when applicable, and executed/reused/completed/blocked/rejected/failed status. It has no `generated_at` field. Dry-run, invalid input, and invalid acknowledgement write no report. Runner-owned failures expose a safe exception category only and omit traceback text.

**Excluded content**: Raw transcript, evidence snippets, semantic summary body, prompts, raw provider responses, base URL, URL query or fragment, secret values, and investment-action language are never included in the report, stdout, stderr, warnings, or runner-owned exception messages.

**Alternatives considered**:
- Persist dry-run reports: rejected because strict zero-file applies to the complete tree.
- Include diagnostic bodies for troubleshooting: rejected because they can disclose private transcript content, provider output, endpoints, or secrets.
- Add a report generation timestamp: rejected because the agreed latest-report schema is deterministic and the existing timestamped review remains the historical audit artifact.

## Decision: Preserve integration, cache, and public-contract boundaries

**Rationale**: Feature 015 adds only an additive public Core API, additive result/storage/error models, and one thin local CLI. It does not call or modify the behavior of 010 or 014; does not refresh persisted 008/009 artifacts; does not rebuild SQLite cache; and does not add, remove, or change MCP tools or response envelopes. Confirmed reports warn that derived corpus metadata and cache state may be stale and require separate manual refresh commands.

**Alternatives considered**:
- Automatically rebuild index, plan, or SQLite cache after a semantic write: rejected because repository policy keeps cache refresh manual and an automatic refresh would add unconfirmed writes.
- Add batch, scheduling, full-chain, retry, automatic review, stock-lens continuation, or live market data: rejected because each materially expands side effects or safety scope beyond the single-episode, single-action v1 contract.