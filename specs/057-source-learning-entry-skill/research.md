# Research decisions

## Independent entry rather than overriding existing Skills

Decision: add source-learning-entry; do not modify standalone stopping rules. Reason: source-preparation intentionally reports/stops even when ready, while source-content-qa requires known prepared IDs and cannot prepare a bare URL. The baseline synthetic probe follows those rules and cannot fulfill the new combined entry request. Alternative: change both Skills globally; rejected because preparation-only/QA-only requests must remain independent.

## Reuse actual public contracts

Decision: URL requests get one Tool33 preview, then ready explicit QA intent can enter Tool35. Confirm-once uses canonical_url/plan_id and fresh approval. Job status is offline and returns IDs, not URL/source_type; compare retained job_id and source IDs. Busy may expose another source's active job_id and must not bind it to this request. Non-executable previews can retain context_digest; only plan_id is absent and no confirmation is allowed. Evidence: source_preparation.py _preview, source_preparation_jobs.py inspect, MCP wrappers and existing contract tests. Alternative: parse URLs/paths or implement a new runtime router; rejected as unnecessary.

## Fresh query inspection and truthful coverage

Decision: readiness only permits attempting content inspect; it is not readability/accuracy/coverage evidence. Existing ready validation can accept empty segments that Tool35 rejects as source_empty. Continue via source-content-qa with pinned version, chunk continuity and cumulative budget, using its single editable note template. Alternative: trust job readiness as complete notes; rejected by actual Core behavior.

## Same-conversation handoff

Decision: visibly retain original question, source reference, job_id and approved settings; no durable memory/queue. Status-only stops; explicit continuation checks once then reads only matching ready source. Lost context asks for the missing reference/request. Alternative: persistent job-associated questions/autonomous notification; outside approved scope.

## Host acceptance

Decision: separate developer checks from live Hermes execution. Read-only discovery: Get-Command hermes/hermes-agent had no result; no callable Hermes capability exists in current tool surface. This does not prove installation absence elsewhere. Existing prepared X JSON exists with SHA256 ddfc97d0ada4c1b90bd3f327f98293eac9a75961b96d7921700af40e266026af. Windows stdio new submissions remain blocked; an existing independently managed compatible HTTP host is needed for live preparation. Deliver operator procedure and retain actual acceptance as pending until its real trace is available. Alternative: silently install/configure/launch or count SDK evidence as Hermes acceptance; outside scope or untruthful.

Research agents were read-only. No settings/.env, providers, network or service startup were used. No unresolved planning decision remains.
