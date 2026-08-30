"""Spec 037: the summary profile registry.

The registry is pure data, so these tests construct no provider, touch no
network, and need no ``api_cost_ack`` — except where the threading tests
deliberately exercise the factory.

The ``finance`` assertions compare against literals hardcoded *here* rather than
against the implementation. Comparing the registry to ``_chunk_prompt`` would
pass even if both drifted together; the literal is what makes 股癌's already
published summaries a fixed point.
"""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError

import pytest

from corpus_ingest_core.errors import LLMProviderConfigError, UnknownSummaryProfileError
from corpus_ingest_core.summary_profiles import (
    DEFAULT_SUMMARY_PROFILE,
    FINANCE,
    LEARNING_NOTES,
    SUMMARY_PROFILES,
    UNSET,
    resolve_summary_profile,
)

# --- Frozen copies of today's behaviour (pre-Spec-037 source) ----------------

FINANCE_CHUNK_SYSTEM = (
    "你是 podcast 逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，所有重點盡量附 timestamp evidence，不要產生投資建議。"
)
FINANCE_CHUNK_SECTIONS = (
    "請包含：主要內容、提到的人物 / 公司 / 股票 / 產業 / 地點 / 書籍 / 電影 / 餐廳、可引用片段、不確定事項。"
)
FINANCE_CHUNK_CONSTRAINTS = "限制：不要產生投資建議；所有判斷都要能回到逐字稿 timestamp。"
FINANCE_FINAL_SYSTEM = (
    "你是 podcast 語意摘要器。根據 chunk summaries 整理整集摘要，"
    "不得產生投資建議，所有市場觀點、公司、人物與事件都要盡量附 timestamp evidence。"
)
FINANCE_FINAL_SECTIONS = (
    "請將以下 chunk summaries 合併成整集摘要，使用 Markdown，包含本集主題、市場觀點、"
    "台股觀點、美股觀點、總經觀點、提到的公司 / 股票 / 產業、"
    "人物 / 書 / 電影 / 音樂 / 餐廳 / 地點、生活閒聊、廣告 / 業配段落、時間軸摘要、"
    "可驗證引用、不確定事項。"
)
FINANCE_FINAL_CONSTRAINTS = "限制：不要產生投資建議；所有重要判斷都要盡量附 timestamp evidence。"
FINANCE_LIMITATION_LINES = (
    "本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。",
    "本摘要不構成投資建議。",
)
FINANCE_EXTRACTIVE_PROMPT_LINES = (
    "請根據本集逐字稿整理：",
    "1. 本集主題",
    "2. 市場觀點",
    "3. 提到的公司 / 股票 / 產業",
    "4. 總經觀點",
    "5. 生活閒聊",
    "6. 廣告段落",
    "7. 可驗證時間戳引用",
    "",
    "限制：",
    "- 不要產生投資建議。",
    "- 所有判斷都要能回到逐字稿。",
)


# --- T007: the registry itself ----------------------------------------------


def test_registry_holds_exactly_two_profiles():
    assert set(SUMMARY_PROFILES) == {"finance", "learning-notes"}
    assert FINANCE == "finance"
    assert LEARNING_NOTES == "learning-notes"
    assert DEFAULT_SUMMARY_PROFILE == FINANCE


def test_unconfigured_profile_resolves_to_finance():
    """A missing key is the only thing that means "use the default"."""

    assert resolve_summary_profile().name == FINANCE
    assert resolve_summary_profile(UNSET).name == FINANCE


def test_explicit_null_is_refused_rather_than_treated_as_unconfigured():
    """YAML ``summary_profile:`` is an operator writing something deliberate.
    Conflating it with an absent key is the last silent path, and this package's
    own doctrine is that an unenforced discriminant is a defect."""

    with pytest.raises(UnknownSummaryProfileError):
        resolve_summary_profile(None)


def test_unknown_profile_names_both_the_bad_value_and_the_known_ones():
    """A silent fallback to finance is the failure mode this refusal prevents."""

    with pytest.raises(UnknownSummaryProfileError) as excinfo:
        resolve_summary_profile("leraning-notes")

    message = str(excinfo.value)
    assert "leraning-notes" in message
    assert "finance" in message
    assert "learning-notes" in message


@pytest.mark.parametrize("value", [123, True, False, "", "   ", [], {}, 1.5])
def test_non_string_profile_is_refused_rather_than_defaulted(value):
    """``config._optional_text`` turns a non-string into None; that must not
    become a silent finance fallback here."""

    with pytest.raises(UnknownSummaryProfileError):
        resolve_summary_profile(value)


