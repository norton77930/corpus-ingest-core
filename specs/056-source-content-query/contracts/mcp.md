# Tool 35 — query_source_content

Arguments: podcast_id:str, episode_ref:str, action:str="inspect", expected_source_version:str="", query:str="", start_seconds:float|None=None, end_seconds:float|None=None, cursor:str="", limit:int=40, max_chars:int=8000.

Actions: inspect returns safe metadata only; read returns ordered timed text; search returns case-insensitive literal keyword/phrase matches. Only read/search accept expected_source_version and filters/cursor; query is required only for search. Strict bounds/types reject booleans used as numbers. inspect refuses irrelevant query/version/window/cursor and nondefault paging fields.

Read/search require the inspected source_version. No automatic resolver from URL. Explicit podcast_id/episode_ref can come from known completed preparation references or known episode identity. Missing identity is clarified in host conversation.

Every segment carries ordinal, segment_id, start, end, text, text_offset and text_complete. Returned text is capped by max_chars with continuation even within a long segment. coverage states scope, selected_segments, returned_ordinals, scope_exhausted, complete, truncated. next_cursor=null means this selection is exhausted; continuation responses still have complete=false. Search scope additionally states scanned_segments, total_matches and literal_keyword; no matches are not proof a topic is absent.

On changed bytes, cursor scope mismatch, unsafe links, ambiguity, malformed/empty/partial source, return fixed reason/error envelope without body. Legacy completed omission produces a warning; completed false/null/nontrue is incomplete. No arbitrary paths, no network, no provider, no SQLite, no automatic rebuild or artifact writes. Tool registration preserves original slots 1–34 and appends this tool at index 34.

Constitution IV applies to repository provider construction and its acknowledgement; none occurs here. Host model use of MCP responses can expose evidence and incur billing under host configuration; do not imply zero host cost or private-only model processing.
