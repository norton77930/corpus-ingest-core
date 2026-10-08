# Design decisions

## Recovery and source consistency

Decision: one recovery total per QA task after pinning, only structured invalid_request/invalid_cursor host-parameter failures. Reinspect exact IDs, compare original version, retry unread position. Initial inspect failure stops. Rationale: preserve prior evidence and budget without repeated side effects or version mixing. Rejected: per-page retries, restart all pages, accepting a new version.

## Diagnostics

Decision: optional finite Core diagnosis and fixed MCP text, same public reason/envelope/signature. Rationale: current generic message loses validation context; arbitrary exception strings risk leakage. Rejected: echo request/exception, add public reasons, infer typo from valid version mismatch.

## Host-owned process and discoverability

Decision: existing Skill/response-contract owns retry guidance and conversation checkpoint; verifier remains no-retry. Synthetic real-tool sequences and read-only pressure tests explicitly are not actual Hermes. Rationale: adding backend sessions/tool/retry executor expands scope. Entry descriptions cover learning intents, body says local-first; discovery still requires operator installation. No host settings shipped.

## Quality and portability

Decision: strengthen existing conditional template with neutral speaker reference, concrete example preservation and separate AI additions. Default120000 with other verifier bounds unchanged. Lecture fixture uses native tmp_path plus POSIX characterization. Rationale: default60000 misses a long source, and Linux native Path does not parse backslashes as Windows separators.