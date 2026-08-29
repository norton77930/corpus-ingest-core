"""將逐字稿 segments 併成適合閱讀的區塊。

Whisper 產出的 segment 太短，單獨閱讀沒有意義。這裡把連續 segment 併成
30-90 秒的區塊，規則移植自 spec 036 引用的 X 影片原型。

純函數，不讀寫任何檔案：區塊由 segments 現算，不會存成 artifact。
"""

from __future__ import annotations

from typing import Any


DEFAULT_MIN_DURATION_SECONDS = 30.0
DEFAULT_MAX_DURATION_SECONDS = 90.0
# 半形給英文來源，全形給中文——本 repo 的主語料是 zh，只認半形的話中文逐字稿
# 永遠不會在句尾軟切，每個區塊都會被推到 max_duration 硬上限。
_SENTENCE_ENDINGS = (".", "?", "!", "。", "？", "！")


def group_segments(
    segments: list[dict[str, Any]],
    min_duration: float = DEFAULT_MIN_DURATION_SECONDS,
    max_duration: float = DEFAULT_MAX_DURATION_SECONDS,
) -> list[dict[str, Any]]:
    """把連續 segments 併成區塊。

    於句尾且已達 ``min_duration`` 時斷開；達 ``max_duration`` 則無條件斷開，
    因此不會因為講者不停頓而長成無上限的區塊。
    """

    groups: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        groups.append(
            {
                "start": current[0]["start"],
                "end": current[-1]["end"],
                "text": " ".join(segment["text"] for segment in current).strip(),
                "segments": current,
            }
        )
        current = []

    for segment in segments:
        if not current:
            current.append(segment)
            continue
        duration = segment["end"] - current[0]["start"]
        current.append(segment)
        ends_sentence = segment["text"].strip().endswith(_SENTENCE_ENDINGS)
        if (ends_sentence and duration >= min_duration) or duration >= max_duration:
            flush()

    flush()
    return groups
