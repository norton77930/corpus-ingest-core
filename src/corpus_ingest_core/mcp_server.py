"""Facade for the corpus-ingest-core MCP server.

specs/025-core-consolidation FR-005: the single ``FastMCP`` instance lives in
``mcp_runtime``; tool functions live in the ``mcp_tools_*`` group modules
that register on import, so the group import order below IS the registration
order (Tools 1-35). Tests and clients keep reaching every tool function,
envelope, and dependency-module alias through this module — the re-exports
below are contract surface. Next-tool playbook (as used for Tool 22, spec 035, Tool 23, spec 040, and
Tool 25, spec 043): add a group module imported LAST so existing slots keep
their order, extend the re-exports here, then deliberately update
``tests/test_mcp_tool_registry_contract.py``.
"""

from __future__ import annotations

from .mcp_runtime import (
    MAX_CONTEXT_SEGMENTS,
    MAX_LIMIT,
    SEMANTIC_API_COST_ACK,
    StreamableHttpConfig,
    mcp,
    run,
    run_streamable_http,
    tool_action_plan,
    tool_error,
    tool_success,
)

# Registration order: read (1-6) -> side-effect (7-12) -> corpus workflows
# (13-16) -> verified-report queries (17-21) -> stock lens (22) ->
# x-video ingest (23) -> youtube-video ingest (24) -> workflow derivation
# (25) -> study-guide bundle (26) -> learning next-step query (27) -> derivation lineage query (28) -> study-guide lineage query (29) -> recovery query (30) -> learning status overview (31) -> single learning action (32) -> source preparation (33/34) -> prepared source content (35).
# Do not reorder these imports; a new group is appended last to preserve all slots. Append here, not only to
# the re-export block below:
# a re-export happens to register too, but then this list stops being the
# order it claims to be, and the next group appended here would take the slot.
#
# The fence runs to the end of the alias block below, because the
# re-export block mirrors this order by hand and the alias block is
# grouped by purpose -- none of it is alphabetical, all of it is
# deliberate. The fence is load-bearing, not decoration. `ruff check --fix` sorted this
# block alphabetically the first time the lint gate ran: mcp_tools_corpus_
# workflows moved to the front, so Tool 1 became run_corpus_episode_completion_
# workflow instead of list_episodes, and mcp_tools_x_video landed after
# workflow_derivation. Three registry contract tests caught it. A comment
# saying "do not reorder" does not stop a formatter -- this does.
# isort: off
from . import mcp_tools_read
from . import mcp_tools_side_effect
from . import mcp_tools_corpus_workflows
from . import mcp_tools_verified_report_queries
from . import mcp_tools_stock_lens
from . import mcp_tools_x_video
from . import mcp_tools_youtube_video
from . import mcp_tools_workflow_derivation
from . import mcp_tools_study_guide
from . import mcp_tools_learning_workflow
from . import mcp_tools_workflow_lineage
from . import mcp_tools_study_guide_lineage
from . import mcp_tools_learning_recovery
from . import mcp_tools_learning_status
from . import mcp_tools_learning_advance
from . import mcp_tools_source_preparation
from . import mcp_tools_source_content

from .mcp_tools_read import (
    get_episode,
    list_episodes,
    rebuild_cache,
    search_mentions,
    search_transcripts,
    validate_transcript,
)
from .mcp_tools_side_effect import (
    ALLOWED_SEMANTIC_PROVIDERS,
    ALLOWED_TRANSCRIPTION_COMPUTE_TYPES,
    ALLOWED_TRANSCRIPTION_DEVICES,
    ALLOWED_TRANSCRIPTION_MODELS,
    CACHE_STALE_WARNING,
    MAX_EVIDENCE_PER_MENTION,
    MAX_QUOTES,
    MAX_SEMANTIC_CHUNK_SECONDS,
    MAX_SEMANTIC_SEGMENTS_PER_CHUNK,
    MAX_WINDOW_SECONDS,
    MIN_EVIDENCE_PER_MENTION,
    MIN_SEMANTIC_CHUNK_SECONDS,
    MIN_SEMANTIC_SEGMENTS_PER_CHUNK,
    MIN_WINDOW_SECONDS,
    SEMANTIC_CACHE_STALE_WARNING,
    WORKFLOW_CACHE_STALE_WARNING,
    download_audio,
    extract_mentions,
    run_research_workflow,
    semantic_summarize_episode,
    summarize_episode_extractive,
    transcribe_episode,
)
from .mcp_tools_corpus_workflows import (
    run_corpus_episode_completion_workflow,
    run_corpus_latest_episode_deterministic_workflow,
    run_episode_verified_research_report_workflow,
    run_latest_episode_verified_research_report_workflow,
)
from .mcp_tools_verified_report_queries import (
    list_verified_report_gap_backlog,
    query_verified_research_report_catalog,
    query_verified_research_report_coverage,
    revalidate_verified_research_report_sources,
    suggest_historical_verified_report_next_step,
)
from .mcp_tools_stock_lens import (
    MAX_EVIDENCE_ITEMS,
    MIN_EVIDENCE_ITEMS,
    NOT_INVESTMENT_ADVICE,
    STOCK_LENS_CACHE_STALE_WARNING,
    generate_stock_lens_report,
)
from .mcp_tools_x_video import ingest_x_video
from .mcp_tools_youtube_video import ingest_youtube_video
from .mcp_tools_workflow_derivation import derive_workflow_bundle
from .mcp_tools_study_guide import generate_study_guide_bundle
from .mcp_tools_learning_workflow import suggest_learning_workflow_next_step
from .mcp_tools_workflow_lineage import inspect_workflow_derivation_lineage
from .mcp_tools_study_guide_lineage import inspect_study_guide_lineage
from .mcp_tools_learning_recovery import inspect_learning_bundle_recovery
from .mcp_tools_learning_status import inspect_learning_workflow_status
from .mcp_tools_learning_advance import advance_learning_workflow
from .mcp_tools_source_preparation import prepare_learning_source, inspect_source_preparation_job
from . import source_preparation
from .mcp_tools_source_content import query_source_content
from . import source_content_query

# Dependency-module aliases: tests monkeypatch through these shared module
# objects (e.g. monkeypatch.setattr(mcp_server.feed_reader, ...)), and the
# group modules call them attribute-style, so patches land everywhere.
from . import cache as cache_module
from . import corpus_episode_completion_workflow_runner as completion_workflow_runner
from . import corpus_latest_episode_deterministic_workflow_runner as latest_deterministic_workflow_runner
from . import latest_episode_verified_research_report_workflow_runner as verified_research_report_workflow_runner
from . import mcp_episode_verified_research_report
from . import mcp_verified_research_report_catalog
from . import mcp_historical_verified_report_path
from . import mcp_verified_report_gap_backlog
from . import mcp_verified_research_report_coverage
from . import mcp_verified_research_report_source_revalidation
from . import downloader
from . import entity_extractor
from . import feed_reader
from . import research_workflow
from . import search as search_module
from . import semantic_summarizer
from . import summarizer
from . import transcriber
from . import validator
from . import stock_lens
from . import x_video_ingest
from . import youtube_video_ingest
from . import study_guide_bundle
# isort: on
