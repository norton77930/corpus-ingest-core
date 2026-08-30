"""Spec 042: derivation prompts are pure data."""

from __future__ import annotations

from corpus_ingest_core.workflow_derivation_profiles import (
    BUNDLE_KEYS,
    WORKFLOW_DERIVATION_PROFILE,
)


def test_bundle_keys_are_05_and_06_only():
    assert BUNDLE_KEYS == ("05_prompt_examples", "06_apply_to_my_workflow")


def test_prompt_forbids_transcript_and_unnamed_tools():
    text = WORKFLOW_DERIVATION_PROFILE.system_message + WORKFLOW_DERIVATION_PROFILE.user_instructions
    assert "逐字稿" in text
    assert "清單以外" in text or "context 沒有" in text
    assert "投資" in text
