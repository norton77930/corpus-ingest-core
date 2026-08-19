"""Spec 038: study-guide prompt and heading registry is pure data."""

from __future__ import annotations

from podcast_ingest_core.study_guide_profiles import (
    BUNDLE_KEYS,
    FINANCE_HEADINGS,
    GUIDE_HEADINGS,
    NOTES_HEADINGS,
    STUDY_GUIDE_PROFILE,
    SUMMARY_HEADINGS,
    WORKFLOW_MARKERS,
)


def test_bundle_keys_are_the_three_generated_files_only():
    assert BUNDLE_KEYS == (
        "03_full_summary",
        "04_learning_notes",
        "07_final_study_guide",
    )
    assert "01" not in "".join(BUNDLE_KEYS)
    assert "02" not in "".join(BUNDLE_KEYS)
    assert "05" not in "".join(BUNDLE_KEYS)
    assert "06" not in "".join(BUNDLE_KEYS)


def test_required_headings_match_fr_010_to_012():
    assert SUMMARY_HEADINGS == STUDY_GUIDE_PROFILE.summary_headings
    assert "影片主題" in SUMMARY_HEADINGS
    assert "一句話總結" in SUMMARY_HEADINGS
    assert "這個觀念是什麼" in NOTES_HEADINGS
    assert "影片中怎麼說" in NOTES_HEADINGS
    assert "30 秒版本總結" in GUIDE_HEADINGS
    assert "3 分鐘版本總結" in GUIDE_HEADINGS
    assert "不確定事項" in SUMMARY_HEADINGS
    assert "不確定事項" in NOTES_HEADINGS
    assert "不確定事項" in GUIDE_HEADINGS


def test_prompt_forbids_workflow_derivation_and_finance_shape():
    text = (
        STUDY_GUIDE_PROFILE.system_message
        + STUDY_GUIDE_PROFILE.user_instructions
    )
    for marker in WORKFLOW_MARKERS:
        assert marker in text
    assert "逐字稿" in text
    assert "市場觀點" in text
    for heading in FINANCE_HEADINGS:
        assert heading in FINANCE_HEADINGS
