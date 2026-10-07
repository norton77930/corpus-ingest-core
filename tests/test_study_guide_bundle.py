"""Spec 038: study-guide bundle runner."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from corpus_ingest_core.errors import LLMProviderConfigError, StudyGuideBundleError
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from corpus_ingest_core.study_guide_bundle import (
    result_to_dict,
    run_study_guide_bundle,
)
from corpus_ingest_core.study_guide_profiles import COVER_FILENAME

PODCAST = "x-raytar"
EPISODE = "2071290493581840707"
TITLE = "Alpha Talk"

LEARNING_SUMMARY = """# @Raytar - learning notes

## Metadata

- Summary mode: semantic-llm
- Provider: openai-compatible
- Model: fake

## Summary Limitations

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


def _ready_episode(
    tmp_data_dirs: Path,
    *,
    finance_body: bool = False,
    episode_ref: str = EPISODE,
    title: str = TITLE,
) -> None:
    from corpus_ingest_core import storage

    seed = storage.corpus_episode_seed_asset_path(PODCAST, episode_ref)
    _write_json(
        seed,
        {
            "podcast_id": PODCAST,
            "episode_ref": episode_ref,
            "title": title,
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
    transcript = storage.transcript_asset_paths(PODCAST, episode_ref, title)
    transcript.json_path.parent.mkdir(parents=True, exist_ok=True)
    transcript.text_path.write_text("transcript body must not leak", encoding="utf-8")
    transcript.srt_path.write_text("1\n", encoding="utf-8")
    _write_json(
        transcript.json_path,
        {
            "podcast_id": PODCAST,
            "episode_ref": episode_ref,
            "title": title,
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
    summary = storage.semantic_summary_asset_path(PODCAST, episode_ref, title)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        FINANCE_SUMMARY if finance_body else LEARNING_SUMMARY,
        encoding="utf-8",
    )
    audio = storage.audio_asset_path(PODCAST, episode_ref, title, ".wav")
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"RIFF")


def _tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file())


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


def test_dry_run_writes_nothing_and_does_not_construct_provider(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

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
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
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
    assert not (tmp_data_dirs / "study-guides").exists() or not any((tmp_data_dirs / "study-guides").rglob("*.md"))


def test_missing_summary_is_refused(tmp_data_dirs):
    with pytest.raises(StudyGuideBundleError, match="semantic summary is missing"):
        run_study_guide_bundle(PODCAST, EPISODE)


def test_finance_shaped_source_is_refused(tmp_data_dirs):
    _ready_episode(tmp_data_dirs, finance_body=True)
    with pytest.raises(StudyGuideBundleError, match="finance-shaped"):
        run_study_guide_bundle(PODCAST, EPISODE)


def test_wrong_ack_does_not_construct_provider(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

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
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )

    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)

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
    from corpus_ingest_core import study_guide_bundle as bundle

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
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)


def test_partial_bundle_is_refused_unless_force(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    paths.notes_path.unlink()
    with pytest.raises(StudyGuideBundleError, match="incomplete"):
        run_study_guide_bundle(PODCAST, EPISODE)
    assert captured  # first confirm only
    first_calls = len(captured)
    with pytest.raises(StudyGuideBundleError, match="incomplete"):
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert len(captured) == first_calls


def test_missing_cover_only_does_not_call_llm(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    paths = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE)
    paths.cover_path.unlink()
    captured.clear()
    planned = run_study_guide_bundle(PODCAST, EPISODE)
    assert planned.planned_writes == [str(paths.cover_path)]
    assert captured == []
    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="wrong")
    assert captured == []
    assert paths.cover_path.is_file()
    assert result.reused is False


def test_required_phrases_may_appear_in_body_not_only_headings(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

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
    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    notes = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).notes_path
    assert "這個觀念是什麼" in notes.read_text(encoding="utf-8")
    assert result.confirm is True


def test_merged_source_clocks_are_accepted(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    payload = _valid_payload()
    payload["04_learning_notes"] += "\nmerged [00:00:01 - 00:02:53]\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )
    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert result.confirm is True


def test_invented_timestamp_is_rejected(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

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
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)


def test_force_rewrites_existing_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    first = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert first.reused is False
    reused = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
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
    from corpus_ingest_core import study_guide_bundle as bundle

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
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)


def test_artifact_ladder_does_not_include_study_guide():
    from corpus_ingest_core.corpus_remediation_plan import ARTIFACT_LADDER

    assert "study_guide" not in ARTIFACT_LADDER


def test_index_reports_available_and_partial(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle
    from corpus_ingest_core.corpus_index import generate_corpus_index

    _ready_episode(tmp_data_dirs)
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    bundle.run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)
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


def _forbid_provider(monkeypatch) -> None:
    from corpus_ingest_core import study_guide_bundle as bundle

    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("provider")),
    )


