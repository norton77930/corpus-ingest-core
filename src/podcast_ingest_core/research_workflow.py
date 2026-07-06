from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .cache import rebuild_cache
from .entity_extractor import extract_mentions
from .episode_intelligence import generate_episode_intelligence_report
from .errors import PodcastIngestCoreError, ResearchWorkflowFailedError, ResearchWorkflowInputError
from .external_data_boundary import generate_external_data_boundary
from .external_data_verification import (
    DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
    SUPPORTED_PROVIDER as SUPPORTED_EXTERNAL_DATA_PROVIDER,
    verify_external_data_boundary,
)
from .industry_mapping import generate_industry_chain_mapping
from .models import ResearchWorkflowResult, ResearchWorkflowStep
from .semantic_summarizer import SEMANTIC_API_COST_ACK, semantic_summarize_episode
from .stock_lens import generate_stock_lens_report
from .stock_lens_synthesis import generate_stock_lens_synthesis_report
from . import storage
from .validator import validate_transcript


CACHE_STALE_WARNING = "Cache may be stale. Run rebuild_cache manually after workflow completion."
SEMANTIC_STEP_WARNING = (
    "semantic_summarize_episode is not executed unless include_semantic_summary=True "
    "with exact api_cost_ack"
)
DOWNSTREAM_REFRESH_WARNING = (
    "External boundary verification updated local external data, but an existing stock lens "
    "report was reused. Use force=True to refresh downstream stock lens artifacts."
)
EXTERNAL_API_STEPS = ["semantic_summarize_episode"]


