from __future__ import annotations

import json
import os
import sys

import pytest


ACK = (
    "I understand this may call an external LLM API, send transcript text outside this machine, "
    "and incur costs."
)


class FakeSynthesisProvider:
    provider_name = "openai-compatible"
    model = "test-model"

    def __init__(self, response: str | None = None):
        self.response = response or (
            "這份 synthesis 只根據 stock lens JSON：台積電有 direct podcast evidence；"
            "NVIDIA 是 inferred_from_industry research lead；external data remains not_fetched。"
        )
        self.messages = []

    def complete(self, messages):
        self.messages.append(messages)
        return self.response


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

    monkeypatch.setattr(storage, "STOCK_LENS_DIR", tmp_path / "stock-lens", raising=False)


def _write_stock_lens(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    stock_query="台積電",
    report_status="final",
    report_mode="deterministic-stock-lens-v1",
):
    from corpus_ingest_core.storage import stock_lens_report_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    paths = stock_lens_report_asset_paths(podcast_id, stock_query)
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "podcast_id": podcast_id,
        "stock_query": stock_query,
        "report_mode": report_mode,
        "report_status": report_status,
        "source_status": {
            "industry_mappings": "available",
            "external_boundaries": "available",
            "gooaye_lens": "available",
        },
        "query_match_summary": {
            "stock_query": stock_query,
            "matched_candidate_count": 2,
            "direct_podcast_evidence_count": 0
            if report_status == "no-direct-podcast-evidence"
            else 1,
            "inferred_research_lead_count": 1,
            "no_direct_podcast_evidence": report_status == "no-direct-podcast-evidence",
        },
        "direct_podcast_evidence": [] if report_status == "no-direct-podcast-evidence" else [
            {
                "episode_ref": "EP672",
                "title": "EP672 title",
                "company_name": "台積電",
                "tickers": ["2330.TW", "TSM"],
                "relation": "podcast_mention",
                "relation_type": "podcast_explicit",
                "evidence_status": "podcast_explicit",
                "verification_status": "podcast_evidence",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
                "external_boundary": {
                    "external_verification_status": "not_requested",
                    "source_status": "not_fetched",
                    "data_date": None,
                    "required_external_checks": [
                        {
                            "data_type": "company_identity",
                            "label": "Company identity and legal entity",
                        }
                    ],
                },
            }
        ],
        "inferred_research_leads": [
            {
                "episode_ref": "EP672",
                "title": "EP672 title",
                "company_name": "NVIDIA",
                "tickers": ["NVDA"],
                "relation": "accelerator_design",
                "relation_type": "inferred_from_industry",
                "evidence_status": "inferred_from_industry",
                "verification_status": "needs_verification",
                "evidence": [
                    {
                        "segment_id": 1,
                        "start": 83.1,
                        "end": 90.2,
                        "timestamp": "[00:01:23 - 00:01:30]",
                        "text": "今天聊到台積電、半導體和 AI 需求。",
                    }
                ],
                "external_boundary": {
                    "external_verification_status": "not_requested",
                    "source_status": "not_fetched",
                    "data_date": None,
                    "required_external_checks": [
                        {
                            "data_type": "market_snapshot",
                            "label": "Price, market cap, and liquidity snapshot",
                        }
                    ],
                },
            }
        ],
        "gooaye_lens": {
            "name": "Gooaye Lens",
            "version": 1,
            "dimension_count": 1,
            "dimensions": [
                {
                    "id": "industry_chain_position",
                    "label": "產業鏈位置",
                    "output_guidance": "Separate explicit podcast evidence from inferred chain position.",
                }
            ],
            "safety_rules": [
                "Do not provide buy/sell/hold advice.",
                "Do not provide target price.",
                "Separate podcast evidence, inference, and external-data status.",
            ],
        },
        "external_verification_needs": [
            {
                "company_name": "台積電",
                "tickers": ["2330.TW", "TSM"],
                "episode_ref": "EP672",
                "required_external_checks": [{"data_type": "company_identity"}],
                "external_verification_status": "not_requested",
                "source_status": "not_fetched",
                "data_date": None,
            }
        ],
        "warnings": [],
        "not_investment_advice": True,
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    paths.markdown_path.write_text("# stock lens", encoding="utf-8")
    return paths