def _generated_bundle(tmp_data_dirs, monkeypatch) -> None:
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), []),
    )
    run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack=SEMANTIC_API_COST_ACK)


def _non_cover_bytes(bundle: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in bundle.iterdir()
        if path.is_file() and path.name != COVER_FILENAME
    }


@pytest.mark.parametrize("cover_mode", ["missing", "invalid-utf8"])
def test_cover_only_preserves_lecture_derivation_and_extra_bytes(
    tmp_data_dirs, monkeypatch, cover_mode: str
):
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    bundle = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    preserved = {
        "03_full_summary.md": b"\xef\xbb\xbf## kept\r\nline-lf-only\n",
        "04_learning_notes.md": b"\xef\xbb\xbfnotes\r\ncrlf\r\n",
        "07_final_study_guide.md": b"\xef\xbb\xbfguide\r\n",
        "05_prompt_examples.md": b"\xef\xbb\xbf05 sentinel\r\n",
        "06_apply_to_my_workflow.md": b"06 sentinel\r\n\x00",
        "extra.bin": bytes([0x00, 0xFF, 0xFE]) + b"EXTRA\r\n",
        "notes.txt": b"\xef\xbb\xbfextra\r\ntext\n",
    }
    for name, body in preserved.items():
        (bundle / name).write_bytes(body)
    cover = bundle / COVER_FILENAME
    if cover_mode == "missing":
        cover.unlink()
    else:
        cover.write_bytes(b"\xff\xfe not utf-8 \x80")
    before = _non_cover_bytes(bundle)
    _forbid_provider(monkeypatch)

    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")

    assert result.reused is False
    assert set(result.output_paths) == {"00", "03", "04", "07"}
    assert _non_cover_bytes(bundle) == before
    assert cover.is_file()
    if cover_mode == "invalid-utf8":
        assert cover.read_bytes() != b"\xff\xfe not utf-8 \x80"


def test_allowed_force_without_derivation_preserves_extra_bytes(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    extras = {
        "extra.bin": bytes([0x00, 0xFF, 0xFE]) + b"FORCE\r\n",
        "notes.txt": b"\xef\xbb\xbfextra\r\ntext\n",
    }
    for name, body in extras.items():
        (directory / name).write_bytes(body)
    lecture_before = (directory / "03_full_summary.md").read_bytes()
    payload = _valid_payload()
    payload["03_full_summary"] += "\nforce-overlay-sentinel\n"
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(payload, captured),
    )

    result = run_study_guide_bundle(
        PODCAST,
        EPISODE,
        confirm=True,
        force=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert result.reused is False
    assert set(result.output_paths) == {"00", "03", "04", "07"}
    assert captured
    assert (directory / "03_full_summary.md").read_bytes() != lecture_before
    for name, body in extras.items():
        assert (directory / name).read_bytes() == body


_SOURCE_SENTINEL = "SOURCE-BODY-SENTINEL"


def _manifest(root: Path) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
        relative = str(path.relative_to(root)).replace("\\", "/")
        try:
            info = path.lstat()
        except OSError:
            rows.append((relative, "unstatable"))
            continue
        if stat.S_ISLNK(info.st_mode):
            rows.append((relative, "link:" + os.readlink(path)))
        elif stat.S_ISDIR(info.st_mode):
            rows.append((relative, "dir"))
        elif stat.S_ISREG(info.st_mode):
            rows.append((relative, path.read_bytes()))
        else:
            rows.append((relative, f"mode:{info.st_mode}"))
    return rows


def _symlink(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc.__class__.__name__}")


def _refuse(
    tmp_data_dirs: Path,
    monkeypatch,
    podcast: str,
    episode: str,
    *,
    reason: str,
    confirm: bool = False,
    force: bool = False,
    ack: str = "",
) -> None:
    from corpus_ingest_core import study_guide_bundle as bundle

    called = {"provider": 0, "write": 0}

    def provider(*args, **kwargs):
        called["provider"] += 1
        raise AssertionError("provider")

    def write(*args, **kwargs):
        called["write"] += 1
        raise AssertionError("writer")

    monkeypatch.setattr(bundle, "create_provider", provider)
    monkeypatch.setattr(bundle, "_atomic_write_bundle", write)
    before = _manifest(tmp_data_dirs)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            podcast,
            episode,
            confirm=confirm,
            force=force,
            api_cost_ack=ack,
        )
    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert getattr(caught.value, "reason_code", None) == reason
    assert _SOURCE_SENTINEL not in str(caught.value)
    assert called == {"provider": 0, "write": 0}
    assert _manifest(tmp_data_dirs) == before


