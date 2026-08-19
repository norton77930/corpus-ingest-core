"""Spec 038: study-guide bundle runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from podcast_ingest_core.errors import LLMProviderConfigError, StudyGuideBundleError
from podcast_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from podcast_ingest_core.study_guide_bundle import (
    run_study_guide_bundle,
    result_to_dict,
)
from podcast_ingest_core.study_guide_profiles import COVER_FILENAME


PODCAST = "x-raytar"
EPISODE = "2071290493581840707"
TITLE = "Alpha Talk"

LEARNING_SUMMARY = """# @Raytar - learning notes

## Metadata

- Summary mode: semantic-llm
- Provider: openai-compatible
- Model: fake

## 摘要限制

本摘要由 LLM 根據逐字稿產生。

# 學習筆記

## 1. 影片主題與適合誰看

主題是 eval-driven prompt work [00:00:01 - 00:00:10]。

## 2. 核心觀念

### 2.1 Evals
- 是什麼：一組測試案例 [00:02:41 - 00:02:53]

## 9. 不確定事項

- 完整 Prompt 文本：可複用片段是依口述重構，不是逐字抄錄。

## Chunk Summaries

### Chunk 1

transcript body must not leak into the provider
"""

FINANCE_SUMMARY = """# gooaye summary

## Metadata

- Summary mode: semantic-llm

## 市場觀點

買進 [00:00:01 - 00:00:02]

## Chunk Summaries