def test_registry_module_performs_no_io():
    """Pure data is the reason this module is testable without a provider."""

    import corpus_ingest_core.summary_profiles as module

    source = inspect.getsource(module)
    for forbidden in ("import os", "import requests", "open(", "Path(", "getenv"):
        assert forbidden not in source, f"summary_profiles must stay pure: {forbidden}"


def test_profiles_are_frozen():
    profile = resolve_summary_profile(FINANCE)
    with pytest.raises(FrozenInstanceError):
        profile.name = "mutated"  # type: ignore[misc]


# --- T008: finance is a fixed point -----------------------------------------


def test_finance_profile_matches_the_pre_spec_037_literals():
    profile = resolve_summary_profile(FINANCE)

    assert profile.chunk_system == FINANCE_CHUNK_SYSTEM
    assert profile.chunk_sections == FINANCE_CHUNK_SECTIONS
    assert profile.chunk_constraints == FINANCE_CHUNK_CONSTRAINTS
    assert profile.final_system == FINANCE_FINAL_SYSTEM
    assert profile.final_sections == FINANCE_FINAL_SECTIONS
    assert profile.final_constraints == FINANCE_FINAL_CONSTRAINTS
    assert profile.limitation_lines == FINANCE_LIMITATION_LINES
    assert profile.extractive_prompt_lines == FINANCE_EXTRACTIVE_PROMPT_LINES


def test_finance_chunk_prompt_renders_exactly_as_before():
    from corpus_ingest_core.llm_provider import _chunk_prompt

    chunk = {
        "index": 1,
        "start_time": "00:00:00",
        "end_time": "00:10:00",
        "text": "示範逐字稿內容。",
    }

    assert _chunk_prompt(resolve_summary_profile(FINANCE), chunk) == "\n".join(
        [
            "請摘要 chunk 1，時間範圍 00:00:00 - 00:10:00。",
            "",
            FINANCE_CHUNK_SECTIONS,
            FINANCE_CHUNK_CONSTRAINTS,
            "",
            "示範逐字稿內容。",
        ]
    )


def test_finance_final_prompt_renders_exactly_as_before():
    from corpus_ingest_core.llm_provider import _final_prompt

    rendered = _final_prompt(
        resolve_summary_profile(FINANCE),
        podcast_display_name="Gooaye 股癌",
        episode_ref="EP687",
        title="示範標題",
        chunk_summaries=["chunk one", "chunk two"],
    )

    assert rendered == "\n\n".join(
        [
            "Podcast: Gooaye 股癌",
            "Episode: EP687",
            "Title: 示範標題",
            FINANCE_FINAL_SECTIONS,
            FINANCE_FINAL_CONSTRAINTS,
            "chunk one\n\nchunk two",
        ]
    )


# --- T009: the learning-notes shape -----------------------------------------


def test_learning_notes_chunk_prompt_asks_for_teaching_nouns_not_market_nouns():
    profile = resolve_summary_profile(LEARNING_NOTES)

    for wanted in ("觀念", "方法", "工具", "名詞", "可引用片段", "不確定事項"):
        assert wanted in profile.chunk_sections
    for unwanted in ("股票", "產業", "市場"):
        assert unwanted not in profile.chunk_sections


def test_learning_notes_final_prompt_asks_for_the_study_sections_in_order():
    profile = resolve_summary_profile(LEARNING_NOTES)

    expected_order = [
        "本片主題與適合誰看",
        "核心觀念",
        "可操作步驟與實際用法",
        "常見錯誤用法 vs 正確用法",
        "值得記住的名詞與工具",
        "可直接複用的 prompt 或範例片段",
        "時間軸摘要",
        "可驗證引用",
        "不確定事項",
    ]

    positions = [profile.final_sections.find(section) for section in expected_order]
    assert all(position >= 0 for position in positions), dict(zip(expected_order, positions, strict=True))
    assert positions == sorted(positions), "sections must appear in the FR-014 order"


def test_learning_notes_final_prompt_carries_no_market_vocabulary():
    profile = resolve_summary_profile(LEARNING_NOTES)

    for unwanted in ("市場觀點", "台股", "美股", "總經", "業配", "股票"):
        assert unwanted not in profile.final_sections
        assert unwanted not in profile.final_constraints
        assert unwanted not in profile.final_system


def test_learning_notes_limitation_lines_carry_no_investment_disclaimer():
    profile = resolve_summary_profile(LEARNING_NOTES)

    body = "\n".join(profile.limitation_lines)
    assert "投資" not in body
    assert "LLM" in body
    assert "timestamp" in body


# --- FR-015: evidence discipline is repo policy, not a finance convention ----


