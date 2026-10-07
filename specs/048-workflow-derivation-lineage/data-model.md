# Data model

## Stored receipt

UTF-8 JSON, deterministic sorted keys and compact separators, optional final LF, maximum65536 bytes. Reject duplicate keys, extra/missing keys, booleans in integer fields and malformed values.

| Field | Contract |
| --- | --- |
| schema_version | Integer1; other versions unsupported |
| recipe_version | Positive integer; current recipe1, a different positive version compares stale |
| family | Literal workflow_derivation |
| podcast_id, episode_ref | Exact validated canonical identity |
| identity_stem_sha256 | SHA-256 of canonical artifact stem UTF-8; no absolute path |
| context_origin | default or custom |
| input_sha256 | Exact lecture_03, lecture_04, lecture_07, effective_context keys |
| request_sha256 | Digest of canonical JSON ordered role/content message list actually submitted |
| output_sha256 | Exact output_05, output_06 keys |

Every digest is exactly64 lowercase hexadecimal characters. Lecture digests hash consumed strings encoded UTF-8; effective_context hashes canonical JSON of the stripped allowed_tools list, preserving order and duplicates. Canonical JSON uses ensure_ascii=False, sort_keys=True, separators=(',', ':'). Output digests hash actual staged file bytes. Recipe version captures intentionally versioned generation behavior; request digest also captures rendered profile/message changes. No timestamps, provider information, raw content, tool names or custom paths.

## Public values

WorkflowDerivationResult appends defaulted metadata_writes:list[str]; generation includes one canonical sibling receipt path, reuse includes none. Existing constructors remain compatible.

Inspection result is a closed object: podcast_id, episode_ref, status, reason, changed_roles, scope, read_only, network_access, warnings. Status/reason and changed_roles follow contracts/lineage.md; scope is workflow_derivation_inputs_outputs, read_only=true, network_access=false. warnings is exactly ["derivation_scope_only", "non_atomic_observation"]. No digest/path/body is returned.

Receipt lifecycle: absent -> confirmed generation -> valid record; explicit confirmed force generation may replace a recognized record. Preview/reuse/query never transition stored state. A report failure after commit retains the committed record.