def _write_semantic_context(
    monkeypatch,
    tmp_path,
    *,
    review_status="passed",
    body_extra="",
):
    from corpus_ingest_core import storage
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries", raising=False)
    monkeypatch.setattr(
        synthesis,
        "SEMANTIC_REVIEW_REPORTS_DIR",
        tmp_path / "evals" / "research-llm-smoke" / "reports",
        raising=False,
    )
    summary_path = tmp_path / "summaries" / "gooaye" / "EP672__EP672.semantic.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "\n".join(
            [
                "# Gooaye 股癌 - EP672 語意摘要",
                "",
                "## Metadata",
                "",
                "- Podcast ID: gooaye",
                "- Episode: EP672",
                "- Summary mode: semantic-llm",
                "- Provider: openai-compatible",
                "- Model: GB10",
                "",
                "## Synthesis",
                "",
                "Reviewed semantic summary says 台積電產能限制延長 AI cycle [00:26:35 - 00:27:04].",
                body_extra,
                "",
                "## Chunk Summaries",
                "",
                "raw-ish chunk detail that must not enter synthesis prompt",
            ]
        ),
        encoding="utf-8",
    )
    review_dir = tmp_path / "evals" / "research-llm-smoke" / "reports"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / "20260702-000848__gooaye__EP672.semantic-review.json"
    review_path.write_text(
        json.dumps(
            {
                "review_status": review_status,
                "semantic_summary_path": str(summary_path),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return summary_path, review_path


def test_stock_lens_synthesis_dry_run_requires_ack_and_writes_nothing(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built during dry-run"),
    )

    result = synthesis.generate_stock_lens_synthesis_report("gooaye", "台積電")

    assert result.dry_run is True
    assert result.requires_confirmation is True
    assert result.requires_api_cost_ack is True
    assert result.required_acknowledgement == ACK
    assert result.source_report_status == "final"
    assert "Calls an external LLM API" in result.risks
    assert "Uses only Phase 6F stock lens JSON as LLM input" in result.risks
    assert not result.synthesis_json_path.exists()
    assert not result.synthesis_markdown_path.exists()


def test_stock_lens_synthesis_refuses_non_finance_summary_profile(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path, podcast_id="x-raytar")
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built for a non-finance profile"),
    )

    with pytest.raises(StockLensSynthesisInputError, match="learning-notes"):
        synthesis.generate_stock_lens_synthesis_report("x-raytar", "ignored")

    with pytest.raises(StockLensSynthesisInputError, match="learning-notes"):
        synthesis.generate_stock_lens_synthesis_report(
            "x-raytar",
            "ignored",
            confirm=True,
            api_cost_ack=ACK,
        )


def test_stock_lens_synthesis_refuses_unknown_podcast_before_provider(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path, podcast_id="no-such-podcast")
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built for an unknown podcast"),
    )

    with pytest.raises(StockLensSynthesisInputError, match="no-such-podcast"):
        synthesis.generate_stock_lens_synthesis_report("no-such-podcast", "台積電")


def test_stock_lens_synthesis_confirm_requires_exact_ack_before_writes(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built without exact ack"),
    )

    with pytest.raises(StockLensSynthesisInputError, match="api_cost_ack"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack="wrong",
        )

    assert not (tmp_path / "stock-lens" / "gooaye" / "台積電.stock-lens-synthesis.json").exists()


def test_stock_lens_synthesis_confirm_writes_json_and_markdown(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    monkeypatch.delenv(synthesis.DEBUG_OUTPUT_PATH_ENV, raising=False)
    _write_stock_lens(monkeypatch, tmp_path)
    provider = FakeSynthesisProvider()
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: provider)
    raw_path = tmp_path / "raw-output.md"

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        api_cost_ack=ACK,
        model="test-model",
    )

    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    markdown = result.synthesis_markdown_path.read_text(encoding="utf-8")
    prompt_text = provider.messages[0][1]["content"]
    assert result.generated is True
    assert result.already_exists is False
    assert result.synthesis_status == "final"
    assert payload["synthesis_mode"] == "llm-stock-lens-synthesis-v1"
    assert payload["source_report_mode"] == "deterministic-stock-lens-v1"
    assert payload["source_report_status"] == "final"
    assert payload["llm_input_boundary"] == "phase-6f-stock-lens-json-only"
    assert "synthesis_text" in payload
    assert "不構成投資建議" in markdown
    assert "No buy/sell/hold advice" in markdown
    assert "raw transcript was not used" in markdown
    assert "今天聊到台積電" in prompt_text
    assert ".semantic.md" not in prompt_text
    assert "OPENAI_API_KEY" not in json.dumps(payload, ensure_ascii=False)
    assert not raw_path.exists()