def run_research_workflow(
    podcast_id: str,
    episode_ref: str,
    *,
    stock_query: str | None = None,
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    include_semantic_summary: bool = False,
    include_stock_lens_synthesis: bool = False,
    include_semantic_context_in_synthesis: bool = False,
    include_external_data_verification: bool = False,
    api_cost_ack: str = "",
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
    synthesis_provider: str = "openai-compatible",
    synthesis_model: str | None = None,
    synthesis_base_url: str | None = None,
    synthesis_api_key_env: str = "OPENAI_API_KEY",
    synthesis_max_prompt_chars: int = 24000,
    synthesis_semantic_context_max_chars: int = 12000,
    external_data_provider: str = SUPPORTED_EXTERNAL_DATA_PROVIDER,
    external_fixture_path: Path = DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
    max_evidence_per_mention: int = 5,
    report_window_seconds: int = 300,
    max_evidence_per_section: int = 5,
    max_candidates_per_node: int = 5,
    max_evidence_per_candidate: int = 5,
    max_stock_evidence_items: int = 10,
) -> ResearchWorkflowResult:
    """Dry-run or execute the local deterministic research workflow."""

    _validate_positive("max_evidence_per_mention", max_evidence_per_mention)
    _validate_positive("semantic_chunk_seconds", semantic_chunk_seconds)
    _validate_positive("semantic_max_segments_per_chunk", semantic_max_segments_per_chunk)
    _validate_positive("synthesis_max_prompt_chars", synthesis_max_prompt_chars)
    _validate_positive(
        "synthesis_semantic_context_max_chars",
        synthesis_semantic_context_max_chars,
    )
    _validate_positive("report_window_seconds", report_window_seconds)
    _validate_positive("max_evidence_per_section", max_evidence_per_section)
    _validate_positive("max_candidates_per_node", max_candidates_per_node)
    _validate_positive("max_evidence_per_candidate", max_evidence_per_candidate)
    _validate_positive("max_stock_evidence_items", max_stock_evidence_items)

    normalized_stock_query = _normalize_stock_query(stock_query)
    if include_stock_lens_synthesis and normalized_stock_query is None:
        raise ResearchWorkflowInputError(
            "include_stock_lens_synthesis requires stock_query."
        )
    if external_data_provider != SUPPORTED_EXTERNAL_DATA_PROVIDER:
        raise ResearchWorkflowInputError(
            f"unsupported external data provider: {external_data_provider}"
        )
    validation = validate_transcript(podcast_id, episode_ref)
    transcript_paths = storage.find_transcript_asset_paths(podcast_id, episode_ref)
    planned_reads = [str(transcript_paths.json_path)] if transcript_paths else []
    step_specs = _step_specs(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        stock_query=normalized_stock_query,
        force=force,
        allow_partial=allow_partial,
        include_semantic_summary=include_semantic_summary,
        include_stock_lens_synthesis=include_stock_lens_synthesis,
        include_semantic_context_in_synthesis=include_semantic_context_in_synthesis,
        include_external_data_verification=include_external_data_verification,
        semantic_provider=semantic_provider,
        semantic_model=semantic_model,
        semantic_base_url=semantic_base_url,
        semantic_api_key_env=semantic_api_key_env,
        semantic_chunk_seconds=semantic_chunk_seconds,
        semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
        synthesis_provider=synthesis_provider,
        synthesis_model=synthesis_model,
        synthesis_base_url=synthesis_base_url,
        synthesis_api_key_env=synthesis_api_key_env,
        synthesis_max_prompt_chars=synthesis_max_prompt_chars,
        synthesis_semantic_context_max_chars=synthesis_semantic_context_max_chars,
        external_data_provider=external_data_provider,
        external_fixture_path=Path(external_fixture_path),
        max_evidence_per_mention=max_evidence_per_mention,
        report_window_seconds=report_window_seconds,
        max_evidence_per_section=max_evidence_per_section,
        max_candidates_per_node=max_candidates_per_node,
        max_evidence_per_candidate=max_evidence_per_candidate,
        max_stock_evidence_items=max_stock_evidence_items,
    )
    blocked = _is_blocked(validation.status, allow_partial)
    semantic_warnings = [] if include_semantic_summary else [SEMANTIC_STEP_WARNING]
    warnings = [*semantic_warnings, CACHE_STALE_WARNING, *validation.warnings]
    external_api_steps = _external_api_steps(include_stock_lens_synthesis)

    if not confirm:
        return ResearchWorkflowResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            stock_query=normalized_stock_query,
            workflow_status="blocked" if blocked else "planned",
            dry_run=True,
            requires_confirmation=not blocked,
            requires_api_cost_ack=include_semantic_summary or include_stock_lens_synthesis,
            required_acknowledgement=SEMANTIC_API_COST_ACK
            if include_semantic_summary or include_stock_lens_synthesis
            else None,
            transcript_status=validation.status,
            steps=[
                _planned_step(spec, "blocked" if blocked else "planned")
                for spec in step_specs
            ],
            planned_reads=planned_reads,
            planned_writes=_unique(path for spec in step_specs for path in spec["planned_writes"]),
            written_artifacts=[],
            generated_artifacts=[],
            reused_artifacts=[],
            external_api_steps=external_api_steps,
            warnings=warnings + validation.problems,
            not_investment_advice=True,
        )

    _raise_for_blocking_transcript(validation.status, validation.problems, allow_partial)
    _raise_for_missing_api_cost_ack(
        include_semantic_summary or include_stock_lens_synthesis,
        api_cost_ack,
    )

    steps: list[ResearchWorkflowStep] = []
    generated_artifacts: list[str] = []
    reused_artifacts: list[str] = []
    try:
        for spec in step_specs:
            step = _execute_step(spec)
            steps.append(step)
            generated_artifacts.extend(step.generated_artifacts)
            reused_artifacts.extend(step.reused_artifacts)
    except PodcastIngestCoreError:
        raise
    except Exception as exc:
        raise ResearchWorkflowFailedError(f"research workflow execution failed: {exc}") from exc

    generated_artifacts = _unique(generated_artifacts)
    reused_artifacts = _unique(reused_artifacts)
    workflow_warnings = list(warnings)
    if _verification_updated_and_stock_reused(steps):
        workflow_warnings.append(DOWNSTREAM_REFRESH_WARNING)
    return ResearchWorkflowResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        stock_query=normalized_stock_query,
        workflow_status="partial-draft" if validation.status == "partial" else "completed",
        dry_run=False,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        required_acknowledgement=None,
        transcript_status=validation.status,
        steps=steps,
        planned_reads=planned_reads,
        planned_writes=_unique(path for spec in step_specs for path in spec["planned_writes"]),
        written_artifacts=generated_artifacts,
        generated_artifacts=generated_artifacts,
        reused_artifacts=reused_artifacts,
        external_api_steps=external_api_steps,
        warnings=workflow_warnings,
        not_investment_advice=True,
    )


def _validate_positive(name: str, value: int) -> None:
    if value < 1:
        raise ValueError(f"{name} 必須大於 0。")


def _normalize_stock_query(stock_query: str | None) -> str | None:
    if stock_query is None:
        return None
    normalized = stock_query.strip()
    return normalized or None


def _is_blocked(status: str, allow_partial: bool) -> bool:
    if status in {"missing", "corrupt", "incomplete_outputs"}:
        return True
    return status == "partial" and not allow_partial


