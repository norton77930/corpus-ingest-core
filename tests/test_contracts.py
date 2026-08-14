from pathlib import Path
import inspect

import pytest


def test_loads_gooaye_profile_from_yaml():
    from podcast_ingest_core.config import load_podcast_profiles

    profiles = load_podcast_profiles(Path("config/podcasts.yaml"))

    assert set(profiles) == {"gooaye"}
    profile = profiles["gooaye"]
    assert profile.podcast_id == "gooaye"
    assert profile.display_name == "Gooaye 股癌"
    assert profile.rss_url == (
        "https://feeds.soundon.fm/podcasts/"
        "954689a5-3096-43a4-a80b-7810b219cef3.xml"
    )
    assert profile.language == "zh"
    assert profile.default_episode_prefix == "EP"


def test_package_exports_required_core_functions():
    import podcast_ingest_core as core

    expected = {
        "list_episodes": ["podcast_id", "limit"],
        "get_episode": ["podcast_id", "episode_ref"],
        "download_audio": ["podcast_id", "episode_ref"],
        "transcribe_episode": [
            "podcast_id",
            "episode_ref",
            "model",
            "device",
            "compute_type",
            "vad_filter",
            "force",
            "audio_path",
            "progress_callback",
        ],
        "summarize_episode": [
            "podcast_id",
            "episode_ref",
            "force",
            "max_quotes",
            "window_seconds",
            "allow_partial",
        ],
        "semantic_summarize_episode": [
            "podcast_id",
            "episode_ref",
            "api_cost_ack",
            "provider",
            "model",
            "base_url",
            "api_key_env",
            "reasoning_effort",
            "read_timeout_seconds",
            "force",
            "chunk_seconds",
            "max_segments_per_chunk",
            "allow_partial",
            "progress_callback",
        ],
        "extract_mentions": [
            "podcast_id",
            "episode_ref",
            "force",
            "allow_partial",
            "max_evidence_per_mention",
        ],
        "generate_episode_intelligence_report": [
            "podcast_id",
            "episode_ref",
            "force",
            "allow_partial",
            "window_seconds",
            "max_evidence_per_section",
        ],
        "generate_industry_chain_mapping": [
            "podcast_id",
            "episode_ref",
            "force",
            "allow_partial",
            "max_candidates_per_node",
            "max_evidence_per_candidate",
        ],
        "generate_external_data_boundary": [
            "podcast_id",
            "episode_ref",
            "force",
            "allow_partial",
        ],
        "verify_external_data_boundary": [
            "podcast_id",
            "episode_ref",
            "confirm",
            "force",
            "allow_partial",
            "provider",
            "fixture_path",
        ],
        "load_gooaye_lens_model": ["path"],
        "load_llm_profile": ["profile_id", "path"],
        "review_research_llm_smoke": [
            "podcast_id",
            "episode_ref",
            "stock_query",
            "workflow_stdout_path",
            "raw_output_path",
        ],
        "review_semantic_summary_smoke": [
            "podcast_id",
            "episode_ref",
            "workflow_stdout_path",
        ],
        "generate_stock_lens_report": [
            "podcast_id",
            "stock_query",
            "force",
            "allow_partial",
            "max_evidence_items",
        ],
        "generate_stock_lens_synthesis_report": [
            "podcast_id",
            "stock_query",
            "confirm",
            "force",
            "allow_partial",
            "api_cost_ack",
            "provider",
            "model",
            "base_url",
            "api_key_env",
            "max_prompt_chars",
            "include_semantic_context",
            "semantic_context_max_chars",
            "require_semantic_review",
        ],
        "run_research_workflow": [
            "podcast_id",
            "episode_ref",
            "stock_query",
            "confirm",
            "force",
            "allow_partial",
            "include_semantic_summary",
            "include_stock_lens_synthesis",
            "include_semantic_context_in_synthesis",
            "include_external_data_verification",
            "api_cost_ack",
            "semantic_provider",
            "semantic_model",
            "semantic_base_url",
            "semantic_api_key_env",
            "semantic_chunk_seconds",
            "semantic_max_segments_per_chunk",
            "synthesis_provider",
            "synthesis_model",
            "synthesis_base_url",
            "synthesis_api_key_env",
            "synthesis_max_prompt_chars",
            "synthesis_semantic_context_max_chars",
            "external_data_provider",
            "external_fixture_path",
            "max_evidence_per_mention",
            "report_window_seconds",
            "max_evidence_per_section",
            "max_candidates_per_node",
            "max_evidence_per_candidate",
            "max_stock_evidence_items",
        ],
        "initialize_cache": ["db_path"],
        "index_episode": ["podcast_id", "episode_ref", "force", "db_path"],
        "rebuild_cache": ["podcast_id", "force", "db_path"],
        "validate_transcript": ["podcast_id", "episode_ref"],
        "search_transcripts": [
            "query",
            "podcast_id",
            "limit",
            "db_path",
            "search_mode",
            "context_segments",
            "case_sensitive",
        ],
        "search_mentions": [
            "query",
            "podcast_id",
            "mention_type",
            "limit",
            "db_path",
            "case_sensitive",
        ],
    }

    for name, parameters in expected.items():
        function = getattr(core, name)
        assert list(inspect.signature(function).parameters) == parameters