@pytest.mark.parametrize("name", [FINANCE, LEARNING_NOTES])
def test_every_profile_requires_uncertainty_and_timestamp_traceability(name):
    profile = resolve_summary_profile(name)

    assert "不確定事項" in profile.chunk_sections
    assert "不確定事項" in profile.final_sections
    assert "timestamp" in profile.chunk_constraints
    assert "timestamp" in profile.final_constraints
    assert "timestamp" in "\n".join(profile.limitation_lines)


# --- T013: threading through the factory ------------------------------------


def test_create_provider_takes_summary_profile_keyword_only_with_finance_default():
    from corpus_ingest_core.llm_provider import create_provider

    parameters = inspect.signature(create_provider).parameters

    assert "summary_profile" in parameters
    assert parameters["summary_profile"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["summary_profile"].default == DEFAULT_SUMMARY_PROFILE
    # Spec 036/037 safety boundary: the ack gate keeps its own shape.
    assert parameters["api_cost_ack"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["api_cost_ack"].default == ""


def test_wrong_ack_raises_before_the_profile_is_resolved(monkeypatch):
    """An invalid profile name must never precede, mask, or substitute for an
    ack failure. Pass both a wrong ack and a bad profile; the ack must win."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    from corpus_ingest_core.llm_provider import create_provider

    with pytest.raises(LLMProviderConfigError, match="api_cost_ack"):
        create_provider(
            "openai-compatible",
            model="test-model",
            api_cost_ack="wrong",
            summary_profile="leraning-notes",
        )


def _provider_with_captured_messages(monkeypatch, summary_profile):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    provider = create_provider(
        "openai-compatible",
        model="test-model",
        api_cost_ack=SEMANTIC_API_COST_ACK,
        summary_profile=summary_profile,
    )

    captured: list[list[dict[str, str]]] = []

    def _fake_complete(messages):
        captured.append(messages)
        return "stubbed"

    monkeypatch.setattr(provider, "complete", _fake_complete)
    return provider, captured


def test_provider_sends_the_profile_prompts_for_learning_notes(monkeypatch):
    provider, captured = _provider_with_captured_messages(monkeypatch, LEARNING_NOTES)
    profile = resolve_summary_profile(LEARNING_NOTES)

    provider.summarize_chunk({"index": 1, "start_time": "00:00:00", "end_time": "00:10:00", "text": "內容"})
    provider.summarize_final(
        podcast_display_name="@Raytar (X)",
        episode_ref="2071290493581840707",
        title="示範標題",
        chunk_summaries=["chunk one"],
    )

    chunk_messages, final_messages = captured
    assert chunk_messages[0]["content"] == profile.chunk_system
    assert profile.chunk_sections in chunk_messages[1]["content"]
    assert final_messages[0]["content"] == profile.final_system
    assert profile.final_sections in final_messages[1]["content"]
    assert "投資建議" not in final_messages[1]["content"]


def test_provider_defaults_to_the_finance_prompts(monkeypatch):
    """An existing caller that passes no profile must be unchanged."""

    provider, captured = _provider_with_captured_messages(monkeypatch, DEFAULT_SUMMARY_PROFILE)

    provider.summarize_chunk({"index": 1, "start_time": "00:00:00", "end_time": "00:10:00", "text": "內容"})

    assert captured[0][0]["content"] == FINANCE_CHUNK_SYSTEM
    assert FINANCE_CHUNK_SECTIONS in captured[0][1]["content"]


# --- Post-review hardening -------------------------------------------------


@pytest.mark.parametrize("name", sorted(SUMMARY_PROFILES))
def test_no_profile_body_line_can_forge_a_markdown_heading(name):
    """The rendered envelope is a contract for four downstream readers. The
    renderers own every heading, and the profile injects only body lines — but
    nothing stopped a body line from *starting* with ``#``. A line reading
    ``## Chunk Summaries`` inside the limitation block would truncate
    ``stock_lens_synthesis.py``'s maxsplit=1 split and confuse
    ``semantic_review_artifact``. Turn construction-plus-convention into
    construction-plus-invariant before a third profile exists, not after."""

    profile = resolve_summary_profile(name)

    for line in (*profile.limitation_lines, *profile.extractive_prompt_lines):
        assert not line.lstrip().startswith("#"), (
            f"{name}: a profile body line must never look like a heading: {line!r}"
        )


def test_unknown_profile_at_the_factory_raises_the_profile_error(monkeypatch):
    """Unreachable through the real pipeline — config canonicalises the name
    first — but it is the one new branch with no test, and the error type that
    escapes ``create_provider`` is not an ``LLMProviderConfigError``."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    with pytest.raises(UnknownSummaryProfileError):
        create_provider(
            "openai-compatible",
            model="test-model",
            api_cost_ack=SEMANTIC_API_COST_ACK,
            summary_profile="leraning-notes",
        )