def _raise_for_blocking_transcript(
    status: str, problems: list[str], allow_partial: bool
) -> None:
    if not _is_blocked(status, allow_partial):
        return
    details = "; ".join(problems)
    raise ResearchWorkflowInputError(f"transcript validation status is {status}: {details}")


def _raise_for_missing_api_cost_ack(
    requires_api_cost_ack: bool, api_cost_ack: str
) -> None:
    if requires_api_cost_ack and api_cost_ack != SEMANTIC_API_COST_ACK:
        raise ResearchWorkflowInputError(
            f"external LLM steps require exact api_cost_ack: {SEMANTIC_API_COST_ACK}"
        )


def _external_api_steps(include_stock_lens_synthesis: bool) -> list[str]:
    steps = EXTERNAL_API_STEPS.copy()
    if include_stock_lens_synthesis:
        steps.append("generate_stock_lens_synthesis_report")
    return steps


def _step_specs(
    *,
    podcast_id: str,
    episode_ref: str,
    stock_query: str | None,
    force: bool,
    allow_partial: bool,
    include_semantic_summary: bool,
    include_stock_lens_synthesis: bool,
    include_semantic_context_in_synthesis: bool,
    include_external_data_verification: bool,
    semantic_provider: str,
    semantic_model: str | None,
    semantic_base_url: str | None,
    semantic_api_key_env: str,
    semantic_chunk_seconds: int,
    semantic_max_segments_per_chunk: int,
    synthesis_provider: str,
    synthesis_model: str | None,
    synthesis_base_url: str | None,
    synthesis_api_key_env: str,
    synthesis_max_prompt_chars: int,
    synthesis_semantic_context_max_chars: int,
    external_data_provider: str,
    external_fixture_path: Path,
    max_evidence_per_mention: int,
    report_window_seconds: int,
    max_evidence_per_section: int,
    max_candidates_per_node: int,
    max_evidence_per_candidate: int,
    max_stock_evidence_items: int,
) -> list[dict[str, Any]]:
    specs = _base_step_specs(
        podcast_id,
        episode_ref,
        stock_query,
        include_semantic_summary=include_semantic_summary,
        include_stock_lens_synthesis=include_stock_lens_synthesis,
        include_semantic_context_in_synthesis=include_semantic_context_in_synthesis,
        include_external_data_verification=include_external_data_verification,
        external_fixture_path=external_fixture_path,
    )
    operation_index = 0
    if include_semantic_summary:
        specs[operation_index]["operation"] = lambda: semantic_summarize_episode(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            provider=semantic_provider,
            model=semantic_model,
            base_url=semantic_base_url,
            api_key_env=semantic_api_key_env,
            force=force,
            chunk_seconds=semantic_chunk_seconds,
            max_segments_per_chunk=semantic_max_segments_per_chunk,
            allow_partial=allow_partial,
        )
        operation_index += 1
    specs[operation_index]["operation"] = lambda: extract_mentions(
        podcast_id,
        episode_ref,
        force=force,
        allow_partial=allow_partial,
        max_evidence_per_mention=max_evidence_per_mention,
    )
    specs[operation_index + 1]["operation"] = lambda: generate_episode_intelligence_report(
        podcast_id,
        episode_ref,
        force=force,
        allow_partial=allow_partial,
        window_seconds=report_window_seconds,
        max_evidence_per_section=max_evidence_per_section,
    )
    specs[operation_index + 2]["operation"] = lambda: generate_industry_chain_mapping(
        podcast_id,
        episode_ref,
        force=force,
        allow_partial=allow_partial,
        max_candidates_per_node=max_candidates_per_node,
        max_evidence_per_candidate=max_evidence_per_candidate,
    )
    specs[operation_index + 3]["operation"] = lambda: generate_external_data_boundary(
        podcast_id,
        episode_ref,
        force=force,
        allow_partial=allow_partial,
    )
    stock_index = operation_index + 4
    if include_external_data_verification:
        specs[stock_index]["operation"] = lambda: verify_external_data_boundary(
            podcast_id,
            episode_ref,
            confirm=True,
            force=force,
            allow_partial=allow_partial,
            provider=external_data_provider,
            fixture_path=external_fixture_path,
        )
        stock_index += 1
    if stock_query is not None:
        specs[stock_index]["operation"] = lambda: generate_stock_lens_report(
            podcast_id,
            stock_query,
            force=force,
            allow_partial=allow_partial,
            max_evidence_items=max_stock_evidence_items,
        )
        if include_stock_lens_synthesis:
            specs[stock_index + 1]["operation"] = lambda: generate_stock_lens_synthesis_report(
                podcast_id,
                stock_query,
                confirm=True,
                force=force,
                allow_partial=allow_partial,
                api_cost_ack=SEMANTIC_API_COST_ACK,
                provider=synthesis_provider,
                model=synthesis_model,
                base_url=synthesis_base_url,
                api_key_env=synthesis_api_key_env,
                max_prompt_chars=synthesis_max_prompt_chars,
                include_semantic_context=include_semantic_context_in_synthesis,
                semantic_context_max_chars=synthesis_semantic_context_max_chars,
            )
    return specs


