"""Spec 042: workflow derivation runner."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from corpus_ingest_core.errors import LLMProviderConfigError, WorkflowDerivationError
from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK
from corpus_ingest_core.workflow_derivation import (
    result_to_dict,
    run_workflow_derivation,
)

PODCAST = "x-raytar"
EPISODE = "2071290493581840707"
TITLE = "Alpha Talk"

LECTURE = {
    "00_video_info.md": "# cover\n- title: Alpha Talk\n",
    "03_full_summary.md": "## 影片主題\nevals [00:00:01 - 00:00:10]\n## 核心觀念\n## 影片結構\n## 一句話總結\n## 適合誰看\n## 不確定事項\n",
    "04_learning_notes.md": "## 這個觀念是什麼\nEvals\n## 為什麼重要\n## 影片中怎麼說\n[00:02:41 - 00:02:53]\n## 實際開發時怎麼用\n## 錯誤用法\n## 正確用法\n## 不確定事項\n",
    "07_final_study_guide.md": "## 背景知識\n## 核心重點\n## 白話說明\n## 常見錯誤\n## 30 秒版本總結\n## 3 分鐘版本總結\n## 不確定事項\n",
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _ready_lecture(tmp_data_dirs: Path) -> None:
    from corpus_ingest_core import storage

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
        "# learning notes\n## Metadata\n- Summary mode: semantic-llm\n\n# 學習筆記\n\n## Chunk Summaries\nsecret\n",
        encoding="utf-8",
    )
    stem = summary.name.removesuffix(".semantic.md")
    paths = storage.study_guide_bundle_paths_from_stem(PODCAST, stem)
    paths.bundle_dir.mkdir(parents=True, exist_ok=True)
    for name, body in LECTURE.items():
        (paths.bundle_dir / name).write_text(body, encoding="utf-8")


def _context(tmp_data_dirs: Path, tools: list[str]) -> Path:
    path = tmp_data_dirs / "operator_workflow.yaml"
    path.write_text(
        yaml.safe_dump({"allowed_tools": tools}, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def _tree(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file())


def _valid_payload(*, copilot: bool = False) -> dict[str, str]:
    apply_extra = "GitHub Copilot 適合補程式。" if copilot else "只用 Claude Code 與 Codex。"
    return {
        "05_prompt_examples": "\n".join(
            [
                "## 壞 prompt vs 好 prompt",
                "| 壞 | 好 |",
                "幫我修。 | 先分類 failure mode。 |",
                "## 可複用模板",
                "```text\nGoal / Context / Evaluation\n```",
                "## 不確定事項",
                "reconstructed：日常模板依口述重構，不是逐字抄錄。",
            ]
        ),
        "06_apply_to_my_workflow": "\n".join(
            [
                "## 如何套用到我的工作流",
                "這是運算元應用，不是講者點名 Claude Code。",
                apply_extra,
                "## 不確定事項",
                "講者沒有點名這些工具。",
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
        joined = json.dumps(messages, ensure_ascii=False)
        assert "transcript body must not leak" not in joined
        return json.dumps(self._payload, ensure_ascii=False)


def test_dry_run_writes_nothing_and_does_not_construct_provider(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    before = _tree(tmp_data_dirs)

    def boom(*_args, **_kwargs):
        raise AssertionError("provider must not be constructed")

    monkeypatch.setattr("corpus_ingest_core.workflow_derivation.create_provider", boom)
    result = run_workflow_derivation(PODCAST, EPISODE, workflow_context=context)

    assert result.confirm is False
    assert result.run_mode == "preview"
    assert result.prompt_examples_path is None
    assert any("05_prompt_examples.md" in path for path in result.planned_writes)
    assert any("06_apply_to_my_workflow.md" in path for path in result.planned_writes)
    assert str(context) in result.planned_reads
    assert _tree(tmp_data_dirs) == before
    payload = result_to_dict(result)
    assert payload["dry_run"] is True
    assert "transcript body" not in json.dumps(payload)


def test_finance_profile_is_refused(tmp_data_dirs):
    context = _context(tmp_data_dirs, ["Claude Code"])
    with pytest.raises(WorkflowDerivationError, match="learning-notes"):
        run_workflow_derivation("gooaye", "EP672", workflow_context=context)


def test_missing_lecture_is_refused(tmp_data_dirs):
    from corpus_ingest_core import storage

    _ready_lecture(tmp_data_dirs)
    stem = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md")
    bundle = storage.study_guide_bundle_paths_from_stem(PODCAST, stem).bundle_dir
    for name in LECTURE:
        (bundle / name).unlink()
    context = _context(tmp_data_dirs, ["Claude Code"])
    with pytest.raises(WorkflowDerivationError, match="lecture"):
        run_workflow_derivation(PODCAST, EPISODE, workflow_context=context)


def test_missing_context_is_refused(tmp_data_dirs):
    _ready_lecture(tmp_data_dirs)
    missing = tmp_data_dirs / "nope.yaml"
    with pytest.raises(WorkflowDerivationError, match="context is missing"):
        run_workflow_derivation(PODCAST, EPISODE, workflow_context=missing)


def test_confirm_writes_pair_and_omits_tools_absent_from_context(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    captured: list = []
    monkeypatch.setattr(
        "corpus_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(_valid_payload(), captured),
    )
    from corpus_ingest_core import storage

    lecture_before = {
        name: (
            storage.study_guide_bundle_paths_from_stem(
                PODCAST,
                storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md"),
            ).bundle_dir
            / name
        ).read_text(encoding="utf-8")
        for name in LECTURE
    }

    result = run_workflow_derivation(
        PODCAST,
        EPISODE,
        confirm=True,
        api_cost_ack=SEMANTIC_API_COST_ACK,
        workflow_context=context,
    )

    assert result.confirm is True
    assert Path(result.prompt_examples_path).is_file()
    assert Path(result.apply_path).is_file()
    apply_text = Path(result.apply_path).read_text(encoding="utf-8")
    assert "GitHub Copilot" not in apply_text
    assert "Claude Code" in apply_text
    assert captured
    assert "transcript body must not leak" not in json.dumps(captured, ensure_ascii=False)
    stem = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md")
    bundle = storage.study_guide_bundle_paths_from_stem(PODCAST, stem).bundle_dir
    for name, body in lecture_before.items():
        assert (bundle / name).read_text(encoding="utf-8") == body


def test_confirm_rejects_payload_that_advises_omitted_tool(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    monkeypatch.setattr(
        "corpus_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(_valid_payload(copilot=True), []),
    )
    with pytest.raises(WorkflowDerivationError, match="absent from context"):
        run_workflow_derivation(
            PODCAST,
            EPISODE,
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
            workflow_context=context,
        )


def test_artifact_ladder_does_not_include_workflow_derivation():
    from corpus_ingest_core.corpus_remediation_plan import ARTIFACT_LADDER

    assert "workflow_derivation" not in ARTIFACT_LADDER


def test_lecture_stays_available_without_derivation_files(tmp_data_dirs):
    from corpus_ingest_core import storage
    from corpus_ingest_core.corpus_index import generate_corpus_index

    _ready_lecture(tmp_data_dirs)
    result = generate_corpus_index(PODCAST)
    payload = json.loads(result.index_json_path.read_text(encoding="utf-8"))
    row = payload["episodes"][0]
    assert row["artifact_status"]["study_guide"]["status"] == "available"
    assert row["artifact_status"]["workflow_derivation"]["status"] == "missing"
    stem = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md")
    lecture = storage.study_guide_bundle_paths_from_stem(PODCAST, stem)
    assert lecture.cover_path.is_file()


def test_failed_publish_leaves_neither_derivation_file(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    from corpus_ingest_core import storage

    stem = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md")
    bundle = storage.study_guide_bundle_paths_from_stem(PODCAST, stem).bundle_dir
    lecture_before = {name: (bundle / name).read_bytes() for name in LECTURE}
    before = _tree(tmp_data_dirs)
    live_06 = bundle / "06_apply_to_my_workflow.md"

    real_copy2 = shutil.copy2

    def copy2(src, dst, *args, **kwargs):
        if Path(dst).resolve() == live_06.resolve():
            raise OSError("boom")
        return real_copy2(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", copy2)
    publishes = {"count": 0}
    real_rename = Path.rename

    def rename(self, target):
        target_path = Path(target)
        staged_06 = self / "06_apply_to_my_workflow.md"
        if (
            target_path.resolve() == bundle.resolve()
            and self.resolve() != bundle.resolve()
            and staged_06.is_file()
        ):
            publishes["count"] += 1
            if publishes["count"] == 1:
                raise OSError("boom")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    monkeypatch.setattr(
        "corpus_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(_valid_payload(), []),
    )

    with pytest.raises(WorkflowDerivationError, match="failed to write derivation pair"):
        run_workflow_derivation(
            PODCAST,
            EPISODE,
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
            workflow_context=context,
        )

    assert _tree(tmp_data_dirs) == before
    for name, body in lecture_before.items():
        assert (bundle / name).read_bytes() == body
    assert not (bundle / "05_prompt_examples.md").exists()
    assert not live_06.exists()


def _write_existing_pair(tmp_data_dirs: Path) -> None:
    from corpus_ingest_core import storage

    stem = storage.semantic_summary_asset_path(PODCAST, EPISODE, TITLE).name.removesuffix(".semantic.md")
    paths = storage.workflow_derivation_paths_from_stem(PODCAST, stem)
    payload = _valid_payload()
    paths.prompt_examples_path.write_text(payload["05_prompt_examples"], encoding="utf-8")
    paths.apply_path.write_text(payload["06_apply_to_my_workflow"], encoding="utf-8")


def test_confirm_reuse_omits_cache_warning_and_skips_provider(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    _write_existing_pair(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])

    def boom(*_args, **_kwargs):
        raise AssertionError("provider must not be constructed")

    monkeypatch.setattr("corpus_ingest_core.workflow_derivation.create_provider", boom)
    result = run_workflow_derivation(
        PODCAST,
        EPISODE,
        confirm=True,
        workflow_context=context,
    )

    assert result.reused is True
    assert result.warnings == []


def test_confirm_rejects_05_without_reusable_template(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    payload = _valid_payload()
    payload["05_prompt_examples"] = payload["05_prompt_examples"].replace("可複用模板", "其他標題")
    monkeypatch.setattr(
        "corpus_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(payload, []),
    )
    with pytest.raises(WorkflowDerivationError, match="05_prompt_examples missing heading 可複用模板"):
        run_workflow_derivation(
            PODCAST,
            EPISODE,
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
            workflow_context=context,
        )


def test_confirm_rejects_06_without_operator_application_label(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code", "Codex"])
    payload = _valid_payload()
    payload["06_apply_to_my_workflow"] = payload["06_apply_to_my_workflow"].replace("運算元應用", "套用說明")
    monkeypatch.setattr(
        "corpus_ingest_core.workflow_derivation.create_provider",
        lambda *_args, **_kwargs: _FakeProvider(payload, []),
    )
    with pytest.raises(WorkflowDerivationError, match="06_apply_to_my_workflow missing heading 運算元應用"):
        run_workflow_derivation(
            PODCAST,
            EPISODE,
            confirm=True,
            api_cost_ack=SEMANTIC_API_COST_ACK,
            workflow_context=context,
        )


def test_wrong_ack_never_constructs_provider(tmp_data_dirs, monkeypatch):
    _ready_lecture(tmp_data_dirs)
    context = _context(tmp_data_dirs, ["Claude Code"])

    def boom(*_args, **_kwargs):
        raise AssertionError("provider must not be constructed")

    monkeypatch.setattr("corpus_ingest_core.workflow_derivation.create_provider", boom)
    with pytest.raises(LLMProviderConfigError):
        run_workflow_derivation(
            PODCAST,
            EPISODE,
            confirm=True,
            api_cost_ack="nope",
            workflow_context=context,
        )