@pytest.mark.parametrize("episode", ["", "latest", "NEXT", "a/b", "a\\b", "..", "has space"])
@pytest.mark.parametrize("confirm", [False, True])
def test_explicit_identity_rejects_invalid_and_reserved(tmp_data_dirs, monkeypatch, episode, confirm):
    _ready_episode(tmp_data_dirs)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        episode,
        reason="invalid_identity",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


def test_invalid_podcast_slug_is_rejected(tmp_data_dirs, monkeypatch):
    _ready_episode(tmp_data_dirs)
    _refuse(tmp_data_dirs, monkeypatch, "Bad_Slug", EPISODE, reason="invalid_identity")


def test_underscore_episode_identity_is_accepted(tmp_data_dirs, monkeypatch):
    episode = "ab_cd"
    _ready_episode(tmp_data_dirs, episode_ref=episode, title="Underscore Talk")
    _forbid_provider(monkeypatch)
    result = run_study_guide_bundle(PODCAST, episode)
    assert result.confirm is False
    assert result.episode_ref == episode


@pytest.mark.parametrize("confirm", [False, True])
def test_canonical_identity_mismatch_is_rejected(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    path = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE).json_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["episode_ref"] = "other-episode"
    payload["segments"][0]["text"] = _SOURCE_SENTINEL
    path.write_text(json.dumps(payload), encoding="utf-8")
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="invalid_identity",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_canonical_identity_ambiguity_is_rejected(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    original = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE).json_path
    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["title"] = "Beta Talk"
    payload["segments"][0]["text"] = _SOURCE_SENTINEL
    other = storage.transcript_asset_paths(PODCAST, EPISODE, "Beta Talk")
    _write_json(other.json_path, payload)
    storage.corpus_episode_seed_asset_path(PODCAST, EPISODE).unlink()
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="invalid_identity",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_symlinked_source_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    summary = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE)
    outside = tmp_data_dirs / "outside-source.md"
    outside.write_bytes(summary.read_bytes() + f"\n{_SOURCE_SENTINEL}\n".encode())
    summary.unlink()
    _symlink(summary, outside)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_summary_ancestor_symlink_is_refused(tmp_data_dirs, monkeypatch, confirm):
    import shutil

    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    source_dir = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).parent
    moved = tmp_data_dirs / "outside-summary-dir"
    shutil.move(str(source_dir), str(moved))
    _symlink(source_dir, moved, directory=True)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_bundle_ancestor_symlink_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    outside = tmp_data_dirs / "outside-guides"
    outside.mkdir()
    sentinel = outside / "keep.bin"
    sentinel.write_bytes(_SOURCE_SENTINEL.encode())
    podcast_dir = storage.STUDY_GUIDES_DIR / PODCAST
    podcast_dir.parent.mkdir(parents=True, exist_ok=True)
    _symlink(podcast_dir, outside, directory=True)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )
    assert sentinel.read_bytes() == _SOURCE_SENTINEL.encode()


@pytest.mark.parametrize("confirm", [False, True])
def test_bundle_child_directory_is_refused_on_reuse(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    nested = directory / "nested"
    nested.mkdir()
    (nested / "keep.bin").write_bytes(_SOURCE_SENTINEL.encode())
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_dangling_bundle_link_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    _symlink(directory / "linked.md", directory / "missing-target")
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_bundle_special_file_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _generated_bundle(tmp_data_dirs, monkeypatch)
    extra = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir / "extra.bin"
    extra.write_bytes(b"SPECIAL")
    real_lstat = Path.lstat

    def lstat(self):
        info = real_lstat(self)
        if self == extra:
            values = list(info)
            values[0] = stat.S_IFCHR
            return os.stat_result(tuple(values))
        return info

    monkeypatch.setattr(Path, "lstat", lstat)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_mocked_windows_reparse_bundle_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir
    target_inode = directory.lstat().st_ino
    original = getattr(bundle, "_is_reparse", lambda value: False)
    monkeypatch.setattr(
        bundle,
        "_is_reparse",
        lambda value: getattr(value, "st_ino", None) == target_inode or original(value),
        raising=False,
    )
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_symlinked_seed_is_refused(tmp_data_dirs, monkeypatch, confirm):
    from corpus_ingest_core import storage

    _ready_episode(tmp_data_dirs)
    seed = storage.corpus_episode_seed_asset_path(PODCAST, EPISODE)
    outside = tmp_data_dirs / "outside-seed.json"
    outside.write_bytes(seed.read_bytes() + _SOURCE_SENTINEL.encode())
    seed.unlink()
    _symlink(seed, outside)
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="unsafe_path",
        confirm=confirm,
        ack=SEMANTIC_API_COST_ACK,
    )


_DERIVATION_CASES = (
    ("05_prompt_examples.md",),
    ("06_apply_to_my_workflow.md",),
    ("05_prompt_examples.md", "06_apply_to_my_workflow.md"),
)
_RECOVERY_SUFFIXES = (".part", ".old", ".wfderive.part", ".wfderive.old")


