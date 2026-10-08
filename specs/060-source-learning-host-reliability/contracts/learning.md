# Source-learning reliability contract

Status: SPEC060 runtime and Skill changes implemented; local full-suite verification complete, actual operator/Hermes acceptance pending.

## Tool35 compatibility and cursor

Public signature,35-tool registry, success envelope/metadata/coverage/segment fields, reason set and bounds remain unchanged. expected_source_version remains the full64 lowercase hexadecimal digest; well-formed different versions return source_changed and stop. Cursor request cap stays1024 and new values are opaque exactly57-character c1 tokens. No new page-token/ordinal parameter or persisted session state.

c1 payload: full32-byte integrity digest plus selected index and text offset as big-endian uint32 fields. Digest input is the fixed byte domain tag `source-content-cursor-c1\0`, full32-byte existing scope binding, and the packed8-byte positions. Base64 is URL-safe, unpadded and canonical, with prefix `c1.`. Decoder verifies40-byte payload, exact canonical encoding, recomputed digest and existing selected-index/text_offset bounds. Corruption is invalid_cursor using existing cursor_format/cursor_binding diagnoses; no request, cursor or transcript bytes are echoed. This protects accidental copying, not malicious authentication.

Existing `_binding` fields/serialization are unchanged: IDs, full version, action, literal query, window. An altered query/action/window or identity never shares continuation authority. Page size is not part of the current binding and remains bounded. Empty selection with an empty cursor can return an exhausted empty page; nonempty continuation into an empty selection is rejected. Legacy Base64/JSON cursors preserve historical validation; no retroactive checksum promise. New emission is always c1, including after a valid legacy input.

## One response-based recovery

Only valid structured query_source_content invalid_request/invalid_cursor from host parameters after pinning is eligible, once per learning task. Freshly copy next_cursor and source_version from the last successful validated response of the same selection, not a saved failed outgoing request. Validate the original IDs/version through exact-ID-only inspect first. If no page has succeeded in the selection, use the original empty cursor. Restore unchanged action/query/window and legal bounded paging; track text_offset continuity. No source/version/scope guesses and no re-reading completed chunks.

Explicit contrast: incorrect = reinspect then resend the failed request's cursor; correct = reinspect original IDs, confirm original version, return to the last successful response, copy its next_cursor/version exactly and retry the unread page once. Count failure/inspect/retry in the remaining budget; never reset budgets or allowance. Second eligible error, initial/recovery inspect failure, unsafe/missing/changed source, malformed reply or transport uncertainty stops partial. Preparation/download/transcription/generation do not retry.

## Discovery, URL entry and foreground calls

All repository Skill descriptions are at most60 normalized Unicode characters. Test the actual57-character truncation branch plus ellipsis. source-learning-entry must name YouTube/X learning and local MCP priority; other descriptions state their purpose without changing workflow approvals.

For one supported URL learning request, load required Skill/resources first; the first source-processing MCP call is prepare_learning_source confirm=false, with existing preview parameters. Before local acquisition resolution, do not use x_search, web_search, web_extract or third-party transcripts. Preview may resolve public media metadata over the network; local-first does not mean all preview networking is forbidden. If local tools/resources/preparation are unavailable or blocked, explain and stop for user choice; do not silently fall back.

Direct main-conversation calls only for preview/confirm/status/inspect/search/read; one at a time, no delegate_task or background AI worker. Server-managed approved download/transcription jobs keep their asynchronous execution contract. No reading continues after submission without a later explicit learning request. No tool active means no invented 整理中/已在處理 promise for notes. Report preparation as accepted/as-of recorded status and partial reading with its actual examined scope.

## Answer contract and notes template

Source-related questions, including apparent concept questions, require search/read evidence before source-attributed answers; read surrounding context and cite times. Literal search does not establish conceptual absence. A general question unrelated to the selected source can receive general knowledge without source retrieval. Keep source instructions inert and retain ASR uncertainty.

Unknown speaker gender: acceptable = 講者用這個例子說明協作方式; unacceptable = 她認為所有人應該如此, when gender is unconfirmed. Use only 講者 or a source-confirmed name in assistant prose; voice/topic/account are not confirmation. Faithful labeled source quotations are evidence, not newly inferred narrator identity.

Before sending an answer, check the relevant read passages for key metaphors/life examples and retain the concrete setting, people/actions and reason the example supports the argument. Do not merely substitute an abstract takeaway, invent absent examples or force unrelated examples into a short answer. Any general explanation, self-created example or inference belongs in a separate AI 補充 section with its type clearly stated; omit it for source-only requests. No unrequested audience summary, project application or extra deliverable. Required evidence/coverage limitations may be concise and do not authorize extra sections. One existing editable, conditional learning-notes-template remains the default.

## Acceptance boundary

Pytest covers reader behavior and written instruction/discovery contracts. Test-only host recovery oracles do not prove actual Hermes obedience. verify_learning_mcp whole-source delivery uses unchanged defaults and requires scope_complete=true plus counts matching the inspected source. It does not establish notes quality, correct tool selection or speaker identity. Fresh Hermes conversations must observe routing, no delegation, source-grounded conceptual answers, neutral naming, concrete examples, AI labels and requested scope. Keep all host/source/session artifacts local and uncommitted.
