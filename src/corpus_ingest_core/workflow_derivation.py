"""Dry-run-first 05/06 workflow derivation runner.

Reads an available Spec 038 lecture plus operator context. Never sends
transcript text to a provider. Never rewrites the lecture four.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from . import storage
from .config import load_podcast_profile
from .errors import WorkflowDerivationError
from .llm_provider import create_provider, require_exact_api_cost_ack
from .models import WorkflowDerivationResult
from .report_safety import matched_investment_advice_guard
from .run_report_io import write_part_staged_report_pair
from .semantic_summary_identity import canonical_semantic_summary_path
from .study_guide_profiles import WORKFLOW_MARKERS
from .summary_profiles import LEARNING_NOTES
from .workflow_derivation_profiles import (
    APPLY_FILENAME,
    APPLY_HEADINGS,
    APPLY_KEY,
    BUNDLE_KEYS,
    PROMPT_EXAMPLES_FILENAME,
    PROMPT_EXAMPLES_HEADINGS,
    PROMPT_EXAMPLES_KEY,
    WORKFLOW_DERIVATION_PROFILE,
)

CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. This workflow never rebuilds it automatically."
)
DEFAULT_CONTEXT_PATH = Path(__file__).resolve().parents[2] / "config" / "operator_workflow.yaml"
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_MAX_SOURCE_BYTES = 2 * 1024 * 1024
REQUIRED_PROFILE = LEARNING_NOTES


def run_workflow_derivation(
    podcast_id: str,
    episode_ref: str,
    *,
    confirm: bool = False,
    force: bool = False,
    api_cost_ack: str = "",
    workflow_context: str | Path | None = None,
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
) -> WorkflowDerivationResult:
    """Plan or write 05/06 for one learning-notes lecture."""

    profile = load_podcast_profile(podcast_id)
    if profile.summary_profile != REQUIRED_PROFILE:
        raise WorkflowDerivationError(
            f"workflow derivation requires summary_profile={REQUIRED_PROFILE}; got {profile.summary_profile!r}"
        )

    context_path = Path(workflow_context) if workflow_context else DEFAULT_CONTEXT_PATH
    allowed_tools = _load_context(context_path)

    source_path = canonical_semantic_summary_path(podcast_id, episode_ref)
    if source_path is None or not source_path.is_file():
        raise WorkflowDerivationError("canonical learning-notes semantic summary is missing")
    stem = source_path.name.removesuffix(".semantic.md")
    lecture = storage.study_guide_bundle_paths_from_stem(podcast_id, stem)
    _require_lecture(lecture)

    paths = storage.workflow_derivation_paths_from_stem(podcast_id, stem)
    existing = [path for path in (paths.prompt_examples_path, paths.apply_path) if path.is_file()]
    complete = len(existing) == 2
    if existing and not complete and not force:
        raise WorkflowDerivationError("incomplete workflow derivation pair; pass force=true to replace")
    reuse_all = complete and not force

    planned_reads = [
        str(lecture.summary_path),
        str(lecture.notes_path),
        str(lecture.guide_path),
        str(context_path),
    ]
    if reuse_all:
        planned_writes: list[str] = []
        planned_reuses = [str(paths.prompt_examples_path), str(paths.apply_path)]
    else:
        planned_writes = [str(paths.prompt_examples_path), str(paths.apply_path)]
        planned_reuses = []

    if not confirm:
        return _result(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            confirm=False,
            lecture_dir=str(paths.bundle_dir),
            context_path=str(context_path),
            planned_reads=planned_reads,
            planned_writes=planned_writes,
            planned_reuses=planned_reuses,
            prompt_examples_path=None,
            apply_path=None,
            report_json_path=None,
            report_markdown_path=None,
            reused=reuse_all,
            warnings=[CACHE_STALE_WARNING] if planned_writes else [],
        )

    if reuse_all:
        bodies = {
            PROMPT_EXAMPLES_KEY: paths.prompt_examples_path.read_text(encoding="utf-8"),
            APPLY_KEY: paths.apply_path.read_text(encoding="utf-8"),
        }
    else:
        require_exact_api_cost_ack(api_cost_ack)
        lecture_text = {
            "03": _read_capped(lecture.summary_path),
            "04": _read_capped(lecture.notes_path),
            "07": _read_capped(lecture.guide_path),
        }
        llm = create_provider(
            provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            reasoning_effort=reasoning_effort,
            read_timeout_seconds=read_timeout_seconds,
            api_cost_ack=api_cost_ack,
        )
        raw = llm.complete(_build_messages(lecture_text, allowed_tools))
        bodies = _parse_payload(raw)
        _validate_generated(bodies, allowed_tools)
        _atomic_write_pair(paths, bodies)

    report_paths = storage.workflow_derivation_run_asset_paths(podcast_id, episode_ref)
    result = _result(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=True,
        lecture_dir=str(paths.bundle_dir),
        context_path=str(context_path),
        planned_reads=planned_reads,
        planned_writes=planned_writes,
        planned_reuses=planned_reuses,
        prompt_examples_path=str(paths.prompt_examples_path),
        apply_path=str(paths.apply_path),
        report_json_path=report_paths.json_path,
        report_markdown_path=report_paths.markdown_path,
        reused=reuse_all,
        warnings=[CACHE_STALE_WARNING],
    )
    _write_run_report(result)
    return result


def result_to_dict(result: WorkflowDerivationResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["report_json_path"] = _path_or_none(result.report_json_path)
    payload["report_markdown_path"] = _path_or_none(result.report_markdown_path)
    payload["dry_run"] = not result.confirm
    return payload


def _result(**kwargs: Any) -> WorkflowDerivationResult:
    confirm = bool(kwargs["confirm"])
    return WorkflowDerivationResult(
        run_mode="confirmed" if confirm else "preview",
        not_investment_advice=True,
        **kwargs,
    )


def _load_context(path: Path) -> list[str]:
    if not path.is_file():
        raise WorkflowDerivationError(f"operator workflow context is missing: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise WorkflowDerivationError(f"operator workflow context is unreadable: {path}") from exc
    if not isinstance(raw, dict):
        raise WorkflowDerivationError("operator workflow context must be a mapping")
    tools = raw.get("allowed_tools")
    if not isinstance(tools, list) or not tools or not all(isinstance(item, str) and item.strip() for item in tools):
        raise WorkflowDerivationError("operator workflow context requires a non-empty allowed_tools list")
    return [item.strip() for item in tools]


def _require_lecture(lecture: storage.StudyGuideBundlePaths) -> None:
    files = (
        lecture.cover_path,
        lecture.summary_path,
        lecture.notes_path,
        lecture.guide_path,
    )
    existing = [path for path in files if path.is_file()]
    if len(existing) < 4:
        raise WorkflowDerivationError("study-guide lecture is missing or partial; generate Spec 038 first")
    for path in files:
        _read_capped(path)


def _read_capped(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise WorkflowDerivationError(f"unreadable: {path}") from exc
    if len(payload) > _MAX_SOURCE_BYTES:
        raise WorkflowDerivationError(f"exceeded read size cap: {path}")
    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise WorkflowDerivationError(f"not UTF-8: {path}") from exc


def _build_messages(lecture_text: dict[str, str], allowed_tools: list[str]) -> list[dict[str, str]]:
    tools = ", ".join(allowed_tools)
    user = (
        f"{WORKFLOW_DERIVATION_PROFILE.user_instructions}\n\n"
        f"allowed_tools: {tools}\n\n"
        f"## 03\n{lecture_text['03']}\n\n"
        f"## 04\n{lecture_text['04']}\n\n"
        f"## 07\n{lecture_text['07']}\n"
    )
    return [
        {"role": "system", "content": WORKFLOW_DERIVATION_PROFILE.system_message},
        {"role": "user", "content": user},
    ]


def _parse_payload(raw: str) -> dict[str, str]:
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkflowDerivationError("workflow derivation output is not JSON") from exc
    if not isinstance(parsed, dict):
        raise WorkflowDerivationError("workflow derivation output is not an object")
    if set(parsed) != set(BUNDLE_KEYS):
        raise WorkflowDerivationError("workflow derivation output keys are wrong")
    bodies: dict[str, str] = {}
    for key in BUNDLE_KEYS:
        value = parsed[key]
        if not isinstance(value, str) or not value.strip():
            raise WorkflowDerivationError(f"workflow derivation output {key} is empty")
        bodies[key] = value
    return bodies


def _validate_generated(bodies: dict[str, str], allowed_tools: list[str]) -> None:
    for key, headings in (
        (PROMPT_EXAMPLES_KEY, PROMPT_EXAMPLES_HEADINGS),
        (APPLY_KEY, APPLY_HEADINGS),
    ):
        text = bodies[key]
        for heading in headings:
            if heading not in text:
                raise WorkflowDerivationError(f"{key} missing heading {heading}")
        if matched_investment_advice_guard(text) is not None:
            raise WorkflowDerivationError(f"{key} failed prohibited_advice")
        # Inert, and deliberately left that way for now.
        #
        # This reads as a fourth validation -- every other check in this loop
        # raises WorkflowDerivationError -- but its body has been `pass` since
        # spec 042 introduced it (ced711a); it was never gutted, it was never
        # finished. What it appears to look for is a derived document that
        # mentions 逐字稿 (the transcript) *without* 不得 (the prohibition),
        # i.e. the model inverting the profile's "不得閱讀或要求逐字稿"
        # instruction into an invitation to read one. That would be an
        # instruction-inversion detector.
        #
        # Not completed here, for two reasons. The heuristic is thin -- it
        # turns on two Chinese words co-occurring, so it would fire on
        # perfectly correct documents and miss any inversion phrased
        # differently. And no spec asks for it: 042's checklist covers the
        # *input* boundary (CHK004, transcript never reaches the provider),
        # which the runner enforces by never reading one, and says nothing
        # about this output-side check.
        #
        # The condition is kept rather than deleted so the intent is not lost.
        # Completing it means writing the rule into the spec and giving it a
        # test first, not turning this into a raise and hoping.
        if "逐字稿" in text and "不得" not in text:
            pass
        forbidden_tools = []
        for marker in (*WORKFLOW_MARKERS, "spec-kit"):
            if marker in text and marker not in allowed_tools:
                forbidden_tools.append(marker)
        if forbidden_tools:
            raise WorkflowDerivationError(f"{key} advises tools absent from context: {forbidden_tools}")


def _atomic_write_pair(paths: storage.WorkflowDerivationPaths, bodies: dict[str, str]) -> None:
    dest = paths.bundle_dir
    dest.mkdir(parents=True, exist_ok=True)
    part = dest / ".derivation.part"
    old = dest / ".derivation.old"
    mapping = {
        PROMPT_EXAMPLES_FILENAME: bodies[PROMPT_EXAMPLES_KEY],
        APPLY_FILENAME: bodies[APPLY_KEY],
    }
    targets = {
        PROMPT_EXAMPLES_FILENAME: paths.prompt_examples_path,
        APPLY_FILENAME: paths.apply_path,
    }
    try:
        if part.exists():
            shutil.rmtree(part)
        if old.exists():
            shutil.rmtree(old)
        part.mkdir()
        old.mkdir()
        for name, content in mapping.items():
            (part / name).write_text(content, encoding="utf-8")
            current = targets[name]
            if current.is_file():
                shutil.copy2(current, old / name)
        for name in mapping:
            shutil.copy2(part / name, targets[name])
        shutil.rmtree(part)
        shutil.rmtree(old)
    except OSError as exc:
        if old.exists():
            for name, target in targets.items():
                backup = old / name
                if backup.is_file():
                    shutil.copy2(backup, target)
        shutil.rmtree(part, ignore_errors=True)
        shutil.rmtree(old, ignore_errors=True)
        raise WorkflowDerivationError("failed to write derivation pair") from exc


def _write_run_report(result: WorkflowDerivationResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    markdown = "\n".join(
        [
            f"# Workflow derivation run — {result.podcast_id} / {result.episode_ref}",
            "",
            f"- run_mode: {result.run_mode}",
            f"- reused: {result.reused}",
            f"- context: {result.context_path}",
            "",
        ]
    )
    try:
        write_part_staged_report_pair(
            result.report_json_path,
            result.report_markdown_path,
            result_to_dict(result),
            markdown,
        )
    except OSError as exc:
        raise WorkflowDerivationError("failed to write derivation run report") from exc


def _path_or_none(path: Path | None) -> str | None:
    return None if path is None else str(path)