def _bundle_directory():
    from corpus_ingest_core import storage

    return storage.study_guide_bundle_paths(PODCAST, EPISODE, TITLE).bundle_dir


@pytest.mark.parametrize("names", _DERIVATION_CASES)
@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("confirm", [False, True])
def test_derivation_blocks_lecture_generation(tmp_data_dirs, monkeypatch, names, force, confirm):
    _ready_episode(tmp_data_dirs)
    directory = _bundle_directory()
    directory.mkdir(parents=True)
    for name in names:
        (directory / name).write_bytes(b"keep-" + name.encode())
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="derivation_conflict",
        confirm=confirm,
        force=force,
        ack=SEMANTIC_API_COST_ACK,
    )


@pytest.mark.parametrize("confirm", [False, True])
def test_force_does_not_override_existing_derivation(tmp_data_dirs, monkeypatch, confirm):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "05_prompt_examples.md").write_bytes(b"\xef\xbb\xbf05\r\n")
    (directory / "06_apply_to_my_workflow.md").write_bytes(b"06\r\n")
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="derivation_conflict",
        confirm=confirm,
        force=True,
        ack=SEMANTIC_API_COST_ACK,
    )


def test_reuse_keeps_derivation_bytes(tmp_data_dirs, monkeypatch):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    extras = {
        "05_prompt_examples.md": b"\xef\xbb\xbf05\r\n",
        "06_apply_to_my_workflow.md": b"06\r\n",
    }
    for name, body in extras.items():
        (directory / name).write_bytes(body)
    before = _non_cover_bytes(directory)
    cover = (directory / COVER_FILENAME).read_bytes()
    _forbid_provider(monkeypatch)

    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")

    assert result.reused is True
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).read_bytes() == cover


def test_cover_only_keeps_derivation_bytes(tmp_data_dirs, monkeypatch):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    extras = {
        "05_prompt_examples.md": b"\xef\xbb\xbf05\r\n",
        "06_apply_to_my_workflow.md": b"06\r\n",
        "03_full_summary.md": b"\xef\xbb\xbfkept\n",
        "04_learning_notes.md": b"notes\r\n",
        "07_final_study_guide.md": b"\xef\xbb\xbfguide\r\n",
    }
    for name, body in extras.items():
        (directory / name).write_bytes(body)
    (directory / COVER_FILENAME).unlink()
    before = _non_cover_bytes(directory)
    _forbid_provider(monkeypatch)

    result = run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")

    assert result.reused is False
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).is_file()


@pytest.mark.parametrize("suffix", _RECOVERY_SUFFIXES)
@pytest.mark.parametrize("mode", ["reuse", "generate"])
@pytest.mark.parametrize("confirm", [False, True])
def test_recovery_remnant_refuses_every_mode(tmp_data_dirs, monkeypatch, suffix, mode, confirm):
    if mode == "reuse":
        _generated_bundle(tmp_data_dirs, monkeypatch)
    else:
        _ready_episode(tmp_data_dirs)
    directory = _bundle_directory()
    remnant = directory.with_name(directory.name + suffix)
    remnant.parent.mkdir(parents=True, exist_ok=True)
    remnant.mkdir()
    (remnant / "keep.bin").write_bytes(b"REMNANT-SENTINEL")
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="recovery_required",
        confirm=confirm,
        force=mode == "generate",
        ack=SEMANTIC_API_COST_ACK,
    )
    assert (remnant / "keep.bin").read_bytes() == b"REMNANT-SENTINEL"


@pytest.mark.parametrize("confirm", [False, True])
def test_old_remnant_with_derivation_is_not_recovered(tmp_data_dirs, monkeypatch, confirm):
    _ready_episode(tmp_data_dirs)
    directory = _bundle_directory()
    directory.mkdir(parents=True)
    (directory / "05_prompt_examples.md").write_bytes(b"live-05")
    remnant = directory.with_name(directory.name + ".old")
    remnant.mkdir()
    (remnant / "06_apply_to_my_workflow.md").write_bytes(b"old-06")
    _refuse(
        tmp_data_dirs,
        monkeypatch,
        PODCAST,
        EPISODE,
        reason="recovery_required",
        confirm=confirm,
        force=True,
        ack=SEMANTIC_API_COST_ACK,
    )
    assert (remnant / "06_apply_to_my_workflow.md").read_bytes() == b"old-06"
    assert (directory / "05_prompt_examples.md").read_bytes() == b"live-05"


def _state_reason(caught: pytest.ExceptionInfo) -> str:
    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert "boom" not in str(caught.value)
    return caught.value.reason_code