def _base_step_specs(
    podcast_id: str,
    episode_ref: str,
    stock_query: str | None,
    *,
    include_semantic_summary: bool,
    include_stock_lens_synthesis: bool,
    include_semantic_context_in_synthesis: bool,
    include_external_data_verification: bool,
    external_fixture_path: Path,
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = [
        {
            "name": "extract_mentions",
            "action": "Read existing transcript artifacts and write deterministic mention artifacts.",
            "planned_reads": [f"data/transcripts/{podcast_id}/{episode_ref}__*.json"],
            "planned_writes": [
                f"data/mentions/{podcast_id}/{episode_ref}__{{safe_title_slug}}.mentions.json",
                f"data/mentions/{podcast_id}/{episode_ref}__{{safe_title_slug}}.mentions.md",
            ],
            "risks": ["Writes local mention artifacts", "Does not call external APIs"],
        },
        {
            "name": "generate_episode_intelligence_report",
            "action": "Read transcript and mentions artifacts and write episode intelligence report.",
            "planned_reads": [
                f"data/transcripts/{podcast_id}/{episode_ref}__*.json",
                f"data/mentions/{podcast_id}/{episode_ref}__*.mentions.json",
            ],
            "planned_writes": [
                f"data/reports/{podcast_id}/{episode_ref}__{{safe_title_slug}}.intelligence.json",
                f"data/reports/{podcast_id}/{episode_ref}__{{safe_title_slug}}.intelligence.md",
            ],
            "risks": ["Writes local report artifacts", "Does not call external APIs"],
        },
        {
            "name": "generate_industry_chain_mapping",
            "action": "Read episode intelligence report and write industry chain mapping.",
            "planned_reads": [
                f"data/reports/{podcast_id}/{episode_ref}__*.intelligence.json",
                "config/industry_chain_mappings.yaml",
            ],
            "planned_writes": [
                f"data/mappings/{podcast_id}/{episode_ref}__{{safe_title_slug}}.industry-map.json",
                f"data/mappings/{podcast_id}/{episode_ref}__{{safe_title_slug}}.industry-map.md",
            ],
            "risks": ["Writes local mapping artifacts", "Inferred candidates remain needs_verification"],
        },
        {
            "name": "generate_external_data_boundary",
            "action": "Read industry mapping and write external data boundary scaffold.",
            "planned_reads": [
                f"data/mappings/{podcast_id}/{episode_ref}__*.industry-map.json",
                "config/external_data_boundary.yaml",
            ],
            "planned_writes": [
                f"data/external/{podcast_id}/{episode_ref}__{{safe_title_slug}}.external-boundary.json",
                f"data/external/{podcast_id}/{episode_ref}__{{safe_title_slug}}.external-boundary.md",
            ],
            "risks": ["Writes local external boundary artifacts", "Does not fetch market data"],
        },
    ]
    if include_external_data_verification:
        specs.append(
            {
                "name": "verify_external_data_boundary",
                "action": "Read external boundary and local fixture data, then update fixture verification status.",
                "planned_reads": [
                    f"data/external/{podcast_id}/{episode_ref}__*.external-boundary.json",
                    str(external_fixture_path),
                ],
                "planned_writes": [
                    f"data/external/{podcast_id}/{episode_ref}__{{safe_title_slug}}.external-boundary.json",
                    f"data/external/{podcast_id}/{episode_ref}__{{safe_title_slug}}.external-boundary.md",
                ],
                "risks": [
                    "Writes existing external boundary artifacts",
                    "Uses local fixture provider only",
                    "No live market API",
                    "Does not read API keys",
                    "Does not provide investment advice",
                ],
            }
        )
    if include_semantic_summary:
        specs.insert(
            0,
            {
                "name": "semantic_summarize_episode",
                "action": "Generate semantic LLM summary from an existing transcript.",
                "planned_reads": [
                    f"data/transcripts/{podcast_id}/{episode_ref}__*.json",
                    f"data/transcripts/{podcast_id}/{episode_ref}__*.txt",
                ],
                "planned_writes": [
                    f"data/summaries/{podcast_id}/{episode_ref}__{{safe_title_slug}}.semantic.md",
                ],
                "risks": [
                    "Calls an external LLM API",
                    "Sends transcript text outside this machine as transcript transfer",
                    "May incur API cost risk",
                    "Requires exact api_cost_ack before confirmed execution",
                ],
            },
        )
    if stock_query is not None:
        specs.append(
            {
                "name": "generate_stock_lens_report",
                "action": "Read podcast-wide mapping and boundary artifacts and write stock lens report.",
                "planned_reads": [
                    f"data/mappings/{podcast_id}/*.industry-map.json",
                    f"data/external/{podcast_id}/*.external-boundary.json",
                    "config/gooaye_lens.yaml",
                ],
                "planned_writes": [
                    f"data/stock-lens/{podcast_id}/{{safe_stock_query}}.stock-lens.json",
                    f"data/stock-lens/{podcast_id}/{{safe_stock_query}}.stock-lens.md",
                ],
                "risks": [
                    "Writes local stock lens report artifacts",
                    "No buy/sell/hold advice, target price, or guaranteed return",
                ],
            }
        )
        if include_stock_lens_synthesis:
            planned_reads = [
                f"data/stock-lens/{podcast_id}/{{safe_stock_query}}.stock-lens.json",
            ]
            if include_semantic_context_in_synthesis:
                planned_reads.extend(
                    [
                        f"data/summaries/{podcast_id}/{episode_ref}__*.semantic.md",
                        f"evals/research-llm-smoke/reports/*__{podcast_id}__{episode_ref}.semantic-review.json",
                    ]
                )
            risks = [
                "Calls an external LLM API",
                "Uses only Phase 6F stock lens JSON as LLM input"
                if not include_semantic_context_in_synthesis
                else "Uses Phase 6F stock lens JSON plus reviewed semantic summary context as LLM input",
                "Uses no raw transcript text",
                "May incur API cost risk",
                "Requires exact api_cost_ack before confirmed execution",
            ]
            if include_semantic_context_in_synthesis:
                risks.append("Reviewed semantic summary is an LLM intermediate artifact, not raw transcript or external market fact")
            specs.append(
                {
                    "name": "generate_stock_lens_synthesis_report",
                    "action": "Read stock lens report and write LLM stock lens synthesis.",
                    "planned_reads": planned_reads,
                    "planned_writes": [
                        f"data/stock-lens/{podcast_id}/{{safe_stock_query}}.stock-lens-synthesis.json",
                        f"data/stock-lens/{podcast_id}/{{safe_stock_query}}.stock-lens-synthesis.md",
                    ],
                    "risks": risks,
                }
            )
    return specs


def _planned_step(spec: dict[str, Any], status: str) -> ResearchWorkflowStep:
    return ResearchWorkflowStep(
        name=spec["name"],
        status=status,
        action=spec["action"],
        planned_reads=spec["planned_reads"],
        planned_writes=spec["planned_writes"],
        risks=spec["risks"],
        generated_artifacts=[],
        reused_artifacts=[],
    )


def _execute_step(spec: dict[str, Any]) -> ResearchWorkflowStep:
    operation: Callable[[], Any] = spec["operation"]
    asset = operation()
    artifact_paths = _asset_paths(asset)
    generated = artifact_paths if getattr(asset, "generated", False) else []
    reused = artifact_paths if getattr(asset, "already_exists", False) else []
    return ResearchWorkflowStep(
        name=spec["name"],
        status="completed" if generated else "reused",
        action=spec["action"],
        planned_reads=spec["planned_reads"],
        planned_writes=spec["planned_writes"],
        risks=spec["risks"],
        generated_artifacts=generated,
        reused_artifacts=reused,
    )


def _asset_paths(asset: Any) -> list[str]:
    output_fields = (
        "summary_path",
        "mentions_json_path",
        "mentions_markdown_path",
        "report_json_path",
        "report_markdown_path",
        "mapping_json_path",
        "mapping_markdown_path",
        "boundary_json_path",
        "boundary_markdown_path",
        "synthesis_json_path",
        "synthesis_markdown_path",
    )
    return [
        str(getattr(asset, field_name))
        for field_name in output_fields
        if hasattr(asset, field_name)
    ]


def _verification_updated_and_stock_reused(steps: list[ResearchWorkflowStep]) -> bool:
    verification_updated = any(
        step.name == "verify_external_data_boundary" and step.status == "completed"
        for step in steps
    )
    stock_reused = any(
        step.name == "generate_stock_lens_report" and step.status == "reused"
        for step in steps
    )
    return verification_updated and stock_reused


def _unique(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
