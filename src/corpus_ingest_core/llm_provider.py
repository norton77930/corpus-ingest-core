from __future__ import annotations

import os
from typing import Any, Protocol

import requests

from .errors import LLMProviderConfigError, LLMProviderRequestError
from .summary_profiles import (
    DEFAULT_SUMMARY_PROFILE,
    SummaryProfile,
    resolve_summary_profile,
)

DEFAULT_OPENAI_COMPATIBLE_BASE_URL = "https://api.openai.com/v1"
SEMANTIC_API_COST_ACK = (
    "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
)


def require_exact_api_cost_ack(api_cost_ack: str) -> None:
    """在 provider construction 前強制 exact acknowledgement（audit F-03）。"""

    if api_cost_ack != SEMANTIC_API_COST_ACK:
        raise LLMProviderConfigError(f"LLM provider requires exact api_cost_ack: {SEMANTIC_API_COST_ACK}")


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


# Only create_provider may pass this token into OpenAICompatibleProvider.
# Identity comparison closes the Batch 3C direct-construction ack bypass.
_PROVIDER_FACTORY_TOKEN = object()


class OpenAICompatibleProvider:
    """使用 OpenAI-compatible chat completions API 的 provider。

    Construct only via :func:`create_provider` (Batch 3C). Direct construction
    raises :class:`LLMProviderConfigError` so the exact ``api_cost_ack`` gate
    cannot be skipped by calling this class.
    """

    provider_name = "openai-compatible"

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        reasoning_effort: str | None = None,
        read_timeout_seconds: int = 120,
        summary_profile: str = DEFAULT_SUMMARY_PROFILE,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _PROVIDER_FACTORY_TOKEN:
            raise LLMProviderConfigError(
                "OpenAICompatibleProvider must be constructed via create_provider "
                "so the exact api_cost_ack gate is enforced; direct construction "
                "is not allowed."
            )

        api_key = os.environ.get(api_key_env, "").strip()
        resolved_model = (model or os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL", "")).strip()
        resolved_base_url = (
            base_url
            or os.environ.get("BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_OPENAI_COMPATIBLE_BASE_URL
        ).strip()

        if not api_key:
            raise LLMProviderConfigError(f"Missing LLM API key environment variable: {api_key_env}")
        if not resolved_model:
            raise LLMProviderConfigError("Missing LLM model; pass --model or set MODEL.")

        self.api_key = api_key
        self.model = resolved_model
        self.base_url = resolved_base_url.rstrip("/")
        self.reasoning_effort = reasoning_effort
        self.read_timeout_seconds = read_timeout_seconds
        self.summary_profile: SummaryProfile = resolve_summary_profile(summary_profile)

    def summarize_chunk(self, chunk: dict[str, Any]) -> str:
        messages = [
            {
                "role": "system",
                "content": self.summary_profile.chunk_system,
            },
            {
                "role": "user",
                "content": _chunk_prompt(self.summary_profile, chunk),
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
                "content": self.summary_profile.final_system,
            },
            {
                "role": "user",
                "content": _final_prompt(
                    self.summary_profile,
                    podcast_display_name=podcast_display_name,
                    episode_ref=episode_ref,
                    title=title,
                    chunk_summaries=chunk_summaries,
                ),
            },
        ]
        return self.complete(messages)

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=(10, self.read_timeout_seconds),
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
            raise LLMProviderRequestError("The LLM provider response is not in the expected shape.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderRequestError("The LLM provider response carries no usable content.")
        return content.strip()


def create_provider(
    provider: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
    api_cost_ack: str = "",
    summary_profile: str = DEFAULT_SUMMARY_PROFILE,
) -> SemanticSummaryProvider:
    """依 provider 名稱建立語意摘要 provider。

    ``summary_profile`` 在 ack 之後才解析：一個打錯的 profile 名稱不能搶在
    ack 失敗之前拋錯，否則錯誤訊息會遮住真正的安全邊界。
    """

    require_exact_api_cost_ack(api_cost_ack)
    if provider != "openai-compatible":
        raise LLMProviderConfigError(f"Unsupported LLM provider: {provider}")
    return OpenAICompatibleProvider(
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        reasoning_effort=reasoning_effort,
        read_timeout_seconds=read_timeout_seconds,
        summary_profile=summary_profile,
        _factory_token=_PROVIDER_FACTORY_TOKEN,
    )


def _chunk_prompt(profile: SummaryProfile, chunk: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"請摘要 chunk {chunk['index']}，時間範圍 {chunk['start_time']} - {chunk['end_time']}。",
            "",
            profile.chunk_sections,
            profile.chunk_constraints,
            "",
            chunk["text"],
        ]
    )


def _final_prompt(
    profile: SummaryProfile,
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
            profile.final_sections,
            profile.final_constraints,
            "\n\n".join(chunk_summaries),
        ]
    )
