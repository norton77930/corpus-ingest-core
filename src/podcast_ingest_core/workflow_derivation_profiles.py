"""Workflow-derivation prompt data.

Pure data. No IO, no provider, no environment.
"""

from __future__ import annotations

from dataclasses import dataclass


PROMPT_EXAMPLES_KEY = "05_prompt_examples"
APPLY_KEY = "06_apply_to_my_workflow"
BUNDLE_KEYS = (PROMPT_EXAMPLES_KEY, APPLY_KEY)

PROMPT_EXAMPLES_FILENAME = "05_prompt_examples.md"
APPLY_FILENAME = "06_apply_to_my_workflow.md"

PROMPT_EXAMPLES_HEADINGS = (
    "壞 prompt vs 好 prompt",
    "不確定事項",
)
APPLY_HEADINGS = (
    "如何套用到我的工作流",
    "不確定事項",
)

SYSTEM_MESSAGE = (
    "你是工作流編輯。只根據使用者提供的講義與運算元工具清單，"
    "寫出兩份衍生文件。不得閱讀或要求逐字稿，"
    "不得把講者沒說過的工具說成講者指示，"
    "不得建議清單以外的工具，不得產生投資建議。"
)

USER_INSTRUCTIONS = (
    "把下面的講義改寫成兩個 Markdown 文件。"
    "只輸出一個 JSON 物件，鍵必須恰好是 "
    "05_prompt_examples、06_apply_to_my_workflow。"
    "05 必須含壞 prompt vs 好 prompt 對照，以及至少一個可複用模板；"
    "講義沒有的日常 prompt 目錄必須標成 reconstructed 或 不確定事項。"
    "06 只能把講義觀念對應到運算元 context 列出的工具；"
    "那是運算元應用，不是講者點名，除非講義已出現該工具名。"
    "禁止建議 context 沒有的工具。"
    "禁止買進、賣出、持有、目標價、保證報酬。"
    "禁止輸出 JSON 以外的說明。"
)


@dataclass(frozen=True)
class WorkflowDerivationProfile:
    bundle_keys: tuple[str, ...]
    system_message: str
    user_instructions: str
    prompt_headings: tuple[str, ...]
    apply_headings: tuple[str, ...]


WORKFLOW_DERIVATION_PROFILE = WorkflowDerivationProfile(
    bundle_keys=BUNDLE_KEYS,
    system_message=SYSTEM_MESSAGE,
    user_instructions=USER_INSTRUCTIONS,
    prompt_headings=PROMPT_EXAMPLES_HEADINGS,
    apply_headings=APPLY_HEADINGS,
)