def test_staging_copy_failure_keeps_public_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"EXTRA")
    before = _non_cover_bytes(directory)
    cover = (directory / COVER_FILENAME).read_bytes()
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), []))

    def boom(source, target):
        raise OSError("boom-copy")

    monkeypatch.setattr(bundle, "_stream_copy", boom)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "publish_failed"
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).read_bytes() == cover
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


def test_staging_write_failure_keeps_public_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _non_cover_bytes(directory)
    cover = (directory / COVER_FILENAME).read_bytes()
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), []))
    real_write = Path.write_text

    def write_text(self, data, *args, **kwargs):
        if self.parent.name.endswith(".part"):
            raise OSError("boom-write")
        return real_write(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", write_text)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "publish_failed"
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).read_bytes() == cover


def test_destination_rename_failure_keeps_public_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _non_cover_bytes(directory)
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), []))
    real_rename = Path.rename

    def rename(self, target):
        if Path(self) == directory and Path(target).name.endswith(".old"):
            raise OSError("boom-dest-rename")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "publish_failed"
    assert directory.is_dir()
    assert _non_cover_bytes(directory) == before


def test_publication_rename_failure_restores_public_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _non_cover_bytes(directory)
    cover = (directory / COVER_FILENAME).read_bytes()
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), []))
    real_rename = Path.rename

    def rename(self, target):
        if self.name.endswith(".part") and Path(target) == directory:
            raise OSError("boom-publish-rename")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "publish_failed"
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).read_bytes() == cover
    assert not directory.with_name(directory.name + ".old").exists()
    assert not directory.with_name(directory.name + ".part").exists()


def test_rollback_failure_retains_old_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _non_cover_bytes(directory)
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(_valid_payload(), []))
    real_rename = Path.rename

    def rename(self, target):
        target_path = Path(target)
        if self.name.endswith(".part") and target_path == directory:
            raise OSError("boom-publish-rename")
        if self.name.endswith(".old") and target_path == directory:
            raise OSError("boom-rollback")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "rollback_failed"
    old = directory.with_name(directory.name + ".old")
    assert old.is_dir()
    assert _non_cover_bytes(old) == before
    assert directory.with_name(directory.name + ".part").exists()
    assert not directory.exists()


def test_cleanup_failure_keeps_published_bundle(tmp_data_dirs, monkeypatch):
    import shutil

    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    payload = _valid_payload()
    payload["03_full_summary"] += "\ncleanup-sentinel\n"
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(payload, []))
    real_rmtree = shutil.rmtree

    def rmtree(path, *args, **kwargs):
        if Path(path).name.endswith(".old"):
            raise OSError("boom-cleanup")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(bundle.shutil, "rmtree", rmtree)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "published_cleanup_failed"
    assert b"cleanup-sentinel" in (directory / "03_full_summary.md").read_bytes()
    assert directory.with_name(directory.name + ".old").exists()


def test_published_report_failure_keeps_new_bundle(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    payload = _valid_payload()
    payload["03_full_summary"] += "\nreport-sentinel\n"
    monkeypatch.setattr(bundle, "create_provider", lambda *args, **kwargs: _FakeProvider(payload, []))

    def boom(*args, **kwargs):
        raise OSError("boom-report")

    monkeypatch.setattr(bundle, "write_part_staged_report_pair", boom)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, force=True, api_cost_ack=SEMANTIC_API_COST_ACK)
    assert _state_reason(caught) == "published_report_failed"
    assert b"report-sentinel" in (directory / "03_full_summary.md").read_bytes()
    assert not directory.with_name(directory.name + ".old").exists()