def test_stock_lens_synthesis_can_include_reviewed_semantic_context(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(monkeypatch, tmp_path)
    _write_semantic_context(monkeypatch, tmp_path)
    provider = FakeSynthesisProvider("synthesis used reviewed semantic context safely.")
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: provider)

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        force=True,
        api_cost_ack=ACK,
        include_semantic_context=True,
    )

    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    prompt_text = provider.messages[0][1]["content"]
    assert payload["llm_input_boundary"] == (
        "phase-6f-stock-lens-json-plus-reviewed-semantic-summary"
    )
    assert payload["source_semantic_context"][0]["episode_ref"] == "EP672"
    assert payload["source_semantic_context"][0]["review_status"] == "passed"
    assert "Reviewed semantic summary says 台積電產能限制延長 AI cycle" in prompt_text
    assert "reviewed_semantic_context" in prompt_text
    assert "## Chunk Summaries" not in prompt_text
    assert "raw-ish chunk detail" not in prompt_text
    assert "sk-test-secret" not in prompt_text


def test_stock_lens_synthesis_semantic_context_requires_passed_review(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(monkeypatch, tmp_path)
    _write_semantic_context(monkeypatch, tmp_path, review_status="failed")
    provider = FakeSynthesisProvider()
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: provider)

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        force=True,
        api_cost_ack=ACK,
        include_semantic_context=True,
    )

    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    prompt_text = provider.messages[0][1]["content"]
    assert payload["llm_input_boundary"] == "phase-6f-stock-lens-json-only"
    assert payload["source_semantic_context"] == []
    assert any("semantic review not passed" in warning for warning in payload["warnings"])
    assert "Reviewed semantic summary says" not in prompt_text


def test_stock_lens_synthesis_semantic_context_truncates_with_warning(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(monkeypatch, tmp_path)
    _write_semantic_context(monkeypatch, tmp_path, body_extra="X" * 200)
    provider = FakeSynthesisProvider()
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: provider)

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        force=True,
        api_cost_ack=ACK,
        include_semantic_context=True,
        semantic_context_max_chars=80,
    )

    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    context_text = payload["source_semantic_context"][0]["content"]
    assert len(context_text) <= 120
    assert "[semantic context truncated]" in context_text
    assert any("semantic context truncated" in warning for warning in payload["warnings"])


def test_stock_lens_synthesis_debug_output_writes_success_response(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    response = "debug raw synthesis text"
    raw_path = tmp_path / "raw" / "success.llm-output.md"
    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setenv(synthesis.DEBUG_OUTPUT_PATH_ENV, str(raw_path))
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: FakeSynthesisProvider(response),
    )

    synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        api_cost_ack=ACK,
    )

    assert raw_path.read_text(encoding="utf-8") == response


def test_stock_lens_synthesis_debug_output_writes_before_guard_failure(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    response = "Buy 台積電 now."
    raw_path = tmp_path / "raw" / "blocked.llm-output.md"
    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setenv(synthesis.DEBUG_OUTPUT_PATH_ENV, str(raw_path))
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: FakeSynthesisProvider(response),
    )

    with pytest.raises(StockLensSynthesisInputError) as exc_info:
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )

    message = str(exc_info.value)
    assert "matched_guard=trade_action" in message
    assert response not in message
    assert raw_path.read_text(encoding="utf-8") == response


