# Data model

SourceSnapshot: podcast_id, episode_ref, title, language (bounded text or null), source_version SHA256, actual_transcription (recorded safe fields or null), immutable strict segments and warnings. No persisted state is created.

Segment: ordinal (0-based position), segment_id (bounded str/int or null), start/end finite seconds, text string. Pagination does not use arbitrary original IDs as positions.

Selection: read or literal search, optional start_seconds/end_seconds; ordered selected segment ordinals. Search casefold matches complete original text before chunking.

Continuation: bounded base64url canonical JSON containing binding digest, index into derived selection and text_offset. Binding covers identity/version/action/query/window. Invalid position or offset fails.

Result: identity and version; metadata for inspect; segments, next_cursor, coverage and search scope for read/search. Chunk text is an exact source substring; text_offset and text_complete describe reconstruction.

Errors: invalid_request, source_missing, source_ambiguous, unsafe_source, source_invalid, source_incomplete, source_empty, source_changed, invalid_cursor, internal_error. Fixed MCP messages contain no raw paths or exceptions.