def test_reused_report_failure_keeps_bundle_bytes(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _non_cover_bytes(directory)
    cover = (directory / COVER_FILENAME).read_bytes()
    _forbid_provider(monkeypatch)

    def boom(*args, **kwargs):
        raise OSError("boom-report")

    monkeypatch.setattr(bundle, "write_part_staged_report_pair", boom)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    assert _state_reason(caught) == "reused_report_failed"
    assert _non_cover_bytes(directory) == before
    assert (directory / COVER_FILENAME).read_bytes() == cover


def _plan_result(bundle_dir: Path, writes: list[str]):
    from corpus_ingest_core.models import StudyGuideBundleResult

    return StudyGuideBundleResult(
        podcast_id=PODCAST,
        episode_ref=EPISODE,
        confirm=False,
        run_mode="dry-run",
        source_summary_path="source",
        bundle_dir=str(bundle_dir),
        planned_reads=[],
        planned_writes=writes,
        planned_reuses=[],
        output_paths={},
        report_json_path=None,
        report_markdown_path=None,
        reused=False,
        warnings=[],
        not_investment_advice=True,
    )


def test_describe_study_guide_plan_discriminates_full_paths_without_io(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    describe = getattr(bundle, "describe_study_guide_plan", None)
    assert callable(describe)
    bundle_dir = storage.STUDY_GUIDES_DIR / PODCAST / "stem"
    other = storage.STUDY_GUIDES_DIR / "other" / "stem"
    reports = storage.study_guide_run_asset_paths(PODCAST, EPISODE)
    reads = {"count": 0}
    real_read = Path.read_bytes

    def read_bytes(self):
        reads["count"] += 1
        return real_read(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(
        bundle,
        "load_podcast_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("profile")),
    )
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("provider")),
    )

    generation = describe(
        _plan_result(
            bundle_dir,
            [
                str(bundle_dir / name)
                for name in (
                    "00_video_info.md",
                    "03_full_summary.md",
                    "04_learning_notes.md",
                    "07_final_study_guide.md",
                )
            ],
        )
    )
    cover = describe(_plan_result(bundle_dir, [str(bundle_dir / "00_video_info.md")]))
    reuse = describe(_plan_result(bundle_dir, []))
    foreign = describe(_plan_result(bundle_dir, [str(other / "03_full_summary.md")]))

    assert generation["requires_llm"] is True
    assert cover["requires_llm"] is False
    assert reuse["requires_llm"] is False
    assert foreign["requires_llm"] is False
    assert generation["report_writes"] == [str(reports.json_path), str(reports.markdown_path)]
    assert reads["count"] == 0


def test_preview_plan_keeps_report_fields_empty_and_names_identity(tmp_data_dirs):
    from corpus_ingest_core import storage
    from corpus_ingest_core import study_guide_bundle as bundle

    _ready_episode(tmp_data_dirs)
    preview = run_study_guide_bundle(PODCAST, EPISODE)
    describe = bundle.describe_study_guide_plan
    projected = describe(preview)
    identity = storage.transcript_asset_paths(PODCAST, EPISODE, TITLE).json_path

    assert preview.report_json_path is None
    assert preview.report_markdown_path is None
    assert projected["requires_llm"] is True
    assert len(projected["report_writes"]) == 2
    assert str(identity) in preview.planned_reads


def _directory_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}


def test_extra_metadata_failure_aborts_publish_and_keeps_directory(tmp_data_dirs, monkeypatch):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"EXTRA-BYTES")
    (directory / COVER_FILENAME).unlink()
    before = _directory_bytes(directory)
    real_lstat = Path.lstat
    extra_stats = {"count": 0}

    def lstat(self):
        if self.name == "extra.bin":
            extra_stats["count"] += 1
            if extra_stats["count"] >= 2:
                raise PermissionError("boom-extra-meta")
        return real_lstat(self)

    monkeypatch.setattr(Path, "lstat", lstat)
    _forbid_provider(monkeypatch)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")
    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-extra-meta" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


@pytest.mark.parametrize("confirm", [False, True])
def test_cover_io_error_refuses_instead_of_cover_only(tmp_data_dirs, monkeypatch, confirm):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    before = _directory_bytes(directory)
    real_read = Path.read_bytes

    def read_bytes(self):
        if self.name == COVER_FILENAME:
            raise PermissionError("boom-cover-read")
        return real_read(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    _forbid_provider(monkeypatch)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=confirm,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )
    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-cover-read" not in str(caught.value)
    assert {path.name: real_read(path) for path in directory.iterdir() if path.is_file()} == before


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _report_snapshot() -> dict[str, bytes | None]:
    from corpus_ingest_core import storage

    reports = storage.study_guide_run_asset_paths(PODCAST, EPISODE)
    return {
        path.name: path.read_bytes() if path.is_file() else None
        for path in (reports.json_path, reports.markdown_path)
    }


def _arm_publisher_dest_lstat(monkeypatch, directory: Path, marker: str) -> None:
    """Fail the first destination lstat after publication begins, once."""

    from corpus_ingest_core import study_guide_bundle as bundle

    real_write = bundle._atomic_write_bundle
    real_lstat = Path.lstat
    armed = {"on": False, "fired": False}

    def atomic(paths, files, **kwargs):
        armed["on"] = True
        try:
            return real_write(paths, files, **kwargs)
        finally:
            armed["on"] = False

    def lstat(self):
        if armed["on"] and _same_path(self, directory) and not armed["fired"]:
            armed["fired"] = True
            raise PermissionError(marker)
        return real_lstat(self)

    monkeypatch.setattr(bundle, "_atomic_write_bundle", atomic)
    monkeypatch.setattr(Path, "lstat", lstat)


def _cover_only_directory(tmp_data_dirs, monkeypatch) -> tuple[Path, dict[str, bytes]]:
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"EXTRA-BYTES")
    (directory / "03_full_summary.md").write_bytes(b"\xef\xbb\xbfkept-03\r\n")
    (directory / "04_learning_notes.md").write_bytes(b"kept-04\r\n")
    (directory / "07_final_study_guide.md").write_bytes(b"\xef\xbb\xbfkept-07\r\n")
    (directory / COVER_FILENAME).unlink()
    return directory, _directory_bytes(directory)


