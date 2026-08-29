"""摘要模板（summary profile）註冊表。

這個模組是純資料。它決定「要請 LLM 產生什麼」，不決定「摘要 Markdown 長什麼
樣子」——後者是下游契約（`semantic_review_artifact`、`stock_lens_synthesis`、
`verified_research_lineage` 都在讀），對每個 profile 都一樣。

刻意不 import 任何 IO、網路或環境變數：註冊表因此可以在沒有 provider、沒有
stub、也沒有 api_cost_ack 的情況下被測試。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .errors import UnknownSummaryProfileError

FINANCE = "finance"
LEARNING_NOTES = "learning-notes"
DEFAULT_SUMMARY_PROFILE = FINANCE

# 「設定檔沒有這個 key」的哨兵，刻意與 YAML 的 null 區分開：
# 前者是「沒設定」，後者是操作者寫了 key 卻留空。
UNSET = object()


@dataclass(frozen=True)
class SummaryProfile:
    """一種摘要形狀的完整 prompt 與限制文字。"""

    name: str
    chunk_system: str
    chunk_sections: str
    chunk_constraints: str
    final_system: str
    final_sections: str
    final_constraints: str
    limitation_lines: tuple[str, ...]
    extractive_prompt_lines: tuple[str, ...]


# Spec 037 之前唯一存在的形狀。這些字串是「搬移」而非「改寫」：
# tests/test_summary_profiles.py 用獨立寫死的 literal 比對，任何一個字元的
# 漂移都會讓 gooaye 既有摘要鏈的固定點失效。
_FINANCE = SummaryProfile(
    name=FINANCE,
    chunk_system=(
        "你是 podcast 逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，"
        "所有重點盡量附 timestamp evidence，不要產生投資建議。"
    ),
    chunk_sections=(
        "請包含：主要內容、提到的人物 / 公司 / 股票 / 產業 / 地點 / 書籍 / 電影 / 餐廳、"
        "可引用片段、不確定事項。"
    ),
    chunk_constraints="限制：不要產生投資建議；所有判斷都要能回到逐字稿 timestamp。",
    final_system=(
        "你是 podcast 語意摘要器。根據 chunk summaries 整理整集摘要，"
        "不得產生投資建議，所有市場觀點、公司、人物與事件都要盡量附 timestamp evidence。"
    ),
    final_sections=(
        "請將以下 chunk summaries 合併成整集摘要，使用 Markdown，包含本集主題、市場觀點、"
        "台股觀點、美股觀點、總經觀點、提到的公司 / 股票 / 產業、"
        "人物 / 書 / 電影 / 音樂 / 餐廳 / 地點、生活閒聊、廣告 / 業配段落、時間軸摘要、"
        "可驗證引用、不確定事項。"
    ),
    final_constraints="限制：不要產生投資建議；所有重要判斷都要盡量附 timestamp evidence。",
    limitation_lines=(
        "本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。",
        "本摘要不構成投資建議。",
    ),
    extractive_prompt_lines=(
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
    ),
)


# 教學內容的形狀。限制條款換掉的是「被防範的失效模式」而不是防範強度：
# 財經摘要會憑空生出一個建議，教學摘要會憑空生出一個講者沒說過的步驟，
# 兩者都是同一條規則——不要超出證據。
_LEARNING_NOTES = SummaryProfile(
    name=LEARNING_NOTES,
    chunk_system=(
        "你是教學影片逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，"
        "所有重點盡量附 timestamp evidence，不要補充逐字稿沒有的內容。"
    ),
    chunk_sections=(
        "請包含：主要內容、提到的觀念 / 方法 / 工具 / 名詞 / 人物 / 產品 / 書籍、"
        "可引用片段、不確定事項。"
    ),
    chunk_constraints=(
        "限制：不要補充逐字稿沒有的內容；所有判斷都要能回到逐字稿 timestamp。"
    ),
    final_system=(
        "你是教學影片語意摘要器。根據 chunk summaries 整理成一份可自學的學習筆記，"
        "所有觀念、步驟與範例都要盡量附 timestamp evidence，"
        "逐字稿沒說的一律放進不確定事項。"
    ),
    final_sections=(
        "請將以下 chunk summaries 合併成一份學習筆記，使用 Markdown，依序包含"
        "本片主題與適合誰看、核心觀念（每個觀念含「是什麼 / 為什麼重要 / 影片中怎麼說」）、"
        "可操作步驟與實際用法、常見錯誤用法 vs 正確用法、值得記住的名詞與工具、"
        "可直接複用的 prompt 或範例片段、時間軸摘要、可驗證引用、不確定事項。"
    ),
    final_constraints=(
        "限制：不要補充逐字稿沒有的內容；所有重要判斷都要盡量附 timestamp evidence；"
        "無法從逐字稿確認的一律寫進不確定事項。"
    ),
    limitation_lines=(
        "本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。",
        "本摘要僅整理影片內容，結論請回到 timestamp 驗證。",
    ),
    extractive_prompt_lines=(
        "請根據本片逐字稿整理：",
        "1. 本片主題",
        "2. 核心觀念",
        "3. 可操作步驟與實際用法",
        "4. 常見錯誤用法 vs 正確用法",
        "5. 值得記住的名詞與工具",
        "6. 可驗證時間戳引用",
        "",
        "限制：",
        "- 不要補充逐字稿沒有的內容。",
        "- 所有判斷都要能回到逐字稿。",
    ),
)


SUMMARY_PROFILES: Mapping[str, SummaryProfile] = {
    FINANCE: _FINANCE,
    LEARNING_NOTES: _LEARNING_NOTES,
}


def resolve_summary_profile(name: object = UNSET) -> SummaryProfile:
    """把設定值解析成 profile；只有 ``UNSET``（沒有這個 key）才回退到預設。

    不存在的名稱一律拋錯而不是回退到 finance。靜默回退會讓一個 typo 產出
    形狀正確、內容卻是財經摘要的文件，而那份文件會被寫進 canonical 路徑。

    YAML 的 ``summary_profile:``（null）不算「沒設定」：操作者確實寫了這個
    key，只是寫了個空的。把它和「沒寫」混為一談就是最後一條靜默路徑。
    """

    if name is UNSET:
        return SUMMARY_PROFILES[DEFAULT_SUMMARY_PROFILE]

    known = "、".join(sorted(SUMMARY_PROFILES))
    if not isinstance(name, str) or not name.strip():
        raise UnknownSummaryProfileError(
            f"summary_profile 必須是非空字串，收到 {name!r}。已知的值：{known}。"
        )

    try:
        return SUMMARY_PROFILES[name.strip()]
    except KeyError as exc:
        raise UnknownSummaryProfileError(
            f"未知的 summary_profile：{name!r}。已知的值：{known}。"
        ) from exc