def test_stock_lens_synthesis_debug_output_invalid_path_fails_cleanly(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisFailedError

    raw_path = tmp_path / "raw-directory"
    raw_path.mkdir()
    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setenv(synthesis.DEBUG_OUTPUT_PATH_ENV, str(raw_path))
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: FakeSynthesisProvider())

    with pytest.raises(StockLensSynthesisFailedError, match="debug LLM output"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )


def test_stock_lens_synthesis_preserves_no_evidence_inference_and_external_status(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(
        monkeypatch,
        tmp_path,
        stock_query="不存在公司",
        report_status="no-direct-podcast-evidence",
    )
    provider = FakeSynthesisProvider(
        "沒有 direct podcast evidence。NVIDIA remains needs_verification；"
        "external status remains not_requested / not_fetched / data_date=null。"
    )
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: provider)

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "不存在公司",
        confirm=True,
        api_cost_ack=ACK,
    )
    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))

    assert payload["synthesis_status"] == "no-direct-podcast-evidence"
    assert payload["source_query_match_summary"]["no_direct_podcast_evidence"] is True
    assert payload["source_query_match_summary"]["direct_podcast_evidence_count"] == 0
    assert payload["source_inferred_research_leads"][0]["verification_status"] == "needs_verification"
    assert payload["source_external_verification_needs"][0]["source_status"] == "not_fetched"
    assert payload["source_external_verification_needs"][0]["external_verification_status"] == "not_requested"
    assert payload["source_external_verification_needs"][0]["data_date"] is None


def test_stock_lens_synthesis_handles_partial_source(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path, report_status="partial-draft")
    monkeypatch.setattr(synthesis, "_build_provider", lambda **kwargs: FakeSynthesisProvider())

    with pytest.raises(StockLensSynthesisInputError, match="partial-draft"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        api_cost_ack=ACK,
        allow_partial=True,
    )
    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    assert result.synthesis_status == "partial-draft"
    assert payload["synthesis_status"] == "partial-draft"


def test_stock_lens_synthesis_reuses_existing_without_force(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.storage import stock_lens_synthesis_asset_paths

    _write_stock_lens(monkeypatch, tmp_path)
    paths = stock_lens_synthesis_asset_paths("gooaye", "台積電")
    paths.json_path.write_text(
        json.dumps(
            {
                "synthesis_status": "final",
                "provider": "existing-provider",
                "model": "existing-model",
                "warning_count": 2,
            }
        ),
        encoding="utf-8",
    )
    paths.markdown_path.write_text("existing markdown", encoding="utf-8")
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built for reuse"),
    )

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        api_cost_ack=ACK,
    )

    assert result.generated is False
    assert result.already_exists is True
    assert result.synthesis_status == "final"
    assert paths.markdown_path.read_text(encoding="utf-8") == "existing markdown"


def test_stock_lens_synthesis_rejects_bad_source_inputs(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError
    from corpus_ingest_core.storage import stock_lens_report_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    with pytest.raises(StockLensSynthesisInputError, match="missing"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )

    paths = stock_lens_report_asset_paths("gooaye", "台積電")
    paths.json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.json_path.write_text("{", encoding="utf-8")
    with pytest.raises(StockLensSynthesisInputError, match="格式錯誤"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )

    _write_stock_lens(monkeypatch, tmp_path, report_mode="unsupported")
    with pytest.raises(StockLensSynthesisInputError, match="不支援"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
            force=True,
        )


def test_stock_lens_synthesis_provider_failures_and_output_guard(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import LLMProviderConfigError, StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path)

    def fail_provider(**kwargs):
        raise LLMProviderConfigError("missing model")

    monkeypatch.setattr(synthesis, "_build_provider", fail_provider)
    with pytest.raises(LLMProviderConfigError, match="missing model"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )
    assert not (tmp_path / "stock-lens" / "gooaye" / "台積電.stock-lens-synthesis.json").exists()

    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: FakeSynthesisProvider("Buy 台積電 with target price 1000."),
    )
    with pytest.raises(StockLensSynthesisInputError, match="matched_guard=trade_action"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )


