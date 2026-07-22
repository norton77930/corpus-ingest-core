"""Shared bounded text safety checks for verified research artifacts."""

from __future__ import annotations

import re
from typing import Any


_API_KEY_LIKE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.IGNORECASE)
_PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----", re.IGNORECASE)
_CREDENTIAL_ASSIGNMENT_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])(?:['\"])?(?:aws_secret_access_key|aws_access_key_id|api[_-]?key|"
    r"access[_-]?token|refresh[_-]?token|id[_-]?token|auth(?:orization)?|"
    r"bearer|token|password|passwd|pwd|credential(?:s)?|client[_-]?secret|"
    r"private[_-]?key|cookie)(?:['\"])?\s*[:=]\s*(?:['\"])?\S+",
    re.IGNORECASE,
)
_BEARER_TOKEN_PATTERN = re.compile(
    r"\bbearer[ \t]+[A-Za-z0-9._~+/-]{8,}={0,2}\b", re.IGNORECASE
)
_URI_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s]*")
_URI_QUERY_OR_FRAGMENT_PATTERN = re.compile(
    r"\b[A-Za-z][A-Za-z0-9+.-]*:[^\s?#]*[?#]\S*"
)
_FORBIDDEN_TEXT_FRAGMENTS = (
    "traceback",
    "raw transcript",
    "api_key",
    "authorization",
    "private_key",
    "client_secret",
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed return",
)
_SENSITIVE_KEY_FRAGMENT_PATTERN = re.compile(
    r"(?:secret|token|password|passwd|credential|authorization|cookie|"
    r"api[_-]?key|private[_-]?key)",
    re.IGNORECASE,
)
_EN_TRADE_ACTION_LIST = r"(?:buy/sell/hold|buy\s*,\s*sell\s*,\s*(?:or\s*)?hold)"
_PERSONALIZED_INVESTMENT_ADVICE_PATTERNS = (
    # Direct commands remain advice at the start of a sentence, bullet, or line.
    (
        "trade_action",
        re.compile(
            r"(?im)(?:^|(?<=[.!?。！？:：;；]))[ \t]*(?:[-*•]\s*)?(?:buy|sell|hold)\b"
        ),
    ),
    (
        "trade_action",
        re.compile(
            r"(?m)(?:^|(?<=[.!?。！？:：;；]))[ \t]*(?:[-*•]\s*)?"
            r"(?:(?:請|立即|現在)\s*)?(?:買進|買入|賣出|賣|持有)"
        ),
    ),
    ("trade_action", re.compile(r"\byou\s+(?:should|ought\s+to|need\s+to)\s+(?:buy|sell|hold)\b", re.IGNORECASE)),
    ("trade_action", re.compile(r"\bi\s+(?:strongly\s+)?recommend\s+(?:buying|selling|holding)\b", re.IGNORECASE)),
    ("trade_action", re.compile(r"\byou\s+should\s+consider\s+(?:buying|selling|holding)\b", re.IGNORECASE)),
    ("trade_action", re.compile(r"(?im)^\s*(?:[-*]\s*)?consider\s+(?:buying|selling|holding)\b")),
    ("trade_action", re.compile(r"(?:推薦|建議|值得|應該|可考慮|考慮)\s*(?:買進|買入|買|賣出|賣|持有)")),
    ("target_price", re.compile(r"\btarget\s+price\s*(?:of|is|:)?\s*\$?\d", re.IGNORECASE)),
    ("target_price", re.compile(r"目標價\s*(?:為|是|:|：)?\s*[\d一二三四五六七八九十百千萬]")),
    ("guaranteed_return", re.compile(r"\bguaranteed\s+returns?\s*(?:of|is|:)?\s*\d?", re.IGNORECASE)),
    ("guaranteed_return", re.compile(r"保證報酬")),
)
# A transcript-derived quotation is descriptive only when a direct attribution
# in the opener's current clause introduces exactly one correctly paired quote.
# Multiple or nested quotes are ambiguous and therefore receive no exception.
_DIRECT_QUOTE_ATTRIBUTION_PATTERN = re.compile(
    r"""
    \s*
    (?:(?:the\s+)?(?:transcript|host|speaker|analyst|guest|narrator)|he|she|they)\s+
    (?:quoted|said|wrote|reported|described)
    \s*(?::|-)?\s*
    |
    \s*(?:逐字稿|主持人|來賓|講者|分析師|旁白|他|她|他們)\s*(?:引述|提到|表示|說)\s*(?:[:：-]\s*)?
    """,
    re.IGNORECASE | re.VERBOSE,
)
_QUOTE_OPEN_TO_CLOSE = {"\"": "\"", "“": "”", "「": "」"}
_QUOTE_CLOSERS = frozenset(_QUOTE_OPEN_TO_CLOSE.values())
_SAFETY_DISCLAIMER_PATTERNS = (
    re.compile(r"不構成投資建議"),
    re.compile(
        r"不提供(?:任何)?(?:買賣建議|買進、賣出(?:或|/)?持有建議|買進/賣出/持有建議)"
        r"(?:[、,，或\s]*(?:目標價|保證報酬))*"
    ),
    re.compile(r"沒有(?:目標價|保證報酬)"),
    re.compile(
        r"\b(?:no|without)\s+buy/sell/hold(?:\s+(?:advice|recommendations?))?\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:does\s+not\s+constitute|is\s+not|not)\s+(?:a\s+)?"
        rf"{_EN_TRADE_ACTION_LIST}\s+(?:recommendation|advice)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bno\s+{_EN_TRADE_ACTION_LIST}\s+"
        rf"(?:recommendation|recommendations|advice)\b(?:\s+is\s+provided)?",
        re.IGNORECASE,
    ),
    re.compile(r"\bno\s+target\s+prices?\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+(?:a\s+)?target\s+price\b", re.IGNORECASE),
    re.compile(r"\bno\s+guaranteed\s+returns?\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+guaranteed\s+returns?\b", re.IGNORECASE),
)


