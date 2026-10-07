# Verification entities

Request: identity, start/end, max_calls3..100, max_total_chars1..1200000, timeout_seconds1..300, exactly one data_dir or mcp_url.

Receipt: ok, status passed/blocked/partial, fixed reason, evidence_kind owned_stdio/existing_loopback, identity, source_version/null, actual_transcription/null, registry_count, required tools presence, pages/segments/chars/selected count, range/scope_complete/whole_source_read=false, metadata action trace. host_acceptance/preparation_acceptance/content_quality remain not_evaluated. Success certifies selected-range delivery only.

Read state: pinned version, last ordinal/offset/completion/time bounds, counts, stable selection count, internal seen cursors. Budget includes initial/read/final inspect; setup/registry bounded by elapsed timeout.

Inventory: three fixed installed names, relative resources/availability, fixed diagnoses, no contents/settings. Operational record: case ID, evidence level, pending/pass/fail, exact IDs/version/job, coverage, replay/AI-label observations; independent from utility success.