@pytest.mark.parametrize(
    "response",
    [
        "這份 synthesis 僅供研究整理，不構成投資建議，也不提供買賣建議、目標價或保證報酬。",
        "This synthesis is not investment advice. No buy/sell/hold advice. No target price. No guaranteed returns.",
        "This synthesis does not constitute a buy, sell, or hold recommendation.",
        "This is not a buy, sell, or hold recommendation.",
        "No buy, sell, or hold recommendation is provided.",
        (
            "No Investment Advice: This synthesis does not constitute a buy, sell, "
            "or hold recommendation. No price targets or guaranteed returns are provided."
        ),
    ],
)
def test_stock_lens_synthesis_allows_safety_disclaimers(
    monkeypatch, tmp_path, response
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis

    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: FakeSynthesisProvider(response),
    )

    result = synthesis.generate_stock_lens_synthesis_report(
        "gooaye",
        "台積電",
        confirm=True,
        api_cost_ack=ACK,
    )

    payload = json.loads(result.synthesis_json_path.read_text(encoding="utf-8"))
    assert result.generated is True
    assert payload["synthesis_text"] == response


@pytest.mark.parametrize(
    "response",
    [
        "Buy 台積電 now.",
        "Sell 台積電 on weakness.",
        "Hold 台積電 until next quarter.",
        "建議買進台積電。",
        "不建議買進台積電。",
        "台積電目標價 1000 元。",
        "This has a target price of 1000.",
        "這檔股票保證報酬 20%。",
        "This has a guaranteed return of 20%.",
    ],
)
def test_stock_lens_synthesis_rejects_trade_advice_patterns(
    monkeypatch, tmp_path, response
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: FakeSynthesisProvider(response),
    )

    with pytest.raises(StockLensSynthesisInputError, match="investment advice"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
        )


def test_stock_lens_synthesis_rejects_prompt_over_limit(monkeypatch, tmp_path):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.errors import StockLensSynthesisInputError

    _write_stock_lens(monkeypatch, tmp_path)
    monkeypatch.setattr(
        synthesis,
        "_build_provider",
        lambda **kwargs: pytest.fail("provider must not be built when prompt is too large"),
    )

    with pytest.raises(StockLensSynthesisInputError, match="max_prompt_chars"):
        synthesis.generate_stock_lens_synthesis_report(
            "gooaye",
            "台積電",
            confirm=True,
            api_cost_ack=ACK,
            max_prompt_chars=10,
        )


def test_stock_lens_synthesis_path_removes_illegal_characters_and_emoji():
    from corpus_ingest_core.storage import stock_lens_synthesis_asset_paths

    paths = stock_lens_synthesis_asset_paths("gooaye", ' bad <stock> 🐣 : / \\ | ? * ok ')

    assert not any(character in paths.json_path.name for character in '<>:"/\\|?*')
    assert "🐣" not in paths.json_path.name
    assert paths.json_path.name == "bad_stock_ok.stock-lens-synthesis.json"
    assert paths.markdown_path.name == "bad_stock_ok.stock-lens-synthesis.md"