def test_dir_meta_cover_only_dest_failure_keeps_bytes(tmp_data_dirs, monkeypatch):
    directory, before = _cover_only_directory(tmp_data_dirs, monkeypatch)
    reports = _report_snapshot()
    _arm_publisher_dest_lstat(monkeypatch, directory, "boom-dest-dir")
    _forbid_provider(monkeypatch)

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-dest-dir" not in str(caught.value)
    assert caught.value.reason_code != "publish_failed"
    assert _directory_bytes(directory) == before
    assert set(_directory_bytes(directory)) == set(before)
    assert _report_snapshot() == reports
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


def test_dir_meta_force_dest_failure_keeps_bytes(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(bytes([0x00, 0xFF, 0xFE]) + b"FORCE\r\n")
    before = _directory_bytes(directory)
    reports = _report_snapshot()
    captured: list = []
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )
    _arm_publisher_dest_lstat(monkeypatch, directory, "boom-force-dest")

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=True,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-force-dest" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert len(captured) == 1
    assert _report_snapshot() == reports
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


@pytest.mark.parametrize("suffix", _RECOVERY_SUFFIXES)
@pytest.mark.parametrize("confirm", [False, True])
def test_dir_meta_recovery_sibling_unreadable_refuses(tmp_data_dirs, monkeypatch, suffix, confirm):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"RECOVERY-EXTRA")
    before = _directory_bytes(directory)
    reports = _report_snapshot()
    sibling = directory.with_name(directory.name + suffix)
    real_lstat = Path.lstat

    def lstat(self):
        if _same_path(self, sibling):
            raise PermissionError("boom-recovery-meta")
        return real_lstat(self)

    monkeypatch.setattr(Path, "lstat", lstat)
    _forbid_provider(monkeypatch)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=confirm,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-recovery-meta" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert _report_snapshot() == reports
    assert not sibling.exists()
    for other in _RECOVERY_SUFFIXES:
        assert not directory.with_name(directory.name + other).exists()


@pytest.mark.parametrize("name", ["05_prompt_examples.md", "06_apply_to_my_workflow.md"])
def test_dir_meta_derivation_unreadable_refuses(tmp_data_dirs, monkeypatch, name):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / name).write_bytes(b"keep-" + name.encode())
    before = _directory_bytes(directory)
    reports = _report_snapshot()
    real_has = bundle._has_derivation
    real_lstat = Path.lstat
    armed = {"on": False}
    captured: list = []

    def has_derivation(bundle_dir):
        armed["on"] = True
        try:
            return real_has(bundle_dir)
        finally:
            armed["on"] = False

    def lstat(self):
        if armed["on"] and self.name == name:
            raise PermissionError("boom-derivation-meta")
        return real_lstat(self)

    monkeypatch.setattr(bundle, "_has_derivation", has_derivation)
    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), captured),
    )

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=True,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-derivation-meta" not in str(caught.value)
    assert captured == []
    assert _directory_bytes(directory) == before
    assert _report_snapshot() == reports


@pytest.mark.parametrize("confirm", [False, True])
def test_dir_meta_ancestor_unreadable_refuses(tmp_data_dirs, monkeypatch, confirm):
    directory, before = _cover_only_directory(tmp_data_dirs, monkeypatch)
    reports = _report_snapshot()
    parent = directory.parent
    real_lstat = Path.lstat

    def lstat(self):
        if _same_path(self, parent):
            raise PermissionError("boom-ancestor-meta")
        return real_lstat(self)

    monkeypatch.setattr(Path, "lstat", lstat)
    _forbid_provider(monkeypatch)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=confirm,
            api_cost_ack="",
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-ancestor-meta" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert _report_snapshot() == reports
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


def test_dir_meta_listed_entry_missing_aborts(tmp_data_dirs, monkeypatch):
    directory, before = _cover_only_directory(tmp_data_dirs, monkeypatch)
    reports = _report_snapshot()
    from corpus_ingest_core import study_guide_bundle as bundle

    real_write = bundle._atomic_write_bundle
    real_lstat = Path.lstat
    armed = {"on": False, "fired": False}

    def atomic(paths, files, **kwargs):
        armed["on"] = True
        try:
            return real_write(paths, files, **kwargs)
        finally:
            armed["on"] = False

    def lstat(self):
        if armed["on"] and self.name == "extra.bin" and not armed["fired"]:
            armed["fired"] = True
            raise FileNotFoundError("boom-listed-missing")
        return real_lstat(self)

    monkeypatch.setattr(bundle, "_atomic_write_bundle", atomic)
    monkeypatch.setattr(Path, "lstat", lstat)
    _forbid_provider(monkeypatch)
    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(PODCAST, EPISODE, confirm=True, api_cost_ack="")

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "unsafe_path"
    assert "boom-listed-missing" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert _report_snapshot() == reports
    assert not directory.with_name(directory.name + ".part").exists()
    assert not directory.with_name(directory.name + ".old").exists()