def test_storage_paths_are_deterministic_and_under_data():
    from podcast_ingest_core.storage import (
        audio_path,
        cache_path,
        cache_db_path,
        mention_asset_paths,
        episode_intelligence_report_asset_paths,
        external_data_boundary_asset_paths,
        industry_chain_mapping_asset_paths,
        stock_lens_report_asset_paths,
        stock_lens_synthesis_asset_paths,
        summary_path,
        transcript_path,
    )

    assert audio_path("gooaye", "ep-001") == Path("data/audio/gooaye/ep-001.mp3")
    assert transcript_path("gooaye", "ep-001") == Path(
        "data/transcripts/gooaye/ep-001.json"
    )
    assert summary_path("gooaye", "ep-001") == Path("data/summaries/gooaye/ep-001.md")
    mention_paths = mention_asset_paths("gooaye", "EP001", "Title")
    assert mention_paths.json_path == Path(
        "data/mentions/gooaye/EP001__Title.mentions.json"
    )
    assert mention_paths.markdown_path == Path(
        "data/mentions/gooaye/EP001__Title.mentions.md"
    )
    report_paths = episode_intelligence_report_asset_paths("gooaye", "EP001", "Title")
    assert report_paths.json_path == Path(
        "data/reports/gooaye/EP001__Title.intelligence.json"
    )
    assert report_paths.markdown_path == Path(
        "data/reports/gooaye/EP001__Title.intelligence.md"
    )
    mapping_paths = industry_chain_mapping_asset_paths("gooaye", "EP001", "Title")
    assert mapping_paths.json_path == Path(
        "data/mappings/gooaye/EP001__Title.industry-map.json"
    )
    assert mapping_paths.markdown_path == Path(
        "data/mappings/gooaye/EP001__Title.industry-map.md"
    )
    boundary_paths = external_data_boundary_asset_paths("gooaye", "EP001", "Title")
    assert boundary_paths.json_path == Path(
        "data/external/gooaye/EP001__Title.external-boundary.json"
    )
    assert boundary_paths.markdown_path == Path(
        "data/external/gooaye/EP001__Title.external-boundary.md"
    )
    stock_lens_paths = stock_lens_report_asset_paths("gooaye", "TSM")
    assert stock_lens_paths.json_path == Path(
        "data/stock-lens/gooaye/TSM.stock-lens.json"
    )
    assert stock_lens_paths.markdown_path == Path(
        "data/stock-lens/gooaye/TSM.stock-lens.md"
    )
    synthesis_paths = stock_lens_synthesis_asset_paths("gooaye", "TSM")
    assert synthesis_paths.json_path == Path(
        "data/stock-lens/gooaye/TSM.stock-lens-synthesis.json"
    )
    assert synthesis_paths.markdown_path == Path(
        "data/stock-lens/gooaye/TSM.stock-lens-synthesis.md"
    )
    assert cache_path("gooaye") == Path("data/cache/gooaye/episodes.json")
    assert cache_db_path() == Path("data/cache/podcast_ingest.sqlite3")


def test_storage_rejects_unsafe_slugs():
    from podcast_ingest_core.storage import audio_path

    with pytest.raises(ValueError, match="podcast_id"):
        audio_path("../gooaye", "ep-001")

    with pytest.raises(ValueError, match="episode_ref"):
        audio_path("gooaye", "../ep-001")


def test_search_requires_cache_db(tmp_path):
    from podcast_ingest_core import search_transcripts
    from podcast_ingest_core.errors import SearchError

    with pytest.raises(SearchError):
        search_transcripts("台積電", db_path=tmp_path / "missing.sqlite3")


def test_public_search_functions_resolve_to_search_module():
    from podcast_ingest_core import search_mentions, search_transcripts

    # F-14 (Batch 3B): a dead Phase 0 ``search_transcripts`` stub used to live
    # in storage.py. The public search API must resolve to the real search
    # module so callers (and future agents) never bind the wrong module.
    assert search_transcripts.__module__ == "podcast_ingest_core.search"
    assert search_mentions.__module__ == "podcast_ingest_core.search"


def test_search_result_models_include_phase_3b_fields():
    from dataclasses import fields
    from podcast_ingest_core.models import (
        MentionSearchResult,
        SemanticSummarySmokeReviewResult,
        TranscriptSearchResult,
    )

    transcript_fields = {field.name for field in fields(TranscriptSearchResult)}
    mention_fields = {field.name for field in fields(MentionSearchResult)}

    assert {
        "matched_text",
        "highlighted_text",
        "context_before",
        "context_after",
        "search_mode",
    } <= transcript_fields
    assert {"highlighted_text", "search_mode"} <= mention_fields

    semantic_review_fields = {field.name for field in fields(SemanticSummarySmokeReviewResult)}
    assert {
        "review_status",
        "review_json_path",
        "review_markdown_path",
        "semantic_summary_path",
        "workflow_stdout_path",
        "check_count",
        "failed_check_count",
        "warning_count",
        "blocked_check_count",
    } <= semantic_review_fields


def test_corpus_semantic_remediation_additive_public_contract():
    from podcast_ingest_core import (
        CorpusSemanticRemediationRunAssetPaths,
        CorpusSemanticRemediationRunResult,
        CorpusSemanticRemediationRunnerFailedError,
        PodcastIngestCoreError,
        corpus_semantic_remediation_run_asset_paths,
        run_corpus_semantic_remediation,
    )

    assert callable(run_corpus_semantic_remediation)
    assert callable(corpus_semantic_remediation_run_asset_paths)
    assert CorpusSemanticRemediationRunAssetPaths.__name__ == (
        "CorpusSemanticRemediationRunAssetPaths"
    )
    assert CorpusSemanticRemediationRunResult.__name__ == (
        "CorpusSemanticRemediationRunResult"
    )
    assert issubclass(
        CorpusSemanticRemediationRunnerFailedError, PodcastIngestCoreError
    )