# Kept as a value, rather than returning source text, for every public serializer.
OMITTED_VALUE = "value omitted by safety boundary"


def strip_safety_disclaimers(text: str) -> str:
    """Remove fixed non-advice disclaimers before deterministic advice scanning."""

    review_text = text
    for pattern in _SAFETY_DISCLAIMER_PATTERNS:
        review_text = pattern.sub(" ", review_text)
    return review_text


def matched_investment_advice_guard(text: str) -> str | None:
    """Return a deterministic guard name for actionable personalized advice.

    Explicitly attributed text inside matching quotation marks is a historical or
    descriptive transcript reference, not a newly issued recommendation.  Only
    the contents of a valid attributed quote are excluded; all remaining text on
    the line remains subject to the direct-advice patterns.
    """

    review_text = strip_safety_disclaimers(text)
    review_text = "\n".join(
        _without_attributed_quoted_content(line) for line in review_text.splitlines()
    )
    for name, pattern in _PERSONALIZED_INVESTMENT_ADVICE_PATTERNS:
        if pattern.search(review_text):
            return name
    return None


def _without_attributed_quoted_content(line: str) -> str:
    """Blank only one well-formed, directly attributed quote on a line."""

    pairs = _matched_quote_pairs(line)
    if pairs is None or len(pairs) != 1:
        return line
    opening_index, closing_index = pairs[0]
    if not _has_direct_quote_attribution(line, opening_index):
        return line
    characters = list(line)
    characters[opening_index + 1 : closing_index] = " " * (
        closing_index - opening_index - 1
    )
    return "".join(characters)


def _has_direct_quote_attribution(line: str, opening_index: int) -> bool:
    """Accept only an attribution that ends immediately before this opener."""

    clause_start = 0
    for boundary in re.finditer(r"[.!?。！？;\n]", line[:opening_index]):
        clause_start = boundary.end()
    return _DIRECT_QUOTE_ATTRIBUTION_PATTERN.fullmatch(
        line[clause_start:opening_index]
    ) is not None


def _matched_quote_pairs(line: str) -> list[tuple[int, int]] | None:
    """Return properly nested ASCII, curly, and Chinese-angle quote pairs.

    ASCII double quotes are symmetric delimiters.  A closing curly or Chinese
    delimiter must close the matching most-recent opener; otherwise the whole
    line is malformed and receives no quoted-text exception.
    """

    stack: list[tuple[str, int]] = []
    pairs: list[tuple[int, int]] = []
    for index, character in enumerate(line):
        if character == '"':
            if stack and stack[-1][0] == '"':
                _, opening_index = stack.pop()
                pairs.append((opening_index, index))
            else:
                stack.append(('"', index))
        elif character in _QUOTE_OPEN_TO_CLOSE:
            stack.append((_QUOTE_OPEN_TO_CLOSE[character], index))
        elif character in _QUOTE_CLOSERS:
            if not stack or stack[-1][0] != character:
                return None
            _, opening_index = stack.pop()
            pairs.append((opening_index, index))
    return pairs if not stack else None


def contains_sensitive_text(value: object, *, reject_any_uri: bool = False) -> bool:
    """Return whether text contains a credential, unsafe URI, or report-forbidden body."""

    if not isinstance(value, str):
        return True
    lowered = value.lower()
    return bool(
        _API_KEY_LIKE_PATTERN.search(value)
        or _PRIVATE_KEY_PATTERN.search(value)
        or _CREDENTIAL_ASSIGNMENT_PATTERN.search(value)
        or _BEARER_TOKEN_PATTERN.search(value)
        or _URI_QUERY_OR_FRAGMENT_PATTERN.search(value)
        or (reject_any_uri and _URI_PATTERN.search(value))
        or any(fragment in lowered for fragment in _FORBIDDEN_TEXT_FRAGMENTS)
        or any(
            (ord(character) < 32 and character not in {"\n", "\r", "\t"})
            or ord(character) == 127
            for character in value
        )
    )


def is_sensitive_key(value: object) -> bool:
    """Reject values stored under credential-like keys before serializing metadata."""

    return not isinstance(value, str) or bool(_SENSITIVE_KEY_FRAGMENT_PATTERN.search(value))


def safe_text(value: object, *, maximum_length: int = 4000) -> str:
    """Bound text for rendered reports without reflecting unsafe bodies."""

    if not isinstance(value, str):
        return OMITTED_VALUE
    text = (
        value.replace("\x00", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()[:maximum_length]
    )
    safety_text = strip_safety_disclaimers(text)
    if (
        not text
        or contains_sensitive_text(safety_text, reject_any_uri=True)
        or matched_investment_advice_guard(text) is not None
    ):
        return OMITTED_VALUE
    return text


def is_safe_public_string(value: object, *, maximum_length: int = 1024) -> bool:
    """Accept only bounded strings that can safely cross a public metadata boundary."""

    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum_length
        and value == value.strip()
        and not contains_sensitive_text(value, reject_any_uri=True)
    )


def json_safe_value(value: Any) -> Any:
    """Recursively emit JSON primitives while omitting unsafe or unsupported values."""

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if value == value and value not in {float("inf"), float("-inf")} else None
    if isinstance(value, str):
        return safe_text(value)
    if isinstance(value, list) or isinstance(value, tuple):
        return [json_safe_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or is_sensitive_key(key):
                continue
            result[safe_text(key, maximum_length=128)] = json_safe_value(item)
        return result
    return None