def _arm_publish_rename_failure(monkeypatch, directory: Path, *, rollback_error: bool):
    from corpus_ingest_core import study_guide_bundle as bundle

    real_rename = Path.rename
    real_lstat = Path.lstat
    part = directory.with_name(directory.name + ".part")
    old = directory.with_name(directory.name + ".old")
    stage = {"moved": False, "rollback": False}

    def rename(self, target):
        target_path = Path(target)
        if _same_path(self, directory) and _same_path(target_path, old):
            result = real_rename(self, target)
            stage["moved"] = True
            return result
        if _same_path(self, part) and _same_path(target_path, directory):
            raise OSError("boom-publish-rename")
        if _same_path(self, old) and _same_path(target_path, directory):
            stage["rollback"] = True
            if rollback_error:
                raise OSError("boom-rollback")
            return real_rename(self, target)
        return real_rename(self, target)

    def lstat(self):
        if stage["moved"] and not stage["rollback"] and (
            _same_path(self, directory) or _same_path(self, old)
        ):
            raise PermissionError("boom-phase-status")
        return real_lstat(self)

    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(
        bundle,
        "create_provider",
        lambda *args, **kwargs: _FakeProvider(_valid_payload(), []),
    )


def test_dir_meta_precommit_rollback_restores(tmp_data_dirs, monkeypatch):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"ROLLBACK-EXTRA")
    before = _directory_bytes(directory)
    reports = _report_snapshot()
    _arm_publish_rename_failure(monkeypatch, directory, rollback_error=False)

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=True,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "publish_failed"
    assert "boom-phase-status" not in str(caught.value)
    assert "boom-publish-rename" not in str(caught.value)
    assert _directory_bytes(directory) == before
    assert _report_snapshot() == reports
    assert not directory.with_name(directory.name + ".old").exists()
    assert not directory.with_name(directory.name + ".part").exists()


def test_dir_meta_precommit_rollback_unavailable_keeps_recovery(tmp_data_dirs, monkeypatch):
    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"ROLLBACK-EXTRA")
    before = _directory_bytes(directory)
    _arm_publish_rename_failure(monkeypatch, directory, rollback_error=True)
    old = directory.with_name(directory.name + ".old")
    part = directory.with_name(directory.name + ".part")

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=True,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "rollback_failed"
    assert "boom-rollback" not in str(caught.value)
    assert "boom-phase-status" not in str(caught.value)
    assert "unchanged or restored" not in str(caught.value)
    assert not directory.exists()
    assert _directory_bytes(old) == before
    assert part.is_dir()


def test_dir_meta_post_commit_backup_unreadable_keeps_published(tmp_data_dirs, monkeypatch):
    from corpus_ingest_core import study_guide_bundle as bundle

    _generated_bundle(tmp_data_dirs, monkeypatch)
    directory = _bundle_directory()
    (directory / "extra.bin").write_bytes(b"CLEANUP-EXTRA")
    before = _directory_bytes(directory)
    reports = _report_snapshot()
    payload = _valid_payload()
    payload["03_full_summary"] += "\ncleanup-status-sentinel\n"
    calls = {"count": 0}

    def provider(*args, **kwargs):
        calls["count"] += 1
        return _FakeProvider(payload, [])

    monkeypatch.setattr(bundle, "create_provider", provider)
    real_rename = Path.rename
    real_lstat = Path.lstat
    part = directory.with_name(directory.name + ".part")
    old = directory.with_name(directory.name + ".old")
    stage = {"committed": False}

    def rename(self, target):
        result = real_rename(self, target)
        if _same_path(self, part) and _same_path(Path(target), directory):
            stage["committed"] = True
        return result

    def lstat(self):
        if stage["committed"] and _same_path(self, old):
            raise PermissionError("boom-old-status")
        return real_lstat(self)

    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.setattr(Path, "lstat", lstat)

    with pytest.raises(StudyGuideBundleError) as caught:
        run_study_guide_bundle(
            PODCAST,
            EPISODE,
            confirm=True,
            force=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
        )

    published = _directory_bytes(directory)
    assert type(caught.value).__name__ == "StudyGuideBundleStateError"
    assert caught.value.reason_code == "published_cleanup_failed"
    assert "boom-old-status" not in str(caught.value)
    assert "unchanged or restored" not in str(caught.value)
    assert calls["count"] == 1
    assert b"cleanup-status-sentinel" in published["03_full_summary.md"]
    assert published["extra.bin"] == before["extra.bin"]
    assert set(published) == set(before)
    assert _directory_bytes(old) == before
    assert _report_snapshot() == reports
