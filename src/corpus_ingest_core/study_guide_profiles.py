"""Study-guide bundle prompt and heading data.

Pure data. No IO, no provider, no environment. The runner builds messages
from this module and validates headings against the same lists.
"""

from __future__ import annotations

from dataclasses import dataclass

BUNDLE_KEYS = ("03_full_summary", "04_learning_notes", "07_final_study_guide")

COVER_FILENAME = "00_video_info.md"
SUMMARY_FILENAME = "03_full_summary.md"
NOTES_FILENAME = "04_learning_notes.md"
GUIDE_FILENAME = "07_final_study_guide.md"

SUMMARY_HEADINGS = (
    "影片主題",
    "核心觀念",
    "影片結構",
    "一句話總結",
    "適合誰看",
    "不確定事項",
)
NOTES_HEADINGS = (
    "這個觀念是什麼",
    "為什麼重要",
    "影片中怎麼說",
    "實際開發時怎麼用",
    "錯誤用法",
    "正確用法",
    "不確定事項",
)
GUIDE_HEADINGS = (
    "背景知識",
    "核心重點",
    "白話說明",
    "常見錯誤",
    "30 秒版本總結",
    "3 分鐘版本總結",
    "不確定事項",
)

FINANCE_HEADINGS = (
    "市場觀點",
    "台股觀點",
    "美股觀點",
    "總經觀點",
    "業配",
)

# Operator-workflow derivation markers from prototype 05/06. A generated
# lecture file may keep these only when the source summary already has them.
WORKFLOW_MARKERS = (
    "Claude Code",
    "GitHub Copilot",
    "CLAUDE.md",
    "Codex",
    "Skill",
)

SYSTEM_MESSAGE = (
    "你是教學講義編輯。只根據使用者提供的語意摘要改寫成三份講義，"
    "不得閱讀或要求逐字稿，不得補充摘要沒有的內容，"
    "不得把摘要寫成投資研究，不得產生投資建議。"
)

USER_INSTRUCTIONS = (
    "把下面這份 learning-notes 語意摘要改寫成三個 Markdown 文件。"
    "只輸出一個 JSON 物件，鍵必須恰好是 "
    "03_full_summary、04_learning_notes、07_final_study_guide。"
    "每個值是完整 Markdown。"
    "03 必須含標題：影片主題、核心觀念、影片結構、一句話總結、適合誰看、不確定事項。"
    "04 每個觀念必須含：這個觀念是什麼、為什麼重要、影片中怎麼說、"
    "實際開發時怎麼用、錯誤用法、正確用法；文末要有不確定事項。"
    "07 必須含：背景知識、核心重點、白話說明、常見錯誤、"
    "30 秒版本總結、3 分鐘版本總結、不確定事項。"
    "講者說過的主張必須沿用摘要裡已有的 timestamp，不得新造時間。"
    "摘要沒有的內容只能寫進不確定事項。"
    "禁止撰寫如何套用到 Claude Code、Codex、GitHub Copilot、CLAUDE.md 或 Skill 的工作流建議，"
    "除非該段文字已出現在來源摘要。"
    "禁止 市場觀點、台股觀點、美股觀點、總經觀點、業配。"
    "不要輸出 JSON 以外的說明。"
)


@dataclass(frozen=True)
class StudyGuideProfile:
    """The v1 lecture-bundle shape."""

    system_message: str
    user_instructions: str
    summary_headings: tuple[str, ...]
    notes_headings: tuple[str, ...]
    guide_headings: tuple[str, ...]


STUDY_GUIDE_PROFILE = StudyGuideProfile(
    system_message=SYSTEM_MESSAGE,
    user_instructions=USER_INSTRUCTIONS,
    summary_headings=SUMMARY_HEADINGS,
    notes_headings=NOTES_HEADINGS,
    guide_headings=GUIDE_HEADINGS,
)