x
"""


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _ready_episode(tmp_data_dirs: Path, *, finance_body: bool = False) -> None:
    from podcast_ingest_core import storage

    seed = storage.corpus_episode_seed_asset_path(PODCAST, EPISODE)
    _write_json(
        seed,
        {
            "podcast_id": PODCAST,
            "episode_ref": EPISODE,
            "title": TITLE,
            "published_at": "2026-06-28",
            "duration": "33:24",
            "guid_status": "present",
            "has_audio_url": True,
            "seed_source": "x-video",
            "selector": "https://x.com/Raytar/status/2071290493581840707",
            "warning_count": 0,
            "warnings": [],
            "not_investment_advice": True,
        },
    )
    transcript = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE)
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript.text_path.write_text("transcript body must not leak", encoding="utf-8")
    transcript.srt_path.write_text("1\n", encoding="utf-8")
    _write_json(
        transcript.json_path,
        {
            "podcast_id": PODCAST,
            "episode_ref": EPISODE,
            "title": TITLE,
            "language": "en",
            "segment_count": 1,
            "last_segment_end_seconds": 5.0,
            "segments": [
                {
                    "id": 1,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "transcript body must not leak",
                }
            ],
        },
    )
    summary = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        FINANCE_SUMMARY if finance_body else LEARNING_SUMMARY,
        encoding="utf-8",
    )
    audio = storage.audio_asset_path(PODCAST, EPISODE, TITLE, ".wav")
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"RIFF")


def _tree(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file()
    )


def _valid_payload() -> dict[str, str]:
    return {
        "03_full_summary": "\n".join(
            [
                "## 影片主題",
                "evals [00:00:01 - 00:00:10]",
                "## 核心觀念",
                "先量測 [00:02:41 - 00:02:53]",
                "## 影片結構",
                "開場",
                "## 一句話總結",
                "用 evals 迭代。",
                "## 適合誰看",
                "工程師",
                "## 不確定事項",
                "可複用片段是依口述重構，不是逐字抄錄。",
            ]
        ),
        "04_learning_notes": "\n".join(
            [
                "## 這個觀念是什麼",
                "Evals",
                "## 為什麼重要",
                "知道改動有沒有用",
                "## 影片中怎麼說",
                "[00:02:41 - 00:02:53]",
                "## 實際開發時怎麼用",
                "先寫測試",
                "## 錯誤用法",
                "憑感覺改",
                "## 正確用法",
                "先分類 failure mode",
                "## 不確定事項",
                "可複用片段是依口述重構，不是逐字抄錄。",
            ]
        ),
        "07_final_study_guide": "\n".join(
            [
                "## 背景知識",
                "prompt、model、evals",
                "## 核心重點",
                "先 eval 再改",
                "## 白話說明",
                "像單元測試",
                "## 常見錯誤",
                "沒有 eval 就改",
                "## 30 秒版本總結",
                "工程化迭代",
                "## 3 分鐘版本總結",
                "先 evals 再 hygiene",
                "## 不確定事項",
                "可複用片段是依口述重構，不是逐字抄錄。",
            ]
        ),
    }


class _FakeProvider:
    provider_name = "openai-compatible"
    model = "fake"

    def __init__(self, payload: dict[str, str], captured: list) -> None:
        self._payload = payload
        self._captured = captured

    def summarize_chunk(self, chunk: dict) -> str:
        raise AssertionError("summarize_chunk must not be used")

    def summarize_final(self, **kwargs: object) -> str:
        raise AssertionError("summarize_final must not be used")

    def complete(self, messages: list[dict[str, str]]) -> str:
        self._captured.append(messages)
        return json.dumps(self._payload, ensure_ascii=False)


def test_dry_run_writes_nothing_and_does_not_construct_provider(
    tmp_data_dirs, monkeypatch
):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("provider")),
    )
    before = _tree(tmp_data_dirs)

    result = run_study_guide_bundle(PODCAST, EPISODE)

    assert result.confirm is False
    assert result.run_mode == "dry-run"
    assert result.planned_writes
    assert not result.planned_reuses
    assert result.output_paths == {}
    assert _tree(tmp_data_dirs) == before
    payload = result_to_dict(result)
    assert payload["dry_run"] is True
    dumped = json.dumps(payload)
    assert "transcript body must not leak" not in dumped
    assert COVER_FILENAME.split(".")[0] in " ".join(result.planned_writes) or any(
        "00_video_info.md" in item for item in result.planned_writes
    )


def test_dry_run_reuse_says_reuse(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    captured.clear()
    before = _tree(tmp_data_dirs)

    result = run_study_guide_bundle(PODCAST, EPISODE)

    assert result.reused is True
    assert result.planned_reuses
    assert result.planned_writes == []
    assert captured == []
    assert _tree(tmp_data_dirs) == before
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    assert (paths.bundle_dir / "05_prompt_examples.md").exists() is False
    assert (paths.bundle_dir / "06_apply_to_my_workflow.md").exists() is False


def test_finance_profile_is_refused(tmp_data_dirs):
    with pytest.raises(StudyGuideBundleError, match="learning-notes"):
        run_study_guide_bundle("gooaye", "EP678")
    assert not (tmp_data_dirs / "study-guides").exists() or not any(
        (tmp_data_dirs / "study-guides").rglob("*.md")
    )


def test_missing_summary_is_refused(tmp_data_dirs):
    with pytest.raises(StudyGuideBundleError, match="semantic summary is missing"):
        run_study_guide_bundle(PODCAST, EPISODE)


def test_finance_shaped_source_is_refused(tmp_data_dirs):
    _ready_episode(tmp_data_dirs, finance_body=True)
    with pytest.raises(StudyGuideBundleError, match="finance-shaped"):
        run_study_guide_bundle(PODCAST, EPISODE)


def test_wrong_ack_does_not_construct_provider(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    calls: list[int] = []

    def _create(*args: object, **kwargs: object) -> None:
        calls.append(1)
        raise AssertionError("create_provider")

    monkeypatch.setattr(bundle, "create_provider", _create)
    with pytest.raises(LLMProviderConfigError, match="api_cost_ack"):
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="nope")
    assert calls == []


def test_confirm_writes_four_files_and_keeps_uncertainty(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )

    result = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )

    assert result.confirm is True
    assert result.reused is False
    assert result.warnings
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    assert paths.cover_path.is_file()
    assert paths.summary_path.is_file()
    assert paths.notes_path.is_file()
    assert paths.guide_path.is_file()
    cover = paths.cover_path.read_text(encoding="utf-8")
    assert "x-video" in cover
    assert "codec" not in cover.lower()
    assert "1920" not in cover
    summary = paths.summary_path.read_text(encoding="utf-8")
    assert "影片主題" in summary
    assert "市場觀點" not in summary
    assert "依口述重構" in summary
    notes = paths.notes_path.read_text(encoding="utf-8")
    assert "這個觀念是什麼" in notes
    guide = paths.guide_path.read_text(encoding="utf-8")
    assert "30 秒版本總結" in guide
    assert captured, "complete() should run once"
    joined = json.dumps(captured, ensure_ascii=False)
    assert "transcript body must not leak" not in joined
    assert "Chunk Summaries" not in joined
    assert "Claude Code" not in guide
    dumped = json.dumps(result_to_dict(result))
    assert "transcript body must not leak" not in dumped


def test_advice_shaped_body_is_rejected(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["03_full_summary"] += "\n建議你買進這檔股票，目標價 1000。\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    with pytest.raises(StudyGuideBundleError, match="prohibited_advice"):
        run_study_guide_bundle(
            PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
        )


def test_partial_bundle_is_refused_unless_force(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    paths.notes_path.unlink()
    with pytest.raises(StudyGuideBundleError, match="incomplete"):
        run_study_guide_bundle(PODCAST, EPISODE)
    assert captured  # first confirm only
    first_calls = len(captured)
    with pytest.raises(StudyGuideBundleError, match="incomplete"):
        run_study_guide_bundle(
            PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
        )
    assert len(captured) == first_calls


def test_missing_cover_only_does_not_call_llm(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    paths.cover_path.unlink()
    captured.clear()
    planned = run_study_guide_bundle(PODCAST, EPISODE)
    assert planned.planned_writes == [str(paths.cover_path)]
    assert captured == []
    result = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack="wrong"
    )
    assert captured == []
    assert paths.cover_path.is_file()
    assert result.reused is False


def test_required_phrases_may_appear_in_body_not_only_headings(
    tmp_data_dirs, monkeypatch
):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["04_learning_notes"] = "\n".join(
        [
            "## Evals",
            "這個觀念是什麼：一組測試。",
            "為什麼重要：知道改動有沒有用。",
            "影片中怎麼說：[00:02:41 - 00:02:53]",
            "實際開發時怎麼用：先寫測試。",
            "錯誤用法：憑感覺改。",
            "正確用法：先分類 failure mode。",
            "## 不確定事項",
            "可複用片段是依口述重構，不是逐字抄錄。",
        ]
    )
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    result = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    notes = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).notes_path
    assert "這個觀念是什麼" in notes.read_text(encoding="utf-8")
    assert result.confirm is True


def test_merged_source_clocks_are_accepted(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["04_learning_notes"] += "\nmerged [00:00:01 - 00:02:53]\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    result = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    assert result.confirm is True


def test_invented_timestamp_is_rejected(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["03_full_summary"] += "\nseen at [00:99:99 - 00:99:99]\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    with pytest.raises(StudyGuideBundleError, match="timestamp"):
        run_study_guide_bundle(
            PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
        )


def test_force_rewrites_existing_bundle(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage, study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    first = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    assert first.reused is False
    reused = run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    assert reused.reused is True
    assert len(captured) == 1
    forced = run_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        force=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )
    assert forced.reused is False
    assert len(captured) == 2
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    assert paths.summary_path.is_file()


def test_workflow_markers_not_in_source_are_rejected(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["07_final_study_guide"] += "\n\nUse Claude Code to apply this.\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    with pytest.raises(StudyGuideBundleError, match="Claude Code"):
        run_study_guide_bundle(
            PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
        )


def test_artifact_ladder_does_not_include_study_guide():
    from podcast_ingest_core.corpus_remediation_plan import ARTIFACT_LADDER

    assert "study_guide" not in ARTIFACT_LADDER


def test_index_reports_available_and_partial(tmp_data_dirs, monkeypatch):
    from podcast_ingest_core import storage
    from podcast_ingest_core.corpus_index import generate_corpus_index
    from podcast_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    bundle.run_study_guide_bundle(
        PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK
    )
    result = generate_corpus_index(PODCAST)
    payload = json.loads(result.index_json_path.read_text(encoding="utf-8"))
    row = payload["episodes"][0]
    assert row["artifact_status"]["study_guide"]["status"] == "available"
    assert payload["artifact_family_counts"]["study_guide"]["available"] == 1

    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    paths.guide_path.unlink()
    result = generate_corpus_index(PODCAST)
    payload = json.loads(result.index_json_path.read_text(encoding="utf-8"))
    row = payload["episodes"][0]
    assert row["artifact_status"]["study_guide"]["status"] == "partial"
    assert payload["artifact_family_counts"]["study_guide"]["unreadable"] == 1


def test_cli_defaults_match_semantic_key_name():
    from scripts.run_study_guide_bundle import build_parser

    parser = build_parser()
    args = parser.parse_args(["--podcast", "x-raytar", "--episode", "1"])
    assert args.api_key_env == "API_KEY"
    assert args.confirm is False


def test_cli_stdout_is_metadata_only(tmp_data_dirs, monkeypatch, capsys):
    from scripts import run_study_guide_bundle as cli

    _ready_episode(tmp_data_dirs)
    cli.main(["--podcast", PODCAST, "--episode", EPISODE])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["dry_run"] is True
    assert "transcript body must not leak" not in captured.out
    assert "transcript body must not leak" not in captured.err
