# Acceptance utility contract

Output is metadata-only JSON stdout. Delivery receipts do not certify source accuracy or live host behavior.

inventory checks repository resources. verify requires --podcast, --episode, --start, --end and exactly one --data-dir/--mcp-url. Options --max-calls20, --max-total-chars60000, --timeout60. No confirm/model/repair/cache/arbitrary-command/credential/install parameter.

Exit0: resource readiness or complete selected delivery. Exit1: blocked/partial. Invalid argparse syntax exits2. Transport exceptions become transport_error, never raw strings.

Required native tools: prepare_learning_source, inspect_source_preparation_job, query_source_content. Only query_source_content called. Filtered registry3 accepted but not described as35.

Replies must match explicit IDs, read_only=true, network_access=false and pinned64-hex version. Metadata/times/counts/settings valid and finite. Split offsets exact; ordinal strictly increases after completion, never duplicates/decreases. Original ordinals may legitimately skip because overlap selection can exclude a short intervening segment; use stable selection and accumulated completed count, not adjacency, to verify selected delivery. Repeated cursor/bad coverage fails. Reserve final inspect; budget exhaustion partial. Final inspect must match or source_changed. No retry/fallback.

Known Tool35 reasons are finite; malformed values become protocol_error. No title/transcript/cursor/error/settings/URL contents in stdout. Supported recorded model/device/compute/VAD or null only.

Owned stdio: existing runner/safe explicit directory/child-only override. Both adapters suppress raw SDK diagnostics using temporary owned filters restored afterward. Existing HTTP: numeric loopback only, no credentials/query/fragment/redirect/proxy. Request hooks block SDK reconnection GET and RPC replay before repeat network dispatch; bounded teardown may terminate the test MCP session. No service/mount changes.

Inventory accepts bounded inline and reference-definition Markdown links to .md files within each Skill. Non-Markdown/hidden/unsafe resources fail before reading, including .env. Resource readiness also checks installed-name frontmatter; host loading remains not evaluated.
