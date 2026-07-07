from __future__ import annotations

import os
from typing import Any, Protocol

import requests

from .errors import LLMProviderConfigError, LLMProviderRequestError


DEFAULT_OPENAI_COMPATIBLE_BASE_URL = "https://api.openai.com/v1"
SEMANTIC_API_COST_ACK = (
    "I understand this may call an external LLM API, send transcript text outside this machine, "
    "and incur costs."
)


def require_exact_api_cost_ack(api_cost_ack: str) -> None:
    """在 provider construction 前強制 exact acknowledgement（audit F-03）。"""

    if api_cost_ack != SEMANTIC_API_COST_ACK:
        raise LLMProviderConfigError(
            f"LLM provider requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}"
        )


class SemanticSummaryProvider(Protocol):
    """語意摘要 provider 的最小介面。"""

    provider_name: str
    model: str

    def summarize_chunk(self, chunk: dict[str, Any]) -> str:
        """摘要單一 transcript chunk。"""

    def summarize_final(
        self,
        *,
        podcast_display_name: str,
        episode_ref: str,
        title: str,
        chunk_summaries: list[str],
    ) -> str:
        """合併 chunk summaries 成整集摘要。"""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """執行 OpenAI-compatible chat completion。"""


class OpenAICompatibleProvider:
    """使用 OpenAI-compatible chat completions API 的 provider。"""

    provider_name = "openai-compatible"

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
    ) -> None:
        api_key = os.environ.get(api_key_env, "").strip()
        resolved_model = (
            model or os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL", "")
        ).strip()
        resolved_base_url = (
            base_url
            or os.environ.get("BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_OPENAI_COMPATIBLE_BASE_URL
        ).strip()

        if not api_key:
            raise LLMProviderConfigError(f"缺少 LLM API key 環境變數：{api_key_env}")
        if not resolved_model:
            raise LLMProviderConfigError("缺少 LLM model；請提供 --model 或設定 MODEL。")

        self.api_key = api_key
        self.model = resolved_model
        self.base_url = resolved_base_url.rstrip("/")

    def summarize_chunk(self, chunk: dict[str, Any]) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是 podcast 逐字稿摘要器。只根據使用者提供的逐字稿片段摘要，"
                    "所有重點盡量附 timestamp evidence，不要產生投資建議。"
                ),
            },
            {
                "role": "user",
                "content": _chunk_prompt(chunk),
            },
        ]
        return self.complete(messages)

    def summarize_final(
        self,
        *,
        podcast_display_name: str,
        episode_ref: str,
        title: str,
        chunk_summaries: list[str],
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是 podcast 語意摘要器。根據 chunk summaries 整理整集摘要，"
                    "不得產生投資建議，所有市場觀點、公司、人物與事件都要盡量附 timestamp evidence。"
                ),
            },
            {
                "role": "user",
                "content": _final_prompt(
                    podcast_display_name=podcast_display_name,
                    episode_ref=episode_ref,
                    title=title,
                    chunk_summaries=chunk_summaries,
                ),
            },
        ]
        return self.complete(messages)

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
                timeout=(10, 120),
            )
        except requests.RequestException as exc:
            raise LLMProviderRequestError(f"LLM provider request failed：{exc}") from exc

        if not 200 <= response.status_code < 300:
            raise LLMProviderRequestError(
                f"LLM provider request failed with HTTP {response.status_code}：{response.text}"
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderRequestError("LLM provider response 格式不符合預期。") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderRequestError("LLM provider response 缺少可用內容。")
        return content.strip()


def create_provider(
    provider: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    api_cost_ack: str = "",
) -> SemanticSummaryProvider:
    """依 provider 名稱建立語意摘要 provider。"""

    require_exact_api_cost_ack(api_cost_ack)
    if provider != "openai-compatible":
        raise LLMProviderConfigError(f"不支援的 LLM provider：{provider}")
    return OpenAICompatibleProvider(
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
    )


def _chunk_prompt(chunk: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"請摘要 chunk {chunk['index']}，時間範圍 {chunk['start_time']} - {chunk['end_time']}。",
            "",
            "請包含：主要內容、提到的人物 / 公司 / 股票 / 產業 / 地點 / 書籍 / 電影 / 餐廳、可引用片段、不確定事項。",
            "限制：不要產生投資建議；所有判斷都要能回到逐字稿 timestamp。",
            "",
            chunk["text"],
        ]
    )


def _final_prompt(
    *,
    podcast_display_name: str,
    episode_ref: str,
    title: str,
    chunk_summaries: list[str],
) -> str:
    return "\n\n".join(
        [
            f"Podcast: {podcast_display_name}",
            f"Episode: {episode_ref}",
            f"Title: {title}",
            "請將以下 chunk summaries 合併成整集摘要，使用 Markdown，包含本集主題、市場觀點、台股觀點、美股觀點、總經觀點、提到的公司 / 股票 / 產業、人物 / 書 / 電影 / 音樂 / 餐廳 / 地點、生活閒聊、廣告 / 業配段落、時間軸摘要、可驗證引用、不確定事項。",
            "限制：不要產生投資建議；所有重要判斷都要盡量附 timestamp evidence。",
            "\n\n".join(chunk_summaries),
        ]
    )
