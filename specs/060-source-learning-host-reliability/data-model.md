# Data model and transient state

## Existing source identity and selection

podcast_id, episode_ref, source_version, action, literal query, start_seconds and end_seconds retain their existing validation and binding serialization. expected_source_version stays64 lowercase hex and is compared before paging. Selection order uses normalized source ordinal; search selection index is not a source ordinal.

## Compact continuation c1

Opaque string: c1. prefix plus canonical unpadded URL-safe Base64 of40 bytes. Payload is a32-byte full SHA256 integrity digest followed by unsigned big-endian uint32 selected_index and uint32 text_offset. The digest covers a fixed domain tag, the full existing scope binding and both positions. Current segment/text bounds fit these fields. String length is57; no prefix ambiguity with existing Base64/JSON cursors. Format, integrity/scope and numeric bounds are validated before returning any text. This is not authentication or user approval.

Legacy inputs remain accepted under their historical rules; every subsequent non-final next_cursor is emitted in c1 form. Empty cursor starts a selection and null next_cursor indicates exhaustion. Neither representation is stored server-side.

## Reading checkpoint

Original inspected identity/version, action/query/window, last successful validated tool response including next_cursor and chunk offsets, cumulative budget and recovery-used boolean live in the current conversation only. A failed outgoing request is not a checkpoint. Beginning a different search/read selection initializes that selection's empty cursor but does not replenish the task-wide recovery allowance. Errors while the initial inspect itself runs stop.

State transitions: inspect/pin -> successful page/checkpoint -> next page; eligible parameter error -> consume allowance -> exact-ID inspect -> compare original version -> copy last successful response -> retry unread page. A second error, failed inspect, source change or protocol ambiguity -> partial stop. Successful recovery -> normal reading without resetting allowance. Completion requires consecutive chunks and exhausted requested scope, never a final page alone.

## Host discovery and evidence checks

Description is normalized frontmatter text with at most60 Unicode characters; the host's short index retains the whole description at or below60 and only57 plus an ellipsis above60. Entry keywords/priority must survive the rendered view.

Before answering source questions, retain the relevant read passages, confirmed speaker names, key example details, timestamps and AI additions in conversation. These are response inputs, not persisted records or a new publication format. Unrequested headings stay omitted.

## Acceptance metadata

Verifier returns only existing safe metadata, call/page/character counts, inspected version and selection-delivery status. Whole-source verification requires selected_segments == delivered_segments == inspected segment_count and an end bound beyond the final instant. Model routing, pronouns, source examples and supplementary labels require a separate host output review. No host setting, source text or session trace is committed.