def test_stock_lens_synthesis_cli_parses_options_and_outputs_json(
    monkeypatch, tmp_path, capsys
):
    import corpus_ingest_core.stock_lens_synthesis as synthesis
    from corpus_ingest_core.models import StockLensSynthesisResult
    from scripts import generate_stock_lens_synthesis_report

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text(
        """
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
""".strip(),
        encoding="utf-8",
    )
    captured = {}
    asset = StockLensSynthesisResult(
        podcast_id="gooaye",
        stock_query="台積電",
        synthesis_json_path=tmp_path / "out.stock-lens-synthesis.json",
        synthesis_markdown_path=tmp_path / "out.stock-lens-synthesis.md",
        source_stock_lens_json_path=tmp_path / "in.stock-lens.json",
        synthesis_status="final",
        source_report_status="final",
        dry_run=False,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        required_acknowledgement=None,
        planned_reads=[str(tmp_path / "in.stock-lens.json")],
        planned_writes=[str(tmp_path / "out.stock-lens-synthesis.json")],
        risks=[],
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="test-model",
        prompt_char_count=123,
        warning_count=0,
        not_investment_advice=True,
    )

    def fake_generate(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        captured["debug_env"] = os.environ.get(synthesis.DEBUG_OUTPUT_PATH_ENV)
        return asset

    monkeypatch.setattr(
        generate_stock_lens_synthesis_report,
        "generate_stock_lens_synthesis_report",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_stock_lens_synthesis_report.py",
            "--podcast",
            "gooaye",
            "--stock",
            "台積電",
            "--confirm",
            "--force",
            "--allow-partial",
            "--api-cost-ack",
            ACK,
            "--llm-profile",
            "gb10",
            "--llm-profile-path",
            str(config_path),
            "--provider",
            "openai-compatible",
            "--model",
            "test-model",
            "--base-url",
            "https://example.test/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--max-prompt-chars",
            "12000",
            "--include-semantic-context",
            "--semantic-context-max-chars",
            "9000",
            "--debug-llm-output",
        ],
    )

    generate_stock_lens_synthesis_report.main()

    assert captured["args"] == ("gooaye", "台積電")
    assert captured["kwargs"] == {
        "confirm": True,
        "force": True,
        "allow_partial": True,
        "api_cost_ack": ACK,
        "provider": "openai-compatible",
        "model": "test-model",
        "base_url": "https://example.test/v1",
        "api_key_env": "TEST_API_KEY",
        "max_prompt_chars": 12000,
        "include_semantic_context": True,
        "semantic_context_max_chars": 9000,
    }
    debug_path = captured["debug_env"]
    assert debug_path.endswith(".llm-output.md")
    assert "台積電" in debug_path
    payload = json.loads(capsys.readouterr().out)
    assert payload["synthesis_status"] == "final"
    assert payload["generated"] is True
    assert payload["debug_llm_output_path"] == debug_path


def test_stock_lens_synthesis_cli_loads_env_file(monkeypatch, tmp_path, capsys):
    from corpus_ingest_core.models import StockLensSynthesisResult
    from scripts import generate_stock_lens_synthesis_report

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=file-model\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    captured = {}
    asset = StockLensSynthesisResult(
        podcast_id="gooaye",
        stock_query="台積電",
        synthesis_json_path=tmp_path / "out.stock-lens-synthesis.json",
        synthesis_markdown_path=tmp_path / "out.stock-lens-synthesis.md",
        source_stock_lens_json_path=tmp_path / "in.stock-lens.json",
        synthesis_status="final",
        source_report_status="final",
        dry_run=False,
        requires_confirmation=False,
        requires_api_cost_ack=False,
        required_acknowledgement=None,
        planned_reads=[str(tmp_path / "in.stock-lens.json")],
        planned_writes=[str(tmp_path / "out.stock-lens-synthesis.json")],
        risks=[],
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="file-model",
        prompt_char_count=123,
        warning_count=0,
        not_investment_advice=True,
    )

    def fake_generate(*args, **kwargs):
        captured["api_key"] = os.environ.get("API_KEY")
        captured["model"] = os.environ.get("MODEL")
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(
        generate_stock_lens_synthesis_report,
        "generate_stock_lens_synthesis_report",
        fake_generate,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_stock_lens_synthesis_report.py",
            "--podcast",
            "gooaye",
            "--stock",
            "台積電",
            "--env-file",
            str(env_path),
            "--api-key-env",
            "API_KEY",
        ],
    )

    generate_stock_lens_synthesis_report.main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert captured["api_key"] == "secret-value"
    assert captured["model"] == "file-model"
    assert captured["kwargs"]["api_key_env"] == "API_KEY"
    assert payload["local_env"]["loaded_env_var_names"] == ["API_KEY", "MODEL"]
    assert "secret-value" not in output
